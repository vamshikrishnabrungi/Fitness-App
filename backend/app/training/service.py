"""Training-plan reads and session lifecycle.

Generation is orchestrated by ``ai_generation_service``. This module contains
the persistence views and completion behavior shared by the API and worker.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.core.problems import ProblemError
from backend.app.knowledge.models import MethodVersion
from backend.app.operations.outbox import enqueue_event
from backend.app.training.models import (
    SessionCompletion,
    SessionItem,
    TrainingPlan,
    TrainingSession,
    TrainingWeek,
)
from backend.app.training.schemas import CompletionCommand, PlanView, PlanWeekView, SessionItemView, SessionView


async def _athlete(session: AsyncSession, user_id: UUID) -> AthleteProfile:
    athlete = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if athlete is None:
        raise ProblemError(409, "onboarding_required", "Onboarding required", "Complete athlete onboarding first.")
    return athlete


def _session_view_from_items(
    row: TrainingSession,
    items: list[tuple[SessionItem, MethodVersion]],
) -> SessionView:
    return SessionView(
        id=row.id,
        scheduled_for=row.scheduled_for,
        session_type=row.session_type,
        purpose=row.purpose,
        estimated_minutes=row.estimated_minutes,
        venue_code=row.venue_code,
        status=row.status,
        explanation=row.explanation,
        items=[
            SessionItemView(
                id=item.id,
                method_id=method.method_id,
                method_name=method.canonical_name,
                method_version=method.content_version,
                block_type=item.block_type,
                prescription=item.prescription_json,
                alternatives=[UUID(value["id"]) for value in item.substitution_methods_json],
                instructions=method.instructions,
                coaching_cues=method.cues,
                common_errors=method.common_errors,
                safety_boundaries=method.safety_boundaries,
            )
            for item, method in items
        ],
        version=row.version,
    )


async def session_view(session: AsyncSession, row: TrainingSession) -> SessionView:
    items = list((await session.execute(
        select(SessionItem, MethodVersion)
        .join(
            MethodVersion,
            and_(
                MethodVersion.method_id == SessionItem.method_id,
                MethodVersion.content_version == SessionItem.method_version,
            ),
        )
        .where(SessionItem.session_id == row.id)
        .order_by(SessionItem.sequence)
    )).all())
    return _session_view_from_items(row, items)


async def plan_view(session: AsyncSession, plan_id: UUID, athlete_id: UUID) -> PlanView:
    plan = await session.scalar(select(TrainingPlan).where(
        TrainingPlan.id == plan_id,
        TrainingPlan.athlete_id == athlete_id,
    ))
    if plan is None:
        raise ProblemError(404, "plan_not_found", "Plan not found", "The plan does not exist.")
    sessions = (await session.scalars(
        select(TrainingSession)
        .join(TrainingWeek)
        .where(TrainingWeek.plan_id == plan.id)
        .order_by(TrainingSession.scheduled_for)
    )).all()
    weeks = (await session.scalars(
        select(TrainingWeek)
        .where(TrainingWeek.plan_id == plan.id)
        .order_by(TrainingWeek.week_number)
    )).all()
    item_rows = (await session.execute(
        select(SessionItem, MethodVersion)
        .join(
            MethodVersion,
            and_(
                MethodVersion.method_id == SessionItem.method_id,
                MethodVersion.content_version == SessionItem.method_version,
            ),
        )
        .where(SessionItem.session_id.in_([row.id for row in sessions]))
        .order_by(SessionItem.session_id, SessionItem.sequence)
    )).all() if sessions else ()
    items_by_session: dict[UUID, list[tuple[SessionItem, MethodVersion]]] = defaultdict(list)
    for item, method in item_rows:
        items_by_session[item.session_id].append((item, method))
    inputs = plan.input_snapshot_json or {}
    return PlanView(
        id=plan.id,
        status=plan.status,
        starts_on=plan.starts_on.isoformat(),
        ends_on=plan.ends_on.isoformat(),
        planner_version=plan.planner_version,
        content_release_id=plan.content_release_id,
        dataset_hash=plan.dataset_hash,
        materialized_through=plan.materialized_through,
        sport_code=inputs.get("sport_code"),
        scope_code=inputs.get("scope_code"),
        phase_code=inputs.get("phase_code"),
        goal_code=inputs.get("goal_code"),
        decision_trace=plan.decision_trace_json,
        weeks=[
            PlanWeekView(
                week_number=week.week_number,
                starts_on=week.starts_on,
                planned_load=float(week.planned_load),
                deload=week.deload,
                intent=week.structure_json.get("intent", ""),
            )
            for week in weeks
        ],
        sessions=[_session_view_from_items(row, items_by_session[row.id]) for row in sessions],
    )


async def materialize_next_horizon(
    session: AsyncSession,
    user_id: UUID,
    plan_id: UUID,
) -> PlanView:
    """Return the already materialized AI plan.

    New plans are generated and persisted as a complete four-week horizon. The
    endpoint remains for older clients that still request materialization.
    """
    athlete = await _athlete(session, user_id)
    plan = await session.scalar(select(TrainingPlan).where(
        TrainingPlan.id == plan_id,
        TrainingPlan.athlete_id == athlete.id,
    ))
    if plan is None:
        raise ProblemError(404, "plan_not_found", "Plan not found", "The plan does not exist.")
    pending = await session.scalar(
        select(TrainingWeek.id).where(
            TrainingWeek.plan_id == plan.id,
            TrainingWeek.materialization_status == "pending",
        ).limit(1)
    )
    if pending is not None:
        raise ProblemError(
            409,
            "legacy_plan_not_materializable",
            "Plan is still being prepared",
            "Retry after the current generation has completed.",
        )
    return await plan_view(session, plan.id, athlete.id)


async def complete_session(
    session: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    command: CompletionCommand,
) -> SessionView:
    athlete = await _athlete(session, user_id)
    row = await session.scalar(
        select(TrainingSession)
        .where(
            TrainingSession.id == session_id,
            TrainingSession.athlete_id == athlete.id,
        )
        .with_for_update()
    )
    if row is None:
        raise ProblemError(404, "session_not_found", "Session not found", "The session does not exist.")
    if row.version != command.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the session and try again.")
    if row.status == "completed":
        raise ProblemError(409, "session_already_completed", "Already completed", "This session is already complete.")
    session.add(SessionCompletion(
        session_id=row.id,
        athlete_id=athlete.id,
        completed_at=datetime.now(timezone.utc),
        duration_minutes=command.duration_minutes,
        session_rpe=command.session_rpe,
        completion_ratio=command.completion_ratio,
        pain_flag=command.pain_flag,
        feedback_json={"notes": command.notes},
        calculated_load=command.duration_minutes * command.session_rpe,
    ))
    row.status = "completed"
    row.version += 1
    await enqueue_event(
        session,
        aggregate_type="training_session",
        aggregate_id=row.id,
        event_type="training.session.completed",
        payload={
            "session_id": str(row.id),
            "athlete_id": str(athlete.id),
            "pain_flag": command.pain_flag,
        },
    )
    await session.commit()
    return await session_view(session, row)

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.models import Activity, ActivityQuality
from backend.app.activities.service import athlete_id
from backend.app.core.database import get_session
from backend.app.core.pagination import decode_cursor, encode_cursor
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id, require_roles
from backend.app.operations.models import AuditEvent
from backend.app.operations.outbox import enqueue_event

from .models import CompetitionFlag, ModerationAppeal, ModerationDecision
from .schemas import AppealCreate, AppealDecisionCommand, FlagDecisionCommand

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get("/my-flags")
async def my_flags(
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    athlete = await athlete_id(session, user_id)
    query = select(CompetitionFlag).where(CompetitionFlag.athlete_id == athlete)
    if cursor:
        created_at, flag_id = decode_cursor(cursor)
        query = query.where(
            or_(
                CompetitionFlag.created_at < created_at,
                and_(CompetitionFlag.created_at == created_at, CompetitionFlag.id < flag_id),
            )
        )
    fetched = (
        await session.scalars(
            query.order_by(CompetitionFlag.created_at.desc(), CompetitionFlag.id.desc()).limit(limit + 1)
        )
    ).all()
    rows = fetched[:limit]
    return {
        "items": [
            {
                "id": row.id,
                "subject_type": row.subject_type,
                "subject_id": row.subject_id,
                "flag_code": row.flag_code,
                "severity": row.severity,
                "status": row.status,
                "evidence": row.evidence_json,
                "created_at": row.created_at,
                "version": row.version,
            }
            for row in rows
        ],
        "next_cursor": encode_cursor(rows[-1].created_at, rows[-1].id) if len(fetched) > limit else None,
    }


@router.post("/flags/{flag_id}/appeal", status_code=201)
async def appeal(
    flag_id: UUID,
    body: AppealCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    flag = await session.scalar(
        select(CompetitionFlag)
        .where(CompetitionFlag.id == flag_id, CompetitionFlag.athlete_id == athlete)
        .with_for_update()
    )
    if flag is None:
        raise ProblemError(404, "flag_not_found", "Flag not found", "The moderation flag does not exist.")
    if flag.status != "confirmed":
        raise ProblemError(409, "appeal_not_available", "Appeal unavailable", "Only a confirmed moderation decision can be appealed.")
    decision = await session.scalar(
        select(ModerationDecision)
        .where(ModerationDecision.flag_id == flag.id, ModerationDecision.decision == "confirm_violation")
        .order_by(ModerationDecision.decided_at.desc())
    )
    if decision is None:
        raise ProblemError(409, "decision_required", "Decision required", "An appeal can be filed after a moderation decision.")
    existing = await session.scalar(
        select(ModerationAppeal).where(
            ModerationAppeal.decision_id == decision.id,
            ModerationAppeal.athlete_id == athlete,
        )
    )
    if existing:
        return {"id": existing.id, "status": existing.status, "version": existing.version}
    row = ModerationAppeal(
        decision_id=decision.id,
        athlete_id=athlete,
        reason=body.reason,
        status="open",
    )
    session.add(row)
    flag.status = "appealed"
    flag.version += 1
    await session.flush()
    await enqueue_event(
        session,
        topic="competition",
        event_type="moderation.appeal.created",
        aggregate_type="moderation_appeal",
        aggregate_id=row.id,
        payload={"flag_id": str(flag.id), "athlete_id": str(athlete)},
    )
    await session.commit()
    return {"id": row.id, "status": row.status, "version": row.version}


@router.get("/admin/flags", dependencies=[Depends(require_roles("moderator", "platform_admin"))])
async def admin_flags(
    status: str = "open",
    cursor: str | None = None,
    limit: int = 25,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if status not in {"open", "under_review", "confirmed", "cleared", "appealed"}:
        raise ProblemError(422, "moderation_status_invalid", "Invalid status", "Choose a supported moderation status.")
    limit = max(1, min(limit, 100))
    query = select(CompetitionFlag).where(CompetitionFlag.status == status)
    if cursor:
        created_at, flag_id = decode_cursor(cursor)
        query = query.where(
            or_(
                CompetitionFlag.created_at < created_at,
                and_(CompetitionFlag.created_at == created_at, CompetitionFlag.id < flag_id),
            )
        )
    fetched = (
        await session.scalars(
            query.order_by(CompetitionFlag.created_at.desc(), CompetitionFlag.id.desc()).limit(limit + 1)
        )
    ).all()
    rows = fetched[:limit]
    return {
        "items": [
            {
                "id": row.id,
                "athlete_id": row.athlete_id,
                "subject_type": row.subject_type,
                "subject_id": row.subject_id,
                "flag_code": row.flag_code,
                "severity": row.severity,
                "evidence": row.evidence_json,
                "status": row.status,
                "created_at": row.created_at,
                "version": row.version,
            }
            for row in rows
        ],
        "next_cursor": encode_cursor(rows[-1].created_at, rows[-1].id) if len(fetched) > limit else None,
    }


async def _apply_activity_decision(
    session: AsyncSession,
    flag: CompetitionFlag,
    *,
    cleared: bool,
) -> None:
    if flag.subject_type != "activity":
        return
    activity = await session.get(Activity, flag.subject_id)
    if activity is None:
        return
    quality = await session.scalar(
        select(ActivityQuality)
        .where(
            ActivityQuality.activity_id == activity.id,
            ActivityQuality.computation_version == activity.computation_version,
        )
        .with_for_update()
    )
    if cleared and activity.source == "runlete":
        await enqueue_event(
            session,
            topic="activity",
            event_type="activity.reprocess.requested",
            aggregate_type="activity",
            aggregate_id=activity.id,
            payload={"activity_id": str(activity.id), "reason": "moderation_flag_cleared"},
        )
    elif not cleared:
        if quality:
            quality.competition_eligible = False
            quality.territory_eligible = False
            quality.reasons = sorted(set(quality.reasons + ["moderation_violation_confirmed"]))
            quality.version += 1
        await enqueue_event(
            session,
            topic="competition",
            event_type="activity.competition.disqualified",
            aggregate_type="activity",
            aggregate_id=activity.id,
            payload={"activity_id": str(activity.id), "athlete_id": str(activity.athlete_id)},
        )


@router.post(
    "/admin/flags/{flag_id}/decision",
    dependencies=[Depends(require_roles("moderator", "platform_admin"))],
)
async def decide_flag(
    flag_id: UUID,
    body: FlagDecisionCommand,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    moderator_user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    flag = await session.get(CompetitionFlag, flag_id, with_for_update=True)
    if flag is None:
        raise ProblemError(404, "flag_not_found", "Flag not found", "The moderation flag does not exist.")
    if flag.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the flag and try again.")
    if flag.status not in {"open", "under_review"}:
        raise ProblemError(409, "flag_already_decided", "Flag already decided", "This flag cannot receive another initial decision.")
    now = datetime.now(timezone.utc)
    decision = ModerationDecision(
        flag_id=flag.id,
        moderator_user_id=moderator_user_id,
        decision=body.decision,
        rationale=body.rationale,
        evidence_snapshot_json={
            "flag_code": flag.flag_code,
            "severity": flag.severity,
            "evidence": flag.evidence_json,
            "computation_version": flag.computation_version,
        },
        decided_at=now,
    )
    session.add(decision)
    flag.status = "cleared" if body.decision == "clear_flag" else "confirmed"
    flag.version += 1
    await _apply_activity_decision(session, flag, cleared=body.decision == "clear_flag")
    session.add(
        AuditEvent(
            actor_user_id=moderator_user_id,
            action="moderation.flag_decided",
            subject_type="competition_flag",
            subject_id=flag.id,
            before={"status": "open"},
            after={"status": flag.status, "decision": body.decision},
            created_at=now,
        )
    )
    await enqueue_event(
        session,
        topic="competition",
        event_type="moderation.flag.decided",
        aggregate_type="competition_flag",
        aggregate_id=flag.id,
        payload={"athlete_id": str(flag.athlete_id), "status": flag.status},
    )
    await session.commit()
    return {"id": decision.id, "flag_id": flag.id, "status": flag.status, "version": flag.version}


@router.get("/admin/appeals", dependencies=[Depends(require_roles("moderator", "platform_admin"))])
async def admin_appeals(
    status: str = "open",
    cursor: str | None = None,
    limit: int = 25,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if status not in {"open", "upheld", "overturned"}:
        raise ProblemError(422, "appeal_status_invalid", "Invalid status", "Choose a supported appeal status.")
    limit = max(1, min(limit, 100))
    query = select(ModerationAppeal).where(ModerationAppeal.status == status)
    if cursor:
        created_at, appeal_id = decode_cursor(cursor)
        query = query.where(
            or_(
                ModerationAppeal.created_at < created_at,
                and_(ModerationAppeal.created_at == created_at, ModerationAppeal.id < appeal_id),
            )
        )
    fetched = (
        await session.scalars(
            query.order_by(ModerationAppeal.created_at.desc(), ModerationAppeal.id.desc()).limit(limit + 1)
        )
    ).all()
    rows = fetched[:limit]
    return {
        "items": [
            {
                "id": row.id,
                "decision_id": row.decision_id,
                "athlete_id": row.athlete_id,
                "reason": row.reason,
                "status": row.status,
                "created_at": row.created_at,
                "version": row.version,
            }
            for row in rows
        ],
        "next_cursor": encode_cursor(rows[-1].created_at, rows[-1].id) if len(fetched) > limit else None,
    }


@router.post(
    "/admin/appeals/{appeal_id}/decision",
    dependencies=[Depends(require_roles("moderator", "platform_admin"))],
)
async def decide_appeal(
    appeal_id: UUID,
    body: AppealDecisionCommand,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    moderator_user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    appeal_row = await session.get(ModerationAppeal, appeal_id, with_for_update=True)
    if appeal_row is None:
        raise ProblemError(404, "appeal_not_found", "Appeal not found", "The moderation appeal does not exist.")
    if appeal_row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the appeal and try again.")
    if appeal_row.status != "open":
        raise ProblemError(409, "appeal_already_decided", "Appeal already decided", "This appeal is no longer open.")
    original = await session.get(ModerationDecision, appeal_row.decision_id)
    flag = await session.get(CompetitionFlag, original.flag_id, with_for_update=True) if original else None
    if flag is None:
        raise ProblemError(409, "appeal_flag_missing", "Flag unavailable", "The original moderation flag is unavailable.")
    now = datetime.now(timezone.utc)
    overturned = body.decision == "overturn"
    appeal_row.status = "overturned" if overturned else "upheld"
    appeal_row.version += 1
    flag.status = "cleared" if overturned else "confirmed"
    flag.version += 1
    session.add(
        ModerationDecision(
            flag_id=flag.id,
            moderator_user_id=moderator_user_id,
            decision="clear_flag_on_appeal" if overturned else "uphold_violation_on_appeal",
            rationale=body.rationale,
            evidence_snapshot_json={"appeal_id": str(appeal_row.id), "appeal_reason": appeal_row.reason},
            decided_at=now,
        )
    )
    await _apply_activity_decision(session, flag, cleared=overturned)
    session.add(
        AuditEvent(
            actor_user_id=moderator_user_id,
            action="moderation.appeal_decided",
            subject_type="moderation_appeal",
            subject_id=appeal_row.id,
            before={"status": "open"},
            after={"status": appeal_row.status, "flag_status": flag.status},
            created_at=now,
        )
    )
    await enqueue_event(
        session,
        topic="competition",
        event_type="moderation.appeal.decided",
        aggregate_type="moderation_appeal",
        aggregate_id=appeal_row.id,
        payload={"athlete_id": str(appeal_row.athlete_id), "status": appeal_row.status},
    )
    await session.commit()
    return {"id": appeal_row.id, "status": appeal_row.status, "flag_status": flag.status, "version": appeal_row.version}

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from .models import TrainingPlan, TrainingSession, TrainingWeek
from .schemas import CompletionCommand, PlanCreate, PlanView, SessionView
from .ai_generation_service import generate_ai_plan
from .service import complete_session, materialize_next_horizon, plan_view, session_view

router = APIRouter(prefix="/training", tags=["training"])


async def _athlete_id(session: AsyncSession, user_id: UUID) -> UUID:
    value = await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == user_id))
    if value is None:
        raise ProblemError(409, "onboarding_required", "Onboarding required", "Complete onboarding first.")
    return value


@router.post("/plans", response_model=PlanView, status_code=201)
async def create_plan(body: PlanCreate, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> PlanView:
    return await generate_ai_plan(
        session,
        user_id,
        body.weeks,
        body.starts_on,
        fitness_level=body.fitness_level,
        training_days_per_week=body.training_days_per_week,
        health_context=body.health_context,
        schedule_constraints=body.schedule_constraints,
    )


@router.get("/history", response_model=list[SessionView])
async def history(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> list[SessionView]:
    athlete_id = await _athlete_id(session, user_id)
    rows = (await session.scalars(
        select(TrainingSession)
        .join(TrainingWeek, TrainingWeek.id == TrainingSession.week_id)
        .join(TrainingPlan, TrainingPlan.id == TrainingWeek.plan_id)
        .where(TrainingSession.athlete_id == athlete_id, TrainingPlan.status == "active")
        .order_by(TrainingSession.scheduled_for.desc())
        .limit(100)
    )).all()
    return [await session_view(session, row) for row in rows]


@router.get("/plans/{plan_id}", response_model=PlanView)
async def get_plan(plan_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> PlanView:
    return await plan_view(session, plan_id, await _athlete_id(session, user_id))


@router.post("/plans/{plan_id}/materialize", response_model=PlanView)
async def materialize(plan_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> PlanView:
    return await materialize_next_horizon(session,user_id,plan_id)


@router.get("/sessions/today", response_model=SessionView | None)
async def today(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> SessionView | None:
    athlete_id = await _athlete_id(session, user_id)
    now = datetime.now(timezone.utc)
    row = await session.scalar(
        select(TrainingSession)
        .join(TrainingWeek, TrainingWeek.id == TrainingSession.week_id)
        .join(TrainingPlan, TrainingPlan.id == TrainingWeek.plan_id)
        .where(
            TrainingSession.athlete_id == athlete_id,
            TrainingPlan.status == "active",
            TrainingSession.scheduled_for >= now.replace(hour=0, minute=0, second=0),
            TrainingSession.scheduled_for < now.replace(hour=0, minute=0, second=0) + __import__('datetime').timedelta(days=1),
        )
        .order_by(TrainingSession.scheduled_for)
    )
    return await session_view(session, row) if row else None


@router.get("/sessions/{session_id}", response_model=SessionView)
async def get_session_detail(session_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> SessionView:
    athlete_id = await _athlete_id(session, user_id)
    row = await session.scalar(select(TrainingSession).where(TrainingSession.id == session_id, TrainingSession.athlete_id == athlete_id))
    if row is None:
        raise ProblemError(404, "session_not_found", "Session not found", "The session does not exist.")
    return await session_view(session, row)


@router.post("/sessions/{session_id}/complete", response_model=SessionView)
async def complete(session_id: UUID, body: CompletionCommand, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> SessionView:
    return await complete_session(session, user_id, session_id, body)

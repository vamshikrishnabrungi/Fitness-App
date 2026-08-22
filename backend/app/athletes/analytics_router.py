from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_session
from backend.app.core.security import current_user_id
from backend.app.activities.models import Activity
from backend.app.activities.service import athlete_id
from backend.app.training.models import SessionCompletion
from .models import Assessment

router = APIRouter(tags=["athlete analytics"])


@router.get("/profile/stats")
async def profile_stats(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); values = (await session.execute(select(func.count(Activity.id), func.coalesce(func.sum(Activity.distance_m), 0), func.coalesce(func.sum(Activity.moving_seconds), 0)).where(Activity.athlete_id == athlete, Activity.status == "complete"))).one()
    return {"activities": values[0], "distance_km": float(values[1]) / 1000, "moving_minutes": float(values[2]) / 60}


@router.get("/training/fitness")
async def fitness(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); now = datetime.now(timezone.utc)
    recent = float(await session.scalar(select(func.coalesce(func.sum(SessionCompletion.calculated_load), 0)).where(SessionCompletion.athlete_id == athlete, SessionCompletion.completed_at >= now - timedelta(days=7))) or 0) / 7
    chronic = float(await session.scalar(select(func.coalesce(func.sum(SessionCompletion.calculated_load), 0)).where(SessionCompletion.athlete_id == athlete, SessionCompletion.completed_at >= now - timedelta(days=28))) or 0) / 28
    return {"current": {"fitness": chronic, "fatigue": recent, "form": chronic - recent}}


@router.get("/training-load")
async def training_load(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict: return await fitness(user_id, session)


@router.get("/activities/stats")
async def run_stats(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict: return await profile_stats(user_id, session)


@router.post("/athletes/me/assessments", status_code=201)
async def assessment(body: dict, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); created=[]
    for code,value in body.items():
        if isinstance(value,(int,float)) and value >= 0:
            row=Assessment(athlete_id=athlete,assessment_code=code,value=value,unit="count" if "seconds" not in code and "pace" not in code else "seconds",measured_at=datetime.now(timezone.utc),source="athlete");session.add(row);created.append(row)
    await session.commit(); return {"ids":[row.id for row in created]}


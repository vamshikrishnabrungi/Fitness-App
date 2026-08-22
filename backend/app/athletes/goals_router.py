from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_session
from backend.app.core.security import current_user_id
from backend.app.activities.service import athlete_id
from .models import AthleteGoal

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("")
async def goals(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> list[dict]:
    athlete = await athlete_id(session, user_id); rows = (await session.scalars(select(AthleteGoal).where(AthleteGoal.athlete_id == athlete, AthleteGoal.status == "active").order_by(AthleteGoal.priority))).all()
    return [
        {
            "id": row.id,
            "goal_type": row.goal_type,
            "name": row.goal_type.replace("_", " ").title(),
            "target": float(row.target_value) if row.target_value is not None else None,
            "unit": row.target_unit,
            "target_date": row.target_date,
        }
        for row in rows
    ]


@router.post("", status_code=201)
async def create_goal(body: dict, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); row = AthleteGoal(athlete_id=athlete, goal_type=body.get("metric", body.get("goal_type", "distance")), target_value=body.get("target"), target_unit=body.get("unit", "km"), status="active", priority=2)
    session.add(row); await session.commit(); return {"id": row.id}

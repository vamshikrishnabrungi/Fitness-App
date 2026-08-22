from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.security import current_user_id
from .schemas import AthleteProfileView, OnboardingCommand
from .service import complete_onboarding, get_profile

router = APIRouter(tags=["athletes"])


@router.put("/onboarding", response_model=AthleteProfileView)
async def onboarding(body: OnboardingCommand, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> AthleteProfileView:
    return await complete_onboarding(session, user_id, body)


@router.get("/athletes/me", response_model=AthleteProfileView)
async def me(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> AthleteProfileView:
    return await get_profile(session, user_id)


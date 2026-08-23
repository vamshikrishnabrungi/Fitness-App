from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.problems import ProblemError
from backend.app.identity.models import User
from .models import AthleteGoal, AthleteProfile, AthleteSport, AvailabilityWindow, EquipmentAccess
from .schemas import AthleteProfileView, AvailabilityInput, GoalInput, OnboardingCommand, SportInput


async def get_profile(session: AsyncSession, user_id: UUID) -> AthleteProfileView:
    profile = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if profile is None:
        raise ProblemError(404, "athlete_not_found", "Athlete profile not found", "Complete onboarding first.")
    sports = (await session.scalars(select(AthleteSport).where(AthleteSport.athlete_id == profile.id))).all()
    slots = (await session.scalars(select(AvailabilityWindow).where(AvailabilityWindow.athlete_id == profile.id))).all()
    equipment = (await session.scalars(select(EquipmentAccess.equipment_code).where(EquipmentAccess.athlete_id == profile.id))).all()
    goal = await session.scalar(select(AthleteGoal).where(AthleteGoal.athlete_id == profile.id, AthleteGoal.status == "active").order_by(AthleteGoal.priority))
    return AthleteProfileView(
        id=profile.id, timezone=profile.timezone, country_code=profile.country_code,
        height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
        weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
        competition_level=profile.competition_level, training_age_years=profile.training_age_years,
        maximum_session_minutes=profile.maximum_session_minutes,
        sports=[SportInput.model_validate(x, from_attributes=True) for x in sports],
        availability=[AvailabilityInput.model_validate(x, from_attributes=True) for x in slots],
        equipment_codes=list(equipment),
        active_goal=GoalInput.model_validate(goal, from_attributes=True) if goal else None,
        version=profile.version,
    )


async def complete_onboarding(session: AsyncSession, user_id: UUID, command: OnboardingCommand) -> AthleteProfileView:
    user = await session.get(User, user_id, with_for_update=True)
    if user is None:
        raise ProblemError(404, "user_not_found", "User not found", "The account does not exist.")
    profile = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id).with_for_update())
    if profile is None:
        profile = AthleteProfile(user_id=user_id)
        session.add(profile)
        await session.flush()
    profile.timezone = command.timezone
    profile.country_code = command.country_code.upper() if command.country_code else None
    profile.height_cm = command.height_cm
    profile.weight_kg = command.weight_kg
    profile.competition_level = command.competition_level
    profile.training_age_years = command.training_age_years
    profile.maximum_session_minutes = command.maximum_session_minutes
    await session.execute(delete(AthleteSport).where(AthleteSport.athlete_id == profile.id))
    await session.execute(delete(AvailabilityWindow).where(AvailabilityWindow.athlete_id == profile.id))
    await session.execute(delete(EquipmentAccess).where(EquipmentAccess.athlete_id == profile.id))
    for sport in command.sports:
        session.add(AthleteSport(athlete_id=profile.id, **sport.model_dump()))
    for slot in command.availability:
        session.add(AvailabilityWindow(athlete_id=profile.id, **slot.model_dump()))
    for code in sorted(set(command.equipment_codes)):
        session.add(EquipmentAccess(athlete_id=profile.id, equipment_code=code, environments=command.environments))
    await session.execute(delete(AthleteGoal).where(AthleteGoal.athlete_id == profile.id, AthleteGoal.status == "active"))
    session.add(AthleteGoal(athlete_id=profile.id, **command.goal.model_dump()))
    user.onboarding_completed = True
    await session.commit()
    return await get_profile(session, user_id)


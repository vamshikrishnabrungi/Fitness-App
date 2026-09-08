from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.problems import ProblemError
from backend.app.identity.models import User
from backend.app.knowledge.models import Method
from .models import (
    AthleteGoal,
    AthleteMethodFamiliarity,
    AthleteProfile,
    AthleteSport,
    AvailabilityWindow,
    EquipmentAccess,
    ExternalLoad,
)
from .schemas import (
    AthleteProfileView,
    AvailabilityInput,
    EquipmentAccessInput,
    ExternalLoadInput,
    GoalInput,
    MethodFamiliarityInput,
    OnboardingCommand,
    SportInput,
    AthleteProfileUpdate,
)


async def get_profile(session: AsyncSession, user_id: UUID) -> AthleteProfileView:
    profile = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if profile is None:
        raise ProblemError(404, "athlete_not_found", "Athlete profile not found", "Complete onboarding first.")
    sports = (await session.scalars(select(AthleteSport).where(AthleteSport.athlete_id == profile.id))).all()
    slots = (await session.scalars(select(AvailabilityWindow).where(AvailabilityWindow.athlete_id == profile.id))).all()
    external_loads = (await session.scalars(
        select(ExternalLoad)
        .where(ExternalLoad.athlete_id == profile.id)
        .order_by(ExternalLoad.starts_at)
    )).all()
    equipment = (await session.scalars(
        select(EquipmentAccess)
        .where(EquipmentAccess.athlete_id == profile.id)
        .order_by(EquipmentAccess.equipment_code)
    )).all()
    familiarity = (await session.execute(
        select(AthleteMethodFamiliarity, Method.code)
        .join(Method, Method.id == AthleteMethodFamiliarity.method_id)
        .where(AthleteMethodFamiliarity.athlete_id == profile.id)
        .order_by(Method.code)
    )).all()
    goal = await session.scalar(select(AthleteGoal).where(AthleteGoal.athlete_id == profile.id, AthleteGoal.status == "active").order_by(AthleteGoal.priority))
    return AthleteProfileView(
        id=profile.id, timezone=profile.timezone, country_code=profile.country_code,
        height_cm=float(profile.height_cm) if profile.height_cm is not None else None,
        weight_kg=float(profile.weight_kg) if profile.weight_kg is not None else None,
        competition_level=profile.competition_level, training_age_years=profile.training_age_years,
        maximum_session_minutes=profile.maximum_session_minutes, season_phase=profile.season_phase,
        distance_unit=profile.distance_unit, running_experience=profile.running_experience,
        runs_per_week=profile.runs_per_week, weekly_distance_m=float(profile.weekly_distance_m),
        longest_recent_run_m=float(profile.longest_recent_run_m), recent_race_event=profile.recent_race_event,
        recent_race_time_seconds=profile.recent_race_time_seconds,
        training_interruption=profile.training_interruption, terrains=list(profile.terrains),
        cross_training_consent=profile.cross_training_consent,
        health_context=dict(profile.health_context_json or {}),
        sports=[SportInput.model_validate(x, from_attributes=True) for x in sports],
        availability=[AvailabilityInput.model_validate(x, from_attributes=True) for x in slots],
        external_loads=[
            ExternalLoadInput.model_validate({
                "sport_code": row.sport_code,
                "load_type": row.load_type,
                "starts_at": row.starts_at,
                "duration_minutes": row.duration_minutes,
                "intensity": row.intensity,
                "recurrence": row.recurrence_json,
            })
            for row in external_loads
        ],
        equipment_access=[EquipmentAccessInput.model_validate(row, from_attributes=True) for row in equipment],
        method_familiarity=[
            MethodFamiliarityInput(
                method_code=method_code,
                familiarity=row.familiarity,
                successful_exposures=row.successful_exposures,
                last_performed_on=row.last_performed_on,
            )
            for row, method_code in familiarity
        ],
        active_goal=GoalInput.model_validate(goal, from_attributes=True) if goal else None,
        version=profile.version,
    )


async def complete_onboarding(session: AsyncSession, user_id: UUID, command: OnboardingCommand) -> AthleteProfileView:
    user = await session.get(User, user_id, with_for_update=True)
    if user is None:
        raise ProblemError(404, "user_not_found", "User not found", "The account does not exist.")
    profile = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id).with_for_update())
    created_profile = profile is None
    if profile is None:
        profile = AthleteProfile(user_id=user_id)
        session.add(profile)
        await session.flush()
    profile.timezone = command.timezone
    profile.country_code = command.country_code.upper() if command.country_code else None
    profile.height_cm = command.height_cm
    profile.weight_kg = command.weight_kg
    profile.competition_level = {"beginner": "recreational", "intermediate": "club", "advanced": "regional"}[command.fitness_level]
    # The onboarding level is the explicit training signal used by the
    # generator. Keep the existing integer field populated for older clients
    # and analytics that still read training age.
    profile.training_age_years = (
        {"beginner": 0, "intermediate": 2, "advanced": 5}[command.fitness_level]
    )
    profile.maximum_session_minutes = command.maximum_session_minutes
    profile.season_phase = command.season_phase
    profile.cross_training_consent = False
    profile.health_context_json = command.health_context
    profile.distance_unit = command.distance_unit
    profile.running_experience = command.fitness_level
    profile.runs_per_week = command.runs_per_week
    profile.weekly_distance_m = command.weekly_distance_m
    profile.longest_recent_run_m = command.longest_recent_run_m
    profile.recent_race_event = command.recent_race_event
    profile.recent_race_time_seconds = command.recent_race_time_seconds
    profile.training_interruption = command.training_interruption
    profile.terrains = command.terrains
    if not created_profile:
        await session.execute(delete(AthleteSport).where(AthleteSport.athlete_id == profile.id))
        await session.execute(delete(AvailabilityWindow).where(AvailabilityWindow.athlete_id == profile.id))
        await session.execute(delete(EquipmentAccess).where(EquipmentAccess.athlete_id == profile.id))
        await session.execute(delete(AthleteMethodFamiliarity).where(AthleteMethodFamiliarity.athlete_id == profile.id))
        await session.execute(delete(ExternalLoad).where(ExternalLoad.athlete_id == profile.id))
    session.add(AthleteSport(
        athlete_id=profile.id,
        sport_code="running",
        event_code=command.target_event,
        is_primary=True,
        weekly_external_minutes=0,
        sessions_per_week=len(command.availability),
    ))
    for slot in command.availability:
        session.add(AvailabilityWindow(athlete_id=profile.id, **slot.model_dump()))
    all_available_environments = sorted({
        environment
        for slot in command.availability
        for environment in slot.environments
    })
    equipment_access = {row.equipment_code: row.environments for row in command.equipment_access}
    equipment_access["bodyweight"] = all_available_environments
    for code, environments in sorted(equipment_access.items()):
        session.add(EquipmentAccess(
            athlete_id=profile.id,
            equipment_code=code,
            environments=environments,
        ))
    active_goal = await session.scalar(
        select(AthleteGoal)
        .where(AthleteGoal.athlete_id == profile.id, AthleteGoal.status == "active")
        .order_by(AthleteGoal.priority, AthleteGoal.created_at)
        .limit(1)
    )
    if active_goal is None:
        session.add(AthleteGoal(athlete_id=profile.id, **command.goal.model_dump()))
    else:
        for field, value in command.goal.model_dump().items():
            setattr(active_goal, field, value)
        active_goal.version += 1
    user.onboarding_completed = True
    await session.commit()
    return await get_profile(session, user_id)


async def update_profile(session: AsyncSession, user_id: UUID, command: AthleteProfileUpdate) -> AthleteProfileView:
    profile = await session.scalar(
        select(AthleteProfile)
        .where(AthleteProfile.user_id == user_id)
        .with_for_update()
    )
    if profile is None:
        raise ProblemError(404, "athlete_not_found", "Runner profile not found", "Complete onboarding first.")
    if profile.version != command.expected_version:
        raise ProblemError(409, "version_conflict", "Profile changed", "Reload your profile and try again.")
    fields = command.model_fields_set
    if "height_cm" in fields:
        profile.height_cm = command.height_cm
    if "weight_kg" in fields:
        profile.weight_kg = command.weight_kg
    if command.distance_unit is not None:
        profile.distance_unit = command.distance_unit
    profile.version += 1
    await session.commit()
    return await get_profile(session, user_id)

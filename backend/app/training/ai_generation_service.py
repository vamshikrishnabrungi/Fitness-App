"""AI backed training-plan generation.

The database owns the released sport priorities, templates, exercise catalogue,
prescription bounds, and safety metadata. This module turns that reviewed data
into a compact reference packet, asks the workout model to author the complete
four-week plan, and persists catalog references alongside plan-scoped generated
exercise definitions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, replace
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

from sqlalchemy import Integer, func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.app.athletes.models import AthleteGoal, AthleteProfile, AthleteSport
from backend.app.core.config import get_settings
from backend.app.core.ids import uuid7
from backend.app.core.openai_responses import OpenAIResponseError
from backend.app.core.problems import ProblemError
from backend.app.knowledge.models import Method, MethodEffect, MethodVersion
from backend.app.operations.outbox import enqueue_event

from .ai_selector import PROMPT_VERSION, RESPONSE_SCHEMA_VERSION, AIWorkoutProgram, build_generation_packet, get_workout_generation_provider
from .models import SessionCompletion, SessionItem, TrainingGenerationRun, TrainingPhase, TrainingPlan, TrainingSession, TrainingWeek
from .planner import (
    CandidateMethod,
    PlanInvariantError,
    PlannerInput,
    SessionDefinition,
    SlotDefinition,
    prepare_horizon,
)
from .reference_prescription import bind_prescription_to_method
from .reference_service import _load_reference_inputs


PLANNER_VERSION = "ai-full-program-v3"
LEVEL_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3}
MAIN_ROLES = frozenset({"primary_reference", "supporting_reference"})
WARMUP_CODES = ("world_s_greatest_stretch", "easy_mode_specific_raise", "a_skip")
COOLDOWN_CODES = ("standing_quadriceps_stretch", "calf_wall_stretch", "crossover_arm_stretch")
STRETCH_CODES = frozenset((*WARMUP_CODES[:1], *COOLDOWN_CODES))


def _clean_dose(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "reference_source"}


def _canonical_slot_id(template_id: UUID, week_number: int, block_type: str, group: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"runlete:{template_id}:{week_number}:{block_type}:{group}")


def _available_equipment(context: Any) -> frozenset[str]:
    return frozenset(set(context.equipment) | {"bodyweight"})


def _equipment_allowed(method_equipment: frozenset[str], available: frozenset[str]) -> bool:
    if not method_equipment or method_equipment <= {"bodyweight"} or "full_gym" in available:
        return True
    # Catalog rows sometimes contain optional/alternative equipment in one
    # array. Requiring one recorded item is safer than silently inventing gear.
    normalized = {item for item in method_equipment if not item.endswith("_optional")}
    return not normalized or bool(normalized & available)


def _environment_allowed(
    environments: frozenset[str],
    context: Any,
    *,
    code: str | None = None,
    block_type: str | None = None,
) -> bool:
    if not environments:
        return True
    available = set(context.environments)
    # Basic mobility and stretching are safe in any outdoor training space,
    # even when the runner's selected venue is road, trail, track, or field.
    outdoor = bool(available & {"road", "trail", "track", "field"})
    if block_type in {"warmup", "cooldown"} and code in STRETCH_CODES and outdoor:
        return True
    return "all" in environments or bool(environments & available)


def _method_allowed(
    method: Any,
    context: Any,
    *,
    codes: frozenset[str] | None = None,
    block_type: str | None = None,
) -> bool:
    if codes is not None and method.code not in codes:
        return False
    if LEVEL_RANK.get(method.minimum_level, 99) > LEVEL_RANK.get(context.athlete_level, 0):
        return False
    if method.sport_codes and context.sport_code not in method.sport_codes:
        return False
    if method.scope_codes and context.scope_code not in method.scope_codes:
        return False
    if method.applicable_modes and not ({"all", context.primary_mode} & set(method.applicable_modes)):
        return False
    available = _available_equipment(context)
    if not _equipment_allowed(method.equipment, available):
        return False
    if not _environment_allowed(method.environments, context, code=method.code, block_type=block_type):
        return False
    return True


def _candidate_from_reference(
    method: Any,
    bound: dict[str, Any],
    *,
    quality: str,
    role: str,
    template_code: str,
    details: MethodVersion | None = None,
    quality_tags: tuple[str, ...] = (),
) -> CandidateMethod:
    return CandidateMethod(
        id=method.method_id,
        code=method.code,
        quality=quality,
        role=role,
        equipment=frozenset(),
        environments=frozenset(),
        level_rank=LEVEL_RANK.get(method.minimum_level, 3),
        technical_cost=method.technical_cost,
        impact_cost=method.impact_cost,
        fatigue_cost=method.fatigue_cost,
        dose_units=frozenset(bound),
        method_version=method.method_version,
        name=method.name,
        equipment_codes=method.equipment,
        instruction_steps=tuple(details.instructions) if details else (),
        coaching_cues=tuple(details.cues) if details else (),
        common_errors=tuple(details.common_errors) if details else (),
        safety_boundaries=tuple(details.safety_boundaries) if details else tuple(method.safety_boundaries),
        source_template_code=template_code,
        selection_tags=(
            {
                "qualities": list(quality_tags),
                "equipment": sorted(method.equipment),
                "environments": sorted(method.environments),
                "method_type": details.method_type,
                "movement_pattern": details.movement_pattern,
                "surfaces": list(details.surfaces),
                "force_directions": list(details.force_directions),
                "contractions": list(details.contractions),
                "speed_intent": details.speed_intent,
                "supervision_required": details.supervision_required,
            }
            if details else {"qualities": list(quality_tags)}
        ),
    )


async def _catalog_methods(session: AsyncSession, codes: tuple[str, ...]) -> dict[str, tuple[MethodVersion, str]]:
    rows = (await session.execute(
        select(MethodVersion, Method.code)
        .join(Method, Method.id == MethodVersion.method_id)
        .where(
            Method.code.in_(codes),
            MethodVersion.content_version == Method.latest_version,
            MethodVersion.status == "released",
            MethodVersion.generator_eligible.is_(True),
        )
    )).all()
    return {code: (version, code) for version, code in rows}


def _catalog_candidate(
    version: MethodVersion,
    code: str,
    *,
    quality: str,
    role: str,
    quality_tags: tuple[str, ...] = (),
) -> CandidateMethod:
    return CandidateMethod(
        id=version.method_id,
        code=code,
        quality=quality,
        role=role,
        equipment=frozenset(),
        environments=frozenset(),
        level_rank=LEVEL_RANK.get(version.level_minimum, 3),
        technical_cost=version.technical_cost,
        impact_cost=version.impact_cost,
        fatigue_cost=version.fatigue_cost,
        dose_units=frozenset({"sets", "duration_seconds"}),
        method_version=version.content_version,
        name=version.canonical_name,
        equipment_codes=frozenset(version.equipment_codes),
        instruction_steps=tuple(version.instructions),
        coaching_cues=tuple(version.cues),
        common_errors=tuple(version.common_errors),
        safety_boundaries=tuple(version.safety_boundaries),
        selection_tags={
            "qualities": list(quality_tags),
            "equipment": list(version.equipment_codes),
            "environments": list(version.environments),
            "method_type": version.method_type,
            "movement_pattern": version.movement_pattern,
            "surfaces": list(version.surfaces),
            "force_directions": list(version.force_directions),
            "contractions": list(version.contractions),
            "speed_intent": version.speed_intent,
            "supervision_required": version.supervision_required,
        },
    )


async def _supplemental_methods(
    session: AsyncSession,
    context: Any,
    quality_codes: set[str],
) -> list[CandidateMethod]:
    """Load a bounded quality-matched pool beyond the reference templates.

    This is the hybrid portion of generation: sport templates establish the
    required qualities and dose shapes, while the coach may choose another
    released exercise that satisfies the same quality, level, equipment,
    environment, and dose contract.
    """
    if not quality_codes:
        return []
    rows = (await session.execute(
        select(MethodVersion, Method.code, MethodEffect.quality_code)
        .join(Method, Method.id == MethodVersion.method_id)
        .join(
            MethodEffect,
            (MethodEffect.method_id == MethodVersion.method_id)
            & (MethodEffect.method_version == MethodVersion.content_version),
        )
        .where(
            MethodVersion.content_version == Method.latest_version,
            MethodVersion.status == "released",
            MethodVersion.generator_eligible.is_(True),
            MethodEffect.quality_code.in_(quality_codes),
        )
        .order_by(
            MethodEffect.quality_code,
            MethodVersion.technical_cost,
            MethodVersion.impact_cost,
            MethodVersion.fatigue_cost,
            Method.code,
        )
    )).all()
    grouped: dict[str, list[CandidateMethod]] = defaultdict(list)
    for version, code, quality_code in rows:
        if LEVEL_RANK.get(version.level_minimum, 99) > LEVEL_RANK.get(context.athlete_level, 0):
            continue
        equipment = frozenset(version.equipment_codes)
        environments = frozenset(version.environments)
        if not _equipment_allowed(equipment, _available_equipment(context)):
            continue
        if not _environment_allowed(environments, context, code=code, block_type="main_work"):
            continue
        grouped[quality_code].append(CandidateMethod(
            id=version.method_id,
            code=code,
            quality=quality_code,
            role="primary",
            equipment=frozenset(),
            environments=frozenset(),
            level_rank=LEVEL_RANK.get(version.level_minimum, 3),
            technical_cost=version.technical_cost,
            impact_cost=version.impact_cost,
            fatigue_cost=version.fatigue_cost,
            dose_units=frozenset(version.accepted_dose_units),
            method_version=version.content_version,
            name=version.canonical_name,
            equipment_codes=equipment,
            instruction_steps=tuple(version.instructions),
            coaching_cues=tuple(version.cues),
            common_errors=tuple(version.common_errors),
            safety_boundaries=tuple(version.safety_boundaries),
            source_template_code=None,
            selection_tags={
                "qualities": [quality_code],
                "equipment": list(version.equipment_codes),
                "environments": list(version.environments),
                "method_type": version.method_type,
                "movement_pattern": version.movement_pattern,
                "surfaces": list(version.surfaces),
                "force_directions": list(version.force_directions),
                "contractions": list(version.contractions),
                "speed_intent": version.speed_intent,
                "supervision_required": version.supervision_required,
                "source": "released_quality_matched_supplement",
            },
        ))
    return [method for quality in sorted(grouped) for method in grouped[quality][:12]]


def _template_slots(
    template: Any,
    week_number: int,
    context: Any,
    *,
    block_type: str,
    method_details: dict[tuple[UUID, int], MethodVersion] | None = None,
    method_quality_tags: dict[tuple[UUID, int], tuple[str, ...]] | None = None,
) -> list[tuple[SlotDefinition, list[CandidateMethod]]]:
    week = next((item for item in template.weeks if item.week_number == week_number), template.weeks[0])
    grouped: dict[tuple[str, ...], list[tuple[Any, dict[str, Any]]]] = defaultdict(list)
    for reference_method in template.methods:
        if block_type == "main_work" and reference_method.block_role not in MAIN_ROLES:
            continue
        if block_type == "warmup" and reference_method.block_role != "preparation":
            continue
        if not _method_allowed(reference_method, context, block_type=block_type):
            continue
        try:
            bound = _clean_dose(bind_prescription_to_method(week.prescription, reference_method.accepted_dose_units))
        except (TypeError, ValueError):
            continue
        grouped[tuple(sorted(bound))].append((reference_method, bound))
    output: list[tuple[SlotDefinition, list[CandidateMethod]]] = []
    for group_index, key in enumerate(sorted(grouped)):
        rows = grouped[key]
        dose = rows[0][1]
        candidates = [
            _candidate_from_reference(
                row,
                bound,
                quality=template.category_code,
                role="primary",
                template_code=template.code,
                details=(method_details or {}).get((row.method_id, row.method_version)),
                quality_tags=(method_quality_tags or {}).get((row.method_id, row.method_version), ()),
            )
            for row, bound in rows
        ]
        # A reviewed template may carry a primary method plus several
        # supporting exercises. Ask the model for up to two distinct methods
        # from that exact bounded set so a long session is not reduced to one
        # movement while still preventing catalogue invention.
        slot_count = min(2, len(rows)) if block_type == "main_work" else 1
        for slot_offset in range(slot_count):
            slot = SlotDefinition(
                id=_canonical_slot_id(template.template_id, week_number, block_type, group_index * 2 + slot_offset),
                code=f"{template.code}:{block_type}:{group_index + 1}:{slot_offset + 1}",
                quality=template.category_code,
                role="primary",
                block_type=block_type,
                dose=dose,
                metadata={
                    "template_id": str(template.template_id),
                    "template_version": template.template_version,
                    "template_code": template.code,
                    "category_code": template.category_code,
                    "purpose": template.purpose,
                    "reference_week": week_number,
                    "week_intent": week.intent,
                    "progression_condition": week.progression_condition,
                    "regression_condition": week.regression_condition,
                    "week_4_policy": template.week_4_policy if week_number == 4 else None,
                    "slot_index": slot_offset + 1,
                    "slot_count": slot_count,
                },
            )
            output.append((slot, candidates))
    return output


def _catalog_slots(
    catalog: dict[str, tuple[MethodVersion, str]],
    codes: tuple[str, ...],
    *,
    block_type: str,
    context: Any | None = None,
    method_quality_tags: dict[tuple[UUID, int], tuple[str, ...]] | None = None,
) -> list[tuple[SlotDefinition, list[CandidateMethod]]]:
    candidates: list[CandidateMethod] = []
    for code in codes:
        row = catalog.get(code)
        if row is None:
            continue
        version, name = row
        if context is not None:
            equipment = frozenset(version.equipment_codes)
            environments = frozenset(version.environments)
            if not _equipment_allowed(equipment, _available_equipment(context)):
                continue
            if not _environment_allowed(environments, context, code=code, block_type=block_type):
                continue
        candidates.append(_catalog_candidate(
            version,
            name,
            quality=block_type,
            role=block_type,
            quality_tags=(method_quality_tags or {}).get((version.method_id, version.content_version), ()),
        ))
    if not candidates:
        return []
    slot = SlotDefinition(
        id=uuid5(NAMESPACE_URL, f"runlete:catalog:{block_type}"),
        code=f"catalog:{block_type}",
        quality=block_type,
        role=block_type,
        block_type=block_type,
        dose={"sets": 1, "duration_seconds": {"minimum": 20, "maximum": 60, "step": 5}},
        metadata={"source": "released_exercise_catalog", "catalog_codes": list(codes)},
    )
    return [(slot, candidates)]


def _next_occurrence(start: date, weekday: int, week: int) -> date:
    offset = (weekday - start.weekday()) % 7
    return start + timedelta(days=offset + week * 7)


def _context_snapshot(context: Any, priority: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    return {
        "sport_code": context.sport_code,
        "scope_code": context.scope_code,
        "phase_code": context.phase_code,
        "goal_code": context.goal_code,
        "athlete_level": context.athlete_level,
        "maximum_session_minutes": context.maximum_session_minutes,
        "availability": [
            {
                "weekday": item.weekday,
                "start_minute": item.start_minute,
                "duration_minutes": item.duration_minutes,
                "environments": sorted(item.environments),
            }
            for item in context.availability
        ],
        "equipment": sorted(context.equipment),
        "environments": sorted(context.environments),
        "external_hard_dates": sorted(value.isoformat() for value in context.external_hard_dates),
        "priority": {
            "primary_category": priority.primary_category,
            "block_order": list(priority.block_order),
            "ranked_categories": [asdict(item) for item in priority.ranked_categories],
        },
        "overrides": overrides,
    }


def _program_warnings(program: AIWorkoutProgram, packet: dict[str, Any]) -> list[str]:
    """Return concise semantic issues for the single model repair attempt.

    The structured-output schema handles shape and type correctness. These
    checks provide feedback to the model but do not rewrite or reject its plan.
    """
    warnings: list[str] = []
    requirements = packet["output_requirements"]
    expected_sessions = requirements["sessions_per_week"]
    duration_ceilings = {
        item["scheduled_for"]: item["duration_minutes"]
        for item in packet["reference_templates_and_schedule"]
    }
    catalog = {
        (value["method_id"], value["method_version"])
        for value in packet["candidate_catalog"].values()
    }
    definitions = {item.generated_exercise_id for item in program.generated_exercises}
    if [week.week_number for week in program.weeks] != [1, 2, 3, 4]:
        warnings.append("weeks must be numbered exactly 1, 2, 3, 4")
    for week in program.weeks:
        if len(week.sessions) != expected_sessions:
            warnings.append(f"week {week.week_number} must contain exactly {expected_sessions} sessions")
        for planned in week.sessions:
            block_minutes = sum(block.estimated_minutes for block in planned.blocks)
            ceiling = duration_ceilings.get(planned.scheduled_for)
            if block_minutes != planned.estimated_minutes or ceiling is None or planned.estimated_minutes > ceiling:
                warnings.append(
                    f"week {week.week_number} session {planned.session_number} must not exceed its {ceiling}-minute ceiling; "
                    f"session={planned.estimated_minutes}, blocks={block_minutes}"
                )
            for block in planned.blocks:
                for occurrence in block.exercises:
                    reference = occurrence.exercise
                    if reference.source == "catalog" and (str(reference.method_id), reference.method_version) not in catalog:
                        warnings.append(f"unknown catalog exercise {reference.method_id}:{reference.method_version}")
                    if reference.source == "generated" and reference.generated_exercise_id not in definitions:
                        warnings.append(f"missing generated exercise definition {reference.generated_exercise_id}")
    return list(dict.fromkeys(warnings))


async def generate_ai_plan(
    session: AsyncSession,
    user_id: UUID,
    weeks: int,
    starts_on: date | None,
    *,
    fitness_level: str | None = None,
    training_days_per_week: int | None = None,
    health_context: dict[str, Any] | None = None,
    schedule_constraints: str | None = None,
) -> Any:
    settings = get_settings()
    if not settings.generation_enabled:
        raise ProblemError(503, "generation_disabled", "Training generation is paused", "Enable training generation to create a plan.")
    if weeks != 4:
        raise ProblemError(422, "invalid_plan_duration", "Invalid duration", "Plans currently use a four-week progression.")
    athlete = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if athlete is None:
        raise ProblemError(409, "onboarding_required", "Onboarding required", "Complete onboarding first.")
    advisory_key = int.from_bytes(athlete.id.bytes[:8], byteorder="big", signed=True)
    await session.execute(select(func.pg_advisory_xact_lock(advisory_key)))
    primary = await session.scalar(select(AthleteSport).where(AthleteSport.athlete_id == athlete.id, AthleteSport.is_primary.is_(True)))
    goal = await session.scalar(select(AthleteGoal).where(AthleteGoal.athlete_id == athlete.id, AthleteGoal.status == "active").order_by(AthleteGoal.priority, AthleteGoal.created_at))
    if primary is None or goal is None:
        raise ProblemError(409, "planning_inputs_incomplete", "Planning inputs incomplete", "A primary sport and active goal are required.")
    normalized_start = starts_on or (date.today() + timedelta(days=(7 - date.today().weekday()) % 7))
    try:
        context, priority, templates_by_category, dataset_hash, content_release_id = await _load_reference_inputs(
            session,
            athlete=athlete,
            primary=primary,
            goal=goal,
            starts_on=normalized_start,
            athlete_level_override=fitness_level,
        )
    except (ValueError, RuntimeError) as exc:
        raise ProblemError(422, "training_inputs_unresolved", "A safe plan could not be created", str(exc)) from exc

    chosen_level = fitness_level if fitness_level in LEVEL_RANK else context.athlete_level
    stored_health_context = dict(athlete.health_context_json or {})
    stored_health_context.update(health_context or {})
    previous_plan = await session.scalar(
        select(TrainingPlan)
        .where(TrainingPlan.athlete_id == athlete.id, TrainingPlan.status == "active")
        .order_by(TrainingPlan.plan_number.desc())
        .limit(1)
    )
    previous_block: dict[str, Any] | None = None
    if previous_plan is not None and normalized_start > previous_plan.starts_on:
        planned_sessions = int(await session.scalar(
            select(func.count(TrainingSession.id))
            .join(TrainingWeek, TrainingWeek.id == TrainingSession.week_id)
            .where(TrainingWeek.plan_id == previous_plan.id)
        ) or 0)
        completion_row = (await session.execute(
            select(
                func.count(SessionCompletion.id),
                func.avg(SessionCompletion.completion_ratio),
                func.avg(SessionCompletion.session_rpe),
                func.sum(func.cast(SessionCompletion.pain_flag, Integer)),
            )
            .join(TrainingSession, TrainingSession.id == SessionCompletion.session_id)
            .join(TrainingWeek, TrainingWeek.id == TrainingSession.week_id)
            .where(TrainingWeek.plan_id == previous_plan.id)
        )).one()
        completed_sessions = int(completion_row[0] or 0)
        previous_block = {
            "plan_number": previous_plan.plan_number,
            "starts_on": previous_plan.starts_on.isoformat(),
            "ends_on": previous_plan.ends_on.isoformat(),
            "planned_sessions": planned_sessions,
            "completed_sessions": completed_sessions,
            "session_adherence": round(completed_sessions / planned_sessions, 3) if planned_sessions else 0,
            "average_completion_ratio": round(float(completion_row[1]), 3) if completion_row[1] is not None else None,
            "average_session_rpe": round(float(completion_row[2]), 2) if completion_row[2] is not None else None,
            "pain_flagged_sessions": int(completion_row[3] or 0),
        }
    additional_context = {
        "fitness_level": chosen_level,
        "competition_level": athlete.competition_level,
        "height_cm": float(athlete.height_cm) if athlete.height_cm is not None else None,
        "weight_kg": float(athlete.weight_kg) if athlete.weight_kg is not None else None,
        "season_phase": context.phase_code,
        "runner_baseline": {
            "experience": athlete.running_experience,
            "runs_per_week": athlete.runs_per_week,
            "weekly_distance_m": float(athlete.weekly_distance_m),
            "longest_recent_run_m": float(athlete.longest_recent_run_m),
            "recent_race_event": athlete.recent_race_event,
            "recent_race_time_seconds": athlete.recent_race_time_seconds,
            "training_interruption": athlete.training_interruption,
            "terrains": list(athlete.terrains),
            "distance_unit_preference": athlete.distance_unit,
            "target_event": goal.target_event,
            "target_distance_m": float(goal.target_distance_m) if goal.target_distance_m is not None else None,
            "target_time_seconds": goal.target_time_seconds,
        },
        "training_days_per_week": training_days_per_week,
        "health": stored_health_context,
        "schedule_constraints": schedule_constraints,
        "availability": [
            {
                "weekday": item.weekday,
                "start_minute": item.start_minute,
                "duration_minutes": item.duration_minutes,
                "environments": sorted(item.environments),
            }
            for item in context.availability
        ],
        "external_schedule": list(context.external_schedule),
        "readiness": context.readiness,
        "acute_illness": context.acute_illness,
        "scenario_codes": sorted(context.scenario_codes),
        "competition_dates": [value.isoformat() for value in context.competition_dates],
        "days_to_competition": context.days_to_competition,
        "previous_four_week_block": previous_block,
        "sport_requirements": [asdict(item) for item in priority.ranked_categories],
        "phase_policy": {
            "progression_mode": context.phase_policy.progression_mode,
            "weekly_volume_multipliers": list(context.phase_policy.weekly_volume_multipliers),
            "novelty_policy": context.phase_policy.novelty_policy,
        },
    }
    context = replace(context, athlete_level=chosen_level)
    max_sessions = context.phase_policy.maximum_sessions_per_week
    desired_sessions = training_days_per_week or len(context.availability)
    session_count = max(1, min(desired_sessions, len(context.availability), max_sessions))
    windows = sorted(context.availability, key=lambda item: (item.weekday, item.start_minute))[:session_count]

    selected_templates: list[Any] = []
    for ranked in priority.ranked_categories:
        templates = templates_by_category.get(ranked.category_code, ())
        if templates:
            selected_templates.append(templates[0])
        if len(selected_templates) >= context.phase_policy.maximum_categories:
            break
    if not selected_templates:
        raise ProblemError(422, "training_templates_unresolved", "No compatible training templates", "There are no released templates for this sport and level.")
    preparation_templates = templates_by_category.get("performance_preparation", ())
    catalog = await _catalog_methods(session, WARMUP_CODES + COOLDOWN_CODES)
    reference_keys = {
        (method.method_id, method.method_version)
        for template in (*selected_templates, *(preparation_templates[:1]))
        for method in template.methods
    }
    method_details: dict[tuple[UUID, int], MethodVersion] = {}
    if reference_keys:
        rows = (await session.scalars(
            select(MethodVersion).where(tuple_(MethodVersion.method_id, MethodVersion.content_version).in_(reference_keys))
        )).all()
        method_details = {(row.method_id, row.content_version): row for row in rows}
    quality_keys = reference_keys | {
        (version.method_id, version.content_version)
        for version, _code in catalog.values()
    }
    method_quality_tags: dict[tuple[UUID, int], tuple[str, ...]] = defaultdict(tuple)
    if quality_keys:
        quality_rows = (await session.execute(
            select(MethodEffect.method_id, MethodEffect.method_version, MethodEffect.quality_code)
            .where(tuple_(MethodEffect.method_id, MethodEffect.method_version).in_(quality_keys))
            .order_by(MethodEffect.method_id, MethodEffect.method_version, MethodEffect.quality_code)
        )).all()
        grouped_quality_tags: dict[tuple[UUID, int], list[str]] = defaultdict(list)
        for method_id, method_version, quality_code in quality_rows:
            grouped_quality_tags[(method_id, method_version)].append(quality_code)
        method_quality_tags = {
            key: tuple(dict.fromkeys(values))
            for key, values in grouped_quality_tags.items()
        }

    methods = await _supplemental_methods(
        session,
        context,
        {template.category_code for template in selected_templates},
    )
    scheduled_definitions: list[tuple[datetime, SessionDefinition]] = []
    try:
        zone = ZoneInfo(athlete.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ProblemError(422, "invalid_timezone", "Invalid timezone", "The athlete timezone is not a valid IANA timezone.") from exc
    for week_index in range(weeks):
        week_number = week_index + 1
        for sequence, window in enumerate(windows, 1):
            scheduled_date = _next_occurrence(normalized_start, window.weekday, week_index)
            scheduled_for = datetime.combine(
                scheduled_date,
                datetime.min.time().replace(hour=window.start_minute // 60, minute=window.start_minute % 60),
                zone,
            ).astimezone(timezone.utc)
            slots: list[SlotDefinition] = []
            slot_candidates: list[CandidateMethod] = []
            warmup = _template_slots(
                preparation_templates[0],
                week_number,
                context,
                block_type="warmup",
                method_details=method_details,
                method_quality_tags=method_quality_tags,
            ) if preparation_templates else []
            if warmup:
                slots.append(warmup[0][0])
                slot_candidates.extend(warmup[0][1])
            else:
                fallback = _catalog_slots(
                    catalog,
                    WARMUP_CODES,
                    block_type="warmup",
                    context=context,
                    method_quality_tags=method_quality_tags,
                )
                if fallback:
                    slots.append(fallback[0][0])
                    slot_candidates.extend(fallback[0][1])
            for template in selected_templates:
                for slot, candidates in _template_slots(
                    template,
                    week_number,
                    context,
                    block_type="main_work",
                    method_details=method_details,
                    method_quality_tags=method_quality_tags,
                ):
                    slots.append(slot)
                    slot_candidates.extend(candidates)
            cooldown = _catalog_slots(
                catalog,
                COOLDOWN_CODES,
                block_type="cooldown",
                context=context,
                method_quality_tags=method_quality_tags,
            )
            if cooldown:
                slots.append(cooldown[0][0])
                slot_candidates.extend(cooldown[0][1])
            if not slots:
                raise ProblemError(422, "training_slots_unresolved", "No compatible exercises", "The released exercise catalogue has no safe choices for this profile.")
            methods.extend(slot_candidates)
            definition = SessionDefinition(
                recipe_id=uuid5(NAMESPACE_URL, f"runlete:ai:{primary.sport_code}:{week_number}:{sequence}"),
                session_type="ai_training",
                purpose=f"AI-selected {primary.sport_code.replace('_', ' ')} training",
                load_class="moderate",
                estimated_minutes=window.duration_minutes,
                slots=tuple(slots),
                recipe_version=1,
                phase_code=context.phase_code,
                metadata={
                    "sport_code": primary.sport_code,
                    "goal_code": context.goal_code,
                    "selected_template_codes": [template.code for template in selected_templates],
                    "selection": "openai_constrained_to_released_candidates",
                },
            )
            scheduled_definitions.append((scheduled_for, definition))

    # CandidateMethod IDs repeat across weeks by design. The validator permits
    # that, while the session-level duplicate guard still prevents an exercise
    # from being selected twice in one session.
    planner_input = PlannerInput(
        athlete_id=athlete.id,
        level_rank=LEVEL_RANK[chosen_level],
        goal_code=context.goal_code,
        primary_sport=primary.sport_code,
        event_code=primary.event_code,
        role_code=primary.role_code,
        target_date=goal.target_date,
        available_slots=tuple((item.weekday, item.start_minute, item.duration_minutes) for item in context.availability),
        equipment=frozenset(context.equipment),
        environments=frozenset(context.environments),
        maximum_session_minutes=athlete.maximum_session_minutes,
        external_hard_days=frozenset(value.weekday() for value in context.external_hard_dates),
        pain_flag=context.pain_unresolved,
        content_release_id=content_release_id,
        starts_on=normalized_start,
        discipline_code=primary.discipline_code,
        format_code=primary.format_code,
        weight_class_code=primary.weight_class_code,
        athlete_context=additional_context,
    )
    try:
        draft = prepare_horizon(planner_input, scheduled_definitions, methods)
    except PlanInvariantError as exc:
        raise ProblemError(422, "training_plan_unresolved", "A safe plan could not be created", str(exc)) from exc

    existing = await session.scalar(select(TrainingPlan).where(
        TrainingPlan.athlete_id == athlete.id,
        TrainingPlan.input_hash == draft.input_hash,
        TrainingPlan.dataset_hash == dataset_hash,
        TrainingPlan.planner_version == PLANNER_VERSION,
    ))
    if existing is not None:
        if existing.status != "active":
            await session.execute(
                update(TrainingPlan)
                .where(TrainingPlan.athlete_id == athlete.id, TrainingPlan.status == "active")
                .values(status="superseded")
            )
            existing.status = "active"
            await session.commit()
        from backend.app.training.service import plan_view
        return await plan_view(session, existing.id, athlete.id)

    packet = build_generation_packet(planner_input, draft)
    # OpenAI generation can take longer than Cloud SQL's idle-in-transaction
    # timeout. Release the read transaction before the network call; the
    # accepted response is validated against this immutable packet and all
    # writes happen in a fresh transaction below.
    await session.commit()
    provider = get_workout_generation_provider()
    selected_result = None
    validation_warnings: list[str] = []
    for attempt in range(1, 3):
        try:
            repair_context = None
            if attempt == 2:
                repair_context = {
                    "validation_issues": validation_warnings,
                    "previous_program": selected_result.output.model_dump(mode="json") if selected_result else None,
                }
            candidate_result = await provider.generate(packet=packet, repair_context=repair_context)
            candidate_warnings = _program_warnings(candidate_result.output, packet)
            selected_result = candidate_result
            validation_warnings = candidate_warnings
            if not candidate_warnings or attempt == 2:
                break
        except OpenAIResponseError as exc:
            raise ProblemError(502, "ai_generation_failed", "Workout generation failed", str(exc)) from exc
        except ValueError as exc:
            raise ProblemError(
                502,
                "ai_generation_failed",
                "Workout generation failed",
                "The coach model returned a response that could not be displayed. Please try again.",
            ) from exc
    if selected_result is None:
        raise ProblemError(502, "ai_generation_failed", "Workout generation failed", "The workout model did not return a usable plan.")

    input_snapshot = _context_snapshot(context, priority, additional_context)
    input_snapshot["templates"] = [template.code for template in selected_templates]
    input_snapshot["session_count_per_week"] = session_count
    input_snapshot["generation"] = {"provider": selected_result.provider, "model": selected_result.model_id, "prompt_version": PROMPT_VERSION}
    # A newly generated block replaces the current block. Older blocks remain
    # available for history and adaptation summaries, but only one can be active.
    await session.execute(
        update(TrainingPlan)
        .where(
            TrainingPlan.athlete_id == athlete.id,
            TrainingPlan.status == "active",
        )
        .values(status="superseded")
    )
    plan_number = int(await session.scalar(select(func.coalesce(func.max(TrainingPlan.plan_number), 0)).where(TrainingPlan.athlete_id == athlete.id)) or 0) + 1
    plan = TrainingPlan(
        id=uuid7(), athlete_id=athlete.id, plan_number=plan_number, status="active", goal_id=goal.id,
        content_release_id=content_release_id, dataset_hash=dataset_hash, planner_version=PLANNER_VERSION,
        input_hash=draft.input_hash, input_snapshot_json=input_snapshot, starts_on=draft.starts_on,
        ends_on=draft.ends_on, decision_trace_json=[{"decision": "ai_authored_full_program", "prompt_version": PROMPT_VERSION}],
        validation_json={"passed": not validation_warnings, "warnings": validation_warnings, "ai_used": True, "provider": selected_result.provider, "attempt_count": attempt},
        activated_at=datetime.now(timezone.utc), materialized_through=draft.ends_on, selection_horizon_weeks=4,
    )
    session.add(plan)
    await session.flush()
    phase = TrainingPhase(
        id=uuid7(), plan_id=plan.id, sequence=1, phase_code=context.phase_code,
        starts_on=plan.starts_on, ends_on=plan.ends_on,
        priority_vector_json={item.category_code: item.weight for item in priority.ranked_categories},
    )
    session.add(phase)
    await session.flush()
    weeks_by_number: dict[int, TrainingWeek] = {}
    generated_weeks = {week.week_number: week for week in selected_result.output.weeks}
    for week_number in range(1, weeks + 1):
        week_start = plan.starts_on + timedelta(days=(week_number - 1) * 7)
        generated_week = generated_weeks.get(week_number)
        row = TrainingWeek(
            id=uuid7(), plan_id=plan.id, phase_id=phase.id, week_number=week_number,
            starts_on=week_start, planned_load=0, deload=generated_week.deload if generated_week else False,
            structure_json={
                "intent": generated_week.theme if generated_week else "AI-generated training week",
                "progression_rule": generated_week.progression_rule if generated_week else "",
                "session_count": session_count,
                "ai_selected": True,
            },
            materialization_status="materialized",
        )
        session.add(row)
        weeks_by_number[week_number] = row
    await session.flush()
    generated_by_id = {item.generated_exercise_id: item.model_dump(mode="json") for item in selected_result.output.generated_exercises}
    session_rows: list[TrainingSession] = []
    item_rows: list[SessionItem] = []
    load_by_week: dict[int, int] = defaultdict(int)
    flattened_sessions = [item for week in selected_result.output.weeks for item in week.sessions]
    for sequence, planned in enumerate(flattened_sessions, 1):
        week_number = planned.week_number
        try:
            scheduled_for = datetime.fromisoformat(planned.scheduled_for.replace("Z", "+00:00"))
        except ValueError:
            scheduled_for = draft.sessions[sequence - 1].scheduled_for if sequence <= len(draft.sessions) else datetime.combine(plan.starts_on + timedelta(days=(week_number - 1) * 7), datetime.min.time(), timezone.utc)
        session_row = TrainingSession(
            id=uuid7(), week_id=weeks_by_number[week_number].id, athlete_id=athlete.id,
            recipe_id=None, recipe_version=None, sequence=((sequence - 1) % session_count) + 1,
            scheduled_for=scheduled_for, session_type="ai_training", purpose=planned.purpose,
            estimated_minutes=planned.estimated_minutes, load_class=planned.load_class,
            venue_code=None, status="scheduled",
            explanation=planned.title,
        )
        session_rows.append(session_row)
        occurrences = [(block, occurrence) for block in planned.blocks for occurrence in block.exercises]
        load_by_week[week_number] += len(occurrences)
        for item_sequence, (block, planned_item) in enumerate(occurrences, 1):
            reference = planned_item.exercise
            is_catalog = reference.source == "catalog"
            generated = None if is_catalog else generated_by_id.get(reference.generated_exercise_id)
            prescription = dict(planned_item.prescription)
            prescription["estimated_minutes"] = planned_item.estimated_minutes
            if planned_item.circuit is not None:
                prescription["circuit"] = planned_item.circuit.model_dump(mode="json")
            item_rows.append(SessionItem(
                id=uuid7(), session_id=session_row.id,
                method_id=reference.method_id if is_catalog else None,
                method_version=reference.method_version if is_catalog else None,
                generated_exercise_json=generated, slot_id=None, sequence=item_sequence,
                block_type=block.block_type, prescription_json=prescription,
                substitution_methods_json=[],
                decision_trace_json=[{"ai": True, "source": reference.source, "coaching_note": planned_item.coaching_note}],
            ))
    session.add_all(session_rows)
    await session.flush()
    session.add_all(item_rows)
    for week_number, row in weeks_by_number.items():
        row.planned_load = load_by_week[week_number]
    generation_run = TrainingGenerationRun(
        id=uuid7(), athlete_id=athlete.id, content_release_id=content_release_id, plan_id=plan.id,
        horizon_starts_on=draft.starts_on, horizon_ends_on=draft.ends_on,
        provider=selected_result.provider, model_id=selected_result.model_id,
        prompt_version=PROMPT_VERSION, response_schema_version=RESPONSE_SCHEMA_VERSION,
        planner_version=PLANNER_VERSION, input_hash=draft.input_hash, status="accepted",
        attempt_count=attempt, latency_ms=selected_result.latency_ms,
        input_tokens=selected_result.input_tokens, output_tokens=selected_result.output_tokens,
        accepted_output_json=selected_result.output.model_dump(mode="json"),
        validation_json={"passed": not validation_warnings, "warnings": validation_warnings},
    )
    session.add(generation_run)
    await enqueue_event(
        session, aggregate_type="training_plan", aggregate_id=plan.id, event_type="training.plan.created",
        payload={"plan_id": str(plan.id), "athlete_id": str(athlete.id), "ai_generated": True, "generation_run_id": str(generation_run.id)},
    )
    await session.commit()
    from backend.app.training.service import plan_view
    return await plan_view(session, plan.id, athlete.id)

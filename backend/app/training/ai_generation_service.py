"""AI backed training-plan generation.

The database owns the released sport priorities, templates, exercise catalogue,
prescription bounds, and safety metadata. This module turns that reviewed data
into a bounded selection packet, asks the workout model to choose methods, and
persists only selections that pass the domain validator. No workout choice is
made by a deterministic compiler.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, replace
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

from sqlalchemy import func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.app.athletes.models import AthleteGoal, AthleteProfile, AthleteSport
from backend.app.core.config import get_settings
from backend.app.core.ids import uuid7
from backend.app.core.openai_responses import OpenAIResponseError
from backend.app.core.problems import ProblemError
from backend.app.knowledge.models import Method, MethodVersion
from backend.app.operations.outbox import enqueue_event

from .ai_selector import PROMPT_VERSION, RESPONSE_SCHEMA_VERSION, build_selection_packet, get_workout_selection_provider
from .models import SessionItem, TrainingGenerationRun, TrainingPhase, TrainingPlan, TrainingSession, TrainingWeek
from .planner import (
    CandidateMethod,
    PlanInvariantError,
    PlannerInput,
    SessionDefinition,
    SlotDefinition,
    finalize_plan,
    prepare_horizon,
)
from .reference_prescription import bind_prescription_to_method
from .reference_service import _load_reference_inputs


PLANNER_VERSION = "ai-selection-v1"
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
    if "gym" in available:
        available.add("combat_gym")
    if "combat_gym" in available:
        available.add("gym")
    # Basic mobility and stretching are safe in any outdoor training space,
    # even when the athlete's selected sport venue is road, track, or court.
    outdoor = bool(available & {"road", "trail", "track", "field", "court"})
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
) -> CandidateMethod:
    return CandidateMethod(
        id=method.method_id,
        code=method.code,
        quality=quality,
        role=role,
        equipment=frozenset(),
        environments=frozenset(method.environments),
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


def _catalog_candidate(version: MethodVersion, code: str, *, quality: str, role: str) -> CandidateMethod:
    return CandidateMethod(
        id=version.method_id,
        code=code,
        quality=quality,
        role=role,
        equipment=frozenset(),
        environments=frozenset(version.environments),
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
    )


def _template_slots(
    template: Any,
    week_number: int,
    context: Any,
    *,
    block_type: str,
    method_details: dict[tuple[UUID, int], MethodVersion] | None = None,
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
        candidates.append(_catalog_candidate(version, name, quality=block_type, role=block_type))
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
            session, athlete=athlete, primary=primary, goal=goal, starts_on=normalized_start
        )
    except (ValueError, RuntimeError) as exc:
        raise ProblemError(422, "training_inputs_unresolved", "A safe plan could not be created", str(exc)) from exc

    chosen_level = fitness_level if fitness_level in LEVEL_RANK else context.athlete_level
    additional_context = {
        "fitness_level": chosen_level,
        "training_days_per_week": training_days_per_week,
        "health": health_context or {},
        "schedule_constraints": schedule_constraints,
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

    methods: list[CandidateMethod] = []
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
            ) if preparation_templates else []
            if warmup:
                slots.append(warmup[0][0])
                slot_candidates.extend(warmup[0][1])
            else:
                fallback = _catalog_slots(catalog, WARMUP_CODES, block_type="warmup", context=context)
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
                ):
                    slots.append(slot)
                    slot_candidates.extend(candidates)
            cooldown = _catalog_slots(catalog, COOLDOWN_CODES, block_type="cooldown", context=context)
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
                estimated_minutes=athlete.maximum_session_minutes,
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
        equipment=frozenset(),
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

    packet = build_selection_packet(planner_input, draft)
    provider = get_workout_selection_provider()
    validation_errors: list[str] | None = None
    selected_result = None
    result = None
    for attempt in range(1, 3):
        try:
            selected_result = await provider.select(packet=packet, validation_errors=validation_errors)
            result = finalize_plan(draft, selected_result.output.to_domain())
            break
        except OpenAIResponseError as exc:
            raise ProblemError(502, "ai_generation_failed", "Workout generation failed", str(exc)) from exc
        except (PlanInvariantError, ValueError) as exc:
            validation_errors = [str(exc)]
            if attempt == 2:
                raise ProblemError(422, "ai_selection_unresolved", "The workout model returned an unsafe selection", str(exc)) from exc
    if result is None or selected_result is None:
        raise ProblemError(502, "ai_generation_failed", "Workout generation failed", "The workout model did not return a usable plan.")

    input_snapshot = _context_snapshot(context, priority, additional_context)
    input_snapshot["templates"] = [template.code for template in selected_templates]
    input_snapshot["session_count_per_week"] = session_count
    input_snapshot["generation"] = {"provider": selected_result.provider, "model": selected_result.model_id, "prompt_version": PROMPT_VERSION}
    # A newly generated plan replaces any older reference or legacy plan for
    # the athlete. Its rows remain available for audit/history, but cannot be
    # mistaken for the current program by the mobile client.
    await session.execute(
        update(TrainingPlan)
        .where(
            TrainingPlan.athlete_id == athlete.id,
            TrainingPlan.status == "active",
            TrainingPlan.planner_version != PLANNER_VERSION,
        )
        .values(status="superseded")
    )
    existing = await session.scalar(select(TrainingPlan).where(
        TrainingPlan.athlete_id == athlete.id,
        TrainingPlan.input_hash == result.input_hash,
        TrainingPlan.dataset_hash == dataset_hash,
        TrainingPlan.planner_version == PLANNER_VERSION,
    ))
    if existing is not None:
        await session.commit()
        from backend.app.training.service import plan_view
        return await plan_view(session, existing.id, athlete.id)
    plan_number = int(await session.scalar(select(func.coalesce(func.max(TrainingPlan.plan_number), 0)).where(TrainingPlan.athlete_id == athlete.id)) or 0) + 1
    plan = TrainingPlan(
        id=uuid7(), athlete_id=athlete.id, plan_number=plan_number, status="active", goal_id=goal.id,
        content_release_id=content_release_id, dataset_hash=dataset_hash, planner_version=PLANNER_VERSION,
        input_hash=result.input_hash, input_snapshot_json=input_snapshot, starts_on=result.starts_on,
        ends_on=result.ends_on, decision_trace_json=result.trace,
        validation_json={"passed": True, "ai_used": True, "provider": selected_result.provider, "attempt_count": attempt},
        activated_at=datetime.now(timezone.utc), materialized_through=result.ends_on, selection_horizon_weeks=4,
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
    for week_number in range(1, weeks + 1):
        week_start = plan.starts_on + timedelta(days=(week_number - 1) * 7)
        row = TrainingWeek(
            id=uuid7(), plan_id=plan.id, phase_id=phase.id, week_number=week_number,
            starts_on=week_start, planned_load=0, deload=False,
            structure_json={"intent": "AI-selected from released sport templates", "session_count": session_count, "ai_selected": True},
            materialization_status="materialized",
        )
        session.add(row)
        weeks_by_number[week_number] = row
    await session.flush()
    method_by_key = {(method.id, method.method_version): method for method in methods}
    session_rows: list[TrainingSession] = []
    item_rows: list[SessionItem] = []
    load_by_week: dict[int, int] = defaultdict(int)
    for sequence, planned in enumerate(result.sessions, 1):
        week_number = min(weeks, max(1, ((planned.scheduled_for.date() - plan.starts_on).days // 7) + 1))
        session_row = TrainingSession(
            id=uuid7(), week_id=weeks_by_number[week_number].id, athlete_id=athlete.id,
            recipe_id=None, recipe_version=None, sequence=((sequence - 1) % session_count) + 1,
            scheduled_for=planned.scheduled_for, session_type="ai_training", purpose=planned.definition.purpose,
            estimated_minutes=planned.definition.estimated_minutes, load_class=planned.definition.load_class,
            venue_code=None, status="scheduled",
            explanation="Selected by Runlete AI from the released sport templates and eligible exercise catalogue.",
        )
        session_rows.append(session_row)
        load_by_week[week_number] += len(planned.items)
        for item_sequence, planned_item in enumerate(planned.items, 1):
            method = method_by_key[(planned_item.method_id, planned_item.method_version)]
            item_rows.append(SessionItem(
                id=uuid7(), session_id=session_row.id, method_id=planned_item.method_id,
                method_version=planned_item.method_version, slot_id=None, sequence=item_sequence,
                block_type=planned_item.block_type, prescription_json=planned_item.prescription,
                substitution_methods_json=[{"id": str(value)} for value in planned_item.alternatives],
                decision_trace_json=planned_item.trace + [{"source_template_code": method.source_template_code, "ai": True}],
            ))
    session.add_all(session_rows)
    await session.flush()
    session.add_all(item_rows)
    for week_number, row in weeks_by_number.items():
        row.planned_load = load_by_week[week_number]
    generation_run = TrainingGenerationRun(
        id=uuid7(), athlete_id=athlete.id, content_release_id=content_release_id, plan_id=plan.id,
        horizon_starts_on=result.starts_on, horizon_ends_on=result.ends_on,
        provider=selected_result.provider, model_id=selected_result.model_id,
        prompt_version=PROMPT_VERSION, response_schema_version=RESPONSE_SCHEMA_VERSION,
        planner_version=PLANNER_VERSION, input_hash=result.input_hash, status="accepted",
        attempt_count=attempt, latency_ms=selected_result.latency_ms,
        input_tokens=selected_result.input_tokens, output_tokens=selected_result.output_tokens,
        accepted_output_json=selected_result.output.model_dump(mode="json"),
        validation_json={"passed": True, "errors": []},
    )
    session.add(generation_run)
    await enqueue_event(
        session, aggregate_type="training_plan", aggregate_id=plan.id, event_type="training.plan.created",
        payload={"plan_id": str(plan.id), "athlete_id": str(athlete.id), "ai_generated": True, "generation_run_id": str(generation_run.id)},
    )
    await session.commit()
    from backend.app.training.service import plan_view
    return await plan_view(session, plan.id, athlete.id)

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import (
    AthleteGoal,
    AthleteProfile,
    AthleteSport,
    AvailabilityWindow,
    EquipmentAccess,
    ExternalLoad,
)
from backend.app.core.config import get_settings
from backend.app.core.problems import ProblemError
from backend.app.health.models import PainReport
from backend.app.knowledge.models import (
    ContentRelease,
    Method,
    MethodEffect,
    MethodVersion,
    PhaseTemplate,
    PrescriptionRule,
    PrescriptionRuleVersion,
    ProgramArchetype,
    ProgramArchetypeVersion,
    Recipe,
    RecipeBlock,
    RecipeSlot,
    RecipeVersion,
    ReleaseItem,
    SportQualityPriority,
    WeekTemplate,
    WeekTemplateSession,
)
from backend.app.operations.outbox import enqueue_event

from .ai_selector import PROMPT_VERSION, RESPONSE_SCHEMA_VERSION, build_selection_packet, get_workout_selection_provider
from .models import (
    SessionCompletion,
    SessionItem,
    TrainingGenerationRun,
    TrainingPhase,
    TrainingPlan,
    TrainingSession,
    TrainingWeek,
)
from .planner import (
    PLANNER_VERSION,
    CandidateMethod,
    PlanInvariantError,
    PlannerInput,
    SessionDefinition,
    SlotDefinition,
    finalize_plan,
    prepare_horizon,
)
from .rules import RuleEvaluationError, apply_bounded_actions
from .schemas import CompletionCommand, PlanView, SessionItemView, SessionView


LEVEL_RANK = {
    "beginner": 1,
    "recreational": 1,
    "intermediate": 2,
    "club": 2,
    "regional": 3,
    "advanced": 3,
    "national": 3,
    "international": 4,
}


@dataclass(frozen=True)
class PhaseAllocation:
    code: str
    starts_on: date
    ends_on: date
    start_week: int
    week_count: int
    priorities: dict[str, float]


@dataclass(frozen=True)
class SportScope:
    sport_code: str
    event_code: str | None
    role_code: str | None
    discipline_code: str | None = None
    format_code: str | None = None
    weight_class_code: str | None = None


@dataclass(frozen=True)
class StructuredWeek:
    week_number: int
    starts_on: date
    phase_code: str
    deload: bool
    sessions: tuple[tuple[datetime, SessionDefinition], ...]


@dataclass(frozen=True)
class ReleasedKnowledge:
    release: ContentRelease
    primary: AthleteSport | SportScope
    goal: AthleteGoal
    archetype: ProgramArchetypeVersion
    phases: tuple[PhaseTemplate, ...]
    week_templates: tuple[WeekTemplate, ...]
    week_sessions: dict[UUID, tuple[WeekTemplateSession, ...]]
    recipes: dict[UUID, SessionDefinition]
    methods: tuple[CandidateMethod, ...]
    priorities: tuple[SportQualityPriority, ...]
    rules: tuple[PrescriptionRuleVersion, ...]


async def _athlete(session: AsyncSession, user_id: UUID) -> AthleteProfile:
    athlete = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    if athlete is None:
        raise ProblemError(409, "onboarding_required", "Onboarding required", "Complete athlete onboarding first.")
    return athlete


def _manifest_versions(items: list[ReleaseItem], entity_type: str) -> dict[UUID, int]:
    return {row.entity_id: row.entity_version for row in items if row.entity_type == entity_type}


def _matches_scope(values: list[str], selected: str | None) -> bool:
    return not values or (selected is not None and selected in values)


async def _released_knowledge(session: AsyncSession, athlete: AthleteProfile, weeks: int, *, release_id: UUID | None = None, goal_id: UUID | None = None, sport_scope: SportScope | None = None) -> ReleasedKnowledge:
    primary = sport_scope or await session.scalar(
        select(AthleteSport).where(AthleteSport.athlete_id == athlete.id, AthleteSport.is_primary.is_(True))
    )
    goal = await session.scalar(
        select(AthleteGoal)
        .where(AthleteGoal.athlete_id == athlete.id, *((AthleteGoal.id == goal_id,) if goal_id else (AthleteGoal.status == "active",)))
        .order_by(AthleteGoal.priority, AthleteGoal.created_at)
    )
    if primary is None or goal is None:
        raise ProblemError(
            409,
            "planning_inputs_incomplete",
            "Planning inputs incomplete",
            "A primary sport and active goal are required.",
        )
    release = await session.scalar(
        select(ContentRelease)
        .where(
            *((ContentRelease.id == release_id,) if release_id else (ContentRelease.state == "released",)),
            ContentRelease.package_type == "sport",
            ContentRelease.sport_code == primary.sport_code,
        )
        .order_by(ContentRelease.published_at.desc())
    )
    if release is None:
        raise ProblemError(
            409,
            "sport_not_released",
            "Sport unavailable",
            "This sport has not passed its independent release gate.",
        )
    items = (await session.scalars(select(ReleaseItem).where(ReleaseItem.release_id == release.id))).all()
    versions = {kind: _manifest_versions(items, kind) for kind in {
        "method", "recipe", "program_archetype", "prescription_rule"
    }}

    archetype_conditions = [
        and_(
            ProgramArchetypeVersion.archetype_id == entity_id,
            ProgramArchetypeVersion.content_version == version,
        )
        for entity_id, version in versions["program_archetype"].items()
    ]
    archetype_rows = [] if not archetype_conditions else (
        await session.scalars(
            select(ProgramArchetypeVersion)
            .join(ProgramArchetype, ProgramArchetype.id == ProgramArchetypeVersion.archetype_id)
            .where(ProgramArchetype.sport_code == primary.sport_code, or_(*archetype_conditions))
        )
    ).all()
    eligible_archetypes = [
        row for row in archetype_rows
        if row.minimum_weeks <= weeks <= row.maximum_weeks
        and _matches_scope(row.event_codes, primary.event_code)
        and _matches_scope(row.role_codes, primary.role_code)
        and _matches_scope(row.discipline_codes, primary.discipline_code)
        and _matches_scope(row.format_codes, primary.format_code)
        and _matches_scope(row.goal_codes, goal.goal_type)
        and _matches_scope(row.level_codes, athlete.competition_level)
    ]
    if not eligible_archetypes:
        raise ProblemError(422, "program_archetype_unresolved", "No program structure", "No released program archetype matches these inputs.")
    archetype = sorted(eligible_archetypes, key=lambda row: (row.name, str(row.archetype_id)))[0]
    phases = tuple((await session.scalars(
        select(PhaseTemplate)
        .where(
            PhaseTemplate.archetype_id == archetype.archetype_id,
            PhaseTemplate.archetype_version == archetype.content_version,
        )
        .order_by(PhaseTemplate.sequence)
    )).all())
    if not phases:
        raise ProblemError(422, "phase_structure_unresolved", "No phases", "The released archetype has no phase structure.")

    week_ids = set(_manifest_versions(items, "week_template"))
    week_templates = tuple((await session.scalars(
        select(WeekTemplate).where(
            WeekTemplate.id.in_(week_ids),
            WeekTemplate.sport_code == primary.sport_code,
        )
    )).all()) if week_ids else ()
    week_templates = tuple(
        row for row in week_templates
        if not row.level_codes or athlete.competition_level in row.level_codes
    )
    week_sessions: dict[UUID, tuple[WeekTemplateSession, ...]] = {}
    for row in week_templates:
        week_sessions[row.id] = tuple((await session.scalars(
            select(WeekTemplateSession)
            .where(WeekTemplateSession.week_template_id == row.id)
            .order_by(WeekTemplateSession.sequence)
        )).all())

    recipe_conditions = [
        and_(RecipeVersion.recipe_id == entity_id, RecipeVersion.recipe_version == version)
        for entity_id, version in versions["recipe"].items()
    ]
    recipe_rows = [] if not recipe_conditions else (await session.scalars(
        select(RecipeVersion).where(or_(*recipe_conditions))
    )).all()
    recipe_definitions: dict[UUID, SessionDefinition] = {}
    for recipe in recipe_rows:
        if recipe.sport_code not in {None, primary.sport_code}:
            continue
        if not (
            _matches_scope(recipe.event_codes, primary.event_code)
            and _matches_scope(recipe.role_codes, primary.role_code)
            and _matches_scope(recipe.discipline_codes, primary.discipline_code)
            and _matches_scope(recipe.format_codes, primary.format_code)
            and _matches_scope(recipe.goal_codes, goal.goal_type)
            and _matches_scope(recipe.level_codes, athlete.competition_level)
        ):
            continue
        blocks = (await session.scalars(
            select(RecipeBlock)
            .where(RecipeBlock.recipe_id == recipe.recipe_id, RecipeBlock.recipe_version == recipe.recipe_version)
            .order_by(RecipeBlock.sequence)
        )).all()
        slots: list[SlotDefinition] = []
        for block in blocks:
            rows = (await session.scalars(
                select(RecipeSlot).where(RecipeSlot.block_id == block.id).order_by(RecipeSlot.sequence)
            )).all()
            slots.extend(
                SlotDefinition(
                    row.id,
                    row.slot_code,
                    row.required_quality,
                    row.training_role,
                    block.block_type,
                    row.dose_schema_json,
                    row.required,
                )
                for row in rows
            )
        recipe_definitions[recipe.recipe_id] = SessionDefinition(
            recipe_id=recipe.recipe_id,
            session_type=recipe.recipe_type,
            purpose=recipe.purpose,
            load_class=recipe.load_class,
            estimated_minutes=sum(block.duration_maximum for block in blocks),
            slots=tuple(slots),
            recipe_version=recipe.recipe_version,
        )

    method_conditions = [
        and_(MethodVersion.method_id == entity_id, MethodVersion.content_version == version)
        for entity_id, version in versions["method"].items()
    ]
    method_versions = [] if not method_conditions else (await session.scalars(
        select(MethodVersion).where(or_(*method_conditions), MethodVersion.generator_eligible.is_(True))
    )).all()
    method_by_key = {(row.method_id, row.content_version): row for row in method_versions}
    effect_conditions = [
        and_(MethodEffect.method_id == entity_id, MethodEffect.method_version == version)
        for entity_id, version in method_by_key
    ]
    effect_rows = [] if not effect_conditions else (await session.scalars(
        select(MethodEffect).where(or_(*effect_conditions))
    )).all()
    method_codes = dict((await session.execute(
        select(Method.id, Method.code).where(Method.id.in_([key[0] for key in method_by_key]))
    )).all()) if method_by_key else {}
    methods = tuple(
        CandidateMethod(
            id=method.method_id,
            code=method_codes[method.method_id],
            quality=effect.quality_code,
            role=effect.training_role,
            equipment=frozenset(method.equipment_codes),
            environments=frozenset(method.environments),
            level_rank=LEVEL_RANK.get(method.level_minimum, 99),
            technical_cost=method.technical_cost,
            impact_cost=method.impact_cost,
            fatigue_cost=method.fatigue_cost,
            dose_units=frozenset(method.accepted_dose_units),
            method_version=method.content_version,
        )
        for effect in effect_rows
        if (method := method_by_key.get((effect.method_id, effect.method_version))) is not None
    )

    priority_ids = set(_manifest_versions(items, "sport_quality_priority"))
    priorities = tuple((await session.scalars(select(SportQualityPriority).where(
        SportQualityPriority.id.in_(priority_ids),
        SportQualityPriority.sport_code == primary.sport_code,
    ))).all()) if priority_ids else ()

    rule_conditions = [
        and_(PrescriptionRuleVersion.rule_id == entity_id, PrescriptionRuleVersion.rule_version == version)
        for entity_id, version in versions["prescription_rule"].items()
    ]
    rules = tuple() if not rule_conditions else tuple((await session.scalars(
        select(PrescriptionRuleVersion).where(
            or_(*rule_conditions),
            or_(PrescriptionRuleVersion.sport_code.is_(None), PrescriptionRuleVersion.sport_code == primary.sport_code),
        ).order_by(PrescriptionRuleVersion.priority, PrescriptionRuleVersion.rule_id)
    )).all())
    return ReleasedKnowledge(
        release, primary, goal, archetype, phases, week_templates, week_sessions,
        recipe_definitions, methods, priorities, rules,
    )


def _allocate_phases(phases: tuple[PhaseTemplate, ...], weeks: int, starts_on: date, priorities: tuple[SportQualityPriority, ...], level: str, event: str | None, role: str | None, discipline: str | None, format_code: str | None) -> tuple[PhaseAllocation, ...]:
    minimum = sum(row.minimum_weeks for row in phases)
    maximum = sum(row.maximum_weeks for row in phases)
    if weeks < minimum or weeks > maximum:
        raise PlanInvariantError(f"requested duration does not fit released phase bounds ({minimum}-{maximum} weeks)")
    allocations = [row.minimum_weeks for row in phases]
    remaining = weeks - minimum
    while remaining:
        eligible = [index for index, row in enumerate(phases) if allocations[index] < row.maximum_weeks]
        if not eligible:
            raise PlanInvariantError("phase allocation exhausted before the requested duration")
        index = min(eligible, key=lambda item: (allocations[item] / max(float(phases[item].allocation_weight), 0.0001), phases[item].sequence))
        allocations[index] += 1
        remaining -= 1
    output: list[PhaseAllocation] = []
    start_week = 1
    for row, count in zip(phases, allocations, strict=True):
        scoped = [
            item for item in priorities
            if item.phase_code == row.phase_code
            and item.event_code in {None, event}
            and item.role_code in {None, role}
            and item.discipline_code in {None, discipline}
            and item.format_code in {None, format_code}
            and item.level_code in {None, level}
        ]
        vector: dict[str, float] = {}
        for item in sorted(scoped, key=lambda value: (value.quality_code, str(value.id))):
            vector[item.quality_code] = max(vector.get(item.quality_code, 0), float(item.priority_weight))
        phase_start = starts_on + timedelta(weeks=start_week - 1)
        output.append(PhaseAllocation(row.phase_code, phase_start, phase_start + timedelta(weeks=count, days=-1), start_week, count, vector))
        start_week += count
    return tuple(output)


def _timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise PlanInvariantError("athlete timezone is not a valid IANA timezone") from exc


def _apply_slot_rules(definition: SessionDefinition, knowledge: ReleasedKnowledge, state: PlannerInput) -> SessionDefinition:
    context_base = {
        "athlete": {"level_rank": state.level_rank},
        "goal": {"code": state.goal_code},
        "sport": {"code": state.primary_sport, "event_code": state.event_code, "role_code": state.role_code, "discipline_code": state.discipline_code, "format_code": state.format_code, "weight_class_code": state.weight_class_code},
        "pain": {"unresolved": state.pain_flag},
        "phase": {"code": definition.phase_code},
        "session": {"type": definition.session_type, "load_class": definition.load_class},
    }
    rules = [
        (str(row.rule_id), row.rule_version, row.conditions_json, row.actions_json)
        for row in knowledge.rules
    ]
    slots: list[SlotDefinition] = []
    for slot in definition.slots:
        context = {**context_base, "slot": {"code": slot.code, "quality": slot.quality, "role": slot.role}}
        application = apply_bounded_actions(slot.dose, rules, context)
        if application.stopped or application.referral_required:
            raise PlanInvariantError("a released safety rule stopped generation and requires athlete follow-up")
        slots.append(SlotDefinition(slot.id, slot.code, slot.quality, slot.role, slot.block_type, application.values, slot.required))
    return SessionDefinition(**{**definition.__dict__, "slots": tuple(slots)})


def _structure_program(
    knowledge: ReleasedKnowledge,
    state: PlannerInput,
    availability: list[AvailabilityWindow],
    weeks: int,
    timezone_name: str,
) -> tuple[tuple[PhaseAllocation, ...], tuple[StructuredWeek, ...]]:
    phases = _allocate_phases(
        knowledge.phases, weeks, state.starts_on, knowledge.priorities,
        "recreational" if state.level_rank == 1 else "intermediate" if state.level_rank == 2 else "advanced",
        state.event_code, state.role_code, state.discipline_code, state.format_code,
    )
    windows = sorted(availability, key=lambda row: (row.weekday, row.start_minute))
    if not windows:
        raise PlanInvariantError("at least one availability window is required")
    zone = _timezone(timezone_name)
    output: list[StructuredWeek] = []
    for week_number in range(1, weeks + 1):
        phase = next(row for row in phases if row.start_week <= week_number < row.start_week + row.week_count)
        candidates = sorted(
            [row for row in knowledge.week_templates if row.phase_code == phase.code],
            key=lambda row: (row.sessions_minimum, row.code, str(row.id)),
        )
        if not candidates:
            raise PlanInvariantError(f"no released weekly template exists for phase {phase.code}")
        template = candidates[0]
        template_sessions = list(knowledge.week_sessions.get(template.id, ()))
        required_count = len([row for row in template_sessions if row.required])
        if required_count < template.sessions_minimum or required_count > template.sessions_maximum:
            raise PlanInvariantError(f"weekly template {template.code} has incoherent session bounds")
        if required_count > len(windows):
            raise PlanInvariantError(f"athlete availability cannot satisfy weekly template {template.code}")
        used_days: set[int] = set()
        scheduled: list[tuple[datetime, SessionDefinition]] = []
        hard_days: list[int] = []
        for link in template_sessions:
            if not link.required and len(scheduled) >= min(template.sessions_maximum, len(windows)):
                continue
            definition = knowledge.recipes.get(link.recipe_id)
            if definition is None:
                if link.required:
                    raise PlanInvariantError(f"weekly template references an ineligible recipe {link.recipe_id}")
                continue
            definition = SessionDefinition(**{**definition.__dict__, "phase_code": phase.code})
            definition = _apply_slot_rules(definition, knowledge, state)
            available_windows = [row for row in windows if row.weekday not in used_days]
            if link.preferred_weekday is not None:
                available_windows.sort(key=lambda row: (row.weekday != link.preferred_weekday, row.weekday, row.start_minute))
            else:
                available_windows.sort(key=lambda row: (row.weekday, row.start_minute))
            selected = None
            for window in available_windows:
                if definition.estimated_minutes > min(window.duration_minutes, state.maximum_session_minutes):
                    continue
                if definition.load_class == "hard" and (
                    window.weekday in state.external_hard_days
                    or any(abs(window.weekday - day) < 2 for day in hard_days)
                ):
                    continue
                selected = window
                break
            if selected is None:
                if link.required:
                    raise PlanInvariantError(f"no safe schedule slot resolves required recipe {definition.recipe_id}")
                continue
            used_days.add(selected.weekday)
            if definition.load_class == "hard":
                hard_days.append(selected.weekday)
            local_date = state.starts_on + timedelta(weeks=week_number - 1, days=selected.weekday)
            local_datetime = datetime.combine(local_date, time(selected.start_minute // 60, selected.start_minute % 60), zone)
            scheduled.append((local_datetime.astimezone(timezone.utc), definition))
        deload = bool(template.spacing_rules_json.get("deload_every_weeks") and week_number % int(template.spacing_rules_json["deload_every_weeks"]) == 0)
        output.append(StructuredWeek(week_number, state.starts_on + timedelta(weeks=week_number - 1), phase.code, deload, tuple(sorted(scheduled, key=lambda item: item[0]))))
    return phases, tuple(output)


async def _select_horizon(session: AsyncSession, athlete: AthleteProfile, knowledge: ReleasedKnowledge, state: PlannerInput, structured: tuple[StructuredWeek, ...]):
    horizon = structured[: min(2, len(structured))]
    scheduled = [item for week in horizon for item in week.sessions]
    draft = prepare_horizon(state, scheduled, list(knowledge.methods))
    provider = get_workout_selection_provider()
    packet = build_selection_packet(state, draft)
    provider_results = []
    validation_errors: list[str] = []
    result = None
    for _attempt in range(2):
        try:
            provider_result = await provider.select(packet=packet, validation_errors=validation_errors or None)
            provider_results.append(provider_result)
            result = finalize_plan(draft, provider_result.output.to_domain())
            break
        except PlanInvariantError as exc:
            validation_errors = [str(exc)]
        except Exception as exc:
            validation_errors = ["provider_or_schema_failure"]
            if _attempt == 1:
                raise ProblemError(503, "workout_ai_unavailable", "Workout generation unavailable", "The constrained selector did not return a valid response.") from exc
    if result is None:
        raise ProblemError(422, "ai_selection_rejected", "A safe plan could not be created", "The selector remained outside approved constraints after one repair attempt.")
    return draft, result, provider_results


async def _persist_materialized_sessions(
    session: AsyncSession,
    *,
    athlete: AthleteProfile,
    knowledge: ReleasedKnowledge,
    plan: TrainingPlan,
    week_rows: dict[int, TrainingWeek],
    draft,
    result,
    provider_results,
) -> None:
    last = provider_results[-1]
    session.add(TrainingGenerationRun(
        athlete_id=athlete.id, content_release_id=knowledge.release.id, plan_id=plan.id,
        horizon_starts_on=draft.starts_on, horizon_ends_on=draft.ends_on,
        provider=last.provider, model_id=last.model_id, prompt_version=PROMPT_VERSION,
        response_schema_version=RESPONSE_SCHEMA_VERSION, planner_version=PLANNER_VERSION,
        input_hash=draft.input_hash, status="accepted", attempt_count=len(provider_results),
        latency_ms=sum(item.latency_ms for item in provider_results),
        input_tokens=sum(item.input_tokens or 0 for item in provider_results) or None,
        output_tokens=sum(item.output_tokens or 0 for item in provider_results) or None,
        accepted_output_json=last.output.model_dump(mode="json"),
        validation_json={"passed": True, "repair_used": len(provider_results) > 1},
    ))
    session_sequence: dict[int, int] = defaultdict(int)
    existing = (await session.execute(
        select(TrainingWeek.week_number, func.count(TrainingSession.id))
        .outerjoin(TrainingSession, TrainingSession.week_id == TrainingWeek.id)
        .where(TrainingWeek.id.in_([row.id for row in week_rows.values()]))
        .group_by(TrainingWeek.week_number)
    )).all()
    session_sequence.update({week_number: int(count) for week_number, count in existing})
    for planned in result.sessions:
        week_number = ((planned.scheduled_for.date() - plan.starts_on).days // 7) + 1
        session_sequence[week_number] += 1
        row = TrainingSession(
            week_id=week_rows[week_number].id, athlete_id=athlete.id,
            recipe_id=planned.definition.recipe_id, recipe_version=planned.definition.recipe_version,
            sequence=session_sequence[week_number], scheduled_for=planned.scheduled_for,
            session_type=planned.definition.session_type, purpose=planned.definition.purpose,
            estimated_minutes=planned.definition.estimated_minutes, load_class=planned.definition.load_class,
            explanation=f"This session supports {planned.definition.purpose.lower()} in the {planned.definition.phase_code.replace('_', ' ')} phase.",
        )
        session.add(row)
        await session.flush()
        for sequence, item in enumerate(planned.items, 1):
            session.add(SessionItem(
                session_id=row.id, method_id=item.method_id, method_version=item.method_version,
                slot_id=item.slot_id, sequence=sequence, block_type=item.block_type,
                prescription_json=item.prescription,
                substitution_methods_json=[{"id": str(value), "version": next((method.method_version for method in knowledge.methods if method.id == value), 1)} for value in item.alternatives],
                decision_trace_json=item.trace,
            ))


async def generate_plan(session: AsyncSession, user_id: UUID, weeks: int, starts_on: date | None = None) -> PlanView:
    settings = get_settings()
    if not settings.generation_enabled:
        raise ProblemError(503, "generation_disabled", "Training generation is paused", "Generation opens only after a sport package is published.")
    athlete = await _athlete(session, user_id)
    normalized_start = starts_on or (date.today() + timedelta(days=(7 - date.today().weekday()) % 7))
    if normalized_start.weekday() != 0:
        raise ProblemError(422, "invalid_plan_start", "Invalid start date", "Training plans must start on a Monday.")
    knowledge = await _released_knowledge(session, athlete, weeks)
    availability = (await session.scalars(select(AvailabilityWindow).where(AvailabilityWindow.athlete_id == athlete.id))).all()
    equipment_rows = (await session.scalars(select(EquipmentAccess).where(EquipmentAccess.athlete_id == athlete.id))).all()
    external = (await session.scalars(select(ExternalLoad).where(ExternalLoad.athlete_id == athlete.id))).all()
    pain_flag = bool(await session.scalar(select(func.count()).select_from(PainReport).where(PainReport.athlete_id == athlete.id, PainReport.status == "open")))
    external_hard_days = frozenset(row.starts_at.astimezone(_timezone(athlete.timezone)).weekday() for row in external if row.intensity in {"hard", "high", "maximal"})
    equipment = frozenset(row.equipment_code for row in equipment_rows)
    environments = frozenset(value for row in equipment_rows for value in row.environments) or frozenset({"home", "gym", "field", "road", "pool"})
    state = PlannerInput(
        athlete.id, LEVEL_RANK.get(athlete.competition_level, 1), knowledge.goal.goal_type,
        knowledge.primary.sport_code, knowledge.primary.event_code, knowledge.primary.role_code,
        knowledge.goal.target_date, tuple((row.weekday, row.start_minute, row.duration_minutes) for row in availability),
        equipment, environments, athlete.maximum_session_minutes, external_hard_days, pain_flag,
        knowledge.release.id, normalized_start, knowledge.primary.discipline_code, knowledge.primary.format_code, knowledge.primary.weight_class_code,
    )
    try:
        phases, structured = _structure_program(knowledge, state, availability, weeks, athlete.timezone)
        draft, result, provider_results = await _select_horizon(session, athlete, knowledge, state, structured)
    except (PlanInvariantError, RuleEvaluationError) as exc:
        raise ProblemError(422, "plan_invariant_failed", "A safe plan could not be created", str(exc)) from exc

    plan_number = (await session.scalar(select(func.coalesce(func.max(TrainingPlan.plan_number), 0)).where(TrainingPlan.athlete_id == athlete.id))) + 1
    plan = TrainingPlan(
        athlete_id=athlete.id, plan_number=plan_number, status="active", goal_id=knowledge.goal.id,
        content_release_id=knowledge.release.id, planner_version=PLANNER_VERSION, input_hash=result.input_hash,
        input_snapshot_json={
            "competition_level": athlete.competition_level,
            "maximum_session_minutes": athlete.maximum_session_minutes,
            "timezone": athlete.timezone,
            "sport_code": knowledge.primary.sport_code,
            "event_code": knowledge.primary.event_code,
            "role_code": knowledge.primary.role_code,
            "discipline_code": knowledge.primary.discipline_code,
            "format_code": knowledge.primary.format_code,
            "weight_class_code": knowledge.primary.weight_class_code,
            "goal_code": knowledge.goal.goal_type,
            "target_date": knowledge.goal.target_date.isoformat() if knowledge.goal.target_date else None,
            "availability": [[row.weekday,row.start_minute,row.duration_minutes] for row in availability],
            "equipment": sorted(equipment),
            "environments": sorted(environments),
            "external_hard_days": sorted(external_hard_days),
        },
        starts_on=normalized_start, ends_on=normalized_start + timedelta(weeks=weeks, days=-1),
        decision_trace_json=[
            {"decision": "sport_release_selected", "release_id": str(knowledge.release.id)},
            {"decision": "archetype_selected", "id": str(knowledge.archetype.archetype_id), "version": knowledge.archetype.content_version},
            {"decision": "phase_structure_allocated", "phases": [row.code for row in phases]},
            *result.trace,
        ],
        validation_json={"passed": True, "full_structure_weeks": weeks, "materialized_weeks": min(2, weeks)},
        activated_at=datetime.now(timezone.utc), materialized_through=min(structured[1 if weeks > 1 else 0].starts_on + timedelta(days=6), normalized_start + timedelta(weeks=weeks, days=-1)),
        selection_horizon_weeks=2,
    )
    session.add(plan)
    await session.flush()

    phase_rows: dict[str, TrainingPhase] = {}
    for sequence, phase in enumerate(phases, 1):
        row = TrainingPhase(plan_id=plan.id, sequence=sequence, phase_code=phase.code, starts_on=phase.starts_on, ends_on=phase.ends_on, priority_vector_json=phase.priorities)
        session.add(row)
        await session.flush()
        phase_rows[phase.code] = row
    week_rows: dict[int, TrainingWeek] = {}
    for week in structured:
        structure_json = {
            "sessions": [
                {"scheduled_for": scheduled.isoformat(), "recipe_id": str(definition.recipe_id), "recipe_version": definition.recipe_version, "load_class": definition.load_class}
                for scheduled, definition in week.sessions
            ]
        }
        row = TrainingWeek(
            plan_id=plan.id, phase_id=phase_rows[week.phase_code].id, week_number=week.week_number,
            starts_on=week.starts_on, planned_load=0, deload=week.deload, structure_json=structure_json,
            materialization_status="materialized" if week.week_number <= 2 else "pending",
        )
        session.add(row)
        await session.flush()
        week_rows[week.week_number] = row

    await _persist_materialized_sessions(
        session, athlete=athlete, knowledge=knowledge, plan=plan, week_rows=week_rows,
        draft=draft, result=result, provider_results=provider_results,
    )
    await enqueue_event(session, aggregate_type="training_plan", aggregate_id=plan.id, event_type="training.plan.created", payload={"plan_id": str(plan.id), "athlete_id": str(athlete.id)})
    await session.commit()
    return await plan_view(session, plan.id, athlete.id)


async def materialize_next_horizon(session: AsyncSession, user_id: UUID, plan_id: UUID) -> PlanView:
    settings=get_settings()
    if not settings.generation_enabled: raise ProblemError(503,"generation_disabled","Training generation is paused","Generation opens only after a sport package is published.")
    athlete=await _athlete(session,user_id)
    plan=await session.scalar(select(TrainingPlan).where(TrainingPlan.id==plan_id,TrainingPlan.athlete_id==athlete.id).with_for_update())
    if plan is None: raise ProblemError(404,"plan_not_found","Plan not found","The plan does not exist.")
    if plan.status!="active": raise ProblemError(409,"plan_not_active","Plan not active","Only an active plan can materialize future sessions.")
    pending=(await session.scalars(select(TrainingWeek).where(TrainingWeek.plan_id==plan.id,TrainingWeek.materialization_status=="pending").order_by(TrainingWeek.week_number).limit(plan.selection_horizon_weeks).with_for_update())).all()
    if not pending: return await plan_view(session,plan.id,athlete.id)
    total_weeks=((plan.ends_on-plan.starts_on).days+1)//7; snapshot=plan.input_snapshot_json
    scope=SportScope(snapshot["sport_code"],snapshot.get("event_code"),snapshot.get("role_code"),snapshot.get("discipline_code"),snapshot.get("format_code"),snapshot.get("weight_class_code"))
    knowledge=await _released_knowledge(session,athlete,total_weeks,release_id=plan.content_release_id,goal_id=plan.goal_id,sport_scope=scope)
    state=PlannerInput(
        athlete.id,LEVEL_RANK.get(snapshot["competition_level"],1),snapshot["goal_code"],scope.sport_code,scope.event_code,scope.role_code,
        date.fromisoformat(snapshot["target_date"]) if snapshot.get("target_date") else None,
        tuple(tuple(value) for value in snapshot["availability"]),frozenset(snapshot["equipment"]),frozenset(snapshot["environments"]),
        int(snapshot["maximum_session_minutes"]),frozenset(snapshot["external_hard_days"]),
        bool(await session.scalar(select(func.count()).select_from(PainReport).where(PainReport.athlete_id==athlete.id,PainReport.status=="open"))),
        plan.content_release_id,plan.starts_on,scope.discipline_code,scope.format_code,scope.weight_class_code,
    )
    phase_codes=dict((await session.execute(select(TrainingPhase.id,TrainingPhase.phase_code).where(TrainingPhase.plan_id==plan.id))).all())
    structured=[]
    for week in pending:
        scheduled=[]
        for item in week.structure_json.get("sessions",[]):
            definition=knowledge.recipes.get(UUID(item["recipe_id"]))
            if definition is None or definition.recipe_version!=int(item["recipe_version"]): raise ProblemError(409,"pinned_recipe_unavailable","Pinned recipe unavailable","The plan references a recipe version outside its release.")
            definition=SessionDefinition(**{**definition.__dict__,"phase_code":phase_codes[week.phase_id]})
            definition=_apply_slot_rules(definition,knowledge,state)
            scheduled.append((datetime.fromisoformat(item["scheduled_for"]),definition))
        structured.append(StructuredWeek(week.week_number,week.starts_on,phase_codes[week.phase_id],week.deload,tuple(scheduled)))
    try: draft,result,provider_results=await _select_horizon(session,athlete,knowledge,state,tuple(structured))
    except (PlanInvariantError,RuleEvaluationError) as exc: raise ProblemError(422,"plan_invariant_failed","A safe horizon could not be created",str(exc)) from exc
    week_rows={row.week_number:row for row in pending}
    await _persist_materialized_sessions(session,athlete=athlete,knowledge=knowledge,plan=plan,week_rows=week_rows,draft=draft,result=result,provider_results=provider_results)
    for row in pending: row.materialization_status="materialized"; row.version+=1
    plan.materialized_through=max(row.starts_on+timedelta(days=6) for row in pending); plan.version+=1
    await enqueue_event(session,aggregate_type="training_plan",aggregate_id=plan.id,event_type="training.plan.horizon_materialized",payload={"plan_id":str(plan.id),"through":plan.materialized_through.isoformat()})
    await session.commit(); return await plan_view(session,plan.id,athlete.id)


async def session_view(session: AsyncSession, row: TrainingSession) -> SessionView:
    items = (await session.execute(
        select(SessionItem, MethodVersion)
        .join(MethodVersion, and_(MethodVersion.method_id == SessionItem.method_id, MethodVersion.content_version == SessionItem.method_version))
        .where(SessionItem.session_id == row.id)
        .order_by(SessionItem.sequence)
    )).all()
    return SessionView(
        id=row.id, scheduled_for=row.scheduled_for, session_type=row.session_type,
        purpose=row.purpose, estimated_minutes=row.estimated_minutes, status=row.status,
        explanation=row.explanation,
        items=[SessionItemView(
            id=item.id, method_id=method.method_id, method_name=method.canonical_name,
            method_version=method.content_version, block_type=item.block_type,
            prescription=item.prescription_json,
            alternatives=[UUID(value["id"]) for value in item.substitution_methods_json],
        ) for item, method in items],
        version=row.version,
    )


async def plan_view(session: AsyncSession, plan_id: UUID, athlete_id: UUID) -> PlanView:
    plan = await session.scalar(select(TrainingPlan).where(TrainingPlan.id == plan_id, TrainingPlan.athlete_id == athlete_id))
    if plan is None:
        raise ProblemError(404, "plan_not_found", "Plan not found", "The plan does not exist.")
    sessions = (await session.scalars(
        select(TrainingSession).join(TrainingWeek).where(TrainingWeek.plan_id == plan.id).order_by(TrainingSession.scheduled_for)
    )).all()
    return PlanView(
        id=plan.id, status=plan.status, starts_on=plan.starts_on.isoformat(), ends_on=plan.ends_on.isoformat(),
        planner_version=plan.planner_version, content_release_id=plan.content_release_id,
        materialized_through=plan.materialized_through,
        sessions=[await session_view(session, row) for row in sessions],
    )


async def complete_session(session: AsyncSession, user_id: UUID, session_id: UUID, command: CompletionCommand) -> SessionView:
    athlete = await _athlete(session, user_id)
    row = await session.scalar(select(TrainingSession).where(TrainingSession.id == session_id, TrainingSession.athlete_id == athlete.id).with_for_update())
    if row is None:
        raise ProblemError(404, "session_not_found", "Session not found", "The session does not exist.")
    if row.version != command.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the session and try again.")
    if row.status == "completed":
        raise ProblemError(409, "session_already_completed", "Already completed", "This session is already complete.")
    completion = SessionCompletion(
        session_id=row.id, athlete_id=athlete.id, completed_at=datetime.now(timezone.utc),
        duration_minutes=command.duration_minutes, session_rpe=command.session_rpe,
        completion_ratio=command.completion_ratio, pain_flag=command.pain_flag,
        feedback_json={"notes": command.notes}, calculated_load=command.duration_minutes * command.session_rpe,
    )
    session.add(completion)
    row.status = "completed"
    row.version += 1
    await enqueue_event(session, aggregate_type="training_session", aggregate_id=row.id, event_type="training.session.completed", payload={"session_id": str(row.id), "athlete_id": str(athlete.id), "pain_flag": command.pain_flag})
    await session.commit()
    return await session_view(session, row)

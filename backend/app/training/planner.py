from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

PLANNER_VERSION = "2.0.0"


class PlanInvariantError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateMethod:
    id: UUID
    code: str
    quality: str
    role: str
    equipment: frozenset[str]
    environments: frozenset[str]
    level_rank: int
    technical_cost: int
    impact_cost: int
    fatigue_cost: int
    dose_units: frozenset[str]
    method_version: int = 1
    # Athlete-facing catalogue data is carried into the AI packet and then
    # returned by the read adapter. These fields are optional so the pure
    # planner tests can continue to use small domain fixtures.
    name: str = ""
    equipment_codes: frozenset[str] = frozenset()
    instruction_steps: tuple[str, ...] = ()
    coaching_cues: tuple[str, ...] = ()
    common_errors: tuple[str, ...] = ()
    safety_boundaries: tuple[str, ...] = ()
    source_template_code: str | None = None


@dataclass(frozen=True)
class SlotDefinition:
    id: UUID
    code: str
    quality: str
    role: str
    block_type: str
    dose: dict[str, Any]
    required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SessionDefinition:
    recipe_id: UUID
    session_type: str
    purpose: str
    load_class: str
    estimated_minutes: int
    slots: tuple[SlotDefinition, ...]
    recipe_version: int = 1
    phase_code: str = "general_preparation"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlannerInput:
    athlete_id: UUID
    level_rank: int
    goal_code: str
    primary_sport: str
    event_code: str | None
    role_code: str | None
    target_date: date | None
    available_slots: tuple[tuple[int, int, int], ...]
    equipment: frozenset[str]
    environments: frozenset[str]
    maximum_session_minutes: int
    external_hard_days: frozenset[int]
    pain_flag: bool
    content_release_id: UUID
    starts_on: date
    discipline_code: str | None = None
    format_code: str | None = None
    weight_class_code: str | None = None
    athlete_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateSlot:
    occurrence_id: str
    definition: SlotDefinition
    candidates: tuple[CandidateMethod, ...]


@dataclass(frozen=True)
class DraftSession:
    scheduled_for: datetime
    definition: SessionDefinition
    slots: tuple[CandidateSlot, ...]


@dataclass(frozen=True)
class PlanDraft:
    input_hash: str
    starts_on: date
    ends_on: date
    sessions: tuple[DraftSession, ...]
    trace: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class MethodSelection:
    occurrence_id: str
    slot_id: UUID
    method_id: UUID
    prescription: dict[str, Any]
    alternative_method_ids: tuple[UUID, ...]
    rationale_code: str


@dataclass
class PlannedItem:
    slot_id: UUID
    method_id: UUID
    block_type: str
    prescription: dict[str, Any]
    alternatives: list[UUID]
    trace: list[dict[str, Any]]
    method_version: int = 1


@dataclass
class PlannedSession:
    scheduled_for: datetime
    definition: SessionDefinition
    items: list[PlannedItem]


@dataclass
class PlanResult:
    input_hash: str
    starts_on: date
    ends_on: date
    sessions: list[PlannedSession]
    trace: list[dict[str, Any]] = field(default_factory=list)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _eligible_methods(slot: SlotDefinition, methods: list[CandidateMethod], state: PlannerInput) -> tuple[CandidateMethod, ...]:
    required_units = set(slot.dose)
    eligible = [
        method
        for method in methods
        if method.quality == slot.quality
        and method.role == slot.role
        and method.level_rank <= state.level_rank
        and method.equipment.issubset(state.equipment)
        and (not method.environments or bool(method.environments & state.environments))
        and required_units.issubset(method.dose_units)
    ]
    eligible.sort(key=lambda method: (method.code, str(method.id)))
    if slot.required and not eligible:
        raise PlanInvariantError(f"no eligible approved method for required slot {slot.code}")
    return tuple(eligible)


def prepare_plan(state: PlannerInput, recipes: list[SessionDefinition], methods: list[CandidateMethod], *, weeks: int) -> PlanDraft:
    """Build the reviewed structure and bounded candidate set sent to the AI selector."""
    if state.pain_flag:
        raise PlanInvariantError("unresolved pain requires modification or professional referral before generation")
    if not 1 <= weeks <= 52:
        raise PlanInvariantError("plan duration must be between 1 and 52 weeks")
    if state.starts_on.weekday() != 0:
        raise PlanInvariantError("plan start date must be a Monday")
    available = sorted(state.available_slots)
    if not available:
        raise PlanInvariantError("at least one availability window is required")
    usable = [slot for slot in available if slot[0] not in state.external_hard_days]
    if not usable:
        raise PlanInvariantError("external workload leaves no valid training day")
    definitions = sorted(
        [recipe for recipe in recipes if recipe.estimated_minutes <= state.maximum_session_minutes],
        key=lambda recipe: (recipe.load_class == "hard", recipe.session_type, str(recipe.recipe_id)),
    )
    if not definitions:
        raise PlanInvariantError("no released session recipe fits the athlete's duration")

    sessions: list[DraftSession] = []
    previous_hard: date | None = None
    for week in range(weeks):
        for sequence, definition in enumerate(definitions[: len(usable)]):
            weekday, start_minute, _duration = usable[sequence % len(usable)]
            scheduled_date = state.starts_on + timedelta(days=week * 7 + weekday)
            if definition.load_class == "hard" and previous_hard and (scheduled_date - previous_hard).days < 2:
                raise PlanInvariantError("hard sessions require at least one intervening day")
            if definition.load_class == "hard":
                previous_hard = scheduled_date
            scheduled_for = datetime.combine(
                scheduled_date,
                time(start_minute // 60, start_minute % 60),
                timezone.utc,
            )
            candidate_slots: list[CandidateSlot] = []
            for slot in definition.slots:
                candidates = _eligible_methods(slot, methods, state)
                if not candidates and not slot.required:
                    continue
                occurrence_id = canonical_hash(
                    {"recipe_id": definition.recipe_id, "scheduled_for": scheduled_for, "slot_id": slot.id}
                )[:24]
                candidate_slots.append(CandidateSlot(occurrence_id, slot, candidates))
            sessions.append(DraftSession(scheduled_for, definition, tuple(candidate_slots)))

    source = {
        "state": state,
        "recipes": recipes,
        "candidate_sessions": sessions,
        "weeks": weeks,
        "planner_version": PLANNER_VERSION,
    }
    trace = (
        {
            "decision": "candidate_plan_prepared",
            "planner_version": PLANNER_VERSION,
            "release_id": str(state.content_release_id),
            "session_count": len(sessions),
        },
    )
    return PlanDraft(
        canonical_hash(source),
        state.starts_on,
        state.starts_on + timedelta(days=weeks * 7 - 1),
        tuple(sessions),
        trace,
    )


def prepare_horizon(
    state: PlannerInput,
    scheduled_definitions: list[tuple[datetime, SessionDefinition]],
    methods: list[CandidateMethod],
) -> PlanDraft:
    """Prepare scheduled template slots for constrained AI selection.

    Dates and session definitions are supplied by the generation adapter. This
    function applies hard eligibility checks and creates the bounded AI packet;
    it never chooses an exercise.
    """
    if state.pain_flag:
        raise PlanInvariantError("unresolved pain requires modification or professional referral before generation")
    if not scheduled_definitions:
        raise PlanInvariantError("the materialization horizon has no scheduled sessions")
    sessions: list[DraftSession] = []
    previous_hard: date | None = None
    for scheduled_for, definition in sorted(scheduled_definitions, key=lambda item: item[0]):
        if definition.estimated_minutes > state.maximum_session_minutes:
            raise PlanInvariantError(f"recipe {definition.recipe_id} exceeds the athlete session limit")
        if scheduled_for.weekday() in state.external_hard_days and definition.load_class == "hard":
            raise PlanInvariantError("a hard training session conflicts with external hard load")
        if definition.load_class == "hard" and previous_hard and (scheduled_for.date() - previous_hard).days < 2:
            raise PlanInvariantError("hard sessions require at least one intervening day")
        if definition.load_class == "hard":
            previous_hard = scheduled_for.date()
        candidate_slots: list[CandidateSlot] = []
        for slot in definition.slots:
            candidates = _eligible_methods(slot, methods, state)
            if not candidates and not slot.required:
                continue
            occurrence_id = canonical_hash(
                {
                    "recipe_id": definition.recipe_id,
                    "recipe_version": definition.recipe_version,
                    "scheduled_for": scheduled_for,
                    "slot_id": slot.id,
                }
            )[:24]
            candidate_slots.append(CandidateSlot(occurrence_id, slot, candidates))
        sessions.append(DraftSession(scheduled_for, definition, tuple(candidate_slots)))
    trace = (
        {
            "decision": "materialization_horizon_prepared",
            "planner_version": PLANNER_VERSION,
            "release_id": str(state.content_release_id),
            "session_count": len(sessions),
        },
    )
    source = {"state": state, "sessions": sessions, "planner_version": PLANNER_VERSION}
    return PlanDraft(
        input_hash=canonical_hash(source),
        starts_on=sessions[0].scheduled_for.date(),
        ends_on=sessions[-1].scheduled_for.date(),
        sessions=tuple(sessions),
        trace=trace,
    )


def _validate_dose_value(unit: str, specification: Any, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise PlanInvariantError(f"prescription {unit} must be a scalar value")
    if isinstance(specification, dict):
        minimum = specification.get("minimum", specification.get("min"))
        maximum = specification.get("maximum", specification.get("max"))
        allowed = specification.get("allowed_values")
        if allowed is not None and value not in allowed:
            raise PlanInvariantError(f"prescription {unit} is not an allowed value")
        if minimum is not None and (not isinstance(value, (int, float)) or value < minimum):
            raise PlanInvariantError(f"prescription {unit} is below the released minimum")
        if maximum is not None and (not isinstance(value, (int, float)) or value > maximum):
            raise PlanInvariantError(f"prescription {unit} exceeds the released maximum")
        step = specification.get("step")
        if step and minimum is not None and isinstance(value, (int, float)):
            quotient = (value - minimum) / step
            if abs(quotient - round(quotient)) > 1e-8:
                raise PlanInvariantError(f"prescription {unit} does not follow the released increment")
    elif isinstance(specification, list):
        if value not in specification:
            raise PlanInvariantError(f"prescription {unit} is not an allowed value")
    elif value != specification:
        raise PlanInvariantError(f"prescription {unit} must equal the fixed released value")


def finalize_plan(draft: PlanDraft, selections: list[MethodSelection]) -> PlanResult:
    """Validate AI selections against the exact candidate packet and released dose bounds."""
    expected = {slot.occurrence_id: (session, slot) for session in draft.sessions for slot in session.slots}
    received: dict[str, MethodSelection] = {}
    for selection in selections:
        if selection.occurrence_id in received:
            raise PlanInvariantError(f"duplicate selection for occurrence {selection.occurrence_id}")
        received[selection.occurrence_id] = selection
    if set(received) != set(expected):
        missing = sorted(set(expected) - set(received))
        unknown = sorted(set(received) - set(expected))
        raise PlanInvariantError(f"selection coverage mismatch; missing={missing}, unknown={unknown}")

    planned_sessions: list[PlannedSession] = []
    for draft_session in draft.sessions:
        used: set[UUID] = set()
        items: list[PlannedItem] = []
        for candidate_slot in draft_session.slots:
            selected = received[candidate_slot.occurrence_id]
            slot = candidate_slot.definition
            if selected.slot_id != slot.id:
                raise PlanInvariantError(f"slot ID mismatch for occurrence {candidate_slot.occurrence_id}")
            candidate_ids = {method.id for method in candidate_slot.candidates}
            if selected.method_id not in candidate_ids:
                raise PlanInvariantError(f"AI selected an ineligible or unknown method for slot {slot.code}")
            if selected.method_id in used:
                raise PlanInvariantError("a method cannot appear twice in one session")
            used.add(selected.method_id)
            if set(selected.prescription) != set(slot.dose):
                raise PlanInvariantError(f"prescription fields do not match released dose schema for slot {slot.code}")
            for unit, specification in slot.dose.items():
                _validate_dose_value(unit, specification, selected.prescription[unit])
            alternatives = list(selected.alternative_method_ids)
            if len(alternatives) > 3 or len(set(alternatives)) != len(alternatives):
                raise PlanInvariantError(f"invalid alternatives for slot {slot.code}")
            if selected.method_id in alternatives or any(item not in candidate_ids for item in alternatives):
                raise PlanInvariantError(f"alternative is not eligible for slot {slot.code}")
            items.append(
                PlannedItem(
                    slot.id,
                    selected.method_id,
                    slot.block_type,
                    dict(selected.prescription),
                    alternatives,
                    [
                        {
                            "decision": "ai_method_selected",
                            "occurrence_id": candidate_slot.occurrence_id,
                            "rationale_code": selected.rationale_code,
                            "validated_against_release": True,
                        }
                    ],
                    next(method.method_version for method in candidate_slot.candidates if method.id == selected.method_id),
                )
            )
        planned_sessions.append(PlannedSession(draft_session.scheduled_for, draft_session.definition, items))

    trace = list(draft.trace)
    trace.append({"decision": "ai_selections_validated", "selection_count": len(selections)})
    trace.append({"decision": "plan_validated", "session_count": len(planned_sessions)})
    return PlanResult(draft.input_hash, draft.starts_on, draft.ends_on, planned_sessions, trace)

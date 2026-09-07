"""Legacy pure reference rules used by release tooling and compatibility tests.

Runtime plan generation is handled by ``ai_generation_service``. This module
does not participate in the API generation path and remains available for
validating historical reference packages.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from math import ceil
from typing import Any, Iterable
from uuid import UUID

from backend.app.training.reference_prescription import (
    NormalizedReferencePrescription,
    PrescriptionBindingError,
    bind_prescription_to_method,
)


LEVEL_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3}
INTRINSIC_EQUIPMENT = {"bodyweight", "mode_specific", "mode_specific_equipment"}
FULL_GYM_EQUIPMENT = {
    "barbell", "bench", "bench_or_box", "cable_machine", "dumbbells",
    "floor", "kettlebell", "landmine", "low_box", "machine", "mat",
    "medicine_ball", "mini_band", "plates", "power_rack", "pull_up_bar",
    "resistance_band", "smith_machine", "soft_landing_surface", "squat_rack",
    "stability_ball",
}
# The source catalogue uses a flat equipment list. Most multi-item lists mean
# every item is required (for example barbell + rack + plates), but these
# reviewed methods contain genuine alternatives. Each tuple entry is one
# complete valid equipment option. Keeping the exceptions explicit prevents
# the compiler from guessing based on names or punctuation.
METHOD_EQUIPMENT_OPTIONS: dict[str, tuple[frozenset[str], ...]] = {
    "goblet_squat": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "box_squat": (frozenset({"bench", "barbell"}), frozenset({"bench", "dumbbells"})),
    "bulgarian_split_squat": tuple(
        frozenset({support, load})
        for support in ("bench", "low_box")
        for load in ("dumbbells", "kettlebell", "barbell")
    ),
    "dumbbell_split_squat": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "reverse_lunge": tuple(frozenset({item}) for item in ("dumbbells", "kettlebell", "barbell")),
    "forward_lunge": tuple(frozenset({item}) for item in ("dumbbells", "kettlebell", "barbell")),
    "lateral_lunge": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "walking_lunge": tuple(frozenset({item}) for item in ("dumbbells", "kettlebell", "barbell")),
    "step_up": (frozenset({"bench", "dumbbells"}), frozenset({"bench", "kettlebell"})),
    "lateral_step_up": (frozenset({"bench", "dumbbells"}), frozenset({"bench", "kettlebell"})),
    "single_leg_romanian_deadlift": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "nordic_hamstring_curl": (frozenset({"bench"}), frozenset({"cable_machine"})),
    "assisted_nordic_hamstring_curl": (frozenset({"resistance_band"}), frozenset({"cable_machine"})),
    "standing_calf_raise": tuple(frozenset({item}) for item in ("machine", "dumbbells", "smith_machine")),
    "seated_calf_raise": (frozenset({"machine", "plates"}), frozenset({"dumbbells"})),
    "single_leg_calf_raise": (frozenset({"bench"}), frozenset({"dumbbells"})),
    "low_impact_recovery_session": tuple(frozenset({item}) for item in ("cycle_ergometer", "pool", "rowing_ergometer")),
    "lat_pulldown": (frozenset({"machine"}), frozenset({"cable_machine"})),
    "neutral_grip_lat_pulldown": (frozenset({"machine"}), frozenset({"cable_machine"})),
    "inverted_row": (frozenset({"barbell", "squat_rack"}), frozenset({"smith_machine"})),
    "face_pull": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "push_up_plus_full_push_up": (
        frozenset({"floor"}), frozenset({"bench"}), frozenset({"wall"}),
    ),
    "plank_drag_through": tuple(frozenset({item}) for item in ("dumbbells", "kettlebell", "medicine_ball")),
    "pallof_press": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "pallof_press_iso_hold": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "half_kneeling_pallof_press": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "cable_wood_chop": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "half_kneeling_cable_chop": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "cable_lift": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "half_kneeling_cable_lift": (frozenset({"cable_machine"}), frozenset({"resistance_band"})),
    "farmer_s_carry": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "suitcase_carry": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "single_arm_front_rack_carry": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "overhead_carry": (frozenset({"dumbbells"}), frozenset({"kettlebell"})),
    "bear_hug_carry": (frozenset({"medicine_ball"}), frozenset({"plates"})),
    "adductor_squeeze": (frozenset({"medicine_ball"}), frozenset({"stability_ball"})),
    "banded_lateral_walk": (frozenset({"mini_band"}), frozenset({"resistance_band"})),
    "reverse_hyperextension": tuple(frozenset({item}) for item in ("machine", "bench", "cable_machine")),
    # These conditioning methods use human-readable compound tokens in the
    # catalogue. Resolve them to the actual equipment an athlete records.
    "easy_continuous_run": (frozenset({"safe_route"}), frozenset({"treadmill"})),
    "steady_tempo_run": (frozenset({"safe_route"}), frozenset({"treadmill"})),
    "threshold_run_intervals": (
        frozenset({"timer", "safe_route"}),
        frozenset({"timer", "treadmill"}),
    ),
    "easy_continuous_cycle": (
        frozenset({"bicycle"}), frozenset({"cycle_ergometer"}),
    ),
    "cycling_threshold_intervals": (
        frozenset({"bicycle"}), frozenset({"cycle_ergometer"}),
    ),
    "cycling_aerobic_power_intervals": (
        frozenset({"bicycle"}), frozenset({"cycle_ergometer"}),
    ),
    "cycling_sprint_repeats": (
        frozenset({"bicycle"}), frozenset({"cycle_ergometer"}),
    ),
}
HARD_CATEGORIES = {
    "maximum_strength", "overcoming_isometric_force", "eccentric_capacity",
    "explosive_strength", "vertical_power", "horizontal_power",
    "lateral_power", "rotational_power", "upper_body_power",
    "acceleration", "maximum_velocity", "speed_endurance", "deceleration",
    "planned_change_of_direction", "reactive_agility", "landing_capacity",
    "reactive_elastic_strength",
    "anaerobic_power", "anaerobic_capacity", "high_intensity_aerobic_power",
    "repeated_sprint_ability", "repeated_high_intensity_ability",
}


class ReferenceCompilationError(ValueError):
    """The supplied reference data cannot produce a safe bounded program."""


@dataclass(frozen=True)
class AvailabilitySlot:
    weekday: int
    start_minute: int
    duration_minutes: int
    environments: frozenset[str]


@dataclass(frozen=True)
class PhasePolicy:
    phase_code: str
    policy_version: int
    progression_mode: str
    maximum_categories: int
    maximum_sessions_per_week: int
    weekly_volume_multipliers: tuple[float, float, float, float]
    novelty_policy: str
    source_hash: str


@dataclass(frozen=True)
class CompilerContext:
    starts_on: date
    athlete_level: str
    primary_mode: str
    availability: tuple[AvailabilitySlot, ...]
    equipment: frozenset[str]
    environments: frozenset[str]
    equipment_by_environment: tuple[tuple[str, frozenset[str]], ...]
    external_hard_days: frozenset[int]
    maximum_session_minutes: int
    phase_policy: PhasePolicy
    external_hard_dates: frozenset[date] = frozenset()
    pain_unresolved: bool = False
    sport_code: str = ""
    scope_code: str = ""
    phase_code: str = ""
    goal_code: str = ""
    readiness: int | None = None
    acute_illness: bool = False
    scenario_codes: frozenset[str] = frozenset()
    method_familiarity: tuple[tuple[str, str], ...] = ()
    competition_dates: tuple[date, ...] = ()
    days_to_competition: int | None = None
    cross_training_consent: bool = False
    external_schedule: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ReferenceWeek:
    week_number: int
    sessions_per_week: str
    intent: str
    prescription: NormalizedReferencePrescription
    progression_condition: str
    regression_condition: str


@dataclass(frozen=True)
class ReferenceMethod:
    method_id: UUID
    method_version: int
    code: str
    name: str
    sequence: int
    applicable_modes: frozenset[str]
    equipment: frozenset[str]
    environments: frozenset[str]
    minimum_level: str
    technical_cost: int
    impact_cost: int
    fatigue_cost: int
    accepted_dose_units: frozenset[str]
    safety_boundaries: tuple[str, ...]
    sport_codes: frozenset[str] = frozenset()
    scope_codes: frozenset[str] = frozenset()
    block_role: str = "primary_reference"


@dataclass(frozen=True)
class ReferenceTemplate:
    template_id: UUID
    template_version: int
    code: str
    category_code: str
    purpose: str
    source_hash: str
    methods: tuple[ReferenceMethod, ...]
    weeks: tuple[ReferenceWeek, ...]
    week_4_policy: str = ""


@dataclass(frozen=True)
class RankedCategory:
    category_code: str
    rank: int
    weight: float


@dataclass(frozen=True)
class PriorityContext:
    primary_category: str
    block_order: tuple[str, ...]
    ranked_categories: tuple[RankedCategory, ...]
    source_hash: str


@dataclass(frozen=True)
class SelectedReference:
    rank: int
    weight: float
    template: ReferenceTemplate
    method: ReferenceMethod
    bound_doses: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class CompiledItem:
    category_code: str
    rank: int
    template_id: UUID
    template_version: int
    template_code: str
    method_id: UUID
    method_version: int
    method_code: str
    method_name: str
    prescription: dict[str, Any]
    progression_condition: str
    regression_condition: str
    safety_boundaries: tuple[str, ...]


@dataclass(frozen=True)
class CompiledSession:
    weekday: int
    start_minute: int
    estimated_minutes: int
    load_class: str
    scheduling_demand: str
    relative_load: float
    venue_code: str
    purpose: str
    items: tuple[CompiledItem, ...]


@dataclass(frozen=True)
class CompiledWeek:
    week_number: int
    starts_on: date
    intent: str
    deload: bool
    planned_load: float
    sessions: tuple[CompiledSession, ...]


@dataclass(frozen=True)
class CompiledProgram:
    dataset_hash: str
    selected: tuple[SelectedReference, ...]
    weeks: tuple[CompiledWeek, ...]
    trace: tuple[dict[str, Any], ...]


def normalize_equipment_code(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "kettlebells": "kettlebell",
        "resistance_bands": "resistance_band",
        "none": "bodyweight",
        "bike": "cycle_ergometer",
        "rower": "rowing_ergometer",
    }
    return aliases.get(normalized, normalized)


def _minimum_frequency(value: str) -> int:
    try:
        result = int(value.split("-", 1)[0])
    except (TypeError, ValueError) as exc:
        raise ReferenceCompilationError(f"invalid sessions_per_week value: {value}") from exc
    if result not in {1, 2}:
        raise ReferenceCompilationError("reference frequency must be one or two sessions per week")
    return result


def _required_equipment_options(method: ReferenceMethod) -> tuple[frozenset[str], ...]:
    alternatives = METHOD_EQUIPMENT_OPTIONS.get(method.code)
    if alternatives:
        return tuple(
            frozenset(normalize_equipment_code(value) for value in option)
            for option in alternatives
        )
    required = frozenset(
        normalize_equipment_code(value)
        for value in method.equipment
        if not value.endswith("_optional")
        and normalize_equipment_code(value) not in INTRINSIC_EQUIPMENT
    )
    return (required,)


def _equipment_matches_at_venue(
    method: ReferenceMethod,
    context: CompilerContext,
    venue: str,
) -> bool:
    equipment_by_environment = dict(context.equipment_by_environment)
    available = {
        normalize_equipment_code(value)
        for value in equipment_by_environment.get(venue, frozenset())
    }
    if "full_gym" in available:
        available |= FULL_GYM_EQUIPMENT
    return any(option <= (available | {"bodyweight"}) for option in _required_equipment_options(method))


def _normalized_method_environments(method: ReferenceMethod) -> frozenset[str]:
    aliases = {
        "trail_supported": "trail",
        "treadmill": "gym",
        "cycle_ergometer": "gym",
    }
    environments = {aliases.get(value, value) for value in method.environments}
    # A combat gym is a gym subtype, not an assertion that the method is
    # combat-specific. Venue-scoped equipment still has to satisfy the method.
    if "gym" in environments:
        environments.add("combat_gym")
    return frozenset(environments)


def _method_feasible_venues(method: ReferenceMethod, context: CompilerContext) -> frozenset[str]:
    window_venues = {
        venue
        for window in context.availability
        for venue in window.environments
    }
    method_venues = _normalized_method_environments(method)
    candidates = window_venues & method_venues if method_venues else window_venues
    return frozenset(
        venue
        for venue in candidates
        if _equipment_matches_at_venue(method, context, venue)
    )


def _familiarity(method: ReferenceMethod, context: CompilerContext) -> str:
    return dict(context.method_familiarity).get(method.code, "unknown")


def _method_rejection_reasons(method: ReferenceMethod, context: CompilerContext) -> tuple[str, ...]:
    reasons: list[str] = []
    if LEVEL_RANK.get(method.minimum_level, 99) > LEVEL_RANK.get(context.athlete_level, 0):
        reasons.append("minimum_level_not_met")
    if (
        method.applicable_modes
        and not ({"all", context.primary_mode} & set(method.applicable_modes))
        and not context.cross_training_consent
    ):
        reasons.append("training_mode_mismatch")
    if method.sport_codes and context.sport_code not in method.sport_codes:
        reasons.append("sport_not_allowed")
    if method.scope_codes and context.scope_code not in method.scope_codes:
        reasons.append("scope_not_allowed")
    window_venues = {venue for window in context.availability for venue in window.environments}
    method_venues = _normalized_method_environments(method)
    candidate_venues = window_venues & method_venues if method_venues else window_venues
    if not candidate_venues:
        reasons.append("environment_unavailable")
    elif not any(_equipment_matches_at_venue(method, context, venue) for venue in candidate_venues):
        reasons.append("equipment_unavailable_at_compatible_venue")
    familiarity = _familiarity(method, context)
    high_novelty_cost = (
        method.technical_cost >= 4
        or method.impact_cost >= 4
        or method.minimum_level == "advanced"
    )
    close_to_competition = (
        context.days_to_competition is not None
        and 0 <= context.days_to_competition <= 14
    )
    if high_novelty_cost and familiarity in {"unfamiliar", "unknown"}:
        if close_to_competition:
            reasons.append("unfamiliar_high_cost_method_near_competition")
        elif "re_entry_after_clearance" in context.scenario_codes:
            reasons.append("unfamiliar_high_cost_method_during_re_entry")
        elif context.phase_policy.novelty_policy in {"familiar_only", "low_cost_only"}:
            reasons.append("phase_policy_rejects_unfamiliar_high_cost_method")
    if context.phase_policy.novelty_policy == "familiar_only" and familiarity != "familiar":
        reasons.append("phase_requires_familiar_method")
    return tuple(reasons)


def _scale_range(value: dict[str, Any], multiplier: float, *, floor: float = 1.0) -> dict[str, Any]:
    return {
        **value,
        "minimum": max(floor, round(float(value["minimum"]) * multiplier, 2)),
        "maximum": max(floor, round(float(value["maximum"]) * multiplier, 2)),
    }


def _apply_contextual_volume_policy(
    dose: dict[str, Any],
    context: CompilerContext,
    week_index: int,
) -> dict[str, Any]:
    """Apply small, explicit phase/readiness volume policies.

    Intensity and recovery are retained. Competition keeps familiar quality
    work but removes development volume; low readiness halves volume. When a
    method has multiple sets, sets are the only scaled dimension. A continuous
    one-set method scales its work duration/distance instead. This avoids
    multiplying several dose dimensions and accidentally squaring a modifier.
    """
    multiplier = 1.0
    policies: list[str] = []
    phase_multiplier = context.phase_policy.weekly_volume_multipliers[week_index]
    # The released phase policy is the sole dose multiplier. Competition
    # dates gate familiarity and scheduling, but must not silently multiply a
    # second taper onto the already reduced four-week prescription.
    if phase_multiplier != 1.0:
        multiplier *= phase_multiplier
        policies.append(f"{context.phase_code}_phase_volume_policy_v{context.phase_policy.policy_version}")
    if context.readiness == 2:
        multiplier *= 0.50
        policies.append("low_readiness_reduced_volume")
    if multiplier == 1.0:
        return dose

    adjusted = dict(dose)
    sets = int(adjusted.get("sets", 1))
    if sets > 1:
        scaled_sets = sets * multiplier
        adjusted["sets"] = max(1, ceil(scaled_sets))
        # Once a taper drops below one complete set, the one-set safety floor
        # would otherwise make Week 4 identical to Week 3. Apply only the
        # unrepresented residual to the work amount; this realizes the stated
        # multiplier without compounding two independent reductions.
        if scaled_sets < 1:
            for key in ("duration_seconds", "bout_duration_seconds", "duration_minutes", "distance_m", "contacts", "repetitions"):
                value = adjusted.get(key)
                if isinstance(value, dict):
                    adjusted[key] = _scale_range(value, scaled_sets)
                    break
    else:
        for key in ("duration_seconds", "bout_duration_seconds", "duration_minutes", "distance_m", "contacts"):
            if key in adjusted:
                adjusted[key] = _scale_range(adjusted[key], multiplier)
                break
        else:
            repetitions = adjusted.get("repetitions")
            if isinstance(repetitions, dict):
                adjusted["repetitions"] = _scale_range(repetitions, multiplier)
    adjusted["context_adjustment"] = {
        "volume_multiplier": round(multiplier, 3),
        "policies": policies,
        "intensity_and_recovery_retained": True,
    }
    return adjusted


def _select_method(
    template: ReferenceTemplate,
    context: CompilerContext,
) -> tuple[tuple[ReferenceMethod, tuple[dict[str, Any], ...]] | None, list[dict[str, Any]]]:
    eligible: list[tuple[ReferenceMethod, tuple[dict[str, Any], ...]]] = []
    decisions: list[dict[str, Any]] = []
    for method in template.methods:
        reasons = _method_rejection_reasons(method, context)
        if reasons:
            decisions.append({"method_code": method.code, "accepted": False, "reason_codes": list(reasons)})
            continue
        try:
            raw_doses = tuple(
                bind_prescription_to_method(week.prescription, method.accepted_dose_units)
                for week in template.weeks
            )
            # A competition block maintains the familiar Week 1 exercise,
            # intensity and recovery prescription while volume tapers. It must
            # not continue the development progression underneath a taper.
            doses = tuple(
                _apply_contextual_volume_policy(
                    raw_doses[0]
                    if context.phase_policy.progression_mode in {"maintain_week_1", "competition_taper"}
                    else raw_dose,
                    context,
                    week_index,
                )
                for week_index, raw_dose in enumerate(raw_doses)
            )
        except PrescriptionBindingError as exc:
            decisions.append({
                "method_code": method.code,
                "accepted": False,
                "reason_codes": ["dose_binding_failed"],
                "detail": str(exc),
            })
            continue
        eligible.append((method, doses))
    if not eligible:
        return None, decisions
    selected = min(
        eligible,
        key=lambda item: (
            0 if ({"all", context.primary_mode} & set(item[0].applicable_modes)) else 1,
            {"familiar": 0, "previously_exposed": 1, "unknown": 2, "unfamiliar": 3}[
                _familiarity(item[0], context)
            ],
            -LEVEL_RANK[item[0].minimum_level],
            item[0].technical_cost + item[0].impact_cost + item[0].fatigue_cost,
            item[0].sequence,
            item[0].code,
        ),
    )
    for method, _ in eligible:
        decisions.append({
            "method_code": method.code,
            "accepted": method.method_id == selected[0].method_id,
            "reason_codes": [] if method.method_id == selected[0].method_id else ["lower_contextual_suitability_rank"],
            "familiarity": _familiarity(method, context),
        })
    return selected, decisions


def select_references(
    context: CompilerContext,
    priority: PriorityContext,
    templates_by_category: dict[str, tuple[ReferenceTemplate, ...]],
    *,
    maximum_categories: int = 4,
    decision_trace: list[dict[str, Any]] | None = None,
) -> tuple[SelectedReference, ...]:
    if context.pain_unresolved:
        raise ReferenceCompilationError("unresolved pain requires review before a plan can be generated")
    if context.acute_illness:
        raise ReferenceCompilationError("acute illness stops ordinary plan generation")
    if context.readiness == 1:
        raise ReferenceCompilationError("very low readiness requires recovery and reassessment before generation")
    if context.athlete_level not in LEVEL_RANK:
        raise ReferenceCompilationError("athlete level is not supported")
    if not context.availability:
        raise ReferenceCompilationError("at least one availability window is required")
    selected: list[SelectedReference] = []
    for ranked in priority.ranked_categories:
        if len(selected) >= maximum_categories:
            if decision_trace is not None:
                decision_trace.append({
                    "category_code": ranked.category_code,
                    "rank": ranked.rank,
                    "accepted": False,
                    "reason_codes": ["category_limit_reached"],
                })
            continue
        templates = sorted(
            templates_by_category.get(ranked.category_code, ()),
            key=lambda row: (row.code, row.template_version),
        )
        if not templates and decision_trace is not None:
            decision_trace.append({
                "category_code": ranked.category_code,
                "rank": ranked.rank,
                "accepted": False,
                "reason_codes": ["no_released_level_template"],
            })
        for template in templates:
            choice, methods = _select_method(template, context)
            if choice is None:
                if decision_trace is not None:
                    decision_trace.append({
                        "category_code": ranked.category_code,
                        "rank": ranked.rank,
                        "template_code": template.code,
                        "accepted": False,
                        "reason_codes": ["no_compatible_method"],
                        "methods": methods,
                    })
                continue
            method, doses = choice
            selected.append(SelectedReference(ranked.rank, ranked.weight, template, method, doses))
            if decision_trace is not None:
                decision_trace.append({
                    "category_code": ranked.category_code,
                    "rank": ranked.rank,
                    "template_code": template.code,
                    "accepted": True,
                    "reason_codes": [],
                    "methods": methods,
                })
            break
    if not selected:
        raise ReferenceCompilationError("no ranked category has a compatible template and exercise")
    return tuple(selected)


def estimate_block_seconds(dose: dict[str, Any]) -> int:
    """Estimate one exercise block from explicit work and recovery scopes.

    Repetition work uses three seconds per controlled repetition; contact work
    uses two seconds per contact; distance work uses a conservative three
    metres/second with a 15-second minimum effort. Per-side work is doubled.
    Every block receives two minutes for setup and transitions and a five-minute
    minimum. These are deterministic scheduling estimates, not physiological
    workload claims.
    """
    sets = int(dose.get("sets", 1))
    effort_count = 1
    if "duration_seconds" in dose:
        effort_seconds = float(dose["duration_seconds"]["maximum"])
    elif "bout_duration_seconds" in dose:
        effort_seconds = float(dose["bout_duration_seconds"]["maximum"])
    elif "duration_minutes" in dose:
        effort_seconds = float(dose["duration_minutes"]["maximum"]) * 60
    elif "repetitions" in dose and isinstance(dose["repetitions"], dict):
        effort_seconds = float(dose["repetitions"]["maximum"]) * 3
        if dose["repetitions"].get("per_side"):
            effort_seconds *= 2
    elif "contacts" in dose:
        effort_seconds = float(dose["contacts"]["maximum"]) * 2
    elif "distance_m" in dose:
        effort_seconds = max(15, float(dose["distance_m"]["maximum"]) / 3)
        effort_count = int(dose.get("repetitions", 1))
    else:
        raise ReferenceCompilationError("bound prescription has no timeable work dose")
    effort_recovery = dose.get("recovery_between_efforts_seconds")
    set_recovery = dose.get("recovery_between_sets_seconds")
    recovery_seconds = 0.0
    if effort_recovery:
        recovery_seconds += float(effort_recovery["maximum"]) * max(effort_count - 1, 0) * sets
    if set_recovery:
        recovery_seconds += float(set_recovery["maximum"]) * max(sets - 1, 0)
    work_seconds = effort_seconds * effort_count * sets
    return max(5 * 60, int(work_seconds + recovery_seconds + 2 * 60))


def _is_hard(item: SelectedReference) -> bool:
    return (
        item.template.category_code in HARD_CATEGORIES
        or item.method.impact_cost >= 4
        or item.method.fatigue_cost >= 4
    )


def _work_exposure(dose: dict[str, Any]) -> float:
    """Return a within-method volume measure, never an absolute workload."""
    sets = int(dose.get("sets", 1))
    repetitions = dose.get("repetitions", 1)
    if isinstance(repetitions, dict):
        work = float(repetitions["maximum"])
        if repetitions.get("per_side"):
            work *= 2
        repetitions = 1
    elif "contacts" in dose:
        work = float(dose["contacts"]["maximum"])
    elif "duration_seconds" in dose:
        work = float(dose["duration_seconds"]["maximum"])
    elif "bout_duration_seconds" in dose:
        work = float(dose["bout_duration_seconds"]["maximum"])
    elif "duration_minutes" in dose:
        work = float(dose["duration_minutes"]["maximum"])
    elif "distance_m" in dose:
        work = float(dose["distance_m"]["maximum"])
    else:
        raise ReferenceCompilationError("bound prescription has no measurable work exposure")
    return max(0.001, sets * int(repetitions) * work)


def _relative_item_load(item: SelectedReference, week_index: int) -> float:
    baseline = _work_exposure(item.bound_doses[0])
    current = _work_exposure(item.bound_doses[week_index])
    return round(100 * item.weight * current / baseline, 2)


def _ordered(items: Iterable[SelectedReference], block_order: tuple[str, ...]) -> list[SelectedReference]:
    positions = {category: index for index, category in enumerate(block_order)}
    return sorted(items, key=lambda item: (positions.get(item.template.category_code, 999), item.rank))


def _bucket_feasible_venues(
    bucket: Iterable[SelectedReference],
    context: CompilerContext,
) -> frozenset[str]:
    venue_sets = [_method_feasible_venues(item.method, context) for item in bucket]
    if not venue_sets:
        return frozenset()
    feasible = set(venue_sets[0])
    for venues in venue_sets[1:]:
        feasible &= set(venues)
    return frozenset(feasible)


def _pick_windows(
    windows: tuple[AvailabilitySlot, ...],
    required_minutes: tuple[int, ...],
    required_venues: tuple[frozenset[str], ...],
    hard_flags: tuple[bool, ...],
    external_hard_days: frozenset[int],
    external_hard_dates: frozenset[date],
    competition_dates: tuple[date, ...],
    week_starts_on: date,
) -> tuple[tuple[AvailabilitySlot, str], ...] | None:
    bounded = tuple(sorted(windows, key=lambda row: (row.weekday, row.start_minute, sorted(row.environments))))
    assigned: list[tuple[int, AvailabilitySlot, str, bool]] = []

    def assign(index: int) -> bool:
        if index == len(required_minutes):
            return True
        for window_index, window in enumerate(bounded):
            if any(existing_index == window_index for existing_index, *_ in assigned):
                continue
            if window.duration_minutes < required_minutes[index]:
                continue
            venues = sorted(required_venues[index] & window.environments)
            if not venues:
                continue
            if hard_flags[index]:
                day = window.weekday
                if any(
                    min(abs(day - external_day), 7 - abs(day - external_day)) < 2
                    for external_day in external_hard_days
                ):
                    continue
                scheduled_date = week_starts_on + timedelta(days=day)
                if any(
                    abs((scheduled_date - external_date).days) < 2
                    for external_date in external_hard_dates
                ):
                    continue
                if any(
                    0 <= (competition_date - scheduled_date).days <= 3
                    for competition_date in competition_dates
                ):
                    continue
                if any(
                    existing_hard
                    and min(abs(day - existing_window.weekday), 7 - abs(day - existing_window.weekday)) < 2
                    for _, existing_window, _, existing_hard in assigned
                ):
                    continue
            assigned.append((window_index, window, venues[0], hard_flags[index]))
            if assign(index + 1):
                return True
            assigned.pop()
        return False

    if not assign(0):
        return None
    return tuple((window, venue) for _, window, venue, _ in assigned)


def _compile_week(
    context: CompilerContext,
    priority: PriorityContext,
    selected: tuple[SelectedReference, ...],
    week_index: int,
) -> CompiledWeek:
    session_count = max(_minimum_frequency(item.template.weeks[week_index].sessions_per_week) for item in selected)
    session_count = min(session_count, context.phase_policy.maximum_sessions_per_week)
    buckets: list[list[SelectedReference]] = [[] for _ in range(session_count)]
    for item in selected:
        frequency = _minimum_frequency(item.template.weeks[week_index].sessions_per_week)
        frequency = min(frequency, context.phase_policy.maximum_sessions_per_week)
        used_buckets: set[int] = set()
        for _ in range(frequency):
            compatible = [
                index
                for index, bucket in enumerate(buckets)
                if index not in used_buckets
                and _bucket_feasible_venues((*bucket, item), context)
            ]
            if compatible:
                target = min(
                    compatible,
                    key=lambda index: (
                        sum(estimate_block_seconds(value.bound_doses[week_index]) for value in buckets[index]),
                        index,
                    ),
                )
                buckets[target].append(item)
                used_buckets.add(target)
            else:
                if len(buckets) < context.phase_policy.maximum_sessions_per_week:
                    buckets.append([item])
                    used_buckets.add(len(buckets) - 1)
                else:
                    raise ReferenceCompilationError(
                        "phase session cap cannot accommodate the selected venue-separated methods"
                    )
    buckets = [bucket for bucket in buckets if bucket]
    buckets = [_ordered(bucket, priority.block_order) for bucket in buckets]
    durations = tuple(
        max(15, (sum(estimate_block_seconds(item.bound_doses[week_index]) for item in bucket) + 59) // 60)
        for bucket in buckets
    )
    if any(value > context.maximum_session_minutes for value in durations):
        raise ReferenceCompilationError("selected references exceed the athlete's maximum session duration")
    required_venues = tuple(_bucket_feasible_venues(bucket, context) for bucket in buckets)
    if any(not venues for venues in required_venues):
        raise ReferenceCompilationError("selected methods do not share a feasible venue within their session")
    hard_flags = tuple(any(_is_hard(item) for item in bucket) for bucket in buckets)
    week_starts_on = context.starts_on + timedelta(weeks=week_index)
    windows = _pick_windows(
        context.availability,
        durations,
        required_venues,
        hard_flags,
        context.external_hard_days,
        context.external_hard_dates,
        context.competition_dates,
        week_starts_on,
    )
    if windows is None:
        raise ReferenceCompilationError("availability cannot fit the selected references with safe hard-day spacing")
    sessions: list[CompiledSession] = []
    week_load = 0.0
    for bucket, scheduled_window, duration in zip(buckets, windows, durations, strict=True):
        window, venue = scheduled_window
        relative_load = round(sum(_relative_item_load(item, week_index) for item in bucket), 2)
        week_load += relative_load
        items = tuple(
            CompiledItem(
                category_code=item.template.category_code,
                rank=item.rank,
                template_id=item.template.template_id,
                template_version=item.template.template_version,
                template_code=item.template.code,
                method_id=item.method.method_id,
                method_version=item.method.method_version,
                method_code=item.method.code,
                method_name=item.method.name,
                prescription=item.bound_doses[week_index],
                progression_condition=item.template.weeks[week_index].progression_condition,
                regression_condition=item.template.weeks[week_index].regression_condition,
                safety_boundaries=item.method.safety_boundaries,
            )
            for item in bucket
        )
        sessions.append(CompiledSession(
            weekday=window.weekday,
            start_minute=window.start_minute,
            estimated_minutes=duration,
            load_class="hard" if any(_is_hard(item) for item in bucket) else "moderate",
            scheduling_demand="high" if any(_is_hard(item) for item in bucket) else "standard",
            relative_load=relative_load,
            venue_code=venue,
            purpose="; ".join(item.template.purpose for item in bucket),
            items=items,
        ))
    intents = tuple(dict.fromkeys(item.template.weeks[week_index].intent for item in selected))
    intent = "; ".join(intents)
    if context.phase_policy.progression_mode == "competition_taper":
        intent = (
            "competition phase: familiar quality exposure with reduced development volume"
            if week_index < 2
            else "competition taper: reduced familiar quality exposure"
            if week_index == 2
            else "competition primer: short familiar quality exposure"
        )
    return CompiledWeek(
        week_number=week_index + 1,
        starts_on=week_starts_on,
        intent=intent,
        deload=False,
        planned_load=round(week_load, 2),
        sessions=tuple(sessions),
    )


def compile_program(
    context: CompilerContext,
    priority: PriorityContext,
    templates_by_category: dict[str, tuple[ReferenceTemplate, ...]],
    dataset_hash: str,
) -> CompiledProgram:
    if context.starts_on.weekday() != 0:
        raise ReferenceCompilationError("training plans must start on a Monday")
    candidate_trace: list[dict[str, Any]] = []
    maximum_categories = context.phase_policy.maximum_categories
    if context.readiness == 2:
        maximum_categories = min(maximum_categories, 2)
    selected = list(select_references(
        context,
        priority,
        templates_by_category,
        maximum_categories=maximum_categories,
        decision_trace=candidate_trace,
    ))
    effective_primary = next(
        (item.template.category_code for item in selected if item.template.category_code == priority.primary_category),
        selected[0].template.category_code,
    )
    # If rank 1 has no compatible method, selection transparently continues
    # through the existing sport-priority row. There is no second fallback
    # graph and no hidden category substitution.
    # Keep the primary category; remove only the lowest-priority optional
    # category when actual windows cannot fit the combined weekly dose.
    schedule_adjustments: list[dict[str, Any]] = []
    while True:
        try:
            weeks = tuple(_compile_week(context, priority, tuple(selected), index) for index in range(4))
            break
        except ReferenceCompilationError:
            removable = [item for item in selected if item.template.category_code != effective_primary]
            if not removable:
                raise
            removed = max(removable, key=lambda item: item.rank)
            selected.remove(removed)
            schedule_adjustments.append({
                "category_code": removed.template.category_code,
                "rank": removed.rank,
                "reason_code": "removed_to_satisfy_schedule_constraints",
            })
    phase_week_four_reduction = (
        context.phase_policy.weekly_volume_multipliers[3]
        < max(context.phase_policy.weekly_volume_multipliers[:3])
    )
    week4_policy_is_deload = phase_week_four_reduction or (
        context.phase_policy.progression_mode != "maintain_week_1"
        and all("deload" in item.template.week_4_policy.lower() for item in selected)
    )
    if week4_policy_is_deload:
        if (
            context.phase_policy.progression_mode != "competition_taper"
            and weeks[3].planned_load >= max(week.planned_load for week in weeks[:3])
        ):
            raise ReferenceCompilationError("week four policy requires a measurable workload reduction")
        weeks = (*weeks[:3], replace(weeks[3], deload=True))
    return CompiledProgram(
        dataset_hash=dataset_hash,
        selected=tuple(selected),
        weeks=weeks,
        trace=(
            {
                "decision": "exact_priority_row_selected",
                "source_hash": priority.source_hash,
                "sport_code": context.sport_code,
                "scope_code": context.scope_code,
                "phase_code": context.phase_code,
                "goal_code": context.goal_code,
                "scenario_codes": sorted(context.scenario_codes),
                "phase_policy": {
                    "version": context.phase_policy.policy_version,
                    "progression_mode": context.phase_policy.progression_mode,
                    "maximum_categories": context.phase_policy.maximum_categories,
                    "maximum_sessions_per_week": context.phase_policy.maximum_sessions_per_week,
                    "novelty_policy": context.phase_policy.novelty_policy,
                    "source_hash": context.phase_policy.source_hash,
                },
            },
            {
                "decision": "ranked_compatible_category_resolved",
                "requested": priority.primary_category,
                "selected": effective_primary,
                "primary_skipped": effective_primary != priority.primary_category,
                "selection_strategy": "first_ranked_compatible_category",
            },
            {
                "decision": "compatible_references_selected",
                "categories": [item.template.category_code for item in selected],
                "maximum_categories": maximum_categories,
            },
            {"decision": "four_week_schedule_validated", "session_counts": [len(week.sessions) for week in weeks]},
            {"decision": "candidate_evaluation", "candidates": candidate_trace},
            {"decision": "schedule_adjustments", "adjustments": schedule_adjustments},
            {
                "decision": "relative_workload_validated",
                "definition": "plan-relative within-method volume index",
                "weekly_values": [week.planned_load for week in weeks],
                "week_four_deload": weeks[3].deload,
            },
            {
                "decision": "contextual_volume_policy",
                "phase_code": context.phase_code,
                "readiness": context.readiness,
                "competition_session_cap": 1 if context.phase_code == "competition" else None,
            },
        ),
    )

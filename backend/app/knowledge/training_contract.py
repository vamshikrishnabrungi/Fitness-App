from __future__ import annotations

from typing import Literal


AthleteLevel = Literal["beginner", "intermediate", "advanced"]
TrainingPhase = Literal[
    "general_preparation",
    "specific_preparation",
    "competition",
    "transition",
]
TrainingGoal = Literal[
    "general_performance",
    "strength_power",
    "speed_movement",
    "conditioning",
]


# A focused goal is allowed to use any sport-specific category mix, but its
# primary category must express the requested adaptation. The families overlap
# deliberately: anaerobic power can be a speed outcome in cyclic sports and a
# conditioning outcome when used as an energy-system objective.
GOAL_CATEGORY_FAMILIES: dict[TrainingGoal, frozenset[str]] = {
    "general_performance": frozenset(),
    "strength_power": frozenset({
        "maximum_strength", "explosive_strength", "vertical_power",
        "horizontal_power", "lateral_power", "rotational_power",
        "upper_body_power", "yielding_isometric_force",
        "overcoming_isometric_force", "eccentric_capacity",
    }),
    "speed_movement": frozenset({
        "acceleration", "maximum_velocity", "speed_endurance", "deceleration",
        "planned_change_of_direction", "reactive_agility", "landing_capacity",
        "reactive_elastic_strength", "extensive_plyometrics",
        "horizontal_bounding", "lateral_elastic_strength", "anaerobic_power",
        "explosive_strength", "vertical_power", "horizontal_power",
        "lateral_power", "rotational_power", "upper_body_power",
    }),
    "conditioning": frozenset({
        "aerobic_capacity", "threshold_capacity", "high_intensity_aerobic_power",
        "anaerobic_power", "anaerobic_capacity", "repeated_sprint_ability",
        "repeated_high_intensity_ability", "local_muscular_endurance",
    }),
}


COMPETITION_LEVEL_TO_ATHLETE_LEVEL: dict[str, AthleteLevel] = {
    "recreational": "beginner",
    "club": "intermediate",
    "regional": "advanced",
    "national": "advanced",
    "international": "advanced",
}

GOAL_ALIASES: dict[str, TrainingGoal] = {
    "athletic": "general_performance",
    "general": "general_performance",
    "general_fitness": "general_performance",
    "general_performance": "general_performance",
    "muscle": "strength_power",
    "strength": "strength_power",
    "strength_power": "strength_power",
    "run_faster": "speed_movement",
    "jump_higher": "speed_movement",
    "speed_movement": "speed_movement",
    "conditioning": "conditioning",
    "endurance": "conditioning",
    "lose_weight": "conditioning",
}

PHASE_ALIASES: dict[str, TrainingPhase] = {
    "general": "general_preparation",
    "off_season": "general_preparation",
    "general_preparation": "general_preparation",
    "pre_season": "specific_preparation",
    "specific_preparation": "specific_preparation",
    "in_season": "competition",
    "competition": "competition",
    "transition": "transition",
}

# These values are the exact scope keys in the production priority matrix.
SPORT_SCOPE_VALUES: dict[str, tuple[str, frozenset[str]]] = {
    "badminton": ("format", frozenset({"singles", "doubles"})),
    "basketball": ("role", frozenset({"guard", "wing", "big"})),
    "boxing": ("format", frozenset({"amateur", "professional"})),
    "cricket": ("role", frozenset({"batter", "pace_bowler", "spin_bowler", "wicketkeeper", "all_rounder"})),
    "cycling": ("event", frozenset({"fitness_endurance", "road_endurance", "sprint", "time_trial"})),
    "football": ("role", frozenset({"goalkeeper", "central_defender", "fullback_wingback", "central_midfielder", "winger", "striker"})),
    "mma": ("format", frozenset({"three_round", "five_round"})),
    "running": ("event", frozenset({"100m", "200m", "400m", "5k", "10k", "half_marathon", "marathon", "run_walk"})),
    "swimming": (
        "event_discipline",
        frozenset(
            f"{event}:{discipline}"
            for event in ("sprint", "middle_distance", "distance")
            for discipline in ("freestyle", "backstroke", "breaststroke", "butterfly", "individual_medley")
        ),
    ),
    "tennis": ("format", frozenset({"singles", "doubles"})),
    "volleyball": ("role", frozenset({"setter", "outside_hitter", "middle_blocker", "opposite", "libero"})),
}


def normalize_goal(value: str) -> TrainingGoal:
    try:
        return GOAL_ALIASES[value.strip().lower()]
    except KeyError as exc:
        raise ValueError("goal is not supported by the training priority matrix") from exc


def normalize_phase(value: str) -> TrainingPhase:
    try:
        return PHASE_ALIASES[value.strip().lower()]
    except KeyError as exc:
        raise ValueError("season phase is not supported by the training priority matrix") from exc


def athlete_level(competition_level: str) -> AthleteLevel:
    try:
        return COMPETITION_LEVEL_TO_ATHLETE_LEVEL[competition_level]
    except KeyError as exc:
        raise ValueError("competition level has no training-template mapping") from exc


def sport_scope_key(
    sport_code: str,
    *,
    event_code: str | None,
    role_code: str | None,
    discipline_code: str | None,
    format_code: str | None,
) -> tuple[str, str]:
    try:
        scope_type, allowed = SPORT_SCOPE_VALUES[sport_code]
    except KeyError as exc:
        raise ValueError("sport is not supported by the training priority matrix") from exc
    if scope_type == "role":
        value = role_code
    elif scope_type == "event":
        value = event_code
    elif scope_type == "format":
        value = format_code
    else:
        value = f"{event_code}:{discipline_code}" if event_code and discipline_code else None
    if value not in allowed:
        raise ValueError(f"{sport_code} requires a valid {scope_type.replace('_', ' ')}")
    return scope_type, value

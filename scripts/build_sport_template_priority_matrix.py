#!/usr/bin/env python3
"""Build the sport-scope to four-week-template priority matrix."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Backend data files" / "sport models" / "sport_role_phase_goal_priority_matrix.csv"
SUMMARY = ROOT / "Backend data files" / "sport models" / "SPORT_TEMPLATE_PRIORITY_MATRIX.md"
COVERAGE = ROOT / "Backend data files" / "exercise templates" / "category_coverage.json"

PHASES = ("general_preparation", "specific_preparation", "competition", "transition")
GOALS = ("general_performance", "strength_power", "speed_movement", "conditioning")

SCOPES = {
    "running": ("event", ("run_walk", "5k", "10k", "half_marathon", "marathon", "100m", "200m", "400m")),
    "football": ("role", ("goalkeeper", "central_defender", "fullback_wingback", "central_midfielder", "winger", "striker")),
    "cricket": ("role", ("batter", "wicketkeeper", "pace_bowler", "spin_bowler", "all_rounder")),
    "basketball": ("role", ("guard", "wing", "big")),
    "volleyball": ("role", ("setter", "outside_hitter", "opposite", "middle_blocker", "libero")),
    "badminton": ("format", ("singles", "doubles")),
    "tennis": ("format", ("singles", "doubles")),
    "cycling": ("event", ("fitness_endurance", "road_endurance", "time_trial", "sprint")),
    "swimming": ("event_discipline", tuple(
        f"{event}:{discipline}"
        for event in ("sprint", "middle_distance", "distance")
        for discipline in ("freestyle", "backstroke", "breaststroke", "butterfly", "individual_medley")
    )),
    "boxing": ("format", ("amateur", "professional")),
    "mma": ("format", ("three_round", "five_round")),
}

# Scores are ordinal retrieval weights, not claims about percentage contribution.
BASE = {
    "running": {"aerobic_capacity":9,"threshold_capacity":8,"maximum_strength":6,"calf_soleus_capacity":7,"hamstring_capacity":6,"trunk_force_transfer":4,"mobility_range_capacity":3},
    "football": {"acceleration":10,"deceleration":10,"planned_change_of_direction":9,"reactive_agility":9,"repeated_sprint_ability":9,"maximum_velocity":8,"maximum_strength":7,"hamstring_capacity":7,"adductor_capacity":7,"calf_soleus_capacity":6,"reactive_elastic_strength":6},
    "cricket": {"rotational_power":9,"acceleration":7,"maximum_strength":7,"trunk_force_transfer":8,"shoulder_capacity":7,"repeated_high_intensity_ability":6,"aerobic_capacity":5,"hamstring_capacity":5},
    "basketball": {"acceleration":9,"deceleration":10,"planned_change_of_direction":9,"reactive_agility":9,"vertical_power":10,"landing_capacity":10,"repeated_high_intensity_ability":8,"maximum_strength":7,"calf_soleus_capacity":7},
    "volleyball": {"vertical_power":10,"landing_capacity":10,"reactive_elastic_strength":9,"maximum_strength":8,"shoulder_capacity":7,"planned_change_of_direction":6,"acceleration":6,"calf_soleus_capacity":7},
    "badminton": {"reactive_agility":10,"deceleration":10,"planned_change_of_direction":9,"acceleration":9,"repeated_high_intensity_ability":9,"reactive_elastic_strength":8,"landing_capacity":8,"rotational_power":7,"calf_soleus_capacity":7,"adductor_capacity":7},
    "tennis": {"reactive_agility":10,"deceleration":9,"planned_change_of_direction":9,"acceleration":9,"rotational_power":9,"repeated_high_intensity_ability":8,"shoulder_capacity":7,"trunk_force_transfer":8,"aerobic_capacity":6},
    "cycling": {"aerobic_capacity":10,"threshold_capacity":10,"high_intensity_aerobic_power":8,"maximum_strength":6,"local_muscular_endurance":7,"trunk_force_transfer":5,"recovery_management":4},
    "swimming": {"aerobic_capacity":9,"threshold_capacity":8,"high_intensity_aerobic_power":7,"shoulder_capacity":9,"trunk_force_transfer":7,"maximum_strength":5,"mobility_range_capacity":5,"recovery_management":4},
    "boxing": {"upper_body_power":9,"rotational_power":9,"high_intensity_aerobic_power":9,"anaerobic_capacity":8,"repeated_high_intensity_ability":9,"acceleration":7,"deceleration":7,"trunk_force_transfer":8,"shoulder_capacity":8,"neck_capacity":7},
    "mma": {"maximum_strength":9,"isometric_force_capacity":9,"local_muscular_endurance":8,"high_intensity_aerobic_power":9,"anaerobic_capacity":8,"repeated_high_intensity_ability":9,"explosive_strength":8,"trunk_force_transfer":8,"grip_capacity":8,"neck_capacity":8},
}

OVERRIDES = {
    ("running","run_walk"): {"aerobic_capacity":4,"mobility_range_capacity":2,"maximum_strength":1,"calf_soleus_capacity":2,"threshold_capacity":-5},
    ("running","5k"): {"threshold_capacity":3,"high_intensity_aerobic_power":3,"aerobic_capacity":1},
    ("running","10k"): {"threshold_capacity":3,"aerobic_capacity":2,"high_intensity_aerobic_power":1},
    ("running","half_marathon"): {"aerobic_capacity":3,"threshold_capacity":2,"calf_soleus_capacity":1},
    ("running","marathon"): {"aerobic_capacity":5,"threshold_capacity":1,"calf_soleus_capacity":2,"hamstring_capacity":1},
    ("running","100m"): {"acceleration":12,"maximum_velocity":12,"explosive_strength":10,"horizontal_power":9,"maximum_strength":8,"reactive_elastic_strength":8,"speed_endurance":5,"aerobic_capacity":-7,"threshold_capacity":-7},
    ("running","200m"): {"acceleration":10,"maximum_velocity":11,"speed_endurance":10,"explosive_strength":9,"horizontal_power":8,"maximum_strength":7,"reactive_elastic_strength":7,"aerobic_capacity":-6,"threshold_capacity":-6},
    ("running","400m"): {"speed_endurance":12,"anaerobic_capacity":10,"maximum_velocity":9,"acceleration":7,"explosive_strength":7,"aerobic_capacity":-4,"threshold_capacity":-5},
    ("football","goalkeeper"): {"vertical_power":5,"lateral_power":4,"landing_capacity":5,"reactive_agility":3,"maximum_velocity":-3,"repeated_sprint_ability":-2},
    ("football","central_midfielder"): {"aerobic_capacity":5,"threshold_capacity":3,"repeated_sprint_ability":3},
    ("football","winger"): {"maximum_velocity":5,"acceleration":4,"repeated_sprint_ability":3},
    ("football","fullback_wingback"): {"maximum_velocity":4,"repeated_sprint_ability":4,"aerobic_capacity":3},
    ("football","central_defender"): {"maximum_strength":3,"vertical_power":3,"acceleration":2},
    ("cricket","pace_bowler"): {"speed_endurance":4,"hamstring_capacity":5,"calf_soleus_capacity":4,"trunk_force_transfer":3,"shoulder_capacity":3,"aerobic_capacity":3},
    ("cricket","wicketkeeper"): {"reactive_agility":5,"isometric_force_capacity":4,"local_muscular_endurance":4,"deceleration":3},
    ("cricket","batter"): {"rotational_power":5,"acceleration":3,"reactive_agility":2},
    ("cricket","spin_bowler"): {"rotational_power":4,"shoulder_capacity":3,"trunk_force_transfer":4},
    ("basketball","guard"): {"acceleration":4,"deceleration":3,"reactive_agility":4,"maximum_velocity":2},
    ("basketball","wing"): {"maximum_velocity":3,"vertical_power":3,"planned_change_of_direction":2},
    ("basketball","big"): {"vertical_power":4,"landing_capacity":4,"maximum_strength":4,"maximum_velocity":-2},
    ("volleyball","middle_blocker"): {"vertical_power":5,"landing_capacity":5,"reactive_elastic_strength":4},
    ("volleyball","libero"): {"reactive_agility":6,"deceleration":4,"planned_change_of_direction":4,"vertical_power":-3},
    ("volleyball","setter"): {"reactive_agility":4,"shoulder_capacity":3,"vertical_power":1},
    ("badminton","singles"): {"aerobic_capacity":5,"repeated_high_intensity_ability":3,"deceleration":2},
    ("badminton","doubles"): {"reactive_agility":4,"acceleration":4,"upper_body_power":2},
    ("tennis","singles"): {"aerobic_capacity":4,"threshold_capacity":2,"repeated_high_intensity_ability":3},
    ("tennis","doubles"): {"reactive_agility":3,"acceleration":3,"upper_body_power":2},
    ("cycling","fitness_endurance"): {"aerobic_capacity":4,"threshold_capacity":-2},
    ("cycling","road_endurance"): {"aerobic_capacity":4,"threshold_capacity":3,"high_intensity_aerobic_power":2},
    ("cycling","time_trial"): {"threshold_capacity":5,"aerobic_capacity":3,"trunk_force_transfer":2},
    ("cycling","sprint"): {"anaerobic_power":12,"anaerobic_capacity":8,"maximum_strength":7,"explosive_strength":7,"aerobic_capacity":-3,"threshold_capacity":-3},
    ("swimming","sprint"): {"anaerobic_power":10,"anaerobic_capacity":8,"upper_body_power":6,"maximum_strength":4,"aerobic_capacity":-3},
    ("swimming","middle_distance"): {"threshold_capacity":4,"high_intensity_aerobic_power":4,"anaerobic_capacity":3},
    ("swimming","distance"): {"aerobic_capacity":5,"threshold_capacity":4,"high_intensity_aerobic_power":1},
    ("boxing","professional"): {"aerobic_capacity":4,"threshold_capacity":3,"repeated_high_intensity_ability":3,"neck_capacity":1},
    ("boxing","amateur"): {"anaerobic_power":3,"high_intensity_aerobic_power":3,"reactive_agility":3},
    ("mma","five_round"): {"aerobic_capacity":4,"threshold_capacity":3,"repeated_high_intensity_ability":3},
    ("mma","three_round"): {"anaerobic_power":3,"anaerobic_capacity":3,"explosive_strength":2},
}

GOAL_BIAS = {
    "general_performance": {},
    "strength_power": {"maximum_strength":6,"explosive_strength":6,"vertical_power":4,"horizontal_power":4,"lateral_power":4,"rotational_power":4,"upper_body_power":4,"isometric_force_capacity":3},
    "speed_movement": {"acceleration":6,"maximum_velocity":6,"speed_endurance":4,"deceleration":5,"planned_change_of_direction":5,"reactive_agility":5,"landing_capacity":3,"reactive_elastic_strength":3},
    "conditioning": {"aerobic_capacity":6,"threshold_capacity":6,"high_intensity_aerobic_power":6,"anaerobic_power":4,"anaerobic_capacity":5,"repeated_sprint_ability":5,"repeated_high_intensity_ability":5},
}

PHASE_BIAS = {
    "general_preparation": {"maximum_strength":3,"aerobic_capacity":3,"local_muscular_endurance":2,"mobility_range_capacity":2,"calf_soleus_capacity":1,"hamstring_capacity":1,"adductor_capacity":1,"shoulder_capacity":1,"trunk_force_transfer":1,"neck_capacity":1,"grip_capacity":1},
    "specific_preparation": {"acceleration":3,"maximum_velocity":2,"speed_endurance":2,"deceleration":3,"planned_change_of_direction":3,"reactive_agility":3,"explosive_strength":3,"vertical_power":2,"horizontal_power":2,"lateral_power":2,"rotational_power":2,"upper_body_power":2,"reactive_elastic_strength":2,"high_intensity_aerobic_power":2,"repeated_sprint_ability":2,"repeated_high_intensity_ability":2},
    "competition": {"performance_preparation":4,"recovery_management":4,"maximum_strength":-2,"local_muscular_endurance":-2,"anaerobic_capacity":-2},
    "transition": {"recovery_management":6,"aerobic_capacity":2,"mobility_range_capacity":3,"performance_preparation":2,"anaerobic_capacity":-5,"repeated_sprint_ability":-5,"repeated_high_intensity_ability":-5,"maximum_velocity":-4},
}

SESSION_PRECEDENCE = {
    "performance_preparation": 0, "acceleration": 1, "maximum_velocity": 1,
    "reactive_agility": 1, "deceleration": 2, "planned_change_of_direction": 2,
    "landing_capacity": 2, "extensive_plyometrics": 3,
    "reactive_elastic_strength": 3, "horizontal_bounding": 3,
    "lateral_elastic_strength": 3, "explosive_strength": 4,
    "vertical_power": 4, "horizontal_power": 4, "lateral_power": 4,
    "rotational_power": 4, "upper_body_power": 4, "maximum_strength": 5,
    "yielding_isometric_force": 6, "overcoming_isometric_force": 6,
    "eccentric_capacity": 6, "calf_soleus_capacity": 6,
    "hamstring_capacity": 6, "adductor_capacity": 6, "shoulder_capacity": 6,
    "trunk_force_transfer": 6, "neck_capacity": 6, "grip_capacity": 6,
    "local_muscular_endurance": 7, "aerobic_capacity": 8,
    "threshold_capacity": 8, "high_intensity_aerobic_power": 8,
    "anaerobic_power": 8, "anaerobic_capacity": 8,
    "repeated_sprint_ability": 8, "repeated_high_intensity_ability": 8,
    "speed_endurance": 8, "mobility_range_capacity": 9, "recovery_management": 10,
}


def add(scores: dict[str, float], changes: dict[str, float]) -> None:
    for category, value in changes.items():
        scores[category] = scores.get(category, 0) + value


def add_existing(scores: dict[str, float], changes: dict[str, float]) -> None:
    """Re-rank applicable demands without inventing a sport demand."""
    for category, value in changes.items():
        if category in scores:
            scores[category] += value


def main() -> None:
    categories = {item["category_code"] for item in json.loads(COVERAGE.read_text())["categories"]}
    rows = []
    for sport, (scope_type, scope_values) in SCOPES.items():
        for scope in scope_values:
            scope_head = scope.split(":", 1)[0]
            for phase in PHASES:
                for goal in GOALS:
                    scores = dict(BASE[sport])
                    add(scores, OVERRIDES.get((sport, scope), {}))
                    add(scores, OVERRIDES.get((sport, scope_head), {}))
                    add_existing(scores, PHASE_BIAS[phase])
                    # Preparation and recovery are phase-level structures and
                    # may be introduced even when they are not a defining
                    # competition demand.
                    if phase in {"competition", "transition"}:
                        for category in ("performance_preparation", "recovery_management"):
                            if category in PHASE_BIAS[phase]:
                                scores[category] = PHASE_BIAS[phase][category]
                    add_existing(scores, GOAL_BIAS[goal])
                    ranked = [(category, score) for category, score in scores.items() if category in categories and score > 0]
                    ranked.sort(key=lambda item: (-item[1], SESSION_PRECEDENCE.get(item[0], 7), item[0]))
                    top = ranked[:8]
                    ordered = sorted((category for category, _ in top), key=lambda category: (SESSION_PRECEDENCE.get(category, 7), -dict(top)[category], category))
                    row = {
                        "sport_code": sport, "scope_type": scope_type, "scope_code": scope,
                        "phase_code": phase, "goal_code": goal,
                        "primary_template_category": top[0][0],
                        "session_block_order": ";".join(ordered),
                        "priority_basis": "ordinal evidence-informed retrieval weighting; athlete deficits, schedule, safety and external load may lower or omit a category",
                    }
                    for index in range(8):
                        row[f"rank_{index+1}_category"] = top[index][0] if index < len(top) else ""
                        row[f"rank_{index+1}_weight"] = min(1.0, round(top[index][1] / 20, 3)) if index < len(top) else ""
                    rows.append(row)

    fields = ["sport_code","scope_type","scope_code","phase_code","goal_code","primary_template_category","session_block_order","priority_basis"]
    fields += [value for index in range(1,9) for value in (f"rank_{index}_category",f"rank_{index}_weight")]
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)

    SUMMARY.write_text(
        "# Sport, role, phase and goal priority matrix\n\n"
        f"The machine-readable matrix contains **{len(rows)} rows** across **{len(SCOPES)} launch sports**, "
        f"**{sum(len(v[1]) for v in SCOPES.values())} event/role/format scopes**, four phases and four goal contexts.\n\n"
        "Each row ranks only existing four-week template categories. Weights are ordinal retrieval weights, not percentages of performance and not automatic weekly prescriptions. The athlete's deficit, level, schedule, external practice, equipment, readiness and safety rules may remove or demote a category.\n\n"
        "`session_block_order` applies when selected categories share a session: preparation first; fresh speed/perception work; landing/COD; plyometric/power; strength; supporting capacity; conditioning; recovery. The primary session objective is never buried merely to obey a global order.\n",
        encoding="utf-8",
    )
    print(json.dumps({"rows":len(rows),"sports":len(SCOPES),"scopes":sum(len(v[1]) for v in SCOPES.values()),"phases":len(PHASES),"goals":len(GOALS)},indent=2))


if __name__ == "__main__":
    main()

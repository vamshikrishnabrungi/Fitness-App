#!/usr/bin/env python3
"""Build the curated, deduplicated exercise-review rows used by Excel.

This does not mutate MongoDB. Existing instructions are exposed only as
internal research notes and are explicitly marked for rewrite before product use.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "Research materials" / "audits" / "exercise library" / "exercise_inventory.json"


GROUPS = OrderedDict({
    "Lower Body Strength": [
        "Bodyweight Squat", "Goblet Squat", "Barbell Back Squat", "Barbell Front Squat",
        "Box Squat", "Safety Bar Squat", "Belt Squat", "Landmine Squat", "Leg Press",
        "Single-Leg Leg Press", "Bulgarian Split Squat", "Dumbbell Split Squat", "Reverse Lunge",
        "Forward Lunge", "Lateral Lunge", "Walking Lunge", "Step-Up", "Lateral Step-Up",
        "Cossack Squat", "Trap Bar Deadlift", "Conventional Barbell Deadlift",
        "Barbell Romanian Deadlift", "Dumbbell Romanian Deadlift", "Single-Leg Romanian Deadlift",
        "Kettlebell Deadlift", "Barbell Hip Thrust", "Dumbbell Hip Thrust", "Single-Leg Hip Thrust",
        "Glute Bridge", "Nordic Hamstring Curl", "Assisted Nordic Hamstring Curl",
        "Slider Hamstring Curl", "Seated Leg Curl", "Leg Extension", "Standing Calf Raise",
        "Seated Calf Raise", "Single-Leg Calf Raise", "Tibialis Raise",
    ],
    "Upper Body Strength": [
        "Negative Push-Up", "Push-Up", "Dumbbell Floor Press", "Barbell Bench Press",
        "Dumbbell Bench Press", "Incline Dumbbell Bench Press", "Neutral-Grip Dumbbell Bench Press",
        "Barbell Overhead Press", "Dumbbell Shoulder Press", "Half-Kneeling Landmine Press",
        "Landmine Press", "Machine Chest Press", "Machine Shoulder Press", "Cable Chest Press",
        "Band-Assisted Pull-Up", "Pull-Up", "Chin-Up", "Inverted Row", "Lat Pulldown",
        "Neutral-Grip Lat Pulldown", "One-Arm Dumbbell Row", "Barbell Bent-Over Row",
        "Chest-Supported Dumbbell Row", "Seated Cable Row", "Machine Row", "Landmine Row",
        "Face Pull", "Band Pull-Apart", "Push-Up Plus", "Scapular Pull-Up",
        "Band External Rotation at Side", "Side-Lying Dumbbell External Rotation",
        "Prone Y-T-W Raise", "Wall Slide with Lift-Off",
    ],
    "Trunk and Carries": [
        "Dead Bug", "Bird Dog", "Bear Plank Hold", "Front Plank", "Side Plank from Knees",
        "Side Plank", "Long-Lever Plank", "Plank Shoulder Tap", "Plank Drag-Through",
        "Stability Ball Stir-the-Pot", "Stability Ball Rollout", "Pallof Press",
        "Pallof Press Iso Hold", "Half-Kneeling Pallof Press", "Cable Wood Chop",
        "Half-Kneeling Cable Chop", "Cable Lift", "Half-Kneeling Cable Lift",
        "Landmine Rotation", "Farmer's Carry", "Suitcase Carry", "Single-Arm Front Rack Carry",
        "Kettlebell Front Rack Carry", "Overhead Carry", "Bear Hug Carry",
    ],
    "Athletic Accessories": [
        "Adductor Squeeze", "Short-Lever Copenhagen Plank", "Copenhagen Plank",
        "Short-Lever Copenhagen Adduction", "Copenhagen Adduction", "Banded Clamshell",
        "Banded Lateral Walk", "Hip Airplane", "Spanish Squat Hold", "Glute-Ham Raise",
        "Glute-Biased 45-Degree Back Extension", "Reverse Hyperextension", "Cable Hip Abduction",
        "Cable Hip Adduction", "Incline Y Raise", "Cable 90/90 External Rotation",
        "Serratus Cable Punch", "Cervical Isometric Around-the-World", "Passive Hang",
    ],
    "Power and Plyometrics": [
        "Kettlebell Swing", "Push Press", "Squat Jump", "Box Jump", "Standing Jump-and-reach",
        "Standing Long Jump", "Two-foot Ankle Hops", "Side-to-side Ankle Hop",
        "Single-foot Side-to-side Ankle Hop", "Single-leg Lateral Jump", "Front Cone Hop",
        "Lateral Cone Hop", "Diagonal Cone Hop", "Hurdle (barrier) Hop", "Zigzag Drill",
        "Power Skipping", "Alternate Bounding with Single-arm Action", "Chest Pass",
        "Side Throw", "Overhead Throw", "Underhand Throw", "Medicine Ball Slam",
    ],
    "Movement Preparation": [
        "90/90 Hip Switch", "Adductor Rockback", "Arm Circles", "Band External Rotation",
        "Calf Wall Stretch", "Cat-Cow", "Child's Pose Lat Stretch", "Couch Stretch",
        "Crossover Arm Stretch", "Deep Squat Pry", "Doorway Pec Stretch",
        "Dynamic Hamstring Floor Stretch", "Figure-4 Stretch", "Frog Rockback",
        "Front-Back Leg Swing", "Half-Kneeling Hip Flexor Stretch", "Inchworm Walkout",
        "Knee-To-Wall Ankle Rocks", "Lateral Leg Swing", "Open Book Thoracic Rotation",
        "Scapular Push-Up", "Short Foot", "Soleus Wall Stretch", "Standing Quadriceps Stretch",
        "Supine Hamstring Stretch", "Supported Single-Leg Balance", "Thread The Needle",
        "Wall Angel", "Wall Slide", "World's Greatest Stretch", "Wrist Rocks",
    ],
    "Conditioning Movements": [
        "Sled Push", "Backward Sled Drag", "Forward Sled Drag", "Bear Crawl",
        "Lateral Bear Crawl", "Crab Walk",
    ],
})


GAPS = [
    ["Acceleration mechanics", "Exercise/drill library", "Missing", "High", "Wall drills, falling starts, split-stance starts and resisted accelerations", "Field", "S&C + sprint coach", "Create original progressions and dosage rules"],
    ["Maximum-velocity mechanics", "Exercise/drill library", "Missing", "High", "A-skip/B-skip variants, dribble runs, wicket runs and flying runs", "Field", "Sprint coach", "Separate technique drills from full-speed exposures"],
    ["Deceleration", "Exercise/drill library", "Missing", "High", "Snap-down, run-to-stop, lateral stop and multi-step braking progressions", "Field/Gym", "S&C + physio", "Include landing/braking quality gates"],
    ["Planned change of direction", "Exercise/drill library", "Partial", "High", "45°, 90° and 180° cutting progressions with entry-speed control", "Field", "S&C coach", "Existing box drills are not a complete COD curriculum"],
    ["Reactive agility", "Exercise/drill library", "Missing", "High", "Mirror, visual-call and partner-reaction drills", "Field", "S&C coach", "Must define stimulus, space and athlete-to-coach ratio"],
    ["Aerobic conditioning", "Protocol/template", "Missing", "High", "Continuous, tempo, extensive interval and low-impact cross-training protocols", "Home/Gym/Field", "S&C coach", "Store work:rest and progression outside exercise records"],
    ["Anaerobic conditioning", "Protocol/template", "Missing", "High", "Short hard intervals, hill efforts and modality-based intervals", "Gym/Field", "S&C coach", "Require intensity and recovery constraints"],
    ["Repeated-sprint ability", "Protocol/template", "Missing", "High", "Repeated straight and shuttle sprint sessions", "Field", "S&C + sprint coach", "Include fatigue cutoff and minimum recovery"],
    ["Team circuit templates", "Protocol/template", "Missing", "Medium", "Station layouts, rotations, capacity and equipment-sharing rules", "Gym/Field", "Team S&C coach", "Do not model a whole circuit as one exercise"],
    ["Cooldown and recovery", "Exercise + protocol", "Partial", "Medium", "Walking cooldowns, breathing and recovery sequencing", "Home/Gym/Field", "S&C + physio", "Keep medical claims out of generic recovery copy"],
    ["Original instructions", "Content", "Missing", "Critical", "Rewrite every retained movement as original Runlete content", "All", "S&C reviewer", "Existing prose remains internal research only"],
    ["Owned exercise media", "Media", "Partial", "Critical", "Create or verify technically correct owned demonstrations", "All", "Coach + content team", "No external media without explicit product license"],
]


WHY = {
    "Lower Body Strength": "Foundational force, unilateral control and lower-body tissue capacity.",
    "Upper Body Strength": "Essential pushing, pulling and shoulder-capacity options across equipment levels.",
    "Trunk and Carries": "Bracing, force transfer, anti-rotation and loaded locomotion.",
    "Athletic Accessories": "Targeted joint, tendon and supporting-muscle capacity for athletes.",
    "Power and Plyometrics": "Explosive intent, landing, jumping, elastic and throwing qualities.",
    "Movement Preparation": "Warm-up, mobility, activation and recovery building blocks.",
    "Conditioning Movements": "Scalable loaded or bodyweight conditioning movements; protocols remain separate.",
}


def _list(value: Any) -> List[str]:
    if value in (None, "", [], {}):
        return []
    values = value if isinstance(value, list) else [value]
    return [str(item).strip() for item in values if not isinstance(item, dict) and str(item).strip()]


def _join(value: Any, limit: int = 5) -> str:
    return "; ".join(_list(value)[:limit])


def _display_terms(value: Any, limit: int = 5) -> str:
    """Convert stored taxonomy tokens into reviewer-friendly labels."""
    labels: List[str] = []
    for item in _list(value)[:limit]:
        label = item.replace("_", " ").strip().title()
        for source, replacement in (("Trx", "TRX"), ("Ghd", "GHD"), ("Rom", "ROM")):
            label = label.replace(source, replacement)
        labels.append(label)
    return "; ".join(labels)


def _resolve_references(value: Any, name_by_source_id: Mapping[str, str], limit: int = 5) -> str:
    """Render relationship references as exercise names when the audit knows them."""
    resolved: List[str] = []
    seen = set()
    for item in _list(value):
        display = name_by_source_id.get(item, item)
        if display == item and re.match(r"^(?:cal_ex_|gym_raw_|ex_)", item):
            display = re.sub(r"^(?:cal_ex_|gym_raw_|ex_)", "", item).replace("_", " ").title()
        key = display.casefold()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(display)
        if len(resolved) == limit:
            break
    return "; ".join(resolved)


def _short_notes(value: Any, limit: int = 3, max_chars: int = 420) -> str:
    text = "; ".join(_list(value)[:limit])
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def _find_doc(db: Any, source_id: str) -> Mapping[str, Any]:
    for collection in ("exercise_library", "mobility_drills", "primary_exercise_library", "exercise_variation_library"):
        doc = db[collection].find_one({"id": source_id}, {"embedding": 0})
        if doc:
            return doc
    return {}


def build_rows() -> Dict[str, Any]:
    audit = json.loads(AUDIT_PATH.read_text())
    by_name = {row["name"].lower(): row for row in audit["records"]}
    name_by_source_id = {row["source_id"]: row["name"] for row in audit["records"]}
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
    db = client.test_database
    client.admin.command("ping")
    for collection in ("exercise_library", "mobility_drills", "primary_exercise_library", "exercise_variation_library"):
        for source in db[collection].find({}, {"id": 1, "name": 1, "exercise_name": 1}):
            source_id = str(source.get("id") or "").strip()
            source_name = str(source.get("name") or source.get("exercise_name") or "").strip()
            if source_id and source_name:
                name_by_source_id.setdefault(source_id, source_name)
    rows: List[List[Any]] = []
    missing_names: List[str] = []
    seen = set()
    try:
        for group, names in GROUPS.items():
            for name in names:
                audit_row = by_name.get(name.lower())
                if not audit_row:
                    missing_names.append(name)
                    continue
                key = audit_row["audit_key"]
                if key in seen:
                    continue
                seen.add(key)
                doc = _find_doc(db, audit_row["source_id"])
                environments = ", ".join(k.title() for k, value in audit_row["environments"].items() if value)
                disposition = audit_row["disposition"]
                role = "Advanced / specialist review" if disposition == "specialist" else (
                    "Retain; instructions need rewrite" if disposition == "rewrite_required" else disposition.title()
                )
                technical = audit_row.get("technical_complexity") or (
                    "high" if audit_row["risk"]["risk_level"] == "high" else
                    "moderate" if audit_row["risk"]["risk_level"] == "moderate" else "low"
                )
                impact = str(doc.get("impact_level") or ("high" if any(x in name.lower() for x in ("jump", "hop", "bound")) else "low"))
                media = audit_row.get("media") or {}
                rows.append([
                    f"REV-{len(rows)+1:03d}", name, group, role, _display_terms(audit_row.get("patterns"), 7),
                    _display_terms(audit_row.get("qualities"), 7), _display_terms(audit_row.get("primary_muscles"), 6),
                    _display_terms(audit_row.get("secondary_muscles"), 6), _display_terms(audit_row.get("equipment"), 7),
                    environments, str(audit_row.get("difficulty") or "Needs classification").title(), technical.title(), impact.title(),
                    audit_row["risk"]["supervision"].title(), audit_row["team"]["team_scalability"].title(),
                    _short_notes(doc.get("coaching_cues") or doc.get("instructions")),
                    _short_notes(doc.get("common_errors") or doc.get("common_mistakes")),
                    _short_notes(doc.get("avoid_when") or doc.get("contraindications") or doc.get("injury_flags")),
                    _resolve_references(audit_row.get("progressions"), name_by_source_id, 5),
                    _resolve_references(audit_row.get("regressions"), name_by_source_id, 5),
                    _resolve_references(audit_row.get("substitutions"), name_by_source_id, 5), WHY[group],
                    "Research notes only — original Runlete copy and expert approval required",
                    "Present; review pending" if media.get("thumbnail_present") else "Missing",
                    "Needs Review", "Required" if audit_row["expert_review"]["physiotherapy"] == "required" else "As Needed",
                    "", audit_row["source_id"],
                ])
    finally:
        client.close()
    headers = [
        "Review ID", "Exercise Name", "Section", "Proposed Role", "Movement Patterns",
        "Training Qualities", "Primary Muscles", "Secondary Muscles", "Equipment",
        "Environments", "Difficulty", "Technical Complexity", "Impact", "Supervision",
        "Team Scalability", "Coaching Cues — Research Notes", "Common Mistakes — Research Notes",
        "Safety / Avoid — Research Notes", "Progressions", "Regressions", "Substitutions",
        "Why Included", "Content Status", "Media Status", "S&C Review Decision",
        "Physio Review", "Reviewer Notes", "Source Record ID",
    ]
    return {
        "headers": headers,
        "rows": rows,
        "gaps_headers": ["Capability", "Record Type", "Current State", "Priority", "Needed Content", "Environment", "Required Reviewer", "Implementation Note"],
        "gaps": GAPS,
        "missing_requested_names": missing_names,
        "counts": {
            "curated": len(rows),
            "source_candidates": audit["summary"]["movement_candidate_count"],
            "exact_duplicate_records": len(audit["reconciliation"]["duplicate_records"]),
            "probable_equivalence_groups": audit["reconciliation"]["possible_equivalent_group_count"],
            "rejected_non_movements": audit["summary"]["dispositions"]["reject"],
            "original_audit_production_ready": audit["summary"]["production_ready_count"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    data = build_rows()
    if args.offset or args.limit is not None:
        end = None if args.limit is None else args.offset + args.limit
        data["rows"] = data["rows"][args.offset:end]
        data["offset"] = args.offset
    print(json.dumps(data, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()

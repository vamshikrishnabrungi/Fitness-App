#!/usr/bin/env python3
"""Idempotent, batch-scoped fixes for the exercise-data issues confirmed by the audit.

Only applies changes that were triaged as unambiguous true-positives. Logs every before->after so
changes are auditable/reversible. Deliberately does NOT touch: Olympic/combo-lift muscle sets (audit
false positives), cross-collection duplicate ids (intentional), missing movement-pattern tags, or
'full_body' on Olympic accessories — those are left for coach review. Run:

    python -m backend.fix_exercise_data            # apply
    python -m backend.fix_exercise_data --dry-run  # preview only
"""
from __future__ import annotations

import os
import re
import sys

from pymongo import MongoClient

COLLECTIONS = ["primary_exercise_library", "exercise_variation_library", "exercise_library", "mobility_drills"]

# Unambiguous single-pattern movements — safe to set the correct primary muscles on every record.
MUSCLE_CORRECTIONS = {
    "good morning": ["hamstrings", "glutes", "erector_spinae"],
    "seated good morning": ["hamstrings", "glutes", "erector_spinae"],
    "single-leg squat": ["quadriceps", "glutes", "adductors"],
    "lunge squat with toss": ["quadriceps", "glutes", "trunk"],
    "plyometric push-up": ["chest", "triceps", "shoulders"],
    "incline push-up depth jump": ["chest", "shoulders", "triceps"],
}
# Conditional fixes: only correct records whose current muscles contain a wrong token.
CONDITIONAL = {
    "pull-up": {"wrong_if_contains": {"glutes", "hamstrings", "quadriceps", "calves"},
                "corrected": ["lats", "upper_back", "biceps"]},
}
EQUIP_WORDS = {"barbell": "barbell", "dumbbell": "dumbbells", "kettlebell": "kettlebell",
               "cable": "cable", "landmine": "landmine", "band": "band"}

# Unambiguous movement-pattern tags for exercises that currently have none. (Upper Back
# Extensions intentionally omitted — thoracic vs hip extension is ambiguous → coach review.)
PATTERN_CORRECTIONS = {
    "good morning": ["hinge"],
    "seated good morning": ["hinge"],
    "clean shrug": ["olympic_lift", "pull"],
    "clean rack support": ["olympic_lift"],
}


def _db():
    url, name = "mongodb://localhost:27017", "test_database"
    env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env):
        for line in open(env, errors="ignore"):
            line = line.strip()
            if line.startswith("MONGO_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("DB_NAME="):
                name = line.split("=", 1)[1].strip().strip('"').strip("'")
    return MongoClient(url)[name]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def batch_b_muscles(db, dry) -> int:
    print("BATCH B — muscle corrections")
    # Normalize keys so hyphens/case in exercise names match (e.g. "Pull-up" -> "pull up").
    corrections = {_norm(k): v for k, v in MUSCLE_CORRECTIONS.items()}
    conditional = {_norm(k): v for k, v in CONDITIONAL.items()}
    changed = 0
    for col in COLLECTIONS:
        for d in db[col].find({"primary_muscles": {"$exists": True}}, {"name": 1, "primary_muscles": 1}):
            key = _norm(d.get("name"))
            cur = [str(m).lower() for m in (d.get("primary_muscles") or [])]
            new = None
            if key in corrections and cur != corrections[key]:
                new = corrections[key]
            elif key in conditional and set(cur) & conditional[key]["wrong_if_contains"]:
                new = conditional[key]["corrected"]
            if new:
                print(f"  {col}: {d.get('name')}: {cur} -> {new}")
                if not dry:
                    db[col].update_one({"_id": d["_id"]}, {"$set": {"primary_muscles": new}})
                changed += 1
    print(f"  → {changed} records {'would be ' if dry else ''}updated")
    return changed


def batch_a_non_movement(db, dry) -> int:
    print("BATCH A — flag non-movement principle entries")
    changed = 0
    q = {"category": {"$in": ["mobility_principles", "principle", "knowledge", "concept"]}}
    for d in db.mobility_drills.find(q, {"name": 1, "is_movement": 1}):
        if d.get("is_movement") is False:
            continue
        print(f"  mobility_drills: '{d.get('name')}' -> is_movement=False (excluded from drill selection)")
        if not dry:
            db.mobility_drills.update_one({"_id": d["_id"]}, {"$set": {"is_movement": False}})
        changed += 1
    print(f"  → {changed} entries {'would be ' if dry else ''}flagged")
    return changed


def batch_c_equipment(db, dry) -> int:
    print("BATCH C — fill name-implied missing equipment")
    changed = 0
    for col in ["primary_exercise_library", "exercise_variation_library"]:
        for d in db[col].find({}, {"name": 1, "equipment": 1, "equipment_required": 1}):
            name = str(d.get("name") or "").lower()
            eq = [str(x).lower() for x in (d.get("equipment") or d.get("equipment_required") or [])]
            if "bodyweight" in eq:
                continue
            for word, tag in EQUIP_WORDS.items():
                if word in name and not any(tag in e or e in tag for e in eq):
                    new_eq = eq + [tag]
                    print(f"  {col}: {d.get('name')}: equipment {eq} -> {new_eq}")
                    if not dry:
                        db[col].update_one({"_id": d["_id"]}, {"$set": {"equipment": new_eq}})
                    changed += 1
                    break
    print(f"  → {changed} records {'would be ' if dry else ''}updated")
    return changed


def batch_d_patterns(db, dry) -> int:
    print("BATCH D — add missing movement-pattern tags (unambiguous only)")
    corr = {_norm(k): v for k, v in PATTERN_CORRECTIONS.items()}
    changed = 0
    for col in COLLECTIONS:
        field = "movement_patterns" if col == "exercise_library" else "patterns"
        for d in db[col].find({}, {"name": 1, "patterns": 1, "movement_patterns": 1}):
            key = _norm(d.get("name"))
            if key in corr and not (d.get("patterns") or d.get("movement_patterns")):
                print(f"  {col}: {d.get('name')}: {field}={corr[key]}")
                if not dry:
                    db[col].update_one({"_id": d["_id"]}, {"$set": {field: corr[key]}})
                changed += 1
    print(f"  → {changed} records {'would be ' if dry else ''}updated")
    return changed


def main(dry: bool) -> None:
    db = _db()
    total = (batch_b_muscles(db, dry) + batch_a_non_movement(db, dry)
             + batch_c_equipment(db, dry) + batch_d_patterns(db, dry))
    print(f"\n{'DRY-RUN: ' if dry else ''}total records touched: {total}")


if __name__ == "__main__":
    main("--dry-run" in sys.argv)

#!/usr/bin/env python3
"""Produce the conservative Excel decisions for the exercise technical pre-review.

This is not a clinical authorization and does not mutate MongoDB.  It approves
only movement selection and structured metadata under the workbook's Review
Guide definition.  App-facing instructions, media, dosage, injury use, and
physiotherapy sign-off remain pending.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, List

from build_exercise_review_data import build_rows


# Explicitly selected only after reviewing every catalogue row.  Each row must
# also pass the mechanical safeguards in build_prereview() below.
APPROVED_REVIEW_IDS = {
    "REV-002",  # Goblet Squat
    "REV-007",  # Belt Squat
    "REV-009",  # Leg Press
    "REV-012",  # Dumbbell Split Squat
    "REV-023",  # Dumbbell Romanian Deadlift
    "REV-027",  # Dumbbell Hip Thrust
    "REV-041",  # Dumbbell Floor Press
    "REV-045",  # Neutral-Grip Dumbbell Bench Press
    "REV-059",  # One-Arm Dumbbell Row
    "REV-061",  # Chest-Supported Dumbbell Row
    "REV-062",  # Seated Cable Row
    "REV-069",  # Band External Rotation at Side
    "REV-070",  # Side-Lying Dumbbell External Rotation
    "REV-071",  # Prone Y-T-W Raise
    "REV-075",  # Bear Plank Hold
    "REV-076",  # Front Plank
    "REV-077",  # Side Plank from Knees
    "REV-078",  # Side Plank
    "REV-079",  # Long-Lever Plank
    "REV-080",  # Plank Shoulder Tap
    "REV-083",  # Stability Ball Rollout
    "REV-084",  # Pallof Press
    "REV-085",  # Pallof Press Iso Hold
    "REV-086",  # Half-Kneeling Pallof Press
    "REV-089",  # Cable Lift
    "REV-090",  # Half-Kneeling Cable Lift
    "REV-092",  # Farmer's Carry
    "REV-093",  # Suitcase Carry
    "REV-094",  # Single-Arm Front Rack Carry
    "REV-099",  # Short-Lever Copenhagen Plank
    "REV-101",  # Short-Lever Copenhagen Adduction
    "REV-103",  # Banded Clamshell
    "REV-104",  # Banded Lateral Walk
    "REV-106",  # Spanish Squat Hold
    "REV-171",  # Backward Sled Drag
    "REV-172",  # Forward Sled Drag
    "REV-173",  # Bear Crawl
    "REV-174",  # Lateral Bear Crawl
}


REVIEW_NOTE = (
    "AI technical pre-review: movement and metadata suitable for healthy athletes "
    "16+ in general S&C. Instructions and media remain unapproved. Not a clinical "
    "sign-off; human review is still required before release."
)


def _tokens(value: str) -> set[str]:
    return {item.strip().casefold() for item in value.split(";") if item.strip()}


def _hold_reason(row: List[Any]) -> str:
    if row[3] == "Advanced / specialist review":
        return "specialist review required"
    if row[3] == "Retain; instructions need rewrite":
        return "record already flagged for rewrite"
    if row[10] == "Advanced" or row[11] == "High" or row[12] == "High" or row[13] == "Required":
        return "advanced, high-impact, high-complexity, or required-supervision review"
    if not all(str(row[index]).strip() for index in (4, 5, 6, 8, 15, 16, 17, 18, 19, 20)):
        return "required metadata or relationship is incomplete"
    if _tokens(row[6]) & _tokens(row[7]):
        return "primary and secondary muscle metadata overlap"
    if row[11] != "Low" or row[12] != "Low" or row[13] != "Normal":
        return "moderate technical or supervision judgement remains"
    return "movement-specific metadata requires human confirmation"


def build_prereview() -> Dict[str, Any]:
    catalogue = build_rows()
    rows = catalogue["rows"]
    by_id = {row[0]: row for row in rows}
    missing = sorted(APPROVED_REVIEW_IDS - by_id.keys())
    if missing:
        raise RuntimeError(f"Approved review IDs missing from catalogue: {missing}")

    updates = []
    held = []
    for excel_row, row in enumerate(rows, start=5):
        review_id = row[0]
        if review_id in APPROVED_REVIEW_IDS:
            failures = []
            if row[3] not in {"Core", "Contextual"}:
                failures.append("role")
            if row[10] not in {"Beginner", "Intermediate"}:
                failures.append("difficulty")
            if (row[11], row[12], row[13]) != ("Low", "Low", "Normal"):
                failures.append("risk classification")
            if not all(str(row[index]).strip() for index in (4, 5, 6, 8, 15, 16, 17, 18, 19, 20)):
                failures.append("completeness")
            if _tokens(row[6]) & _tokens(row[7]):
                failures.append("muscle overlap")
            if failures:
                raise RuntimeError(f"{review_id} {row[1]} failed safeguards: {failures}")
            updates.append({
                "excel_row": excel_row,
                "review_id": review_id,
                "exercise_name": row[1],
                "decision": "Approved",
                "physio_review": row[25],
                "reviewer_note": REVIEW_NOTE,
            })
        else:
            held.append({
                "review_id": review_id,
                "exercise_name": row[1],
                "reason": _hold_reason(row),
            })

    reasons = Counter(item["reason"] for item in held)
    return {
        "reviewed": len(rows),
        "approved": len(updates),
        "held": len(held),
        "updates": updates,
        "held_reason_counts": dict(sorted(reasons.items())),
        "clinical_signoff_changed": False,
    }


if __name__ == "__main__":
    print(json.dumps(build_prereview(), ensure_ascii=False, separators=(",", ":")))

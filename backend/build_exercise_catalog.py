from __future__ import annotations

import argparse
import asyncio
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PRIMARY_EXERCISE_NAMES = {
    "back squat",
    "front squat",
    "pause squat",
    "pulling-stance back squat",
    "romanian deadlift",
    "stiff-legged deadlift",
    "straight-legged deadlift",
    "good morning",
    "seated good morning",
    "bulgarian split squat",
    "split squat",
    "lunge",
    "press",
    "push press",
    "bent row",
    "pull-up",
    "chin-up",
    "upper back extensions",
}

SPECIALIST_MARKERS = {
    "block",
    "hang",
    "segment",
    "halting",
    "floating",
    "tall",
    "dip",
    "riser",
    "rack support",
    "jerk balance",
    "snatch balance",
    "behind the neck",
    " in split",
    "from power position",
    "no brush",
    "no jump",
    "pull-down",
    "transition",
    "stage",
    "barkski",
    "everett",
    "bench pull",
    "support",
    "recovery",
}

ADVANCED_FAMILIES = {"snatch", "clean", "jerk"}
LOWER_COMPLEXITY_FAMILIES = {"squat", "deadlift", "hinge", "row", "lunge", "press", "general_strength"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _clean_list(value: Any, *, limit: int = 6) -> List[Any]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    cleaned: List[Any] = []
    for item in items:
        if item in (None, "", [], {}):
            continue
        if isinstance(item, str):
            text = item.strip()
            if not text or text.startswith("..."):
                continue
            text = re.sub(r"^(Notes?|Purpose):\\s*", "", text).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        elif item not in cleaned:
            cleaned.append(item)
        if len(cleaned) >= limit:
            break
    return cleaned


def _safe_refs(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    refs = []
    for ref in (doc.get("source_refs") or [])[:2]:
        if not isinstance(ref, dict):
            continue
        refs.append({
            "source_book_id": ref.get("source_book_id"),
            "section_id": ref.get("section_id"),
            "section_title": ref.get("section_title"),
            "heading": ref.get("heading"),
        })
    return refs


def _base_exercise(doc: Dict[str, Any]) -> str:
    name = str(doc.get("name") or "")
    family = str(doc.get("exercise_family") or "").strip()
    lowered = name.lower()
    if family in {"snatch", "clean", "jerk"}:
        return family.title()
    if "squat" in lowered:
        return "Squat"
    if "deadlift" in lowered or "good morning" in lowered:
        return "Hinge"
    if "pull-up" in lowered or "chin-up" in lowered or "row" in lowered:
        return "Pull"
    if "press" in lowered:
        return "Press"
    if "lunge" in lowered or "split squat" in lowered:
        return "Single-Leg Squat"
    return family.title() if family else name


def _is_specialist_variation(doc: Dict[str, Any]) -> bool:
    name = str(doc.get("name") or "").lower()
    family = str(doc.get("exercise_family") or "").lower()
    if name in PRIMARY_EXERCISE_NAMES:
        return False
    if any(token in name for token in ["snatch", "clean", "jerk", "overhead"]):
        return True
    if any(marker in name for marker in SPECIALIST_MARKERS):
        return True
    if family in ADVANCED_FAMILIES:
        return True
    return False


def _technical_complexity(doc: Dict[str, Any], is_variation: bool) -> str:
    family = str(doc.get("exercise_family") or "").lower()
    name = str(doc.get("name") or "").lower()
    if is_variation or family in ADVANCED_FAMILIES:
        return "high"
    if "overhead" in name or family in {"squat", "deadlift"}:
        return "medium"
    return "low"


def _mobility_requirement(doc: Dict[str, Any]) -> str:
    terms = " ".join([
        str(doc.get("name") or ""),
        " ".join(doc.get("movement_patterns") or []),
        " ".join(doc.get("contraindications") or []),
    ]).lower()
    if any(token in terms for token in ["overhead", "snatch", "rack", "jerk"]):
        return "high"
    if any(token in terms for token in ["squat", "lunge", "split"]):
        return "medium"
    return "low"


def _impact_level(doc: Dict[str, Any]) -> str:
    text = " ".join([
        str(doc.get("name") or ""),
        " ".join(doc.get("movement_patterns") or []),
        " ".join(doc.get("training_qualities") or []),
    ]).lower()
    if any(token in text for token in ["jump", "plyometric", "bound", "hop"]):
        return "high"
    if any(token in text for token in ["power", "olympic_lift", "triple_extension"]):
        return "medium"
    return "none"


def _coaching_requirement(doc: Dict[str, Any], is_variation: bool) -> str:
    family = str(doc.get("exercise_family") or "").lower()
    if is_variation or family in ADVANCED_FAMILIES:
        return "required"
    if family in {"squat", "deadlift", "press"}:
        return "recommended"
    return "none"


def _default_user_level(doc: Dict[str, Any], is_variation: bool) -> str:
    if is_variation:
        return "advanced"
    raw = str(doc.get("difficulty") or "intermediate").lower()
    if raw in {"beginner", "intermediate", "advanced"}:
        return raw
    return "intermediate"


def _variation_type(doc: Dict[str, Any]) -> str:
    name = str(doc.get("name") or "").lower()
    if any(token in name for token in ["block", "hang", "riser", "power position"]):
        return "start_position_variation"
    if any(token in name for token in ["segment", "halting", "floating", "slow"]):
        return "tempo_or_position_control"
    if any(token in name for token in ["pull", "deadlift", "shrug", "lift-off"]):
        return "pull_strength_or_technique"
    if any(token in name for token in ["balance", "tall", "drop", "scarecrow"]):
        return "receiving_or_turnover_drill"
    return "specialist_variation"


def _use_when(doc: Dict[str, Any], is_variation: bool) -> List[str]:
    base = _base_exercise(doc)
    qualities = _clean_list(doc.get("training_qualities"), limit=3)
    if is_variation:
        return [
            "advanced athlete or Olympic lifting context",
            f"{base.lower()} technical development",
            *[f"{quality.replace('_', ' ')} focus" for quality in qualities],
        ][:5]
    return [
        "general strength and conditioning plan",
        f"{base.lower()} pattern development",
        *[f"{quality.replace('_', ' ')} focus" for quality in qualities],
    ][:5]


def _avoid_when(doc: Dict[str, Any], is_variation: bool) -> List[str]:
    avoid = [str(item).replace("_", " ") for item in _clean_list(doc.get("contraindications") or doc.get("injury_flags"), limit=5)]
    if is_variation:
        avoid.extend(["beginner without coaching", "missing required equipment"])
    return list(dict.fromkeys(avoid))[:7]


def _catalog_record(doc: Dict[str, Any], *, is_variation: bool, now: datetime) -> Dict[str, Any]:
    name = str(doc.get("name") or "").strip()
    base = _base_exercise(doc)
    source_id = doc.get("id")
    equipment = _clean_list(doc.get("equipment_required") or doc.get("equipment"), limit=8)
    patterns = _clean_list(doc.get("movement_patterns"), limit=8)
    qualities = _clean_list(doc.get("training_qualities"), limit=8)
    record = {
        "id": f"{'var' if is_variation else 'pex'}_{_slug(name)}",
        "source_exercise_id": source_id,
        "name": name,
        "aliases": _clean_list(doc.get("aliases"), limit=5),
        "base_exercise": base,
        "tier": "specialist_variation" if is_variation else "primary",
        "category": doc.get("category") or doc.get("exercise_type"),
        "difficulty": doc.get("difficulty"),
        "default_user_level": _default_user_level(doc, is_variation),
        "technical_complexity": _technical_complexity(doc, is_variation),
        "mobility_requirement": _mobility_requirement(doc),
        "stability_requirement": "high" if "overhead" in " ".join(patterns).lower() else "medium",
        "impact_level": _impact_level(doc),
        "load_scalability": "high" if "barbell" in equipment or "dumbbells" in equipment else "medium",
        "coaching_requirement": _coaching_requirement(doc, is_variation),
        "beginner_usable_as_drill": bool(is_variation and doc.get("exercise_family") in ADVANCED_FAMILIES),
        "equipment": equipment,
        "patterns": patterns,
        "qualities": qualities,
        "primary_muscles": _clean_list(doc.get("primary_muscles"), limit=8),
        "secondary_muscles": _clean_list(doc.get("secondary_muscles"), limit=8),
        "summary": doc.get("summary") or doc.get("definition"),
        "coaching_cues": _clean_list(doc.get("coaching_cues"), limit=5),
        "common_errors": _clean_list(doc.get("common_errors") or doc.get("common_mistakes"), limit=5),
        "use_when": _use_when(doc, is_variation),
        "avoid_when": _avoid_when(doc, is_variation),
        "progressions": _clean_list(doc.get("progressions"), limit=6),
        "regressions": _clean_list(doc.get("regressions"), limit=6),
        "source_refs": _safe_refs(doc),
        "expert_validation_status": doc.get("expert_validation_status", "pending"),
        "created_at": now,
        "updated_at": now,
    }
    if is_variation:
        record["variation_type"] = _variation_type(doc)
    return record


def _progression_edges(records: Iterable[Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
    by_name = {str(record.get("name") or "").lower(): record for record in records}
    edges: List[Dict[str, Any]] = []

    def add_edge(source: Dict[str, Any], target: Dict[str, Any], direction: str = "progression") -> None:
        if source["id"] == target["id"]:
            return
        key = (source["id"], target["id"], direction)
        if any((edge["from_exercise_id"], edge["to_exercise_id"], edge["direction"]) == key for edge in edges):
            return
        edges.append({
            "id": f"edge_{uuid.uuid4()}",
            "base_exercise": target.get("base_exercise") or source.get("base_exercise"),
            "from_exercise_id": source["id"],
            "from_exercise_name": source["name"],
            "to_exercise_id": target["id"],
            "to_exercise_name": target["name"],
            "direction": direction,
            "min_user_level": target.get("default_user_level") or "intermediate",
            "created_at": now,
            "updated_at": now,
        })

    for record in records:
        for direction, field in [("progression", "progressions"), ("regression", "regressions")]:
            for target_name in record.get(field) or []:
                target = by_name.get(str(target_name).lower())
                if not target:
                    continue
                add_edge(record, target, direction)

    canonical_chains = [
        ["Press", "Push Press", "Power Jerk", "Jerk Balance", "Jerk Behind the Neck", "Clean-Jerk"],
        ["Muscle Snatch", "Tall Snatch", "Hang Power Snatch", "Power Snatch", "Block Power Snatch", "Block Snatch", "Snatch"],
        ["Muscle Clean", "Tall Clean", "Hang Power Clean", "Power Clean", "Block Power Clean", "Block Clean", "Clean"],
        ["Romanian Deadlift", "Clean Deadlift", "Clean Pull", "Power Clean"],
        ["Romanian Deadlift", "Snatch Deadlift", "Snatch Pull", "Power Snatch"],
        ["Back Squat", "Pause Squat", "Front Squat", "Overhead Squat"],
        ["Split Squat", "Bulgarian Split Squat", "Overhead Split Squat"],
    ]
    for chain in canonical_chains:
        available = [by_name[name.lower()] for name in chain if name.lower() in by_name]
        for source, target in zip(available, available[1:]):
            add_edge(source, target, "progression")
            add_edge(target, source, "regression")
    return edges


async def build_catalog(*, dry_run: bool = False) -> Dict[str, int]:
    load_dotenv(Path("backend/.env"))
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "sftc_database")]
    await ensure_database_schema(db)

    raw_docs = await db.exercise_library.find({}).sort("name", 1).to_list(10000)
    now = datetime.utcnow()
    primary: List[Dict[str, Any]] = []
    variations: List[Dict[str, Any]] = []
    for doc in raw_docs:
        name = str(doc.get("name") or "").strip()
        if not name:
            continue
        is_variation = _is_specialist_variation(doc)
        record = _catalog_record(doc, is_variation=is_variation, now=now)
        if is_variation:
            variations.append(record)
        else:
            primary.append(record)

    all_catalog_records = [*primary, *variations]
    edges = _progression_edges(all_catalog_records, now)

    if not dry_run:
        await db.primary_exercise_library.delete_many({})
        await db.exercise_variation_library.delete_many({})
        await db.exercise_progression_graph.delete_many({})
        if primary:
            await db.primary_exercise_library.insert_many(primary)
        if variations:
            await db.exercise_variation_library.insert_many(variations)
        if edges:
            await db.exercise_progression_graph.insert_many(edges)

    client.close()
    return {
        "raw_exercises": len(raw_docs),
        "primary_exercises": len(primary),
        "variation_exercises": len(variations),
        "progression_edges": len(edges),
        "dry_run": int(dry_run),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compact app-facing exercise catalogs from raw exercise knowledge.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(build_catalog(dry_run=args.dry_run))
    print(result)


if __name__ == "__main__":
    main()

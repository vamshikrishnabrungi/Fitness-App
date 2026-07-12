from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema
from backend.merge_exercise_research_drafts import OUTPUT_PATH as MERGED_DRAFT_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK_ID = "general_gym_exercise_research_v1"
INGESTION_METHOD = "parallel_web_research_normalized_general_gym_v1"


LIST_FIELDS = {
    "aliases",
    "equipment",
    "equipment_required",
    "patterns",
    "movement_patterns",
    "qualities",
    "training_qualities",
    "primary_muscles",
    "secondary_muscles",
    "coaching_cues",
    "common_errors",
    "use_when",
    "avoid_when",
    "contraindications",
    "injury_flags",
    "progressions",
    "regressions",
    "substitutions",
    "source_refs",
    "source_book_ids",
    "draft_source_files",
    "sport_tags",
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _dedupe_list(items: Iterable[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for item in items:
        if item in (None, "", [], {}):
            continue
        if isinstance(item, dict):
            key = json.dumps(item, sort_keys=True)
        else:
            key = str(item).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _merge_list(existing: Any, incoming: Any) -> List[Any]:
    existing_items = existing if isinstance(existing, list) else [existing]
    incoming_items = incoming if isinstance(incoming, list) else [incoming]
    return _dedupe_list([*existing_items, *incoming_items])


def _source_ref(source_ref: Dict[str, Any], exercise_name: str) -> Dict[str, Any]:
    title = str(source_ref.get("title") or "General Gym Exercise Research").strip()
    url = str(source_ref.get("url") or "").strip()
    source_type = str(source_ref.get("source_type") or "exercise_reference").strip()
    source_slug = _slug(f"{title}_{url}")[:96] or "source"
    return {
        "source_book_id": SOURCE_PACK_ID,
        "source_id": f"gym_src_{source_slug}",
        "section_id": f"gym_src_{source_slug}",
        "section_title": title,
        "heading": exercise_name,
        "url": url,
        "source_type": source_type,
    }


def _source_refs(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    refs = []
    for ref in record.get("source_refs") or []:
        if isinstance(ref, dict) and ref.get("title") and ref.get("url"):
            refs.append(_source_ref(ref, str(record.get("name") or "")))
    return refs


def _records(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise ValueError("Merged general gym exercise file must be a JSON list")


def _primary_docs(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    for record in records:
        refs = _source_refs(record)
        qualities = record.get("qualities") or []
        patterns = record.get("patterns") or []
        docs.append({
            **record,
            "source_book_id": SOURCE_PACK_ID,
            "source_book_ids": [SOURCE_PACK_ID],
            "source_refs": refs,
            "sport_tags": _dedupe_list([
                "general_gym",
                "strength_and_conditioning",
                *(record.get("patterns") or []),
                *(record.get("qualities") or []),
                *(record.get("primary_muscles") or []),
            ]),
            "expert_validation_status": "pending",
            "ingestion_method": INGESTION_METHOD,
            "version": "v1.0.0",
            "created_at": now,
            "updated_at": now,
            "sample_prescription": _sample_prescription(record),
            "retrieval_notes": {
                "app_facing_default_pool": True,
                "general_gym_record": True,
                "tier": record.get("tier"),
                "category": record.get("category"),
                "patterns": patterns,
                "qualities": qualities,
            },
        })
    return docs


def _raw_docs(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    for record in records:
        refs = _source_refs(record)
        docs.append({
            "id": f"gym_raw_{_slug(record['name'])}",
            "name": record["name"],
            "aliases": record.get("aliases") or [],
            "definition": record.get("summary"),
            "exercise_family": record.get("base_exercise"),
            "exercise_type": record.get("category"),
            "category": record.get("category"),
            "difficulty": record.get("difficulty"),
            "equipment_required": record.get("equipment") or [],
            "movement_patterns": record.get("patterns") or [],
            "training_qualities": record.get("qualities") or [],
            "primary_muscles": record.get("primary_muscles") or [],
            "secondary_muscles": record.get("secondary_muscles") or [],
            "coaching_cues": record.get("coaching_cues") or [],
            "common_errors": record.get("common_errors") or [],
            "contraindications": record.get("avoid_when") or [],
            "injury_flags": record.get("avoid_when") or [],
            "progressions": record.get("progressions") or [],
            "regressions": record.get("regressions") or [],
            "substitutions": record.get("substitutions") or [],
            "sport_tags": _dedupe_list([
                "general_gym",
                "strength_and_conditioning",
                *(record.get("patterns") or []),
                *(record.get("qualities") or []),
                *(record.get("primary_muscles") or []),
            ]),
            "summary": record.get("summary"),
            "source_book_id": SOURCE_PACK_ID,
            "source_book_ids": [SOURCE_PACK_ID],
            "source_refs": refs,
            "source_text_hash": hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
            "expert_validation_status": "pending",
            "ingestion_method": INGESTION_METHOD,
            "version": "v1.0.0",
            "created_at": now,
            "updated_at": now,
        })
    return docs


def _sample_prescription(record: Dict[str, Any]) -> Dict[str, str]:
    category = str(record.get("category") or "")
    tier = str(record.get("tier") or "")
    if category == "power":
        return {"sets": "3-5", "reps": "2-5", "intensity": "explosive, high-quality reps", "rest": "90-180 sec"}
    if category == "conditioning":
        return {"sets": "3-6", "duration": "10-40 m or 15-45 sec", "intensity": "smooth repeatable effort", "rest": "45-120 sec"}
    if tier in {"accessory", "machine"} or category == "hypertrophy":
        return {"sets": "2-4", "reps": "8-15", "intensity": "RPE 6-8", "rest": "45-90 sec"}
    if tier == "regression":
        return {"sets": "2-3", "reps": "6-12", "intensity": "easy-moderate, technique first", "rest": "45-90 sec"}
    return {"sets": "3-5", "reps": "3-8", "intensity": "RPE 6-8", "rest": "90-180 sec"}


def _source_section_docs(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs_by_id: Dict[str, Dict[str, Any]] = {}
    order = 10000
    for record in records:
        for ref in _source_refs(record):
            source_id = ref["section_id"]
            if source_id not in docs_by_id:
                order += 1
                docs_by_id[source_id] = {
                    "id": source_id,
                    "source_book_id": SOURCE_PACK_ID,
                    "section_order": order,
                    "section_title": ref["section_title"],
                    "domain": "general_gym_exercise_library",
                    "topics": ["general_gym", "strength_and_conditioning", ref.get("source_type")],
                    "summary": f"Source used for general gym exercise record normalization: {ref['section_title']}.",
                    "url": ref.get("url"),
                    "source_type": ref.get("source_type"),
                    "created_at": now,
                    "updated_at": now,
                }
        order += 1
        docs_by_id[f"gym_section_exercise_{_slug(record['name'])}"] = {
            "id": f"gym_section_exercise_{_slug(record['name'])}",
            "source_book_id": SOURCE_PACK_ID,
            "section_order": order,
            "section_title": record["name"],
            "domain": "general_gym_exercise_library",
            "topics": _dedupe_list(["general_gym", record.get("category"), record.get("tier"), *(record.get("patterns") or []), *(record.get("qualities") or [])]),
            "summary": record.get("summary"),
            "source_text_hash": hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
            "created_at": now,
            "updated_at": now,
        }
    return list(docs_by_id.values())


def _progression_docs(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name = {str(record.get("name") or "").strip().lower(): record for record in records}
    docs: List[Dict[str, Any]] = []
    now = datetime.utcnow()

    def add_edge(from_record: Dict[str, Any], to_record: Dict[str, Any], direction: str) -> None:
        edge_id = f"gym_prog_{_slug(from_record['name'])}_to_{_slug(to_record['name'])}"
        docs.append({
            "id": edge_id,
            "base_exercise": to_record.get("base_exercise") or from_record.get("base_exercise"),
            "from_exercise_id": from_record["id"],
            "from_exercise_name": from_record["name"],
            "to_exercise_id": to_record["id"],
            "to_exercise_name": to_record["name"],
            "direction": direction,
            "min_user_level": to_record.get("difficulty") or "beginner",
            "source_book_id": SOURCE_PACK_ID,
            "source_book_ids": [SOURCE_PACK_ID],
            "source_refs": to_record.get("source_refs") or [],
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        })

    for record in records:
        for regression_name in record.get("regressions") or []:
            regression = by_name.get(str(regression_name).strip().lower())
            if regression:
                add_edge(regression, record, "progression")
        for progression_name in record.get("progressions") or []:
            progression = by_name.get(str(progression_name).strip().lower())
            if progression:
                add_edge(record, progression, "progression")

    unique_docs: Dict[str, Dict[str, Any]] = {}
    for doc in docs:
        unique_docs[doc["id"]] = doc
    return list(unique_docs.values())


def _merge_doc(existing: Dict[str, Any], incoming: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "_id":
            continue
        if key == "id" and existing.get("id"):
            continue
        if key == "created_at" and existing.get("created_at"):
            continue
        if key in LIST_FIELDS:
            merged[key] = _merge_list(merged.get(key), value)
        elif value not in (None, "", [], {}):
            merged[key] = value
    merged["source_book_ids"] = _merge_list(merged.get("source_book_ids"), SOURCE_PACK_ID)
    merged["updated_at"] = now
    return merged


async def _upsert_many(db: Any, collection_name: str, docs: Iterable[Dict[str, Any]]) -> int:
    now = datetime.utcnow()
    collection = db[collection_name]
    count = 0
    for doc in docs:
        doc = {**doc, "updated_at": now}
        doc.setdefault("created_at", now)
        existing = await collection.find_one({"id": doc["id"]})
        if not existing and doc.get("name"):
            existing = await collection.find_one({"name": doc["name"]})
        if existing:
            merged = _merge_doc(existing, doc, now)
            await collection.replace_one({"_id": existing["_id"]}, merged)
        else:
            await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
        count += 1
    return count


async def ingest(path: Path = MERGED_DRAFT_PATH) -> Dict[str, int]:
    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    await ensure_database_schema(db)

    records = _records(path)
    now = datetime.utcnow()
    source_doc = {
        "id": SOURCE_PACK_ID,
        "title": "General Gym Exercise Research Library",
        "source_type": "parallel_web_research",
        "domains": ["general_gym", "strength_and_conditioning", "exercise_selection", "progressions", "substitutions"],
        "summary": "Normalized general gym S&C exercise library covering lower body, upper body, trunk/core, carries, machines, regressions, progressions, and athletic accessories.",
        "exercise_count": len(records),
        "ingestion_method": INGESTION_METHOD,
        "created_at": now,
        "updated_at": now,
    }

    counts: Dict[str, int] = {}
    for collection in ("source_registry", "knowledge_sources"):
        await db[collection].replace_one({"id": SOURCE_PACK_ID}, source_doc, upsert=True)
        counts[collection] = 1

    primary_docs = _primary_docs(records)
    raw_docs = _raw_docs(records)
    progression_docs = _progression_docs(records)
    counts["source_sections"] = await _upsert_many(db, "source_sections", _source_section_docs(records))
    counts["primary_exercise_library"] = await _upsert_many(db, "primary_exercise_library", primary_docs)
    counts["exercise_library"] = await _upsert_many(db, "exercise_library", raw_docs)
    counts["exercise_progression_graph"] = await _upsert_many(db, "exercise_progression_graph", progression_docs)
    client.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest merged general gym exercise research into MongoDB.")
    parser.add_argument("--path", default=str(MERGED_DRAFT_PATH), help="Merged exercise JSON path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = asyncio.run(ingest(Path(args.path)))
    for collection, count in counts.items():
        print(f"{collection}: {count}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOLLEYBALL_DIR = PROJECT_ROOT / "backend" / "sport_research" / "volleyball"
DRAFT_DIR = VOLLEYBALL_DIR / "drafts"
OUTPUT_PATH = VOLLEYBALL_DIR / "volleyball_teaching_database.json"

SOURCE_PACK_ID = "volleyball_teaching_database_v1"
INGESTION_METHOD = "volleyball_research_drafts_structured_converter_v1"

LEVELS = ["beginner", "intermediate", "advanced"]

DOMAIN_DRAFTS: Dict[str, List[str]] = {
    "rules_rotations_systems": ["rules_rotations_systems_draft.json"],
    "positions_roles_demands": ["positions_roles_demands_draft.json"],
    "serving": ["serving_receive_passing_draft.json", "volleyball_level_teaching_draft.json"],
    "passing_serve_receive": ["serving_receive_passing_draft.json", "volleyball_level_teaching_draft.json"],
    "setting": ["setting_offense_attacking_draft.json", "volleyball_level_teaching_draft.json"],
    "attacking": ["setting_offense_attacking_draft.json", "volleyball_level_teaching_draft.json"],
    "blocking": ["blocking_defense_transition_draft.json", "volleyball_level_teaching_draft.json"],
    "defense_digging": ["blocking_defense_transition_draft.json", "volleyball_level_teaching_draft.json"],
    "transition": ["blocking_defense_transition_draft.json", "volleyball_level_teaching_draft.json"],
    "match_iq": ["match_iq_scouting_tactics_draft.json", "volleyball_level_teaching_draft.json"],
    "volleyball_snc": ["volleyball_snc_injury_macro_planning_draft.json", "volleyball_level_teaching_draft.json"],
}

ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "setter": ["all_roles"],
    "outside_hitter": ["pin_hitter", "passer", "left_side", "all_roles"],
    "opposite": ["right_side", "pin_hitter", "all_roles"],
    "middle_blocker": ["middle_hitter", "blocker", "all_roles"],
    "middle_hitter": ["middle_blocker", "blocker", "all_roles"],
    "libero": ["defensive_specialist", "passer", "all_roles"],
    "defensive_specialist": ["libero", "passer", "all_roles"],
    "serving_specialist": ["server", "all_roles"],
}

DOMAIN_PHYSICAL_SUPPORT: Dict[str, List[str]] = {
    "serving": ["shoulder durability", "scapular control", "trunk rotation", "landing control for jump serves"],
    "passing_serve_receive": ["low stance capacity", "hip mobility", "lateral movement", "trunk control"],
    "setting": ["shoulder and wrist tolerance", "footwork speed", "trunk control", "overhead control"],
    "attacking": ["approach mechanics", "jump power", "landing control", "shoulder durability", "trunk stiffness"],
    "blocking": ["lateral net movement", "reactive jump control", "ankle and knee landing capacity", "trunk stiffness"],
    "defense_digging": ["low posture endurance", "lateral acceleration", "deceleration", "floor contact tolerance"],
    "transition": ["repeat effort capacity", "deceleration to approach", "communication under fatigue", "landing control"],
    "match_iq": ["decision quality under fatigue", "communication", "rotation awareness", "readiness management"],
    "volleyball_snc": ["lower-body strength", "repeated jump ability", "shoulder durability", "mobility", "recovery"],
}


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _dedupe(items: Iterable[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for item in items:
        if item in (None, "", [], {}):
            continue
        key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _strings(value: Any) -> List[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        items: List[str] = []
        for nested in value.values():
            items.extend(_strings(nested))
        return items
    if isinstance(value, (list, tuple, set)):
        items = []
        for nested in value:
            items.extend(_strings(nested))
        return items
    return [str(value)]


def _load_draft(file_name: str) -> Dict[str, Any]:
    path = DRAFT_DIR / file_name
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _all_drafts() -> Dict[str, Dict[str, Any]]:
    return {path.name: _load_draft(path.name) for path in sorted(DRAFT_DIR.glob("*_draft.json"))}


def _source_refs_for_files(file_names: Sequence[str], limit: int = 12) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for file_name in file_names:
        draft = _load_draft(file_name)
        for ref in draft.get("source_refs") or []:
            if not isinstance(ref, dict) or not ref.get("title") or not ref.get("url"):
                continue
            refs.append({
                "source_pack_id": SOURCE_PACK_ID,
                "draft_file": file_name,
                "title": ref.get("title"),
                "url": ref.get("url"),
                "source_type": ref.get("source_type"),
                "organization_or_author": ref.get("organization_or_author"),
                "notes": ref.get("notes"),
            })
    return _dedupe(refs)[:limit]


def _source_refs_for_domain(domain: str, limit: int = 12) -> List[Dict[str, Any]]:
    return _source_refs_for_files(DOMAIN_DRAFTS.get(domain, []), limit=limit)


def _flatten_backend_records() -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for file_name, draft in _all_drafts().items():
        for item in draft.get("backend_records_to_create") or []:
            if not isinstance(item, dict):
                continue
            if item.get("collection") and isinstance(item.get("records"), list):
                collection = str(item["collection"])
                for record in item["records"]:
                    if isinstance(record, dict):
                        flattened.append({
                            **record,
                            "_collection": collection,
                            "_draft_file": file_name,
                        })
                continue
            record_type = item.get("record_type") or item.get("collection")
            flattened.append({
                **item,
                "_collection": str(record_type or "volleyball_research_record"),
                "_draft_file": file_name,
            })
    return flattened


def _expanded_role_tags(value: Any) -> List[str]:
    tags = ["all_roles"]
    for token in _strings(value):
        slug = _slug(token)
        if not slug:
            continue
        tags.append(slug)
        tags.extend(ROLE_EQUIVALENTS.get(slug, []))
    return sorted(set(tags))


def _record_id(record: Dict[str, Any]) -> str:
    return str(record.get("record_id") or record.get("id") or _slug(record.get("name") or record.get("title") or record.get("_collection")))


def _record_title(record: Dict[str, Any]) -> str:
    return str(record.get("name") or record.get("title") or record.get("display_name") or _record_id(record).replace("_", " ").title())


def _level_doc_to_progression(record: Dict[str, Any], level: str, level_doc: Dict[str, Any]) -> Dict[str, Any]:
    domain = _slug(record.get("domain"))
    role_specific_progression = level_doc.get("role_specific_progression") or {}
    role_keys = list(role_specific_progression.keys()) if isinstance(role_specific_progression, dict) else []
    role_tags = _expanded_role_tags(role_keys)
    learning_goal = (
        level_doc.get("learning_goal")
        or f"Develop {domain.replace('_', ' ')} from {level} volleyball standards with safe progressions and clear assessment gates."
    )
    teaching_priorities = _dedupe([
        *level_doc.get("expectations", []),
        *level_doc.get("skill_prerequisites", [])[:2],
    ])
    technical_focus = _dedupe([
        *level_doc.get("expectations", []),
        *level_doc.get("skill_prerequisites", []),
    ])[:8]
    tactical_focus = _dedupe([
        *level_doc.get("assessment_signals", []),
        *level_doc.get("role_specific_progression", {}).keys(),
    ])[:8]
    typical_drills = level_doc.get("typical_drills") or []
    return {
        "id": f"volleyball_teach_{domain}_{level}",
        "sport": "volleyball",
        "domain": domain,
        "level": level,
        "role_tags": role_tags,
        "learning_goal": learning_goal,
        "suitable_for": [f"{level} volleyball players", "indoor six-player volleyball"],
        "prerequisites": level_doc.get("skill_prerequisites") or [],
        "teaching_priorities": teaching_priorities,
        "technical_focus": technical_focus,
        "tactical_focus": tactical_focus,
        "physical_support": DOMAIN_PHYSICAL_SUPPORT.get(domain, []),
        "practice_design": typical_drills[:4],
        "typical_drills": typical_drills,
        "avoid_until_ready": level_doc.get("avoid_until_ready_gates") or [],
        "progression_signals": level_doc.get("assessment_signals") or [],
        "coach_notes": _dedupe([
            *level_doc.get("coaching_notes", []),
            f"Source record: {_record_id(record)}",
        ]),
        "retrieval_tags": sorted(set([
            "volleyball",
            domain,
            level,
            *role_tags,
            *_strings(level_doc.get("expectations")),
            *_strings(level_doc.get("assessment_signals")),
        ])),
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain(domain),
    }


def _teaching_progressions(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    progressions: List[Dict[str, Any]] = []
    for record in records:
        if record.get("_collection") != "sport_teaching_progressions":
            continue
        levels = record.get("levels")
        if not isinstance(levels, dict):
            continue
        for level in LEVELS:
            level_doc = levels.get(level)
            if isinstance(level_doc, dict):
                progressions.append(_level_doc_to_progression(record, level, level_doc))
    return progressions


def _assessment_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    domain = _slug(record.get("domain"))
    level_signals = record.get("level_signals") if isinstance(record.get("level_signals"), dict) else {}
    return {
        "id": f"volleyball_assess_{domain}",
        "sport": "volleyball",
        "domain": domain,
        "summary": f"Assesses volleyball {domain.replace('_', ' ')} level using skill quality, live-game transfer, tactical decisions, and safety signals.",
        "metrics": record.get("metrics") or [],
        "level_bands": [
            {
                "level": level,
                "indicators": level_signals.get(level) or [],
                "ready_for_next_when": level_signals.get(level) or [],
            }
            for level in LEVELS
            if level_signals.get(level)
        ],
        "hold_if": record.get("red_flags") or [],
        "retrieval_tags": sorted(set(["volleyball", domain, "assessment", *_strings(record.get("metrics"))])),
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain(domain),
    }


def _skill_assessments(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        _assessment_from_record(record)
        for record in records
        if record.get("_collection") == "sport_skill_assessments"
    ]


def _transition_rule_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    record_id = _record_id(record)
    applies_to = _expanded_role_tags(record.get("applies_to") or record.get("roles") or record.get("role_tags"))
    required_evidence = record.get("required_evidence") or record.get("minimum_evidence") or []
    hold_when = record.get("do_not_progress_if") or record.get("hold_when") or []
    return {
        "id": record_id if record_id.startswith("volleyball_") else f"volleyball_level_{record_id}",
        "sport": "volleyball",
        "from_level": _slug(record.get("from_level") or "any"),
        "to_level": _slug(record.get("to_level") or "hold_or_conservative_progression"),
        "applies_to": applies_to,
        "minimum_evidence": required_evidence,
        "promote_when": required_evidence,
        "hold_when": hold_when,
        "backend_action": record.get("backend_action"),
        "retrieval_tags": sorted(set(["volleyball", *applies_to, *_strings(required_evidence), *_strings(hold_when)])),
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain("volleyball_snc"),
    }


def _level_transition_rules(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        _transition_rule_from_record(record)
        for record in records
        if record.get("_collection") == "sport_level_transition_rules"
    ]


def _sport_roles(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    role_records = [
        record
        for record in records
        if record.get("_collection") == "volleyball_role_profile"
    ]
    docs: List[Dict[str, Any]] = []
    for record in role_records:
        role = _slug(record.get("role") or _record_id(record).replace("role_profile_", ""))
        docs.append({
            "id": f"volleyball_role_{role}",
            "sport": "volleyball",
            "role": role,
            "display_name": record.get("display_name") or role.replace("_", " ").title(),
            "summary": record.get("role_summary"),
            "responsibilities": record.get("responsibilities") or {},
            "skill_priorities": _strings(record.get("responsibilities"))[:16],
            "physical_demands": DOMAIN_PHYSICAL_SUPPORT.get(role, []),
            "retrieval_tags": _expanded_role_tags(role),
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs_for_domain("positions_roles_demands"),
        })
    return docs


def _payload_summary(record: Dict[str, Any]) -> str:
    payload = record.get("payload_fields") or record.get("payload") or record.get("fields") or record
    if not isinstance(payload, dict):
        return str(payload)[:600]
    parts: List[str] = []
    for key in ("description", "summary", "selection_rule", "progression_rule", "backend_note", "rule", "condition"):
        if payload.get(key):
            parts.extend(_strings(payload[key]))
    if not parts:
        for key, value in payload.items():
            if key.startswith("_"):
                continue
            values = _strings(value)
            if values:
                parts.append(f"{key}: {', '.join(values[:5])}")
    return " ".join(parts)[:900]


def _recommended_actions(record: Dict[str, Any]) -> List[str]:
    payload = record.get("payload_fields") or record.get("payload") or record.get("fields") or {}
    if not isinstance(payload, dict):
        return []
    for key in ("then", "recommended_action", "recommended_actions", "recommended_focus", "primary_priorities", "coaching_actions", "corrections"):
        if payload.get(key):
            return _strings(payload[key])[:12]
    return _strings(record.get("training_implications"))[:12]


def _blocked_actions(record: Dict[str, Any]) -> List[str]:
    payload = record.get("payload_fields") or record.get("payload") or record.get("fields") or {}
    if not isinstance(payload, dict):
        return []
    for key in ("avoid", "do_not", "blocked_actions", "contraindications", "do_not_progress_if"):
        if payload.get(key):
            return _strings(payload[key])[:12]
    return []


def _sport_training_rules(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    excluded = {"sport_teaching_progressions", "sport_skill_assessments", "sport_level_transition_rules"}
    for record in records:
        collection = str(record.get("_collection") or "")
        if collection in excluded:
            continue
        record_id = _record_id(record)
        docs.append({
            "id": f"volleyball_training_rule_{collection}_{record_id}",
            "sport": "volleyball",
            "category": collection,
            "condition": _payload_summary(record)[:240],
            "rule": _payload_summary(record),
            "recommended_action": _recommended_actions(record),
            "blocked_action": _blocked_actions(record),
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs_for_files([record.get("_draft_file")], limit=8),
            "retrieval_tags": sorted(set(["volleyball", collection, record_id, *_strings(record)]))[:80],
        })
    return docs


def _planning_rules(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    allowed = {
        "volleyball_injury_risk_rule",
        "volleyball_macro_planning_rule",
        "volleyball_return_to_play_rule",
        "volleyball_readiness_adjustment_rule",
    }
    for record in records:
        collection = str(record.get("_collection") or "")
        if collection not in allowed:
            continue
        record_id = _record_id(record)
        docs.append({
            "id": f"volleyball_plan_{record_id}",
            "sport": "volleyball",
            "category": collection,
            "applies_to": ["volleyball"],
            "priority": 75 if collection == "volleyball_macro_planning_rule" else 90,
            "rule": _payload_summary(record),
            "recommended_action": _recommended_actions(record),
            "blocked_action": _blocked_actions(record),
            "source_refs": _source_refs_for_files([record.get("_draft_file")], limit=8),
            "source_pack_id": SOURCE_PACK_ID,
        })
    return docs


def _sport_profile(records: Sequence[Dict[str, Any]], planning_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    demand_names = [
        _record_title(record)
        for record in records
        if str(record.get("_collection") or "").endswith("physical_demand")
    ]
    risk_names = [
        _record_title(record)
        for record in records
        if "injury" in str(record.get("_collection") or "") or "risk" in str(record.get("_collection") or "")
    ]
    return {
        "id": "sport_profile_volleyball",
        "sport": "volleyball",
        "planning_summary": "Indoor volleyball is a repeated-jump, overhead, transition-based court sport. Planning should balance jump/landing exposure, shoulder contact load, role-specific court skill, match schedule, and recovery.",
        "training_priorities": [
            "jump and landing mechanics",
            "lower-body strength and power",
            "shoulder and scapular durability",
            "trunk stiffness",
            "deceleration and lateral movement",
            "low-stance defensive capacity",
            "match-week fatigue management",
        ],
        "key_physical_qualities": _dedupe([
            "repeated jump ability",
            "approach jump power",
            "block jump reactivity",
            "landing control",
            "ankle stiffness",
            "knee control",
            "hip control",
            "shoulder durability",
            "trunk stiffness",
            "lateral movement",
            *demand_names,
        ])[:20],
        "realistic_weekly_frequency": {
            "beginner": {"gym_sessions": "2-3", "court_sessions": "1-3", "jump_load": "low to moderate"},
            "intermediate": {"gym_sessions": "2-4", "court_sessions": "2-4", "jump_load": "tracked by role"},
            "advanced": {"gym_sessions": "2-4", "court_sessions": "3-6", "jump_load": "individualized and competition-aware"},
        },
        "common_injury_or_load_risks": _dedupe([
            "ankle sprain",
            "patellar tendon overload",
            "ACL landing risk",
            "shoulder overuse",
            "low back extension-rotation stress",
            "finger/wrist contact injuries",
            *risk_names,
        ])[:20],
        "do_not_pair": [
            "high-volume lower-body plyometrics with heavy lower-body strength on the same fatigue-limited day",
            "new jump-serve volume with high overhead pressing volume",
            "max jump testing during knee or patellar tendon pain",
            "high soreness lower-body work within 24 hours of important matches",
        ],
        "progression_guardrails": [
            "progress jump volume and intensity separately",
            "use pain and next-day response to adjust jumping and overhead contacts",
            "unlock advanced jump-serve, swing-block, and tempo attack work only after landing and shoulder tolerance are stable",
            "reduce gym novelty during tournament or heavy match weeks",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules[:12]],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain("volleyball_snc"),
    }


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    for index, path in enumerate(sorted(DRAFT_DIR.glob("*_draft.json")), start=60001):
        draft = _load_draft(path.name)
        metadata = draft.get("metadata") or {}
        docs.append({
            "id": f"volleyball_teaching_section_{_slug(metadata.get('domain') or path.stem)}",
            "source_book_id": SOURCE_PACK_ID,
            "section_order": index,
            "section_title": f"Volleyball {str(metadata.get('domain') or path.stem).replace('_', ' ').title()}",
            "domain": "volleyball_teaching",
            "topics": ["volleyball", _slug(metadata.get("domain") or path.stem), "teaching_progression"],
            "summary": str(metadata.get("research_goal") or "")[:1200],
            "source_refs": _source_refs_for_files([path.name]),
            "created_at": now,
            "updated_at": now,
        })
    return docs


def _with_metadata(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **record,
            "ingestion_method": INGESTION_METHOD,
            "version": "v1.0.0",
            "created_at": now,
            "updated_at": now,
        }
        for record in records
    ]


def build_database() -> Dict[str, Any]:
    raw_records = _flatten_backend_records()
    teaching_progressions = _teaching_progressions(raw_records)
    skill_assessments = _skill_assessments(raw_records)
    transition_rules = _level_transition_rules(raw_records)
    planning_rules = _planning_rules(raw_records)
    sport_roles = _sport_roles(raw_records)
    sport_training_rules = _sport_training_rules(raw_records)
    return {
        "metadata": {
            "id": SOURCE_PACK_ID,
            "title": "SFTC Volleyball Teaching And Planning Database",
            "sport": "volleyball",
            "version": "v1.0.0",
            "description": "App-facing volleyball teaching, role, tactical, S&C, injury, macro-planning, and retrieval records derived from structured volleyball research drafts.",
            "domains": sorted(DOMAIN_DRAFTS),
            "levels": LEVELS,
            "source_draft_count": len(list(DRAFT_DIR.glob("*_draft.json"))),
        },
        "sport_profiles": [_sport_profile(raw_records, planning_rules)],
        "sport_roles": sport_roles,
        "sport_training_rules": sport_training_rules,
        "planning_rules": planning_rules,
        "sport_teaching_progressions": teaching_progressions,
        "sport_skill_assessments": skill_assessments,
        "sport_level_transition_rules": transition_rules,
    }


def export_database(path: Path = OUTPUT_PATH) -> Dict[str, Any]:
    payload = build_database()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


async def _upsert_many(db: Any, collection_name: str, docs: Sequence[Dict[str, Any]]) -> int:
    count = 0
    collection = db[collection_name]
    for doc in docs:
        if not doc.get("id"):
            continue
        await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
        count += 1
    return count


async def ingest(export_only: bool = False) -> Dict[str, int]:
    payload = export_database()
    if export_only:
        return {
            f"exported_{key}": len(value)
            for key, value in payload.items()
            if isinstance(value, list)
        }

    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    await ensure_database_schema(db)

    now = datetime.utcnow()
    source_doc = {
        "id": SOURCE_PACK_ID,
        "title": payload["metadata"]["title"],
        "source_type": "curated_research_database",
        "sport": "volleyball",
        "summary": payload["metadata"]["description"],
        "source_files": sorted(str(path.relative_to(PROJECT_ROOT)) for path in DRAFT_DIR.glob("*_draft.json")),
        "created_at": now,
        "updated_at": now,
    }
    counts: Dict[str, int] = {}
    for collection_name in ("source_registry", "knowledge_sources"):
        await db[collection_name].replace_one({"id": SOURCE_PACK_ID}, source_doc, upsert=True)
        counts[collection_name] = 1

    counts["source_sections"] = await _upsert_many(db, "source_sections", _source_sections())
    for collection_name in [
        "sport_profiles",
        "sport_roles",
        "sport_training_rules",
        "planning_rules",
        "sport_teaching_progressions",
        "sport_skill_assessments",
        "sport_level_transition_rules",
    ]:
        counts[collection_name] = await _upsert_many(
            db,
            collection_name,
            _with_metadata(payload[collection_name]),
        )
    client.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and ingest volleyball app-facing teaching database.")
    parser.add_argument("--export-only", action="store_true", help="Only write the JSON export file; do not write MongoDB.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    for collection, count in counts.items():
        print(f"{collection}: {count}")
    print(f"export: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KICKBOXING_DIR = PROJECT_ROOT / "backend" / "sport_research" / "kickboxing"
DRAFT_DIR = KICKBOXING_DIR / "drafts"
OUTPUT_PATH = KICKBOXING_DIR / "kickboxing_teaching_database.json"

SOURCE_PACK_ID = "kickboxing_teaching_database_v1"
INGESTION_METHOD = "kickboxing_research_drafts_structured_converter_v1"
SPORT = "kickboxing"

DOMAIN_SOURCE_HINTS: Dict[str, List[str]] = {
    "kickboxing_rules_scoring": ["kickboxing_rules_style_systems_draft.json"],
    "kickboxing_style_differences": ["kickboxing_rules_style_systems_draft.json", "kickboxing_level_teaching_draft.json"],
    "kickboxing_stance_guard": ["kickboxing_stance_footwork_ringcraft_draft.json"],
    "kickboxing_footwork_ringcraft": ["kickboxing_stance_footwork_ringcraft_draft.json"],
    "kickboxing_punch_mechanics": ["kickboxing_strikes_combinations_defense_draft.json"],
    "kickboxing_kick_mechanics": ["kickboxing_strikes_combinations_defense_draft.json"],
    "kickboxing_kick_defense_checks": ["kickboxing_strikes_combinations_defense_draft.json"],
    "kickboxing_combinations_entries_exits": ["kickboxing_strikes_combinations_defense_draft.json"],
    "kickboxing_defense_countering": ["kickboxing_strikes_combinations_defense_draft.json"],
    "kickboxing_clinch_knees_rule_dependent": ["kickboxing_clinch_knees_rule_dependent_draft.json", "kickboxing_rules_style_systems_draft.json"],
    "kickboxing_sparring_contact": ["kickboxing_snc_injury_load_draft.json", "kickboxing_level_teaching_draft.json"],
    "kickboxing_strength_conditioning": ["kickboxing_snc_injury_load_draft.json"],
    "kickboxing_injury_load_management": ["kickboxing_snc_injury_load_draft.json"],
    "kickboxing_competition_week": ["kickboxing_snc_injury_load_draft.json"],
    "kickboxing_level_progression": ["kickboxing_level_teaching_draft.json"],
}

ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_kickboxer": ["kickboxing_level_progression", "kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_defense_countering"],
    "point_fighter": ["kickboxing_rules_scoring", "kickboxing_style_differences", "kickboxing_footwork_ringcraft", "kickboxing_combinations_entries_exits", "kickboxing_defense_countering"],
    "light_contact_fighter": ["kickboxing_rules_scoring", "kickboxing_style_differences", "kickboxing_combinations_entries_exits", "kickboxing_defense_countering", "kickboxing_sparring_contact"],
    "kick_light_fighter": ["kickboxing_rules_scoring", "kickboxing_kick_defense_checks", "kickboxing_kick_mechanics", "kickboxing_sparring_contact", "kickboxing_injury_load_management"],
    "full_contact_kickboxer": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_combinations_entries_exits", "kickboxing_strength_conditioning"],
    "low_kick_fighter": ["kickboxing_rules_scoring", "kickboxing_kick_mechanics", "kickboxing_kick_defense_checks", "kickboxing_injury_load_management", "kickboxing_strength_conditioning"],
    "k1_fighter": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_clinch_knees_rule_dependent", "kickboxing_competition_week"],
    "pressure_fighter": ["kickboxing_footwork_ringcraft", "kickboxing_combinations_entries_exits", "kickboxing_defense_countering", "kickboxing_strength_conditioning"],
    "outfighter": ["kickboxing_footwork_ringcraft", "kickboxing_kick_mechanics", "kickboxing_defense_countering", "kickboxing_style_differences"],
    "counter_fighter": ["kickboxing_defense_countering", "kickboxing_kick_defense_checks", "kickboxing_footwork_ringcraft", "kickboxing_style_differences"],
    "kicker": ["kickboxing_kick_mechanics", "kickboxing_kick_defense_checks", "kickboxing_injury_load_management", "kickboxing_strength_conditioning"],
    "boxer_kickboxer": ["kickboxing_punch_mechanics", "kickboxing_combinations_entries_exits", "kickboxing_kick_defense_checks", "kickboxing_footwork_ringcraft"],
    "southpaw": ["kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_defense_countering"],
    "orthodox": ["kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_defense_countering"],
    "fitness_kickboxing": ["kickboxing_level_progression", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_injury_load_management"],
}

ROLE_ALIASES: Dict[str, List[str]] = {
    "beginner_kickboxer": ["beginner", "new_kickboxer"],
    "point_fighter": ["point_fighting", "tatami_fighter"],
    "light_contact_fighter": ["light_contact"],
    "kick_light_fighter": ["kick_light"],
    "full_contact_kickboxer": ["full_contact"],
    "low_kick_fighter": ["low_kick"],
    "k1_fighter": ["k1", "k_1", "glory_style"],
    "pressure_fighter": ["pressure"],
    "outfighter": ["outside_fighter", "range_fighter"],
    "counter_fighter": ["counter_striker", "counter"],
    "kicker": ["kick_specialist"],
    "boxer_kickboxer": ["boxing_based", "hands_heavy"],
    "southpaw": ["left_handed"],
    "orthodox": ["right_handed"],
    "fitness_kickboxing": ["fitness", "bag_work", "no_sparring"],
}


def _slug(value: Any, fallback: str = "record") -> str:
    text = str(value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or fallback


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
        items: List[str] = []
        for nested in value:
            items.extend(_strings(nested))
        return items
    return [str(value)]


def _short(value: Any, max_chars: int = 900) -> str:
    return " ".join(_dedupe(_strings(value)))[:max_chars]


def _all_drafts() -> Dict[str, Dict[str, Any]]:
    drafts: Dict[str, Dict[str, Any]] = {}
    for path in sorted(DRAFT_DIR.glob("*_draft.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        drafts[path.name] = data if isinstance(data, dict) else {}
    return drafts


def _source_refs_for_files(drafts: Dict[str, Dict[str, Any]], file_names: Sequence[str], limit: int = 12) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for file_name in file_names:
        for ref in (drafts.get(file_name) or {}).get("source_refs") or []:
            if not isinstance(ref, dict) or not ref.get("title"):
                continue
            refs.append(
                {
                    "source_pack_id": SOURCE_PACK_ID,
                    "draft_file": file_name,
                    "title": ref.get("title"),
                    "url": ref.get("url"),
                    "source_type": ref.get("source_type"),
                    "organization_or_author": ref.get("organization_or_author"),
                    "notes": ref.get("notes"),
                }
            )
    return _dedupe(refs)[:limit]


def _domain_refs(drafts: Dict[str, Dict[str, Any]], domain: str, fallback_file: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    files = DOMAIN_SOURCE_HINTS.get(domain) or ([fallback_file] if fallback_file else [])
    return _source_refs_for_files(drafts, files, limit=limit)


def _draft_domain(file_name: str) -> str:
    return file_name.replace("_draft.json", "")


def _source_sections(drafts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs: List[Dict[str, Any]] = []
    for index, (file_name, draft) in enumerate(sorted(drafts.items()), start=122001):
        domain = _draft_domain(file_name)
        docs.append(
            {
                "id": f"kickboxing_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe([SPORT, domain, *_strings(draft.get("domains_covered")), *_strings(draft.get("research_goal"))])[:32],
                "summary": draft.get("research_goal") or draft.get("metadata", {}).get("purpose"),
                "draft_file": file_name,
                "source_refs": _source_refs_for_files(drafts, [file_name], limit=14),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _record_bucket(draft: Dict[str, Any], record_key: str) -> List[Dict[str, Any]]:
    backend_records = draft.get("backend_records") or {}
    aliases = {
        "sport_training_rules": ["sport_training_rules", "training_rules"],
        "planning_rules": ["planning_rules"],
        "teaching_progressions": ["teaching_progressions", "sport_teaching_progressions"],
        "skill_assessments": ["skill_assessments", "sport_skill_assessments"],
        "level_transition_rules": ["level_transition_rules", "sport_level_transition_rules"],
    }
    records: List[Dict[str, Any]] = []
    for key in aliases.get(record_key, [record_key]):
        bucket = backend_records.get(key) if isinstance(backend_records, dict) else None
        if isinstance(bucket, list):
            records.extend(item for item in bucket if isinstance(item, dict))
        direct = draft.get(key)
        if isinstance(direct, list):
            records.extend(item for item in direct if isinstance(item, dict))
    return records


def _normalize_record(record: Dict[str, Any], *, collection_name: str, file_name: str, index: int, drafts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    domain = _slug(record.get("domain") or record.get("category") or _draft_domain(file_name), "kickboxing_general")
    if domain in {"technical_rule", "session_design", "level_model", "safety", "load_management"}:
        domain = _draft_domain(file_name)
    record_id = _slug(record.get("id") or f"kickboxing_{collection_name}_{domain}_{index}")
    if not record_id.startswith("kickboxing_"):
        record_id = f"kickboxing_{record_id}"
    summary = _short(record.get("summary") or record.get("rule") or record.get("condition") or record.get("learning_goal") or record)
    refs = record.get("source_refs") or _domain_refs(drafts, domain, fallback_file=file_name)
    tags = _dedupe(
        [
            SPORT,
            "combat_sports",
            domain,
            collection_name,
            *_strings(record.get("retrieval_tags")),
            *_strings(record.get("output_tags")),
            *_strings(record.get("applies_to")),
            *_strings(record.get("level")),
            *_strings(record.get("from_level")),
            *_strings(record.get("to_level")),
        ]
    )
    base = {
        **record,
        "id": record_id,
        "sport": SPORT,
        "domain": domain,
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": refs,
        "retrieval_tags": tags[:120],
    }
    if collection_name == "sport_training_rules":
        base.setdefault("category", record.get("category") or "kickboxing_training_rule")
        base.setdefault("condition", _short(record.get("trigger") or record.get("condition") or summary, 240))
        base.setdefault("rule", summary)
        base.setdefault("recommended_action", _dedupe([*_strings(record.get("recommended_action")), *_strings(record.get("output_tags"))])[:10])
        base.setdefault("blocked_action", _strings(record.get("blocked_action"))[:10])
    elif collection_name == "planning_rules":
        base.setdefault("category", record.get("category") or "kickboxing_planning")
        base.setdefault("applies_to", _dedupe([SPORT, "combat_sports", *_strings(record.get("applies_to"))]))
        base.setdefault("priority", record.get("priority") or (95 if "pain" in summary.lower() or "competition" in summary.lower() else 84))
        base.setdefault("rule", summary)
        base.setdefault("recommended_action", _strings(record.get("recommended_action"))[:10])
        base.setdefault("blocked_action", _strings(record.get("blocked_action"))[:10])
    elif collection_name == "sport_teaching_progressions":
        base.setdefault("level", record.get("level") or "all")
        base.setdefault("learning_goal", summary)
        base.setdefault("teaching_priorities", _strings(record.get("teaching_priorities") or record.get("technical_focus"))[:10])
        base.setdefault("practice_design", _strings(record.get("practice_design") or record.get("progression_steps"))[:10])
        base.setdefault("avoid_until_ready", _strings(record.get("avoid_until_ready"))[:10])
        base.setdefault("progression_signals", _strings(record.get("progression_signals"))[:10])
    elif collection_name == "sport_skill_assessments":
        base.setdefault("summary", summary)
        base.setdefault("metrics", _strings(record.get("metrics"))[:12])
        base.setdefault("hold_if", _strings(record.get("hold_if"))[:12])
    elif collection_name == "sport_level_transition_rules":
        base.setdefault("from_level", record.get("from_level") or "any")
        base.setdefault("to_level", record.get("to_level") or "review")
        base.setdefault("minimum_evidence", _strings(record.get("minimum_evidence"))[:10])
        base.setdefault("promote_when", _strings(record.get("promote_when"))[:10])
        base.setdefault("hold_when", _strings(record.get("hold_when"))[:10])
        base.setdefault("backend_action", record.get("backend_action") or summary)
    return base


def _collect_records(drafts: Dict[str, Dict[str, Any]], record_key: str, collection_name: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    seen = set()
    for file_name, draft in sorted(drafts.items()):
        for index, record in enumerate(_record_bucket(draft, record_key), start=1):
            doc = _normalize_record(record, collection_name=collection_name, file_name=file_name, index=index, drafts=drafts)
            if doc["id"] in seen:
                doc["id"] = f"{doc['id']}_{_slug(_draft_domain(file_name))}_{index}"
            seen.add(doc["id"])
            docs.append(doc)
    return docs


def _physical_demands_for_role(role: str) -> List[str]:
    if role in {"point_fighter"}:
        return ["reactive speed", "lead-leg speed", "elastic footwork", "distance control", "low fatigue power"]
    if role in {"low_kick_fighter", "k1_fighter"}:
        return ["hip rotation", "adductor capacity", "calf and shin tolerance", "trunk power", "repeat-power conditioning"]
    if role in {"pressure_fighter", "boxer_kickboxer"}:
        return ["guard endurance", "rotational power", "repeat combinations", "neck/trunk stiffness", "aerobic recovery"]
    if role in {"kicker", "outfighter"}:
        return ["hip mobility", "single-leg balance", "calf capacity", "trunk rotation", "range footwork"]
    return ["aerobic base", "repeat power", "hip mobility", "trunk rotation", "shoulder endurance", "ankle/calf capacity"]


def _risk_flags_for_role(role: str) -> List[str]:
    flags = ["head_contact_risk", "wrist_hand_pain", "shoulder_pain", "hip_groin_pain", "low_back_pain"]
    if role in {"low_kick_fighter", "k1_fighter", "kick_light_fighter", "kicker"}:
        flags.extend(["knee_pain", "shin_pain", "ankle_pain", "adductor_pain"])
    if role in {"point_fighter", "outfighter"}:
        flags.extend(["achilles_pain", "calf_pain"])
    return _dedupe(flags)


def _sport_roles(drafts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for role, domains in ROLE_DOMAIN_TAGS.items():
        docs.append(
            {
                "id": f"kickboxing_role_{role}",
                "sport": SPORT,
                "role": role,
                "display_name": role.replace("_", " ").title(),
                "aliases": ROLE_ALIASES.get(role, []),
                "summary": f"Kickboxing role emphasizing {', '.join(domain.replace('kickboxing_', '').replace('_', ' ') for domain in domains[:5])}.",
                "responsibilities": {
                    "primary_domains": domains,
                    "rule_set_context": ["point_fighting", "light_contact", "kick_light", "full_contact", "low_kick", "k1", "fitness_kickboxing"],
                },
                "skill_priorities": domains,
                "physical_demands": _physical_demands_for_role(role),
                "risk_flags": _risk_flags_for_role(role),
                "retrieval_tags": sorted(set([SPORT, "combat_sports", role, *ROLE_ALIASES.get(role, []), *domains])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _domain_refs(drafts, domains[0] if domains else "kickboxing_level_progression"),
            }
        )
    return docs


def _sport_profile(drafts: Dict[str, Dict[str, Any]], planning_rules: Sequence[Dict[str, Any]], training_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_kickboxing",
        "sport": SPORT,
        "planning_summary": (
            "Kickboxing is a rule-set-dependent striking sport. Point fighting, light contact, kick light, "
            "full contact, low kick, K-1/Glory style, and fitness kickboxing create different priorities for "
            "stance, footwork, punch/kick mechanics, checking, combinations, sparring, knees, conditioning, and injury management."
        ),
        "training_priorities": [
            "identify rule set and contact level before selecting tactics",
            "build stance, guard, footwork, and strike recovery first",
            "connect punch-kick combinations to defensive exits",
            "progress low-kick and K-1 knee content only when rule set and readiness support it",
            "treat sparring, bag impact, pad impact, low-kick contact, and head contact as training load",
            "train aerobic base, repeat power, hip mobility, trunk rotation, shoulder endurance, calf/ankle capacity, and adductor resilience",
            "preserve technical quality and safety during conditioning",
        ],
        "key_physical_qualities": [
            "aerobic recovery",
            "repeat power",
            "rotational power",
            "hip mobility",
            "adductor capacity",
            "calf and ankle stiffness",
            "shoulder and scapular endurance",
            "trunk stiffness",
            "reaction speed",
            "contact tolerance",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"technical_sessions": "2-4", "snc_sessions": "2-3", "sparring": "none or constrained technical"},
            "intermediate": {"technical_sessions": "3-5", "snc_sessions": "2-4", "sparring": "controlled and rule-set specific"},
            "advanced": {"technical_sessions": "5-8", "snc_sessions": "2-4", "sparring": "periodized by camp and readiness"},
        },
        "common_injury_or_load_risks": [
            "head-contact symptoms",
            "hand and wrist pain",
            "shoulder irritation",
            "neck and trunk fatigue",
            "hip, groin, and adductor irritation",
            "knee pain",
            "shin, ankle, foot, calf, and Achilles overload",
            "unsafe weight-cut behavior",
        ],
        "do_not_pair": [
            "hard sparring with poor sleep or head-contact symptoms",
            "hard low-kick sparring with shin, knee, ankle, or hip pain",
            "heavy eccentric lower-body work close to fight day",
            "high-volume kicking with hip/adductor irritation",
            "fatigue circuits that destroy guard, stance, and contact control",
        ],
        "progression_guardrails": [
            "progress stance and single strikes before combinations",
            "progress defense before hard sparring",
            "unlock rule-set-specific low-kick, point-fighting, or K-1 knee content by readiness",
            "reduce contact load when symptoms or readiness worsen",
            "competition week preserves sharpness while reducing soreness and contact risk",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules[:18]],
        "training_rule_ids": [rule["id"] for rule in training_rules[:24]],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_files(drafts, sorted(drafts.keys()), limit=24),
    }


def _with_metadata(docs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    return [
        {
            **doc,
            "source_pack_id": doc.get("source_pack_id") or SOURCE_PACK_ID,
            "ingestion_method": doc.get("ingestion_method") or INGESTION_METHOD,
            "created_at": doc.get("created_at") or now,
            "updated_at": now,
            "version": doc.get("version") or "v1.0.0",
        }
        for doc in docs
    ]


def build_database_payload() -> Dict[str, Any]:
    drafts = _all_drafts()
    training_rules = _collect_records(drafts, "sport_training_rules", "sport_training_rules")
    planning_rules = _collect_records(drafts, "planning_rules", "planning_rules")
    collections = {
        "source_sections": _source_sections(drafts),
        "sport_profiles": [_sport_profile(drafts, planning_rules, training_rules)],
        "sport_roles": _sport_roles(drafts),
        "sport_training_rules": training_rules,
        "planning_rules": planning_rules,
        "sport_teaching_progressions": _collect_records(drafts, "teaching_progressions", "sport_teaching_progressions"),
        "sport_skill_assessments": _collect_records(drafts, "skill_assessments", "sport_skill_assessments"),
        "sport_level_transition_rules": _collect_records(drafts, "level_transition_rules", "sport_level_transition_rules"),
    }
    refs = _source_refs_for_files(drafts, sorted(drafts.keys()), limit=40)
    return {
        "metadata": {
            "source_pack_id": SOURCE_PACK_ID,
            "sport": SPORT,
            "created_at": datetime.utcnow().isoformat(),
            "ingestion_method": INGESTION_METHOD,
            "draft_files": sorted(drafts.keys()),
            "collection_counts": {name: len(records) for name, records in collections.items()},
        },
        "source_registry": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Kickboxing Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing kickboxing teaching, tactical, rules, safety, S&C, competition-week, and level progression records generated from structured research drafts.",
                "evidence_rank": 80,
                "source_refs": refs,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Kickboxing Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized kickboxing knowledge pack for retrieval and AI workout generation.",
                "source_refs": refs,
            }
        ],
        "collections": {name: _with_metadata(records) for name, records in collections.items()},
    }


async def _upsert_many(db: Any, collection_name: str, records: Sequence[Dict[str, Any]]) -> int:
    count = 0
    collection = db[collection_name]
    for record in records:
        if not record.get("id"):
            continue
        await collection.replace_one({"id": record["id"]}, record, upsert=True)
        count += 1
    return count


async def ingest(*, export_only: bool = False) -> Dict[str, int]:
    payload = build_database_payload()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = {name: len(records) for name, records in payload["collections"].items()}
    if export_only:
        return counts

    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        await ensure_database_schema(db)
        for collection_name in ("source_registry", "knowledge_sources"):
            await _upsert_many(db, collection_name, _with_metadata(payload[collection_name]))
        for collection_name, records in payload["collections"].items():
            counts[collection_name] = await _upsert_many(db, collection_name, records)
        return counts
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert kickboxing research drafts into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

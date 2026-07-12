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
MMA_DIR = PROJECT_ROOT / "backend" / "sport_research" / "mma"
DRAFT_DIR = MMA_DIR / "drafts"
OUTPUT_PATH = MMA_DIR / "mma_teaching_database.json"

SOURCE_PACK_ID = "mma_teaching_database_v1"
INGESTION_METHOD = "mma_research_drafts_structured_converter_v1"
SPORT = "mma"
LEVELS = ["beginner", "intermediate", "advanced"]

DOMAIN_SOURCE_HINTS: Dict[str, List[str]] = {
    "mma_rules_scoring": ["rules_scoring_fight_iq_draft.json"],
    "mma_fight_iq": ["rules_scoring_fight_iq_draft.json", "mma_level_teaching_draft.json"],
    "mma_range_management": ["rules_scoring_fight_iq_draft.json", "striking_kickboxing_mma_draft.json"],
    "mma_stance_guard": ["striking_kickboxing_mma_draft.json", "mma_level_teaching_draft.json"],
    "mma_striking_entries": ["striking_kickboxing_mma_draft.json"],
    "mma_kicking": ["striking_kickboxing_mma_draft.json"],
    "mma_striking_defense": ["striking_kickboxing_mma_draft.json"],
    "mma_clinch_cage": ["wrestling_grappling_cage_draft.json", "striking_kickboxing_mma_draft.json"],
    "mma_wrestling": ["wrestling_grappling_cage_draft.json"],
    "mma_takedown_entries": ["wrestling_grappling_cage_draft.json"],
    "mma_takedown_defense": ["wrestling_grappling_cage_draft.json"],
    "mma_ground_control": ["wrestling_grappling_cage_draft.json"],
    "mma_submissions": ["wrestling_grappling_cage_draft.json"],
    "mma_escapes_scrambles": ["wrestling_grappling_cage_draft.json"],
    "mma_ground_and_pound": ["wrestling_grappling_cage_draft.json"],
    "mma_transitions": ["wrestling_grappling_cage_draft.json", "rules_scoring_fight_iq_draft.json"],
    "mma_strength_conditioning": ["mma_snc_fight_camp_draft.json"],
    "mma_sparring_contact": ["mma_snc_fight_camp_draft.json", "mma_level_teaching_draft.json"],
    "mma_fight_camp": ["mma_snc_fight_camp_draft.json", "rules_scoring_fight_iq_draft.json"],
    "mma_injury_load_management": ["mma_snc_fight_camp_draft.json", "mma_level_teaching_draft.json"],
    "mma_level_progression": ["mma_level_teaching_draft.json"],
}

ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_mma": ["mma_level_progression", "mma_stance_guard", "mma_wrestling", "mma_ground_control", "mma_strength_conditioning"],
    "mma_generalist": ["mma_fight_iq", "mma_striking_entries", "mma_wrestling", "mma_ground_control", "mma_strength_conditioning"],
    "striker": ["mma_stance_guard", "mma_striking_entries", "mma_kicking", "mma_striking_defense", "mma_range_management"],
    "kickboxer": ["mma_stance_guard", "mma_striking_entries", "mma_kicking", "mma_clinch_cage", "mma_range_management"],
    "wrestler": ["mma_wrestling", "mma_takedown_entries", "mma_takedown_defense", "mma_clinch_cage", "mma_ground_control"],
    "grappler": ["mma_ground_control", "mma_submissions", "mma_escapes_scrambles", "mma_takedown_defense", "mma_clinch_cage"],
    "bjj_grappler": ["mma_ground_control", "mma_submissions", "mma_escapes_scrambles", "mma_transitions"],
    "pressure_fighter": ["mma_range_management", "mma_clinch_cage", "mma_wrestling", "mma_striking_entries", "mma_strength_conditioning"],
    "counter_fighter": ["mma_range_management", "mma_striking_defense", "mma_fight_iq", "mma_takedown_defense"],
    "southpaw": ["mma_stance_guard", "mma_range_management", "mma_striking_entries", "mma_fight_iq"],
    "orthodox": ["mma_stance_guard", "mma_range_management", "mma_striking_entries", "mma_fight_iq"],
}

ROLE_ALIASES: Dict[str, List[str]] = {
    "beginner_mma": ["beginner", "new_mma_user"],
    "mma_generalist": ["mixed_martial_artist", "all_rounder", "all_around"],
    "striker": ["standup_fighter", "boxing_based", "striking_based"],
    "kickboxer": ["muay_thai", "k1", "standup_fighter"],
    "wrestler": ["wrestling_based", "takedown_fighter"],
    "grappler": ["submission_grappler", "ground_fighter"],
    "bjj_grappler": ["bjj", "jiu_jitsu", "submission_grappler"],
    "pressure_fighter": ["pressure", "cage_pressure"],
    "counter_fighter": ["counter_striker", "counter"],
    "southpaw": ["left_handed", "opposite_stance"],
    "orthodox": ["right_handed"],
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
    text = " ".join(_dedupe(_strings(value)))
    return text[:max_chars]


def _load_draft(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _all_drafts() -> Dict[str, Dict[str, Any]]:
    return {path.name: _load_draft(path) for path in sorted(DRAFT_DIR.glob("*_draft.json"))}


def _source_refs_for_files(drafts: Dict[str, Dict[str, Any]], file_names: Sequence[str], limit: int = 12) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for file_name in file_names:
        draft = drafts.get(file_name) or {}
        for ref in draft.get("source_refs") or []:
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
    for index, (file_name, draft) in enumerate(sorted(drafts.items()), start=120001):
        domain = _draft_domain(file_name)
        docs.append(
            {
                "id": f"mma_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe([SPORT, domain, *_strings(draft.get("domains_covered")), *_strings(draft.get("research_goal"))])[:32],
                "summary": draft.get("research_goal"),
                "draft_file": file_name,
                "source_refs": _source_refs_for_files(drafts, [file_name], limit=14),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _normalize_rule_record(
    record: Dict[str, Any],
    *,
    collection_name: str,
    file_name: str,
    index: int,
    drafts: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    domain = _slug(record.get("domain") or record.get("category") or _draft_domain(file_name), "mma_general")
    record_id = _slug(record.get("id") or f"mma_{collection_name}_{domain}_{index}")
    if not record_id.startswith("mma_"):
        record_id = f"mma_{record_id}"
    summary = _short(record.get("summary") or record.get("rule") or record.get("condition") or record.get("learning_goal") or record)
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
    refs = record.get("source_refs") or _domain_refs(drafts, domain, fallback_file=file_name)
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
        base.setdefault("category", record.get("category") or "mma_training_rule")
        base.setdefault("condition", _short(record.get("trigger") or record.get("condition") or summary, 240))
        base.setdefault("rule", summary)
        base.setdefault("recommended_action", _dedupe([*_strings(record.get("recommended_action")), *_strings(record.get("output_tags"))])[:10])
        base.setdefault("blocked_action", _strings(record.get("blocked_action"))[:10])
    elif collection_name == "planning_rules":
        base.setdefault("category", record.get("category") or "mma_planning")
        base.setdefault("applies_to", _dedupe([SPORT, "combat_sports", *_strings(record.get("applies_to"))]))
        base.setdefault("priority", record.get("priority") or (100 if "symptom" in summary.lower() or "contact" in summary.lower() else 82))
        base.setdefault("rule", summary)
        base.setdefault("recommended_action", _strings(record.get("recommended_action"))[:10])
        base.setdefault("blocked_action", _strings(record.get("blocked_action"))[:10])
    elif collection_name == "sport_teaching_progressions":
        base.setdefault("level", record.get("level") or "all")
        base.setdefault("learning_goal", summary)
        base.setdefault("teaching_priorities", _strings(record.get("teaching_priorities") or record.get("technical_focus"))[:10])
        base.setdefault("practice_design", _strings(record.get("practice_design"))[:10])
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


def _collect_backend_records(drafts: Dict[str, Dict[str, Any]], record_key: str, collection_name: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    seen = set()
    for file_name, draft in sorted(drafts.items()):
        records = ((draft.get("backend_records") or {}).get(record_key) or [])
        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue
            doc = _normalize_rule_record(record, collection_name=collection_name, file_name=file_name, index=index, drafts=drafts)
            if doc["id"] in seen:
                doc["id"] = f"{doc['id']}_{_slug(_draft_domain(file_name))}_{index}"
            seen.add(doc["id"])
            docs.append(doc)
    return docs


def _sport_roles(drafts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for role, domains in ROLE_DOMAIN_TAGS.items():
        docs.append(
            {
                "id": f"mma_role_{role}",
                "sport": SPORT,
                "role": role,
                "display_name": role.replace("_", " ").title(),
                "aliases": ROLE_ALIASES.get(role, []),
                "summary": f"MMA role emphasizing {', '.join(domain.replace('mma_', '').replace('_', ' ') for domain in domains[:5])}.",
                "responsibilities": {
                    "primary_domains": domains,
                    "safety_context": ["contact readiness", "phase connection", "symptom tracking"],
                },
                "skill_priorities": domains,
                "physical_demands": _physical_demands_for_role(role),
                "risk_flags": _risk_flags_for_role(role),
                "retrieval_tags": sorted(set([SPORT, "combat_sports", role, *ROLE_ALIASES.get(role, []), *domains])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _domain_refs(drafts, domains[0] if domains else "mma_level_progression"),
            }
        )
    return docs


def _physical_demands_for_role(role: str) -> List[str]:
    if role in {"striker", "kickboxer", "counter_fighter"}:
        return ["rotational power", "footwork capacity", "shoulder durability", "reaction speed", "aerobic recovery"]
    if role in {"wrestler", "pressure_fighter"}:
        return ["posterior-chain strength", "grip endurance", "neck/trunk stiffness", "repeat-power conditioning", "hip mobility"]
    if role in {"grappler", "bjj_grappler"}:
        return ["grip endurance", "hip mobility", "trunk stiffness", "shoulder/elbow resilience", "scramble repeatability"]
    return ["aerobic base", "repeat power", "trunk control", "shoulder durability", "hip mobility"]


def _risk_flags_for_role(role: str) -> List[str]:
    flags = ["head_symptoms", "neck_pain", "shoulder_pain"]
    if role in {"striker", "kickboxer", "counter_fighter"}:
        flags.extend(["hand_wrist_pain", "shin_foot_pain"])
    if role in {"wrestler", "pressure_fighter"}:
        flags.extend(["knee_pain", "rib_pain", "low_back_pain"])
    if role in {"grappler", "bjj_grappler"}:
        flags.extend(["elbow_pain", "knee_pain", "neck_pain"])
    return _dedupe(flags)


def _sport_profile(planning_rules: Sequence[Dict[str, Any]], training_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_mma",
        "sport": SPORT,
        "planning_summary": (
            "MMA combines striking, wrestling, clinch/cage control, ground control, submissions, "
            "ground-and-pound, transitions, fight IQ, contact management, and round-based conditioning. "
            "Training must connect phases and gate contact by domain readiness."
        ),
        "training_priorities": [
            "domain-specific level assessment instead of one global MMA label",
            "stance, guard, range, and defense before contact escalation",
            "strike-to-takedown and takedown-to-control phase connection",
            "cage wrestling, wall-walks, pummeling, and mat-return logic",
            "ground position, posture, tap culture, and escapes before high-risk submissions",
            "aerobic base, repeat-power conditioning, rotational power, trunk/neck/shoulder durability",
            "contact load, symptoms, sleep, stress, and recovery tracked in athlete_state",
            "fight-camp and opponent-specific work only for advanced, ready athletes",
        ],
        "key_physical_qualities": [
            "aerobic base",
            "anaerobic repeat power",
            "relative strength",
            "rotational power",
            "neck and trunk stiffness",
            "shoulder/scapular durability",
            "grip and upper-back endurance",
            "hip mobility",
            "adductor and knee capacity",
            "reaction speed",
            "late-round technical repeatability",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"mma_skill_sessions": "2-4", "snc_sessions": "2-3", "sparring": "none or touch/technical only"},
            "intermediate": {"mma_skill_sessions": "3-6", "snc_sessions": "2-4", "sparring": "controlled and task-defined"},
            "advanced": {"mma_skill_sessions": "5-10", "snc_sessions": "2-4", "sparring": "periodized by camp phase and readiness"},
        },
        "common_injury_or_load_risks": [
            "head trauma or concussion symptoms",
            "hand and wrist impact overload",
            "neck overload from contact and grappling",
            "shoulder, elbow, and wrist stress from posting, frames, pummeling, and submissions",
            "rib and trunk irritation from clinch and body shots",
            "knee, ankle, and adductor strain from kicks, shots, sprawls, and scrambles",
            "fatigue and dehydration risk from unsafe weight cutting",
        ],
        "do_not_pair": [
            "hard sparring with heavy neck work",
            "hard live wrestling with heavy lower-body strength on poor readiness days",
            "advanced submissions with beginner tap culture",
            "fight-camp conditioning with unresolved symptoms",
            "late-camp novelty with high contact load",
        ],
        "progression_guardrails": [
            "progress solo mechanics to cooperative partner work to constrained resistance to controlled sparring",
            "use the weakest safety-relevant domain to gate contact and advanced drills",
            "track contact load and symptoms like training load",
            "reduce contact and live grappling when head, neck, joint, sleep, stress, or readiness signals are poor",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules[:18]],
        "training_rule_ids": [rule["id"] for rule in training_rules[:24]],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_files(drafts=_all_drafts(), file_names=sorted(_all_drafts().keys()), limit=24),
    }


def _with_metadata(docs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    output: List[Dict[str, Any]] = []
    for doc in docs:
        output.append(
            {
                **doc,
                "source_pack_id": doc.get("source_pack_id") or SOURCE_PACK_ID,
                "ingestion_method": doc.get("ingestion_method") or INGESTION_METHOD,
                "created_at": doc.get("created_at") or now,
                "updated_at": now,
                "version": doc.get("version") or "v1.0.0",
            }
        )
    return output


def build_database_payload() -> Dict[str, Any]:
    drafts = _all_drafts()
    training_rules = _collect_backend_records(drafts, "sport_training_rules", "sport_training_rules")
    planning_rules = _collect_backend_records(drafts, "planning_rules", "planning_rules")
    collections = {
        "source_sections": _source_sections(drafts),
        "sport_profiles": [_sport_profile(planning_rules, training_rules)],
        "sport_roles": _sport_roles(drafts),
        "sport_training_rules": training_rules,
        "planning_rules": planning_rules,
        "sport_teaching_progressions": _collect_backend_records(drafts, "teaching_progressions", "sport_teaching_progressions"),
        "sport_skill_assessments": _collect_backend_records(drafts, "skill_assessments", "sport_skill_assessments"),
        "sport_level_transition_rules": _collect_backend_records(drafts, "level_transition_rules", "sport_level_transition_rules"),
    }
    all_source_refs = _source_refs_for_files(drafts, sorted(drafts.keys()), limit=40)
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
                "title": "SFTC MMA Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing MMA teaching, tactical, safety, S&C, fight-camp, and level progression records generated from structured research drafts.",
                "evidence_rank": 80,
                "source_refs": all_source_refs,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC MMA Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized MMA knowledge pack for retrieval and AI workout generation.",
                "source_refs": all_source_refs,
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
    parser = argparse.ArgumentParser(description="Convert MMA research drafts into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

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
WRESTLING_DIR = PROJECT_ROOT / "backend" / "sport_research" / "wrestling"
DRAFT_DIR = WRESTLING_DIR / "drafts"
OUTPUT_PATH = WRESTLING_DIR / "wrestling_teaching_database.json"

SOURCE_PACK_ID = "wrestling_teaching_database_v1"
INGESTION_METHOD = "wrestling_research_drafts_structured_converter_v1"
SPORT = "wrestling"

DOMAIN_SOURCE_HINTS: Dict[str, List[str]] = {
    "wrestling_rules_scoring": ["wrestling_rules_style_systems_draft.json"],
    "wrestling_style_differences": ["wrestling_rules_style_systems_draft.json", "wrestling_level_teaching_draft.json"],
    "wrestling_stance_motion": ["wrestling_neutral_takedown_systems_draft.json"],
    "wrestling_hand_fighting_ties": ["wrestling_neutral_takedown_systems_draft.json"],
    "wrestling_takedown_offense": ["wrestling_neutral_takedown_systems_draft.json"],
    "wrestling_takedown_defense": ["wrestling_neutral_takedown_systems_draft.json"],
    "wrestling_top_control_turns": ["wrestling_top_bottom_par_terre_draft.json"],
    "wrestling_bottom_escapes_reversals": ["wrestling_top_bottom_par_terre_draft.json"],
    "wrestling_par_terre": ["wrestling_top_bottom_par_terre_draft.json", "wrestling_rules_style_systems_draft.json"],
    "wrestling_mat_returns": ["wrestling_top_bottom_par_terre_draft.json"],
    "wrestling_scrambles": ["wrestling_neutral_takedown_systems_draft.json", "wrestling_level_teaching_draft.json"],
    "wrestling_edge_tactics": ["wrestling_rules_style_systems_draft.json"],
    "wrestling_match_iq": ["wrestling_rules_style_systems_draft.json", "wrestling_level_teaching_draft.json"],
    "wrestling_strength_conditioning": ["wrestling_snc_injury_load_draft.json"],
    "wrestling_injury_load_management": ["wrestling_snc_injury_load_draft.json"],
    "wrestling_competition_week": ["wrestling_snc_injury_load_draft.json", "wrestling_rules_style_systems_draft.json"],
    "wrestling_level_progression": ["wrestling_level_teaching_draft.json"],
}

ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_wrestler": ["wrestling_level_progression", "wrestling_stance_motion", "wrestling_takedown_defense", "wrestling_top_control_turns", "wrestling_bottom_escapes_reversals"],
    "folkstyle_wrestler": ["wrestling_rules_scoring", "wrestling_top_control_turns", "wrestling_bottom_escapes_reversals", "wrestling_mat_returns", "wrestling_match_iq"],
    "freestyle_wrestler": ["wrestling_rules_scoring", "wrestling_takedown_offense", "wrestling_par_terre", "wrestling_edge_tactics", "wrestling_match_iq"],
    "greco_wrestler": ["wrestling_rules_scoring", "wrestling_hand_fighting_ties", "wrestling_par_terre", "wrestling_style_differences", "wrestling_strength_conditioning"],
    "leg_attacker": ["wrestling_stance_motion", "wrestling_takedown_offense", "wrestling_takedown_defense", "wrestling_scrambles"],
    "upper_body_wrestler": ["wrestling_hand_fighting_ties", "wrestling_takedown_offense", "wrestling_par_terre", "wrestling_strength_conditioning"],
    "counter_wrestler": ["wrestling_takedown_defense", "wrestling_hand_fighting_ties", "wrestling_scrambles", "wrestling_match_iq"],
    "top_rider": ["wrestling_top_control_turns", "wrestling_mat_returns", "wrestling_strength_conditioning"],
    "bottom_escape_specialist": ["wrestling_bottom_escapes_reversals", "wrestling_scrambles", "wrestling_match_iq"],
    "scrambler": ["wrestling_scrambles", "wrestling_takedown_defense", "wrestling_bottom_escapes_reversals"],
}

ROLE_ALIASES: Dict[str, List[str]] = {
    "beginner_wrestler": ["beginner", "new_wrestler"],
    "folkstyle_wrestler": ["folkstyle", "scholastic", "collegiate"],
    "freestyle_wrestler": ["freestyle"],
    "greco_wrestler": ["greco", "greco_roman"],
    "leg_attacker": ["shot_wrestler", "single_leg", "double_leg"],
    "upper_body_wrestler": ["thrower", "greco_style"],
    "counter_wrestler": ["defensive_wrestler", "reattack"],
    "top_rider": ["rider", "top_wrestler"],
    "bottom_escape_specialist": ["bottom_wrestler", "escape_specialist"],
    "scrambler": ["scramble_wrestler", "funk"],
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
    for index, (file_name, draft) in enumerate(sorted(drafts.items()), start=121001):
        domain = _draft_domain(file_name)
        docs.append(
            {
                "id": f"wrestling_section_{domain}",
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


def _normalize_record(record: Dict[str, Any], *, collection_name: str, file_name: str, index: int, drafts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    domain = _slug(record.get("domain") or record.get("category") or _draft_domain(file_name), "wrestling_general")
    record_id = _slug(record.get("id") or f"wrestling_{collection_name}_{domain}_{index}")
    if not record_id.startswith("wrestling_"):
        record_id = f"wrestling_{record_id}"
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
        base.setdefault("category", record.get("category") or "wrestling_training_rule")
        base.setdefault("condition", _short(record.get("trigger") or record.get("condition") or summary, 240))
        base.setdefault("rule", summary)
        base.setdefault("recommended_action", _dedupe([*_strings(record.get("recommended_action")), *_strings(record.get("output_tags"))])[:10])
        base.setdefault("blocked_action", _strings(record.get("blocked_action"))[:10])
    elif collection_name == "planning_rules":
        base.setdefault("category", record.get("category") or "wrestling_planning")
        base.setdefault("applies_to", _dedupe([SPORT, "combat_sports", *_strings(record.get("applies_to"))]))
        base.setdefault("priority", record.get("priority") or (95 if "pain" in summary.lower() or "competition" in summary.lower() else 82))
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


def _collect_records(drafts: Dict[str, Dict[str, Any]], record_key: str, collection_name: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    seen = set()
    for file_name, draft in sorted(drafts.items()):
        for index, record in enumerate(((draft.get("backend_records") or {}).get(record_key) or []), start=1):
            if not isinstance(record, dict):
                continue
            doc = _normalize_record(record, collection_name=collection_name, file_name=file_name, index=index, drafts=drafts)
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
                "id": f"wrestling_role_{role}",
                "sport": SPORT,
                "role": role,
                "display_name": role.replace("_", " ").title(),
                "aliases": ROLE_ALIASES.get(role, []),
                "summary": f"Wrestling role emphasizing {', '.join(domain.replace('wrestling_', '').replace('_', ' ') for domain in domains[:5])}.",
                "responsibilities": {
                    "primary_domains": domains,
                    "style_context": ["folkstyle", "freestyle", "greco", "general wrestling"],
                },
                "skill_priorities": domains,
                "physical_demands": _physical_demands_for_role(role),
                "risk_flags": _risk_flags_for_role(role),
                "retrieval_tags": sorted(set([SPORT, "combat_sports", role, *ROLE_ALIASES.get(role, []), *domains])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _domain_refs(drafts, domains[0] if domains else "wrestling_level_progression"),
            }
        )
    return docs


def _physical_demands_for_role(role: str) -> List[str]:
    if role in {"leg_attacker", "scrambler"}:
        return ["hip mobility", "knee capacity", "posterior-chain strength", "repeat shots", "trunk stiffness"]
    if role in {"upper_body_wrestler", "greco_wrestler"}:
        return ["neck/trunk stiffness", "grip endurance", "upper-back strength", "hip extension", "shoulder durability"]
    if role in {"top_rider", "folkstyle_wrestler"}:
        return ["grip endurance", "isometric trunk strength", "mat return capacity", "upper-back endurance"]
    if role == "bottom_escape_specialist":
        return ["hip heist power", "trunk control", "hand-fighting endurance", "shoulder resilience"]
    return ["relative strength", "aerobic base", "repeat power", "neck/trunk control", "hip mobility"]


def _risk_flags_for_role(role: str) -> List[str]:
    flags = ["neck_pain", "shoulder_pain", "low_back_pain"]
    if role in {"leg_attacker", "scrambler", "freestyle_wrestler"}:
        flags.extend(["knee_pain", "hip_groin_pain", "ankle_pain"])
    if role in {"upper_body_wrestler", "greco_wrestler"}:
        flags.extend(["rib_pain", "elbow_pain"])
    if role in {"top_rider", "bottom_escape_specialist"}:
        flags.extend(["wrist_finger_pain", "rib_pain"])
    return _dedupe(flags)


def _sport_profile(drafts: Dict[str, Dict[str, Any]], planning_rules: Sequence[Dict[str, Any]], training_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_wrestling",
        "sport": SPORT,
        "planning_summary": (
            "Wrestling is a rule-set-specific grappling sport built around stance, motion, hand fighting, "
            "takedowns, takedown defense, top control, bottom escapes, par terre, scrambles, match IQ, "
            "relative strength, repeat power, grip, neck/trunk control, and safe weight/load management."
        ),
        "training_priorities": [
            "identify wrestling style: folkstyle, freestyle, Greco, or general",
            "build stance, motion, level change, and hand-fighting literacy first",
            "connect tie systems to takedown offense and defense",
            "match top/bottom/par-terre emphasis to rule set",
            "progress live intensity only after safe mechanics and domain readiness",
            "train relative strength, repeat power, grip, neck/trunk stiffness, hips, adductors, knees, and aerobic support",
            "protect against unsafe weight-cut behavior and poor-readiness live volume",
        ],
        "key_physical_qualities": [
            "relative strength",
            "repeat power",
            "grip endurance",
            "neck and trunk stiffness",
            "hip mobility",
            "adductor and knee capacity",
            "posterior-chain strength",
            "aerobic recovery",
            "scramble repeatability",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"wrestling_sessions": "2-4", "snc_sessions": "2-3", "live_goes": "none or short controlled goes"},
            "intermediate": {"wrestling_sessions": "3-6", "snc_sessions": "2-4", "live_goes": "controlled and position-defined"},
            "advanced": {"wrestling_sessions": "5-9", "snc_sessions": "2-4", "live_goes": "periodized by competition phase"},
        },
        "common_injury_or_load_risks": [
            "neck symptoms",
            "shoulder, elbow, wrist, and finger overload",
            "rib and trunk irritation",
            "low-back irritation",
            "hip, groin, adductor, knee, and ankle strain",
            "skin and hygiene risk",
            "unsafe dehydration or weight-cut behavior",
        ],
        "do_not_pair": [
            "hard live wrestling with heavy neck work",
            "high-volume shots with knee, groin, hip, or back pain",
            "hard live volume with poor sleep, high stress, or poor readiness",
            "heavy eccentric lower-body work close to competition",
            "unsafe weight-cut behavior with hard conditioning",
        ],
        "progression_guardrails": [
            "progress mechanics to cooperative partner work to controlled resistance to short live goes",
            "use domain readiness to unlock advanced throws, scrambles, and live volume",
            "style-specific rules should change exercise and skill selection",
            "reduce live and shot volume when pain/readiness signals worsen",
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
                "title": "SFTC Wrestling Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing wrestling teaching, tactical, safety, S&C, competition-week, and level progression records generated from structured research drafts.",
                "evidence_rank": 80,
                "source_refs": refs,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Wrestling Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized wrestling knowledge pack for retrieval and AI workout generation.",
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
    parser = argparse.ArgumentParser(description="Convert wrestling research drafts into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

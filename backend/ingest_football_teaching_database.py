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
FOOTBALL_DIR = PROJECT_ROOT / "backend" / "sport_research" / "football"
DRAFT_DIR = FOOTBALL_DIR / "drafts"
OUTPUT_PATH = FOOTBALL_DIR / "football_teaching_database.json"

SOURCE_PACK_ID = "football_teaching_database_v1"
INGESTION_METHOD = "football_research_drafts_structured_converter_v1"
SPORT = "soccer"

LEVELS = ["beginner", "intermediate", "advanced"]

DOMAIN_DRAFTS: Dict[str, List[str]] = {
    "rules_match_structure_game_model": ["rules_match_structure_game_model_draft.json"],
    "positions_roles_demands": ["positions_roles_demands_draft.json"],
    "ball_mastery": ["ball_mastery_first_touch_passing_draft.json", "football_level_teaching_draft.json"],
    "first_touch_receiving": ["ball_mastery_first_touch_passing_draft.json", "football_level_teaching_draft.json"],
    "passing": ["ball_mastery_first_touch_passing_draft.json", "football_level_teaching_draft.json"],
    "dribbling_1v1": ["dribbling_1v1_carrying_turning_draft.json", "football_level_teaching_draft.json"],
    "shooting_finishing": ["shooting_finishing_crossing_chance_creation_draft.json", "football_level_teaching_draft.json"],
    "crossing_chance_creation": ["shooting_finishing_crossing_chance_creation_draft.json", "football_level_teaching_draft.json"],
    "defending_pressing": ["defending_pressing_tackling_duels_draft.json", "football_level_teaching_draft.json"],
    "match_iq_tactics": ["team_tactics_formations_match_iq_draft.json", "football_level_teaching_draft.json"],
    "team_tactics": ["team_tactics_formations_match_iq_draft.json", "football_level_teaching_draft.json"],
    "match_iq": ["team_tactics_formations_match_iq_draft.json", "football_level_teaching_draft.json"],
    "goalkeeping": ["goalkeeping_draft.json", "football_level_teaching_draft.json"],
    "football_strength_conditioning": ["football_snc_injury_macro_planning_draft.json", "football_level_teaching_draft.json"],
    "football_snc": ["football_snc_injury_macro_planning_draft.json", "football_level_teaching_draft.json"],
}

ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "goalkeeper": ["keeper", "gk", "all_roles"],
    "keeper": ["goalkeeper", "gk", "all_roles"],
    "gk": ["goalkeeper", "keeper", "all_roles"],
    "center_back": ["centre_back", "central_defender", "defender", "all_roles"],
    "centre_back": ["center_back", "central_defender", "defender", "all_roles"],
    "fullback_wingback": ["fullback", "wingback", "wide_defender", "all_roles"],
    "fullback": ["fullback_wingback", "wingback", "wide_defender", "all_roles"],
    "wingback": ["fullback_wingback", "fullback", "wide_defender", "all_roles"],
    "defensive_midfielder": ["number_6", "holding_midfielder", "midfielder", "all_roles"],
    "central_midfielder": ["number_8", "box_to_box_midfielder", "midfielder", "all_roles"],
    "attacking_midfielder": ["number_10", "playmaker", "midfielder", "all_roles"],
    "winger_wide_forward": ["winger", "wide_forward", "wide_attacker", "all_roles"],
    "winger": ["winger_wide_forward", "wide_forward", "wide_attacker", "all_roles"],
    "wide_forward": ["winger_wide_forward", "winger", "wide_attacker", "all_roles"],
    "striker_center_forward": ["striker", "center_forward", "centre_forward", "forward", "all_roles"],
    "striker": ["striker_center_forward", "center_forward", "centre_forward", "forward", "all_roles"],
    "center_forward": ["striker_center_forward", "striker", "centre_forward", "forward", "all_roles"],
    "centre_forward": ["striker_center_forward", "striker", "center_forward", "forward", "all_roles"],
}

DOMAIN_PHYSICAL_SUPPORT: Dict[str, List[str]] = {
    "ball_mastery": ["ankle control", "hip control", "single-leg balance", "deceleration control"],
    "first_touch_receiving": ["scanning under fatigue", "hip orientation", "trunk control", "ankle stiffness"],
    "passing": ["plant-leg stability", "hip control", "adductor capacity", "decision quality under fatigue"],
    "dribbling_1v1": ["acceleration", "deceleration", "change of direction", "ankle and groin durability"],
    "shooting_finishing": ["single-leg plant strength", "hip flexor and adductor capacity", "trunk rotation", "hamstring resilience"],
    "crossing_chance_creation": ["wide acceleration", "plant-leg control", "hip mobility", "crossing volume tolerance"],
    "defending_pressing": ["deceleration", "lateral movement", "repeated sprint ability", "adductor and hamstring resilience"],
    "match_iq_tactics": ["aerobic base", "repeated sprint ability", "decision quality under fatigue", "communication"],
    "team_tactics": ["aerobic base", "repeated sprint ability", "decision quality under fatigue", "communication"],
    "match_iq": ["aerobic base", "repeated sprint ability", "decision quality under fatigue", "communication"],
    "goalkeeping": ["diving and landing capacity", "explosive lateral power", "shoulder and wrist tolerance", "hip mobility"],
    "football_strength_conditioning": ["acceleration", "max velocity exposure", "deceleration", "hamstring, adductor, calf capacity"],
    "football_snc": ["acceleration", "max velocity exposure", "deceleration", "hamstring, adductor, calf capacity"],
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
        items: List[str] = []
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
            if not isinstance(ref, dict) or not ref.get("title"):
                continue
            refs.append({
                "source_pack_id": SOURCE_PACK_ID,
                "draft_file": file_name,
                "source_id": ref.get("source_id") or ref.get("id"),
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
                "_collection": str(record_type or "football_research_record"),
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
    return str(
        record.get("record_id")
        or record.get("canonical_id")
        or record.get("candidate_id")
        or record.get("candidate_slug")
        or record.get("id")
        or _slug(record.get("name") or record.get("title") or record.get("_collection"))
    )


def _record_title(record: Dict[str, Any]) -> str:
    return str(record.get("name") or record.get("title") or record.get("display_name") or _record_id(record).replace("_", " ").title())


def _level_doc_to_progression(record: Dict[str, Any], level: str, level_doc: Dict[str, Any]) -> Dict[str, Any]:
    domain = _slug(record.get("domain"))
    role_specific_progression = level_doc.get("role_specific_progression") or level_doc.get("position_specific_progression") or {}
    role_keys = list(role_specific_progression.keys()) if isinstance(role_specific_progression, dict) else []
    role_tags = _expanded_role_tags(role_keys)
    learning_goal = (
        level_doc.get("learning_goal")
        or f"Develop {domain.replace('_', ' ')} from {level} soccer standards with safe progressions and clear assessment gates."
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
        *_strings(list(role_specific_progression.keys()) if isinstance(role_specific_progression, dict) else []),
    ])[:8]
    typical_drills = level_doc.get("typical_drills") or []
    return {
        "id": f"soccer_teach_{domain}_{level}",
        "sport": SPORT,
        "domain": domain,
        "level": level,
        "role_tags": role_tags,
        "learning_goal": learning_goal,
        "suitable_for": [f"{level} soccer players", "football/soccer training"],
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
            "soccer",
            "football",
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
        "id": f"soccer_assess_{domain}",
        "sport": SPORT,
        "domain": domain,
        "summary": f"Assesses soccer {domain.replace('_', ' ')} level using technical quality, tactical transfer, pressure tolerance, and safety signals.",
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
        "retrieval_tags": sorted(set(["soccer", "football", domain, "assessment", *_strings(record.get("metrics"))])),
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
        "id": record_id if record_id.startswith("soccer_") else f"soccer_level_{record_id}",
        "sport": SPORT,
        "from_level": _slug(record.get("from_level") or "any"),
        "to_level": _slug(record.get("to_level") or "hold_or_conservative_progression"),
        "applies_to": applies_to,
        "minimum_evidence": required_evidence,
        "promote_when": required_evidence,
        "hold_when": hold_when,
        "backend_action": record.get("backend_action"),
        "retrieval_tags": sorted(set(["soccer", "football", *applies_to, *_strings(required_evidence), *_strings(hold_when)])),
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain("football_snc"),
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
        if record.get("_collection") == "football_role_profile"
    ]
    docs: List[Dict[str, Any]] = []
    for record in role_records:
        role = _slug(record.get("role") or _record_id(record).replace("role_profile_", ""))
        responsibilities = record.get("responsibilities") or {}
        docs.append({
            "id": f"soccer_role_{role}",
            "sport": SPORT,
            "role": role,
            "display_name": record.get("display_name") or role.replace("_", " ").title(),
            "summary": record.get("role_summary"),
            "responsibilities": responsibilities,
            "skill_priorities": _strings(responsibilities)[:18],
            "physical_demands": _role_physical_demands(role, records),
            "retrieval_tags": _expanded_role_tags(role),
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs_for_domain("positions_roles_demands"),
        })
    return docs


def _role_physical_demands(role: str, records: Sequence[Dict[str, Any]]) -> List[str]:
    role_demand_records = [
        record
        for record in records
        if record.get("_collection") == "football_role_physical_demand" and _slug(record.get("role")) == role
    ]
    demands = _dedupe([
        *_strings([record.get("summary") or record.get("name") for record in role_demand_records]),
        *DOMAIN_PHYSICAL_SUPPORT.get("football_snc", []),
    ])
    return demands[:12]


def _payload(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = record.get("payload_fields") or record.get("payload") or record.get("fields") or record.get("suggested_schema") or record
    return payload if isinstance(payload, dict) else {"text": payload}


def _payload_summary(record: Dict[str, Any]) -> str:
    payload = _payload(record)
    parts: List[str] = []
    for key in (
        "name",
        "description",
        "summary",
        "selection_rule",
        "progression_rule",
        "backend_note",
        "rule",
        "condition",
        "trigger_conditions",
        "recommended_adjustment",
        "match_week_rule",
        "training_implication",
    ):
        if payload.get(key):
            parts.extend(_strings(payload[key]))
    if not parts:
        for key, value in payload.items():
            if str(key).startswith("_"):
                continue
            values = _strings(value)
            if values:
                parts.append(f"{key}: {', '.join(values[:5])}")
    return " ".join(parts)[:900]


def _recommended_actions(record: Dict[str, Any]) -> List[str]:
    payload = _payload(record)
    for key in ("then", "recommended_action", "recommended_actions", "recommended_focus", "primary_priorities", "coaching_actions", "corrections", "outputs"):
        if payload.get(key):
            return _strings(payload[key])[:12]
    for key in ("recommended_adjustment", "match_week_rule", "position_notes", "level_implications"):
        if record.get(key):
            return _strings(record[key])[:12]
    return _strings(record.get("training_implications"))[:12]


def _blocked_actions(record: Dict[str, Any]) -> List[str]:
    payload = _payload(record)
    for key in ("avoid", "do_not", "blocked_actions", "contraindications", "do_not_progress_if", "watch_outs"):
        if payload.get(key):
            return _strings(payload[key])[:12]
    for key in ("hard_stop_conditions", "do_not_progress_if", "contraindications", "watch_outs"):
        if record.get(key):
            return _strings(record[key])[:12]
    return []


def _sport_training_rules(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    excluded = {
        "sport_teaching_progressions",
        "sport_skill_assessments",
        "sport_level_transition_rules",
        "football_role_profile",
    }
    for record in records:
        collection = str(record.get("_collection") or "")
        if collection in excluded:
            continue
        record_id = _record_id(record)
        docs.append({
            "id": f"soccer_training_rule_{collection}_{record_id}",
            "sport": SPORT,
            "category": collection,
            "condition": _payload_summary(record)[:240],
            "rule": _payload_summary(record),
            "recommended_action": _recommended_actions(record),
            "blocked_action": _blocked_actions(record),
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs_for_files([record.get("_draft_file")], limit=8),
            "retrieval_tags": sorted(set(["soccer", "football", collection, record_id, *_strings(record)]))[:90],
        })
    return docs


def _planning_rules(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    allowed = {
        "football_injury_risk_rule",
        "football_macro_planning_rule",
        "football_return_to_play_rule",
        "football_readiness_adjustment_rule",
        "football_finishing_load_rule",
    }
    for record in records:
        collection = str(record.get("_collection") or "")
        if collection not in allowed:
            continue
        record_id = _record_id(record)
        docs.append({
            "id": f"soccer_plan_{record_id}",
            "sport": SPORT,
            "category": collection,
            "applies_to": ["soccer", "football"],
            "priority": 75 if collection == "football_macro_planning_rule" else 90,
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
        "id": "sport_profile_soccer",
        "sport": SPORT,
        "aliases": ["football"],
        "planning_summary": "Football/soccer is an intermittent field sport combining repeated accelerations, high-speed running, deceleration, change of direction, duels, technical skill, tactical decision-making, and match-week fatigue management.",
        "training_priorities": [
            "acceleration and first-step quality",
            "max velocity exposure when healthy",
            "deceleration and change-of-direction mechanics",
            "unilateral lower-body strength",
            "hamstring, adductor, calf, ankle durability",
            "aerobic base and repeated sprint ability",
            "technical skill under pressure",
            "position-specific tactical decision-making",
            "match-week load management",
        ],
        "key_physical_qualities": _dedupe([
            "acceleration",
            "max velocity",
            "deceleration",
            "change of direction",
            "repeated sprint ability",
            "aerobic base",
            "unilateral strength",
            "hamstring resilience",
            "adductor and groin durability",
            "calf and ankle capacity",
            *demand_names,
        ])[:24],
        "realistic_weekly_frequency": {
            "beginner": {"gym_sessions": "2-3", "field_sessions": "1-3", "high_speed_exposure": "low and technique-led"},
            "intermediate": {"gym_sessions": "2-4", "field_sessions": "2-4", "high_speed_exposure": "weekly if healthy"},
            "advanced": {"gym_sessions": "2-4", "field_sessions": "3-6", "high_speed_exposure": "individualized by role and match load"},
        },
        "common_injury_or_load_risks": _dedupe([
            "hamstring strain",
            "adductor/groin pain",
            "ankle sprain",
            "knee ligament risk",
            "calf/Achilles overload",
            "hip flexor overload",
            "concussion/head contact",
            *risk_names,
        ])[:24],
        "do_not_pair": [
            "large novel sprint volume with heavy lower-body eccentric work in the same fatigue-limited window",
            "high-volume change-of-direction with groin/adductor symptoms",
            "heavy lower-body soreness work within 24 hours of important matches",
            "heading/contact progression when concussion symptoms or head injury suspicion exists",
            "new maximal sprint exposure late in a congested match week",
        ],
        "progression_guardrails": [
            "build running tolerance before repeated sprint or high-speed volume",
            "progress speed, COD, and gym eccentric load separately when symptoms or fatigue are present",
            "use role demands to bias technical and physical work without eliminating broad football skill exposure",
            "reduce novelty and soreness near match day",
            "use pain, readiness, and completion trends before increasing high-speed or COD exposure",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules[:16]],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain("football_snc"),
    }


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    for index, path in enumerate(sorted(DRAFT_DIR.glob("*_draft.json")), start=70001):
        draft = _load_draft(path.name)
        metadata = draft.get("metadata") or {}
        docs.append({
            "id": f"football_teaching_section_{_slug(metadata.get('domain') or path.stem)}",
            "source_book_id": SOURCE_PACK_ID,
            "section_order": index,
            "section_title": f"Football {str(metadata.get('domain') or path.stem).replace('_', ' ').title()}",
            "domain": "football_teaching",
            "topics": ["soccer", "football", _slug(metadata.get("domain") or path.stem), "teaching_progression"],
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
            "title": "SFTC Football/Soccer Teaching And Planning Database",
            "sport": SPORT,
            "aliases": ["football"],
            "version": "v1.0.0",
            "description": "App-facing football/soccer teaching, role, tactical, S&C, injury, macro-planning, and retrieval records derived from structured football research drafts.",
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
        "sport": SPORT,
        "aliases": ["football"],
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
    parser = argparse.ArgumentParser(description="Build and ingest football/soccer app-facing teaching database.")
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

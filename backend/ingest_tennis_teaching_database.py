from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TENNIS_DIR = PROJECT_ROOT / "backend" / "sport_research" / "tennis"
OUTPUT_PATH = TENNIS_DIR / "tennis_teaching_database.json"
DRAFT_DIR = TENNIS_DIR / "drafts"

SOURCE_PACK_ID = "tennis_teaching_database_v1"
INGESTION_METHOD = "tennis_research_structured_converter_v1"
SPORT = "tennis"
LEVELS = ["beginner", "intermediate", "advanced"]

SOURCE_REFS: List[Dict[str, Any]] = [
    {
        "title": "ITF Tennis Play and Stay",
        "url": "https://www.itftennis.com/en/growing-the-game/participation/play-and-stay/",
        "source_type": "official_coaching_education",
        "organization_or_author": "International Tennis Federation",
        "notes": "Used for starter development, scaled courts, rally-first teaching, and progression into full tennis.",
    },
    {
        "title": "USTA Player Development Teaching and Coaching Resources",
        "url": "https://www.usta.com/en/home/coach-organize/coach-resources.html",
        "source_type": "official_coaching_education",
        "organization_or_author": "United States Tennis Association",
        "notes": "Used for player development, coaching language, tactical learning, and athlete pathway context.",
    },
    {
        "title": "ITF Biomechanics of Advanced Tennis",
        "url": "https://www.itftennis.com/en/news-and-media/articles/biomechanics-of-advanced-tennis/",
        "source_type": "official_sport_science",
        "organization_or_author": "International Tennis Federation",
        "notes": "Used for serve, groundstroke, kinetic-chain, and stroke-mechanics principles.",
    },
    {
        "title": "Tennis Injuries: Epidemiology, Pathophysiology, and Treatment",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4547115/",
        "source_type": "peer_reviewed_review",
        "organization_or_author": "Sports medicine review authors",
        "notes": "Used for common tennis injury locations, load risks, and return-to-play context.",
    },
    {
        "title": "Physiological Demands and Activity Patterns of Tennis Match Play",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3761832/",
        "source_type": "peer_reviewed_review",
        "organization_or_author": "Sport science review authors",
        "notes": "Used for rally demands, repeated sprint/change-of-direction load, and conditioning implications.",
    },
    {
        "title": "Tennis Medicine: Injury Prevention and Load Management",
        "url": "https://www.aspetar.com/journal/viewarticle.aspx?id=394",
        "source_type": "sports_medicine_education",
        "organization_or_author": "Aspetar Sports Medicine Journal",
        "notes": "Used for shoulder, elbow, trunk, lower-limb, and workload management principles.",
    },
    {
        "title": "ITF Rules of Tennis",
        "url": "https://www.itftennis.com/en/about-us/governance/rules-and-regulations/",
        "source_type": "official_rules",
        "organization_or_author": "International Tennis Federation",
        "notes": "Used for scoring, singles/doubles format, court/surface context, and match structure.",
    },
]

DOMAINS: Dict[str, Dict[str, Any]] = {
    "rules_scoring_match_iq": {
        "summary": "Tennis match play is point-based, momentum-driven, and shaped by serve/return advantage, score pressure, surface speed, opponent tendencies, and singles or doubles format.",
        "qualities": ["score awareness", "serve return decisions", "momentum control", "opponent scouting"],
        "risk_flags": ["rushing under pressure", "low percentage decisions", "poor score-state awareness"],
    },
    "serve_return": {
        "summary": "Serve and return create the first tactical advantage; development must balance technical mechanics, placement, spin, first-strike patterns, and shoulder/elbow load.",
        "qualities": ["serve mechanics", "return positioning", "first strike", "shoulder durability", "elbow load management"],
        "risk_flags": ["serve_volume_spike", "shoulder_pain", "elbow_pain", "poor_kinetic_chain"],
    },
    "forehand_backhand": {
        "summary": "Forehand and backhand development links grip, preparation, contact spacing, swing path, recovery, spin, depth, and tactical rally intention.",
        "qualities": ["groundstroke mechanics", "rotation control", "rally tolerance", "shot depth", "spin control"],
        "risk_flags": ["late_contact", "wrist_elbow_load", "trunk_rotation_irritation"],
    },
    "volley_net_play": {
        "summary": "Volley and net play require split-step timing, compact stroke mechanics, closing patterns, touch, overhead readiness, and rapid transition decisions.",
        "qualities": ["volley technique", "net positioning", "reaction speed", "overhead readiness", "transition attack"],
        "risk_flags": ["late_split_step", "partner_collision", "shoulder_overuse"],
    },
    "footwork_recovery": {
        "summary": "Tennis movement depends on split-step timing, first step, crossover and shuffle choices, deceleration, open/neutral stance recovery, and repeat directional changes.",
        "qualities": ["split_step", "deceleration", "change_of_direction", "court_recovery", "single_leg_control"],
        "risk_flags": ["ankle_sprain", "knee_pain", "achilles_load", "hip_groin_load"],
    },
    "singles_tactics": {
        "summary": "Singles tactics combine serve-plus-one, return-plus-one, crosscourt stability, down-the-line risk control, attacking space, defending under pressure, and opponent-pattern exploitation.",
        "qualities": ["rally construction", "court geometry", "serve_plus_one", "return_plus_one", "pattern recognition"],
        "risk_flags": ["overplaying_low_percentage_shots", "poor_recovery_position", "excessive_defensive_load"],
    },
    "doubles_tactics": {
        "summary": "Doubles prioritizes serve/return pressure, net control, poaching, formations, communication, role clarity, and synchronized court coverage.",
        "qualities": ["net control", "poaching", "formation choice", "communication", "serve return pressure"],
        "risk_flags": ["partner_collision", "chaotic_rotation", "weak_first_volley_position"],
    },
    "surface_adaptation": {
        "summary": "Surface changes alter bounce, speed, sliding demands, rally length, footwork, footwear, and training load; clay, grass, hard, and indoor courts need different planning bias.",
        "qualities": ["surface tactics", "sliding or braking control", "footwear choice", "rally tolerance", "load adaptation"],
        "risk_flags": ["surface_transition_spike", "slip_or_brake_risk", "calf_achilles_load"],
    },
    "tennis_strength_conditioning": {
        "summary": "Tennis S&C should develop rotational power, deceleration, lateral reactivity, shoulder/scapular and elbow/wrist durability, trunk control, repeated-sprint capacity, and match-load tolerance.",
        "qualities": ["rotational_power", "deceleration", "lateral_movement", "shoulder_durability", "repeat_sprint_capacity"],
        "risk_flags": ["plyometric_spike", "throwing_volume_spike", "shoulder_elbow_overuse", "low_back_rotation"],
    },
    "injury_load_management": {
        "summary": "Tennis load management tracks serve volume, groundstroke volume, court surface changes, match density, shoulder/elbow/wrist symptoms, back irritation, and lower-limb response.",
        "qualities": ["pain monitoring", "match density management", "surface transition control", "return_to_court", "serve volume tracking"],
        "risk_flags": ["shoulder_pain", "elbow_pain", "wrist_pain", "low_back_pain", "ankle_knee_achilles_load"],
    },
}

ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "aggressive_baseliner": ["baseline_attacker", "power_baseliner", "all_roles"],
    "counterpuncher": ["defensive_baseliner", "retriever", "all_roles"],
    "defensive_retriever": ["counterpuncher", "retriever", "all_roles"],
    "all_court_player": ["all_round_player", "net_transition_player", "all_roles"],
    "serve_and_volley_player": ["net_rusher", "attacking_net_player", "all_roles"],
    "big_server": ["serve_dominant_player", "first_strike_player", "all_roles"],
    "doubles_net_player": ["net_player", "poacher", "doubles", "all_roles"],
    "doubles_baseline_player": ["returner", "doubles", "all_roles"],
    "singles": ["single", "all_roles"],
    "single": ["singles", "all_roles"],
    "doubles": ["double", "doubles_net_player", "doubles_baseline_player", "all_roles"],
    "double": ["doubles", "doubles_net_player", "doubles_baseline_player", "all_roles"],
    "one_handed_backhand": ["single_handed_backhand", "backhand_player", "all_roles"],
    "two_handed_backhand": ["double_handed_backhand", "backhand_player", "all_roles"],
    "left_handed_player": ["lefty", "southpaw_tennis", "all_roles"],
}

ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "aggressive_baseliner": ["forehand_backhand", "singles_tactics", "serve_return", "footwork_recovery", "tennis_strength_conditioning"],
    "counterpuncher": ["forehand_backhand", "singles_tactics", "footwork_recovery", "surface_adaptation", "injury_load_management"],
    "defensive_retriever": ["forehand_backhand", "singles_tactics", "footwork_recovery", "surface_adaptation"],
    "all_court_player": ["forehand_backhand", "volley_net_play", "singles_tactics", "serve_return", "footwork_recovery"],
    "serve_and_volley_player": ["serve_return", "volley_net_play", "doubles_tactics", "footwork_recovery", "tennis_strength_conditioning"],
    "big_server": ["serve_return", "tennis_strength_conditioning", "injury_load_management", "singles_tactics"],
    "doubles_net_player": ["doubles_tactics", "volley_net_play", "serve_return", "footwork_recovery"],
    "doubles_baseline_player": ["doubles_tactics", "serve_return", "forehand_backhand", "footwork_recovery"],
    "singles": ["singles_tactics", "serve_return", "forehand_backhand", "footwork_recovery", "surface_adaptation"],
    "doubles": ["doubles_tactics", "serve_return", "volley_net_play", "footwork_recovery"],
    "one_handed_backhand": ["forehand_backhand", "surface_adaptation", "injury_load_management"],
    "two_handed_backhand": ["forehand_backhand", "singles_tactics"],
    "left_handed_player": ["serve_return", "singles_tactics", "doubles_tactics"],
}


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


def _source_refs(limit: int = 8) -> List[Dict[str, Any]]:
    return SOURCE_REFS[:limit]


def _slug(value: Any, fallback: str = "record") -> str:
    text = str(value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or fallback


def _listify(value: Any) -> List[Any]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "", [], {})]
    if isinstance(value, dict):
        return [value]
    return [value]


def _text_items(value: Any) -> List[str]:
    output: List[str] = []
    for item in _listify(value):
        if isinstance(item, dict):
            output.extend(_text_items(list(item.values())))
        else:
            text = str(item or "").strip()
            if text:
                output.append(text)
    return output


def _short(value: Any, max_chars: int = 700) -> str:
    if isinstance(value, dict):
        text = "; ".join(_text_items(value))
    elif isinstance(value, list):
        text = "; ".join(_text_items(value))
    else:
        text = str(value or "").strip()
    return text[:max_chars]


def _title_from_item(item: Mapping[str, Any], fallback: str) -> str:
    for key in ("name", "title", "concept", "model", "quality", "risk", "rule", "id", "record_id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:140]
    return fallback


def _summary_from_item(item: Mapping[str, Any]) -> str:
    for key in (
        "summary",
        "details",
        "description",
        "rule",
        "recommendation",
        "rationale",
        "why_it_matters",
        "mechanics",
        "model",
        "concept",
        "risk",
        "quality",
        "record_purpose",
    ):
        text = _short(item.get(key))
        if text:
            return text
    return _short(item)


def _collect_source_ids(value: Any) -> List[str]:
    source_ids: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"source_ids", "source_ref_ids", "source_refs"}:
                source_ids.extend(str(item) for item in _listify(child) if not isinstance(item, dict))
            else:
                source_ids.extend(_collect_source_ids(child))
    elif isinstance(value, list):
        for child in value:
            source_ids.extend(_collect_source_ids(child))
    return _dedupe(source_ids)


def _draft_domain(draft: Dict[str, Any]) -> str:
    metadata = draft.get("metadata") or {}
    return _slug(metadata.get("domain") or "tennis_deep_research")


def _draft_summary(draft: Dict[str, Any]) -> str:
    metadata = draft.get("metadata") or {}
    return str(metadata.get("research_goal") or metadata.get("scope") or _draft_domain(draft).replace("_", " ")).strip()


def _draft_ref_map(draft: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    refs: Dict[str, Dict[str, Any]] = {}
    for ref in draft.get("source_refs") or []:
        if not isinstance(ref, dict):
            continue
        ref_id = str(ref.get("id") or ref.get("title") or "").strip()
        if not ref_id:
            continue
        refs[ref_id] = {
            "source_book_id": SOURCE_PACK_ID,
            "section_id": f"tennis_source_{_slug(ref_id)}",
            "section_title": ref.get("title"),
            "heading": ref.get("source_type"),
            "url": ref.get("url"),
            "organization_or_author": ref.get("organization_or_author"),
        }
    return refs


def _refs_for_item(draft: Dict[str, Any], item: Mapping[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    ref_map = _draft_ref_map(draft)
    refs = [ref_map[source_id] for source_id in _collect_source_ids(item) if source_id in ref_map]
    if refs:
        return refs[:limit]
    domain = _draft_domain(draft)
    return [
        {
            "source_book_id": SOURCE_PACK_ID,
            "section_id": f"tennis_section_{domain}",
            "section_title": domain.replace("_", " ").title(),
            "heading": "tennis_deep_research",
        }
    ]


def _load_deep_drafts() -> List[Dict[str, Any]]:
    drafts: List[Dict[str, Any]] = []
    if not DRAFT_DIR.exists():
        return drafts
    for path in sorted(DRAFT_DIR.glob("*_draft.json")):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and (data.get("metadata") or {}).get("sport") == SPORT:
            data["_draft_path"] = str(path.relative_to(PROJECT_ROOT))
            drafts.append(data)
    return drafts


def _draft_role_tags(domain: str, item: Mapping[str, Any]) -> List[str]:
    text = " ".join(_text_items([domain, item])).lower()
    roles = ["all_roles"]
    if "double" in text or "poach" in text or "i formation" in text or "australian" in text or "partner" in text:
        roles.extend(["doubles", "doubles_net_player"])
    if "serve" in text:
        roles.extend(["big_server", "serve_and_volley_player"])
    if "baseline" in text or "forehand" in text or "backhand" in text or "rally" in text:
        roles.extend(["aggressive_baseliner", "counterpuncher", "all_court_player"])
    if "slice" in text or "volley" in text or "net" in text or "approach" in text:
        roles.extend(["all_court_player", "serve_and_volley_player"])
    if "retrieve" in text or "defensive" in text:
        roles.extend(["counterpuncher", "defensive_retriever"])
    return _dedupe(roles)


def _draft_tags(domain: str, field: str, item: Mapping[str, Any]) -> List[str]:
    return sorted(
        set(
            [
                SPORT,
                domain,
                field,
                *_draft_role_tags(domain, item),
                *_slug(_title_from_item(item, field)).split("_"),
                *_slug(_summary_from_item(item)).split("_")[:18],
                *_text_items(item.get("backend_tags")),
                *_text_items(item.get("applies_to")),
                *_text_items(item.get("levels")),
                *_text_items(item.get("level")),
            ]
        )
    )


def _deep_source_sections(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs: List[Dict[str, Any]] = []
    for index, draft in enumerate(drafts, start=160000):
        domain = _draft_domain(draft)
        field_counts = {
            key: len(draft.get(key) or [])
            for key in [
                "key_concepts",
                "technical_models",
                "tactical_rules",
                "physical_demands",
                "injury_or_load_risks",
                "training_implications",
                "backend_records_to_create",
            ]
        }
        docs.append(
            {
                "id": f"tennis_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe([SPORT, domain, *field_counts.keys()]),
                "summary": _draft_summary(draft),
                "field_counts": field_counts,
                "draft_path": draft.get("_draft_path"),
                "source_refs": [
                    {
                        "source_book_id": SOURCE_PACK_ID,
                        "section_id": f"tennis_source_{_slug(ref.get('id') or ref.get('title'))}",
                        "section_title": ref.get("title"),
                        "heading": ref.get("source_type"),
                        "url": ref.get("url"),
                    }
                    for ref in (draft.get("source_refs") or [])[:12]
                    if isinstance(ref, dict)
                ],
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _deep_sport_training_rules(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fields = [
        "key_concepts",
        "technical_models",
        "tactical_rules",
        "physical_demands",
        "injury_or_load_risks",
        "training_implications",
    ]
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        for field in fields:
            for index, item in enumerate(draft.get(field) or [], start=1):
                if not isinstance(item, dict):
                    continue
                title = _title_from_item(item, f"{domain} {field} {index}")
                docs.append(
                    {
                        "id": f"tennis_deep_rule_{domain}_{field}_{_slug(item.get('id') or item.get('record_id') or title)}",
                        "sport": SPORT,
                        "domain": domain,
                        "category": field.rstrip("s"),
                        "title": title,
                        "condition": _short(item.get("condition") or item.get("risk_context") or item.get("mechanism"), 360),
                        "rule": _summary_from_item(item),
                        "summary": _summary_from_item(item),
                        "recommended_action": _dedupe(
                            _text_items(
                                [
                                    item.get("backend_action"),
                                    item.get("training_notes"),
                                    item.get("preferred_training"),
                                    item.get("prevention_or_management"),
                                    item.get("mitigation"),
                                    item.get("teaching_points"),
                                    item.get("teaching_progression"),
                                ]
                            )
                        )[:12],
                        "blocked_action": _dedupe(
                            _text_items(
                                [
                                    item.get("avoid"),
                                    item.get("avoid_until_ready"),
                                    item.get("common_errors"),
                                    item.get("warning_signs"),
                                    item.get("monitoring_flags"),
                                ]
                            )
                        )[:12],
                        "coaching_cues": _dedupe(_text_items(item.get("coaching_cues")))[:10],
                        "common_errors": _dedupe(_text_items(item.get("common_errors")))[:10],
                        "applies_to": _draft_role_tags(domain, item),
                        "level": item.get("level") if isinstance(item.get("level"), str) else None,
                        "detail": item,
                        "retrieval_tags": _draft_tags(domain, field, item),
                        "source_pack_id": SOURCE_PACK_ID,
                        "source_refs": _refs_for_item(draft, item),
                    }
                )
    return docs


def _deep_planning_rules(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        for field in ("tactical_rules", "injury_or_load_risks", "training_implications"):
            for item in draft.get(field) or []:
                if not isinstance(item, dict):
                    continue
                title = _title_from_item(item, f"{domain} planning")
                category = str(item.get("category") or item.get("rule_category") or field).strip() or field
                docs.append(
                    {
                        "id": f"tennis_deep_plan_{domain}_{field}_{_slug(item.get('id') or title)}",
                        "sport": SPORT,
                        "applies_to": _draft_role_tags(domain, item),
                        "category": category,
                        "title": title,
                        "rule": _summary_from_item(item),
                        "rule_text": _summary_from_item(item),
                        "recommended_action": _dedupe(
                            _text_items(
                                [
                                    item.get("backend_action"),
                                    item.get("recommended_action"),
                                    item.get("preferred_training"),
                                    item.get("progression"),
                                    item.get("quality_gates"),
                                ]
                            )
                        )[:10],
                        "blocked_action": _dedupe(
                            _text_items(
                                [
                                    item.get("avoid"),
                                    item.get("load_controls"),
                                    item.get("monitoring_flags"),
                                    item.get("warning_signs"),
                                ]
                            )
                        )[:10],
                        "priority": 78 if field == "tactical_rules" else 88,
                        "topics": _draft_tags(domain, field, item),
                        "source_pack_id": SOURCE_PACK_ID,
                        "source_refs": _refs_for_item(draft, item),
                    }
                )
        for item in draft.get("backend_records_to_create") or []:
            if not isinstance(item, dict):
                continue
            record_type = str(item.get("record_type") or item.get("collection") or "").lower()
            if "planning" not in record_type and "readiness" not in record_type and "injury" not in record_type:
                continue
            title = _title_from_item(item, f"{domain} backend planning")
            docs.append(
                {
                    "id": f"tennis_deep_plan_{domain}_{_slug(item.get('record_id') or item.get('id') or title)}",
                    "sport": SPORT,
                    "applies_to": _draft_role_tags(domain, item),
                    "category": record_type or "backend_planning_record",
                    "title": title,
                    "rule": _summary_from_item(item),
                    "rule_text": _summary_from_item(item),
                    "recommended_action": _dedupe(_text_items(item.get("payload_fields")))[:12],
                    "blocked_action": [],
                    "priority": 86,
                    "topics": _draft_tags(domain, "backend_records_to_create", item),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _refs_for_item(draft, item),
                }
            )
    return docs


def _deep_teaching_progressions(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        for item in draft.get("training_implications") or []:
            if not isinstance(item, dict):
                continue
            level = str(item.get("level") or "intermediate").lower()
            if level not in LEVELS:
                level = "intermediate"
            title = _title_from_item(item, f"{domain} {level} teaching")
            docs.append(
                {
                    "id": f"tennis_deep_teach_{domain}_{level}_{_slug(item.get('id') or title)}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _draft_role_tags(domain, item),
                    "learning_goal": _summary_from_item(item),
                    "suitable_for": [f"{level} tennis players", "tennis sport skill training"],
                    "prerequisites": _dedupe(_text_items(item.get("prerequisites")))[:8] or _prerequisites("footwork_recovery", level),
                    "teaching_priorities": _dedupe(_text_items([item.get("preferred_training"), item.get("summary"), item.get("recommendation")]))[:8],
                    "technical_focus": _dedupe(_text_items([item.get("progression"), item.get("quality_gates"), item.get("implementation_notes")]))[:8],
                    "tactical_focus": _dedupe(_text_items([item.get("implementation_examples"), item.get("backend_use")]))[:6],
                    "physical_support": _dedupe(_text_items([item.get("training_methods"), item.get("preferred_training")]))[:8],
                    "practice_design": _dedupe(_text_items([item.get("progression"), item.get("practice_design"), item.get("implementation_examples")]))[:8],
                    "typical_drills": _dedupe(_text_items([item.get("progression"), item.get("preferred_training")]))[:8],
                    "avoid_until_ready": _dedupe(_text_items(item.get("avoid")))[:8],
                    "progression_signals": _dedupe(_text_items(item.get("quality_gates") or item.get("assessment_signals")))[:8]
                    or _progression_signals("footwork_recovery", level),
                    "coach_notes": _dedupe(_text_items([item.get("source_ids"), item.get("implementation_notes")]))[:6],
                    "retrieval_tags": _draft_tags(domain, "training_implications", item),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _refs_for_item(draft, item),
                }
            )

        for model in draft.get("technical_models") or []:
            if not isinstance(model, dict) or not isinstance(model.get("teaching_progression"), dict):
                continue
            model_title = _title_from_item(model, domain)
            for level, steps in model["teaching_progression"].items():
                level_key = str(level).lower()
                if level_key not in LEVELS:
                    continue
                docs.append(
                    {
                        "id": f"tennis_deep_teach_{domain}_{level_key}_{_slug(model.get('id') or model_title)}",
                        "sport": SPORT,
                        "domain": domain,
                        "level": level_key,
                        "role_tags": _draft_role_tags(domain, model),
                        "learning_goal": f"Develop {model_title} for a {level_key} tennis player.",
                        "suitable_for": [f"{level_key} tennis players"],
                        "prerequisites": _prerequisites("forehand_backhand", level_key),
                        "teaching_priorities": _dedupe(_text_items([model.get("mechanics"), model.get("racket_preparation")]))[:8],
                        "technical_focus": _dedupe(_text_items([model.get("coaching_cues"), model.get("teaching_points")]))[:8],
                        "tactical_focus": _dedupe(_text_items([model.get("tactical_use"), model.get("shot_selection")]))[:6],
                        "physical_support": _dedupe(_text_items([model.get("physical_demands"), model.get("load_notes")]))[:6],
                        "practice_design": _dedupe(_text_items(steps))[:8],
                        "typical_drills": _dedupe(_text_items(steps))[:8],
                        "avoid_until_ready": _dedupe(_text_items(model.get("common_errors")))[:8],
                        "progression_signals": _dedupe(_text_items(model.get("quality_markers")))[:8]
                        or _progression_signals("forehand_backhand", level_key),
                        "coach_notes": _dedupe(_text_items(model.get("coaching_cues")))[:6],
                        "retrieval_tags": _draft_tags(domain, "technical_models", model),
                        "source_pack_id": SOURCE_PACK_ID,
                        "source_refs": _refs_for_item(draft, model),
                    }
                )
    return docs


def _deep_skill_assessments(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        technical_items = [item for item in draft.get("technical_models") or [] if isinstance(item, dict)]
        demand_items = [item for item in draft.get("physical_demands") or [] if isinstance(item, dict)]
        risk_items = [item for item in draft.get("injury_or_load_risks") or [] if isinstance(item, dict)]
        metrics = _dedupe(
            _text_items(
                [
                    [item.get("quality_markers") for item in technical_items],
                    [item.get("monitoring") for item in demand_items],
                    [item.get("monitoring_flags") for item in risk_items],
                    [item.get("warning_signs") for item in risk_items],
                ]
            )
        )[:14]
        docs.append(
            {
                "id": f"tennis_deep_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _draft_role_tags(domain, {"domain": domain}),
                "summary": f"Assesses {domain.replace('_', ' ')} using technical quality, tactical transfer, physical demand tolerance, and 24-hour symptom response.",
                "metrics": metrics or _assessment_metrics("footwork_recovery"),
                "level_bands": [
                    {
                        "level": "beginner",
                        "indicators": ["can perform the skill slowly with control", "understands the basic tactical purpose"],
                        "ready_for_next_when": ["control holds under light feed pressure", "no worsening 24-hour pain response"],
                    },
                    {
                        "level": "intermediate",
                        "indicators": ["links the skill to opponent, score, surface, or partner context", "quality survives moderate fatigue"],
                        "ready_for_next_when": ["quality remains stable under constraints", "load channels are tolerated"],
                    },
                    {
                        "level": "advanced",
                        "indicators": ["adapts to opponent and match state", "manages surface, tournament, or dense match exposure"],
                        "ready_for_next_when": ["competition transfer and recovery are reliable"],
                    },
                ],
                "hold_if": _dedupe(
                    _text_items(
                        [
                            [item.get("warning_signs") for item in risk_items],
                            [item.get("avoid") for item in draft.get("training_implications") or [] if isinstance(item, dict)],
                        ]
                    )
                )[:10],
                "retrieval_tags": _draft_tags(domain, "skill_assessment", {"metrics": metrics}),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _refs_for_item(draft, {"source_ids": _dedupe(_collect_source_ids(draft))[:8]}),
            }
        )
    return docs


def _sport_roles() -> List[Dict[str, Any]]:
    roles = {
        "aggressive_baseliner": {
            "display_name": "Aggressive Baseliner",
            "summary": "Uses heavy groundstrokes, first-strike patterns, and court positioning to control rallies from the baseline.",
            "skill_priorities": ["forehand/backhand depth", "serve plus one", "return plus one", "inside-out patterns", "controlled aggression"],
            "physical_demands": ["rotational power", "repeat lateral movement", "deceleration", "trunk stiffness"],
        },
        "counterpuncher": {
            "display_name": "Counterpuncher",
            "summary": "Absorbs pressure, extends rallies, changes direction selectively, and wins with consistency and opponent errors.",
            "skill_priorities": ["rally tolerance", "defensive neutralization", "depth control", "recovery position", "shot tolerance"],
            "physical_demands": ["aerobic support", "repeat change of direction", "hip/calf capacity", "back durability"],
        },
        "all_court_player": {
            "display_name": "All-Court Player",
            "summary": "Combines baseline stability, approach patterns, volley skill, serve/return pressure, and tactical adaptation.",
            "skill_priorities": ["transition attack", "volley quality", "serve/return patterns", "groundstroke variety", "court awareness"],
            "physical_demands": ["multi-direction speed", "reaction speed", "shoulder/scapular durability", "rotational power"],
        },
        "serve_and_volley_player": {
            "display_name": "Serve-And-Volley Player",
            "summary": "Uses serve placement, first volley positioning, net pressure, and closing speed to shorten points.",
            "skill_priorities": ["serve location", "split-step timing", "first volley", "overhead", "net positioning"],
            "physical_demands": ["acceleration", "reaction speed", "shoulder/elbow capacity", "low volley strength"],
        },
        "big_server": {
            "display_name": "Big Server",
            "summary": "Creates advantage through serve quality, first-ball pressure, and careful shoulder/elbow load management.",
            "skill_priorities": ["serve mechanics", "serve placement", "serve plus one", "second serve reliability", "return games"],
            "physical_demands": ["rotational power", "shoulder/scapular endurance", "trunk control", "landing/braking control"],
        },
        "doubles_net_player": {
            "display_name": "Doubles Net Player",
            "summary": "Controls the net through positioning, poaching, reflex volleys, formations, and communication.",
            "skill_priorities": ["poaching", "volley reactions", "I-formation/Australian cues", "communication", "overhead readiness"],
            "physical_demands": ["reaction speed", "short acceleration", "shoulder endurance", "partner spacing awareness"],
        },
        "doubles_baseline_player": {
            "display_name": "Doubles Baseline Player",
            "summary": "Supports doubles structure with return quality, lob/drive choices, crosscourt stability, and setup for the net partner.",
            "skill_priorities": ["return placement", "crosscourt control", "lob/drive decisions", "partner setup", "defensive reset"],
            "physical_demands": ["lateral movement", "repeat split-step", "rotational control", "court coverage"],
        },
    }
    docs: List[Dict[str, Any]] = []
    for role, data in roles.items():
        docs.append(
            {
                "id": f"tennis_role_{role}",
                "sport": SPORT,
                "role": role,
                "display_name": data["display_name"],
                "aliases": ROLE_EQUIVALENTS.get(role, []),
                "summary": data["summary"],
                "responsibilities": {"domains": ROLE_DOMAIN_TAGS.get(role, []), "format": role},
                "skill_priorities": data["skill_priorities"],
                "physical_demands": data["physical_demands"],
                "risk_flags": _role_risks(role),
                "retrieval_tags": sorted(set([SPORT, role, *ROLE_EQUIVALENTS.get(role, []), *ROLE_DOMAIN_TAGS.get(role, [])])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _role_risks(role: str) -> List[str]:
    if role in {"big_server", "serve_and_volley_player"}:
        return ["shoulder_pain", "elbow_pain", "serve_volume_spike", "low_back_rotation"]
    if role in {"doubles_net_player", "doubles_baseline_player"}:
        return ["partner_collision", "reaction_overload", "shoulder_overuse"]
    if role == "counterpuncher":
        return ["knee_pain", "ankle_sprain", "calf_achilles_load", "low_back_pain"]
    return ["shoulder_elbow_overuse", "ankle_knee_achilles_load", "low_back_rotation"]


def _sport_training_rules() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        docs.append(
            {
                "id": f"tennis_training_rule_{domain}",
                "sport": SPORT,
                "domain": domain,
                "category": "tennis_domain_rule",
                "condition": data["summary"][:240],
                "rule": data["summary"],
                "recommended_action": data["qualities"],
                "blocked_action": data["risk_flags"],
                "retrieval_tags": sorted(set([SPORT, domain, *data["qualities"], *data["risk_flags"]])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _planning_rules() -> List[Dict[str, Any]]:
    rules = [
        {
            "id": "tennis_plan_rally_foundation_before_power",
            "category": "progression",
            "rule": "Build contact quality, rally tolerance, split-step timing, and safe deceleration before high-volume serving, max-speed points, or aggressive power patterns.",
            "recommended_action": ["prioritize rally consistency, court recovery, contact spacing, and low-pressure serve/return patterns"],
            "blocked_action": ["do not use fatigue-first point play for beginners"],
            "priority": 88,
        },
        {
            "id": "tennis_plan_serve_volume_gate",
            "category": "injury_risk",
            "rule": "Progress serve volume and speed by shoulder, elbow, back, and 24-hour symptom response; power serve work needs kinetic-chain quality and recovery.",
            "recommended_action": ["track weekly serve volume", "include scapular, rotator cuff, trunk, hip, and landing support"],
            "blocked_action": ["avoid serve-volume spikes with shoulder, elbow, wrist, or back symptoms"],
            "priority": 95,
        },
        {
            "id": "tennis_plan_surface_transition_gate",
            "category": "surface_adaptation",
            "rule": "Court surface changes should alter footwork, rally volume, footwear, and load because braking, sliding, bounce, and rally length change.",
            "recommended_action": ["use transition weeks and surface-specific movement drills"],
            "blocked_action": ["avoid abrupt high-volume match play after changing surfaces"],
            "priority": 89,
        },
        {
            "id": "tennis_plan_singles_vs_doubles",
            "category": "sport_specificity",
            "rule": "Singles and doubles require different tactical and physical stress: rally construction and full-court coverage for singles, serve/return/net formations and partner communication for doubles.",
            "recommended_action": ["use role-specific domains when singles/doubles style is known"],
            "blocked_action": ["do not prescribe one generic tennis plan for all formats"],
            "priority": 84,
        },
        {
            "id": "tennis_plan_tournament_density",
            "category": "competition_week",
            "rule": "During tournament or match-dense weeks, reduce new S&C soreness, high serve volume, and high-impact court conditioning while preserving rhythm, reaction, mobility, and recovery.",
            "recommended_action": ["use short activation, movement sharpness, light hitting rhythm, and recovery"],
            "blocked_action": ["avoid new plyometrics or heavy eccentric lower-body work before important matches"],
            "priority": 90,
        },
        {
            "id": "tennis_plan_return_to_court",
            "category": "return_to_sport",
            "rule": "Return to tennis should progress from shadow swings and controlled feeds to cooperative rallies, constrained points, serve exposure, and match play only when symptoms remain stable.",
            "recommended_action": ["use staged return-to-court progressions and 24-hour response checks"],
            "blocked_action": ["avoid match play or serve volume based only on pain-free rest"],
            "priority": 96,
        },
    ]
    return [
        {
            **rule,
            "sport": SPORT,
            "applies_to": [SPORT],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        }
        for rule in rules
    ]


def _sport_profile(planning_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_tennis",
        "sport": SPORT,
        "planning_summary": "Tennis is an open-skill racket sport requiring serve/return advantage, groundstroke quality, split-step timing, surface-specific movement, singles/doubles tactical intelligence, rotational power, shoulder/elbow/trunk durability, repeat change-of-direction capacity, and competition-week load management.",
        "training_priorities": [
            "serve and return mechanics with load control",
            "forehand/backhand contact spacing, depth, spin, and recovery",
            "split-step timing, first step, deceleration, and court recovery",
            "singles rally construction or doubles net/formation systems based on role",
            "surface-specific footwork and match pacing",
            "shoulder/scapular, elbow/wrist, trunk, calf/Achilles, knee, and hip durability",
            "rotational power and repeat high-intensity effort capacity",
            "tournament-week fatigue and serve-volume management",
        ],
        "key_physical_qualities": [
            "split-step reactivity",
            "lateral acceleration",
            "deceleration",
            "rotational power",
            "shoulder and scapular endurance",
            "elbow/wrist capacity",
            "trunk rotation control",
            "calf/Achilles capacity",
            "repeat sprint ability",
            "surface-specific braking or sliding control",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"court_sessions": "2-4", "snc_sessions": "2", "match_play": "low and skill-led"},
            "intermediate": {"court_sessions": "3-5", "snc_sessions": "2-3", "match_play": "1-3 exposures"},
            "advanced": {"court_sessions": "4-8", "snc_sessions": "2-4", "match_play": "periodized by competition"},
        },
        "common_injury_or_load_risks": [
            "shoulder overuse",
            "elbow pain",
            "wrist pain",
            "low-back rotation irritation",
            "ankle sprain",
            "knee pain",
            "calf or Achilles overload",
            "hip/groin irritation",
        ],
        "do_not_pair": [
            "high serve volume with shoulder, elbow, wrist, or back symptoms",
            "new plyometrics and match-dense weeks",
            "high-volume open-court conditioning with calf, Achilles, knee, or ankle symptoms",
            "heavy rotational lifting immediately before important matches",
            "fatigue-first tactical play before stroke and footwork quality are stable",
        ],
        "progression_guardrails": [
            "progress rally consistency before point pressure",
            "progress serve volume before serve speed",
            "use 24-hour shoulder, elbow, wrist, back, calf, Achilles, and knee response before adding court load",
            "separate high-impact court conditioning from heavy lower-body S&C",
            "make tactics format-specific: singles, doubles, player style, and surface",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs(),
    }


def _role_tags_for_domain(domain: str) -> List[str]:
    if domain == "singles_tactics":
        return ["all_roles", "singles", "aggressive_baseliner", "counterpuncher", "all_court_player"]
    if domain == "doubles_tactics":
        return ["all_roles", "doubles", "doubles_net_player", "doubles_baseline_player", "serve_and_volley_player"]
    if domain == "volley_net_play":
        return ["all_roles", "all_court_player", "serve_and_volley_player", "doubles_net_player"]
    if domain == "serve_return":
        return ["all_roles", "big_server", "serve_and_volley_player", "doubles_baseline_player"]
    if domain == "forehand_backhand":
        return ["all_roles", "aggressive_baseliner", "counterpuncher", "all_court_player"]
    return ["all_roles"]


def _teaching_progressions() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        for level in LEVELS:
            docs.append(
                {
                    "id": f"tennis_teach_{domain}_{level}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _role_tags_for_domain(domain),
                    "learning_goal": f"Develop tennis {domain.replace('_', ' ')} for a {level} player with safe court-load progression and tactical purpose.",
                    "suitable_for": [f"{level} tennis players", "tennis training"],
                    "prerequisites": _prerequisites(domain, level),
                    "teaching_priorities": _teaching_priorities(domain, level),
                    "technical_focus": _technical_focus(domain, level),
                    "tactical_focus": _tactical_focus(domain, level),
                    "physical_support": data["qualities"],
                    "practice_design": _practice_design(domain, level),
                    "typical_drills": _practice_design(domain, level),
                    "avoid_until_ready": _avoid_until_ready(domain, level),
                    "progression_signals": _progression_signals(domain, level),
                    "coach_notes": [
                        "Teach contact and movement quality before adding point pressure, surface complexity, or fatigue.",
                        "Progress court load based on 24-hour shoulder, elbow, wrist, back, knee, ankle, calf, and Achilles response.",
                    ],
                    "retrieval_tags": sorted(set([SPORT, domain, level, *data["qualities"], *data["risk_flags"], *_role_tags_for_domain(domain)])),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _source_refs(),
                }
            )
    return docs


def _prerequisites(domain: str, level: str) -> List[str]:
    if level == "beginner":
        return ["safe basic movement", "can rally or feed with simple contact", "no sharp court-movement or serving pain"]
    if level == "intermediate":
        return ["basic strokes and footwork are repeatable", "can recover between shots under simple pressure"]
    return ["consistent match exposure", "playing style or format is known", "court and serve load are tracked"]


def _teaching_priorities(domain: str, level: str) -> List[str]:
    base = {
        "beginner": ["contact quality", "safe split-step and recovery", "simple serve/return", "success and control"],
        "intermediate": ["decision-making", "depth and spin variation", "recovery speed", "pressure tolerance"],
        "advanced": ["opponent-specific patterns", "surface adaptation", "serve/return pressure", "competition load control"],
    }
    return _dedupe([*base[level], *DOMAINS[domain]["qualities"][:3]])


def _technical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "serve_return": ["serve setup", "kinetic chain", "contact point", "serve landing/recovery", "return split-step"],
        "forehand_backhand": ["grip and preparation", "contact spacing", "swing path", "trunk rotation", "recovery after contact"],
        "volley_net_play": ["split-step timing", "compact volley", "racket head stability", "closing angle", "overhead readiness"],
        "footwork_recovery": ["split-step timing", "first step", "shuffle/crossover choice", "braking mechanics", "recovery position"],
        "surface_adaptation": ["surface-specific braking", "sliding or small steps", "bounce timing", "footwear/load adjustment"],
        "tennis_strength_conditioning": ["deceleration", "rotational power", "scapular control", "calf/Achilles capacity"],
        "injury_load_management": ["symptom tracking", "serve volume caps", "surface transition staging", "return-to-court stages"],
    }
    return mapping.get(domain, ["score awareness", "serve/return choices", "basic tactical decisions"])


def _tactical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "singles_tactics": ["crosscourt stability", "attack open court", "recover position", "change direction only with advantage"],
        "doubles_tactics": ["serve/return pressure", "net positioning", "poaching cues", "partner communication", "formation choice"],
        "serve_return": ["serve plus one", "return plus one", "body/wide/T patterns", "neutralize strong serves"],
        "forehand_backhand": ["depth before direction change", "use spin/height by surface", "play to opponent weakness"],
        "volley_net_play": ["close behind advantage", "volley into space", "protect middle in doubles"],
        "surface_adaptation": ["adjust rally tolerance and court position by surface", "respect bounce and skid"],
    }
    if level == "advanced":
        return _dedupe([*mapping.get(domain, []), "opponent-specific adjustment", "score-state decisions"])
    return mapping.get(domain, ["simple tactical purpose", "recover after shot"])


def _practice_design(domain: str, level: str) -> List[str]:
    mapping = {
        "serve_return": ["serve target ladder", "return split-step timing", "serve plus one pattern drill"],
        "forehand_backhand": ["crosscourt rally constraint", "depth target drill", "forehand/backhand pattern feed"],
        "volley_net_play": ["split-step volley feeds", "approach plus first volley", "reaction volley game"],
        "footwork_recovery": ["split-step timing drill", "wide ball recover drill", "brake and recover cone drill"],
        "singles_tactics": ["crosscourt tolerance game", "change direction on short ball", "serve plus one scenario"],
        "doubles_tactics": ["serve/return pairs", "poach cue drill", "I-formation/Australian formation walk-through"],
        "surface_adaptation": ["surface movement rehearsal", "bounce-height timing drill", "short transition load session"],
        "tennis_strength_conditioning": ["lateral deceleration", "medicine ball rotation", "rotator cuff/scapular capacity", "repeat sprint with recovery"],
        "injury_load_management": ["court-load diary", "reduced-volume technical day", "return-to-court stage testing"],
    }
    return mapping.get(domain, ["rules/scoring scenario", "serve-side pressure game"])


def _avoid_until_ready(domain: str, level: str) -> List[str]:
    avoid = ["pain that changes movement", "fatigue-first skill work"]
    if level == "beginner":
        avoid.extend(["high serve volume", "open-court max-speed point play", "advanced deception or formations"])
    if domain in {"serve_return", "tennis_strength_conditioning"}:
        avoid.extend(["serve or medicine-ball volume spikes with shoulder, elbow, wrist, or back pain"])
    if domain in {"footwork_recovery", "surface_adaptation", "injury_load_management"}:
        avoid.extend(["high-volume open-court drills with knee, Achilles, calf, hip/groin, or ankle symptoms"])
    return _dedupe(avoid)


def _progression_signals(domain: str, level: str) -> List[str]:
    signals = ["24-hour pain response stable", "movement quality does not collapse under fatigue", "skill intent is clear"]
    if level in {"intermediate", "advanced"}:
        signals.extend(["decision quality remains under pressure", "recovery position or partner shape is reliable"])
    if domain in {"serve_return", "doubles_tactics", "singles_tactics"}:
        signals.append("serve/return or first-pattern decision is reliable")
    return signals


def _skill_assessments() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain in DOMAINS:
        docs.append(
            {
                "id": f"tennis_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _role_tags_for_domain(domain),
                "summary": f"Assesses tennis {domain.replace('_', ' ')} through technical quality, tactical transfer, movement recovery, and load response.",
                "metrics": _assessment_metrics(domain),
                "level_bands": [
                    {
                        "level": "beginner",
                        "indicators": ["simple contact/control is repeatable", "basic movement is safe", "understands simple tactical purpose"],
                        "ready_for_next_when": ["can perform under light feed pressure", "no worsening pain response", "recovers safely"],
                    },
                    {
                        "level": "intermediate",
                        "indicators": ["links shot choice to opponent/partner/score", "handles directional movement", "maintains form under moderate fatigue"],
                        "ready_for_next_when": ["can adapt in constraints", "court load is tolerated", "format/style is understood"],
                    },
                    {
                        "level": "advanced",
                        "indicators": ["uses opponent-specific tactics", "controls tournament load", "maintains quality across dense points"],
                        "ready_for_next_when": ["competition-specific plan is stable", "load and recovery are tracked"],
                    },
                ],
                "hold_if": [
                    "shoulder, elbow, wrist, back, ankle, knee, calf, Achilles, hip, or groin pain worsens",
                    "repeated late contact or unsafe braking mechanics",
                    "serve or open-court volume spikes",
                    "match/tournament load disrupts recovery",
                ],
                "retrieval_tags": sorted(set([SPORT, domain, "assessment", *_assessment_metrics(domain)])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _assessment_metrics(domain: str) -> List[str]:
    base = ["technical consistency", "decision quality", "movement recovery", "24-hour pain response"]
    specific = {
        "serve_return": ["serve accuracy", "return pressure", "first-pattern quality", "shoulder/elbow response"],
        "forehand_backhand": ["contact point", "depth/spin control", "trunk/back response"],
        "volley_net_play": ["split-step timing", "volley compactness", "reaction timing"],
        "footwork_recovery": ["split-step timing", "braking quality", "court recovery"],
        "singles_tactics": ["rally construction", "court position", "shot selection"],
        "doubles_tactics": ["formation understanding", "communication", "net pressure"],
        "surface_adaptation": ["braking/sliding quality", "bounce timing", "surface-load response"],
        "tennis_strength_conditioning": ["deceleration quality", "rotational power", "shoulder/scapular endurance"],
        "injury_load_management": ["symptom trend", "court-load tolerance", "return-to-court stage completion"],
    }
    return _dedupe([*specific.get(domain, []), *base])


def _level_transition_rules() -> List[Dict[str, Any]]:
    return [
        {
            "id": "tennis_beginner_to_intermediate",
            "sport": SPORT,
            "from_level": "beginner",
            "to_level": "intermediate",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "4+ weeks or 8+ completed tennis/S&C sessions",
                "safe split-step, braking, and court recovery",
                "can serve, return, rally, and recover with basic control",
                "no worsening shoulder, elbow, wrist, back, knee, ankle, calf, Achilles, hip, or groin symptoms",
            ],
            "promote_when": ["can maintain base skills under light pressure", "can recover between shots", "court load is stable"],
            "hold_when": ["pain trend worsens", "movement quality collapses", "serve or open-court volume causes symptoms"],
            "backend_action": "Unlock intermediate tactical constraints, directional footwork, serve/return patterns, and controlled singles/doubles specificity.",
            "retrieval_tags": ["tennis", "beginner", "intermediate", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "tennis_intermediate_to_advanced",
            "sport": SPORT,
            "from_level": "intermediate",
            "to_level": "advanced",
            "applies_to": ["all_roles", "singles", "doubles", "all_court_player", "aggressive_baseliner"],
            "minimum_evidence": [
                "8+ additional weeks or 16+ completed sessions",
                "format/style-specific tactics are understood",
                "can handle match-speed movement and serve exposure without symptom escalation",
                "S&C and court load support tournament/repeated-match exposure",
            ],
            "promote_when": ["uses opponent-specific tactics", "maintains quality under fatigue", "recovery and pain trends are stable"],
            "hold_when": ["unresolved shoulder/elbow/back/knee/Achilles symptoms", "unsafe braking or poor serve mechanics persist"],
            "backend_action": "Unlock advanced opponent-specific, surface-specific, tournament-week, and high-speed reactive planning with load gates.",
            "retrieval_tags": ["tennis", "intermediate", "advanced", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "tennis_hold_or_regress",
            "sport": SPORT,
            "from_level": "any",
            "to_level": "hold_or_regress",
            "applies_to": ["all_roles"],
            "minimum_evidence": ["pain, fatigue, completion, match-density, or surface-transition risk"],
            "promote_when": [],
            "hold_when": [
                "shoulder, elbow, wrist, back, ankle, knee, calf, Achilles, hip, or groin pain worsens",
                "braking or split-step mechanics are unsafe",
                "court sessions are missed from soreness/fatigue",
                "tournament or match density is high",
            ],
            "backend_action": "Bias next block toward reduced court load, technique, controlled movement, mobility, and strength capacity.",
            "retrieval_tags": ["tennis", "regression", "return_to_court", "safety"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
    ]


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs = []
    for index, domain in enumerate(DOMAINS, start=150001):
        docs.append(
            {
                "id": f"tennis_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe([SPORT, domain, *DOMAINS[domain]["qualities"], *DOMAINS[domain]["risk_flags"]]),
                "summary": DOMAINS[domain]["summary"],
                "source_refs": _source_refs(),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _with_metadata(docs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    output = []
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


def _merge_by_id(*record_groups: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for records in record_groups:
        for record in records:
            record_id = record.get("id")
            if not record_id:
                continue
            merged[str(record_id)] = record
    return list(merged.values())


def build_database_payload() -> Dict[str, Any]:
    deep_drafts = _load_deep_drafts()
    planning_rules = _planning_rules()
    collections = {
        "source_sections": _merge_by_id(_source_sections(), _deep_source_sections(deep_drafts)),
        "sport_profiles": [_sport_profile(planning_rules)],
        "sport_roles": _sport_roles(),
        "sport_training_rules": _merge_by_id(_sport_training_rules(), _deep_sport_training_rules(deep_drafts)),
        "planning_rules": _merge_by_id(planning_rules, _deep_planning_rules(deep_drafts)),
        "sport_teaching_progressions": _merge_by_id(_teaching_progressions(), _deep_teaching_progressions(deep_drafts)),
        "sport_skill_assessments": _merge_by_id(_skill_assessments(), _deep_skill_assessments(deep_drafts)),
        "sport_level_transition_rules": _level_transition_rules(),
    }
    return {
        "metadata": {
            "source_pack_id": SOURCE_PACK_ID,
            "sport": SPORT,
            "created_at": datetime.utcnow().isoformat(),
            "ingestion_method": INGESTION_METHOD,
            "deep_draft_count": len(deep_drafts),
            "deep_draft_paths": [draft.get("_draft_path") for draft in deep_drafts],
            "collection_counts": {name: len(records) for name, records in collections.items()},
        },
        "source_registry": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Tennis Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing tennis teaching, tactical, S&C, injury, surface, doubles, and level progression records.",
                "evidence_rank": 80,
                "source_refs": SOURCE_REFS,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Tennis Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized tennis knowledge pack for retrieval and AI workout generation.",
                "source_refs": SOURCE_REFS,
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
    TENNIS_DIR.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Convert tennis research into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

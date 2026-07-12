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
BADMINTON_DIR = PROJECT_ROOT / "backend" / "sport_research" / "badminton"
OUTPUT_PATH = BADMINTON_DIR / "badminton_teaching_database.json"
DRAFT_DIR = BADMINTON_DIR / "drafts"

SOURCE_PACK_ID = "badminton_teaching_database_v1"
INGESTION_METHOD = "badminton_research_structured_converter_v1"
SPORT = "badminton"
LEVELS = ["beginner", "intermediate", "advanced"]

SOURCE_REFS: List[Dict[str, Any]] = [
    {
        "title": "BWF Shuttle Time Teacher Manual",
        "url": "https://shuttletime.bwfbadminton.com/teacher-manual",
        "source_type": "official_coaching_education",
        "organization_or_author": "Badminton World Federation",
        "notes": "Used for beginner teaching progression, inclusive lesson design, techniques, tactics, and physical elements.",
    },
    {
        "title": "BWF Coach Education Level 1",
        "url": "https://development.bwfbadminton.com/coaches/level-1",
        "source_type": "official_coaching_education",
        "organization_or_author": "Badminton World Federation",
        "notes": "Used for coaching framework, technical/tactical fundamentals, movement, strokes, and performance factors.",
    },
    {
        "title": "Badminton Coaches' Manual Level 1",
        "url": "https://www.badminton-israel.co.il/newsNdata/General/CoachEducationBWF/BWF_Coach_Manual_Level_1.pdf",
        "source_type": "coach_manual_pdf",
        "organization_or_author": "Badminton World Federation coach education",
        "notes": "Used for strokes, movement, tactics, coaching progression, and athlete-development principles.",
    },
    {
        "title": "How to play badminton: rules, scoring system and equipment",
        "url": "https://www.olympics.com/en/news/badminton-guide-how-to-play-rules-olympic-history",
        "source_type": "official_sport_education",
        "organization_or_author": "Olympics",
        "notes": "Used for scoring, match format, singles/doubles context, and basic game model.",
    },
    {
        "title": "Badminton Injuries in Elite Athletes: A Review of Epidemiology and Biomechanics",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7205924/",
        "source_type": "peer_reviewed_review",
        "organization_or_author": "Review authors",
        "notes": "Used for common injury sites, mechanisms, and load-risk context.",
    },
    {
        "title": "Systematic review on badminton injuries",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11781153/",
        "source_type": "peer_reviewed_systematic_review",
        "organization_or_author": "Review authors",
        "notes": "Used for injury incidence, location, mechanisms, and risk factors.",
    },
    {
        "title": "The most common injuries in badminton",
        "url": "https://fittoplay.org/sports/badminton/the-most-common-injuries-in-badminton/",
        "source_type": "sports_medicine_education",
        "organization_or_author": "FitToPlay",
        "notes": "Used for practical injury-risk categories such as knee, ankle, shin, shoulder, plantar fascia, Achilles, and back pain.",
    },
]

DOMAINS: Dict[str, Dict[str, Any]] = {
    "rules_scoring_match_iq": {
        "summary": "Badminton match play is rally-scored to 21 points in best-of-three games, with tactical pressure changing by score, serve/receive, and singles or doubles format.",
        "qualities": ["score awareness", "serve receive decisions", "rally management", "momentum control"],
        "risk_flags": ["rushing under pressure", "poor serve legality awareness"],
    },
    "grip_racket_control": {
        "summary": "Grip changes and racket preparation determine whether the athlete can hit overheads, net shots, drives, lifts, blocks, and deceptive actions efficiently.",
        "qualities": ["finger control", "forearm endurance", "racket readiness", "touch"],
        "risk_flags": ["wrist_overuse", "forearm_tension", "late_racket_prep"],
    },
    "serve_return": {
        "summary": "Serve and return start every rally and shape tactical advantage, especially in doubles where serve height, receiver pressure, and third-shot intent matter.",
        "qualities": ["serve accuracy", "receive pressure", "first-three-shots", "decision speed"],
        "risk_flags": ["illegal_or_loose_serve", "static_receive_position"],
    },
    "clear_drop_smash": {
        "summary": "Overhead clear, drop, and smash share preparation but differ in contact, intent, and tactical use, allowing depth, deception, pressure, and finishing.",
        "qualities": ["overhead mechanics", "shoulder durability", "trunk rotation", "shot disguise"],
        "risk_flags": ["shoulder_overuse", "low_back_rotation", "late_contact"],
    },
    "drive_lift_block_net": {
        "summary": "Flat drives, defensive blocks, lifts, and net shots control speed, height, and space in the forecourt and midcourt.",
        "qualities": ["reaction speed", "racket face control", "net touch", "defensive reset"],
        "risk_flags": ["wrist_elbow_load", "poor_lunge_position"],
    },
    "footwork_recovery": {
        "summary": "Split-step, first-step direction, chasse, lunge, scissor kick, recovery steps, and base-position awareness decide whether strokes happen on time.",
        "qualities": ["split_step", "lunge control", "change_of_direction", "recovery footwork", "ankle stiffness"],
        "risk_flags": ["ankle_sprain", "knee_pain", "achilles_load", "fatigue_lunge_collapse"],
    },
    "singles_tactics": {
        "summary": "Singles demands court coverage, patient rally construction, depth changes, opponent movement, and disciplined recovery to base.",
        "qualities": ["court coverage", "rally construction", "pacing", "deception", "endurance"],
        "risk_flags": ["overrunning_base", "low_quality_recovery", "excessive_jump_smash_volume"],
    },
    "doubles_tactics": {
        "summary": "Doubles prioritizes serve/receive, rotation, front-back and side-by-side systems, intercepting, drive exchanges, and communication.",
        "qualities": ["rotation", "communication", "front_court_intercept", "rear_court_attack", "drive_speed"],
        "risk_flags": ["partner_collision", "shoulder_volume", "chaotic_rotation"],
    },
    "mixed_doubles_tactics": {
        "summary": "Mixed doubles uses role clarity, serve/receive pressure, front-court control, rear-court attack, and adaptive rotation based on matchup.",
        "qualities": ["role clarity", "front-court control", "rear-court power", "serve receive pressure"],
        "risk_flags": ["fixed_roles_without_adaptation", "communication_breakdown"],
    },
    "badminton_strength_conditioning": {
        "summary": "Badminton S&C should build deceleration, lunge strength, calf/Achilles capacity, shoulder/scapular durability, trunk rotation control, and repeat high-intensity efforts.",
        "qualities": ["deceleration", "lunge strength", "reactive agility", "shoulder durability", "repeat sprint ability"],
        "risk_flags": ["plyometric_spike", "shoulder_overuse", "knee_ankle_achilles_load"],
    },
    "injury_load_management": {
        "summary": "Badminton load management must track jumping/smashing volume, lunging volume, ankle/knee/Achilles response, shoulder symptoms, and match/tournament density.",
        "qualities": ["pain monitoring", "tournament recovery", "load tracking", "return_to_court"],
        "risk_flags": ["ankle_sprain", "patellar_tendon_pain", "shin_pain", "shoulder_pain", "low_back_pain"],
    },
}

ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "singles": ["single", "all_roles"],
    "single": ["singles", "all_roles"],
    "doubles": ["double", "front_court", "rear_court", "all_roles"],
    "double": ["doubles", "front_court", "rear_court", "all_roles"],
    "mixed_doubles": ["mixed", "xd", "front_court", "rear_court", "all_roles"],
    "mixed": ["mixed_doubles", "xd", "all_roles"],
    "xd": ["mixed_doubles", "mixed", "all_roles"],
    "front_court": ["net_player", "doubles", "mixed_doubles", "all_roles"],
    "rear_court": ["back_court", "doubles", "mixed_doubles", "all_roles"],
    "back_court": ["rear_court", "doubles", "mixed_doubles", "all_roles"],
    "attacking_player": ["rear_court", "smash", "all_roles"],
    "defensive_player": ["drive_lift_block_net", "all_roles"],
}

ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "singles": ["singles_tactics", "footwork_recovery", "clear_drop_smash", "serve_return", "badminton_strength_conditioning"],
    "single": ["singles_tactics", "footwork_recovery", "clear_drop_smash", "serve_return", "badminton_strength_conditioning"],
    "doubles": ["doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "footwork_recovery"],
    "double": ["doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "footwork_recovery"],
    "mixed_doubles": ["mixed_doubles_tactics", "doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash"],
    "mixed": ["mixed_doubles_tactics", "doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash"],
    "front_court": ["drive_lift_block_net", "serve_return", "doubles_tactics", "mixed_doubles_tactics"],
    "rear_court": ["clear_drop_smash", "doubles_tactics", "mixed_doubles_tactics", "badminton_strength_conditioning"],
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
        value = item.get(key)
        text = _short(value)
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
            "section_id": f"badminton_source_{_slug(ref_id)}",
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
            "section_id": f"badminton_section_{domain}",
            "section_title": domain.replace("_", " ").title(),
            "heading": "badminton_deep_research",
        }
    ]


def _draft_domain(draft: Dict[str, Any]) -> str:
    metadata = draft.get("metadata") or {}
    return _slug(metadata.get("domain") or "badminton_deep_research")


def _draft_summary(draft: Dict[str, Any]) -> str:
    metadata = draft.get("metadata") or {}
    return str(metadata.get("research_goal") or metadata.get("scope") or _draft_domain(draft).replace("_", " ")).strip()


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
    if "single" in text:
        roles.append("singles")
    if "double" in text or "formation" in text or "partner" in text:
        roles.append("doubles")
    if "mixed" in text or "xd" in text:
        roles.append("mixed_doubles")
    if "front" in text or "net" in text:
        roles.append("front_court")
    if "rear" in text or "overhead" in text or "smash" in text or "clear" in text:
        roles.append("rear_court")
    return _dedupe(roles)


def _draft_tags(domain: str, field: str, item: Mapping[str, Any]) -> List[str]:
    return sorted(set([
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
    ]))


def _deep_source_sections(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs: List[Dict[str, Any]] = []
    for index, draft in enumerate(drafts, start=131000):
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
                "id": f"badminton_section_{domain}",
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
                        "section_id": f"badminton_source_{_slug(ref.get('id') or ref.get('title'))}",
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
                doc_id = f"badminton_deep_rule_{domain}_{field}_{_slug(item.get('id') or item.get('record_id') or title)}"
                docs.append(
                    {
                        "id": doc_id,
                        "sport": SPORT,
                        "domain": domain,
                        "category": field.rstrip("s"),
                        "title": title,
                        "condition": _short(item.get("condition") or item.get("risk_context") or item.get("mechanism"), 360),
                        "rule": _summary_from_item(item),
                        "summary": _summary_from_item(item),
                        "recommended_action": _dedupe(
                            _text_items([
                                item.get("backend_action"),
                                item.get("training_notes"),
                                item.get("preferred_training"),
                                item.get("prevention_or_management"),
                                item.get("mitigation"),
                                item.get("teaching_points"),
                                item.get("teaching_progression"),
                            ])
                        )[:12],
                        "blocked_action": _dedupe(
                            _text_items([
                                item.get("avoid"),
                                item.get("avoid_until_ready"),
                                item.get("common_errors"),
                                item.get("warning_signs"),
                                item.get("monitoring_flags"),
                            ])
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
            for index, item in enumerate(draft.get(field) or [], start=1):
                if not isinstance(item, dict):
                    continue
                title = _title_from_item(item, f"{domain} planning {index}")
                category = str(item.get("category") or item.get("rule_category") or field).strip() or field
                docs.append(
                    {
                        "id": f"badminton_deep_plan_{domain}_{field}_{_slug(item.get('id') or title)}",
                        "sport": SPORT,
                        "applies_to": _draft_role_tags(domain, item),
                        "category": category,
                        "title": title,
                        "rule": _summary_from_item(item),
                        "rule_text": _summary_from_item(item),
                        "recommended_action": _dedupe(
                            _text_items([
                                item.get("backend_action"),
                                item.get("recommended_action"),
                                item.get("preferred_training"),
                                item.get("progression"),
                                item.get("quality_gates"),
                            ])
                        )[:10],
                        "blocked_action": _dedupe(
                            _text_items([
                                item.get("avoid"),
                                item.get("load_controls"),
                                item.get("monitoring_flags"),
                                item.get("warning_signs"),
                            ])
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
                    "id": f"badminton_deep_plan_{domain}_{_slug(item.get('record_id') or item.get('id') or title)}",
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
                    "id": f"badminton_deep_teach_{domain}_{level}_{_slug(item.get('id') or title)}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _draft_role_tags(domain, item),
                    "learning_goal": _summary_from_item(item),
                    "suitable_for": [f"{level} badminton players", "badminton sport skill training"],
                    "prerequisites": _dedupe(_text_items(item.get("prerequisites")))[:8] or _prerequisites("footwork_recovery", level),
                    "teaching_priorities": _dedupe(_text_items([item.get("preferred_training"), item.get("summary"), item.get("recommendation")]))[:8],
                    "technical_focus": _dedupe(_text_items([item.get("progression"), item.get("quality_gates"), item.get("implementation_notes")]))[:8],
                    "tactical_focus": _dedupe(_text_items([item.get("implementation_examples"), item.get("backend_use")]))[:6],
                    "physical_support": _dedupe(_text_items([item.get("training_methods"), item.get("preferred_training")]))[:8],
                    "practice_design": _dedupe(_text_items([item.get("progression"), item.get("practice_design"), item.get("implementation_examples")]))[:8],
                    "typical_drills": _dedupe(_text_items([item.get("progression"), item.get("preferred_training")]))[:8],
                    "avoid_until_ready": _dedupe(_text_items(item.get("avoid")))[:8],
                    "progression_signals": _dedupe(_text_items(item.get("quality_gates") or item.get("assessment_signals")))[:8] or _progression_signals("footwork_recovery", level),
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
                        "id": f"badminton_deep_teach_{domain}_{level_key}_{_slug(model.get('id') or model_title)}",
                        "sport": SPORT,
                        "domain": domain,
                        "level": level_key,
                        "role_tags": _draft_role_tags(domain, model),
                        "learning_goal": f"Develop {model_title} for a {level_key} badminton player.",
                        "suitable_for": [f"{level_key} badminton players"],
                        "prerequisites": _prerequisites("grip_racket_control", level_key),
                        "teaching_priorities": _dedupe(_text_items([model.get("mechanics"), model.get("racket_preparation")]))[:8],
                        "technical_focus": _dedupe(_text_items([model.get("coaching_cues"), model.get("teaching_points")]))[:8],
                        "tactical_focus": _dedupe(_text_items([model.get("tactical_use"), model.get("shot_selection")]))[:6],
                        "physical_support": _dedupe(_text_items([model.get("physical_demands"), model.get("load_notes")]))[:6],
                        "practice_design": _dedupe(_text_items(steps))[:8],
                        "typical_drills": _dedupe(_text_items(steps))[:8],
                        "avoid_until_ready": _dedupe(_text_items(model.get("common_errors")))[:8],
                        "progression_signals": _dedupe(_text_items(model.get("quality_markers")))[:8] or _progression_signals("grip_racket_control", level_key),
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
            _text_items([
                [item.get("quality_markers") for item in technical_items],
                [item.get("monitoring") for item in demand_items],
                [item.get("monitoring_flags") for item in risk_items],
                [item.get("warning_signs") for item in risk_items],
            ])
        )[:14]
        docs.append(
            {
                "id": f"badminton_deep_assess_{domain}",
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
                        "indicators": ["links the skill to opponent, partner, or score context", "movement and racket quality survive moderate fatigue"],
                        "ready_for_next_when": ["quality remains stable under constraints", "load channels are tolerated"],
                    },
                    {
                        "level": "advanced",
                        "indicators": ["adapts to opponent and match state", "manages tournament or dense match exposure"],
                        "ready_for_next_when": ["competition transfer and recovery are reliable"],
                    },
                ],
                "hold_if": _dedupe(_text_items([[item.get("warning_signs") for item in risk_items], [item.get("avoid") for item in draft.get("training_implications") or [] if isinstance(item, dict)]]))[:10],
                "retrieval_tags": _draft_tags(domain, "skill_assessment", {"metrics": metrics}),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _refs_for_item(draft, {"source_ids": _dedupe(_collect_source_ids(draft))[:8]}),
            }
        )
    return docs


def _sport_roles() -> List[Dict[str, Any]]:
    roles = {
        "singles": {
            "display_name": "Singles Player",
            "summary": "Covers the full court alone, manages rally length, depth, deception, and recovery to base.",
            "skill_priorities": ["serve quality", "clear/drop/smash variation", "full-court footwork", "rally construction", "endurance"],
            "physical_demands": ["aerobic support", "repeat lunge capacity", "ankle/knee control", "shoulder endurance"],
        },
        "doubles": {
            "display_name": "Doubles Player",
            "summary": "Uses serve/receive pressure, fast drives, intercepts, rotation, and partnership communication.",
            "skill_priorities": ["serve/receive", "drive exchanges", "front-back rotation", "side-by-side defense", "communication"],
            "physical_demands": ["reaction speed", "shoulder speed endurance", "lateral movement", "front-court explosiveness"],
        },
        "mixed_doubles": {
            "display_name": "Mixed Doubles Player",
            "summary": "Balances front-court control, rear-court attack, rotation, matchup awareness, and role adaptation.",
            "skill_priorities": ["serve/receive", "front-court control", "rear-court pressure", "adaptive rotation", "communication"],
            "physical_demands": ["reaction speed", "overhead durability", "lunge control", "power endurance"],
        },
        "front_court": {
            "display_name": "Front-Court Player",
            "summary": "Controls net, interceptions, kills, serve pressure, and early rally advantage.",
            "skill_priorities": ["net shot", "tumble/spin control", "intercept", "serve return", "racket readiness"],
            "physical_demands": ["reaction speed", "low lunge strength", "wrist/forearm control", "calf stiffness"],
        },
        "rear_court": {
            "display_name": "Rear-Court Player",
            "summary": "Creates pressure through clears, drops, smashes, punch clears, and tactical shot disguise.",
            "skill_priorities": ["clear/drop/smash disguise", "recovery after overhead", "power control", "shot selection"],
            "physical_demands": ["shoulder/scapular durability", "trunk rotation", "jump/landing control", "repeat power"],
        },
    }
    docs: List[Dict[str, Any]] = []
    for role, data in roles.items():
        docs.append(
            {
                "id": f"badminton_role_{role}",
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
    if role in {"rear_court", "mixed_doubles"}:
        return ["shoulder_overuse", "low_back_rotation", "jump_landing_load"]
    if role in {"front_court", "doubles"}:
        return ["ankle_sprain", "wrist_elbow_load", "reaction_collision"]
    return ["knee_pain", "ankle_sprain", "shoulder_overuse", "achilles_load"]


def _sport_training_rules() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        docs.append(
            {
                "id": f"badminton_training_rule_{domain}",
                "sport": SPORT,
                "domain": domain,
                "category": "badminton_domain_rule",
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
            "id": "badminton_plan_foundation_before_power",
            "category": "progression",
            "rule": "Build grip changes, racket preparation, basic footwork, and safe lunge mechanics before high-volume smash, jump-smash, or reactive agility work.",
            "recommended_action": ["prioritize split-step, base recovery, lunge control, clear/drop technique"],
            "blocked_action": ["do not use fatigue smash circuits for beginners"],
            "priority": 86,
        },
        {
            "id": "badminton_plan_lunge_load_gate",
            "category": "injury_risk",
            "rule": "Progress lunges, deep net retrievals, and multi-shuttle footwork by knee, ankle, Achilles, and 24-hour symptom response.",
            "recommended_action": ["use controlled lunge volume", "add direction and speed gradually"],
            "blocked_action": ["avoid high-volume deep lunges with knee, Achilles, ankle, or shin pain"],
            "priority": 94,
        },
        {
            "id": "badminton_plan_shoulder_volume_gate",
            "category": "injury_risk",
            "rule": "Track overhead and smash volume because shoulder/scapular endurance and trunk rotation quality shape safe progression.",
            "recommended_action": ["include rotator cuff, scapular, thoracic, trunk, and posterior-chain support"],
            "blocked_action": ["avoid power-smash volume spikes with shoulder or back symptoms"],
            "priority": 92,
        },
        {
            "id": "badminton_plan_singles_vs_doubles",
            "category": "sport_specificity",
            "rule": "Singles, doubles, and mixed doubles should bias different tactical and physical stress: full-court endurance for singles, reaction/rotation for doubles, role clarity for mixed doubles.",
            "recommended_action": ["use format-specific domains when role is known"],
            "blocked_action": ["do not prescribe one generic badminton plan for all match formats"],
            "priority": 82,
        },
        {
            "id": "badminton_plan_tournament_density",
            "category": "competition_week",
            "rule": "During tournament weeks, reduce new S&C soreness, high lunge volume, and shoulder power volume while preserving rhythm, footwork sharpness, and recovery.",
            "recommended_action": ["use activation, short movement sharpness, light hitting rhythm"],
            "blocked_action": ["avoid new plyometrics or heavy lower-body eccentric work before competition"],
            "priority": 88,
        },
        {
            "id": "badminton_plan_return_to_court",
            "category": "return_to_sport",
            "rule": "Return to badminton should progress from shadow footwork and controlled hitting to directional lunge work, multi-shuttle drills, and match play only when symptoms remain stable.",
            "recommended_action": ["use staged return-to-court progressions"],
            "blocked_action": ["avoid match play based only on pain-free rest"],
            "priority": 95,
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
        "id": "sport_profile_badminton",
        "sport": SPORT,
        "planning_summary": "Badminton is a high-speed racket sport requiring split-step timing, multidirectional footwork, lunge/deceleration capacity, overhead shoulder durability, racket touch, serve/receive skill, singles/doubles tactical awareness, and repeat high-intensity rally recovery.",
        "training_priorities": [
            "grip changes and racket readiness",
            "split-step timing, first step, lunge, and recovery to base",
            "clear, drop, smash, drive, lift, block, and net-shot skill",
            "serve/receive and first-three-shot tactical quality",
            "singles rally construction or doubles rotation based on role",
            "shoulder/scapular, trunk, calf/Achilles, knee, and ankle durability",
            "reactive agility and repeat high-intensity effort capacity",
            "tournament-week load management",
        ],
        "key_physical_qualities": [
            "split-step reactivity",
            "lunge strength",
            "deceleration",
            "ankle stiffness",
            "calf/Achilles capacity",
            "shoulder and scapular endurance",
            "trunk rotation control",
            "reaction speed",
            "repeat sprint ability",
            "jump and landing quality",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"court_sessions": "2-4", "snc_sessions": "2", "match_play": "low and skill-led"},
            "intermediate": {"court_sessions": "3-5", "snc_sessions": "2-3", "match_play": "1-3 exposures"},
            "advanced": {"court_sessions": "4-8", "snc_sessions": "2-4", "match_play": "periodized by competition"},
        },
        "common_injury_or_load_risks": [
            "ankle sprain",
            "patellar tendon or knee pain",
            "Achilles or calf overload",
            "shin pain",
            "shoulder overuse",
            "elbow/wrist overload",
            "low-back rotation irritation",
            "plantar fascia irritation",
        ],
        "do_not_pair": [
            "high-volume multi-shuttle lunges with knee, shin, Achilles, or ankle symptoms",
            "smash-volume spikes with shoulder or low-back symptoms",
            "new plyometrics and high tournament/match density",
            "heavy lower-body eccentric work immediately before important matches",
            "fatigue-first agility before footwork quality is stable",
        ],
        "progression_guardrails": [
            "progress footwork complexity before footwork speed",
            "progress stroke volume before power volume",
            "use 24-hour knee, ankle, Achilles, shoulder, and back response before adding court load",
            "separate high-impact multi-shuttle work from heavy lower-body S&C",
            "make tactics format-specific: singles, doubles, mixed doubles, front/rear court",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs(),
    }


def _teaching_progressions() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        for level in LEVELS:
            docs.append(
                {
                    "id": f"badminton_teach_{domain}_{level}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _role_tags_for_domain(domain),
                    "learning_goal": f"Develop badminton {domain.replace('_', ' ')} for a {level} player with safe court-load progression and clear tactical purpose.",
                    "suitable_for": [f"{level} badminton players", "badminton training"],
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
                        "Teach technique before adding shuttle speed, opponent pressure, or fatigue.",
                        "Progress court load based on 24-hour knee, ankle, Achilles, shoulder, and back response.",
                    ],
                    "retrieval_tags": sorted(set([SPORT, domain, level, *data["qualities"], *data["risk_flags"], *_role_tags_for_domain(domain)])),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _source_refs(),
                }
            )
    return docs


def _role_tags_for_domain(domain: str) -> List[str]:
    if domain == "singles_tactics":
        return ["all_roles", "singles"]
    if domain == "doubles_tactics":
        return ["all_roles", "doubles", "front_court", "rear_court"]
    if domain == "mixed_doubles_tactics":
        return ["all_roles", "mixed_doubles", "front_court", "rear_court"]
    if domain == "drive_lift_block_net":
        return ["all_roles", "front_court", "doubles"]
    if domain == "clear_drop_smash":
        return ["all_roles", "rear_court", "singles", "doubles"]
    return ["all_roles"]


def _prerequisites(domain: str, level: str) -> List[str]:
    if level == "beginner":
        return ["safe basic movement", "can hold racket and make simple contact", "no sharp court-movement pain"]
    if level == "intermediate":
        return ["basic strokes and footwork are repeatable", "can recover to base under simple pressure"]
    return ["consistent match exposure", "role/format is known", "court load is tracked"]


def _teaching_priorities(domain: str, level: str) -> List[str]:
    base = {
        "beginner": ["simple contact quality", "safe footwork", "racket preparation", "success and control"],
        "intermediate": ["decision-making", "shot variation", "recovery speed", "pressure tolerance"],
        "advanced": ["opponent-specific patterns", "deception", "tempo changes", "competition load control"],
    }
    return _dedupe([*base[level], *DOMAINS[domain]["qualities"][:3]])


def _technical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "grip_racket_control": ["forehand/backhand grip change", "relaxed fingers", "racket up early", "short preparation"],
        "serve_return": ["serve accuracy", "legal/contact height awareness", "receiver stance", "first movement after serve"],
        "clear_drop_smash": ["side-on preparation", "contact point", "trunk rotation", "recovery after overhead", "shot disguise"],
        "drive_lift_block_net": ["racket face angle", "short swing", "net height control", "stable lunge base"],
        "footwork_recovery": ["split-step timing", "first step", "chasse/cross-step choice", "lunge alignment", "recovery to base"],
        "singles_tactics": ["deep length", "move opponent", "base recovery", "tempo variation"],
        "doubles_tactics": ["serve/receive pressure", "front-back attack", "side-by-side defense", "rotation cue"],
        "mixed_doubles_tactics": ["role clarity", "front-court pressure", "rear-court attack", "adaptive rotation"],
        "badminton_strength_conditioning": ["deceleration", "single-leg control", "calf/Achilles capacity", "scapular control"],
        "injury_load_management": ["symptom tracking", "volume caps", "return-to-court staging", "tournament recovery"],
    }
    return mapping.get(domain, ["score awareness", "serve/receive rules", "basic tactical choices"])


def _tactical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "singles_tactics": ["create space", "recover to base", "change depth", "use deception only when stable"],
        "doubles_tactics": ["win serve/receive", "rotate with partner", "attack as front-back", "defend as side-by-side"],
        "mixed_doubles_tactics": ["role clarity", "serve/receive pressure", "protect partner space", "adapt to matchup"],
        "serve_return": ["first-three-shot plan", "pressure receiver/server", "avoid loose lift under pressure"],
        "clear_drop_smash": ["same preparation different outcome", "choose clear/drop/smash by opponent position"],
        "drive_lift_block_net": ["control speed and height", "reset with lift/block when under pressure"],
    }
    if level == "advanced":
        return _dedupe([*mapping.get(domain, []), "opponent-specific adjustment", "score-state decisions"])
    return mapping.get(domain, ["simple tactical purpose", "recover after shot"])


def _practice_design(domain: str, level: str) -> List[str]:
    mapping = {
        "grip_racket_control": ["grip-change shadow reps", "racket-up reaction taps", "forehand/backhand feed alternation"],
        "serve_return": ["target serving", "return pressure games", "first-three-shot pattern drill"],
        "clear_drop_smash": ["overhead shadow", "clear/drop contrast feeds", "controlled smash volume"],
        "drive_lift_block_net": ["net touch feeds", "drive exchange constraints", "lift/block defensive reset drill"],
        "footwork_recovery": ["split-step timing drill", "six-corner shadow footwork", "lunge and recover drill"],
        "singles_tactics": ["deep-clear rally constraint", "move-opponent drill", "base recovery game"],
        "doubles_tactics": ["serve/receive pairs", "rotation cue drill", "front-back attack vs side-by-side defense"],
        "mixed_doubles_tactics": ["front/rear role drill", "serve plus third shot", "adaptive rotation scenario"],
        "badminton_strength_conditioning": ["deceleration bounds", "lateral lunge strength", "rotator cuff/scapular capacity", "repeat-shuttle conditioning"],
        "injury_load_management": ["court-load diary", "reduced-volume technical day", "return-to-court stage testing"],
    }
    return mapping.get(domain, ["rules/scoring game", "serve-side rotation practice"])


def _avoid_until_ready(domain: str, level: str) -> List[str]:
    avoid = ["pain that changes movement", "fatigue-first skill work"]
    if level == "beginner":
        avoid.extend(["jump smash volume", "high-speed multi-shuttle", "advanced deception"])
    if domain in {"clear_drop_smash", "badminton_strength_conditioning"}:
        avoid.extend(["high overhead/smash volume with shoulder or back pain"])
    if domain in {"footwork_recovery", "injury_load_management"}:
        avoid.extend(["deep lunge volume with knee, Achilles, shin, or ankle symptoms"])
    return _dedupe(avoid)


def _progression_signals(domain: str, level: str) -> List[str]:
    signals = ["24-hour pain response stable", "movement quality does not collapse under fatigue", "skill intent is clear"]
    if level in {"intermediate", "advanced"}:
        signals.extend(["decision quality remains under pressure", "recovers to base or partner shape"])
    if domain in {"serve_return", "doubles_tactics", "mixed_doubles_tactics"}:
        signals.append("first-three-shot decision is reliable")
    return signals


def _skill_assessments() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain in DOMAINS:
        docs.append(
            {
                "id": f"badminton_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _role_tags_for_domain(domain),
                "summary": f"Assesses badminton {domain.replace('_', ' ')} through technical quality, tactical transfer, movement recovery, and load response.",
                "metrics": _assessment_metrics(domain),
                "level_bands": [
                    {
                        "level": "beginner",
                        "indicators": ["simple contact/control is repeatable", "basic footwork is safe", "understands simple tactical purpose"],
                        "ready_for_next_when": ["can perform under light feed pressure", "no worsening pain response", "recovers safely"],
                    },
                    {
                        "level": "intermediate",
                        "indicators": ["links shot choice to opponent/partner position", "handles directional movement", "maintains form under moderate fatigue"],
                        "ready_for_next_when": ["can adapt in constraints", "court load is tolerated", "match format is understood"],
                    },
                    {
                        "level": "advanced",
                        "indicators": ["uses opponent-specific tactics", "controls tournament load", "maintains quality across dense rallies"],
                        "ready_for_next_when": ["competition-specific plan is stable", "load and recovery are tracked"],
                    },
                ],
                "hold_if": [
                    "ankle, knee, Achilles, shin, shoulder, elbow/wrist, or back pain worsens",
                    "repeated late contact or unsafe lunge collapse",
                    "overhead or jump volume spikes",
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
        "grip_racket_control": ["grip-change speed", "racket preparation", "touch quality"],
        "serve_return": ["serve accuracy", "return pressure", "first-three-shot quality"],
        "clear_drop_smash": ["contact point", "shot disguise", "shoulder/back response"],
        "drive_lift_block_net": ["racket-face control", "net height control", "reaction timing"],
        "footwork_recovery": ["split-step timing", "lunge alignment", "base recovery"],
        "singles_tactics": ["rally construction", "court coverage", "depth control"],
        "doubles_tactics": ["rotation", "communication", "serve/receive pressure"],
        "mixed_doubles_tactics": ["role clarity", "adaptive rotation", "front/rear coordination"],
        "badminton_strength_conditioning": ["deceleration quality", "repeat effort capacity", "shoulder/scapular endurance"],
        "injury_load_management": ["symptom trend", "court-load tolerance", "return-to-court stage completion"],
    }
    return _dedupe([*specific.get(domain, []), *base])


def _level_transition_rules() -> List[Dict[str, Any]]:
    return [
        {
            "id": "badminton_beginner_to_intermediate",
            "sport": SPORT,
            "from_level": "beginner",
            "to_level": "intermediate",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "4+ weeks or 8+ completed badminton/S&C sessions",
                "safe split-step, basic lunge, and recovery footwork",
                "can serve, clear/drop, and rally with basic control",
                "no worsening knee, ankle, Achilles, shoulder, or back symptoms",
            ],
            "promote_when": ["can maintain base skills under light pressure", "can recover to base", "court load is stable"],
            "hold_when": ["pain trend worsens", "movement quality collapses", "overhead or lunge volume causes symptoms"],
            "backend_action": "Unlock intermediate tactical constraints, multi-direction footwork, and controlled doubles/singles specificity.",
            "retrieval_tags": ["badminton", "beginner", "intermediate", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "badminton_intermediate_to_advanced",
            "sport": SPORT,
            "from_level": "intermediate",
            "to_level": "advanced",
            "applies_to": ["all_roles", "singles", "doubles", "mixed_doubles"],
            "minimum_evidence": [
                "8+ additional weeks or 16+ completed sessions",
                "format-specific tactics are understood",
                "can handle match-speed movement without symptom escalation",
                "S&C and court load support tournament/repeated-match exposure",
            ],
            "promote_when": ["uses opponent-specific tactics", "maintains quality under fatigue", "recovery and pain trends are stable"],
            "hold_when": ["unresolved shoulder/back/knee/Achilles symptoms", "chaotic rotation or unsafe footwork persists"],
            "backend_action": "Unlock advanced opponent-specific, tournament-week, and high-speed reactive planning with load gates.",
            "retrieval_tags": ["badminton", "intermediate", "advanced", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "badminton_hold_or_regress",
            "sport": SPORT,
            "from_level": "any",
            "to_level": "hold_or_regress",
            "applies_to": ["all_roles"],
            "minimum_evidence": ["pain, fatigue, or completion risk"],
            "promote_when": [],
            "hold_when": [
                "ankle, knee, shin, Achilles, shoulder, wrist/elbow, or back pain worsens",
                "lunge or landing mechanics are unsafe",
                "court sessions are missed from soreness/fatigue",
                "tournament or match density is high",
            ],
            "backend_action": "Bias next block toward reduced court load, technique, controlled footwork, mobility, and strength capacity.",
            "retrieval_tags": ["badminton", "regression", "return_to_court", "safety"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
    ]


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs = []
    for index, domain in enumerate(DOMAINS, start=130001):
        docs.append(
            {
                "id": f"badminton_section_{domain}",
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
                "title": "SFTC Badminton Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing badminton teaching, tactical, S&C, injury, and level progression records.",
                "evidence_rank": 80,
                "source_refs": SOURCE_REFS,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Badminton Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized badminton knowledge pack for retrieval and AI workout generation.",
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
    BADMINTON_DIR.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Convert badminton research into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

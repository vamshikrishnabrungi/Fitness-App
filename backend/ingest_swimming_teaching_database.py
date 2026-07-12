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
SWIMMING_DIR = PROJECT_ROOT / "backend" / "sport_research" / "swimming"
OUTPUT_PATH = SWIMMING_DIR / "swimming_teaching_database.json"
DRAFT_DIR = SWIMMING_DIR / "drafts"

SOURCE_PACK_ID = "swimming_teaching_database_v1"
INGESTION_METHOD = "swimming_research_structured_converter_v1"
SPORT = "swimming"
LEVELS = ["beginner", "intermediate", "advanced"]

SOURCE_REFS: List[Dict[str, Any]] = [
    {
        "title": "World Aquatics Competition Regulations",
        "url": "https://www.worldaquatics.com/rules/competition-regulations",
        "source_type": "official_rules",
        "organization_or_author": "World Aquatics",
        "notes": "Used for official stroke, start, turn, race, and competition context.",
    },
    {
        "title": "USA Swimming Athlete Development Model",
        "url": "https://www.usaswimming.org/docs/default-source/coaching-resourcesdocuments/adm-competence-progressions.pdf",
        "source_type": "official_coaching_education",
        "organization_or_author": "USA Swimming",
        "notes": "Used for competency progressions and development-stage guidance.",
    },
    {
        "title": "Swim England Expected Standards",
        "url": "https://www.swimming.org/swimengland/swim-england-expected-standards/",
        "source_type": "official_teaching_education",
        "organization_or_author": "Swim England",
        "notes": "Used for learn-to-swim standards, water confidence, and staged progression.",
    },
    {
        "title": "USA Swimming Teaching Racing Starts",
        "url": "https://www.usaswimming.org/docs/default-source/coaching-resourcesdocuments/teaching-racing-starts.pdf",
        "source_type": "official_coaching_education",
        "organization_or_author": "USA Swimming",
        "notes": "Used for racing-start teaching and safety gates.",
    },
    {
        "title": "Red Cross, YMCA, USA Swimming Hypoxic Blackout Statement",
        "url": "https://www.usaswimming.org/docs/default-source/rules-regulations/hypoxic-training-statement.pdf",
        "source_type": "safety_guidance",
        "organization_or_author": "Red Cross, YMCA, USA Swimming",
        "notes": "Used for breath-holding and hypoxic training safety constraints.",
    },
    {
        "title": "Swimming Injuries Review",
        "url": "https://pubmed.ncbi.nlm.nih.gov/23016094/",
        "source_type": "peer_reviewed_review",
        "organization_or_author": "Sports medicine review authors",
        "notes": "Used for swimmer shoulder, knee, back, and overuse-risk context.",
    },
    {
        "title": "Elite Swimmers Training Patterns",
        "url": "https://researchprofiles.canberra.edu.au/en/publications/elite-swimmers-training-patterns-in-the-25-weeks-prior-to-their-s/",
        "source_type": "peer_reviewed_training_research",
        "organization_or_author": "Sport science authors",
        "notes": "Used for periodization, training distribution, and taper context.",
    },
    {
        "title": "Open-Water Pacing Research",
        "url": "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.00654/full",
        "source_type": "peer_reviewed_research",
        "organization_or_author": "Sport psychology and performance authors",
        "notes": "Used for open-water pacing and race-context logic.",
    },
]

DOMAINS: Dict[str, Dict[str, Any]] = {
    "water_confidence_safety": {
        "summary": "Beginner swimming starts with water comfort, breathing, floating, gliding, recovery to stand, supervision, and safety before fitness volume.",
        "qualities": ["water confidence", "breathing control", "floating", "safe pool behavior"],
        "risk_flags": ["non_swimmer", "panic_or_fear", "unsupervised_water", "unsafe_breath_holding"],
    },
    "freestyle": {
        "summary": "Freestyle performance depends on body line, relaxed exhalation, head position, rotation, catch quality, kick rhythm, and breathing that does not disrupt alignment.",
        "qualities": ["body position", "catch mechanics", "breathing rhythm", "stroke economy"],
        "risk_flags": ["shoulder_pain", "neck_irritation", "poor_exhalation", "cross_midline_pull"],
    },
    "backstroke": {
        "summary": "Backstroke requires stable head position, hip height, body rotation, alternating arm rhythm, consistent kick, and wall awareness.",
        "qualities": ["rotation", "body line", "overhead rhythm", "kick consistency"],
        "risk_flags": ["shoulder_pain", "low_back_arch", "lane_collision"],
    },
    "breaststroke": {
        "summary": "Breaststroke links pull, breath, kick, and glide timing while managing knee, groin, hip, and low-back load from the kick pattern.",
        "qualities": ["stroke timing", "kick mechanics", "glide efficiency", "hip control"],
        "risk_flags": ["knee_pain", "groin_pain", "low_back_extension", "excessive_kick_volume"],
    },
    "butterfly": {
        "summary": "Butterfly requires body-wave timing, dolphin kick rhythm, catch-and-press mechanics, breathing timing, and high shoulder/trunk endurance.",
        "qualities": ["dolphin kick", "body wave", "shoulder endurance", "trunk rhythm"],
        "risk_flags": ["shoulder_overload", "low_back_pain", "fatigue_technique_collapse"],
    },
    "starts_turns_underwaters": {
        "summary": "Starts, turns, streamlines, underwater kicks, and breakouts are race skills that require safety gates, pool context, and high technical quality.",
        "qualities": ["streamline", "turn skill", "underwater phase", "breakout timing", "race skill"],
        "risk_flags": ["diving_safety", "hypoxic_risk", "neck_back_load", "poor_wall_awareness"],
    },
    "event_programming": {
        "summary": "Swimming programming should match sprint, middle-distance, distance, IM, open-water, triathlon, or fitness goals through appropriate pace, volume, intensity, and taper logic.",
        "qualities": ["pacing", "training zones", "race specificity", "periodization"],
        "risk_flags": ["yardage_spike", "intensity_stack", "poor_taper", "technique_decay"],
    },
    "open_water_triathlon": {
        "summary": "Open-water and triathlon swimming adds sighting, drafting, environmental safety, anxiety control, wetsuit/context adaptation, and sustainable rhythm.",
        "qualities": ["sighting", "drafting", "sustained rhythm", "open_water_safety"],
        "risk_flags": ["environmental_risk", "panic_or_fear", "navigation_error", "cold_water_context"],
    },
    "swimming_strength_conditioning": {
        "summary": "Swimming dryland should support shoulder/scapular control, trunk stiffness, thoracic mobility, posterior-chain strength, starts/turns power, and kicking mobility without ruining water quality.",
        "qualities": ["shoulder durability", "trunk control", "thoracic mobility", "posterior_chain", "start_power"],
        "risk_flags": ["upper_body_fatigue", "overhead_overload", "dryland_pool_stack"],
    },
    "injury_load_management": {
        "summary": "Swimming load management tracks yardage, stroke-specific volume, paddles/fins, high-intensity repeats, shoulder/back/knee response, and return-to-swim progression.",
        "qualities": ["load monitoring", "return_to_swim", "pain response", "stroke volume tracking"],
        "risk_flags": ["swimmer_shoulder", "breaststroke_knee", "low_back_pain", "yardage_spike"],
    },
}

ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "beginner_swimmer": ["learn_to_swim", "water_confidence", "non_swimmer"],
    "fitness_swimmer": ["general_swimmer", "recreational_swimmer"],
    "freestyle_sprinter": ["sprint_freestyle", "50m", "100m"],
    "middle_distance_swimmer": ["200m", "400m", "middle_distance"],
    "distance_swimmer": ["800m", "1500m", "distance_freestyle"],
    "backstroke_swimmer": ["backstroke"],
    "breaststroke_swimmer": ["breaststroke"],
    "butterfly_swimmer": ["butterfly", "fly"],
    "im_swimmer": ["individual_medley", "medley"],
    "open_water_swimmer": ["open_water", "distance_swimmer"],
    "triathlon_swimmer": ["triathlon", "open_water_swimmer"],
    "masters_swimmer": ["adult_swimmer", "fitness_swimmer"],
    "youth_development": ["youth_swimmer", "age_group_swimmer"],
}

ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_swimmer": ["water_confidence_safety", "freestyle", "injury_load_management"],
    "learn_to_swim": ["water_confidence_safety", "freestyle"],
    "fitness_swimmer": ["freestyle", "event_programming", "swimming_strength_conditioning", "injury_load_management"],
    "freestyle_sprinter": ["freestyle", "starts_turns_underwaters", "event_programming", "swimming_strength_conditioning"],
    "middle_distance_swimmer": ["freestyle", "event_programming", "starts_turns_underwaters", "injury_load_management"],
    "distance_swimmer": ["freestyle", "event_programming", "injury_load_management", "open_water_triathlon"],
    "backstroke_swimmer": ["backstroke", "starts_turns_underwaters", "injury_load_management"],
    "breaststroke_swimmer": ["breaststroke", "event_programming", "injury_load_management"],
    "butterfly_swimmer": ["butterfly", "starts_turns_underwaters", "injury_load_management"],
    "im_swimmer": ["freestyle", "backstroke", "breaststroke", "butterfly", "starts_turns_underwaters", "event_programming"],
    "open_water_swimmer": ["open_water_triathlon", "freestyle", "event_programming", "injury_load_management"],
    "triathlon_swimmer": ["open_water_triathlon", "freestyle", "event_programming", "swimming_strength_conditioning"],
    "masters_swimmer": ["freestyle", "event_programming", "injury_load_management", "swimming_strength_conditioning"],
    "youth_development": ["water_confidence_safety", "freestyle", "starts_turns_underwaters", "event_programming"],
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


def _source_refs(limit: int = 8) -> List[Dict[str, Any]]:
    return SOURCE_REFS[:limit]


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
    return _slug(metadata.get("domain") or "swimming_deep_research")


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
            "section_id": f"swimming_source_{_slug(ref_id)}",
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
            "section_id": f"swimming_section_{domain}",
            "section_title": domain.replace("_", " ").title(),
            "heading": "swimming_deep_research",
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
    if "beginner" in text or "learn" in text or "confidence" in text or "non-swimmer" in text:
        roles.append("beginner_swimmer")
    if "freestyle" in text or "front crawl" in text:
        roles.extend(["fitness_swimmer", "freestyle_sprinter"])
    if "sprint" in text or "50" in text or "100" in text:
        roles.append("freestyle_sprinter")
    if "distance" in text or "800" in text or "1500" in text:
        roles.append("distance_swimmer")
    if "middle" in text or "200" in text or "400" in text:
        roles.append("middle_distance_swimmer")
    if "backstroke" in text:
        roles.append("backstroke_swimmer")
    if "breaststroke" in text:
        roles.append("breaststroke_swimmer")
    if "butterfly" in text or "dolphin" in text:
        roles.append("butterfly_swimmer")
    if "medley" in text or " im " in f" {text} ":
        roles.append("im_swimmer")
    if "open water" in text:
        roles.append("open_water_swimmer")
    if "triathlon" in text:
        roles.append("triathlon_swimmer")
    if "masters" in text or "adult" in text:
        roles.append("masters_swimmer")
    if "youth" in text or "age group" in text:
        roles.append("youth_development")
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
    for index, draft in enumerate(drafts, start=171000):
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
                "id": f"swimming_section_{domain}",
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
                        "section_id": f"swimming_source_{_slug(ref.get('id') or ref.get('title'))}",
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
                        "id": f"swimming_deep_rule_{domain}_{field}_{_slug(item.get('id') or item.get('record_id') or title)}",
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
                        "id": f"swimming_deep_plan_{domain}_{field}_{_slug(item.get('id') or title)}",
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
                        "priority": 90 if field == "injury_or_load_risks" else 80,
                        "topics": _draft_tags(domain, field, item),
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
                    "id": f"swimming_deep_teach_{domain}_{level}_{_slug(item.get('id') or title)}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _draft_role_tags(domain, item),
                    "learning_goal": _summary_from_item(item),
                    "suitable_for": [f"{level} swimming users", "swimming sport skill training"],
                    "prerequisites": _dedupe(_text_items(item.get("prerequisites")))[:8] or _prerequisites("water_confidence_safety", level),
                    "teaching_priorities": _dedupe(_text_items([item.get("preferred_training"), item.get("summary"), item.get("recommendation")]))[:8],
                    "technical_focus": _dedupe(_text_items([item.get("progression"), item.get("quality_gates"), item.get("implementation_notes")]))[:8],
                    "tactical_focus": _dedupe(_text_items([item.get("implementation_examples"), item.get("backend_use")]))[:6],
                    "physical_support": _dedupe(_text_items([item.get("training_methods"), item.get("preferred_training")]))[:8],
                    "practice_design": _dedupe(_text_items([item.get("progression"), item.get("practice_design"), item.get("implementation_examples")]))[:8],
                    "typical_drills": _dedupe(_text_items([item.get("progression"), item.get("preferred_training")]))[:8],
                    "avoid_until_ready": _dedupe(_text_items(item.get("avoid")))[:8],
                    "progression_signals": _dedupe(_text_items(item.get("quality_gates") or item.get("assessment_signals")))[:8]
                    or _progression_signals("water_confidence_safety", level),
                    "coach_notes": _dedupe(_text_items([item.get("source_ids"), item.get("implementation_notes")]))[:6],
                    "retrieval_tags": _draft_tags(domain, "training_implications", item),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _refs_for_item(draft, item),
                }
            )
    return docs


def _deep_skill_assessments(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        technical_items = [item for item in draft.get("technical_models") or [] if isinstance(item, dict)]
        risk_items = [item for item in draft.get("injury_or_load_risks") or [] if isinstance(item, dict)]
        metrics = _dedupe(
            _text_items(
                [
                    [item.get("quality_markers") for item in technical_items],
                    [item.get("monitoring_flags") for item in risk_items],
                    [item.get("warning_signs") for item in risk_items],
                ]
            )
        )[:14]
        docs.append(
            {
                "id": f"swimming_deep_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _draft_role_tags(domain, {"domain": domain}),
                "summary": f"Assesses {domain.replace('_', ' ')} using technical quality, water safety, pacing or skill transfer, and 24-hour symptom response.",
                "metrics": metrics or _assessment_metrics("water_confidence_safety"),
                "level_bands": _default_level_bands(),
                "hold_if": _dedupe(_text_items([[item.get("warning_signs") for item in risk_items], [item.get("avoid") for item in draft.get("training_implications") or [] if isinstance(item, dict)]]))[:10],
                "retrieval_tags": _draft_tags(domain, "skill_assessment", {"metrics": metrics}),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _refs_for_item(draft, {"source_ids": _dedupe(_collect_source_ids(draft))[:8]}),
            }
        )
    return docs


def _sport_roles() -> List[Dict[str, Any]]:
    roles = {
        "beginner_swimmer": ("Beginner / Learn-To-Swim", "Needs water confidence, breathing, floating, gliding, and safe short swim progression before fitness volume."),
        "fitness_swimmer": ("Fitness Swimmer", "Uses swimming for health, conditioning, body composition, or hybrid-athlete support with technique and load control."),
        "freestyle_sprinter": ("Freestyle Sprinter", "Needs starts, turns, high-quality speed, power, and shoulder-safe short repeat work."),
        "middle_distance_swimmer": ("Middle-Distance Swimmer", "Balances pace skill, aerobic support, lactate tolerance, technique endurance, and controlled race-specific repeats."),
        "distance_swimmer": ("Distance Swimmer", "Needs efficient freestyle, aerobic durability, pacing, shoulder-load control, and conservative volume progression."),
        "im_swimmer": ("Individual Medley Swimmer", "Needs all four strokes, medley transitions, balanced stroke load, and event-specific technical endurance."),
        "open_water_swimmer": ("Open-Water Swimmer", "Needs sustained rhythm, sighting, drafting awareness, environmental safety, and open-water pacing."),
        "triathlon_swimmer": ("Triathlon Swimmer", "Needs efficient freestyle, sighting, open-water comfort, draft/pack awareness, and bike/run fatigue management."),
        "masters_swimmer": ("Masters Swimmer", "Needs adult-appropriate technique, load management, mobility, recovery, and realistic frequency."),
        "youth_development": ("Youth Development Swimmer", "Needs staged skill development, variety, safe starts/turns progression, and long-term athlete development."),
    }
    docs = []
    for role, (display_name, summary) in roles.items():
        docs.append(
            {
                "id": f"swimming_role_{role}",
                "sport": SPORT,
                "role": role,
                "display_name": display_name,
                "aliases": ROLE_EQUIVALENTS.get(role, []),
                "summary": summary,
                "responsibilities": {"domains": ROLE_DOMAIN_TAGS.get(role, []), "format": role},
                "skill_priorities": ROLE_DOMAIN_TAGS.get(role, []),
                "physical_demands": _role_demands(role),
                "risk_flags": _role_risks(role),
                "retrieval_tags": sorted(set([SPORT, role, *ROLE_EQUIVALENTS.get(role, []), *ROLE_DOMAIN_TAGS.get(role, [])])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _role_demands(role: str) -> List[str]:
    if role in {"freestyle_sprinter", "im_swimmer"}:
        return ["start power", "turn skill", "underwater quality", "shoulder durability", "trunk power"]
    if role in {"distance_swimmer", "open_water_swimmer", "triathlon_swimmer"}:
        return ["aerobic durability", "stroke economy", "breathing rhythm", "shoulder endurance"]
    if role == "beginner_swimmer":
        return ["water confidence", "breathing control", "low fatigue", "safety"]
    return ["stroke economy", "shoulder durability", "trunk control", "aerobic support"]


def _role_risks(role: str) -> List[str]:
    if role in {"beginner_swimmer"}:
        return ["panic_or_fear", "unsafe_breath_holding", "unsupervised_water"]
    if role in {"freestyle_sprinter", "im_swimmer"}:
        return ["shoulder_pain", "low_back_pain", "hypoxic_risk", "neck_back_load"]
    if role in {"breaststroke_swimmer"}:
        return ["knee_pain", "groin_pain", "low_back_pain"]
    return ["shoulder_pain", "yardage_spike", "technique_decay"]


def _sport_training_rules() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        docs.append(
            {
                "id": f"swimming_training_rule_{domain}",
                "sport": SPORT,
                "domain": domain,
                "category": "swimming_domain_rule",
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
        ("swimming_plan_safety_before_volume", "progression", "Water confidence, breathing, floating, and safe recovery must come before fitness volume for beginners or non-swimmers.", ["use short supervised skill progressions"], ["avoid long continuous swims for non-swimmers"], 98),
        ("swimming_plan_no_unsafe_hypoxic_work", "safety", "Do not prescribe prolonged breath-holding or hypoxic challenge sets; breath-control work must be conservative and safety-led.", ["teach relaxed exhalation and rhythmic breathing"], ["avoid max breath-holds and underwater endurance challenges"], 99),
        ("swimming_plan_shoulder_load_gate", "injury_risk", "Progress yardage, paddles, pull sets, and high-intensity repeats by shoulder, neck, back, and 24-hour symptom response.", ["track stroke volume and shoulder response"], ["avoid paddles or pull overload with shoulder pain"], 95),
        ("swimming_plan_stroke_specific_load", "injury_risk", "Breaststroke, butterfly, and heavy underwater work require stroke-specific load gates for knees/groin/back/shoulders.", ["bias technique and low volume when adding stroke complexity"], ["avoid high-volume butterfly or breaststroke kick with symptoms"], 92),
        ("swimming_plan_event_specificity", "sport_specificity", "Sprint, middle-distance, distance, IM, open-water, and triathlon swimming need different pace, rest, volume, technique, and dryland emphasis.", ["match programming to event role"], ["do not prescribe one generic swim set for all swimmers"], 88),
        ("swimming_plan_competition_week", "competition_week", "Before races or time trials, reduce new dryland soreness and junk yardage while preserving start/turn sharpness, rhythm, pace feel, and recovery.", ["use short race-specific quality and taper logic"], ["avoid new high-fatigue dryland or yardage spikes"], 86),
    ]
    return [
        {
            "id": rule_id,
            "sport": SPORT,
            "applies_to": [SPORT],
            "category": category,
            "rule": rule,
            "rule_text": rule,
            "recommended_action": recommended,
            "blocked_action": blocked,
            "priority": priority,
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        }
        for rule_id, category, rule, recommended, blocked, priority in rules
    ]


def _sport_profile(planning_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_swimming",
        "sport": SPORT,
        "planning_summary": "Swimming is a technical water sport where safety, breathing, stroke mechanics, water confidence, event specificity, starts/turns/underwaters, pacing, and shoulder/back/knee load management shape the plan.",
        "training_priorities": [
            "water confidence and safety before volume",
            "breathing rhythm and floating/gliding for beginners",
            "freestyle efficiency and body position",
            "stroke-specific development for backstroke, breaststroke, butterfly, and IM",
            "starts, turns, streamlines, and underwater phases when safe and relevant",
            "event-specific pacing for sprint, middle-distance, distance, open-water, and triathlon",
            "shoulder/scapular, trunk, thoracic, posterior-chain, and ankle/kick support",
            "yardage, intensity, tool, and stroke-specific load monitoring",
        ],
        "key_physical_qualities": [
            "aerobic durability",
            "stroke economy",
            "shoulder and scapular endurance",
            "trunk control",
            "thoracic mobility",
            "ankle mobility",
            "start and turn power",
            "breath control",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"pool_sessions": "2-3", "dryland_sessions": "1-2", "match_or_race": "none; skill-led"},
            "intermediate": {"pool_sessions": "3-5", "dryland_sessions": "2", "race_or_time_trial": "periodic"},
            "advanced": {"pool_sessions": "5-9", "dryland_sessions": "2-4", "race_or_time_trial": "periodized by event"},
        },
        "common_injury_or_load_risks": [
            "swimmer shoulder",
            "rotator cuff irritation",
            "neck irritation",
            "low-back pain",
            "breaststroke knee or groin symptoms",
            "yardage spike",
            "unsafe breath-holding",
        ],
        "do_not_pair": [
            "high paddle/pull volume with shoulder symptoms",
            "high butterfly volume with low-back or shoulder symptoms",
            "breaststroke kick volume with knee or groin pain",
            "max breath-holding with any fitness prescription",
            "heavy upper-body dryland immediately before key pool quality",
        ],
        "progression_guardrails": [
            "progress water safety before fitness volume",
            "progress continuous distance before intensity for beginners",
            "progress yardage before adding tools like paddles",
            "use 24-hour shoulder/back/knee/groin response before adding load",
            "match swim sets to event role and stroke ability",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs(),
    }


def _role_tags_for_domain(domain: str) -> List[str]:
    mapping = {
        "water_confidence_safety": ["all_roles", "beginner_swimmer"],
        "freestyle": ["all_roles", "fitness_swimmer", "freestyle_sprinter", "distance_swimmer", "triathlon_swimmer"],
        "backstroke": ["all_roles", "backstroke_swimmer", "im_swimmer"],
        "breaststroke": ["all_roles", "breaststroke_swimmer", "im_swimmer"],
        "butterfly": ["all_roles", "butterfly_swimmer", "im_swimmer"],
        "starts_turns_underwaters": ["all_roles", "freestyle_sprinter", "im_swimmer"],
        "event_programming": ["all_roles", "fitness_swimmer", "freestyle_sprinter", "middle_distance_swimmer", "distance_swimmer"],
        "open_water_triathlon": ["all_roles", "open_water_swimmer", "triathlon_swimmer"],
    }
    return mapping.get(domain, ["all_roles"])


def _teaching_progressions() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        for level in LEVELS:
            docs.append(
                {
                    "id": f"swimming_teach_{domain}_{level}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _role_tags_for_domain(domain),
                    "learning_goal": f"Develop swimming {domain.replace('_', ' ')} for a {level} user with safety, technique, and load gates.",
                    "suitable_for": [f"{level} swimmers", "swimming training"],
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
                        "Use safety and skill gates before adding volume, intensity, starts, underwaters, or stroke complexity.",
                        "Progress by 24-hour shoulder, back, neck, knee, groin, and fatigue response.",
                    ],
                    "retrieval_tags": sorted(set([SPORT, domain, level, *data["qualities"], *data["risk_flags"], *_role_tags_for_domain(domain)])),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _source_refs(),
                }
            )
    return docs


def _prerequisites(domain: str, level: str) -> List[str]:
    if level == "beginner":
        return ["safe supervised pool access", "can follow pool safety instructions", "no panic-level water fear"]
    if level == "intermediate":
        return ["can swim repeated short lengths", "breathing rhythm is stable", "no worsening symptoms from current swim load"]
    return ["consistent pool training", "event or stroke focus is known", "swim load and symptoms are tracked"]


def _teaching_priorities(domain: str, level: str) -> List[str]:
    base = {
        "beginner": ["safety", "breathing", "body position", "short successful repetitions"],
        "intermediate": ["efficiency", "pacing", "technical endurance", "controlled volume"],
        "advanced": ["event specificity", "race skills", "quality under fatigue", "load precision"],
    }
    return _dedupe([*base[level], *DOMAINS[domain]["qualities"][:3]])


def _technical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "water_confidence_safety": ["face immersion", "bubble exhalation", "floating", "gliding", "recovery to stand"],
        "freestyle": ["head position", "exhalation", "rotation", "catch path", "breathing timing"],
        "backstroke": ["head stillness", "hip height", "rotation", "arm timing", "wall awareness"],
        "breaststroke": ["pull-breath-kick-glide timing", "narrow kick", "hip/knee control", "streamline"],
        "butterfly": ["body wave", "dolphin kick", "catch and press", "breathing timing", "low fatigue volume"],
        "starts_turns_underwaters": ["streamline", "wall approach", "push-off alignment", "breakout timing", "safety gates"],
        "event_programming": ["pace control", "set intention", "rest intervals", "technique under fatigue"],
        "open_water_triathlon": ["sighting", "bilateral breathing", "sustained rhythm", "environmental safety"],
        "swimming_strength_conditioning": ["scapular control", "thoracic mobility", "trunk control", "posterior-chain support"],
        "injury_load_management": ["yardage tracking", "stroke-specific volume", "tool use", "symptom response"],
    }
    return mapping.get(domain, ["breathing", "body position", "safe progression"])


def _tactical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "event_programming": ["match pace to event", "protect technical quality", "use taper before competition"],
        "open_water_triathlon": ["sighting rhythm", "drafting awareness", "environmental safety decisions"],
        "starts_turns_underwaters": ["race-skill efficiency", "legal and safe underwater use", "breakout timing"],
    }
    if level == "advanced":
        return _dedupe([*mapping.get(domain, []), "event-specific adjustment", "race-day decision quality"])
    return mapping.get(domain, ["simple training purpose", "stop before safety or technique breaks"])


def _practice_design(domain: str, level: str) -> List[str]:
    mapping = {
        "water_confidence_safety": ["bubble breathing", "float and recover", "wall-supported glide", "short assisted swim"],
        "freestyle": ["side-kick breathing drill", "catch-up drill", "6-1-6 rotation drill", "short technique repeats"],
        "backstroke": ["body-line kick", "single-arm backstroke", "rotation drill", "wall-count awareness"],
        "breaststroke": ["kick on back", "pull-breath-kick-glide drill", "streamline glide", "low-volume skill repeats"],
        "butterfly": ["body dolphin", "single-arm fly", "kick timing drill", "very short quality repeats"],
        "starts_turns_underwaters": ["streamline push-off", "wall approach drill", "open turn drill", "breakout timing drill"],
        "event_programming": ["easy aerobic set", "pace-control repeats", "race-pace short repeats", "technique-plus-endurance set"],
        "open_water_triathlon": ["sighting every few strokes", "bilateral breathing practice", "continuous rhythm set", "open-water safety rehearsal"],
        "swimming_strength_conditioning": ["scapular control", "rotator cuff capacity", "trunk anti-extension", "medicine-ball rotation"],
        "injury_load_management": ["load diary", "reduced-volume technique day", "return-to-swim stage testing"],
    }
    return mapping.get(domain, ["short skill repeats", "safe easy swimming"])


def _avoid_until_ready(domain: str, level: str) -> List[str]:
    avoid = ["pain that changes stroke mechanics", "breath-holding challenges", "unsupervised unsafe water context"]
    if level == "beginner":
        avoid.extend(["long continuous swims", "race starts", "underwater endurance sets", "high-intensity intervals"])
    if domain in {"starts_turns_underwaters"}:
        avoid.extend(["diving starts without pool depth/supervision/skill clearance", "hypoxic underwater sets"])
    if domain in {"butterfly", "swimming_strength_conditioning"}:
        avoid.extend(["high-volume butterfly or upper-body dryland with shoulder/back symptoms"])
    if domain == "breaststroke":
        avoid.append("high-volume breaststroke kick with knee or groin symptoms")
    return _dedupe(avoid)


def _progression_signals(domain: str, level: str) -> List[str]:
    signals = ["24-hour symptom response stable", "breathing remains controlled", "technique does not collapse under fatigue"]
    if level in {"intermediate", "advanced"}:
        signals.extend(["pace or stroke count is repeatable", "session purpose is clear"])
    if domain in {"starts_turns_underwaters", "event_programming"}:
        signals.append("race skill stays safe and legal")
    return signals


def _default_level_bands() -> List[Dict[str, Any]]:
    return [
        {
            "level": "beginner",
            "indicators": ["water confidence is developing", "breathing and floating are controlled", "short swims are safe"],
            "ready_for_next_when": ["can swim short repeats with recovery", "no panic or worsening symptoms", "pool safety is reliable"],
        },
        {
            "level": "intermediate",
            "indicators": ["basic stroke is repeatable", "can complete structured sets", "pacing and rest are understood"],
            "ready_for_next_when": ["can hold technique under moderate fatigue", "load response is stable", "stroke/event goals are clear"],
        },
        {
            "level": "advanced",
            "indicators": ["event-specific pace and race skills are trained", "load is tracked", "recovery is managed"],
            "ready_for_next_when": ["competition transfer and recovery are reliable"],
        },
    ]


def _skill_assessments() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain in DOMAINS:
        docs.append(
            {
                "id": f"swimming_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _role_tags_for_domain(domain),
                "summary": f"Assesses swimming {domain.replace('_', ' ')} through safety, technical quality, pacing or skill transfer, and load response.",
                "metrics": _assessment_metrics(domain),
                "level_bands": _default_level_bands(),
                "hold_if": [
                    "panic, unsafe breath-holding, or unsafe water behavior appears",
                    "shoulder, back, neck, knee, groin, or fatigue symptoms worsen",
                    "stroke mechanics collapse under normal planned volume",
                    "yardage, tool, stroke, or intensity load spikes too quickly",
                ],
                "retrieval_tags": sorted(set([SPORT, domain, "assessment", *_assessment_metrics(domain)])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _assessment_metrics(domain: str) -> List[str]:
    base = ["technical consistency", "breathing control", "24-hour symptom response", "session completion"]
    specific = {
        "water_confidence_safety": ["face immersion comfort", "float and recover", "safe pool behavior"],
        "freestyle": ["body line", "breathing timing", "stroke economy", "shoulder response"],
        "backstroke": ["hip height", "rotation", "wall awareness"],
        "breaststroke": ["kick timing", "glide efficiency", "knee/groin response"],
        "butterfly": ["body wave timing", "shoulder/back response", "short-repeat quality"],
        "starts_turns_underwaters": ["streamline quality", "turn safety", "breakout timing"],
        "event_programming": ["pace control", "rest compliance", "technique under fatigue"],
        "open_water_triathlon": ["sighting rhythm", "open-water comfort", "continuous rhythm"],
        "injury_load_management": ["symptom trend", "yardage tolerance", "tool/stroke response"],
    }
    return _dedupe([*specific.get(domain, []), *base])


def _level_transition_rules() -> List[Dict[str, Any]]:
    return [
        {
            "id": "swimming_beginner_to_intermediate",
            "sport": SPORT,
            "from_level": "beginner",
            "to_level": "intermediate",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "4+ weeks or 8+ completed safe swim sessions",
                "can breathe rhythmically and recover safely",
                "can complete repeated short swims without panic",
                "no worsening shoulder, back, neck, knee, groin, or fatigue symptoms",
            ],
            "promote_when": ["short swim repeats are controlled", "water safety is reliable", "technique remains stable at easy effort"],
            "hold_when": ["unsafe breath holding", "panic/fear disrupts safety", "pain trend worsens", "volume causes symptoms"],
            "backend_action": "Unlock structured aerobic sets, technique-plus-endurance work, and low-volume pace control.",
            "retrieval_tags": ["swimming", "beginner", "intermediate", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "swimming_intermediate_to_advanced",
            "sport": SPORT,
            "from_level": "intermediate",
            "to_level": "advanced",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "8+ additional weeks or 16+ completed sessions",
                "stroke or event focus is known",
                "can hold technique under moderate fatigue",
                "yardage, intensity, and dryland load are tolerated",
            ],
            "promote_when": ["event-specific pace is repeatable", "race skills are safe", "load and recovery trends are stable"],
            "hold_when": ["unresolved shoulder/back/knee/groin symptoms", "technique collapse persists", "load response is poor"],
            "backend_action": "Unlock event-specific race pace, starts/turns/underwaters, and advanced dryland with load gates.",
            "retrieval_tags": ["swimming", "intermediate", "advanced", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "swimming_hold_or_regress",
            "sport": SPORT,
            "from_level": "any",
            "to_level": "hold_or_regress",
            "applies_to": ["all_roles"],
            "minimum_evidence": ["safety, pain, fatigue, completion, or water-confidence risk"],
            "promote_when": [],
            "hold_when": [
                "unsafe breath-holding or panic appears",
                "shoulder, neck, back, knee, groin, or fatigue symptoms worsen",
                "yardage or tool progression is not tolerated",
                "pool safety or supervision context is unclear for beginner skills",
            ],
            "backend_action": "Bias next block toward safety, technique, reduced volume, symptom-gated progression, and simple dryland support.",
            "retrieval_tags": ["swimming", "regression", "return_to_swim", "safety"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
    ]


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs = []
    for index, domain in enumerate(DOMAINS, start=170001):
        docs.append(
            {
                "id": f"swimming_section_{domain}",
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


def _merge_by_id(*record_groups: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for records in record_groups:
        for record in records:
            record_id = record.get("id")
            if record_id:
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
                "title": "SFTC Swimming Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing swimming teaching, safety, stroke, event programming, S&C, injury, and level progression records.",
                "evidence_rank": 80,
                "source_refs": SOURCE_REFS,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Swimming Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized swimming knowledge pack for retrieval and AI workout generation.",
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
    SWIMMING_DIR.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Convert swimming research into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

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
CYCLING_DIR = PROJECT_ROOT / "backend" / "sport_research" / "cycling"
OUTPUT_PATH = CYCLING_DIR / "cycling_teaching_database.json"
DRAFT_DIR = CYCLING_DIR / "drafts"

SOURCE_PACK_ID = "cycling_teaching_database_v1"
INGESTION_METHOD = "cycling_research_structured_converter_v1"
SPORT = "cycling"
LEVELS = ["beginner", "intermediate", "advanced"]


SOURCE_REFS: List[Dict[str, Any]] = [
    {
        "title": "UCI Disciplines",
        "url": "https://www.uci.org/disciplines/all/2tLnZMo6WrUBplRXDxyEi7",
        "source_type": "official_international_federation",
        "organization_or_author": "Union Cycliste Internationale",
        "notes": "Used for cycling discipline taxonomy and competition context.",
    },
    {
        "title": "USA Cycling Resources",
        "url": "https://usacycling.org/resources",
        "source_type": "official_federation_resources",
        "organization_or_author": "USA Cycling",
        "notes": "Used for rider development, rules, safety, racing, and coaching context.",
    },
    {
        "title": "British Cycling Knowledge",
        "url": "https://www.britishcycling.org.uk/knowledge",
        "source_type": "official_federation_education",
        "organization_or_author": "British Cycling",
        "notes": "Used for cycling training intensity, skills, and rider education.",
    },
    {
        "title": "National Standard for Cycle Training",
        "url": "https://www.gov.uk/government/publications/national-standard-for-cycle-training",
        "source_type": "government_cycle_training_standard",
        "organization_or_author": "UK Department for Transport",
        "notes": "Used for beginner control, road-readiness, and safe skill progression.",
    },
    {
        "title": "NHTSA Bicycle Safety",
        "url": "https://www.nhtsa.gov/road-safety/bicycle-safety",
        "source_type": "government_safety_guidance",
        "organization_or_author": "National Highway Traffic Safety Administration",
        "notes": "Used for bike checks, helmet, visibility, predictability, and traffic safety.",
    },
    {
        "title": "CDC Adult Physical Activity Guidelines",
        "url": "https://www.cdc.gov/physical-activity-basics/guidelines/adults.html",
        "source_type": "public_health_guideline",
        "organization_or_author": "Centers for Disease Control and Prevention",
        "notes": "Used for general fitness and activity-dose framing.",
    },
    {
        "title": "World Triathlon Competition Rules",
        "url": "https://triathlon.org/documents/competition-rules",
        "source_type": "official_rules_repository",
        "organization_or_author": "World Triathlon",
        "notes": "Used for triathlon cycling context, draft-legal rules, and competition planning.",
    },
    {
        "title": "TrainingPeaks Power Training Levels",
        "url": "https://www.trainingpeaks.com/blog/power-training-levels/",
        "source_type": "endurance_coaching_reference",
        "organization_or_author": "TrainingPeaks",
        "notes": "Used for FTP-relative power-zone language and threshold-based programming context.",
    },
]


DOMAINS: Dict[str, Dict[str, Any]] = {
    "beginner_confidence_safety": {
        "summary": "Beginner cycling starts with bike checks, mounting, starting, stopping, braking, turning, shifting, scanning, signaling, quiet-route exposure, and confidence before speed or intensity.",
        "qualities": ["bike_control", "braking", "turning", "shifting", "route_safety", "confidence"],
        "risk_flags": ["traffic_stress", "poor_braking", "low_visibility", "beginner_crash_risk"],
    },
    "endurance_power_programming": {
        "summary": "Cycling endurance and power planning uses RPE, heart rate, power, FTP/threshold, cadence, terrain, fueling, and recovery response to progress easy endurance, tempo, threshold, VO2, sprint, and long-ride work.",
        "qualities": ["aerobic_base", "tempo", "threshold", "vo2max", "sprint_power", "cadence"],
        "risk_flags": ["intensity_stack", "under_fueling", "fatigue_accumulation", "poor_recovery"],
    },
    "bike_handling_safety": {
        "summary": "Bike handling covers braking, cornering, descending, climbing, gear choice, cadence, group riding, predictable behavior, hazard scanning, and wet or loose-surface control.",
        "qualities": ["bike_handling", "cornering", "descending", "group_riding", "hazard_awareness"],
        "risk_flags": ["wheel_overlap", "high_speed_descending", "wet_surface", "mechanical_failure"],
    },
    "discipline_tactics": {
        "summary": "Cycling tactics depend on discipline: road, criterium, time trial, track, MTB, gravel, cyclocross, BMX, and triathlon all use different terrain, drafting, pacing, positioning, and event-week decisions.",
        "qualities": ["discipline_specificity", "drafting", "positioning", "pacing", "terrain_decision", "race_iq"],
        "risk_flags": ["wrong_discipline_context", "drafting_rule_error", "route_mismatch", "race_week_overload"],
    },
    "road_criterium": {
        "summary": "Road and criterium riders need drafting, paceline skill, positioning, cornering, repeated accelerations, attack decisions, sprint timing, and terrain or wind awareness.",
        "qualities": ["drafting", "paceline", "cornering", "repeat_acceleration", "sprint_tactics"],
        "risk_flags": ["pack_crash_risk", "corner_fatigue", "over_chasing_attacks"],
    },
    "time_trial_triathlon": {
        "summary": "Time trial and triathlon cycling prioritize steady power, aerodynamic position tolerance, pacing discipline, fueling, route awareness, and run-after-bike management for triathletes.",
        "qualities": ["steady_power", "aero_position", "pacing", "fueling", "triathlon_transfer"],
        "risk_flags": ["low_back_pain", "neck_pain", "under_fueling", "over_biking_before_run"],
    },
    "mtb_gravel_cyclocross": {
        "summary": "MTB, gravel, and cyclocross combine endurance with surface handling, traction, line choice, braking, climbing, descending, dismount/remount, carrying, and repeated anaerobic surges.",
        "qualities": ["traction", "line_choice", "off_road_handling", "repeat_surge", "trunk_control"],
        "risk_flags": ["crash_risk", "loose_surface", "grip_fatigue", "technical_descending"],
    },
    "track_bmx_power": {
        "summary": "Track sprint, track endurance, and BMX contexts require event-specific starts, acceleration, sprint power, cadence, tactics, long rests, and high-quality efforts rather than generic endurance volume.",
        "qualities": ["start_power", "acceleration", "neuromuscular_power", "high_cadence", "tactical_speed"],
        "risk_flags": ["max_sprint_too_early", "crash_risk", "high_power_fatigue"],
    },
    "injury_snc_bike_fit_load": {
        "summary": "Cycling load and S&C management tracks knee, low-back, neck, shoulder, hand, saddle, calf/Achilles, bike-fit, crash, contact-point, cadence, intensity, and weekly duration response.",
        "qualities": ["bike_fit", "load_management", "trunk_endurance", "hip_strength", "postural_capacity"],
        "risk_flags": ["knee_pain", "low_back_pain", "neck_pain", "hand_numbness", "saddle_discomfort"],
    },
    "level_progression": {
        "summary": "Cycling level is contextual: indoor, outdoor road, group riding, MTB/off-road, racing, and triathlon readiness may differ. Advancement needs completion, handling, pain stability, recovery, and appropriate data literacy.",
        "qualities": ["level_assessment", "handling_readiness", "aerobic_readiness", "discipline_readiness", "pain_stability"],
        "risk_flags": ["fitness_without_handling", "advancing_with_pain", "context_mismatch"],
    },
}


ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "road_cyclist": ["road", "road_rider", "road_racer"],
    "criterium_racer": ["criterium", "crit_racer", "crit"],
    "time_trialist": ["time_trial", "tt", "tt_rider"],
    "track_sprinter": ["track_sprint", "sprinter", "track_cyclist"],
    "track_endurance": ["track_endurance_rider", "track_cyclist"],
    "mountain_biker": ["mtb", "mountain_bike", "xc", "trail_rider"],
    "gravel_cyclist": ["gravel", "gravel_rider"],
    "cyclocross_rider": ["cyclocross", "cx"],
    "bmx_racer": ["bmx", "bmx_racing"],
    "triathlon_cyclist": ["triathlon", "triathlete"],
    "commuter_cyclist": ["commuter", "commuting"],
    "fitness_cyclist": ["fitness", "recreational_cyclist", "beginner_cyclist"],
}


ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "road_cyclist": ["road_criterium", "endurance_power_programming", "bike_handling_safety", "discipline_tactics"],
    "criterium_racer": ["road_criterium", "discipline_tactics", "bike_handling_safety", "track_bmx_power"],
    "time_trialist": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "track_sprinter": ["track_bmx_power", "discipline_tactics", "injury_snc_bike_fit_load"],
    "track_endurance": ["track_bmx_power", "endurance_power_programming", "discipline_tactics"],
    "mountain_biker": ["mtb_gravel_cyclocross", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "gravel_cyclist": ["mtb_gravel_cyclocross", "endurance_power_programming", "discipline_tactics"],
    "cyclocross_rider": ["mtb_gravel_cyclocross", "track_bmx_power", "discipline_tactics"],
    "bmx_racer": ["track_bmx_power", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "triathlon_cyclist": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "commuter_cyclist": ["beginner_confidence_safety", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "fitness_cyclist": ["beginner_confidence_safety", "endurance_power_programming", "level_progression"],
}


def _dedupe(items: Iterable[Any]) -> List[Any]:
    output: List[Any] = []
    seen = set()
    for item in items:
        if item in (None, "", [], {}):
            continue
        key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


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
        "payload_seed",
        "backend_use",
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


def _draft_domain(draft: Dict[str, Any]) -> str:
    metadata = draft.get("metadata") or {}
    return _slug(metadata.get("domain") or "cycling_deep_research")


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
            "section_id": f"cycling_source_{_slug(ref_id)}",
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
            "section_id": f"cycling_section_{domain}",
            "section_title": domain.replace("_", " ").title(),
            "heading": "cycling_deep_research",
        }
    ]


def _draft_role_tags(domain: str, item: Mapping[str, Any]) -> List[str]:
    text = " ".join(_text_items([domain, item])).lower()
    roles = ["all_roles"]
    for role, equivalents in ROLE_EQUIVALENTS.items():
        if role in text or any(equivalent in text for equivalent in equivalents):
            roles.append(role)
    if "beginner" in text or "learn" in text or "commuter" in text or "fitness" in text:
        roles.extend(["fitness_cyclist", "commuter_cyclist"])
    if "road" in text or "paceline" in text:
        roles.append("road_cyclist")
    if "criterium" in text or "crit" in text:
        roles.append("criterium_racer")
    if "time trial" in text or "aero" in text:
        roles.append("time_trialist")
    if "triathlon" in text:
        roles.append("triathlon_cyclist")
    if "mountain" in text or "mtb" in text:
        roles.append("mountain_biker")
    if "gravel" in text:
        roles.append("gravel_cyclist")
    if "cyclocross" in text or " cx " in f" {text} ":
        roles.append("cyclocross_rider")
    if "bmx" in text:
        roles.append("bmx_racer")
    if "track" in text and "sprint" in text:
        roles.append("track_sprinter")
    elif "track" in text:
        roles.append("track_endurance")
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


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs = []
    for index, domain in enumerate(DOMAINS, start=180001):
        data = DOMAINS[domain]
        docs.append(
            {
                "id": f"cycling_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe([SPORT, domain, *data["qualities"], *data["risk_flags"]]),
                "summary": data["summary"],
                "source_refs": _source_refs(),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _deep_source_sections(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs: List[Dict[str, Any]] = []
    for index, draft in enumerate(drafts, start=181000):
        domain = _draft_domain(draft)
        fields = [
            "key_concepts",
            "technical_models",
            "tactical_rules",
            "physical_demands",
            "injury_or_load_risks",
            "training_implications",
            "backend_records_to_create",
        ]
        field_counts = {key: len(draft.get(key) or []) for key in fields}
        docs.append(
            {
                "id": f"cycling_section_{domain}",
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
                        "section_id": f"cycling_source_{_slug(ref.get('id') or ref.get('title'))}",
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


def _sport_roles() -> List[Dict[str, Any]]:
    roles = {
        "road_cyclist": ("Road Cyclist", "Needs endurance, drafting, paceline, climbing, descending, wind, positioning, and sprint or attack decisions."),
        "criterium_racer": ("Criterium Racer", "Needs cornering, repeat accelerations, pack positioning, sprint timing, and crash-risk management."),
        "time_trialist": ("Time Trialist", "Needs steady power, aero-position tolerance, pacing, fueling, and low-variability output."),
        "track_sprinter": ("Track Sprinter", "Needs starts, maximal acceleration, high cadence, tactical sprinting, and long-rest power quality."),
        "track_endurance": ("Track Endurance Rider", "Needs high-speed endurance, tactical positioning, repeated surges, and event-specific velodrome skill."),
        "mountain_biker": ("Mountain Biker", "Needs traction, line choice, climbing, descending, braking, trunk/grip endurance, and technical-terrain progression."),
        "gravel_cyclist": ("Gravel Cyclist", "Needs long endurance, surface variability, fueling, route risk management, pacing, and equipment decisions."),
        "cyclocross_rider": ("Cyclocross Rider", "Needs repeated surges, dismount/remount, carrying, mud/sand/grass handling, and race-rhythm skills."),
        "bmx_racer": ("BMX Racer", "Needs gate starts, sprint power, pumping, jumping, landing, cornering, and crash-risk management."),
        "triathlon_cyclist": ("Triathlon Cyclist", "Needs aero steady power, fueling, draft-rule awareness, and bike pacing that protects the run."),
        "commuter_cyclist": ("Commuter Cyclist", "Needs route safety, traffic awareness, visibility, repeat low-moderate load, and fatigue accounting."),
        "fitness_cyclist": ("Fitness Cyclist", "Needs repeatable easy/moderate rides, safe duration progression, basic handling, and strength support."),
    }
    docs = []
    for role, (display_name, summary) in roles.items():
        docs.append(
            {
                "id": f"cycling_role_{role}",
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
    if role in {"track_sprinter", "bmx_racer", "criterium_racer"}:
        return ["acceleration", "sprint power", "high cadence", "reactive handling", "long-rest quality"]
    if role in {"time_trialist", "triathlon_cyclist"}:
        return ["steady power", "aero tolerance", "fueling", "pacing", "postural endurance"]
    if role in {"mountain_biker", "gravel_cyclist", "cyclocross_rider"}:
        return ["terrain handling", "repeated surges", "trunk control", "grip endurance", "climbing"]
    if role in {"commuter_cyclist", "fitness_cyclist"}:
        return ["aerobic base", "bike control", "route safety", "contact-point tolerance"]
    return ["aerobic durability", "threshold power", "cadence", "bike handling", "fueling"]


def _role_risks(role: str) -> List[str]:
    if role in {"track_sprinter", "bmx_racer", "mountain_biker", "cyclocross_rider"}:
        return ["crash_risk", "high_power_fatigue", "wrist_shoulder_impact", "technical_handling_error"]
    if role in {"time_trialist", "triathlon_cyclist"}:
        return ["low_back_pain", "neck_pain", "hand_numbness", "under_fueling"]
    if role in {"commuter_cyclist", "fitness_cyclist"}:
        return ["traffic_stress", "saddle_discomfort", "knee_pain", "hidden_commute_fatigue"]
    return ["knee_pain", "low_back_pain", "crash_risk", "fatigue_accumulation"]


def _sport_training_rules() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        docs.append(
            {
                "id": f"cycling_training_rule_{domain}",
                "sport": SPORT,
                "domain": domain,
                "category": "cycling_domain_rule",
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
                        "id": f"cycling_deep_rule_{domain}_{field}_{_slug(item.get('id') or item.get('record_id') or title)}",
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
                                    item.get("backend_use"),
                                    item.get("training_notes"),
                                    item.get("preferred_training"),
                                    item.get("teaching_points"),
                                    item.get("progression_signal"),
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
    for draft in drafts:
        domain = _draft_domain(draft)
        for item in draft.get("backend_records_to_create") or []:
            if not isinstance(item, dict):
                continue
            record_type = str(item.get("record_type") or "")
            if record_type not in {"sport_training_rule", "sport_profile", "sport_role", "sport_skill_model"}:
                continue
            title = _title_from_item(item, f"{domain} backend record")
            docs.append(
                {
                    "id": f"cycling_deep_seed_rule_{domain}_{_slug(item.get('id') or item.get('name') or title)}",
                    "sport": SPORT,
                    "domain": domain,
                    "category": record_type,
                    "title": title,
                    "rule": _summary_from_item(item),
                    "summary": _summary_from_item(item),
                    "recommended_action": _dedupe(_text_items([item.get("payload_seed"), item.get("backend_use")]))[:8],
                    "blocked_action": [],
                    "applies_to": _draft_role_tags(domain, item),
                    "detail": item,
                    "retrieval_tags": _draft_tags(domain, "backend_records_to_create", item),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _refs_for_item(draft, item),
                }
            )
    return docs


def _planning_rules() -> List[Dict[str, Any]]:
    rules = [
        ("cycling_plan_safety_before_speed", "safety", "Beginner cycling must progress bike checks, braking, turning, shifting, scanning, signaling, and safe-route confidence before fast riding, traffic complexity, or group riding.", ["use protected or quiet routes", "teach control skills first"], ["avoid fast group rides before handling readiness"], 98),
        ("cycling_plan_route_complexity_counts_as_load", "load_management", "Traffic, hills, wind, rain, poor surface, darkness, and route novelty count as training stress and should reduce planned intensity.", ["adjust intensity by route risk"], ["avoid hard intervals on high-complexity beginner routes"], 94),
        ("cycling_plan_intensity_distribution", "programming", "Endurance cycling plans should separate easy endurance, tempo, threshold, VO2, sprint, and recovery work instead of turning every ride into hard middle-intensity work.", ["progress one intensity variable at a time"], ["avoid stacking threshold, VO2, sprints, and long rides without recovery"], 90),
        ("cycling_plan_contact_point_gate", "injury_risk", "Saddle, hand, neck, low-back, knee, calf, Achilles, or contact-point symptoms should gate duration, cadence, gearing, bike-fit review, and intensity progression.", ["use 24-hour symptom response"], ["do not increase duration with worsening symptoms"], 96),
        ("cycling_plan_discipline_specificity", "sport_specificity", "Road, criterium, time trial, track, MTB, gravel, cyclocross, BMX, and triathlon cycling require different power, handling, tactics, equipment, and event-week rules.", ["retrieve discipline-specific context"], ["avoid one generic cycling plan for all riders"], 88),
        ("cycling_plan_commute_counts", "load_management", "Commute rides count toward weekly aerobic and fatigue load, especially when routes are hilly, stressful, loaded with bags, or repeated daily.", ["include commute volume in athlete_state"], ["avoid ignoring commute fatigue"], 86),
        ("cycling_plan_triathlon_bike_run_transfer", "multi_sport", "Triathlon cycling should protect run quality by managing aero position, fueling, steady pacing, and total endurance stress.", ["coordinate bike sessions with run load"], ["avoid over-biking before key runs"], 86),
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


def _deep_planning_rules(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        for field in ("tactical_rules", "injury_or_load_risks", "training_implications", "backend_records_to_create"):
            for item in draft.get(field) or []:
                if not isinstance(item, dict):
                    continue
                record_type = str(item.get("record_type") or "")
                if field == "backend_records_to_create" and record_type not in {"planning_rule", "macro_plan_template", "sport_injury_load_rule"}:
                    continue
                title = _title_from_item(item, f"{domain} planning")
                category = str(item.get("category") or item.get("rule_category") or record_type or field).strip() or field
                docs.append(
                    {
                        "id": f"cycling_deep_plan_{domain}_{field}_{_slug(item.get('id') or item.get('name') or title)}",
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
                                    item.get("backend_use"),
                                    item.get("recommended_action"),
                                    item.get("preferred_training"),
                                    item.get("progression"),
                                    item.get("quality_gates"),
                                    item.get("payload_seed"),
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


def _sport_profile(planning_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_cycling",
        "sport": SPORT,
        "planning_summary": "Cycling is an equipment-mediated endurance, power, handling, safety, and tactical sport. Plans must account for bike control, route and terrain, cadence, FTP/HR/RPE, fueling, bike fit, contact-point symptoms, discipline, and competition or commute context.",
        "training_priorities": [
            "bike checks, braking, turning, shifting, and route safety for beginners",
            "easy aerobic base and long-ride progression",
            "cadence, gear choice, and efficient pedaling",
            "tempo, threshold, VO2, sprint, or climbing work only when readiness supports it",
            "discipline-specific tactics for road, criterium, TT, track, MTB, gravel, cyclocross, BMX, and triathlon",
            "S&C for trunk, hip, posterior chain, posture, neck/shoulder, lower limb, and contact-point tolerance",
            "fueling and hydration practice for longer or hotter rides",
            "bike-fit and pain-response monitoring",
        ],
        "key_physical_qualities": [
            "aerobic base",
            "threshold power",
            "VO2max",
            "sprint power",
            "cadence control",
            "trunk endurance",
            "hip and knee capacity",
            "postural tolerance",
            "bike handling",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"bike_sessions": "2-4", "strength_sessions": "1-2", "hard_sessions": "0-1 short controlled exposure"},
            "intermediate": {"bike_sessions": "3-5", "strength_sessions": "1-2", "hard_sessions": "1-2"},
            "advanced": {"bike_sessions": "4-7+", "strength_sessions": "1-3", "hard_sessions": "2-3 by block and discipline"},
        },
        "common_injury_or_load_risks": [
            "knee pain",
            "low-back pain",
            "neck pain",
            "hand numbness",
            "saddle discomfort",
            "calf or Achilles irritation",
            "crash risk",
            "under-fueling",
            "hidden commute fatigue",
        ],
        "do_not_pair": [
            "new rider plus fast group ride",
            "high-complexity route plus hard intervals",
            "worsening knee pain plus big-gear climbing",
            "low-back/neck symptoms plus long aero-position work",
            "long ride plus VO2/sprint stack without recovery",
            "commute-heavy week plus extra hard cycling volume",
        ],
        "progression_guardrails": [
            "progress handling before speed",
            "progress duration before intensity for beginners",
            "progress one of duration, intensity, hills, or technical route complexity at a time",
            "use 24-hour pain and contact-point response before increasing load",
            "match cycling session type to route, bike, discipline, and equipment context",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs(),
    }


def _role_tags_for_domain(domain: str) -> List[str]:
    roles = ["all_roles"]
    for role, domains in ROLE_DOMAIN_TAGS.items():
        if domain in domains:
            roles.append(role)
    if domain in {"beginner_confidence_safety", "level_progression"}:
        roles.extend(["fitness_cyclist", "commuter_cyclist"])
    return _dedupe(roles)


def _teaching_progressions() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        for level in LEVELS:
            docs.append(
                {
                    "id": f"cycling_teach_{domain}_{level}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": _role_tags_for_domain(domain),
                    "learning_goal": f"Develop cycling {domain.replace('_', ' ')} for a {level} rider with safe progression, clear route context, and load gates.",
                    "suitable_for": [f"{level} cyclists", "cycling training"],
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
                        "Route, terrain, bike, weather, traffic, and indoor/outdoor context change the session demand.",
                        "Use completion, RPE, symptoms, and handling confidence before progressing.",
                    ],
                    "retrieval_tags": sorted(set([SPORT, domain, level, *data["qualities"], *data["risk_flags"], *_role_tags_for_domain(domain)])),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _source_refs(),
                }
            )
    return docs


def _deep_teaching_progressions(drafts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for draft in drafts:
        domain = _draft_domain(draft)
        for field in ("technical_models", "training_implications", "backend_records_to_create"):
            for item in draft.get(field) or []:
                if not isinstance(item, dict):
                    continue
                record_type = str(item.get("record_type") or "")
                if field == "backend_records_to_create" and record_type not in {"sport_teaching_progression", "sport_skill_assessment", "sport_training_rule"}:
                    continue
                level = str(item.get("level") or "intermediate").lower()
                if level not in LEVELS:
                    level = "intermediate"
                title = _title_from_item(item, f"{domain} {level} teaching")
                docs.append(
                    {
                        "id": f"cycling_deep_teach_{domain}_{level}_{_slug(item.get('id') or item.get('name') or title)}",
                        "sport": SPORT,
                        "domain": domain,
                        "level": level,
                        "role_tags": _draft_role_tags(domain, item),
                        "learning_goal": _summary_from_item(item),
                        "suitable_for": [f"{level} cyclists", "cycling sport skill training"],
                        "prerequisites": _dedupe(_text_items(item.get("prerequisites")))[:8] or _prerequisites("beginner_confidence_safety", level),
                        "teaching_priorities": _dedupe(_text_items([item.get("preferred_training"), item.get("summary"), item.get("recommendation"), item.get("backend_use"), item.get("payload_seed")]))[:8],
                        "technical_focus": _dedupe(_text_items([item.get("stages"), item.get("progression"), item.get("quality_gates"), item.get("implementation_notes")]))[:8],
                        "tactical_focus": _dedupe(_text_items([item.get("implementation_examples"), item.get("backend_use"), item.get("tactical_context")]))[:6],
                        "physical_support": _dedupe(_text_items([item.get("training_methods"), item.get("preferred_training"), item.get("physical_quality")]))[:8],
                        "practice_design": _dedupe(_text_items([item.get("progression"), item.get("practice_design"), item.get("implementation_examples"), item.get("stages")]))[:8],
                        "typical_drills": _dedupe(_text_items([item.get("progression"), item.get("preferred_training"), item.get("stages")]))[:8],
                        "avoid_until_ready": _dedupe(_text_items(item.get("avoid")))[:8],
                        "progression_signals": _dedupe(_text_items(item.get("quality_gates") or item.get("assessment_signals") or item.get("progression_signal")))[:8] or _progression_signals("beginner_confidence_safety", level),
                        "coach_notes": _dedupe(_text_items([item.get("source_ids"), item.get("implementation_notes")]))[:6],
                        "retrieval_tags": _draft_tags(domain, field, item),
                        "source_pack_id": SOURCE_PACK_ID,
                        "source_refs": _refs_for_item(draft, item),
                    }
                )
    return docs


def _prerequisites(domain: str, level: str) -> List[str]:
    if level == "beginner":
        return ["safe bike and helmet", "traffic-free or quiet route option", "no worsening symptoms from current riding"]
    if level == "intermediate":
        return ["basic bike handling is reliable", "can complete easy rides without symptom spikes", "route context is known"]
    return ["consistent cycling history", "discipline or event context is known", "training load and symptoms are tracked"]


def _teaching_priorities(domain: str, level: str) -> List[str]:
    base = {
        "beginner": ["safety", "confidence", "easy endurance", "basic bike control"],
        "intermediate": ["structured progression", "cadence", "route-specific skill", "controlled intensity"],
        "advanced": ["discipline specificity", "power targeting", "race or event context", "recovery precision"],
    }
    return _dedupe([*base[level], *DOMAINS[domain]["qualities"][:3]])


def _technical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "beginner_confidence_safety": ["bike check", "mount and dismount", "braking", "turning", "shifting", "scanning"],
        "endurance_power_programming": ["RPE", "heart rate or power zones", "cadence", "long ride progression", "interval quality"],
        "bike_handling_safety": ["braking before turns", "cornering line", "descending control", "group predictability"],
        "discipline_tactics": ["discipline demands", "terrain", "wind", "drafting rules", "event context"],
        "road_criterium": ["drafting", "paceline", "cornering", "positioning", "sprint timing"],
        "time_trial_triathlon": ["steady power", "aero posture", "fueling", "route pacing", "bike-run transfer"],
        "mtb_gravel_cyclocross": ["traction", "line choice", "loose-surface braking", "dismount/remount", "surge tolerance"],
        "track_bmx_power": ["start mechanics", "max acceleration", "cadence", "power quality", "long rest"],
        "injury_snc_bike_fit_load": ["bike-fit flags", "symptom tracking", "trunk/hip support", "postural endurance"],
        "level_progression": ["handling readiness", "aerobic tolerance", "pain stability", "discipline context"],
    }
    return mapping.get(domain, ["safe progression", "ride quality", "symptom response"])


def _tactical_focus(domain: str, level: str) -> List[str]:
    mapping = {
        "discipline_tactics": ["choose tactics by discipline", "match effort to terrain", "respect event rules"],
        "road_criterium": ["conserve in draft", "position before corners", "avoid chasing every attack"],
        "time_trial_triathlon": ["hold steady power", "protect the run", "fuel before fatigue"],
        "mtb_gravel_cyclocross": ["choose line early", "respect traction", "pace surges"],
        "track_bmx_power": ["quality starts", "long rest", "speed without fatigue slop"],
    }
    if level == "advanced":
        return _dedupe([*mapping.get(domain, []), "event-specific decision quality", "competition-week adjustment"])
    return mapping.get(domain, ["simple route and session purpose", "stop if safety or technique breaks"])


def _practice_design(domain: str, level: str) -> List[str]:
    mapping = {
        "beginner_confidence_safety": ["bike check rehearsal", "start-stop drill", "controlled braking", "wide turns", "quiet-route ride"],
        "endurance_power_programming": ["easy endurance ride", "cadence changes", "tempo block", "threshold intervals", "recovery spin"],
        "bike_handling_safety": ["parking-lot cornering", "braking before turn", "descending on easy grade", "group etiquette practice"],
        "discipline_tactics": ["route analysis", "wind and terrain notes", "discipline-specific simulation", "event-week rehearsal"],
        "road_criterium": ["paceline practice", "corner exit acceleration", "short repeat accelerations", "sprint lead-in"],
        "time_trial_triathlon": ["steady power interval", "aero-position block", "fueling rehearsal", "brick context review"],
        "mtb_gravel_cyclocross": ["traction cornering", "short hill repeats", "dismount/remount practice", "technical route exposure"],
        "track_bmx_power": ["start practice", "short sprint", "full recovery", "cadence drill", "power-quality session"],
        "injury_snc_bike_fit_load": ["symptom diary", "trunk endurance", "hip strength", "posture mobility", "fit check prompts"],
        "level_progression": ["completion review", "handling assessment", "long-ride tolerance check", "pain trend review"],
    }
    return mapping.get(domain, ["easy ride", "safe skill practice"])


def _avoid_until_ready(domain: str, level: str) -> List[str]:
    avoid = ["worsening pain", "unsafe bike or route", "fatigue that disrupts handling"]
    if level == "beginner":
        avoid.extend(["fast group rides", "maximal sprints", "technical descents", "busy traffic routes"])
    if domain in {"track_bmx_power", "road_criterium"}:
        avoid.extend(["race-speed pack riding before handling readiness", "maximal sprinting without warmup and recovery"])
    if domain == "time_trial_triathlon":
        avoid.append("long aggressive aero-position blocks with low-back or neck pain")
    if domain == "mtb_gravel_cyclocross":
        avoid.append("technical descents or obstacles before control skills")
    return _dedupe(avoid)


def _progression_signals(domain: str, level: str) -> List[str]:
    signals = ["24-hour symptom response stable", "RPE stays near target", "handling remains calm and controlled"]
    if level in {"intermediate", "advanced"}:
        signals.extend(["session completion is consistent", "cadence or pacing is repeatable"])
    if domain in {"bike_handling_safety", "road_criterium", "mtb_gravel_cyclocross"}:
        signals.append("line, braking, and cornering remain predictable")
    if domain in {"endurance_power_programming", "time_trial_triathlon"}:
        signals.append("power, HR, or RPE response is repeatable")
    return _dedupe(signals)


def _default_level_bands() -> List[Dict[str, Any]]:
    return [
        {
            "level": "beginner",
            "indicators": ["basic bike control is developing", "rides are short and easy", "route complexity is low"],
            "ready_for_next_when": ["can ride 45-75 minutes easy", "handles braking/turning/shifting calmly", "no worsening symptoms"],
        },
        {
            "level": "intermediate",
            "indicators": ["easy rides are consistent", "some structured intensity is tolerated", "basic route or group skills are reliable"],
            "ready_for_next_when": ["tempo/threshold work is controlled", "discipline context is known", "recovery supports harder blocks"],
        },
        {
            "level": "advanced",
            "indicators": ["discipline-specific power and handling are trained", "load is tracked", "event context shapes sessions"],
            "ready_for_next_when": ["competition transfer and recovery are reliable"],
        },
    ]


def _skill_assessments() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain in DOMAINS:
        docs.append(
            {
                "id": f"cycling_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _role_tags_for_domain(domain),
                "summary": f"Assesses cycling {domain.replace('_', ' ')} through safety, ride quality, route fit, physical response, and discipline transfer.",
                "metrics": _assessment_metrics(domain),
                "level_bands": _default_level_bands(),
                "hold_if": [
                    "pain, contact-point symptoms, or fatigue worsen",
                    "handling becomes unsafe or unpredictable",
                    "route or weather complexity exceeds skill",
                    "RPE, HR, or power response is repeatedly above target",
                ],
                "retrieval_tags": sorted(set([SPORT, domain, "assessment", *_assessment_metrics(domain)])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
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
                    [item.get("progression_signal") for item in technical_items],
                ]
            )
        )[:14]
        docs.append(
            {
                "id": f"cycling_deep_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "role_tags": _draft_role_tags(domain, {"domain": domain}),
                "summary": f"Assesses {domain.replace('_', ' ')} using ride quality, cycling skill, discipline transfer, load response, and 24-hour symptom trends.",
                "metrics": metrics or _assessment_metrics("beginner_confidence_safety"),
                "level_bands": _default_level_bands(),
                "hold_if": _dedupe(_text_items([[item.get("warning_signs") for item in risk_items], [item.get("avoid") for item in draft.get("training_implications") or [] if isinstance(item, dict)]]))[:10],
                "retrieval_tags": _draft_tags(domain, "skill_assessment", {"metrics": metrics}),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _refs_for_item(draft, {"source_ids": _dedupe(_collect_source_ids(draft))[:8]}),
            }
        )
    return docs


def _assessment_metrics(domain: str) -> List[str]:
    base = ["session completion", "RPE control", "24-hour symptom response", "ride confidence"]
    specific = {
        "beginner_confidence_safety": ["braking", "turning", "shifting", "scanning", "route safety"],
        "endurance_power_programming": ["easy endurance duration", "cadence", "power or HR drift", "fueling"],
        "bike_handling_safety": ["line holding", "braking control", "cornering", "hazard awareness"],
        "discipline_tactics": ["discipline context", "terrain decision", "pacing", "event-week adjustment"],
        "road_criterium": ["drafting", "corner exit", "pack positioning", "repeat acceleration"],
        "time_trial_triathlon": ["steady power", "aero tolerance", "fueling", "bike-run protection"],
        "mtb_gravel_cyclocross": ["traction", "line choice", "technical control", "surge tolerance"],
        "track_bmx_power": ["start quality", "sprint power", "cadence", "full recovery"],
        "injury_snc_bike_fit_load": ["knee response", "low-back response", "neck/hand/saddle response", "fit flags"],
        "level_progression": ["completion rate", "handling readiness", "pain trend", "discipline readiness"],
    }
    return _dedupe([*specific.get(domain, []), *base])


def _level_transition_rules() -> List[Dict[str, Any]]:
    return [
        {
            "id": "cycling_beginner_to_intermediate",
            "sport": SPORT,
            "from_level": "beginner",
            "to_level": "intermediate",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "4+ weeks or 8+ completed cycling sessions",
                "85% planned completion",
                "can ride 45-75 minutes easy",
                "braking, turning, shifting, scanning, and route confidence are stable",
                "no worsening knee, low-back, neck, hand, saddle, calf, or Achilles symptoms",
            ],
            "promote_when": ["easy ride completion is repeatable", "handling is calm", "RPE stays in target", "symptom response is stable"],
            "hold_when": ["traffic or route anxiety remains high", "pain trend worsens", "handling is unsafe", "completion is inconsistent"],
            "backend_action": "Unlock structured endurance, cadence drills, mild hills, and limited tempo exposure while preserving handling and symptom gates.",
            "retrieval_tags": ["cycling", "beginner", "intermediate", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "cycling_intermediate_to_advanced",
            "sport": SPORT,
            "from_level": "intermediate",
            "to_level": "advanced",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "8+ additional weeks or 16+ completed rides",
                "long rides and tempo or threshold work are tolerated",
                "discipline or event context is known",
                "recovery supports harder blocks",
                "bike/equipment and route context support advanced work",
            ],
            "promote_when": ["structured intensity is controlled", "discipline-specific skill is reliable", "fueling/recovery is consistent"],
            "hold_when": ["pain or contact symptoms persist", "fatigue is high", "discipline-specific skill is not ready"],
            "backend_action": "Unlock discipline-specific VO2, sprint, threshold, race simulation, or technical terrain work with recovery and event-week gates.",
            "retrieval_tags": ["cycling", "intermediate", "advanced", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "cycling_hold_or_regress",
            "sport": SPORT,
            "from_level": "any",
            "to_level": "hold_or_regress",
            "applies_to": ["all_roles"],
            "minimum_evidence": ["pain, crash, high fatigue, low completion, unsafe handling, or long break"],
            "promote_when": [],
            "hold_when": [
                "pain, numbness, saddle symptoms, or fatigue worsen",
                "handling confidence drops",
                "completion below 65%",
                "illness, crash, or long break occurred",
            ],
            "backend_action": "Bias next block toward easier intensity, safer routes, reduced duration, skill rebuild, fit review, and S&C support.",
            "retrieval_tags": ["cycling", "regression", "return_to_ride", "safety"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
    ]


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
                "title": "SFTC Cycling Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing cycling teaching, endurance, power, safety, handling, discipline, tactics, S&C, injury, bike-fit, and level progression records.",
                "evidence_rank": 80,
                "source_refs": SOURCE_REFS,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Cycling Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized cycling knowledge pack for retrieval and AI workout generation.",
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
    CYCLING_DIR.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Convert cycling research into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()


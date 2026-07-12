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
BOXING_DIR = PROJECT_ROOT / "backend" / "sport_research" / "boxing"
DRAFT_DIR = BOXING_DIR / "drafts"
OUTPUT_PATH = BOXING_DIR / "boxing_teaching_database.json"

SOURCE_PACK_ID = "boxing_teaching_database_v1"
INGESTION_METHOD = "boxing_research_drafts_structured_converter_v1"
SPORT = "boxing"
LEVELS = ["beginner", "intermediate", "advanced"]

DOMAIN_DRAFTS: Dict[str, List[str]] = {
    "rules_competition": ["rules_ring_scoring_competition_draft.json"],
    "stance_guard": ["technical_fundamentals_draft.json", "boxing_level_teaching_draft.json"],
    "footwork_ringcraft": ["footwork_ringcraft_wave2_draft.json", "technical_fundamentals_draft.json"],
    "punch_mechanics": ["punch_mechanics_wave2_draft.json", "technical_fundamentals_draft.json"],
    "defense_countering": ["defense_countering_wave2_draft.json", "boxing_level_teaching_draft.json"],
    "style_archetypes": ["style_archetypes_wave2_draft.json", "tactical_iq_strategy_draft.json"],
    "tactical_iq": ["tactical_iq_strategy_draft.json", "style_archetypes_wave2_draft.json"],
    "southpaw_orthodox": ["southpaw_orthodox_matchups_wave2_draft.json"],
    "sparring_contact": ["sparring_fight_camp_wave2_draft.json", "boxing_level_teaching_draft.json"],
    "fight_camp": ["sparring_fight_camp_wave2_draft.json", "boxing_snc_injury_macro_planning_draft.json"],
    "boxing_strength_conditioning": [
        "boxing_snc_injury_macro_planning_draft.json",
        "sparring_fight_camp_wave2_draft.json",
    ],
}

ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "out_boxer": ["outboxer", "long_range", "outside_fighter", "all_roles"],
    "outboxer": ["out_boxer", "long_range", "outside_fighter", "all_roles"],
    "pressure_fighter": ["swarmer", "pressure", "inside_fighter", "all_roles"],
    "swarmer": ["pressure_fighter", "pressure", "inside_fighter", "all_roles"],
    "counterpuncher": ["counter_puncher", "counter", "all_roles"],
    "counter_puncher": ["counterpuncher", "counter", "all_roles"],
    "boxer_puncher": ["adaptive_style", "power_boxer", "all_roles"],
    "inside_fighter": ["pressure_fighter", "close_range", "all_roles"],
    "brawler_puncher": ["brawler", "puncher", "power_puncher", "all_roles"],
    "brawler": ["brawler_puncher", "puncher", "power_puncher", "all_roles"],
    "southpaw": ["left_handed", "opposite_stance", "all_roles"],
    "orthodox": ["right_handed", "opposite_stance", "all_roles"],
}

DOMAIN_LEVEL_GUIDANCE: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "stance_guard": {
        "beginner": {
            "technical_focus": ["stance width", "guard recovery", "balance after jab/cross", "safe reset"],
            "practice_design": ["mirror stance rounds", "step-slide with guard", "jab-cross-return drills"],
            "avoid_until_ready": ["high-speed combinations", "open sparring", "fatigue-first boxing circuits"],
        },
        "intermediate": {
            "technical_focus": ["stance recovery after combinations", "guard under pressure", "range-specific stance changes"],
            "practice_design": ["partner touch drills", "bag rounds with reset rules", "stance recovery after exits"],
            "avoid_until_ready": ["style-specific stance changes before base guard is stable"],
        },
        "advanced": {
            "technical_focus": ["stance manipulation by opponent", "ring-position-specific guard", "fight-camp specificity"],
            "practice_design": ["opponent-style rounds", "corner/rope escape constraints", "camp-specific guard plans"],
            "avoid_until_ready": ["high contact when readiness or head symptoms are poor"],
        },
    },
    "footwork_ringcraft": {
        "beginner": {
            "technical_focus": ["step-slide", "no crossing feet", "pivot basics", "exit after punching"],
            "practice_design": ["line drills", "cone pivots", "jab and exit rounds"],
            "avoid_until_ready": ["reactive cutting drills", "high-volume rope pressure"],
        },
        "intermediate": {
            "technical_focus": ["cutting off the ring", "angle exits", "pressure without chasing", "rope/corner escape"],
            "practice_design": ["constraint ringcraft rounds", "lead-foot battle drills", "angle after defense drills"],
            "avoid_until_ready": ["hard sparring as the only ringcraft test"],
        },
        "advanced": {
            "technical_focus": ["opponent-specific ring traps", "tempo control", "style-specific range denial"],
            "practice_design": ["scenario rounds by score/time", "style matchup rounds", "corner pressure simulations"],
            "avoid_until_ready": ["large footwork-volume spikes near fight week"],
        },
    },
    "punch_mechanics": {
        "beginner": {
            "technical_focus": ["jab mechanics", "cross mechanics", "hip-shoulder connection", "hand return"],
            "practice_design": ["shadowboxing skill rounds", "bag rounds with quality caps", "pad basics"],
            "avoid_until_ready": ["max-power bag rounds", "complex punch chains", "painful hand impact"],
        },
        "intermediate": {
            "technical_focus": ["hooks", "uppercuts", "body-head changes", "combination exits", "counter-ready recovery"],
            "practice_design": ["combo-with-exit rounds", "target-change pad work", "trigger-based counters"],
            "avoid_until_ready": ["power volume spikes with wrist/shoulder symptoms"],
        },
        "advanced": {
            "technical_focus": ["punch selection by opponent", "feint-to-shot chains", "late-round power quality"],
            "practice_design": ["opponent-specific pad rounds", "fight-camp power windows", "score-state shot selection"],
            "avoid_until_ready": ["high power and high contact stacked on poor recovery days"],
        },
    },
    "defense_countering": {
        "beginner": {
            "technical_focus": ["block", "parry", "small slips", "guard after defense", "exit after defense"],
            "practice_design": ["slow partner feeds", "defense-only rounds", "block-parry-exit drills"],
            "avoid_until_ready": ["open sparring", "blind reaction drills", "big defensive movements"],
        },
        "intermediate": {
            "technical_focus": ["defense-to-counter", "trigger recognition", "roll/slip by inches", "clinch reset rules"],
            "practice_design": ["constraint sparring", "trigger-counter rounds", "defense plus one counter drills"],
            "avoid_until_ready": ["counter exchanges without range margin"],
        },
        "advanced": {
            "technical_focus": ["baiting safely", "opponent-specific defensive maps", "counter timing under fatigue"],
            "practice_design": ["style-specific defensive rounds", "score/time scenario counters", "camp sparring themes"],
            "avoid_until_ready": ["contact when head symptoms or poor readiness are present"],
        },
    },
    "style_archetypes": {
        "beginner": {
            "technical_focus": ["broad skill base before style identity", "range awareness", "safe exits"],
            "practice_design": ["exploration rounds", "range control games", "jab/exit and guard reset"],
            "avoid_until_ready": ["locking into one style too early"],
        },
        "intermediate": {
            "technical_focus": ["preferred range", "style vulnerability patching", "style-specific conditioning"],
            "practice_design": ["out-boxer/pressure/counter constraints", "style-denial drills", "vulnerability rounds"],
            "avoid_until_ready": ["style blending without reliable base tools"],
        },
        "advanced": {
            "technical_focus": ["opponent style matchup", "style switching", "camp-specific tactical plan"],
            "practice_design": ["opponent archetype simulations", "score-state style changes", "sparring by matchup"],
            "avoid_until_ready": ["unmanaged total load across style, contact, and S&C"],
        },
    },
    "tactical_iq": {
        "beginner": {
            "technical_focus": ["simple scoring idea", "distance awareness", "what to do after punching"],
            "practice_design": ["one-task rounds", "coach-call shadowboxing", "score-and-exit games"],
            "avoid_until_ready": ["complex opponent reads"],
        },
        "intermediate": {
            "technical_focus": ["setups", "feints", "range traps", "round objective awareness"],
            "practice_design": ["scenario rounds", "constraint sparring", "trigger-based decision drills"],
            "avoid_until_ready": ["hard contact as the primary tactical teacher"],
        },
        "advanced": {
            "technical_focus": ["opponent analysis", "round-by-round adjustment", "fight plan adaptation"],
            "practice_design": ["video-linked tactics", "sparring with score states", "fight week tactical rehearsal"],
            "avoid_until_ready": ["tactical novelty in final taper"],
        },
    },
    "southpaw_orthodox": {
        "beginner": {
            "technical_focus": ["lead-foot awareness", "jab lane", "safe exit direction"],
            "practice_design": ["stance mirror drills", "lead-foot positioning games", "jab-and-exit"],
            "avoid_until_ready": ["advanced angle traps"],
        },
        "intermediate": {
            "technical_focus": ["outside foot battle", "rear-hand lane", "lead hook risk", "angle after exchange"],
            "practice_design": ["open-stance constraints", "rear-hand trigger rounds", "exit side rules"],
            "avoid_until_ready": ["full-speed open-stance sparring without defensive competence"],
        },
        "advanced": {
            "technical_focus": ["opposite-stance fight plans", "counter traps", "stance-specific ringcraft"],
            "practice_design": ["southpaw/orthodox matchup sparring", "opponent-specific lane denial", "score-state tactics"],
            "avoid_until_ready": ["large tactical changes close to competition"],
        },
    },
    "sparring_contact": {
        "beginner": {
            "technical_focus": ["no-contact or touch-contact awareness", "defense before contact", "symptom reporting"],
            "practice_design": ["partner touch drills", "technical feeds", "body-only constraints only when ready"],
            "avoid_until_ready": ["open sparring", "hard head contact", "ego-based rounds"],
        },
        "intermediate": {
            "technical_focus": ["controlled sparring", "defined task rounds", "contact intensity tracking"],
            "practice_design": ["constraint sparring", "technical sparring rounds", "post-round readiness check"],
            "avoid_until_ready": ["hard sparring stacked with heavy S&C"],
        },
        "advanced": {
            "technical_focus": ["sparring periodization", "opponent simulation", "fight-camp contact taper"],
            "practice_design": ["camp-phase sparring", "style-specific partner rounds", "planned deload/taper"],
            "avoid_until_ready": ["contact when symptoms, fatigue, or weight-cut stress are high"],
        },
    },
    "boxing_strength_conditioning": {
        "beginner": {
            "technical_focus": ["basic strength", "aerobic base", "shoulder/trunk control", "low-impact conditioning"],
            "practice_design": ["full-body S&C", "tempo intervals", "shoulder/scapular capacity"],
            "avoid_until_ready": ["max-effort fatigue circuits", "neck fatigue before contact"],
        },
        "intermediate": {
            "technical_focus": ["repeat power", "rotational power", "neck/trunk stiffness", "shoulder endurance"],
            "practice_design": ["power before fatigue", "interval conditioning by round demand", "sparring-load-aware S&C"],
            "avoid_until_ready": ["stacking hard sparring and high fatigue S&C"],
        },
        "advanced": {
            "technical_focus": ["camp-phase qualities", "specific power endurance", "load management by fight calendar"],
            "practice_design": ["phase-specific S&C", "fight-week taper", "post-fight restoration"],
            "avoid_until_ready": ["weight-cut-driven high intensity without readiness checks"],
        },
    },
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


def _source_refs_for_files(file_names: Sequence[str], limit: int = 10) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for file_name in file_names:
        draft = _load_draft(file_name)
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


def _source_refs_for_domain(domain: str, limit: int = 10) -> List[Dict[str, Any]]:
    return _source_refs_for_files(DOMAIN_DRAFTS.get(domain, []), limit=limit)


def _draft_domain(file_name: str) -> str:
    return file_name.replace("_draft.json", "").replace("_wave2", "")


def _item_id(item: Dict[str, Any], fallback: str) -> str:
    return _slug(item.get("id") or item.get("title") or item.get("name") or item.get("rule") or fallback)


def _item_title(item: Dict[str, Any], fallback: str) -> str:
    return str(item.get("title") or item.get("name") or item.get("id") or fallback).replace("_", " ").title()


def _item_summary(item: Dict[str, Any]) -> str:
    preferred = []
    for key in ("summary", "rule", "quality", "risk", "condition", "training_implication", "notes"):
        preferred.extend(_strings(item.get(key)))
    if preferred:
        return " ".join(_dedupe(preferred))[:900]
    return " ".join(_dedupe(_strings(item)))[:900]


def _expanded_role_tags(value: Any) -> List[str]:
    tags = ["all_roles"]
    for token in _strings(value):
        slug = _slug(token)
        if not slug:
            continue
        tags.append(slug)
        tags.extend(ROLE_EQUIVALENTS.get(slug, []))
    return sorted(set(tags))


def _role_domain_tags(role: str) -> List[str]:
    role = _slug(role)
    if role in {"out_boxer", "outboxer"}:
        return ["style_archetypes", "footwork_ringcraft", "punch_mechanics", "defense_countering", "tactical_iq"]
    if role in {"pressure_fighter", "swarmer", "inside_fighter"}:
        return ["style_archetypes", "footwork_ringcraft", "defense_countering", "sparring_contact", "boxing_strength_conditioning"]
    if role in {"counterpuncher", "counter_puncher"}:
        return ["style_archetypes", "defense_countering", "tactical_iq", "punch_mechanics"]
    if role in {"boxer_puncher", "brawler_puncher", "brawler"}:
        return ["style_archetypes", "punch_mechanics", "sparring_contact", "boxing_strength_conditioning"]
    return ["style_archetypes", "tactical_iq", "boxing_strength_conditioning"]


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs: List[Dict[str, Any]] = []
    for index, path in enumerate(sorted(DRAFT_DIR.glob("*_draft.json")), start=110001):
        draft = _load_draft(path.name)
        metadata = draft.get("metadata") or {}
        domain = _draft_domain(path.name)
        docs.append(
            {
                "id": f"boxing_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": metadata.get("domain") or domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe(
                    [
                        SPORT,
                        domain,
                        *_strings(metadata.get("agent_scope")),
                        *_strings(metadata.get("research_goal")),
                    ]
                )[:24],
                "summary": metadata.get("research_goal"),
                "draft_file": path.name,
                "source_refs": _source_refs_for_files([path.name], limit=12),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _sport_roles(drafts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    style_draft = drafts.get("style_archetypes_wave2_draft.json") or {}
    for item in style_draft.get("technical_models") or []:
        if not isinstance(item, dict) or not str(item.get("id", "")).startswith("boxing_style_"):
            continue
        role = _slug(str(item["id"]).replace("boxing_style_", ""))
        docs.append(
            {
                "id": f"boxing_role_{role}",
                "sport": SPORT,
                "role": role,
                "display_name": item.get("title") or role.replace("_", " ").title(),
                "aliases": ROLE_EQUIVALENTS.get(role, []),
                "summary": (
                    f"{item.get('title') or role.replace('_', ' ').title()} prefers {item.get('preferred_range', 'variable')} "
                    f"range and uses {item.get('initiative_mode', 'adaptive')} initiative. Tools: "
                    f"{', '.join(_strings(item.get('tools'))[:6])}."
                ),
                "responsibilities": {
                    "preferred_range": item.get("preferred_range"),
                    "initiative_mode": item.get("initiative_mode"),
                    "tools": item.get("tools") or [],
                    "vulnerabilities": item.get("risk_flags") or [],
                },
                "skill_priorities": _dedupe([*_strings(item.get("tools")), *_role_domain_tags(role)])[:18],
                "physical_demands": _strings(item.get("physical_demands")),
                "risk_flags": _strings(item.get("risk_flags")),
                "retrieval_tags": sorted(set([SPORT, role, *_expanded_role_tags(role), *_role_domain_tags(role)])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs_for_domain("style_archetypes"),
            }
        )
    return docs


def _sport_training_rules(drafts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    fields = [
        "key_concepts",
        "technical_models",
        "tactical_rules",
        "physical_demands",
        "injury_or_load_risks",
        "training_implications",
    ]
    for file_name, draft in drafts.items():
        domain = _draft_domain(file_name)
        for field in fields:
            for index, item in enumerate(draft.get(field) or [], start=1):
                if not isinstance(item, dict):
                    continue
                item_id = _item_id(item, f"{field}_{index}")
                summary = _item_summary(item)
                docs.append(
                    {
                        "id": f"boxing_training_rule_{domain}_{field}_{item_id}",
                        "sport": SPORT,
                        "domain": domain,
                        "category": field,
                        "condition": summary[:240],
                        "rule": summary,
                        "recommended_action": _dedupe(
                            [
                                *_strings(item.get("recommended_action")),
                                *_strings(item.get("summary")),
                                *_strings(item.get("quality")),
                                *_strings(item.get("rule")),
                            ]
                        )[:8],
                        "blocked_action": _dedupe(
                            [
                                *_strings(item.get("avoid")),
                                *_strings(item.get("risk")),
                                *_strings(item.get("do_not")),
                            ]
                        )[:8],
                        "source_pack_id": SOURCE_PACK_ID,
                        "source_refs": _source_refs_for_files([file_name], limit=8),
                        "retrieval_tags": sorted(set([SPORT, domain, field, item_id, *_strings(item)]))[:100],
                    }
                )
    return docs


def _planning_rules(training_rules: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    important_terms = {
        "sparring",
        "contact",
        "fight",
        "camp",
        "taper",
        "post_fight",
        "weight",
        "readiness",
        "injury",
        "risk",
        "symptom",
        "head",
        "hand",
        "wrist",
        "macro",
        "load",
        "competition",
    }
    for rule in training_rules:
        text = " ".join(_strings(rule)).lower()
        if not any(term in text for term in important_terms):
            continue
        docs.append(
            {
                "id": f"boxing_plan_{_slug(rule['id'].replace('boxing_training_rule_', ''))}",
                "sport": SPORT,
                "category": rule.get("category") or "boxing_planning",
                "applies_to": ["boxing", "combat_sports"],
                "priority": 92 if "head" in text or "symptom" in text or "contact" in text else 78,
                "rule": rule.get("rule"),
                "recommended_action": rule.get("recommended_action") or [],
                "blocked_action": rule.get("blocked_action") or [],
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": rule.get("source_refs") or [],
            }
        )
    return docs[:48]


def _sport_profile(planning_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_boxing",
        "sport": SPORT,
        "planning_summary": (
            "Boxing combines technical skill, tactical decision-making, ringcraft, contact management, "
            "repeat high-intensity efforts, rotational power, trunk/neck stiffness, shoulder endurance, "
            "hand/wrist durability, and careful sparring periodization."
        ),
        "training_priorities": [
            "stance, guard, balance, and safe recovery after every action",
            "footwork, ringcraft, range control, and exit quality",
            "jab/cross mechanics before complex combinations",
            "defense-to-counter skill before escalating contact",
            "style-specific tactical development only after fundamentals are stable",
            "aerobic base plus repeat punching/footwork conditioning",
            "rotational power, trunk stiffness, neck control, and shoulder/scapular endurance",
            "hand, wrist, shoulder, neck, and head-symptom load management",
            "sparring periodization and fight-week tapering for advanced users",
        ],
        "key_physical_qualities": [
            "aerobic capacity",
            "anaerobic repeat power",
            "rotational power",
            "neck and trunk stiffness",
            "shoulder and scapular endurance",
            "calf, ankle, and footwork capacity",
            "reaction speed",
            "hand and wrist robustness",
            "late-round technical repeatability",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"boxing_sessions": "2-4", "snc_sessions": "2-3", "sparring": "none or touch/contact prep only"},
            "intermediate": {"boxing_sessions": "3-5", "snc_sessions": "2-4", "sparring": "controlled and task-defined"},
            "advanced": {"boxing_sessions": "4-8", "snc_sessions": "2-4", "sparring": "periodized by fight-camp phase"},
        },
        "common_injury_or_load_risks": [
            "head trauma or concussion symptoms",
            "hand and wrist impact overload",
            "shoulder and scapular overuse",
            "neck overload",
            "low-back irritation from rotation and fatigue",
            "calf, ankle, and foot overuse from movement volume",
            "fatigue and dehydration from unsafe weight cutting",
        ],
        "do_not_pair": [
            "hard sparring with high-fatigue neck or rotational strength work",
            "hard head-contact sparring with poor sleep, headache, dizziness, or high stress",
            "high-volume power punching with hand, wrist, elbow, or shoulder symptoms",
            "large footwork volume spikes with calf, Achilles, ankle, or knee pain",
            "new tactical complexity during fight-week taper",
        ],
        "progression_guardrails": [
            "earn contact through defense, stance, guard recovery, and coach-controlled readiness",
            "progress skill complexity before sparring intensity",
            "track sparring rounds, contact intensity, symptoms, and hand/wrist pain in athlete state",
            "build aerobic base and repeatability before high-density fight conditioning",
            "reduce contact and volume during symptom, weight-cut, or poor-readiness periods",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules[:16]],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs_for_domain("boxing_strength_conditioning"),
    }


def _teaching_progressions() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, levels in DOMAIN_LEVEL_GUIDANCE.items():
        for level, guidance in levels.items():
            source_refs = _source_refs_for_domain(domain)
            technical_focus = guidance.get("technical_focus", [])
            practice_design = guidance.get("practice_design", [])
            avoid_until_ready = guidance.get("avoid_until_ready", [])
            docs.append(
                {
                    "id": f"boxing_teach_{domain}_{level}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": ["all_roles"],
                    "learning_goal": f"Develop boxing {domain.replace('_', ' ')} for a {level} athlete while protecting skill quality and contact safety.",
                    "suitable_for": [f"{level} boxing users", "boxing skill development"],
                    "prerequisites": (
                        ["basic stance and guard"] if level != "beginner" else ["no acute head symptoms", "pain-free basic movement"]
                    ),
                    "teaching_priorities": technical_focus[:6],
                    "technical_focus": technical_focus,
                    "tactical_focus": _dedupe(
                        [
                            domain.replace("_", " "),
                            "range control" if domain in {"footwork_ringcraft", "style_archetypes", "tactical_iq"} else "",
                            "contact safety" if domain in {"sparring_contact", "defense_countering"} else "",
                        ]
                    ),
                    "physical_support": _physical_support_for_domain(domain),
                    "practice_design": practice_design,
                    "typical_drills": practice_design,
                    "avoid_until_ready": avoid_until_ready,
                    "progression_signals": _progression_signals(domain, level),
                    "coach_notes": [
                        "Keep skill learning separated from exhaustion when teaching new actions.",
                        "Escalate contact only when defense, guard recovery, and symptom reporting are reliable.",
                    ],
                    "retrieval_tags": sorted(set([SPORT, domain, level, *_strings(technical_focus), *_strings(practice_design)])),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": source_refs,
                }
            )
    return docs


def _physical_support_for_domain(domain: str) -> List[str]:
    mapping = {
        "stance_guard": ["postural endurance", "trunk control", "shoulder/scapular endurance"],
        "footwork_ringcraft": ["calf/ankle capacity", "aerobic base", "deceleration", "hip control"],
        "punch_mechanics": ["rotational power", "trunk stiffness", "shoulder/scapular control", "hand/wrist capacity"],
        "defense_countering": ["reaction speed", "neck/trunk control", "leg endurance", "guard endurance"],
        "style_archetypes": ["style-specific conditioning", "movement repeatability", "power or endurance as needed"],
        "tactical_iq": ["decision quality under fatigue", "aerobic support", "repeat effort capacity"],
        "southpaw_orthodox": ["lead-leg positioning", "footwork capacity", "range control"],
        "sparring_contact": ["readiness", "neck/trunk robustness", "defense competence", "symptom monitoring"],
        "boxing_strength_conditioning": ["aerobic base", "repeat power", "rotational power", "neck/trunk/shoulder durability"],
    }
    return mapping.get(domain, ["boxing-specific movement quality"])


def _progression_signals(domain: str, level: str) -> List[str]:
    if level == "beginner":
        return [
            "keeps stance and guard after simple actions",
            "can explain the main safety rule for the drill",
            "no worsening pain or head symptoms after training",
        ]
    if level == "intermediate":
        return [
            "executes the skill against variable but controlled partner input",
            "maintains decision quality late in rounds",
            "recovers guard/range after successful and missed actions",
        ]
    return [
        "applies the skill against a specific style or fight scenario",
        "adjusts within the round without losing defensive responsibility",
        "tolerates planned camp load without symptom escalation",
    ]


def _skill_assessments() -> List[Dict[str, Any]]:
    domains = [
        "stance_guard",
        "footwork_ringcraft",
        "punch_mechanics",
        "defense_countering",
        "tactical_iq",
        "sparring_contact",
        "style_archetypes",
        "boxing_strength_conditioning",
    ]
    docs: List[Dict[str, Any]] = []
    for domain in domains:
        docs.append(
            {
                "id": f"boxing_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "summary": f"Assesses boxing {domain.replace('_', ' ')} through technical quality, tactical transfer, fatigue tolerance, and safety signals.",
                "metrics": _assessment_metrics(domain),
                "level_bands": [
                    {
                        "level": "beginner",
                        "indicators": ["can perform simple version without losing stance/guard", "uses safe reset", "no symptom escalation"],
                        "ready_for_next_when": ["stable basics across multiple sessions", "coach/user feedback shows reliable control"],
                    },
                    {
                        "level": "intermediate",
                        "indicators": ["handles variable cues", "links defense to response", "keeps quality under controlled fatigue"],
                        "ready_for_next_when": ["works under constraints without reckless contact", "shows repeatable tactical decisions"],
                    },
                    {
                        "level": "advanced",
                        "indicators": ["adapts by opponent/style/score state", "manages load and readiness", "executes in camp-specific context"],
                        "ready_for_next_when": ["maintains performance while respecting taper, contact, and recovery rules"],
                    },
                ],
                "hold_if": [
                    "headache, dizziness, visual symptoms, confusion, or worsening symptoms",
                    "worsening hand, wrist, shoulder, neck, or back pain",
                    "guard/stance collapses under basic fatigue",
                    "contact intensity exceeds technical readiness",
                ],
                "retrieval_tags": sorted(set([SPORT, domain, "assessment", *_assessment_metrics(domain)])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs_for_domain(domain),
            }
        )
    return docs


def _assessment_metrics(domain: str) -> List[str]:
    base = ["technical stability", "decision quality", "readiness response", "pain/symptom response"]
    mapping = {
        "stance_guard": ["stance balance", "guard recovery", "reset speed"],
        "footwork_ringcraft": ["range control", "angle exit quality", "rope/corner management"],
        "punch_mechanics": ["hand return", "hip-trunk connection", "impact tolerance"],
        "defense_countering": ["defense timing", "counter trigger recognition", "exit after defense"],
        "tactical_iq": ["round objective clarity", "trigger selection", "adjustment quality"],
        "sparring_contact": ["contact control", "symptom reporting", "coach rule compliance"],
        "style_archetypes": ["preferred range control", "style vulnerability patch", "style-denial response"],
        "boxing_strength_conditioning": ["repeat power", "aerobic recovery", "shoulder/neck/trunk capacity"],
    }
    return [*mapping.get(domain, []), *base]


def _level_transition_rules() -> List[Dict[str, Any]]:
    refs = _source_refs_for_domain("sparring_contact", limit=10)
    return [
        {
            "id": "boxing_beginner_to_intermediate",
            "sport": SPORT,
            "from_level": "beginner",
            "to_level": "intermediate",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "4+ weeks or 8+ completed boxing/S&C sessions",
                "stable stance, guard, step-slide, jab/cross, and simple defense",
                "no worsening head, hand, wrist, shoulder, neck, or back symptoms",
                "completion and RPE trends inside target range",
            ],
            "promote_when": [
                "can maintain basics under light fatigue",
                "can follow partner-drill safety rules",
                "can perform defense and safe exit before contact escalation",
            ],
            "hold_when": [
                "open sparring is requested before defense competency",
                "pain or symptoms worsen after bag, pad, or partner work",
                "stance/guard fails during basic combinations",
            ],
            "backend_action": "Recommend intermediate progression and unlock controlled partner/constraint drills, not hard open sparring.",
            "retrieval_tags": ["boxing", "beginner", "intermediate", "contact_gate", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": refs,
        },
        {
            "id": "boxing_intermediate_to_advanced",
            "sport": SPORT,
            "from_level": "intermediate",
            "to_level": "advanced",
            "applies_to": ["all_roles"],
            "minimum_evidence": [
                "8+ additional weeks or 16+ completed boxing/S&C sessions",
                "controlled sparring/contact history without symptom escalation",
                "can adjust tactics by range, style, and round objective",
                "conditioning supports technical quality late in rounds",
            ],
            "promote_when": [
                "style-specific tactics are reliable against live constraints",
                "load, sparring, and recovery are tracked",
                "advanced camp planning or opponent-specific work is appropriate",
            ],
            "hold_when": [
                "contact load is unmanaged",
                "head symptoms, hand pain, or recovery markers are poor",
                "user cannot maintain defensive responsibility under pressure",
            ],
            "backend_action": "Recommend advanced/opponent-specific planning and sparring periodization only with readiness controls.",
            "retrieval_tags": ["boxing", "intermediate", "advanced", "fight_camp", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": refs,
        },
        {
            "id": "boxing_contact_hold_or_regress",
            "sport": SPORT,
            "from_level": "any",
            "to_level": "hold_or_regress_contact",
            "applies_to": ["all_roles"],
            "minimum_evidence": ["any symptom or load-risk signal"],
            "promote_when": [],
            "hold_when": [
                "headache, dizziness, visual symptoms, confusion, or delayed symptom response",
                "worsening hand, wrist, shoulder, neck, or back pain",
                "poor sleep, high stress, hard weight-cut fatigue, or low readiness",
                "technical defense breaks down under light partner input",
            ],
            "backend_action": "Block contact escalation and bias retrieval toward skill, mobility, aerobic base, and non-contact S&C.",
            "retrieval_tags": ["boxing", "contact", "safety", "regression", "symptoms"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": refs,
        },
    ]


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


def build_database_payload() -> Dict[str, Any]:
    drafts = _all_drafts()
    training_rules = _sport_training_rules(drafts)
    planning_rules = _planning_rules(training_rules)
    collections = {
        "source_sections": _source_sections(),
        "sport_profiles": [_sport_profile(planning_rules)],
        "sport_roles": _sport_roles(drafts),
        "sport_training_rules": training_rules,
        "planning_rules": planning_rules,
        "sport_teaching_progressions": _teaching_progressions(),
        "sport_skill_assessments": _skill_assessments(),
        "sport_level_transition_rules": _level_transition_rules(),
    }
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
                "title": "SFTC Boxing Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing boxing teaching, tactical, safety, S&C, and level progression records generated from structured research drafts.",
                "evidence_rank": 80,
                "source_refs": _source_refs_for_files(sorted(drafts.keys()), limit=30),
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Boxing Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized boxing knowledge pack for retrieval and AI workout generation.",
                "source_refs": _source_refs_for_files(sorted(drafts.keys()), limit=30),
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
    parser = argparse.ArgumentParser(description="Convert boxing research drafts into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

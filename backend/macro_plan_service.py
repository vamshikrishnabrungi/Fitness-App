from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

logger = logging.getLogger(__name__)


SPORT_ALIASES = {
    "football": "soccer",
    "soccer": "soccer",
    "soccer_football": "soccer",
    "cricket": "cricket",
    "volleyball": "volleyball",
    "basketball": "basketball",
    "badminton": "badminton",
    "tennis": "tennis",
    "lawn_tennis": "tennis",
    "swimming": "swimming",
    "swim": "swimming",
    "swimmer": "swimming",
    "triathlon_swim": "swimming",
    "cycling": "cycling",
    "cycle": "cycling",
    "cyclist": "cycling",
    "bike": "cycling",
    "biking": "cycling",
    "road_cycling": "cycling",
    "mountain_biking": "cycling",
    "mountain_bike": "cycling",
    "mtb": "cycling",
    "gravel": "cycling",
    "cyclocross": "cycling",
    "bmx": "cycling",
    "triathlon_cycling": "cycling",
    "running": "running_endurance",
    "runner": "running_endurance",
    "endurance": "running_endurance",
    "marathon": "running_endurance",
    "mma": "mma",
    "mixed_martial_arts": "mma",
    "boxing": "boxing",
    "boxer": "boxing",
    "combat": "mma",
    "combat_sports": "mma",
    "kickboxing": "kickboxing",
    "kickboxer": "kickboxing",
    "k1": "kickboxing",
    "k_1": "kickboxing",
    "low_kick": "kickboxing",
    "point_fighting": "kickboxing",
    "light_contact": "kickboxing",
    "kick_light": "kickboxing",
    "fitness_kickboxing": "kickboxing",
    "wrestling": "wrestling",
    "wrestler": "wrestling",
    "folkstyle": "wrestling",
    "freestyle_wrestling": "wrestling",
    "greco": "wrestling",
    "greco_roman": "wrestling",
    "grappling": "mma",
}

FIELD_COURT_SPORTS = {"cricket", "volleyball", "soccer", "basketball", "badminton", "tennis"}
SPEED_POWER_SPORTS = {"cricket", "volleyball", "soccer", "basketball", "badminton", "tennis", "swimming", "cycling", "boxing", "mma", "kickboxing", "wrestling", "combat_sports"}


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _clean_list(value: Any) -> List[Any]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    return [item for item in items if item not in (None, "", [], {})]


def _normalize_sport(value: Any) -> Optional[str]:
    raw = _norm(value)
    if not raw:
        return None
    return SPORT_ALIASES.get(raw, raw)


def _profile_sports(profile: Dict[str, Any]) -> List[str]:
    sports: List[str] = []
    for sport in _clean_list(profile.get("sports")):
        normalized = _normalize_sport(sport)
        if normalized:
            sports.append(normalized)
    for detail in profile.get("sport_details") or []:
        if isinstance(detail, dict):
            normalized = _normalize_sport(detail.get("sport"))
            if normalized:
                sports.append(normalized)

    if not sports:
        goals = " ".join(str(goal).lower() for goal in _clean_list(profile.get("goals") or profile.get("selected_goals")))
        if "run" in goals or "endurance" in goals:
            sports.append("running_endurance")

    return sorted(set(sports))


def _sport_profile_lookup_values(sports: Sequence[str]) -> List[str]:
    values = set(sports)
    if "soccer" in values:
        values.add("soccer_football")
    return sorted(values)


def _profile_goals(profile: Dict[str, Any]) -> List[str]:
    goals = [str(goal) for goal in _clean_list(profile.get("selected_goals") or profile.get("goals"))]
    primary = profile.get("primary_goal")
    if primary and str(primary) not in goals:
        goals.insert(0, str(primary))
    return goals


def _level(profile: Dict[str, Any]) -> str:
    experience = _norm(profile.get("experience"))
    if experience in {"advanced", "elite"}:
        return "advanced"
    if experience in {"intermediate", "regular", "trained"}:
        return "intermediate"
    return "beginner"


def _season_phase(profile: Dict[str, Any]) -> str:
    phase = _norm(profile.get("season_phase"))
    if phase in {"in_season", "competition", "competitive", "match_season"}:
        return "in_season"
    if phase in {"pre_season", "preseason"}:
        return "pre_season"
    if phase in {"off_season", "offseason"}:
        return "off_season"
    return "general_preparation"


def _has_pain_or_injury(profile: Dict[str, Any]) -> bool:
    return bool(
        _clean_list(profile.get("pain_areas"))
        or _clean_list(profile.get("current_injuries"))
        or "injury" in " ".join(goal.lower() for goal in _profile_goals(profile))
    )


def _low_readiness(profile: Dict[str, Any]) -> bool:
    sleep = profile.get("sleep_avg_hours")
    stress = _norm(profile.get("stress_level"))
    try:
        if sleep is not None and float(sleep) < 6:
            return True
    except (TypeError, ValueError):
        pass
    return stress in {"high", "very_high"}


def _template_score(template: Dict[str, Any], profile: Dict[str, Any], sports: Sequence[str]) -> Tuple[int, List[str]]:
    template_id = template.get("id")
    goals = " ".join(goal.lower() for goal in _profile_goals(profile))
    level = _level(profile)
    phase = _season_phase(profile)
    has_pain = _has_pain_or_injury(profile)
    low_readiness = _low_readiness(profile)
    score = 0
    reasons: List[str] = []

    if template_id == "template_return_to_training_8w" and (has_pain or "return" in goals):
        score += 100
        reasons.append("pain_or_return_context")
    if template_id == "template_inseason_maintenance_24w" and phase == "in_season":
        score += 90
        reasons.append("in_season")
    if template_id == "template_beginner_foundation_24w" and (level == "beginner" or low_readiness):
        score += 85
        reasons.append("beginner_or_low_readiness")
    if template_id == "template_strength_base_24w" and any(term in goals for term in ["strength", "muscle", "performance"]):
        score += 55
        reasons.append("strength_base_goal")
    if template_id == "template_speed_agility_16w" and set(sports).intersection(FIELD_COURT_SPORTS):
        score += 45
        reasons.append("field_court_sport")
    if template_id == "template_power_conversion_12w" and level == "advanced" and set(sports).intersection(SPEED_POWER_SPORTS):
        score += 50
        reasons.append("advanced_speed_power_context")

    if has_pain and template_id not in {"template_return_to_training_8w", "template_beginner_foundation_24w"}:
        score -= 35
        reasons.append("pain_penalty")
    if level == "beginner" and template_id in {"template_power_conversion_12w", "template_speed_agility_16w"}:
        score -= 50
        reasons.append("beginner_complexity_penalty")

    return score, reasons


async def _select_template(db: Any, profile: Dict[str, Any], sports: Sequence[str]) -> Tuple[Dict[str, Any], List[str]]:
    templates = await db.macro_plan_templates.find({}).to_list(100)
    if not templates:
        raise RuntimeError("No macro plan templates available. Seed planning collections first.")

    ranked = []
    for template in templates:
        score, reasons = _template_score(template, profile, sports)
        ranked.append((score, reasons, template))
    ranked.sort(key=lambda item: (item[0], item[2].get("id", "")), reverse=True)
    return ranked[0][2], ranked[0][1]


def _week_bounds(weeks: Any) -> Tuple[int, int]:
    text = str(weeks or "").strip()
    numbers = [int(match) for match in re.findall(r"\d+", text)]
    if not numbers:
        return (1, 1)
    if len(numbers) == 1:
        return (numbers[0], numbers[0])
    return (numbers[0], numbers[1])


def _compact_sport_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": profile.get("id"),
        "sport": profile.get("sport"),
        "planning_summary": profile.get("planning_summary"),
        "key_physical_qualities": profile.get("key_physical_qualities") or [],
        "realistic_weekly_frequency": profile.get("realistic_weekly_frequency") or {},
        "common_injury_or_load_risks": profile.get("common_injury_or_load_risks") or [],
        "do_not_pair": profile.get("do_not_pair") or [],
        "progression_guardrails": profile.get("progression_guardrails") or [],
    }


async def _load_rules(db: Any, rule_ids: Sequence[str], sports: Sequence[str]) -> List[Dict[str, Any]]:
    filters: List[Dict[str, Any]] = []
    ids = sorted(set(rule_id for rule_id in rule_ids if rule_id))
    if ids:
        filters.append({"id": {"$in": ids}})
    applies_to = sorted(set([*sports, "all_sports"]))
    if applies_to:
        filters.append({"applies_to": {"$in": applies_to}})
    if not filters:
        return []
    rules = await db.planning_rules.find({"$or": filters}).sort("priority", -1).to_list(40)
    seen = set()
    unique_rules: List[Dict[str, Any]] = []
    for rule in rules:
        rule_id = rule.get("id")
        if rule_id in seen:
            continue
        seen.add(rule_id)
        unique_rules.append(rule)
    return unique_rules[:16]


async def _load_competition_rules(db: Any, sports: Sequence[str]) -> List[Dict[str, Any]]:
    if not sports:
        return []
    return await db.competition_week_rules.find({"applies_to": {"$in": list(sports)}}).to_list(20)


def _compact_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": rule.get("id"),
        "category": rule.get("category"),
        "rule": rule.get("rule"),
        "recommended_action": rule.get("recommended_action") or rule.get("recommended_focus") or [],
        "blocked_action": rule.get("blocked_action") or rule.get("blocked_actions") or [],
        "source_refs": rule.get("source_refs") or [],
    }


def _build_phases(template: Dict[str, Any], rules_by_id: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    phases: List[Dict[str, Any]] = []
    for index, phase in enumerate(template.get("phase_sequence") or [], start=1):
        start_week, end_week = _week_bounds(phase.get("weeks"))
        phases.append({
            "block": index,
            "phase": phase.get("phase"),
            "start_week": start_week,
            "end_week": end_week,
            "primary_goals": phase.get("primary_goals") or [],
            "gym_frequency": phase.get("gym_frequency"),
            "sport_frequency": phase.get("sport_frequency"),
            "progression_logic": phase.get("progression_logic"),
            "deload_logic": phase.get("deload_logic"),
            "linked_rules": [
                _compact_rule(rules_by_id[rule_id])
                for rule_id in template.get("linked_planning_rule_ids") or []
                if rule_id in rules_by_id
            ],
        })
    return phases


def _assumptions(profile: Dict[str, Any], sports: Sequence[str], sport_profiles: Sequence[Dict[str, Any]]) -> List[str]:
    assumptions = []
    if not profile.get("upcoming_events"):
        assumptions.append("No competition calendar supplied, so competition-week rules remain available but inactive.")
    if not profile.get("target_date"):
        assumptions.append("No target date supplied, so the macro plan uses the selected template length.")
    if not profile.get("sport_details"):
        assumptions.append("Sport roles or positions were not fully supplied; sport profiles are applied generally.")
    matched_sports = {
        normalized
        for doc in sport_profiles
        for normalized in [_normalize_sport(doc.get("sport"))]
        if normalized
    }
    missing = sorted(set(sports) - matched_sports)
    if missing:
        assumptions.append(f"No seeded sport profile found for: {', '.join(missing)}.")
    return assumptions


MACRO_TUNING_SYSTEM_PROMPT = """
You are SFTC's periodization editor. A rule-based engine has already selected an expert macro-cycle
template and its phase sequence. Your ONLY job is to TUNE that template to this specific athlete.

You MUST:
- Keep the same number of phases, the same phase names, and the same order.
- Keep the total duration identical: the last phase must end on the template's final week.
- Keep phases contiguous starting at week 1 (each phase starts the week after the previous ends).

You MAY:
- Shift block boundaries (start_week / end_week) to lengthen or shorten phases for this athlete.
- Refine each phase's primary_goals and add a short emphasis list tuned to the athlete's goal,
  sport demands, training level, season phase, and injuries.

Good tuning examples: longer accumulation for a beginner or injury history; longer max-strength for
a pure-strength goal; shorter early phases and a longer sport-specific bridge when a competition date
is near. Do not invent new phases or change the total length.

Return ONLY valid JSON. No markdown, no commentary.
"""


def _macro_tuning_enabled() -> bool:
    return (os.environ.get("MACRO_AI_TUNING", "true") or "true").strip().lower() in {"1", "true", "yes", "on"}


def _merge_tuned_phases(
    original: List[Dict[str, Any]],
    tuned: Any,
    duration_weeks: int,
) -> Optional[List[Dict[str, Any]]]:
    """Validate AI-tuned phases and merge boundaries/emphasis onto the rule-built phases.

    Returns None (caller falls back to rule-based phases) if the AI output violates any invariant:
    same count, same phase names/order, contiguous from week 1, and last phase ends on duration_weeks.
    """
    if not isinstance(tuned, list) or len(tuned) != len(original):
        return None
    merged: List[Dict[str, Any]] = []
    expected_start = 1
    for orig, t in zip(original, tuned):
        if not isinstance(t, dict):
            return None
        if str(t.get("phase", "")).strip().lower() != str(orig.get("phase", "")).strip().lower():
            return None
        try:
            start_week = int(t.get("start_week"))
            end_week = int(t.get("end_week"))
        except (TypeError, ValueError):
            return None
        if start_week != expected_start or end_week < start_week:
            return None
        new_phase = dict(orig)
        new_phase["start_week"] = start_week
        new_phase["end_week"] = end_week
        if t.get("primary_goals"):
            new_phase["primary_goals"] = _clean_list(t.get("primary_goals"))
        if t.get("emphasis"):
            new_phase["emphasis"] = _clean_list(t.get("emphasis"))
        if t.get("tuning_reason"):
            new_phase["tuning_reason"] = str(t.get("tuning_reason"))[:160]
        merged.append(new_phase)
        expected_start = end_week + 1
    if not merged or merged[-1]["end_week"] != duration_weeks:
        return None
    return merged


async def _ai_tune_phases(
    profile: Dict[str, Any],
    template: Dict[str, Any],
    phases: List[Dict[str, Any]],
    sport_profiles: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Hybrid macro: rules build the phase skeleton, the AI tunes boundaries/emphasis to the athlete.

    Fail-open: any missing key, AI error, or invalid output returns the original rule-based phases.
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not _macro_tuning_enabled() or not anthropic_key or not phases:
        return phases, {"tuned": False, "reason": "disabled_no_key_or_no_phases"}

    model = os.environ.get("MACRO_AI_MODEL") or os.environ.get("WORKOUT_AI_MODEL") or "claude-haiku-4-5-20251001"
    duration_weeks = int(phases[-1].get("end_week") or template.get("macro_length_weeks") or 0)
    if duration_weeks < len(phases):
        return phases, {"tuned": False, "reason": "invalid_duration"}

    payload = {
        "athlete": {
            "goals": _profile_goals(profile),
            "sports": _profile_sports(profile),
            "level": _level(profile),
            "season_phase": _season_phase(profile),
            "training_days_per_week": profile.get("training_days_per_week"),
            "session_duration_min": profile.get("session_duration_min"),
            "has_pain_or_injury": _has_pain_or_injury(profile),
            "target_date": profile.get("target_date"),
        },
        "selected_template": {"name": template.get("name"), "duration_weeks": duration_weeks},
        "current_phases": [
            {
                "block": p.get("block"),
                "phase": p.get("phase"),
                "start_week": p.get("start_week"),
                "end_week": p.get("end_week"),
                "primary_goals": p.get("primary_goals") or [],
            }
            for p in phases
        ],
        "sport_demands": [
            {
                "sport": sp.get("sport"),
                "key_qualities": (sp.get("key_qualities") or sp.get("physical_qualities") or [])[:5],
                "common_injuries": (sp.get("common_injuries") or [])[:4],
            }
            for sp in (sport_profiles or [])
        ][:3],
        "required_output_schema": {
            "phases": [
                {
                    "block": "int (unchanged)",
                    "phase": "str (unchanged name/order)",
                    "start_week": "int",
                    "end_week": "int",
                    "primary_goals": ["str"],
                    "emphasis": ["str <= 60 chars"],
                    "tuning_reason": "str <= 140 chars",
                }
            ],
            "summary": "str <= 200 chars",
        },
        "rules": [
            "same phase count, names, and order as current_phases",
            "phases contiguous starting at week 1",
            f"last phase end_week must equal {duration_weeks}",
        ],
        "required_output": "Return only JSON. No markdown. No explanation.",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "system": MACRO_TUNING_SYSTEM_PROMPT,
                    "max_tokens": int(os.environ.get("MACRO_AI_MAX_TOKENS", "2500") or 2500),
                    "messages": [{"role": "user", "content": json.dumps(payload, default=str)}],
                },
            )
        if response.status_code >= 400:
            raise RuntimeError(f"status={response.status_code} body={response.text[:300]}")
        data = response.json()
        text = "\n".join(
            block.get("text", "")
            for block in (data.get("content") or [])
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
        if text.startswith("```"):
            text = text[3:]
            if text.lower().startswith("json"):
                text = text[4:]
        if text.endswith("```"):
            text = text[:-3]
        parsed = json.loads(text.strip())
        merged = _merge_tuned_phases(phases, parsed.get("phases"), duration_weeks)
        if merged is None:
            logger.warning("Macro AI tuning produced invalid phases; using rule-based phases")
            return phases, {"tuned": False, "reason": "invalid_ai_phases", "model": model}
        logger.info("Macro phases AI-tuned model=%s usage=%s", data.get("model"), data.get("usage"))
        return merged, {"tuned": True, "model": model, "summary": parsed.get("summary")}
    except Exception as exc:
        logger.warning("Macro AI tuning failed, using rule-based phases: %s", exc)
        return phases, {"tuned": False, "reason": str(exc)[:200], "model": model}


async def create_user_macro_plan(
    db: Any,
    *,
    user_id: str,
    profile: Dict[str, Any],
    status: str = "active",
) -> Dict[str, Any]:
    now = datetime.utcnow()
    sports = _profile_sports(profile)
    sport_profile_values = _sport_profile_lookup_values(sports)
    sport_profiles = await db.sport_profiles.find({"sport": {"$in": sport_profile_values}}).to_list(20) if sports else []
    template, selection_reasons = await _select_template(db, profile, sports)

    rule_ids: List[str] = list(template.get("linked_planning_rule_ids") or [])
    for sport_profile in sport_profiles:
        rule_ids.extend(sport_profile.get("planning_rule_ids") or [])
    planning_rules = await _load_rules(db, rule_ids, sports)
    competition_rules = await _load_competition_rules(db, sports)
    rules_by_id = {rule.get("id"): rule for rule in planning_rules if rule.get("id")}
    phases = _build_phases(template, rules_by_id)
    phases, phase_tuning = await _ai_tune_phases(profile, template, phases, sport_profiles)

    macro_plan = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "status": status,
        "source": "hybrid_macro_plan_v1" if phase_tuning.get("tuned") else "rule_grounded_macro_plan_v1",
        "created_at": now,
        "updated_at": now,
        "template_id": template.get("id"),
        "template_name": template.get("name"),
        "template_selection_reasons": selection_reasons,
        "duration_weeks": template.get("macro_length_weeks"),
        "current_week": 1,
        "current_block": 1,
        "sports": sports,
        "goals": _profile_goals(profile),
        "user_level": _level(profile),
        "season_phase": _season_phase(profile),
        "profile_snapshot": profile,
        "sport_profiles": [_compact_sport_profile(doc) for doc in sport_profiles],
        "phases": phases,
        "phase_tuning": phase_tuning,
        "planning_rules": [_compact_rule(rule) for rule in planning_rules],
        "competition_week_rules": [_compact_rule(rule) for rule in competition_rules],
        "generation_constraints": {
            "macro_plan_is_source_of_direction": True,
            "generate_blocks_not_random_weeks": True,
            "default_block_generation_weeks": 4,
            "ai_outputs_structure_only": True,
            "database_hydrates_exercise_details": True,
            "monitor_trends_not_single_points": True,
        },
        "assumptions": _assumptions(profile, sports, sport_profiles),
    }

    await db.macro_plans.update_many(
        {"user_id": user_id, "status": "active"},
        {"$set": {"status": "archived", "archived_at": now, "updated_at": now}},
    )
    await db.macro_plans.insert_one(macro_plan)
    await initialize_athlete_state(db, user_id=user_id, profile=profile, macro_plan=macro_plan)
    return macro_plan


async def ensure_user_macro_plan(
    db: Any,
    *,
    user_id: str,
    profile: Dict[str, Any],
    force_new: bool = False,
) -> Dict[str, Any]:
    if not force_new:
        existing = await db.macro_plans.find_one({"user_id": user_id, "status": "active"}, sort=[("created_at", -1)])
        if existing:
            return existing
    return await create_user_macro_plan(db, user_id=user_id, profile=profile)


async def initialize_athlete_state(
    db: Any,
    *,
    user_id: str,
    profile: Dict[str, Any],
    macro_plan: Dict[str, Any],
) -> Dict[str, Any]:
    now = datetime.utcnow()
    state = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "macro_plan_id": macro_plan["id"],
        "status": "active",
        "current_level": macro_plan.get("user_level") or _level(profile),
        "current_block": 1,
        "current_week": 1,
        "completion_rate_28d": None,
        "average_rpe_14d": None,
        "pain_trends": [
            {"area": area, "trend": "unknown", "severity": "unknown"}
            for area in _clean_list(profile.get("pain_areas"))
        ],
        "strength_trends": [],
        "readiness": {
            "sleep_avg_hours": profile.get("sleep_avg_hours"),
            "stress_level": profile.get("stress_level"),
            "fatigue_flag": _low_readiness(profile),
        },
        "coach_summary": "Initial athlete state created from onboarding. Update after completed workouts and block reviews.",
        "created_at": now,
        "updated_at": now,
    }
    insert_state = {
        key: value
        for key, value in state.items()
        if key not in {"macro_plan_id", "status", "updated_at"}
    }
    await db.athlete_states.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": insert_state,
            "$set": {
                "macro_plan_id": macro_plan["id"],
                "status": "active",
                "updated_at": now,
            },
        },
        upsert=True,
    )
    saved = await db.athlete_states.find_one({"user_id": user_id})
    return saved or state


def summarize_macro_plan_for_ai(macro_plan: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not macro_plan:
        return {}
    phases = []
    for phase in macro_plan.get("phases") or []:
        phases.append({
            "block": phase.get("block"),
            "phase": phase.get("phase"),
            "weeks": [phase.get("start_week"), phase.get("end_week")],
            "primary_goals": phase.get("primary_goals") or [],
            "emphasis": phase.get("emphasis") or [],
            "tuning_reason": phase.get("tuning_reason"),
            "progression_logic": phase.get("progression_logic"),
            "deload_logic": phase.get("deload_logic"),
        })
    return {
        "id": macro_plan.get("id"),
        "template_id": macro_plan.get("template_id"),
        "template_name": macro_plan.get("template_name"),
        "duration_weeks": macro_plan.get("duration_weeks"),
        "current_block": macro_plan.get("current_block"),
        "current_week": macro_plan.get("current_week"),
        "sports": macro_plan.get("sports") or [],
        "user_level": macro_plan.get("user_level"),
        "season_phase": macro_plan.get("season_phase"),
        "phases": phases[:8],
        "planning_rules": [
            {
                "id": rule.get("id"),
                "category": rule.get("category"),
                "rule": rule.get("rule"),
                "recommended_action": rule.get("recommended_action") or [],
                "blocked_action": rule.get("blocked_action") or [],
            }
            for rule in (macro_plan.get("planning_rules") or [])[:10]
        ],
        "competition_week_rules": [
            {
                "id": rule.get("id"),
                "category": rule.get("category"),
                "rule": rule.get("rule"),
                "recommended_action": rule.get("recommended_action") or [],
                "blocked_action": rule.get("blocked_action") or [],
            }
            for rule in (macro_plan.get("competition_week_rules") or [])[:6]
        ],
        "generation_constraints": macro_plan.get("generation_constraints") or {},
        "assumptions": macro_plan.get("assumptions") or [],
    }

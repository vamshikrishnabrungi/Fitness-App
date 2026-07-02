import asyncio
import json
import logging
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import httpx

from backend.models import ProgramGenerationOutput


logger = logging.getLogger(__name__)


class WorkoutGenerationError(RuntimeError):
    pass


GENERIC_TITLE_PHRASES = {
    "full body circuit",
    "full body strength",
    "conditioning circuit",
    "random circuit",
    "total body workout",
    "generic workout",
    "overall strength",
}

VAGUE_EXERCISE_NAMES = {
    "dynamic stretching",
    "static stretching",
    "cardio",
    "core work",
    "mobility work",
    "stretching",
    "full body circuit",
    "conditioning circuit",
}

LAZY_FILLER_EXERCISES = {
    "burpees",
    "jumping jacks",
    "mountain climbers",
    "generic hiit circuit",
    "amrap",
}

GENERIC_PURPOSES = {
    "build strength",
    "improve fitness",
    "increase endurance",
    "build muscle",
    "warm up",
    "cool down",
}

SPORT_SPECIFIC_TERMS = {
    "cricket",
    "volleyball",
    "running",
    "runner",
    "football",
    "soccer",
    "basketball",
    "combat",
    "acceleration",
    "deceleration",
    "landing",
    "jump",
    "sprint",
    "lateral",
    "rotational",
    "anti-rotation",
    "throw",
    "overhead",
    "fielding",
    "approach",
    "scapular",
    "shoulder",
    "trunk",
    "hip",
    "knee",
    "ankle",
    "calf",
    "soleus",
    "hamstring",
    "adductor",
    "change of direction",
    "repeated sprint",
    "tissue capacity",
}

WEAK_TRANSFER_TERMS = {
    "overall athleticism",
    "overall strength",
    "endurance",
    "fitness",
    "conditioning",
}

DAY_ALIASES = {
    "mon": "monday",
    "monday": "monday",
    "tue": "tuesday",
    "tues": "tuesday",
    "tuesday": "tuesday",
    "wed": "wednesday",
    "wednesday": "wednesday",
    "thu": "thursday",
    "thur": "thursday",
    "thurs": "thursday",
    "thursday": "thursday",
    "fri": "friday",
    "friday": "friday",
    "sat": "saturday",
    "saturday": "saturday",
    "sun": "sunday",
    "sunday": "sunday",
}


WORKOUT_GENERATION_SYSTEM_PROMPT = """
You are SFTC's elite strength-and-conditioning program architect.
Create athlete-grade programs from the user's profile, not generic templates.

Use the provided knowledge_context as the approved compact exercise/rule catalog:
- If knowledge_context.macro_plan exists, treat it as the source of long-term direction.
- Generate the requested weeks inside the current macro-plan phase instead of inventing a new program direction.
- Prefer allowed_primary_exercises.
- Use allowed_variations only when level, equipment, injury context, and session purpose justify them.
- GROUNDING: select each warmup / main_work / cooldown exercise from allowed_primary_exercises or allowed_variations BY its exact "id", and copy that id into the exercise "exercise_id" field. Only use an exercise that is not in the pool when it is clinically necessary (e.g. a protocol-specified movement that is absent); then set exercise_id to null and name it precisely. Do not invent ids.
- Use progression_paths and recent history when available.
- If knowledge_context.athlete_state exists, let its trends drive progression: progress load when average_rpe is low and completion_rate is high; hold or deload when progression_signal is hold_or_deload / reduce_volume_or_difficulty, average_rpe is high, or pain is rising; respect pain_trends in exercise selection. Use strength_trends per exercise: keep progressing lifts that are 'progressing', change the stimulus (variation, rep range, or tempo) for lifts that are 'plateau', and reduce load or regress lifts that are 'regressing'.
- Use sport_teaching_context to understand the user's sport role, current skill level, teaching priorities, tactical focus, safe progressions, and level gates.
- If knowledge_context.benchmarks exists, prescribe main-lift loads as a % of the relevant 1RM (strength ~80-90%, hypertrophy ~65-75%, power ~30-60% moved fast) and state the resulting working weight; use cmj_cm / single_leg_hop_lsi_pct / visa scores to gate progression (e.g. reintroduce plyometrics only once single_leg_hop_lsi_pct >= 90). When no 1RM exists for a lift, anchor to RPE/RIR.
- If knowledge_context.training_protocols exists, FOLLOW them precisely — these are the expert decisions and override generic programming. Apply the stage prescriptions exactly (sets, reps, TEMPO, intensity/RPE, frequency), obey the key_rules and avoid list, and include the monitoring/testing they specify. Example: for a patellar-tendon athlete, program the isometric/heavy-slow-resistance loading with explicit tempo and hold times rather than generic squats; do not jump straight to plyometrics.
- Do not turn sport_teaching_context drills into gym exercises unless they belong inside a sport-practice note; use it mainly to shape sport_transfer, why_this_session, athlete_analysis, and progression logic.

Programming rules:
- Match the user's goal, sports, level, equipment, schedule, session duration, pain/injury, sleep, and stress.
- Every session needs a clear purpose, sport_transfer, and why_this_session.
- Every exercise needs a specific purpose, prescription, rest, load guidance when sets are used, and RPE when useful.
- Sport users need real transfer: acceleration, deceleration, landing, jumping, rotation, trunk control, shoulder/scapular durability, calf/soleus/hamstring/adductor capacity as relevant.
- Pain changes exercise selection. Knee pain requires low impact, hip control, hamstrings, calf/soleus capacity, landing mechanics only if low-volume and pain-free. Shoulder/back/ankle pain require conservative modifications.
- Avoid vague names: dynamic stretching, cardio, core work, mobility work, stretching, full body circuit.
- Avoid lazy fillers: burpees, jumping jacks, mountain climbers, random HIIT, generic AMRAPs.
- No true 1RM tests, max sprints without prep, or high-impact volume for painful joints.
- Fit the requested duration realistically. Use RPE/RIR/tempo/pain-free range when loads are unknown.

Output compactness rules:
- Generate a structure-only workout prescription blueprint, not a coaching article.
- AI decides what to train, when, why, how hard, and how to progress.
- The database provides how to perform the exercise: definitions, coaching cues, common errors, substitutions, and safety details.
- Do NOT output definitions, coaching cue paragraphs, common errors, or substitutions. The backend enriches those from DB after exercise matching.
- Use the exact JSON field names from required_schema. Do not use aliases like week, phase, block_number, block_name, or focus.
- athlete_analysis must be an object, not a paragraph string.
- sport_transfer must be a list of 2-3 short strings, not one long paragraph.
- why_this_session must be one short string under 220 characters.
- Exercise purpose must be one short string under 150 characters.
- injury_modifications must be a list of at most 3 short strings.
- Structure each session BY ITS CATEGORY using knowledge_context.session_blueprints (per-type warmup/main/cooldown counts, rest, and notes). Do NOT apply one fixed structure to every session: strength = ramp to a top set, 3-5 mains, 2-4 min rest; power = low-volume explosive work, full recovery, plyometrics first while fresh; hypertrophy = 4-6 mains, 60-90s rest, controlled tempo; conditioning = intervals with an explicit work:rest ratio; mobility/recovery = a drill FLOW where main_work may be EMPTY (never force a lift).
- Order main_work correctly: power / plyometric / Olympic lifts first (while fresh), then primary strength, then accessories, then any conditioning finisher.
- Prescribe rest that matches the goal per the blueprint (strength/power longer, hypertrophy/conditioning shorter) — do not default everything to 60-90 sec.
- Prescription depth (populate the tempo/load_guidance/rpe fields, do not leave them generic):
  * TEMPO by goal: controlled eccentric (e.g. tempo "3-0-1") on hypertrophy and primary strength lifts; explosive concentric ("X", move as fast as possible) on power/speed work; slow eccentric + isometric holds on tendon/rehab work.
  * RAMP-UP SETS: for heavy compound main lifts (strength/power), put ramp-up guidance in load_guidance (e.g. "2-3 progressive warm-up sets ramping to the top working set"), not just the working sets.
  * CONTRAST / POTENTIATION: on power days for intermediate+ athletes you may pair a heavy strength lift with a biomechanically similar explosive movement (e.g. heavy squat then box jump).
  * CONDITIONING: always name the target energy system and give an explicit work:rest ratio (e.g. 1:1 for threshold, 1:3-1:5 for speed/alactic), not an open-ended circuit.
- Cooldowns should target the session just done: mobility for the muscles/joints worked plus parasympathetic downregulation (e.g. nasal or box breathing), not a generic stretch list.
- Sequence the training WEEK for recovery: do not place two high-CNS or same-primary-pattern heavy sessions on consecutive days; put power and heavy-strength sessions when the athlete is freshest and separate them with easier or different-focus days.
- If the input contains a deload_directive, this week is a scheduled DELOAD — follow it exactly (cut total volume, keep intensity light-to-moderate, prioritize recovery, do not add load).
- Warm-ups must PREPARE the session, not be generic: follow RAMP — raise (light dynamic movement), then ACTIVATE the muscles the main work will load (e.g. glute activation / banded lateral walks before squats and hinges; scapular + rotator-cuff work like band pull-aparts, face pulls, or Y-T-W before pressing/overhead; trunk bracing like dead bug / bird dog before loaded spine work), and mobilize the key joints. Prefer resistance-band and activation drills from the pool.
- If the athlete has pain_areas or current_injuries, include at least one targeted prehab/activation drill for that area in the warmup (e.g. banded clamshell / hip work for knee pain; cuff + scapular work for shoulder pain; hip-hinge patterning + bracing for low-back pain).
- Do not include long explanations, source summaries, or repeated reasoning in the output.

Return ONLY valid JSON matching the schema. No markdown or commentary.
"""


def _json_schema() -> Dict[str, Any]:
    return {
        "title": "string",
        "goal": "string",
        "sports": ["string"],
        "duration_weeks": "integer",
        "athlete_analysis": {
            "profile_summary": "string <= 240 chars",
            "primary_constraints": ["string <= 120 chars"],
            "sport_demands": ["string <= 120 chars"],
            "block_priority": "string <= 180 chars",
        },
        "blocks": [
            {
                "name": "string",
                "start_week": "integer",
                "end_week": "integer",
                "emphasis": ["string"],
            }
        ],
        "weeks": [
            {
                "week_number": "integer",
                "theme": "string <= 120 chars",
                "progression_rule": "string <= 180 chars",
                "deload_note": "string or null",
                "workouts": [
                    {
                        "day": "string",
                        "title": "string <= 80 chars",
                        "category": "Strength | Power | Conditioning | Mobility | Recovery | Sport",
                        "duration_min": "integer",
                        "intensity": "easy | moderate | moderate-hard | hard",
                        "adaptation_targets": ["string <= 60 chars"],
                        "sport_transfer": ["string <= 120 chars"],
                        "why_this_session": "string <= 220 chars",
                        "warmup": "list of exercise objects (count per session_blueprints for this category; may be empty for a lift-only session)",
                        "main_work": "list of exercise objects (count per session_blueprints; MAY BE EMPTY for mobility/recovery sessions)",
                        "cooldown": "list of exercise objects (count per session_blueprints for this category)",
                        "injury_modifications": ["string <= 120 chars"],
                    }
                ],
            }
        ],
        "exercise_object": {
            "name": "string",
            "exercise_id": "string or null if known from allowed exercises",
            "purpose": "string <= 150 chars",
            "sets": "integer or null",
            "reps": "string or null",
            "duration": "string or null",
            "rest": "string or null",
            "load_guidance": "string or null <= 120 chars",
            "rpe": "string or null, e.g. RPE 6-7",
            "tempo": "string or null",
        },
        "nutrition_focus": "string or null <= 180 chars",
        "recovery_focus": ["string <= 120 chars"],
        "safety_notes": ["string <= 120 chars"],
        "assumptions": ["string <= 120 chars"],
        "notes": [
            "weeks[].workouts count must equal schedule_rules.training_days_per_week",
            "use preferred days when provided",
            "Do not add fields outside this schema",
            "Use exact field names: week_number, theme, progression_rule, deload_note, blocks[].name, blocks[].start_week, blocks[].end_week, blocks[].emphasis"
        ],
    }


def _clean_json(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def _clean_list(value: Any) -> List[Any]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    return [item for item in (_clean_value(item) for item in items) if item not in (None, [], {})]


def _parse_run_pace_seconds(value: Any) -> Optional[int]:
    value = _clean_value(value)
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).lower().replace("/km", "").replace("min/km", "").strip()
    try:
        if ":" in text:
            minutes, seconds = text.split(":", 1)
            return int(minutes) * 60 + int(float(seconds))
        parsed_minutes = float(text)
        return int(parsed_minutes * 60)
    except (TypeError, ValueError):
        return None


def _normalized_fitness_assessment(profile: Dict[str, Any]) -> Dict[str, Any]:
    assessment = dict(profile.get("fitness_assessment") or {})
    return {
        "pushups": assessment.get("pushups"),
        "pullups": assessment.get("pullups"),
        "squats": assessment.get("squats"),
        "plank_seconds": assessment.get("plank_seconds", assessment.get("plank")),
        "run_pace_seconds_per_km": assessment.get(
            "run_pace_seconds_per_km",
            _parse_run_pace_seconds(assessment.get("run_pace") or assessment.get("runPace")),
        ),
    }


def _normalized_sports(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    sports = [str(sport) for sport in _clean_list(profile.get("sports"))]
    detail_by_sport = {
        str(detail.get("sport") or "").lower(): detail
        for detail in (profile.get("sport_details") or [])
        if isinstance(detail, dict) and detail.get("sport")
    }
    normalized = []
    for sport in sports:
        detail = dict(detail_by_sport.get(sport.lower()) or {"sport": sport})
        normalized.append({
            "sport": sport,
            "role": _clean_value(detail.get("role")),
            "position_or_style": _clean_value(detail.get("position_or_style")),
            "competition_level": _clean_value(detail.get("competition_level") or profile.get("competition_level")),
            "season_phase": _clean_value(detail.get("season_phase") or profile.get("season_phase")),
            "weekly_practice_frequency": detail.get("weekly_practice_frequency"),
            "match_days": _clean_list(detail.get("match_days")),
            "current_skill_priority": _clean_list(detail.get("current_skill_priority")),
        })
    return normalized


def _normalized_current_injuries(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    injuries = []
    for injury in profile.get("current_injuries") or []:
        if isinstance(injury, dict):
            injuries.append({
                "area": _clean_value(injury.get("area")),
                "side": _clean_value(injury.get("side")) or "unknown",
                "severity": _clean_value(injury.get("severity")) or "unknown",
                "status": _clean_value(injury.get("status") or injury.get("note")),
                "note": _clean_value(injury.get("note")),
                "triggers": _clean_list(injury.get("triggers")),
                "allowed_movements": _clean_list(injury.get("allowed_movements")),
                "restricted_movements": _clean_list(injury.get("restricted_movements")),
                "medical_clearance": _clean_value(injury.get("medical_clearance")) or "unknown",
            })
    return [injury for injury in injuries if injury.get("area") or injury.get("status") or injury.get("note")]


def _profile_brief(profile: Dict[str, Any]) -> Dict[str, Any]:
    selected_goals = _clean_list(profile.get("selected_goals") or profile.get("goals"))
    primary_goal = _clean_value(profile.get("primary_goal")) or (selected_goals[0] if selected_goals else None)
    secondary_goals = [goal for goal in selected_goals if goal != primary_goal]
    return {
        "identity": {
            "gender": _clean_value(profile.get("gender")),
            "date_of_birth": _clean_value(profile.get("date_of_birth")),
            "height_cm": profile.get("height_cm"),
            "weight_kg": profile.get("weight_kg"),
            "target_weight_kg": profile.get("target_weight_kg"),
            "country": _clean_value(profile.get("country")),
            "state": _clean_value(profile.get("state")),
            "city": _clean_value(profile.get("city")),
            "timezone": _clean_value(profile.get("timezone")),
        },
        "goals": {
            "primary": primary_goal,
            "secondary": secondary_goals,
            "nutrition_goal": _clean_value(profile.get("nutrition_goal")),
            "target_date": _clean_value(profile.get("target_date")),
            "upcoming_events": profile.get("upcoming_events") or [],
        },
        "training_context": {
            "experience": _clean_value(profile.get("experience")),
            "training_location": _clean_value(profile.get("training_location")),
            "equipment": _clean_list(profile.get("equipment")),
            "facilities": _clean_list(profile.get("facilities")),
            "training_days_per_week": profile.get("training_days_per_week"),
            "preferred_training_days": _clean_list(profile.get("preferred_training_days")),
            "session_duration_min": profile.get("session_duration_min"),
            "preferred_training_time": _clean_value(profile.get("preferred_training_time")),
            "schedule_constraints": _clean_value(profile.get("schedule_constraints")),
        },
        "sports": _normalized_sports(profile),
        "fitness_assessment": _normalized_fitness_assessment(profile),
        "health": {
            "current_injuries": _normalized_current_injuries(profile),
            "injury_history": profile.get("injury_history") or [],
            "pain_areas": _clean_list(profile.get("pain_areas")),
            "medical_notes": _clean_value(profile.get("medical_notes")),
            "allergies": _clean_list(profile.get("allergies")),
        },
        "recovery": {
            "sleep_avg_hours": profile.get("sleep_avg_hours"),
            "stress_level": _clean_value(profile.get("stress_level")),
            "recovery_score_baseline": profile.get("recovery_score_baseline"),
        },
        "nutrition": {
            "diet_preference": _clean_value(profile.get("diet_preference")),
            "dietary_restrictions": _clean_list(profile.get("dietary_restrictions")),
            "nutrition_goal": _clean_value(profile.get("nutrition_goal")),
            "allergies": _clean_list(profile.get("allergies")),
        },
    }


def _requested_session_count(profile: Dict[str, Any]) -> int:
    try:
        requested = int(profile.get("training_days_per_week") or 4)
    except (TypeError, ValueError):
        requested = 4
    return min(6, max(1, requested))


def _preferred_days(profile: Dict[str, Any]) -> List[str]:
    return [str(day).strip() for day in (profile.get("preferred_training_days") or []) if str(day).strip()]


def _normalize_day(day: Any) -> str:
    cleaned = str(day or "").strip().lower()
    return DAY_ALIASES.get(cleaned, cleaned)


def _normalize_exercise_name(name: Any) -> str:
    text = str(name or "").lower().strip()
    normalized = []
    for char in text:
        normalized.append(char if char.isalnum() else " ")
    return " ".join("".join(normalized).split())


def _extract_known_exercise_names(knowledge_context: Optional[Dict[str, Any]]) -> set[str]:
    if not knowledge_context:
        return set()

    names: set[str] = set()
    candidate_keys = {
        "exercises",
        "exercise_library",
        "known_exercises",
        "known_exercise_names",
        "relevant_exercises",
        "exercise_candidates",
    }

    def add_name(value: Any) -> None:
        normalized = _normalize_exercise_name(value)
        if normalized:
            names.add(normalized)

    def walk(value: Any, key_hint: Optional[str] = None) -> None:
        if isinstance(value, dict):
            if key_hint in candidate_keys:
                for item in value.values():
                    walk(item, key_hint)
                return
            if value.get("name"):
                add_name(value.get("name"))
            for alias in value.get("aliases") or []:
                add_name(alias)
            for key, item in value.items():
                if key in candidate_keys:
                    walk(item, key)
        elif isinstance(value, list):
            for item in value:
                walk(item, key_hint)
        elif key_hint in candidate_keys:
            add_name(value)

    walk(knowledge_context)
    return names


def _matches_known_exercise(name: str, known_exercises: set[str]) -> bool:
    normalized = _normalize_exercise_name(name)
    if not normalized:
        return False
    if normalized in known_exercises:
        return True
    for known in known_exercises:
        if len(known) >= 5 and (known in normalized or normalized in known):
            return True
    return False


def _has_sport_context(profile: Dict[str, Any]) -> bool:
    sports = profile.get("sports") or []
    sport_details = profile.get("sport_details") or []
    goals = " ".join(str(goal).lower() for goal in (profile.get("goals") or profile.get("selected_goals") or []))
    primary_goal = str(profile.get("primary_goal") or "").lower()
    return bool(sports or sport_details or "sport" in goals or "performance" in goals or "sport" in primary_goal)


def _text_contains_any(text: str, phrases: set[str]) -> Optional[str]:
    lowered = text.lower()
    for phrase in phrases:
        if phrase in lowered:
            return phrase
    return None


def _knowledge_known_names(knowledge_context: Optional[Dict[str, Any]]) -> set[str]:
    return _extract_known_exercise_names(knowledge_context)


def _looks_like_weightlifting_library_exercise(name: str) -> bool:
    lowered = name.lower()
    markers = {
        "snatch",
        "clean",
        "jerk",
        "squat",
        "deadlift",
        "pull",
        "press",
        "rack",
        "overhead",
        "split",
    }
    return any(marker in lowered for marker in markers)


def _exercise_validation_issues(
    exercise: Any,
    section_name: str,
    workout_title: str,
    injury_text: str,
    has_sport_context: bool,
    known_exercise_names: Optional[set[str]] = None,
    strict_library_matches: bool = False,
) -> Tuple[List[str], List[str], List[str]]:
    """Return (hard_issues, soft_issues, safety_issues) for one exercise.

    Hard issues are genuinely broken selections that should trigger regeneration. Soft issues are
    quality nits (logged, non-blocking). Safety issues are injury-context concerns that the caller
    auto-repairs (adds a pain-free cue) in tiered mode rather than discarding the whole program.
    """
    hard: List[str] = []
    soft: List[str] = []
    safety: List[str] = []
    exercise_name = str(exercise.name or "").strip()
    purpose = str(exercise.purpose or "").strip()
    combined = f"{exercise_name} {purpose} {' '.join(exercise.coaching_notes or [])}".lower()

    # --- HARD: nonsense or unsafe exercise selection ---
    vague_name = _text_contains_any(exercise_name, VAGUE_EXERCISE_NAMES)
    if vague_name:
        hard.append(f"{workout_title}: vague exercise name '{vague_name}' in {section_name}")

    if (
        strict_library_matches
        and known_exercise_names
        and section_name == "main_work"
        and _looks_like_weightlifting_library_exercise(exercise_name)
        and not _matches_known_exercise(exercise_name, known_exercise_names)
    ):
        hard.append(f"{workout_title}: unknown exercise '{exercise_name}' is not in retrieved knowledge context")

    filler = _text_contains_any(exercise_name, LAZY_FILLER_EXERCISES)
    if filler:
        if filler in {"burpees", "jumping jacks"} and any(token in injury_text for token in ["knee", "ankle", "achilles", "calf"]):
            hard.append(f"{workout_title}: filler/high-impact exercise '{filler}' conflicts with pain context")
        elif len(purpose) < 55 or ("specific" not in purpose.lower() and "transfer" not in purpose.lower()):
            hard.append(f"{workout_title}: filler exercise '{filler}' lacks strong sport-specific justification")

    # --- SAFETY: injury-context concerns (auto-repaired in tiered mode, not a hard reject) ---
    if any(token in injury_text for token in ["shoulder", "rotator", "overhead"]) and "overhead" in combined:
        if not any(token in combined for token in ["pain-free", "modify", "scap", "shoulder", "substitution"]):
            safety.append(f"{workout_title}: overhead exercise '{exercise_name}' needs shoulder-safety modification")
    knee_impact_name = exercise_name.lower()
    if any(token in injury_text for token in ["knee", "patellar"]) and any(
        token in knee_impact_name for token in ["jump", "hop", "plyometric", "bound", "depth drop", "landing drill"]
    ):
        if not any(token in combined for token in ["pain-free", "landing", "low volume", "modify", "substitution", "quiet"]):
            safety.append(f"{workout_title}: impact exercise '{exercise_name}' needs knee-safety modification")
    if any(token in injury_text for token in ["back", "spine", "lumbar"]) and any(token in combined for token in ["deadlift", "clean", "snatch", "squat", "hinge"]):
        if not any(token in combined for token in ["neutral", "pain-free", "modify", "brace", "substitution", "reduce load"]):
            safety.append(f"{workout_title}: loaded exercise '{exercise_name}' needs back-safety modification")

    # --- SOFT: purpose-quality nits (logged, non-blocking) ---
    if not purpose:
        soft.append(f"{workout_title}: exercise '{exercise_name}' in {section_name} is missing purpose")
    elif len(purpose) < 28:
        soft.append(f"{workout_title}: exercise '{exercise_name}' in {section_name} needs a more specific purpose")
    elif purpose.lower().rstrip(".") in GENERIC_PURPOSES:
        soft.append(f"{workout_title}: exercise '{exercise_name}' has generic purpose '{purpose}'")
    if section_name == "main_work" and 0 < len(purpose) < 32:
        soft.append(f"{workout_title}: main exercise '{exercise_name}' needs a specific purpose")

    return hard, soft, safety


def _validation_mode() -> str:
    """tiered (default) = only hard issues block; strict = legacy all-block; off = skip."""
    mode = (os.environ.get("WORKOUT_AI_VALIDATION_MODE") or "tiered").strip().lower()
    return mode if mode in {"tiered", "strict", "off"} else "tiered"


def _session_duration_cap() -> int:
    """Sane upper bound on session length. Users may request long sessions, but we
    clamp absurd values. Configurable via WORKOUT_AI_MAX_SESSION_MIN (default 150)."""
    try:
        return max(60, int(os.environ.get("WORKOUT_AI_MAX_SESSION_MIN", "150") or 150))
    except (TypeError, ValueError):
        return 150


_DURATION_RE = re.compile(r"(\d+\s*(?:-\s*\d+)?\s*(?:seconds|second|secs|sec|minutes|minute|mins|min|s)\b)", re.IGNORECASE)

_TIME_BASED_KEYWORDS = {
    "hold", "isometric", " iso", "plank", "carry", "hang", "wall sit", "bridge", "dead hang",
    "stretch", "breathing", "interval", "walk", "jog", "run ", "sprint", "shuffle", "crawl",
    "balance", "pose", "farmer", "pallof", "bird dog", "side plank", "hollow",
}


def _extract_duration_text(exercise: Any) -> Optional[str]:
    haystack = " ".join(filter(None, [
        str(exercise.load_guidance or ""),
        " ".join(str(note) for note in (exercise.coaching_notes or [])),
        str(exercise.name or ""),
        str(exercise.tempo or ""),
    ]))
    match = _DURATION_RE.search(haystack)
    return match.group(1).strip() if match else None


def _looks_time_based(name: Any, category: Any) -> bool:
    n = f" {str(name or '').lower()} "
    if any(kw in n for kw in _TIME_BASED_KEYWORDS):
        return True
    return str(category or "").lower() in {"conditioning", "mobility", "recovery"}


def _default_duration(name: Any, category: Any) -> str:
    n = str(name or "").lower()
    if any(k in n for k in ("interval", "walk", "jog", "run", "sprint", "shuffle")) or str(category or "").lower() == "conditioning":
        return "1-2 min"
    return "30-45 sec"


# Per-session-type structure. Drives BOTH the prompt (how to build the session) and the validator
# (what to require) so structure adapts to workout type instead of a single fixed cap.
SESSION_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "strength": {"warmup": "2-3", "main": "3-5", "cooldown": "1-2", "requires_main": True,
                 "rest": "2-4 min on heavy compounds, ~90 sec on accessories",
                 "notes": "Prescribe 2-3 ramp-up sets to the top working set. Controlled eccentric tempo on primary lifts. Order: activation -> primary compound(s) -> accessories."},
    "power": {"warmup": "3-4", "main": "3-4", "cooldown": "1-2", "requires_main": True,
              "rest": "full recovery, 2-3 min between explosive efforts",
              "notes": "Thorough activation + potentiation warm-up. Keep volume LOW with explosive-concentric intent; place jumps/throws/plyometrics FIRST while fresh; consider a heavy+explosive contrast pair for advanced athletes; stop the set when output drops."},
    "hypertrophy": {"warmup": "2-3", "main": "4-6", "cooldown": "1-2", "requires_main": True,
                    "rest": "60-90 sec (up to 2 min on big compounds)",
                    "notes": "8-15 reps, controlled eccentric tempo, 1-3 RIR; order compounds before isolation."},
    "conditioning": {"warmup": "2-3", "main": "2-4", "cooldown": "1-2", "requires_main": True,
                     "rest": "prescribe an explicit work:rest ratio per interval",
                     "notes": "State the energy system targeted; use timed intervals with a work:rest ratio, not endless circuits."},
    "mobility": {"warmup": "0-1", "main": "0", "cooldown": "0-1", "requires_main": False,
                 "rest": "brief, controlled breathing",
                 "notes": "A mobility / movement-quality FLOW, not a lift. Put the drills in warmup and/or cooldown; main_work may be empty."},
    "recovery": {"warmup": "0-1", "main": "0", "cooldown": "0-2", "requires_main": False,
                 "rest": "easy",
                 "notes": "Low-intensity recovery flow; no heavy loading; main_work may be empty."},
    "sport": {"warmup": "2-4", "main": "2-4", "cooldown": "1-2", "requires_main": False,
              "rest": "as appropriate to the drill",
              "notes": "Sport-specific prep that primes the sport's key movement patterns, plus skill/tactical work — not a generic gym warm-up."},
}


def _session_blueprint(category: Any) -> Dict[str, Any]:
    c = str(category or "").lower()
    if "power" in c or "plyo" in c or "ballistic" in c:
        key = "power"
    elif "hypertroph" in c:
        key = "hypertrophy"
    elif "condition" in c or "metcon" in c or "cardio" in c:
        key = "conditioning"
    elif "mobility" in c or "flex" in c or "stretch" in c:
        key = "mobility"
    elif "recovery" in c or "regen" in c or "rest" in c:
        key = "recovery"
    elif "sport" in c or "skill" in c:
        key = "sport"
    else:
        key = "strength"
    return SESSION_BLUEPRINTS[key]


def _default_rest(category: Any) -> str:
    return _session_blueprint(category)["rest"]


def validate_program_quality(
    program: ProgramGenerationOutput,
    profile: Dict[str, Any],
    knowledge_context: Optional[Dict[str, Any]] = None,
    *,
    strict_library_matches: bool = False,
) -> ProgramGenerationOutput:
    mode = _validation_mode()
    if not program.weeks:
        raise ValueError("AI response did not include any training weeks")
    if program.duration_weeks < 1:
        program.duration_weeks = 4
    if mode == "off":
        return program

    session_count = _requested_session_count(profile)
    duration_cap = _session_duration_cap()
    session_duration = min(duration_cap, max(30, int(profile.get("session_duration_min") or 45)))
    preferred_days = _preferred_days(profile)
    preferred_day_set = {_normalize_day(day) for day in preferred_days}
    has_sport_context = _has_sport_context(profile)
    pain_areas = [str(item).lower() for item in (profile.get("pain_areas") or [])]
    current_injuries = [str(item).lower() for item in (profile.get("current_injuries") or [])]
    injury_text = " ".join([*pain_areas, *current_injuries])
    hard_issues: List[str] = []
    soft_issues: List[str] = []
    repairs: List[str] = []
    # Auto-repair only in tiered mode; strict mode preserves legacy reject-everything behavior.
    can_repair = mode == "tiered"
    known_exercise_names = _knowledge_known_names(knowledge_context)

    # Program-level completeness: repair safe defaults, otherwise note.
    if not program.athlete_analysis:
        soft_issues.append("program is missing athlete_analysis")
    if profile.get("nutrition_goal") and not program.nutrition_focus:
        if can_repair:
            program.nutrition_focus = (
                f"Support your {profile.get('nutrition_goal')} goal with adequate daily protein and "
                f"consistent fueling around training sessions."
            )
            repairs.append("nutrition_focus")
        else:
            soft_issues.append("program is missing nutrition_focus despite nutrition goal")
    if not program.recovery_focus:
        if can_repair:
            program.recovery_focus = ["Prioritize 7-9 hours of sleep", "Keep non-session days easy and active"]
            repairs.append("recovery_focus")
        else:
            soft_issues.append("program is missing recovery_focus")
    if not program.safety_notes:
        if can_repair:
            program.safety_notes = ["Train within a pain-free range of motion", "Stop any movement that causes sharp pain"]
            repairs.append("safety_notes")
        else:
            soft_issues.append("program is missing safety_notes")

    for week in program.weeks:
        original_count = len(week.workouts)
        if original_count != session_count:
            hard_issues.append(
                f"week {week.week_number}: expected {session_count} workouts, got {original_count}"
            )
        for workout_index, workout in enumerate(week.workouts):
            if not workout.title or len(workout.title.strip()) < 4:
                if can_repair:
                    workout.title = f"{workout.category} Session"
                    repairs.append("title")
                else:
                    soft_issues.append(f"week {week.week_number} workout {workout_index + 1}: missing specific title")
            generic_title = _text_contains_any(workout.title, GENERIC_TITLE_PHRASES)
            if generic_title:
                soft_issues.append(f"{workout.title}: generic workout title '{generic_title}'")
            # Duration: auto-clamp values above the sane cap; soft-warn if above the user's requested length.
            if workout.duration_min > duration_cap:
                soft_issues.append(f"{workout.title}: duration {workout.duration_min} clamped to cap {duration_cap} min")
                workout.duration_min = duration_cap
            elif workout.duration_min > session_duration:
                soft_issues.append(f"{workout.title}: duration {workout.duration_min} exceeds requested {session_duration} minutes")
            if workout.duration_min < 10:
                soft_issues.append(f"{workout.title}: duration {workout.duration_min} is unrealistically short")
            if not workout.why_this_session or len(str(workout.why_this_session).strip()) < 45:
                if can_repair:
                    targets = ", ".join((workout.adaptation_targets or [])[:2]) or "the target qualities"
                    workout.why_this_session = (
                        f"{workout.category} session developing {targets} within this phase of the plan, "
                        f"progressing steadily while respecting recovery."
                    )
                    repairs.append("why_this_session")
                else:
                    soft_issues.append(f"{workout.title}: missing specific why_this_session")
            elif has_sport_context and not _text_contains_any(str(workout.why_this_session), SPORT_SPECIFIC_TERMS):
                soft_issues.append(f"{workout.title}: why_this_session lacks sport-transfer detail")
            if not workout.sport_transfer:
                soft_issues.append(f"{workout.title}: missing sport_transfer")
            if has_sport_context:
                weak_transfers = [
                    transfer for transfer in workout.sport_transfer
                    if str(transfer).lower().strip() in WEAK_TRANSFER_TERMS
                ]
                if weak_transfers:
                    soft_issues.append(f"{workout.title}: weak sport_transfer values {weak_transfers}")
            blueprint = _session_blueprint(workout.category)
            if preferred_day_set and _normalize_day(workout.day) not in preferred_day_set:
                soft_issues.append(f"{workout.title}: day '{workout.day}' is not in preferred days {preferred_days}")
            if injury_text and not workout.injury_modifications:
                if can_repair:
                    workout.injury_modifications = [
                        "Work within a pain-free range and reduce load or range if symptoms increase."
                    ]
                    repairs.append("injury_modifications")
                else:
                    soft_issues.append(f"{workout.title}: missing injury_modifications for pain/injury context")
            for section_name, section in [
                ("warmup", workout.warmup),
                ("main_work", workout.main_work),
                ("cooldown", workout.cooldown),
            ]:
                if not section:
                    # Requirement depends on the session type: a mobility/recovery day legitimately
                    # has no main_work; a strength day should not be missing it.
                    if section_name == "main_work" and blueprint["requires_main"]:
                        hard_issues.append(f"{workout.title}: missing main_work")
                    elif section_name == "warmup" and not blueprint["warmup"].startswith("0"):
                        soft_issues.append(f"{workout.title}: missing warmup")
                    elif section_name == "cooldown" and not blueprint["cooldown"].startswith("0"):
                        soft_issues.append(f"{workout.title}: missing cooldown")
                for exercise in section:
                    if section_name == "main_work" and not exercise.rest and exercise.sets:
                        exercise.rest = _default_rest(workout.category)
                    if section_name == "main_work" and not exercise.load_guidance and exercise.sets:
                        exercise.load_guidance = "Use controlled reps in a pain-free range at the target session intensity."
                    # Repair time-based/hold/interval exercises that specify neither reps nor duration
                    # (the "3 x None" defect) by recovering a hold time from the text or a sane default.
                    if can_repair and not exercise.reps and not exercise.duration:
                        recovered = _extract_duration_text(exercise)
                        if recovered:
                            exercise.duration = recovered
                            repairs.append("exercise_duration")
                        elif _looks_time_based(exercise.name, workout.category):
                            exercise.duration = _default_duration(exercise.name, workout.category)
                            repairs.append("exercise_duration_default")
                        else:
                            soft_issues.append(f"{workout.title}: '{exercise.name}' has neither reps nor duration")
                    # Repair a missing exercise purpose with a specific-enough default before validating.
                    if can_repair and not str(exercise.purpose or "").strip():
                        section_label = {"warmup": "warm-up", "main_work": "main-set", "cooldown": "cooldown"}.get(section_name, section_name)
                        exercise.purpose = (
                            f"Targeted {section_label} work using {exercise.name} for this session's focus."
                        )
                        repairs.append("exercise_purpose")
                    ex_hard, ex_soft, ex_safety = _exercise_validation_issues(
                        exercise,
                        section_name,
                        workout.title,
                        injury_text,
                        has_sport_context,
                        known_exercise_names,
                        strict_library_matches,
                    )
                    hard_issues.extend(ex_hard)
                    soft_issues.extend(ex_soft)
                    # Injury-safety: repair by adding a pain-free cue (tiered) rather than rejecting.
                    if ex_safety:
                        if can_repair:
                            notes = list(exercise.coaching_notes or [])
                            if not any("pain-free" in str(n).lower() for n in notes):
                                notes.append("Keep this pain-free: reduce range or load, and substitute if the joint is symptomatic.")
                                exercise.coaching_notes = notes
                            repairs.append("injury_safety_cue")
                        else:
                            hard_issues.extend(ex_safety)

    # Quality telemetry: structured, grep-able counts of what was noted vs auto-repaired.
    if repairs or soft_issues or hard_issues:
        logger.info(
            "Workout validation telemetry mode=%s hard=%d soft=%d repaired=%d repairs=%s soft_notes=%s",
            mode, len(hard_issues), len(soft_issues), len(repairs),
            dict(Counter(repairs)), soft_issues[:8],
        )

    # In strict mode every issue blocks (legacy). In tiered mode only hard issues block.
    blocking = (hard_issues + soft_issues) if mode == "strict" else hard_issues
    if blocking:
        issue_text = "; ".join(blocking[:12])
        logger.warning("Rejected AI workout program validation_issues=%s", issue_text)
        raise ValueError(issue_text)

    return program


def _limit_program_weeks(program: ProgramGenerationOutput, max_weeks: Optional[int]) -> ProgramGenerationOutput:
    if not max_weeks:
        return program
    max_weeks = max(1, int(max_weeks))
    if len(program.weeks) > max_weeks:
        logger.info("Trimming generated program weeks from=%s to=%s", len(program.weeks), max_weeks)
        program.weeks = program.weeks[:max_weeks]
    program.duration_weeks = min(program.duration_weeks, max_weeks)
    for block in program.blocks:
        block.start_week = min(block.start_week, max_weeks)
        block.end_week = min(block.end_week, max_weeks)
    program.blocks = [block for block in program.blocks if block.start_week <= max_weeks]
    return program


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def generate_ai_training_program(
    profile: Dict[str, Any],
    *,
    knowledge_context: Optional[Dict[str, Any]] = None,
    openrouter_key: Optional[str] = None,
    anthropic_key: Optional[str] = None,
    model: str = "claude-opus-4-8",
    max_weeks: Optional[int] = None,
    max_attempts: int = 1,
    strict_library_matches: bool = False,
    previous_block_summary: Optional[Dict[str, Any]] = None,
    deload_week: bool = False,
) -> Dict[str, Any]:
    def _user_payload(previous_error: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "profile": _profile_brief(profile),
            "knowledge_context": knowledge_context or {},
            "session_blueprints": SESSION_BLUEPRINTS,
            "required_schema": _json_schema(),
            "schedule_rules": {
                "training_days_per_week": _requested_session_count(profile),
                "preferred_training_days": _preferred_days(profile),
                "must_match_session_count": True,
                "must_use_preferred_days_when_present": True,
            },
            "generation_scope": {
                "duration_weeks": max_weeks or 4,
                "must_generate_exactly_this_many_weeks": bool(max_weeks),
                "testing_mode": bool(max_weeks and max_weeks <= 1),
            },
            "quality_gate": {
                "must_include_athlete_analysis": True,
                "must_include_sport_transfer_for_each_session": True,
                "must_include_why_this_session_for_each_session": True,
                "must_include_specific_purpose_for_each_exercise": True,
                "must_not_use_generic_titles_or_filler_exercises": True,
                "invalid_vague_exercise_names": sorted(VAGUE_EXERCISE_NAMES),
                "cooldowns_must_name_exact_drills": True,
                "must_respect_pain_and_injury_context": True,
                "must_fit_session_duration": True,
                "must_prefer_retrieved_knowledge_when_relevant": bool(knowledge_context),
                "must_prioritize_allowed_primary_exercises": True,
                "must_select_allowed_pool_exercises_by_id": bool(
                    (knowledge_context or {}).get("allowed_primary_exercises")
                ),
                "variations_require_clear_session_justification": True,
                "must_use_progression_paths_and_recent_history_when_available": True,
                "must_use_sport_teaching_context_for_sport_users_when_available": bool(
                    ((knowledge_context or {}).get("sport_teaching_context") or {}).get("teaching_progressions")
                ),
                "must_follow_macro_plan_when_provided": bool((knowledge_context or {}).get("macro_plan")),
                "weightlifting_style_exercise_names_must_match_retrieved_library_when_known_exercises_are_provided": (
                    strict_library_matches and bool(_knowledge_known_names(knowledge_context))
                ),
                "unknown_exercises_should_be_allowed_but_named_clearly": not strict_library_matches,
            },
            "required_output": "Return only JSON. No markdown. No explanation.",
        }
        if deload_week:
            payload["deload_directive"] = (
                "This is a scheduled DELOAD week: reduce total training volume ~40-50% (fewer sets and/or "
                "exercises), keep 1-2 heavier top sets at moderate RPE (6-7) to retain the movement pattern, "
                "prioritize movement quality and recovery, and DO NOT add load or introduce new high-CNS work."
            )
        if previous_block_summary:
            payload["continuation"] = {
                "mode": "next_block",
                "previous_block": previous_block_summary,
                "instruction": (
                    "This is a CONTINUATION, not a new program. Generate the NEXT week that progresses "
                    "from previous_block. Apply progressive overload versus the previous week, rotate "
                    "accessory work sensibly, and adjust to the reported completion, RPE, soreness, and "
                    "pain. Keep the same training days and overall session structure, and stay inside the "
                    "current macro-plan phase. Do not repeat the previous week's sessions verbatim."
                ),
            }
        if previous_error:
            payload["previous_generation_failed_because"] = previous_error[:1800]
            payload["retry_instruction"] = (
                "Regenerate the full program and correct every validation issue. Keep the output compact: "
                "use exact schema fields only, no long paragraphs, <=3 warmup drills, <=4 main exercises, "
                "<=2 cooldown drills per workout, short sport_transfer lists, short exercise purposes, no "
                "coaching_notes, no substitutions, no exercise definitions, and no commentary outside JSON."
            )
        return payload

    async def _parse_program(raw_text: str, source_name: str) -> Dict[str, Any]:
        parsed_doc = json.loads(_clean_json(raw_text))
        program_doc = ProgramGenerationOutput(**parsed_doc)
        program_doc = _limit_program_weeks(program_doc, max_weeks)
        program_doc = validate_program_quality(
            program_doc,
            profile,
            knowledge_context,
            strict_library_matches=strict_library_matches,
        )
        return {
            "program": program_doc,
            "source": source_name,
            "raw": parsed_doc,
            "fallback_used": False,
            "max_weeks": max_weeks,
            "max_attempts": max_attempts,
            "strict_library_matches": strict_library_matches,
        }

    async def _call_anthropic(previous_error: Optional[str] = None) -> str:
        if not anthropic_key:
            raise RuntimeError("Anthropic API key is not configured")

        request_body = {
            "model": model,
            "system": WORKOUT_GENERATION_SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": json.dumps(_user_payload(previous_error), default=str)},
            ],
            "max_tokens": int(os.environ.get("WORKOUT_AI_MAX_TOKENS", "10000") or 10000),
        }
        headers = {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=request_body,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"Anthropic request failed status={response.status_code} body={response.text[:800]}")
        data = response.json()
        logger.info("Anthropic workout generation model=%s usage=%s", data.get("model"), data.get("usage"))
        text_parts = [
            block.get("text", "")
            for block in data.get("content") or []
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(text_parts).strip()

    async def _call_openrouter(previous_error: Optional[str] = None) -> str:
        if not openrouter_key:
            raise RuntimeError("OpenRouter API key is not configured")

        request_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": WORKOUT_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(_user_payload(previous_error), default=str)},
            ],
            "temperature": 0.35,
            "max_tokens": int(os.environ.get("WORKOUT_AI_MAX_TOKENS", "12000") or 12000),
            "usage": {"include": True},
        }
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost"),
            "X-Title": os.environ.get("OPENROUTER_APP_NAME", "SFTC"),
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=request_body,
            )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenRouter request failed status={response.status_code} body={response.text[:800]}")
        data = response.json()
        logger.info(
            "OpenRouter workout generation model=%s usage=%s",
            data.get("model"),
            data.get("usage"),
        )
        return str(data["choices"][0]["message"]["content"]).strip()

    last_error: Optional[Exception] = None
    last_error_text: Optional[str] = None
    max_attempts = min(2, max(1, int(max_attempts or 1)))
    for attempt in range(1, max_attempts + 1):
        try:
            if anthropic_key:
                raw = await asyncio.wait_for(_call_anthropic(last_error_text), timeout=190)
                return await _parse_program(raw, "anthropic")
            raw = await asyncio.wait_for(_call_openrouter(last_error_text), timeout=130)
            return await _parse_program(raw, "openrouter")
        except Exception as exc:
            last_error = exc
            last_error_text = str(exc)
            logger.warning("Workout generation failed attempt=%s error=%s", attempt, exc)

    raise WorkoutGenerationError(f"AI workout generation failed after {max_attempts} attempt(s)") from last_error

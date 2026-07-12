from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNING_DIR = PROJECT_ROOT / "backend" / "sport_research" / "running"
OUTPUT_PATH = RUNNING_DIR / "running_teaching_database.json"

SOURCE_PACK_ID = "running_teaching_database_v1"
INGESTION_METHOD = "running_research_structured_converter_v1"
SPORT = "running_endurance"
LEVELS = ["beginner", "intermediate", "advanced"]

SOURCE_REFS: List[Dict[str, Any]] = [
    {
        "title": "The Training Characteristics of World-Class Distance Runners",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8975965/",
        "source_type": "peer_reviewed_review",
        "organization_or_author": "Haugen et al.",
        "notes": "Used for elite distance running structure, volume, intensity distribution, periodization, and taper principles.",
    },
    {
        "title": "Crossing the Golden Training Divide: The Science and Practice of Training World-Class 800- and 1500-m Runners",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8363530/",
        "source_type": "peer_reviewed_review",
        "organization_or_author": "Haugen et al.",
        "notes": "Used for middle-distance blend of aerobic base, speed, race pace, and periodization.",
    },
    {
        "title": "Effects of Strength Training on Running Economy in Highly Trained Runners",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5015039/",
        "source_type": "peer_reviewed_meta_analysis",
        "organization_or_author": "Denadai et al.",
        "notes": "Used for strength and plyometric support for running economy.",
    },
    {
        "title": "Return to Running Program",
        "url": "https://medicine.osu.edu/-/media/files/medicine/departments/sports-medicine/medical-professionals/rehabilitation-protocols/basic-return-to-running-guideline.pdf",
        "source_type": "sports_medicine_protocol_pdf",
        "organization_or_author": "Ohio State Sports Medicine",
        "notes": "Used for conservative return-to-running stage progression and symptom rules.",
    },
    {
        "title": "Criteria-Based Return to Sprinting Progression Following Lower Extremity Injury",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7134353/",
        "source_type": "peer_reviewed_clinical_commentary",
        "organization_or_author": "Clinical commentary authors",
        "notes": "Used for criteria-based speed exposure and not returning to sprinting based only on time.",
    },
    {
        "title": "Heat-Related Illnesses in Athletes",
        "url": "https://www.cdc.gov/niosh/athletes/heat-illness/index.html",
        "source_type": "public_health_guidance",
        "organization_or_author": "CDC/NIOSH",
        "notes": "Used for heat illness risk, acclimatization, and training modification context.",
    },
    {
        "title": "Couch to 5K Week by Week",
        "url": "https://www.nhs.uk/live-well/exercise/get-running-with-couch-to-5k/",
        "source_type": "public_health_beginner_plan",
        "organization_or_author": "NHS",
        "notes": "Used for beginner run-walk progression logic and habit formation.",
    },
    {
        "title": "World Athletics: Speed Training for Endurance Runners",
        "url": "https://worldathletics.org/be-active/training/speed-training-for-endurance-runners",
        "source_type": "official_sport_education",
        "organization_or_author": "World Athletics",
        "notes": "Used for strides, speed exposure, and endurance-runner speed support.",
    },
]

DOMAINS: Dict[str, Dict[str, Any]] = {
    "run_walk_foundation": {
        "summary": "Use run-walk intervals to build tolerance, habit, and confidence before continuous running.",
        "qualities": ["habit formation", "impact tolerance", "aerobic base", "movement confidence"],
        "risk_flags": ["too_much_too_soon", "shin_pain", "knee_pain", "achilles_pain"],
    },
    "easy_aerobic_base": {
        "summary": "Easy running is the backbone for durable endurance because it builds aerobic capacity with lower mechanical and nervous-system cost.",
        "qualities": ["aerobic base", "capillary density", "recovery support", "volume tolerance"],
        "risk_flags": ["pace_too_hard", "rapid_volume_increase", "poor_recovery"],
    },
    "long_run": {
        "summary": "The long run extends endurance and race-specific durability, but should progress conservatively and not dominate weekly load for beginners.",
        "qualities": ["endurance durability", "fueling practice", "tissue capacity", "mental pacing"],
        "risk_flags": ["excessive_weekly_share", "fueling_errors", "terrain_spike"],
    },
    "threshold_tempo": {
        "summary": "Tempo and threshold running improve sustainable speed and lactate/effort control without becoming all-out racing.",
        "qualities": ["threshold", "sustainable speed", "pacing discipline", "running economy"],
        "risk_flags": ["too_fast", "stacked_intensity", "recovery_debt"],
    },
    "intervals_vo2": {
        "summary": "Interval sessions raise high-end aerobic power and race-specific speed but require a base of easy running and recovery spacing.",
        "qualities": ["VO2 max", "race pace tolerance", "repeat quality", "mechanics under fatigue"],
        "risk_flags": ["overuse", "hamstring_calf_load", "insufficient_base"],
    },
    "speed_strides_hills": {
        "summary": "Strides and short hills maintain speed, coordination, stiffness, and economy with lower volume than full speed sessions.",
        "qualities": ["speed exposure", "neuromuscular coordination", "leg stiffness", "hill strength"],
        "risk_flags": ["sprint_too_soon", "achilles_calf_load", "poor_warmup"],
    },
    "race_specificity": {
        "summary": "Race-specific work links fitness to the target event through pace familiarity, fueling, terrain, and tactical rehearsal.",
        "qualities": ["race pace", "fueling", "pacing", "terrain skill", "taper readiness"],
        "risk_flags": ["late_novelty", "testing_too_often", "taper_misuse"],
    },
    "trail_hill_terrain": {
        "summary": "Trail, hill, and terrain work require downhill control, foot/ankle capacity, pacing by effort, and conservative progression.",
        "qualities": ["hill strength", "downhill control", "ankle stiffness", "effort pacing"],
        "risk_flags": ["downhill_spike", "ankle_sprain", "quad_soreness"],
    },
    "running_strength_conditioning": {
        "summary": "Strength training supports running economy, tissue capacity, posture, and durability when placed around key runs.",
        "qualities": ["running economy", "lower-leg capacity", "trunk stiffness", "single-leg strength", "posterior chain"],
        "risk_flags": ["heavy_lift_before_key_run", "excessive_soreness", "poor_exercise_selection"],
    },
    "return_to_run": {
        "summary": "Return-to-run should use symptom-gated run-walk stages before speed, hills, plyometrics, or race-pace work.",
        "qualities": ["pain monitoring", "impact re-entry", "criteria-based progression", "24-hour response"],
        "risk_flags": ["pain_progression", "sprinting_too_early", "skipping_stages"],
    },
    "heat_environment": {
        "summary": "Heat, humidity, altitude, poor air quality, terrain, and travel change pace targets, hydration needs, and session risk.",
        "qualities": ["heat acclimatization", "effort-based pacing", "hydration", "environmental readiness"],
        "risk_flags": ["heat_illness", "dehydration", "pace_chasing"],
    },
}

RUNNING_WORKOUTS: List[Dict[str, Any]] = [
    {
        "id": "run_workout_run_walk_base",
        "name": "Run-Walk Foundation",
        "workout_type": "run_walk",
        "suitable_user_level": "beginner",
        "goal_tags": ["beginner", "return_to_run", "aerobic_base"],
        "purpose": "Build impact tolerance and aerobic habit without forcing continuous running too early.",
        "structure": ["5-8 min brisk walk warm-up", "alternate 1-3 min easy jog with 1-2 min walk", "20-35 min total", "5 min walk cooldown"],
        "intensity": "easy conversational effort",
        "progression_rule": "Increase total jog time before reducing walk time. Progress only if pain and fatigue are stable over the next 24 hours.",
        "avoid_when": ["sharp pain", "worsening symptoms", "unable to walk briskly pain-free"],
    },
    {
        "id": "run_workout_easy_run",
        "name": "Easy Run",
        "workout_type": "easy_run",
        "suitable_user_level": "all",
        "goal_tags": ["aerobic_base", "recovery", "volume"],
        "purpose": "Develop aerobic base and running durability with low-to-moderate stress.",
        "structure": ["8-10 min gentle build", "20-70 min easy running depending on level", "finish relaxed, not depleted"],
        "intensity": "RPE 3-4 or conversational pace",
        "progression_rule": "Add 5-10 minutes or 5-10% duration only when recovery and tissue response are stable.",
        "avoid_when": ["turning every easy run into tempo", "poor sleep plus high soreness", "pain that changes mechanics"],
    },
    {
        "id": "run_workout_recovery_run",
        "name": "Recovery Run",
        "workout_type": "recovery_run",
        "suitable_user_level": "intermediate",
        "goal_tags": ["recovery", "aerobic_base"],
        "purpose": "Add low-stress circulation and movement between harder training days.",
        "structure": ["15-40 min very easy", "flat route", "optional walk breaks"],
        "intensity": "RPE 2-3",
        "progression_rule": "Keep it short and easy; never progress recovery runs before key sessions recover well.",
        "avoid_when": ["recovery run becomes extra training load", "pain or heavy fatigue"],
    },
    {
        "id": "run_workout_long_run",
        "name": "Long Run",
        "workout_type": "long_run",
        "suitable_user_level": "all",
        "goal_tags": ["endurance", "race_specificity", "aerobic_base"],
        "purpose": "Extend endurance, durability, fueling practice, and confidence for longer events.",
        "structure": ["easy start", "30-150+ min depending on event and level", "optional relaxed finish for trained runners"],
        "intensity": "mostly RPE 3-4",
        "progression_rule": "Increase gradually and deload every 3-5 weeks. Do not spike long run and weekly volume together.",
        "avoid_when": ["beginner long run exceeds too much weekly load", "late fueling novelty", "worsening joint or tendon pain"],
    },
    {
        "id": "run_workout_strides",
        "name": "Strides",
        "workout_type": "strides",
        "suitable_user_level": "all",
        "goal_tags": ["speed", "running_economy", "neuromuscular"],
        "purpose": "Maintain smooth speed and mechanics without a full hard speed session.",
        "structure": ["after easy run or warm-up", "4-8 x 10-20 sec relaxed fast", "walk/jog full recovery"],
        "intensity": "fast but relaxed, not sprinting",
        "progression_rule": "Add reps before speed. Stop if form tightens or calf/Achilles feels reactive.",
        "avoid_when": ["acute calf/Achilles pain", "no warm-up", "all-out sprinting"],
    },
    {
        "id": "run_workout_short_hill_sprints",
        "name": "Short Hill Sprints",
        "workout_type": "hill_sprints",
        "suitable_user_level": "intermediate",
        "goal_tags": ["speed", "power", "hill_strength"],
        "purpose": "Build short acceleration power and stiffness with lower top-speed impact than flat sprinting.",
        "structure": ["thorough warm-up", "4-8 x 8-12 sec uphill", "walk-back/full recovery", "cooldown"],
        "intensity": "powerful but technically clean",
        "progression_rule": "Start with low volume and progress reps slowly; never combine with new speed, hills, and volume spikes.",
        "avoid_when": ["Achilles/calf symptoms", "poor warm-up", "beginner without base"],
    },
    {
        "id": "run_workout_hill_repeats",
        "name": "Hill Repeats",
        "workout_type": "hill_repeats",
        "suitable_user_level": "intermediate",
        "goal_tags": ["strength_endurance", "VO2", "hill_running"],
        "purpose": "Improve uphill strength, aerobic power, and form under controlled load.",
        "structure": ["10-15 min warm-up", "4-10 x 45-120 sec uphill", "easy jog/walk down", "cooldown"],
        "intensity": "RPE 7-8, controlled",
        "progression_rule": "Progress total uphill time before grade or speed. Respect calf/Achilles response.",
        "avoid_when": ["downhill aggravates knee", "Achilles/calf pain", "placed too close to long run"],
    },
    {
        "id": "run_workout_tempo_run",
        "name": "Tempo Run",
        "workout_type": "tempo",
        "suitable_user_level": "intermediate",
        "goal_tags": ["threshold", "sustainable_speed"],
        "purpose": "Build comfortably hard sustainable running and pacing discipline.",
        "structure": ["10-15 min warm-up", "15-35 min continuous tempo", "10 min cooldown"],
        "intensity": "RPE 6-7, controlled, not race effort",
        "progression_rule": "Add 5 minutes only when pace control and recovery are stable.",
        "avoid_when": ["pace becomes time trial", "stacked with interval session without recovery"],
    },
    {
        "id": "run_workout_cruise_intervals",
        "name": "Cruise Intervals",
        "workout_type": "threshold_intervals",
        "suitable_user_level": "intermediate",
        "goal_tags": ["threshold", "pacing", "volume_at_quality"],
        "purpose": "Accumulate threshold work with better quality control than one long tempo.",
        "structure": ["10-15 min warm-up", "3-6 x 4-8 min threshold", "1-2 min easy jog", "cooldown"],
        "intensity": "RPE 6-7",
        "progression_rule": "Add reps or duration before pace. Keep recoveries honest and easy.",
        "avoid_when": ["turning reps into VO2 intervals", "poor readiness"],
    },
    {
        "id": "run_workout_fartlek",
        "name": "Fartlek",
        "workout_type": "fartlek",
        "suitable_user_level": "all",
        "goal_tags": ["speed_play", "threshold", "aerobic_power"],
        "purpose": "Blend speed changes with flexible effort-based pacing, useful when terrain or pace data is imperfect.",
        "structure": ["10 min warm-up", "8-20 x 30 sec to 3 min faster / easy float", "cooldown"],
        "intensity": "varies by rep goal, usually RPE 5-8",
        "progression_rule": "Progress total fast time before intensity. Use effort in heat or hilly terrain.",
        "avoid_when": ["uncontrolled sprinting", "unclear purpose"],
    },
    {
        "id": "run_workout_vo2_intervals",
        "name": "VO2 Intervals",
        "workout_type": "vo2_intervals",
        "suitable_user_level": "advanced",
        "goal_tags": ["VO2", "5k", "10k", "aerobic_power"],
        "purpose": "Improve high-end aerobic power and repeat quality for shorter races.",
        "structure": ["15 min warm-up", "4-8 x 2-5 min hard", "equal or shorter easy jog recovery", "cooldown"],
        "intensity": "RPE 8-9 but not all-out",
        "progression_rule": "Progress one variable at a time: reps, duration, or pace, not all three.",
        "avoid_when": ["beginner base is low", "recent injury", "two hard run days back-to-back"],
    },
    {
        "id": "run_workout_progression_run",
        "name": "Progression Run",
        "workout_type": "progression",
        "suitable_user_level": "intermediate",
        "goal_tags": ["pacing", "aerobic_base", "threshold"],
        "purpose": "Teach controlled pacing by starting easy and finishing moderately stronger.",
        "structure": ["start easy", "gradually progress every 10-15 min", "finish controlled, not sprinting"],
        "intensity": "RPE 3 to 6-7",
        "progression_rule": "Progress finish duration before finish speed.",
        "avoid_when": ["turning into race effort", "poor recovery after previous hard day"],
    },
    {
        "id": "run_workout_race_pace_repeats",
        "name": "Race-Pace Repeats",
        "workout_type": "race_pace",
        "suitable_user_level": "intermediate",
        "goal_tags": ["race_specificity", "pacing"],
        "purpose": "Build familiarity with target race pace without racing the workout.",
        "structure": ["warm-up", "short-to-moderate repeats at target race pace", "easy jog recoveries", "cooldown"],
        "intensity": "event-specific, controlled",
        "progression_rule": "Increase total race-pace volume across the block, then taper into the race.",
        "avoid_when": ["target pace is unrealistic", "race-pace work too close to race without taper"],
    },
    {
        "id": "run_workout_marathon_pace",
        "name": "Marathon-Pace Run",
        "workout_type": "marathon_pace",
        "suitable_user_level": "advanced",
        "goal_tags": ["marathon", "fueling", "race_specificity"],
        "purpose": "Practice marathon rhythm, fueling, and durable pacing.",
        "structure": ["easy warm-up", "20-75 min at marathon effort within longer run", "fueling rehearsal"],
        "intensity": "steady, controlled marathon effort",
        "progression_rule": "Increase marathon-pace time only when long-run recovery and fueling are stable.",
        "avoid_when": ["poor fueling", "heat without pace adjustment", "beginner marathon build"],
    },
    {
        "id": "run_workout_trail_hill_endurance",
        "name": "Trail/Hill Endurance Run",
        "workout_type": "trail_hill",
        "suitable_user_level": "intermediate",
        "goal_tags": ["trail", "hill", "terrain"],
        "purpose": "Build terrain skill, effort pacing, downhill control, and foot/ankle capacity.",
        "structure": ["easy effort by terrain", "controlled climbs", "careful descents", "time-on-feet focus"],
        "intensity": "effort-based, not pace-based",
        "progression_rule": "Progress elevation, technicality, or duration one at a time.",
        "avoid_when": ["acute ankle/knee pain", "large downhill spike", "racing technical terrain in training"],
    },
    {
        "id": "run_workout_benchmark_time_trial",
        "name": "Benchmark Time Trial",
        "workout_type": "benchmark",
        "suitable_user_level": "intermediate",
        "goal_tags": ["benchmark", "pacing", "fitness_check"],
        "purpose": "Check fitness and calibrate training paces without frequent racing.",
        "structure": ["full warm-up", "1-mile/3K/5K controlled time trial depending on level", "cooldown"],
        "intensity": "hard, controlled test",
        "progression_rule": "Use sparingly every 4-8 weeks. Do not test during pain spikes or deload need.",
        "avoid_when": ["testing too often", "poor readiness", "injury return phase"],
    },
    {
        "id": "run_workout_cross_training_aerobic",
        "name": "Low-Impact Aerobic Cross-Training",
        "workout_type": "cross_training",
        "suitable_user_level": "all",
        "goal_tags": ["aerobic_base", "return_to_run", "injury_management"],
        "purpose": "Maintain aerobic work while reducing impact load.",
        "structure": ["bike, elliptical, swim, or row", "20-60 min easy to moderate", "optional intervals for trained runners"],
        "intensity": "RPE 3-6 depending on goal",
        "progression_rule": "Use to support, not replace, progressive run tolerance unless impact is limited.",
        "avoid_when": ["turning every recovery day into hard conditioning"],
    },
]

RUNNING_PLAN_RULES: List[Dict[str, Any]] = [
    {
        "id": "running_rule_easy_majority",
        "rule_type": "intensity_distribution",
        "applies_to": ["running_endurance", "all_runners"],
        "rule": "Most weekly running should be easy enough to support consistency and recovery; hard sessions are selected, not constant.",
        "recommended_action": ["bias beginner and high-stress users toward easy/run-walk work", "limit hard running to 1-2 days weekly for most recreational runners"],
        "blocked_action": ["do not make every run tempo or intervals"],
    },
    {
        "id": "running_rule_progress_one_variable",
        "rule_type": "progression",
        "applies_to": ["running_endurance", "all_runners"],
        "rule": "Progress one major stressor at a time: volume, intensity, terrain, long-run length, or speed exposure.",
        "recommended_action": ["increase duration before intensity for beginners", "deload after multi-week build"],
        "blocked_action": ["do not increase weekly volume and interval intensity in the same week after poor readiness"],
    },
    {
        "id": "running_rule_hard_days_spacing",
        "rule_type": "weekly_structure",
        "applies_to": ["running_endurance", "all_runners"],
        "rule": "Separate hard run sessions with easy or rest days unless the user is advanced and specifically tolerates dense training.",
        "recommended_action": ["place intervals, tempo, hills, and long-run quality apart", "use easy running or cross-training between stress days"],
        "blocked_action": ["avoid back-to-back hard run days for beginners and injured runners"],
    },
    {
        "id": "running_rule_long_run_share",
        "rule_type": "long_run",
        "applies_to": ["running_endurance"],
        "rule": "The long run should build durability but should not become an uncontrolled weekly load spike.",
        "recommended_action": ["cap beginner long-run growth", "deload long run every 3-5 weeks", "practice fueling for longer events"],
        "blocked_action": ["avoid long run jumps after missed weeks or pain flares"],
    },
    {
        "id": "running_rule_return_to_run_symptom_gate",
        "rule_type": "return_to_run",
        "applies_to": ["running_endurance", "return_to_training"],
        "rule": "Return-to-run progression must be guided by pain, mechanics, and 24-hour response before speed, hills, or racing.",
        "recommended_action": ["use run-walk stages", "repeat or regress stage if symptoms increase", "cross-train for aerobic work if impact is reactive"],
        "blocked_action": ["avoid sprinting, hills, plyometrics, or race pace before continuous easy running is tolerated"],
    },
    {
        "id": "running_rule_speed_after_base",
        "rule_type": "speed_exposure",
        "applies_to": ["running_endurance"],
        "rule": "Strides and speed exposure should be short, warm, relaxed, and only progressed after easy running tolerance is stable.",
        "recommended_action": ["start with relaxed strides", "use full recovery", "stop before mechanics tighten"],
        "blocked_action": ["avoid max sprinting with calf, Achilles, hamstring, or return-to-run flags"],
    },
    {
        "id": "running_rule_strength_support",
        "rule_type": "strength_conditioning",
        "applies_to": ["running_endurance"],
        "rule": "Strength training should support running economy, tissue capacity, posture, and durability without compromising key run quality.",
        "recommended_action": ["include calf/soleus, posterior chain, single-leg control, trunk stiffness", "place heavy strength away from key run sessions"],
        "blocked_action": ["avoid high-soreness lower-body lifting before key workouts or races"],
    },
    {
        "id": "running_rule_heat_adjustment",
        "rule_type": "environment",
        "applies_to": ["running_endurance"],
        "rule": "In heat, humidity, altitude, or poor air quality, prescribe effort and safety constraints rather than chasing normal paces.",
        "recommended_action": ["reduce pace expectations", "shorten or move sessions", "prioritize hydration and acclimatization"],
        "blocked_action": ["avoid hard pace targets in unsafe heat or when heat illness symptoms appear"],
    },
    {
        "id": "running_rule_taper_volume_not_fitness",
        "rule_type": "taper",
        "applies_to": ["running_endurance"],
        "rule": "Race taper should reduce fatigue mainly by reducing volume while preserving some rhythm and specificity.",
        "recommended_action": ["keep short race-pace touches if appropriate", "avoid new exercises, terrain, or shoes near race day"],
        "blocked_action": ["do not add last-minute hard workouts to gain fitness"],
    },
    {
        "id": "running_rule_pace_by_goal_and_level",
        "rule_type": "pacing",
        "applies_to": ["running_endurance"],
        "rule": "Use RPE/conversation tests for beginners and heat/terrain; use pace zones only when benchmark data is reliable.",
        "recommended_action": ["calibrate with recent race/time trial when available", "use effort-based targets when data is stale"],
        "blocked_action": ["avoid exact race pace prescriptions from guessed fitness"],
    },
]


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


def _sport_profile(planning_rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": "sport_profile_running_endurance",
        "sport": SPORT,
        "planning_summary": "Running endurance planning balances easy aerobic volume, long-run durability, targeted threshold/interval/speed work, strength support, conservative injury-risk progression, terrain/environment adjustment, and tapering toward target events.",
        "training_priorities": [
            "consistent easy aerobic volume",
            "gradual long-run development",
            "threshold and tempo work when base supports it",
            "interval/VO2 work for race-specific performance",
            "strides, hills, and speed exposure with full warm-up",
            "calf, soleus, Achilles, hamstring, hip, and trunk capacity",
            "race-specific pace, terrain, fueling, and taper planning",
            "return-to-run symptom gating after pain or breaks",
            "environment-aware pacing in heat, humidity, altitude, and terrain",
        ],
        "key_physical_qualities": [
            "aerobic base",
            "running economy",
            "threshold",
            "VO2 max",
            "speed endurance",
            "lower-leg tissue capacity",
            "calf and soleus endurance",
            "hip control",
            "trunk stiffness",
            "hamstring resilience",
            "fueling tolerance",
            "terrain-specific durability",
        ],
        "realistic_weekly_frequency": {
            "beginner": {"run_sessions": "3-4", "quality_sessions": "0-1", "strength_sessions": "2", "long_run": "short/easy or run-walk"},
            "intermediate": {"run_sessions": "4-6", "quality_sessions": "1-2", "strength_sessions": "2-3", "long_run": "weekly with deloads"},
            "advanced": {"run_sessions": "5-10", "quality_sessions": "2-3", "strength_sessions": "2-3", "long_run": "event-specific"},
        },
        "common_injury_or_load_risks": [
            "shin splints or tibial stress reaction",
            "Achilles or calf overload",
            "patellofemoral knee pain",
            "IT band irritation",
            "plantar fascia irritation",
            "hamstring strain during speed exposure",
            "bone stress injury risk from rapid volume/intensity change",
            "heat illness or dehydration",
        ],
        "do_not_pair": [
            "new interval intensity with new weekly volume spike",
            "hard hills or sprints with calf/Achilles symptoms",
            "heavy lower-body strength immediately before key intervals, tempo, or race",
            "long run progression with poor 24-hour pain response",
            "new shoes, terrain, fueling, or workouts close to race day",
        ],
        "progression_guardrails": [
            "progress one variable at a time",
            "use 24-hour pain and soreness response before adding impact",
            "separate hard run sessions with easy/rest days for most users",
            "deload after multi-week builds or if readiness declines",
            "use effort-based pacing in heat, hills, altitude, or poor data conditions",
        ],
        "planning_rule_ids": [rule["id"] for rule in planning_rules[:16]],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs(),
    }


def _sport_training_rules() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain, data in DOMAINS.items():
        docs.append(
            {
                "id": f"running_training_rule_{domain}",
                "sport": SPORT,
                "domain": domain,
                "category": "running_domain_rule",
                "condition": data["summary"][:240],
                "rule": data["summary"],
                "recommended_action": data.get("qualities") or [],
                "blocked_action": data.get("risk_flags") or [],
                "retrieval_tags": sorted(set([SPORT, "running", domain, *data.get("qualities", []), *data.get("risk_flags", [])])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _planning_rules() -> List[Dict[str, Any]]:
    return [
        {
            "id": f"running_plan_{rule['id'].replace('running_rule_', '')}",
            "sport": SPORT,
            "category": rule["rule_type"],
            "applies_to": ["running", "running_endurance"],
            "priority": 92 if rule["rule_type"] in {"return_to_run", "environment"} else 78,
            "rule": rule["rule"],
            "recommended_action": rule["recommended_action"],
            "blocked_action": rule["blocked_action"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        }
        for rule in RUNNING_PLAN_RULES
    ]


def _teaching_progressions() -> List[Dict[str, Any]]:
    domains = list(DOMAINS.keys())
    docs: List[Dict[str, Any]] = []
    for domain in domains:
        for level in LEVELS:
            docs.append(
                {
                    "id": f"running_teach_{domain}_{level}",
                    "sport": SPORT,
                    "domain": domain,
                    "level": level,
                    "role_tags": ["all_roles", _event_tag_for_domain(domain)],
                    "learning_goal": f"Develop {domain.replace('_', ' ')} for a {level} runner with safe load progression and clear pacing intent.",
                    "suitable_for": [f"{level} runners", "running endurance training"],
                    "prerequisites": _prerequisites(domain, level),
                    "teaching_priorities": _teaching_priorities(domain, level),
                    "technical_focus": _technical_focus(domain, level),
                    "tactical_focus": _tactical_focus(domain, level),
                    "physical_support": DOMAINS[domain]["qualities"],
                    "practice_design": _practice_design(domain, level),
                    "typical_drills": _practice_design(domain, level),
                    "avoid_until_ready": _avoid_until_ready(domain, level),
                    "progression_signals": _progression_signals(domain, level),
                    "coach_notes": [
                        "Prescribe purpose first, then pace. If pace data is unreliable, use RPE or talk-test targets.",
                        "The next session should respond to pain, fatigue, sleep, terrain, and previous workout completion.",
                    ],
                    "retrieval_tags": sorted(set([SPORT, "running", domain, level, *DOMAINS[domain]["qualities"], *DOMAINS[domain]["risk_flags"]])),
                    "source_pack_id": SOURCE_PACK_ID,
                    "source_refs": _source_refs(),
                }
            )
    return docs


def _event_tag_for_domain(domain: str) -> str:
    if domain in {"threshold_tempo", "intervals_vo2", "speed_strides_hills"}:
        return "5k_10k"
    if domain in {"long_run", "race_specificity"}:
        return "half_marathon_marathon"
    if domain == "trail_hill_terrain":
        return "trail_running"
    return "all_events"


def _prerequisites(domain: str, level: str) -> List[str]:
    if domain == "return_to_run":
        return ["walk briskly without symptom escalation", "pain response stable over 24 hours"]
    if level == "beginner":
        return ["can complete easy walking or run-walk session", "no sharp or worsening pain"]
    if level == "intermediate":
        return ["stable easy running base", "can recover from one moderate quality session weekly"]
    return ["stable multi-week base", "reliable recovery markers", "recent benchmark or race context"]


def _teaching_priorities(domain: str, level: str) -> List[str]:
    priorities = {
        "beginner": ["consistency", "easy effort", "run-walk tolerance", "pain monitoring"],
        "intermediate": ["pacing control", "weekly structure", "one or two quality sessions", "strength support"],
        "advanced": ["event specificity", "load management", "taper timing", "benchmark-driven paces"],
    }
    return priorities[level] + DOMAINS[domain]["qualities"][:3]


def _technical_focus(domain: str, level: str) -> List[str]:
    base = ["relaxed posture", "quiet arm carriage", "cadence and stride controlled by effort", "no mechanics change from pain"]
    if domain in {"speed_strides_hills", "intervals_vo2"}:
        base.extend(["thorough warm-up", "run fast relaxed, not strained", "full recovery for quality"])
    if domain in {"trail_hill_terrain", "long_run"}:
        base.extend(["effort-based pacing", "terrain-aware stride", "downhill control"])
    if domain == "return_to_run":
        base.extend(["stop before limp or compensation", "repeat stage if 24-hour response worsens"])
    return base


def _tactical_focus(domain: str, level: str) -> List[str]:
    if domain == "race_specificity":
        return ["target pace familiarity", "fueling rehearsal", "race-day pacing plan", "late-race restraint"]
    if domain == "heat_environment":
        return ["pace by effort", "route timing", "hydration plan", "session shortening options"]
    if level == "advanced":
        return ["phase-specific stress placement", "fitness testing restraint", "taper decisions"]
    return ["purposeful session selection", "effort awareness", "recovery-aware progression"]


def _practice_design(domain: str, level: str) -> List[str]:
    if domain == "run_walk_foundation":
        return ["run-walk intervals", "brisk walk warm-up", "short easy jog bouts", "walk cooldown"]
    if domain == "easy_aerobic_base":
        return ["easy run by talk test", "short loop route", "optional relaxed strides for trained users"]
    if domain == "long_run":
        return ["easy long run", "fueling practice for longer sessions", "deload long run every few weeks"]
    if domain == "threshold_tempo":
        return ["continuous tempo", "cruise intervals", "progression run finish"]
    if domain == "intervals_vo2":
        return ["2-5 minute intervals", "equal/easy jog recovery", "controlled cool-down"]
    if domain == "speed_strides_hills":
        return ["4-8 relaxed strides", "short hill sprints", "full recovery"]
    if domain == "trail_hill_terrain":
        return ["effort-based trail run", "controlled hill repeats", "downhill technique exposure"]
    if domain == "running_strength_conditioning":
        return ["calf/soleus capacity", "single-leg strength", "posterior-chain strength", "trunk stiffness"]
    if domain == "return_to_run":
        return ["walk-jog stages", "repeat stage if symptoms rise", "cross-train for aerobic load"]
    if domain == "heat_environment":
        return ["time-of-day adjustment", "effort-based run", "hydration and cooling plan"]
    return ["event-specific run session"]


def _avoid_until_ready(domain: str, level: str) -> List[str]:
    avoid = ["pain that changes mechanics", "rapid load spike"]
    if level == "beginner":
        avoid.extend(["VO2 intervals", "max sprinting", "long-run jumps"])
    if domain in {"speed_strides_hills", "intervals_vo2"}:
        avoid.extend(["calf/Achilles/hamstring symptoms", "no warm-up"])
    if domain == "return_to_run":
        avoid.extend(["speed, hills, plyometrics, or race pace before easy running tolerance"])
    return _dedupe(avoid)


def _progression_signals(domain: str, level: str) -> List[str]:
    signals = ["24-hour pain response stable", "session completed at target RPE", "no limp or mechanics compensation"]
    if level in {"intermediate", "advanced"}:
        signals.extend(["key sessions recovered within expected time", "paces or RPE consistent across reps"])
    if domain == "race_specificity":
        signals.extend(["fueling practiced without GI issue", "target pace based on recent evidence"])
    return signals


def _skill_assessments() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for domain in DOMAINS:
        docs.append(
            {
                "id": f"running_assess_{domain}",
                "sport": SPORT,
                "domain": domain,
                "summary": f"Assesses {domain.replace('_', ' ')} through completion, pacing control, recovery, pain response, and event transfer.",
                "metrics": _assessment_metrics(domain),
                "level_bands": [
                    {
                        "level": "beginner",
                        "indicators": ["uses easy effort", "can complete run-walk/easy work", "no 24-hour pain escalation"],
                        "ready_for_next_when": ["2-4 weeks consistent", "completion is stable", "no mechanics-compensating pain"],
                    },
                    {
                        "level": "intermediate",
                        "indicators": ["can structure easy, long, and one quality session", "recovers predictably", "controls pacing"],
                        "ready_for_next_when": ["consistent progression across block", "readiness supports another quality or event-specific layer"],
                    },
                    {
                        "level": "advanced",
                        "indicators": ["uses phase-specific training", "handles race-specific work", "tapers and adjusts by evidence"],
                        "ready_for_next_when": ["stable load, benchmark, and race execution trends"],
                    },
                ],
                "hold_if": [
                    "pain worsens during or 24 hours after running",
                    "fatigue disrupts easy pace or mechanics",
                    "rapid volume, intensity, terrain, or shoe change",
                    "heat illness symptoms or unsafe environment",
                ],
                "retrieval_tags": sorted(set([SPORT, "running", domain, "assessment", *_assessment_metrics(domain)])),
                "source_pack_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(),
            }
        )
    return docs


def _assessment_metrics(domain: str) -> List[str]:
    base = ["completion rate", "target RPE control", "24-hour pain response", "mechanics quality", "recovery response"]
    specific = {
        "easy_aerobic_base": ["talk-test control", "weekly easy volume tolerance"],
        "long_run": ["long-run duration tolerance", "fueling response", "late-run form"],
        "threshold_tempo": ["controlled comfortably-hard effort", "rep/tempo consistency"],
        "intervals_vo2": ["repeat quality", "recovery between reps"],
        "speed_strides_hills": ["relaxed speed", "calf/Achilles response", "full recovery discipline"],
        "return_to_run": ["stage completion", "symptom-free next day", "walk-jog mechanics"],
        "heat_environment": ["effort adjustment", "hydration/cooling response"],
        "running_strength_conditioning": ["strength session soreness", "run quality after lifting"],
    }
    return _dedupe([*specific.get(domain, []), *base])


def _level_transition_rules() -> List[Dict[str, Any]]:
    return [
        {
            "id": "running_beginner_to_intermediate",
            "sport": SPORT,
            "from_level": "beginner",
            "to_level": "intermediate",
            "applies_to": ["all_roles", "all_events"],
            "minimum_evidence": [
                "4+ weeks or 8+ completed run/S&C sessions",
                "85%+ completion across planned easy/run-walk sessions",
                "no worsening pain or mechanics compensation",
                "can complete continuous easy run or stable run-walk base",
            ],
            "promote_when": ["easy running is reliable", "RPE control is honest", "strength support does not disrupt runs"],
            "hold_when": ["pain trend worsens", "easy runs become hard", "long-run or volume spikes create missed sessions"],
            "backend_action": "Unlock one controlled quality layer such as strides, short hills, fartlek, or tempo intervals based on goal.",
            "retrieval_tags": ["running", "beginner", "intermediate", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "running_intermediate_to_advanced",
            "sport": SPORT,
            "from_level": "intermediate",
            "to_level": "advanced",
            "applies_to": ["all_roles", "5k_10k", "half_marathon_marathon", "trail_running"],
            "minimum_evidence": [
                "8+ additional weeks or 16+ completed run/S&C sessions",
                "consistent easy volume and long-run tolerance",
                "can recover from 1-2 quality sessions per week",
                "recent benchmark or race supports pace targets",
            ],
            "promote_when": ["load is stable", "race-specific work is tolerated", "readiness and pain trends are clean"],
            "hold_when": ["injury flags unresolved", "quality sessions cause repeated missed runs", "pace targets are guessed or unrealistic"],
            "backend_action": "Unlock event-specific blocks, more precise pace zones, and advanced race-prep/taper planning.",
            "retrieval_tags": ["running", "intermediate", "advanced", "level_review"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
        },
        {
            "id": "running_hold_or_regress",
            "sport": SPORT,
            "from_level": "any",
            "to_level": "hold_or_regress",
            "applies_to": ["all_roles", "all_events"],
            "minimum_evidence": ["pain, readiness, or completion risk"],
            "promote_when": [],
            "hold_when": [
                "pain changes running mechanics",
                "24-hour symptoms worsen",
                "completion below 65%",
                "long break from running",
                "heat illness symptoms or unsafe conditions",
            ],
            "backend_action": "Bias next block toward easy/run-walk, cross-training, strength capacity, or deload until response stabilizes.",
            "retrieval_tags": ["running", "regression", "return_to_run", "safety"],
            "source_pack_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(),
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


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()
    docs = []
    for index, domain in enumerate(DOMAINS, start=120001):
        docs.append(
            {
                "id": f"running_section_{domain}",
                "source_book_id": SOURCE_PACK_ID,
                "source_pack_id": SOURCE_PACK_ID,
                "section_order": index,
                "section_title": domain.replace("_", " ").title(),
                "domain": domain,
                "topics": _dedupe(["running", SPORT, domain, *DOMAINS[domain]["qualities"], *DOMAINS[domain]["risk_flags"]]),
                "summary": DOMAINS[domain]["summary"],
                "source_refs": _source_refs(),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def build_database_payload() -> Dict[str, Any]:
    plan_rules = _planning_rules()
    collections = {
        "source_sections": _source_sections(),
        "sport_profiles": [_sport_profile(plan_rules)],
        "sport_training_rules": _sport_training_rules(),
        "planning_rules": plan_rules,
        "sport_teaching_progressions": _teaching_progressions(),
        "sport_skill_assessments": _skill_assessments(),
        "sport_level_transition_rules": _level_transition_rules(),
        "running_workouts": [{**record, "sport": SPORT} for record in RUNNING_WORKOUTS],
        "running_plan_rules": [{**record, "sport": SPORT} for record in RUNNING_PLAN_RULES],
    }
    return {
        "metadata": {
            "source_pack_id": SOURCE_PACK_ID,
            "sport": SPORT,
            "created_at": datetime.utcnow().isoformat(),
            "ingestion_method": INGESTION_METHOD,
            "collection_counts": {name: len(records) for name, records in collections.items()},
        },
        "source_registry": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Running Endurance Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "App-facing running endurance teaching, workout type, planning, safety, return-to-run, and race-preparation records.",
                "evidence_rank": 82,
                "source_refs": SOURCE_REFS,
            }
        ],
        "knowledge_sources": [
            {
                "id": SOURCE_PACK_ID,
                "source_book_id": SOURCE_PACK_ID,
                "title": "SFTC Running Endurance Teaching Database",
                "source_type": "sport_research_synthesis",
                "sport": SPORT,
                "summary": "Normalized running knowledge pack for retrieval and AI workout generation.",
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
    RUNNING_DIR.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser(description="Convert running endurance research into app-facing Mongo records.")
    parser.add_argument("--export-only", action="store_true", help="Write JSON export without inserting into MongoDB.")
    args = parser.parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    print(json.dumps({"output_path": str(OUTPUT_PATH), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()

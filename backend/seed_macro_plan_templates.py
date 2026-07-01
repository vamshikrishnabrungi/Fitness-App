#!/usr/bin/env python3
"""Seed additional macro-plan templates that fill the coverage gaps in the original 6.

Each template's phase structure is grounded in an established, cited periodization framework (see
source_refs). They are AI-drafted from those frameworks and marked needs-review — a qualified S&C
coach should validate before production use. Run:  python -m backend.seed_macro_plan_templates

NOTE: selection also requires matching rules in macro_plan_service._template_score (added alongside).
"""
from __future__ import annotations

import os
from datetime import datetime

from pymongo import MongoClient


def _db():
    mongo_url, db_name = "mongodb://localhost:27017", "test_database"
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, errors="ignore"):
            line = line.strip()
            if line.startswith("MONGO_URL="):
                mongo_url = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("DB_NAME="):
                db_name = line.split("=", 1)[1].strip().strip('"').strip("'")
    return MongoClient(mongo_url)[db_name]


TEMPLATES = [
    {
        "id": "template_hypertrophy_physique_16w",
        "name": "Hypertrophy / Physique 16 Weeks",
        "macro_length_weeks": 16,
        "applies_when": ["muscle_gain", "physique", "bodybuilding", "hypertrophy_goal", "off_season", "aesthetics"],
        "phase_sequence": [
            {"phase": "accumulation_meso_1", "weeks": "1-5", "gym_frequency": "4-6", "sport_frequency": "0-1",
             "primary_goals": ["work_capacity", "muscle_growth_base", "mind_muscle_connection", "movement_quality"],
             "progression_logic": "Start each muscle near MEV (~10-12 sets/wk); add 1-2 sets/wk toward MRV; effort RIR 3-4 -> 1-2.",
             "deload_logic": "Week 5 deload: ~50% volume, RIR 4-5, resensitize before next meso."},
            {"phase": "accumulation_meso_2", "weeks": "6-10", "gym_frequency": "4-6", "sport_frequency": "0-1",
             "primary_goals": ["hypertrophy_primary", "weak_point_bias", "progressive_overload"],
             "progression_logic": "Repeat MEV->MRV with a slightly higher starting volume than meso 1; 8-15 reps @ 65-80% 1RM; RIR 2-3 -> 0-1.",
             "deload_logic": "Week 10 deload week."},
            {"phase": "intensification_metabolite", "weeks": "11-14", "gym_frequency": "4-5", "sport_frequency": "0-1",
             "primary_goals": ["hypertrophy", "heavier_load_bias", "metabolite_finishers", "strength_maintenance"],
             "progression_logic": "Bias 6-12 rep loads with added load week to week; keep a metabolite finisher; RIR 1-2 -> 0.",
             "deload_logic": "Week 14 deload."},
            {"phase": "consolidation_testing", "weeks": "15-16", "gym_frequency": "3-4", "sport_frequency": "0-1",
             "primary_goals": ["deload", "photos_and_measurements", "maintenance", "next_block_selection"],
             "progression_logic": "Light maintenance + reassess body composition and lift progress.",
             "deload_logic": "Full deload / transition."},
        ],
        "source_refs": [
            {"title": "Renaissance Periodization — hypertrophy mesocycles & volume landmarks (MEV/MAV/MRV)", "url": "https://rpstrength.com/blogs/articles/in-defense-of-set-increases-within-the-hypertrophy-mesocycle", "type": "practitioner"},
            {"title": "Mesocycles and Periodization for Hypertrophy", "url": "https://mesostrength.com/blog/mesocycles-and-periodization-for-hypertrophy", "type": "practitioner"},
        ],
    },
    {
        "id": "template_fatloss_recomp_12w",
        "name": "Fat Loss / Recomposition 12 Weeks",
        "macro_length_weeks": 12,
        "applies_when": ["fat_loss", "weight_loss", "recomposition", "get_lean", "cut", "general_fitness_weight"],
        "phase_sequence": [
            {"phase": "priming", "weeks": "1-2", "gym_frequency": "3-4", "sport_frequency": "1-3",
             "primary_goals": ["establish_moderate_deficit", "high_protein", "strength_baseline", "movement_quality"],
             "progression_logic": "Set a moderate deficit (~300-500 kcal / 10-15% below maintenance); protein 1.6-2.2 g/kg; keep lifting loads.",
             "deload_logic": "n/a (onboarding)."},
            {"phase": "recomp_block_1", "weeks": "3-6", "gym_frequency": "3-5", "sport_frequency": "2-3",
             "primary_goals": ["preserve_strength_heavy_compounds", "conditioning_density", "deficit_adherence"],
             "progression_logic": "Hold or progress key compound lifts (defends muscle in a deficit); add 2-3 metabolic conditioning sessions/wk.",
             "deload_logic": "Week 6 lighter lifting week."},
            {"phase": "refeed_diet_break", "weeks": "7", "gym_frequency": "3", "sport_frequency": "1-2",
             "primary_goals": ["maintenance_calories", "hormonal_psychological_recovery", "hold_training"],
             "progression_logic": "Calories to maintenance for one week; reduce conditioning volume; keep lifting.",
             "deload_logic": "Diet-break / refeed week to sustain adherence and muscle."},
            {"phase": "recomp_block_2", "weeks": "8-11", "gym_frequency": "3-5", "sport_frequency": "2-3",
             "primary_goals": ["preserve_strength", "increase_conditioning_intensity", "resume_deficit", "weak_point_muscle"],
             "progression_logic": "Resume deficit; intensify conditioning (intervals/circuits); maintain heavy compound stimulus.",
             "deload_logic": "Week 11 lighter."},
            {"phase": "consolidation_reverse", "weeks": "12", "gym_frequency": "3", "sport_frequency": "1-2",
             "primary_goals": ["reassess_body_comp", "transition_to_maintenance_or_reverse", "retest_strength"],
             "progression_logic": "Reassess; step calories back toward maintenance; plan next block.",
             "deload_logic": "Transition week."},
        ],
        "source_refs": [
            {"title": "Losing Fat Without Losing Muscle — science-backed recomposition (protein, deficit, strength)", "url": "https://www.bodyspec.com/blog/post/losing_fat_without_losing_muscle_sciencebacked_body_recomposition_guide", "type": "review"},
            {"title": "Body Recomposition — How to Lose Fat and Gain Muscle (Healthline)", "url": "https://www.healthline.com/nutrition/body-recomposition", "type": "review"},
        ],
    },
    {
        "id": "template_endurance_base_16w",
        "name": "Endurance Base & Race Build 16 Weeks",
        "macro_length_weeks": 16,
        "applies_when": ["endurance", "marathon", "half_marathon", "10k", "5k", "running", "aerobic_fitness"],
        "phase_sequence": [
            {"phase": "aerobic_base", "weeks": "1-6", "gym_frequency": "1-2", "sport_frequency": "4-6",
             "primary_goals": ["aerobic_base_volume", "easy_dominant_80_20", "weekly_threshold_touch", "long_run_progression", "running_economy_strength"],
             "progression_logic": "Grow weekly volume 5-10% with a cutback every 3-4 weeks; ~80% easy / 20% harder (polarized); long run builds gradually.",
             "deload_logic": "Cutback week every 3-4 weeks: -20-30% volume."},
            {"phase": "specific_build", "weeks": "7-12", "gym_frequency": "1-2", "sport_frequency": "4-6",
             "primary_goals": ["race_pace_progression", "threshold_cruise_intervals", "long_run_to_race_specific", "lactate_threshold"],
             "progression_logic": "Add race-pace segments to long runs; weekly threshold/interval work; keep 80/20 distribution.",
             "deload_logic": "Cutback week ~week 10."},
            {"phase": "peak_specificity", "weeks": "13-14", "gym_frequency": "1", "sport_frequency": "4-5",
             "primary_goals": ["race_specific_workouts", "sharpening", "dress_rehearsal_long_run"],
             "progression_logic": "Highest race-specific quality at controlled volume; final long effort.",
             "deload_logic": "Begin easing volume."},
            {"phase": "taper", "weeks": "15-16", "gym_frequency": "0-1", "sport_frequency": "3-4",
             "primary_goals": ["reduce_volume_hold_intensity", "freshness", "race_readiness"],
             "progression_logic": "Exponential taper: cut volume ~60% while keeping a little intensity; arrive fresh.",
             "deload_logic": "Taper (this whole block is the taper)."},
        ],
        "source_refs": [
            {"title": "16-Week Marathon Training Plan — base/build/peak/taper physiology", "url": "https://marathonhandbook.com/16-week-marathon-training-plan/", "type": "practitioner"},
            {"title": "80/20 polarized intensity distribution (Seiler) for distance runners", "url": "https://runningwithrock.com/80-20-marathon-training-plans/", "type": "practitioner"},
        ],
    },
    {
        "id": "template_hybrid_strength_endurance_12w",
        "name": "Hybrid Strength-Endurance 12 Weeks",
        "macro_length_weeks": 12,
        "applies_when": ["hybrid", "hyrox", "functional_fitness", "strength_and_endurance", "tactical", "obstacle_race"],
        "phase_sequence": [
            {"phase": "base_capacity", "weeks": "1-4", "gym_frequency": "3-4", "sport_frequency": "3",
             "primary_goals": ["aerobic_base", "strength_foundation", "movement_quality", "interference_management"],
             "progression_logic": "Build both at low-moderate intensity; separate hard strength and endurance by 6-24h; cap endurance at <=3 days/wk.",
             "deload_logic": "Light week 4 if fatigue accumulates."},
            {"phase": "concurrent_build", "weeks": "5-8", "gym_frequency": "3-4", "sport_frequency": "3",
             "primary_goals": ["max_strength_bias", "threshold_and_intervals", "station_specific_work", "fatigue_management"],
             "progression_logic": "Alternate strength-emphasis and endurance-emphasis days; if combined, lift before conditioning to limit interference.",
             "deload_logic": "Week 8 deload."},
            {"phase": "specific_integration", "weeks": "9-11", "gym_frequency": "3", "sport_frequency": "3-4",
             "primary_goals": ["event_specific_combined_efforts", "work_capacity_under_load", "pacing", "grip_and_carries"],
             "progression_logic": "Hybrid sessions combining stations + running (e.g. HYROX-style); raise specificity and density.",
             "deload_logic": "Manage by autoregulation."},
            {"phase": "taper_test", "weeks": "12", "gym_frequency": "2-3", "sport_frequency": "2-3",
             "primary_goals": ["freshness", "retest", "event_readiness"],
             "progression_logic": "Reduce volume, hold intensity, rehearse pacing.",
             "deload_logic": "Taper week."},
        ],
        "source_refs": [
            {"title": "Minimising the interference effect in concurrent strength & endurance — programming recommendations", "url": "https://www.researchgate.net/publication/319503195_Minimising_the_interference_effect_during_programmes_of_concurrent_strength_and_endurance_training_Part_2_Programming_recommendations", "type": "review"},
            {"title": "Concurrent Training and the Interference Effect (Barbell Medicine)", "url": "https://www.barbellmedicine.com/blog/concurrent-training-and-the-interference-effect/", "type": "practitioner"},
        ],
    },
    {
        "id": "template_strength_peaking_14w",
        "name": "Strength Peaking (Meet Prep) 14 Weeks",
        "macro_length_weeks": 14,
        "applies_when": ["powerlifting", "max_strength", "peaking", "competition_lift", "meet_prep", "1rm_goal"],
        "phase_sequence": [
            {"phase": "hypertrophy_accumulation", "weeks": "1-5", "gym_frequency": "4", "sport_frequency": "0",
             "primary_goals": ["muscle_and_work_capacity", "technique_volume", "weak_points", "load_65_75pct_1rm"],
             "progression_logic": "Higher-volume 6-12 reps at ~65-75% 1RM; add sets/load weekly; build the tissue that expresses strength.",
             "deload_logic": "Week 5 deload."},
            {"phase": "strength_development", "weeks": "6-10", "gym_frequency": "4", "sport_frequency": "0",
             "primary_goals": ["max_strength", "competition_lift_specificity", "load_70_85pct_1rm", "reduce_volume_raise_intensity"],
             "progression_logic": "3-6 reps at ~70-85% 1RM; overload load week to week; sharpen the competition lifts.",
             "deload_logic": "Week 10 deload."},
            {"phase": "peaking", "weeks": "11-13", "gym_frequency": "3-4", "sport_frequency": "0",
             "primary_goals": ["singles_doubles_87_95pct", "cns_potentiation", "commands_and_openers", "fatigue_dissipation"],
             "progression_logic": "1-3 reps at ~87-95% 1RM; sharply reduce volume so fatigue drops while strength is expressed.",
             "deload_logic": "Volume falls throughout this block."},
            {"phase": "taper_compete", "weeks": "14", "gym_frequency": "2-3", "sport_frequency": "0",
             "primary_goals": ["taper_recover", "attempt_selection_rehearsal", "peak_realization"],
             "progression_logic": "1-week taper: minimal volume, hold intensity, arrive fully recovered for maximal expression.",
             "deload_logic": "Competition taper week."},
        ],
        "source_refs": [
            {"title": "Block Periodization for Powerlifting — hypertrophy/strength/peaking blocks", "url": "https://grindergym.com/block-periodization-for-powerlifting/", "type": "practitioner"},
            {"title": "Tapering and Peaking Maximal Strength for Powerlifting Performance: A Review (PMC)", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7552788/", "type": "peer_reviewed"},
        ],
    },
]


def seed(db) -> int:
    now = datetime.utcnow()
    for tpl in TEMPLATES:
        tpl["updated_at"] = now
        tpl.setdefault("seeded_at", now)
        tpl.setdefault("seed_source", "research_backed_v1")
        tpl.setdefault("expert_validation_status", "ai_drafted_needs_review")
        tpl.setdefault("linked_planning_rule_ids", [])
        db.macro_plan_templates.update_one({"id": tpl["id"]}, {"$set": tpl}, upsert=True)
    return db.macro_plan_templates.count_documents({})


if __name__ == "__main__":
    total = seed(_db())
    print(f"Seeded research-backed macro templates. Total templates now: {total}")

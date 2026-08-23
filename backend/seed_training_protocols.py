#!/usr/bin/env python3
"""Seed the `training_protocols` decision-layer collection.

These are the expert coaching DECISIONS the AI was previously improvising at a generalist level:
condition-specific rehab/loading protocols, load-prescription anchors, testing batteries, and
progression rules — each with concrete dosing (sets/reps/tempo/intensity/frequency + criteria).

Retrieval feeds the relevant few into generation so the AI programs the *specific* protocol instead
of a sensible-but-generic version. Run:  python -m backend.seed_training_protocols
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


# scope: "condition" = injury/context-specific; "general" = broadly relevant (always a candidate).
PROTOCOLS = [
    {
        "id": "proto_patellar_tendinopathy",
        "name": "Patellar Tendinopathy Loading Protocol",
        "category": "tendon_rehab",
        "scope": "condition",
        "match": {"injury_areas": ["knee", "patellar", "patella", "jumpers_knee", "jumper", "tendon", "tendinopathy"],
                  "goals": ["jump", "vertical", "power"], "sports": ["basketball", "volleyball"], "phases": []},
        "summary": "Progressive tendon loading for patellar tendinopathy: isometric for pain, heavy-slow-resistance for capacity, then energy-storage before jumping.",
        "stages": [
            {"stage": "isometric", "when": "reactive / painful", "purpose": "analgesia + early tendon load",
             "prescription": "Spanish squat or leg-extension isometric hold: 5 x 45s at ~70% effort, 2-3x/day, knee ~60deg. Keep pain <=3/10."},
            {"stage": "heavy_slow_resistance", "when": "pain settling", "purpose": "tendon + muscle adaptation",
             "prescription": "Leg press / squat / knee extension: 3-4 x 6-8 with 3s eccentric + 3s concentric tempo, 3x/week, RPE 7-8, progress load weekly."},
            {"stage": "energy_storage", "when": "strength restored, pain-free", "purpose": "return to jumping",
             "prescription": "Reintroduce plyometrics gradually only once single-leg strength LSI >90% and VISA-P improving; start low-volume bilateral landings."},
        ],
        "key_rules": ["Pain <=3/10 during and within 24h is acceptable and does not indicate harm",
                      "Do NOT prescribe high-volume jumping while the tendon is reactive",
                      "Every loaded knee exercise gets an explicit tempo (e.g. 3s down)"],
        "monitoring": ["VISA-P questionnaire weekly", "Single-leg decline squat pain (0-10)", "Pain <=3/10 during & 24h after"],
        "avoid": ["High-volume/max plyometrics while reactive", "Deep loaded knee flexion if painful", "Depth jumps"],
        "recommended_exercises": ["Spanish Squat", "Box Squat", "Single-Leg Calf Raise", "Leg Extension", "Split Squat"],
        "evidence_level": "high",
        "source_refs": [{"title": "Heavy Slow Resistance vs eccentric for patellar tendinopathy (Kongsgaard)", "type": "trial"},
                        {"title": "Isometric exercise for tendon pain (Rio et al.)", "type": "trial"}],
    },
    {
        "id": "proto_achilles_tendinopathy",
        "name": "Achilles Tendinopathy Loading Protocol",
        "category": "tendon_rehab",
        "scope": "condition",
        "match": {"injury_areas": ["achilles", "calf", "heel", "ankle", "tendon", "tendinopathy"],
                  "goals": ["running", "run", "sprint"], "sports": ["running", "running_endurance"], "phases": []},
        "summary": "Graded calf/Achilles loading: isometric for pain, heavy-slow calf raises, then plyometric reintroduction.",
        "stages": [
            {"stage": "isometric", "when": "painful", "purpose": "analgesia",
             "prescription": "Isometric calf raise hold: 5 x 30-45s, 2x/day, straight & bent knee. Pain <=3/10."},
            {"stage": "heavy_slow_resistance", "when": "pain settling", "purpose": "tendon capacity",
             "prescription": "Straight- and bent-knee calf raises: 3-4 x 6-8 slow (3s up/3s down), 3x/week, add load progressively."},
            {"stage": "return_to_running", "when": "pain-free heavy raises", "purpose": "energy storage",
             "prescription": "Gradual return-to-run + low-volume hops once single-leg heel-raise capacity restored."},
        ],
        "key_rules": ["Bent-knee raises bias soleus; include both", "Progress load, keep tempo slow"],
        "monitoring": ["VISA-A questionnaire", "Single-leg heel-raise count vs unaffected side"],
        "avoid": ["Sudden running volume spikes", "Uncontrolled plyometrics while painful"],
        "recommended_exercises": ["Single-Leg Calf Raise", "Seated Calf Raise", "Standing Calf Raise"],
        "evidence_level": "high",
        "source_refs": [{"title": "Alfredson eccentric / HSR Achilles protocols", "type": "review"}],
    },
    {
        "id": "proto_load_prescription_no_1rm",
        "name": "Load Prescription Without a Tested 1RM",
        "category": "load_prescription",
        "scope": "general",
        "match": {"injury_areas": [], "goals": ["strength", "muscle", "hypertrophy", "power", "performance", "general_fitness"], "sports": [], "phases": []},
        "summary": "How to anchor load when no 1RM is known: use RIR/RPE and rep-max targets, then apply double progression.",
        "stages": [
            {"stage": "anchor", "when": "no tested max", "purpose": "individualize without guessing",
             "prescription": "Prescribe by RIR/RPE: strength 3-6 reps @ RPE 7-8 (2-3 RIR); hypertrophy 8-12 @ RPE 8 (2 RIR); power moves stay fast @ RPE 6-7. First set is a calibration set."},
            {"stage": "progress", "when": "each week", "purpose": "progressive overload",
             "prescription": "Double progression: add reps within the range at the same load; once top of range hit for all sets, add ~2.5-5% load and drop to bottom of range."},
        ],
        "key_rules": ["Never prescribe a bare load number the athlete cannot verify — anchor to RPE/RIR",
                      "State a target RPE/RIR for every working set that uses load",
                      "Recommend a light calibration set to find the working weight"],
        "monitoring": ["Logged load x reps x RPE per set", "Bar speed / rep quality on last set"],
        "avoid": ["True 1RM tests for beginners or unprepared joints", "Grinding reps to failure on technical lifts"],
        "recommended_exercises": [],
        "evidence_level": "high",
        "source_refs": [{"title": "RPE/RIR autoregulation (Helms et al.)", "type": "review"}],
    },
    {
        "id": "proto_progressive_overload",
        "name": "Progressive Overload & Weekly Progression",
        "category": "progression",
        "scope": "general",
        "match": {"injury_areas": [], "goals": ["strength", "muscle", "hypertrophy", "power", "performance", "general_fitness"], "sports": [], "phases": []},
        "summary": "Default block progression: build volume/intensity across the block, watch fatigue, deload when needed.",
        "stages": [
            {"stage": "accumulate", "when": "weeks 1-3 of a block", "purpose": "build",
             "prescription": "Add a set or small load each week (progressive overload). Keep 1-3 RIR. Prefer reps->load progression."},
            {"stage": "intensify_or_hold", "when": "high RPE / plateau", "purpose": "manage fatigue",
             "prescription": "If average_rpe high or completion low, hold load and improve quality (tempo, ROM, technique) instead of adding load. Change stimulus for plateaued lifts (variation, rep range)."},
        ],
        "key_rules": ["Progress one variable at a time (load OR volume)", "Regressing lifts -> reduce load and rebuild"],
        "monitoring": ["Completion rate", "Rolling RPE", "Per-lift load/volume trend"],
        "avoid": ["Adding load AND volume simultaneously", "Ignoring rising pain/RPE"],
        "recommended_exercises": [],
        "evidence_level": "moderate",
        "source_refs": [{"title": "Periodization & overload principles (Zatsiorsky/NSCA)", "type": "textbook"}],
    },
    {
        "id": "proto_deload",
        "name": "Deload / Recovery Week Management",
        "category": "progression",
        "scope": "general",
        "match": {"injury_areas": [], "goals": ["strength", "muscle", "power", "performance"], "sports": [], "phases": ["deload", "taper"]},
        "summary": "When fatigue markers spike, cut volume (not necessarily intensity) to recover and resensitize.",
        "stages": [
            {"stage": "deload", "when": "high fatigue / signal=hold_or_deload / every 4-6 weeks", "purpose": "recover",
             "prescription": "Reduce total sets ~40-50%, keep 1-2 heavier top sets at moderate RPE (6-7), maintain movement quality. 1 week."},
        ],
        "key_rules": ["Cut volume before intensity", "Trigger on trends, not one bad day"],
        "monitoring": ["RPE trend", "Pain trend", "Sleep/readiness"],
        "avoid": ["Skipping training entirely (keep light movement)"],
        "recommended_exercises": [],
        "evidence_level": "moderate",
        "source_refs": [{"title": "Fatigue management & deloads (NSCA)", "type": "textbook"}],
    },
    {
        "id": "proto_return_to_sport_testing",
        "name": "Return-to-Sport Testing Battery",
        "category": "testing",
        "scope": "general",
        "match": {"injury_areas": ["knee", "acl", "ankle", "hamstring", "return"], "goals": ["performance", "power", "jump", "vertical"], "sports": [], "phases": ["re_entry", "reconditioning_bridge", "return"]},
        "summary": "Objective criteria to progress phases and clear an athlete for jumping/sport — replaces guesswork.",
        "stages": [
            {"stage": "baseline", "when": "start of plan / phase gate", "purpose": "quantify readiness",
             "prescription": "Test: single-leg hop for distance + triple hop (Limb Symmetry Index target >=90%), countermovement jump height, isometric single-leg strength, and a condition questionnaire (VISA-P/VISA-A) where relevant."},
            {"stage": "gate", "when": "before adding impact/plyos", "purpose": "safe progression",
             "prescription": "Only progress to plyometrics/max power when LSI >=90%, pain-free, and questionnaire improving."},
        ],
        "key_rules": ["Prescribe measurable tests, not qualitative 'assessment'", "Use LSI >=90% as a jump-clearance gate"],
        "monitoring": ["LSI %", "CMJ height", "VISA score"],
        "avoid": ["Clearing to jump on 'feels okay' alone"],
        "recommended_exercises": ["Single-Leg Hop Test", "Countermovement Jump"],
        "evidence_level": "high",
        "source_refs": [{"title": "RTS criteria & LSI hop testing (Grindem, Ardern)", "type": "review"}],
    },
    {
        "id": "proto_hamstring_prevention",
        "name": "Hamstring Strain Prevention & Loading",
        "category": "injury_prevention",
        "scope": "condition",
        "match": {"injury_areas": ["hamstring", "posterior_thigh"], "goals": ["sprint", "speed", "running", "power"], "sports": ["running", "soccer", "football", "basketball"], "phases": []},
        "summary": "Eccentric hamstring strengthening (Nordic-based) plus high-speed running exposure to reduce strain risk.",
        "stages": [
            {"stage": "eccentric_strength", "when": "prep / in-season maintenance", "purpose": "eccentric capacity",
             "prescription": "Nordic hamstring curl: build to 2-3 sets x 5-8 reps, ~1-2x/week (start low volume to manage soreness). Add hip-hinge (RDL) 3x6-8."},
            {"stage": "high_speed_exposure", "when": "healthy", "purpose": "sprint-specific resilience",
             "prescription": "Progressive high-speed running exposure weekly; do not remove sprinting entirely in-season."},
        ],
        "key_rules": ["Nordics reduce hamstring injury risk ~50% — include them", "Manage Nordic soreness with low starting volume"],
        "monitoring": ["Nordic break-point angle", "Sprint exposure load"],
        "avoid": ["Zero high-speed running for weeks (deconditions the tissue)"],
        "recommended_exercises": ["Nordic Hamstring Curl", "Romanian Deadlift", "Single-Leg RDL"],
        "evidence_level": "high",
        "source_refs": [{"title": "Nordic hamstring RCT meta-analysis (van Dyk)", "type": "meta_analysis"}],
    },
    {
        "id": "proto_low_back_loading",
        "name": "Low-Back-Friendly Loading",
        "category": "injury_prevention",
        "scope": "condition",
        "match": {"injury_areas": ["back", "spine", "lumbar", "disc", "si_joint"], "goals": ["strength", "muscle"], "sports": [], "phases": []},
        "summary": "Keep spine neutral, build trunk stiffness, and load hinge/squat within a pain-free range with bracing.",
        "stages": [
            {"stage": "stabilize", "when": "irritable", "purpose": "control",
             "prescription": "McGill big-3 (curl-up, side plank, bird-dog) for endurance; brace and keep neutral spine. Hip-hinge patterning with light load."},
            {"stage": "load", "when": "symptoms controlled", "purpose": "build capacity",
             "prescription": "Reintroduce hinge/squat with neutral spine, RPE 6-7, controlled range; substitute trap-bar/box variations if flexion-sensitive."},
        ],
        "key_rules": ["Every loaded hinge/squat: cue neutral spine + brace", "Reduce range/load before removing the movement"],
        "monitoring": ["Pain during & after", "Morning stiffness"],
        "avoid": ["Loaded lumbar flexion under fatigue if flexion-intolerant", "Max deadlifts while irritable"],
        "recommended_exercises": ["Bird Dog", "Side Plank", "Trap Bar Deadlift", "Goblet Squat"],
        "evidence_level": "moderate",
        "source_refs": [{"title": "McGill spine stability approach", "type": "textbook"}],
    },
    {
        "id": "proto_shoulder_rotator_cuff",
        "name": "Shoulder / Rotator-Cuff-Friendly Pressing",
        "category": "injury_prevention",
        "scope": "condition",
        "match": {"injury_areas": ["shoulder", "rotator", "cuff", "rotator_cuff", "ac_joint", "impingement"], "goals": ["strength", "muscle"], "sports": ["swimming", "tennis", "volleyball", "boxing"], "phases": []},
        "summary": "Build cuff and scapular control, keep pressing in pain-free ranges, favor neutral-grip and landmine paths.",
        "stages": [
            {"stage": "cuff_scap", "when": "always", "purpose": "stability",
             "prescription": "External rotation + scapular work (face pulls, band ER, serratus): 2-3 x 12-15, 2x/week."},
            {"stage": "press_pain_free", "when": "symptom-limited", "purpose": "load without flare",
             "prescription": "Prefer neutral-grip DB press, landmine press, incline over strict barbell overhead if painful; keep in pain-free ROM, RPE 7."},
        ],
        "key_rules": ["Overhead work needs a pain-free range or a scap/neutral-grip modification", "Train the cuff before heavy pressing"],
        "monitoring": ["Pain arc during press", "ER strength symmetry"],
        "avoid": ["Behind-the-neck press", "Max overhead load while impinged"],
        "recommended_exercises": ["Face Pull", "Landmine Press", "Neutral-Grip Dumbbell Press", "Band External Rotation"],
        "evidence_level": "moderate",
        "source_refs": [{"title": "Rotator cuff loading & scapular control", "type": "review"}],
    },
    {
        "id": "proto_plyometric_progression",
        "name": "Plyometric Progression & Landing Mechanics",
        "category": "plyometric",
        "scope": "condition",
        "match": {"injury_areas": ["knee", "ankle", "return"], "goals": ["jump", "vertical", "power", "speed", "performance", "athletic"], "sports": ["basketball", "volleyball", "soccer", "football"], "phases": ["reconditioning_bridge", "power"]},
        "summary": "Build jump capacity safely: landing mechanics -> bilateral low-intensity -> unilateral -> reactive/depth, gated by strength and pain.",
        "stages": [
            {"stage": "landing_mechanics", "when": "entry", "purpose": "absorb force",
             "prescription": "Teach quiet landings (foot-knee-hip aligned): box drops to stick-landing, 3-4 x 5, low volume, full recovery."},
            {"stage": "bilateral_low", "when": "landings clean", "purpose": "extensive plyo",
             "prescription": "Pogo hops, low box jumps: keep contacts low (~40-60/session), quality over height."},
            {"stage": "unilateral_reactive", "when": "LSI>=90%, pain-free", "purpose": "intensive plyo",
             "prescription": "Single-leg bounds, then depth jumps LAST — only once strength & LSI gates pass. Cap contacts, full rest between sets."},
        ],
        "key_rules": ["Depth jumps are the LAST progression, never the first", "Gate plyo volume on knee pain (<=3/10) and LSI>=90%", "Quality of landing > jump height early"],
        "monitoring": ["Contact count/session", "Landing quality", "Knee pain 24h"],
        "avoid": ["High jump volume on a reactive tendon", "Depth jumps before single-leg strength"],
        "recommended_exercises": ["Box Jump", "Pogo Hops", "Single-Leg Bound", "Drop Landing"],
        "evidence_level": "moderate",
        "source_refs": [{"title": "Plyometric progression & landing (NSCA)", "type": "textbook"}],
    },
    {
        "id": "proto_vertical_jump_development",
        "name": "Vertical Jump / Lower-Body Power Development",
        "category": "sport",
        "scope": "condition",
        "match": {"injury_areas": [], "goals": ["jump", "vertical", "power", "athletic", "performance", "speed", "explosive"], "sports": ["basketball", "volleyball"], "phases": ["power", "strength_to_power_bridge"]},
        "summary": "Vertical jump = max strength + rate of force development + plyometrics. Sequence strength -> power -> reactive.",
        "stages": [
            {"stage": "max_strength", "when": "base phase", "purpose": "force ceiling",
             "prescription": "Heavy squat/hinge: 3-5 x 3-5 @ RPE 8. Strong squat relative to bodyweight underpins jump."},
            {"stage": "power_rfd", "when": "bridge phase", "purpose": "rate of force",
             "prescription": "Explosive intent: trap-bar jumps, jump squats (light, fast), Olympic-lift variations 4-5 x 2-3, and contrast/complex pairs."},
            {"stage": "reactive", "when": "peak", "purpose": "elastic",
             "prescription": "Plyometrics per plyometric progression protocol; low contacts, max intent, full recovery."},
        ],
        "key_rules": ["Move light explosive work FAST (RPE by speed, not grind)", "Pair heavy + explosive (contrast) when advanced"],
        "monitoring": ["CMJ height", "Squat strength : bodyweight ratio"],
        "avoid": ["Training jumps in a fatigued state", "High-rep 'power' sets that become grindy"],
        "recommended_exercises": ["Trap Bar Deadlift", "Jump Squat", "Box Jump", "Hang Power Clean"],
        "evidence_level": "moderate",
        "source_refs": [{"title": "Strength-power potentiation & jump training", "type": "review"}],
    },
]


def seed(db) -> int:
    now = datetime.utcnow()
    for proto in PROTOCOLS:
        proto["updated_at"] = now
        proto.setdefault("expert_validation_status", "curated")
        db.training_protocols.update_one({"id": proto["id"]}, {"$set": proto}, upsert=True)
    return db.training_protocols.count_documents({})


if __name__ == "__main__":
    total = seed(_db())
    print(f"Seeded training_protocols. Total in collection: {total}")

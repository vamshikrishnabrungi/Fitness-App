from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK_ID = "mobility_flexibility_web_research_v1"
INGESTION_METHOD = "manual_web_research_curated_mobility_flexibility_v1"


SOURCES: Dict[str, Dict[str, str]] = {
    "hss_static_dynamic": {
        "title": "HSS - Static and Dynamic Stretching: Tips for Athletes",
        "url": "https://www.hss.edu/health-library/move-better/static-dynamic-stretching",
        "type": "sports_medicine_article",
    },
    "hss_flexibility": {
        "title": "HSS - Simple Ways to Increase Your Flexibility",
        "url": "https://www.hss.edu/health-library/move-better/how-to-increase-flexibility",
        "type": "sports_medicine_article",
    },
    "mayo_basic_stretches": {
        "title": "Mayo Clinic - A Guide to Basic Stretches",
        "url": "https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/stretching/art-20546848",
        "type": "medical_fitness_article",
    },
    "mayo_stretching_focus": {
        "title": "Mayo Clinic - Stretching: Focus on Flexibility",
        "url": "https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/stretching/art-20047931",
        "type": "medical_fitness_article",
    },
    "mayo_back": {
        "title": "Mayo Clinic - Back Exercises in 15 Minutes a Day",
        "url": "https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/back-pain/art-20546859",
        "type": "medical_fitness_article",
    },
    "mayo_osteoporosis": {
        "title": "Mayo Clinic - Exercising with Osteoporosis: Stay Active the Safe Way",
        "url": "https://www.mayoclinic.org/diseases-conditions/osteoporosis/in-depth/osteoporosis/art-20044989",
        "type": "medical_fitness_article",
    },
    "mayo_golf_stretches": {
        "title": "Mayo Clinic - Golf Stretches for a More Fluid Swing",
        "url": "https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/golf-stretches/art-20546809",
        "type": "medical_fitness_article",
    },
    "aaos_spine": {
        "title": "AAOS OrthoInfo - Spine Conditioning Program",
        "url": "https://orthoinfo.aaos.org/en/recovery/spine-conditioning-program/",
        "type": "orthopedic_conditioning_program",
    },
    "aaos_hip": {
        "title": "AAOS OrthoInfo - Hip Conditioning Program",
        "url": "https://orthoinfo.aaos.org/en/recovery/hip-conditioning-program/",
        "type": "orthopedic_conditioning_program",
    },
    "aaos_shoulder": {
        "title": "AAOS OrthoInfo - Rotator Cuff and Shoulder Conditioning Program",
        "url": "https://orthoinfo.aaos.org/en/recovery/rotator-cuff-and-shoulder-conditioning-program/",
        "type": "orthopedic_conditioning_program",
    },
    "aaos_knee": {
        "title": "AAOS OrthoInfo - Knee Conditioning Program",
        "url": "https://orthoinfo.aaos.org/en/recovery/knee-conditioning-program/",
        "type": "orthopedic_conditioning_program",
    },
    "hss_knee": {
        "title": "HSS - Knee Strengthening Stretches and Exercises",
        "url": "https://www.hss.edu/health-library/move-better/exercises-strengthen-knees",
        "type": "sports_medicine_article",
    },
    "hss_cross_syndrome": {
        "title": "HSS - Move with Purpose to Combat Upper and Lower Cross Syndromes",
        "url": "https://www.hss.edu/health-library/move-better/avoid-cross-syndrome",
        "type": "sports_medicine_article",
    },
    "mayo_stretch_prevention": {
        "title": "Mayo Clinic Press - Does Stretching Prevent Injuries?",
        "url": "https://mcpress.mayoclinic.org/nutrition-fitness/does-stretching-prevent-injuries/",
        "type": "medical_fitness_article",
    },
    "acsm_youth": {
        "title": "ACSM - Youth Resistance Training Guidelines",
        "url": "https://acsm.org/wp-content/uploads/2025/02/NYSHSI-Youth-Resistance-Training-PDF.pdf",
        "type": "professional_guideline_pdf",
    },
    "acsm_guidelines": {
        "title": "ACSM - Physical Activity Guidelines",
        "url": "https://acsm.org/education-resources/trending-topics-resources/physical-activity-guidelines/",
        "type": "professional_guideline",
    },
}


TRAINING_PRINCIPLES: List[Dict[str, Any]] = [
    {
        "id": "mob_principle_dynamic_before_static_after",
        "title": "Use Dynamic Mobility Before Training And Static Stretching After",
        "topics": ["dynamic_warmup", "static_stretching", "cooldown", "performance"],
        "summary": "Pre-session work should raise temperature and rehearse ranges dynamically; long static holds fit better after training, recovery sessions, or flexibility blocks.",
        "source_ids": ["hss_static_dynamic", "mayo_stretching_focus", "mayo_basic_stretches"],
    },
    {
        "id": "mob_principle_warm_tissue_before_stretching",
        "title": "Warm Tissue Before Long Stretching",
        "topics": ["safety", "warmup", "flexibility"],
        "summary": "Stretching cold tissue is less useful and can irritate symptoms; use light activity first or stretch after the workout.",
        "source_ids": ["mayo_basic_stretches", "mayo_stretching_focus"],
    },
    {
        "id": "mob_principle_mobility_strength_pairing",
        "title": "Pair Mobility With Strength Or Activation",
        "topics": ["mobility", "activation", "joint_stability", "injury_reduction"],
        "summary": "Mobility gains transfer better when the user also strengthens or activates the muscles that control the newly available range.",
        "source_ids": ["aaos_spine", "aaos_hip", "aaos_shoulder", "aaos_knee"],
    },
    {
        "id": "mob_principle_pain_free_range",
        "title": "Use Pain-Free Range And Stop Sharp Symptoms",
        "topics": ["pain", "injury_modification", "return_to_training"],
        "summary": "Mobility and flexibility drills should create gentle tension or mild effort, not sharp pain, nerve symptoms, swelling, or worsening next-day response.",
        "source_ids": ["mayo_basic_stretches", "aaos_spine", "aaos_hip", "aaos_shoulder", "aaos_knee"],
    },
    {
        "id": "mob_principle_age_specific_mobility",
        "title": "Adjust Mobility For Age, Bone Health, And Balance",
        "topics": ["older_adults", "osteoporosis", "youth", "balance"],
        "summary": "Older adults and people with osteoporosis need gentle ranges, balance support, and caution with loaded spinal flexion or forceful twisting; youth should learn simple controlled movements before complex or explosive work.",
        "source_ids": ["mayo_osteoporosis", "acsm_youth"],
    },
]


PROGRAMMING_RULES: List[Dict[str, Any]] = [
    {
        "id": "mob_rule_pre_session_dynamic",
        "title": "Pre-Session Mobility Should Be Dynamic And Specific",
        "category": "warmup",
        "applies_to": ["pre_workout", "sports", "strength_training", "running"],
        "summary": "Use 5-10 minutes of light activity followed by dynamic mobility that resembles the session demands.",
        "rule_text": "Before running, lifting, court sport, or field sport sessions, prefer dynamic mobility and activation over long passive holds.",
        "recommended_focus": ["temperature", "joint_range", "activation", "movement_rehearsal"],
        "source_ids": ["hss_static_dynamic", "mayo_stretching_focus", "mayo_stretch_prevention"],
    },
    {
        "id": "mob_rule_post_session_static",
        "title": "Post-Session Stretching Can Use Longer Static Holds",
        "category": "cooldown",
        "applies_to": ["post_workout", "flexibility", "recovery"],
        "summary": "Static stretches are best used after training or during dedicated flexibility sessions when tissues are warm.",
        "rule_text": "Hold gentle static stretches around 20-60 seconds, repeat key areas, breathe normally, and avoid bouncing or pain.",
        "recommended_focus": ["static_stretching", "breathing", "relaxation", "range_of_motion"],
        "source_ids": ["hss_static_dynamic", "mayo_basic_stretches", "aaos_knee", "aaos_shoulder"],
    },
    {
        "id": "mob_rule_injury_needs_supervision",
        "title": "Injury Or Surgery Requires Individualized Mobility Selection",
        "category": "injury_safety",
        "applies_to": ["injury", "post_surgery", "rehab", "pain"],
        "summary": "Conditioning programs after injury or surgery should be guided by a clinician or physical therapist.",
        "rule_text": "Use conservative ranges and medical review when the user reports recent surgery, severe pain, swelling, neurological symptoms, or unclear restrictions.",
        "recommended_focus": ["pain_free_range", "medical_clearance", "regressions"],
        "source_ids": ["aaos_spine", "aaos_hip", "aaos_shoulder", "aaos_knee"],
    },
    {
        "id": "mob_rule_balance_activation_for_older_adults",
        "title": "Older Adults Need Mobility Plus Balance And Control",
        "category": "older_adults",
        "applies_to": ["older_adults", "osteoporosis", "fall_risk"],
        "summary": "Older users benefit from gentle full-range movement, balance support, and stability drills rather than aggressive end-range stretching.",
        "rule_text": "Use chair or wall support, avoid forceful bouncing, and avoid loaded spinal flexion/twisting when osteoporosis risk is present.",
        "recommended_focus": ["balance", "gentle_range", "posture", "fall_prevention"],
        "source_ids": ["mayo_osteoporosis", "mayo_basic_stretches"],
    },
    {
        "id": "mob_rule_youth_simple_to_complex",
        "title": "Youth Mobility Should Move Simple To Complex",
        "category": "youth",
        "applies_to": ["youth", "beginner", "movement_learning"],
        "summary": "Younger athletes should learn simple, stable, controlled mobility and activation patterns before complex, unstable, or explosive work.",
        "rule_text": "Use clear coaching cues, low load, stable positions, and dynamic warm-ups that mimic the training session.",
        "recommended_focus": ["simple_movements", "stable_before_unstable", "control"],
        "source_ids": ["acsm_youth"],
    },
    {
        "id": "mob_rule_mobility_dose",
        "title": "Mobility Dose Should Match The Goal",
        "category": "dose",
        "applies_to": ["flexibility", "daily_mobility", "warmup", "cooldown"],
        "summary": "Dynamic drills usually use reps or short flows; flexibility sessions use longer gentle holds and more total time.",
        "rule_text": "For warm-ups use 6-12 reps or 20-40 seconds per dynamic drill. For static flexibility use 20-60 second holds and 2-4 rounds on priority areas.",
        "recommended_focus": ["sets_reps", "hold_time", "consistency"],
        "source_ids": ["hss_static_dynamic", "mayo_basic_stretches", "aaos_knee", "aaos_shoulder"],
    },
    {
        "id": "mob_rule_activation_before_power",
        "title": "Activate Stabilizers Before Power Or Skill Work",
        "category": "activation",
        "applies_to": ["jump_training", "running", "lifting", "overhead_sports"],
        "summary": "Use targeted activation for hips, trunk, scapula, ankle, or foot before high-skill or high-force work.",
        "rule_text": "Pair mobility with activation: open the range, then ask the body to control it before sprinting, jumping, throwing, lifting, or overhead work.",
        "recommended_focus": ["glute_activation", "scapular_control", "trunk_bracing", "foot_ankle_control"],
        "source_ids": ["aaos_hip", "aaos_shoulder", "aaos_spine", "hss_knee"],
    },
]


RECOVERY_RULES: List[Dict[str, Any]] = [
    {
        "id": "mob_recovery_low_intensity_movement",
        "title": "Use Low-Intensity Movement To Reduce Stiffness",
        "category": "active_recovery",
        "topics": ["recovery", "stiffness", "dynamic_mobility"],
        "summary": "Easy movement and dynamic mobility can help users feel less stiff after hard training without adding major fatigue.",
        "rule_text": "Use walking, easy cycling, gentle mobility flows, and breathing-based cooldowns when soreness or stiffness is present.",
        "source_ids": ["mayo_stretch_prevention", "mayo_basic_stretches"],
    },
    {
        "id": "mob_recovery_posture_breaks",
        "title": "Break Up Long Sitting With Short Mobility Snacks",
        "category": "daily_recovery",
        "topics": ["desk_work", "posture", "hips", "thoracic_spine", "neck"],
        "summary": "Short mobility breaks for hips, thoracic spine, shoulders, and neck can help normal users maintain range during sedentary days.",
        "rule_text": "Use 2-5 minute movement snacks with hip flexor, thoracic, scapular, and ankle drills rather than one long session only.",
        "source_ids": ["hss_cross_syndrome", "aaos_spine"],
    },
    {
        "id": "mob_recovery_breathing_downshift",
        "title": "Finish Recovery Mobility With Slow Breathing",
        "category": "cooldown",
        "topics": ["breathing", "downregulation", "cooldown"],
        "summary": "Breathing-focused cooldowns can help shift away from high arousal after training and make static mobility easier to tolerate.",
        "rule_text": "Use nasal breathing, long exhales, or relaxed breathing during post-session stretches.",
        "source_ids": ["mayo_basic_stretches", "hss_flexibility"],
    },
]


INJURY_MODIFICATIONS: List[Dict[str, Any]] = [
    {
        "id": "mob_injury_low_back",
        "title": "Low Back Mobility Modification",
        "body_area": "low_back",
        "summary": "Prioritize gentle spine movement, trunk control, hip mobility, and glute activation. Avoid aggressive loaded flexion or painful twisting.",
        "recommended_regressions": ["cat_cow", "pelvic_tilt", "bird_dog", "dead_bug", "childs_pose_breathing"],
        "avoid_patterns": ["loaded_spinal_flexion", "forceful_twisting", "painful_end_range"],
        "source_ids": ["aaos_spine", "mayo_back"],
    },
    {
        "id": "mob_injury_shoulder",
        "title": "Shoulder Mobility Modification",
        "body_area": "shoulder",
        "summary": "Use gentle shoulder range, posterior capsule mobility, scapular control, and rotator cuff activation before overhead loading.",
        "recommended_regressions": ["pendulum", "crossover_arm_stretch", "band_external_rotation", "wall_slide"],
        "avoid_patterns": ["painful_overhead_end_range", "aggressive_sleeper_stretch", "loaded_instability"],
        "source_ids": ["aaos_shoulder", "hss_static_dynamic"],
    },
    {
        "id": "mob_injury_knee",
        "title": "Knee Mobility Modification",
        "body_area": "knee",
        "summary": "Support knee symptoms by improving hip, quad, hamstring, calf, and ankle mobility plus progressive knee-friendly strength.",
        "recommended_regressions": ["dynamic_hamstring_floor_stretch", "half_kneeling_hip_flexor_stretch", "calf_stretch", "quad_set", "mini_squat"],
        "avoid_patterns": ["sharp_knee_pain", "forced_knee_flexion", "fatigue_driven_valgus"],
        "source_ids": ["hss_knee", "aaos_knee"],
    },
    {
        "id": "mob_injury_hip",
        "title": "Hip Mobility Modification",
        "body_area": "hip",
        "summary": "Use gentle hip flexor, glute, piriformis, adductor, hamstring, and abductor mobility with glute/hip control work.",
        "recommended_regressions": ["figure_4_stretch", "half_kneeling_hip_flexor_stretch", "adductor_rockback", "glute_bridge", "clamshell"],
        "avoid_patterns": ["pinching_front_hip_pain", "forced_deep_flexion", "painful_rotation"],
        "source_ids": ["aaos_hip", "hss_knee", "mayo_golf_stretches"],
    },
    {
        "id": "mob_injury_ankle_achilles",
        "title": "Ankle And Achilles Mobility Modification",
        "body_area": "ankle_achilles",
        "summary": "Use calf/soleus mobility, ankle dorsiflexion work, foot activation, and gradual loading before plyometrics or running volume.",
        "recommended_regressions": ["calf_wall_stretch", "soleus_wall_stretch", "knee_to_wall_ankle_rocks", "short_foot", "calf_raise_iso"],
        "avoid_patterns": ["bouncy_end_range", "painful_plyometric_contacts", "sudden_running_spike"],
        "source_ids": ["mayo_basic_stretches", "aaos_knee"],
    },
    {
        "id": "mob_injury_osteoporosis",
        "title": "Osteoporosis Mobility Modification",
        "body_area": "bone_health",
        "summary": "Use gentle range, posture, balance, and extension-friendly drills. Avoid toe-touch style spinal flexion and forceful twisting.",
        "recommended_regressions": ["wall_angels", "standing_hip_flexor_stretch", "supported_single_leg_balance", "thoracic_extension_on_wall"],
        "avoid_patterns": ["deep_spinal_flexion", "forceful_waist_twisting", "unsupported_balance_risk"],
        "source_ids": ["mayo_osteoporosis"],
    },
]


def _drill(
    *,
    id: str,
    name: str,
    category: str,
    phase: str,
    body_regions: List[str],
    addresses: List[str],
    equipment: List[str],
    summary: str,
    setup: str,
    execution: str,
    prescription: Dict[str, str],
    coaching_cues: List[str],
    common_errors: List[str],
    use_when: List[str],
    avoid_when: List[str],
    source_ids: List[str],
    difficulty: str = "beginner",
    aliases: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "aliases": aliases or [],
        "category": category,
        "phase": phase,
        "difficulty": difficulty,
        "body_regions": body_regions,
        "addresses": addresses,
        "equipment": equipment,
        "summary": summary,
        "setup": setup,
        "execution": execution,
        "prescription": prescription,
        "coaching_cues": coaching_cues,
        "common_errors": common_errors,
        "use_when": use_when,
        "avoid_when": avoid_when,
        "source_ids": source_ids,
    }


DRILLS: List[Dict[str, Any]] = [
    _drill(id="mob_drill_leg_swing_front_back", name="Front-Back Leg Swing", category="dynamic_mobility", phase="pre_workout", body_regions=["hip", "hamstring", "hip_flexor"], addresses=["running", "sprint", "field_sports", "hip_mobility"], equipment=["bodyweight", "wall_support_optional"], summary="Dynamic hip and hamstring preparation for running, sprinting, kicking, and lower-body lifting.", setup="Stand tall near a wall or rack for balance.", execution="Swing one leg forward and backward through a comfortable range while the trunk stays quiet.", prescription={"reps": "8-15 each side", "sets": "1-2"}, coaching_cues=["Brace lightly so the low back does not arch.", "Let range build gradually across reps."], common_errors=["Forcing end range.", "Leaning back to fake hip extension."], use_when=["pre-run warm-up", "field or court warm-up", "lower-body lift prep"], avoid_when=["sharp hip or hamstring pain"], source_ids=["hss_static_dynamic", "hss_flexibility"]),
    _drill(id="mob_drill_lateral_leg_swing", name="Lateral Leg Swing", category="dynamic_mobility", phase="pre_workout", body_regions=["hip", "adductor", "abductor"], addresses=["lateral_movement", "groin", "hip_mobility"], equipment=["bodyweight", "wall_support_optional"], summary="Dynamic frontal-plane hip mobility for cutting, skating, cricket fielding, court sports, and squatting.", setup="Stand facing a wall or rack.", execution="Swing one leg side-to-side across the body and out to the side under control.", prescription={"reps": "8-15 each side", "sets": "1-2"}, coaching_cues=["Keep pelvis mostly level.", "Use controlled rhythm, not momentum-only kicking."], common_errors=["Twisting the whole body.", "Snapping into end range."], use_when=["pre-court warm-up", "pre-sprint warm-up", "groin-prep block"], avoid_when=["acute groin pain"], source_ids=["hss_static_dynamic", "hss_knee"]),
    _drill(id="mob_drill_arm_circles", name="Arm Circles", category="dynamic_mobility", phase="pre_workout", body_regions=["shoulder", "upper_back"], addresses=["shoulder_warmup", "overhead_sports", "throwing"], equipment=["bodyweight"], summary="Simple shoulder-temperature and range drill for upper-body, throwing, swimming, and overhead preparation.", setup="Stand tall with arms extended comfortably.", execution="Circle arms forward and backward, starting small and gradually increasing range.", prescription={"reps": "10-20 each direction", "sets": "1"}, coaching_cues=["Keep ribs stacked over pelvis.", "Move smoothly without shoulder pinching."], common_errors=["Arching the back.", "Moving into painful pinching."], use_when=["pre-swim", "pre-throw", "upper-body warm-up"], avoid_when=["acute shoulder pain"], source_ids=["hss_static_dynamic", "aaos_shoulder"]),
    _drill(id="mob_drill_worlds_greatest_stretch", name="World's Greatest Stretch", category="dynamic_mobility", phase="pre_workout", body_regions=["hip", "thoracic_spine", "hamstring", "ankle"], addresses=["field_sports", "running", "squat_prep", "lunge_prep"], equipment=["bodyweight"], summary="Multi-joint dynamic lunge flow combining hip flexor, hamstring, ankle, and thoracic mobility.", setup="Start in a long lunge with hands near the front foot.", execution="Move through lunge, elbow-to-instep or hand reach, thoracic rotation, then hamstring shift-back.", prescription={"reps": "3-6 each side", "sets": "1-2"}, coaching_cues=["Own each position before moving.", "Keep breathing and avoid forcing range."], common_errors=["Rushing through positions.", "Letting the front knee collapse inward."], use_when=["full-body warm-up", "field/court prep", "lower-body lift prep"], avoid_when=["wrist pain in floor support", "acute hip pinching"], source_ids=["hss_flexibility", "mayo_basic_stretches"]),
    _drill(id="mob_drill_inchworm", name="Inchworm Walkout", category="dynamic_mobility", phase="pre_workout", body_regions=["hamstring", "calf", "shoulder", "trunk"], addresses=["posterior_chain", "plank_prep", "pushup_prep"], equipment=["bodyweight"], summary="Dynamic posterior-chain and shoulder/trunk preparation that moves from standing hinge into plank.", setup="Stand tall with feet hip-width.", execution="Hinge to the floor, walk hands to plank, pause briefly, then walk feet or hands back.", prescription={"reps": "4-8", "sets": "1-2"}, coaching_cues=["Bend knees as needed.", "Keep plank strong before walking back."], common_errors=["Forcing hamstring stretch cold.", "Sagging through the low back in plank."], use_when=["general warm-up", "bodyweight workout prep"], avoid_when=["acute back pain", "osteoporosis spine-flexion restriction"], source_ids=["mayo_osteoporosis", "mayo_basic_stretches"]),
    _drill(id="mob_drill_deep_squat_pry", name="Deep Squat Pry", category="dynamic_mobility", phase="pre_workout", body_regions=["ankle", "hip", "adductor", "thoracic_spine"], addresses=["squat_mobility", "ankle_dorsiflexion", "hip_mobility"], equipment=["bodyweight", "support_optional"], summary="Squat-specific mobility drill for hips, ankles, and trunk position.", setup="Hold a post, rack, or counter if needed and sink into a comfortable squat.", execution="Shift gently side to side and use elbows or hands to open the hips without losing foot pressure.", prescription={"duration": "20-45 sec", "sets": "1-3"}, coaching_cues=["Keep heels grounded if possible.", "Use support so range stays controlled."], common_errors=["Collapsing arches.", "Forcing depth with back rounding."], use_when=["squat warm-up", "daily hip/ankle mobility"], avoid_when=["painful hip pinch", "knee pain at deep flexion"], source_ids=["aaos_hip", "aaos_knee"]),
    _drill(id="mob_drill_ankle_knee_to_wall", name="Knee-To-Wall Ankle Rocks", category="dynamic_mobility", phase="pre_workout", body_regions=["ankle", "calf", "soleus"], addresses=["ankle_dorsiflexion", "squat_depth", "running", "jump_landing"], equipment=["wall"], summary="Dynamic ankle dorsiflexion drill for squats, running, jumping, and landing mechanics.", setup="Face a wall with one foot a few inches away.", execution="Drive the knee toward the wall over the toes while the heel stays down, then return.", prescription={"reps": "8-15 each side", "sets": "1-3"}, coaching_cues=["Track knee over the middle toes.", "Move from ankle, not arch collapse."], common_errors=["Heel lifting.", "Knee collapsing inward."], use_when=["pre-squat", "pre-run", "ankle mobility block"], avoid_when=["sharp Achilles or ankle pain"], source_ids=["mayo_basic_stretches", "aaos_knee"]),
    _drill(id="mob_drill_cat_cow", name="Cat-Cow", category="spine_mobility", phase="warmup_or_recovery", body_regions=["spine", "neck", "trunk"], addresses=["spine_mobility", "back_stiffness", "breathing"], equipment=["bodyweight", "mat"], summary="Gentle spinal flexion-extension drill for warming the back and restoring comfortable movement.", setup="Start on hands and knees.", execution="Slowly round the spine, then extend through a comfortable range while breathing.", prescription={"reps": "6-12", "sets": "1-3"}, coaching_cues=["Move segment by segment.", "Stay below pain or nerve symptoms."], common_errors=["Forcing end range.", "Holding breath."], use_when=["back-friendly warm-up", "recovery mobility"], avoid_when=["painful spinal motion", "osteoporosis flexion restriction without clearance"], source_ids=["mayo_back", "aaos_spine"]),
    _drill(id="mob_drill_open_book", name="Open Book Thoracic Rotation", category="spine_mobility", phase="warmup_or_recovery", body_regions=["thoracic_spine", "chest", "shoulder"], addresses=["thoracic_rotation", "throwing", "golf", "tennis", "posture"], equipment=["bodyweight", "mat"], summary="Side-lying thoracic rotation drill for trunk rotation and chest mobility.", setup="Lie on your side with hips and knees bent.", execution="Reach the top arm across the body and rotate the chest open while knees stay stacked.", prescription={"reps": "6-10 each side", "sets": "1-2"}, coaching_cues=["Rotate through upper back, not low back.", "Follow the hand with your eyes if comfortable."], common_errors=["Letting knees separate.", "Forcing shoulder to the floor."], use_when=["throwing warm-up", "golf/tennis mobility", "desk posture reset"], avoid_when=["acute shoulder or spine pain"], source_ids=["mayo_golf_stretches", "aaos_spine"]),
    _drill(id="mob_drill_thread_the_needle", name="Thread The Needle", category="spine_mobility", phase="warmup_or_recovery", body_regions=["thoracic_spine", "shoulder", "upper_back"], addresses=["thoracic_rotation", "shoulder_mobility", "upper_back_stiffness"], equipment=["bodyweight", "mat"], summary="Quadruped rotation drill for upper-back and shoulder mobility.", setup="Start on hands and knees.", execution="Reach one arm under the body, rotate gently, then return and optionally reach upward.", prescription={"reps": "6-10 each side", "sets": "1-2"}, coaching_cues=["Keep hips mostly still.", "Breathe into the upper back."], common_errors=["Twisting aggressively through low back.", "Shrugging into the neck."], use_when=["upper-back warm-up", "overhead prep", "recovery flow"], avoid_when=["painful shoulder loading"], source_ids=["aaos_spine", "hss_cross_syndrome"]),
    _drill(id="mob_drill_wall_slide", name="Wall Slide", category="activation_mobility", phase="pre_workout", body_regions=["shoulder", "scapula", "thoracic_spine"], addresses=["overhead_mobility", "scapular_control", "posture"], equipment=["wall"], summary="Shoulder and scapular control drill for overhead position and posture.", setup="Stand or sit against a wall with ribs down.", execution="Slide forearms upward while keeping shoulders relaxed and avoiding low-back arch.", prescription={"reps": "8-12", "sets": "1-3"}, coaching_cues=["Reach up without shrugging.", "Keep ribs stacked."], common_errors=["Arching the back.", "Forcing painful overhead range."], use_when=["overhead warm-up", "desk posture reset"], avoid_when=["shoulder impingement symptoms"], source_ids=["aaos_shoulder", "hss_cross_syndrome"]),
    _drill(id="mob_drill_band_external_rotation", name="Band External Rotation", category="activation", phase="pre_workout", body_regions=["shoulder", "rotator_cuff"], addresses=["rotator_cuff_activation", "throwing", "overhead_sports"], equipment=["resistance_band"], summary="Rotator cuff activation drill for shoulder preparation and control.", setup="Stand with elbow at side and band anchored across the body.", execution="Rotate forearm outward while keeping elbow close to the ribs, then return slowly.", prescription={"reps": "8-15 each side", "sets": "1-3"}, coaching_cues=["Move from shoulder, not wrist.", "Keep shoulder blade quiet and neck relaxed."], common_errors=["Letting elbow drift away.", "Using too much band resistance."], use_when=["pre-throw", "upper-body lift warm-up", "shoulder prehab"], avoid_when=["sharp shoulder pain"], source_ids=["aaos_shoulder"]),
    _drill(id="mob_drill_band_pull_apart", name="Band Pull-Apart", category="activation", phase="pre_workout", body_regions=["upper_back", "shoulder", "scapula"], addresses=["scapular_control", "posture", "upper_back_activation"], equipment=["resistance_band"], summary="Upper-back activation drill for posture, pulling, pressing, and overhead preparation.", setup="Hold a light band at chest height with arms long.", execution="Pull band apart by moving shoulder blades back and down, then return with control.", prescription={"reps": "10-20", "sets": "1-3"}, coaching_cues=["Keep ribs down.", "Use a light band and smooth control."], common_errors=["Shrugging.", "Overarching low back."], use_when=["upper-body warm-up", "desk posture routine"], avoid_when=["shoulder pain with horizontal abduction"], source_ids=["aaos_shoulder", "hss_cross_syndrome"]),
    _drill(id="mob_drill_scap_pushup", name="Scapular Push-Up", category="activation", phase="pre_workout", body_regions=["scapula", "shoulder", "trunk"], addresses=["serratus_activation", "pushup_prep", "overhead_control"], equipment=["bodyweight"], summary="Closed-chain scapular control drill for serratus and shoulder stability.", setup="Start in plank or hands-elevated plank.", execution="Keep elbows straight and glide shoulder blades together, then push the floor away.", prescription={"reps": "8-15", "sets": "1-3"}, coaching_cues=["Move shoulder blades, not elbows.", "Keep trunk braced."], common_errors=["Bending elbows.", "Sagging hips."], use_when=["push-up prep", "handstand prep", "shoulder activation"], avoid_when=["wrist or shoulder pain"], source_ids=["aaos_shoulder"]),
    _drill(id="mob_drill_glute_bridge", name="Glute Bridge", category="activation", phase="pre_workout", body_regions=["hip", "glutes", "trunk"], addresses=["glute_activation", "hip_extension", "low_back_support"], equipment=["bodyweight", "mat"], summary="Glute activation drill for running, squatting, hinging, and back-friendly hip extension.", setup="Lie on back with knees bent and feet flat.", execution="Squeeze glutes and lift hips until body forms a straight line from shoulders to knees, then lower.", prescription={"reps": "8-15", "sets": "1-3"}, coaching_cues=["Posteriorly tilt pelvis slightly before lifting.", "Feel glutes, not low back."], common_errors=["Overarching at the top.", "Pushing only through the toes."], use_when=["pre-run", "lower-body warm-up", "back-friendly activation"], avoid_when=["painful hip extension"], source_ids=["aaos_hip", "aaos_spine"]),
    _drill(id="mob_drill_clamshell", name="Clamshell", category="activation", phase="pre_workout", body_regions=["hip", "glute_medius"], addresses=["hip_stability", "knee_tracking", "lateral_control"], equipment=["bodyweight", "mini_band_optional"], summary="Hip external-rotator activation drill for knee tracking and lateral stability.", setup="Lie on side with knees bent and hips stacked.", execution="Keep feet together and rotate top knee upward without rolling pelvis back.", prescription={"reps": "10-15 each side", "sets": "1-3"}, coaching_cues=["Keep pelvis stacked.", "Move slowly and feel side hip."], common_errors=["Rolling the torso backward.", "Using too much band resistance."], use_when=["knee-friendly warm-up", "running prehab", "lateral sport prep"], avoid_when=["hip pinching"], source_ids=["aaos_hip", "hss_knee"]),
    _drill(id="mob_drill_lateral_band_walk", name="Lateral Band Walk", category="activation", phase="pre_workout", body_regions=["hip", "glute_medius", "ankle"], addresses=["lateral_control", "knee_tracking", "field_sports"], equipment=["mini_band"], summary="Lateral hip activation drill for cutting, landing, and knee control.", setup="Place a mini-band around thighs or ankles and stand in a quarter-squat.", execution="Step sideways with control, keeping feet parallel and knees tracking.", prescription={"reps": "8-15 steps each way", "sets": "1-3"}, coaching_cues=["Keep tension on the band.", "Avoid bouncing or knee collapse."], common_errors=["Dragging the trailing leg.", "Letting arches collapse."], use_when=["pre-court warm-up", "pre-run hip activation"], avoid_when=["acute hip or knee pain"], source_ids=["aaos_hip", "hss_knee"]),
    _drill(id="mob_drill_dead_bug", name="Dead Bug", category="activation", phase="pre_workout_or_rehab", body_regions=["trunk", "hip"], addresses=["trunk_control", "back_pain", "core_activation"], equipment=["bodyweight", "mat"], summary="Low-back-friendly trunk control drill for bracing and limb movement.", setup="Lie on back with hips and knees bent and arms reaching up.", execution="Brace lightly and lower opposite arm/leg while keeping ribs and pelvis controlled.", prescription={"reps": "6-10 each side", "sets": "1-3"}, coaching_cues=["Keep low back quiet.", "Exhale as the limbs move away."], common_errors=["Arching back.", "Moving faster than control allows."], use_when=["back-friendly warm-up", "lifting prep", "core rehab"], avoid_when=["painful supine position"], source_ids=["aaos_spine", "mayo_back"]),
    _drill(id="mob_drill_bird_dog", name="Bird Dog", category="activation", phase="pre_workout_or_rehab", body_regions=["trunk", "hip", "shoulder"], addresses=["spine_control", "anti_rotation", "low_back_support"], equipment=["bodyweight", "mat"], summary="Quadruped trunk and hip control drill for back-friendly stability.", setup="Start on hands and knees.", execution="Reach opposite arm and leg long, pause, then return without shifting hips.", prescription={"reps": "6-10 each side", "sets": "1-3"}, coaching_cues=["Reach long, not high.", "Keep hips square."], common_errors=["Rotating pelvis.", "Overarching low back."], use_when=["spine warm-up", "back pain modification", "athletic trunk prep"], avoid_when=["wrist pain or shoulder loading intolerance"], source_ids=["aaos_spine", "mayo_back"]),
    _drill(id="mob_drill_half_kneeling_hip_flexor", name="Half-Kneeling Hip Flexor Stretch", category="static_or_active_stretch", phase="post_workout_or_recovery", body_regions=["hip_flexor", "quad", "pelvis"], addresses=["hip_extension", "anterior_hip", "lower_cross_posture", "knee_support"], equipment=["bodyweight", "pad_optional"], summary="Hip flexor mobility drill for runners, desk workers, lifters, and knee/hip support.", setup="Kneel on one knee with the other foot forward.", execution="Tuck pelvis slightly, squeeze the rear glute, and shift forward until a gentle front-hip stretch appears.", prescription={"hold": "30-60 sec each side", "sets": "1-3"}, coaching_cues=["Glute squeeze first, then shift.", "Keep ribs stacked over pelvis."], common_errors=["Arching low back.", "Driving aggressively into the front of the hip."], use_when=["post-run stretch", "desk mobility", "knee-friendly hip work"], avoid_when=["front hip pinching"], source_ids=["hss_knee", "aaos_hip", "mayo_golf_stretches"]),
    _drill(id="mob_drill_couch_stretch", name="Couch Stretch", category="static_or_active_stretch", phase="post_workout_or_recovery", body_regions=["quad", "hip_flexor"], addresses=["hip_extension", "quad_flexibility", "squat_lunge_prep"], equipment=["wall_or_bench", "pad_optional"], summary="Intense quad and hip flexor stretch best used after training or in a dedicated mobility session.", setup="Place one knee near a wall or bench with shin angled upward and the other foot forward.", execution="Squeeze rear glute and bring torso upright only as far as comfortable.", prescription={"hold": "20-60 sec each side", "sets": "1-3"}, coaching_cues=["Start farther from the wall if tight.", "Do not chase full upright posture at the expense of pain."], common_errors=["Overarching back.", "Forcing knee flexion."], use_when=["post-lift", "post-run", "quad/hip flexor flexibility"], avoid_when=["knee pain with deep bend", "front hip pinch"], source_ids=["hss_knee", "mayo_basic_stretches"]),
    _drill(id="mob_drill_figure_4", name="Figure-4 Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["glute", "piriformis", "hip"], addresses=["posterior_hip", "hip_rotation", "low_back_support"], equipment=["bodyweight", "mat"], summary="Posterior hip stretch for glutes and piriformis.", setup="Lie on back with one ankle crossed over the opposite thigh.", execution="Pull the supporting leg toward the chest until a comfortable glute stretch is felt.", prescription={"hold": "30-60 sec each side", "sets": "1-3"}, coaching_cues=["Keep neck relaxed.", "Hold behind the thigh rather than yanking the knee."], common_errors=["Pulling into pain.", "Lifting head and neck excessively."], use_when=["post-run", "hip recovery", "back-friendly cooldown"], avoid_when=["hip pinching or nerve symptoms"], source_ids=["hss_knee", "aaos_hip"]),
    _drill(id="mob_drill_90_90_switch", name="90/90 Hip Switch", category="active_mobility", phase="warmup_or_recovery", body_regions=["hip", "glute", "adductor"], addresses=["hip_rotation", "sport_rotation", "squat_mobility"], equipment=["bodyweight", "mat"], summary="Active hip internal/external rotation drill for athletes and general mobility.", setup="Sit with both knees bent around 90 degrees.", execution="Rotate knees from side to side while staying tall or using hands for support.", prescription={"reps": "6-12 total", "sets": "1-3"}, coaching_cues=["Move slowly through hips.", "Use hands as needed to keep control."], common_errors=["Rushing and collapsing posture.", "Forcing painful hip rotation."], use_when=["hip mobility day", "pre-lift warm-up", "field/court prep"], avoid_when=["hip pinching"], source_ids=["aaos_hip", "mayo_golf_stretches"]),
    _drill(id="mob_drill_adductor_rockback", name="Adductor Rockback", category="active_mobility", phase="warmup_or_recovery", body_regions=["adductor", "hip", "groin"], addresses=["groin_mobility", "squat_mobility", "lateral_sport_prep"], equipment=["bodyweight", "mat"], summary="Adductor mobility drill for squatting, lateral movement, cricket, football, and court sports.", setup="Start on hands and knees with one leg extended to the side.", execution="Rock hips back gently until inner-thigh tension appears, then return.", prescription={"reps": "8-12 each side", "sets": "1-3"}, coaching_cues=["Keep spine neutral.", "Move only through comfortable range."], common_errors=["Forcing groin stretch.", "Rotating away from the working side."], use_when=["pre-squat", "groin prehab", "lateral warm-up"], avoid_when=["acute adductor strain"], source_ids=["aaos_hip", "hss_knee"]),
    _drill(id="mob_drill_frog_rock", name="Frog Rockback", category="active_mobility", phase="recovery_or_warmup", body_regions=["adductor", "hip"], addresses=["groin_mobility", "hip_abduction", "deep_squat"], equipment=["bodyweight", "mat"], summary="Higher-range adductor and hip mobility drill for users who tolerate floor positions.", setup="Start on forearms or hands with knees wide and hips flexed.", execution="Rock hips backward and forward gently while keeping pressure tolerable.", prescription={"reps": "6-12", "sets": "1-3"}, coaching_cues=["Use padding under knees.", "Stay well below sharp groin pain."], common_errors=["Going too wide too soon.", "Holding breath."], use_when=["adductor mobility", "squat mobility"], avoid_when=["acute groin pain", "knee discomfort on floor"], source_ids=["aaos_hip"]),
    _drill(id="mob_drill_supine_hamstring_stretch", name="Supine Hamstring Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["hamstring", "posterior_chain"], addresses=["hamstring_flexibility", "running", "knee_support"], equipment=["bodyweight", "strap_optional"], summary="Hamstring flexibility drill performed on the back with optional strap support.", setup="Lie on back and lift one leg with hands behind thigh or strap support.", execution="Straighten the knee gently until a stretch is felt behind the thigh, without pulling at the knee joint.", prescription={"hold": "30-60 sec each side", "sets": "1-3"}, coaching_cues=["Keep the opposite leg relaxed.", "Stretch the muscle, not the knee joint."], common_errors=["Pulling behind the knee.", "Forcing toes toward face aggressively."], use_when=["post-run", "post-lift", "knee conditioning"], avoid_when=["nerve symptoms or sharp posterior knee pain"], source_ids=["aaos_knee", "mayo_basic_stretches"]),
    _drill(id="mob_drill_dynamic_hamstring_floor", name="Dynamic Hamstring Floor Stretch", category="dynamic_mobility", phase="pre_workout_or_rehab", body_regions=["hamstring", "knee"], addresses=["hamstring_mobility", "knee_support", "running"], equipment=["bodyweight", "mat"], summary="Controlled hamstring mobility drill that bends and straightens the knee through comfortable range.", setup="Lie on back and bring one knee toward the chest while holding behind the thigh.", execution="Slowly straighten and bend the knee without forcing end range.", prescription={"reps": "10-15 each side", "sets": "1-2"}, coaching_cues=["Move smoothly.", "Stay inside comfortable range."], common_errors=["Forcing straight knee.", "Pulling on the knee joint."], use_when=["knee-friendly mobility", "pre-run warm-up"], avoid_when=["sciatic-type nerve symptoms"], source_ids=["hss_knee"]),
    _drill(id="mob_drill_calves_wall_stretch", name="Calf Wall Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["calf", "ankle"], addresses=["calf_flexibility", "ankle_dorsiflexion", "running", "jumping"], equipment=["wall"], summary="Straight-knee calf stretch for gastrocnemius and ankle mobility.", setup="Stand facing a wall with one foot behind.", execution="Keep back knee straight and heel down while bending the front knee until calf tension appears.", prescription={"hold": "30 sec each side", "sets": "2-4"}, coaching_cues=["Keep toes pointed forward.", "Press heel down without bouncing."], common_errors=["Back foot turning out.", "Heel lifting."], use_when=["post-run", "post-jump", "ankle mobility"], avoid_when=["acute Achilles pain"], source_ids=["mayo_basic_stretches", "aaos_knee"]),
    _drill(id="mob_drill_soleus_wall_stretch", name="Soleus Wall Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["soleus", "ankle"], addresses=["ankle_dorsiflexion", "running", "jump_landing"], equipment=["wall"], summary="Bent-knee calf stretch emphasizing soleus for running and landing mechanics.", setup="Stand in a staggered stance facing a wall.", execution="Bend the back knee while keeping heel down until lower-calf/Achilles area tension is felt.", prescription={"hold": "30 sec each side", "sets": "2-4"}, coaching_cues=["Keep heel heavy.", "Use gentle pressure only."], common_errors=["Collapsing arch.", "Bouncing."], use_when=["post-run", "ankle recovery", "squat prep"], avoid_when=["reactive Achilles pain"], source_ids=["mayo_basic_stretches"]),
    _drill(id="mob_drill_quad_stretch", name="Standing Quadriceps Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["quad", "hip_flexor", "knee"], addresses=["quad_flexibility", "knee_conditioning"], equipment=["bodyweight", "wall_support_optional"], summary="Standing quad stretch for front-thigh flexibility and knee conditioning.", setup="Stand near a wall or chair for balance.", execution="Bend one knee, hold the ankle, and gently bring heel toward glute while staying tall.", prescription={"hold": "30-60 sec each side", "sets": "2-3"}, coaching_cues=["Keep knees close together.", "Use support to avoid twisting."], common_errors=["Arching low back.", "Pulling into knee pain."], use_when=["post-leg training", "knee conditioning"], avoid_when=["painful knee flexion"], source_ids=["aaos_knee"]),
    _drill(id="mob_drill_posterior_capsule", name="Crossover Arm Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["shoulder", "posterior_deltoid"], addresses=["posterior_shoulder", "throwing", "overhead_sports"], equipment=["bodyweight"], summary="Posterior shoulder stretch for throwing and upper-body athletes.", setup="Stand or sit tall with shoulders relaxed.", execution="Bring one arm across chest and gently hold at the upper arm, not the elbow.", prescription={"hold": "20-30 sec each side", "sets": "2-4"}, coaching_cues=["Keep shoulder relaxed.", "Pull gently across, not down into pain."], common_errors=["Pulling on elbow.", "Shrugging the neck."], use_when=["post-throw", "post-upper-body", "shoulder mobility"], avoid_when=["sharp shoulder pain"], source_ids=["hss_static_dynamic", "aaos_shoulder"]),
    _drill(id="mob_drill_sleeper_stretch", name="Sleeper Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["shoulder", "posterior_capsule"], addresses=["shoulder_internal_rotation", "throwing", "overhead_sports"], equipment=["bodyweight", "mat"], summary="Posterior shoulder/internal-rotation stretch used carefully for overhead athletes.", setup="Lie on side with shoulder and elbow bent.", execution="Use the opposite hand to gently guide the forearm down until a stretch is felt behind the shoulder.", prescription={"hold": "20-30 sec", "sets": "1-3"}, coaching_cues=["Keep shoulder blade stable.", "Use very gentle pressure."], common_errors=["Pressing on wrist.", "Forcing painful internal rotation."], use_when=["throwing shoulder mobility", "clinician-approved shoulder routine"], avoid_when=["shoulder impingement symptoms", "painful anterior shoulder"], source_ids=["aaos_shoulder"]),
    _drill(id="mob_drill_doorway_pec", name="Doorway Pec Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["chest", "shoulder"], addresses=["pec_flexibility", "posture", "overhead_mobility"], equipment=["doorway"], summary="Chest/pec stretch for posture and shoulder positioning.", setup="Place forearm on a doorway with elbow below or near shoulder height.", execution="Step through gently until a stretch appears across chest, keeping ribs controlled.", prescription={"hold": "20-45 sec each side", "sets": "1-3"}, coaching_cues=["Keep shoulder down away from ear.", "Use low to moderate arm angle first."], common_errors=["Overarching low back.", "Numbing or tingling down arm."], use_when=["post-pressing", "desk posture mobility"], avoid_when=["nerve symptoms", "shoulder instability"], source_ids=["hss_cross_syndrome", "aaos_shoulder"]),
    _drill(id="mob_drill_childs_pose_lat", name="Child's Pose Lat Stretch", category="static_stretch", phase="post_workout_or_recovery", body_regions=["lat", "thoracic_spine", "shoulder"], addresses=["lat_flexibility", "overhead_mobility", "back_relaxation"], equipment=["bodyweight", "mat"], summary="Gentle lat and back stretch useful after pulling, pressing, or overhead work.", setup="Kneel and sit hips back toward heels with arms reaching forward.", execution="Reach hands long, breathe into ribs, and optionally walk hands to each side.", prescription={"hold": "30-60 sec", "sets": "1-3"}, coaching_cues=["Let breathing expand the back.", "Use padding under knees if needed."], common_errors=["Forcing hips to heels through knee pain.", "Holding breath."], use_when=["cooldown", "overhead mobility", "back-friendly recovery"], avoid_when=["knee pain in kneeling", "shoulder pain overhead"], source_ids=["aaos_spine", "mayo_back"]),
    _drill(id="mob_drill_neck_side_bend", name="Neck Side-Bend Stretch", category="static_stretch", phase="recovery", body_regions=["neck", "upper_trapezius"], addresses=["neck_stiffness", "desk_posture"], equipment=["bodyweight"], summary="Gentle neck mobility/stretch drill for upper-trap stiffness.", setup="Sit or stand tall.", execution="Tilt one ear toward the same-side shoulder until gentle tension appears on the opposite side.", prescription={"hold": "15-30 sec each side", "sets": "1-3"}, coaching_cues=["Keep shoulders relaxed.", "Do not pull aggressively on the head."], common_errors=["Forcing range.", "Rotating while side-bending unintentionally."], use_when=["desk mobility", "cooldown"], avoid_when=["dizziness", "nerve symptoms", "acute neck injury"], source_ids=["aaos_spine"]),
    _drill(id="mob_drill_wrist_rocks", name="Wrist Rocks", category="dynamic_mobility", phase="pre_workout", body_regions=["wrist", "forearm"], addresses=["wrist_extension", "pushup_prep", "handstand_prep"], equipment=["bodyweight", "mat"], summary="Wrist preparation drill for floor-based strength, yoga, calisthenics, and pressing.", setup="Start on hands and knees with palms flat or fists if needed.", execution="Rock shoulders forward and back over the wrists within comfortable range.", prescription={"reps": "8-15", "sets": "1-2"}, coaching_cues=["Spread fingers and press through knuckles.", "Increase range gradually."], common_errors=["Dumping weight suddenly into wrists.", "Ignoring tingling."], use_when=["push-up warm-up", "handstand prep"], avoid_when=["acute wrist pain or numbness"], source_ids=["mayo_basic_stretches"]),
    _drill(id="mob_drill_short_foot", name="Short Foot", category="activation", phase="pre_workout_or_rehab", body_regions=["foot", "ankle"], addresses=["arch_control", "ankle_stability", "running", "balance"], equipment=["bodyweight"], summary="Foot intrinsic activation drill for arch control and ankle stability.", setup="Stand or sit with foot flat.", execution="Gently draw the ball of the foot toward the heel without curling toes.", prescription={"holds": "5-10 sec", "reps": "5-10 each foot"}, coaching_cues=["Keep toes relaxed.", "Think of shortening the arch."], common_errors=["Toe curling.", "Rolling to outside foot."], use_when=["pre-run", "ankle rehab", "balance prep"], avoid_when=["foot cramping that does not settle"], source_ids=["aaos_knee", "mayo_osteoporosis"]),
    _drill(id="mob_drill_supported_single_leg_balance", name="Supported Single-Leg Balance", category="activation_balance", phase="warmup_or_recovery", body_regions=["ankle", "hip", "foot"], addresses=["balance", "older_adults", "ankle_stability", "fall_prevention"], equipment=["wall_support_optional"], summary="Low-risk balance and stabilizer drill for older adults, ankle rehab, and warm-ups.", setup="Stand near a wall or chair.", execution="Shift onto one leg and hold balance while maintaining tall posture.", prescription={"hold": "10-30 sec each side", "sets": "2-4"}, coaching_cues=["Use fingertip support if needed.", "Keep hips level."], common_errors=["Holding breath.", "Letting knee collapse inward."], use_when=["older adult mobility", "ankle rehab", "warm-up"], avoid_when=["unsafe balance without support"], source_ids=["mayo_osteoporosis", "aaos_knee"]),
    _drill(id="mob_drill_prone_press_up", name="Prone Press-Up", category="spine_mobility", phase="recovery_or_rehab", body_regions=["lumbar_spine", "hip_flexor"], addresses=["back_extension", "desk_posture", "low_back"], equipment=["bodyweight", "mat"], summary="Gentle extension-biased back mobility drill for users who tolerate prone extension.", setup="Lie face down with hands under shoulders.", execution="Press chest up using arms while hips remain down, stopping below pain.", prescription={"reps": "6-10", "sets": "1-3"}, coaching_cues=["Relax glutes and breathe.", "Use smaller range if symptoms increase."], common_errors=["Pushing through sharp back pain.", "Shrugging shoulders."], use_when=["back extension mobility", "desk-work reset"], avoid_when=["extension-sensitive back pain", "radiating symptoms"], source_ids=["mayo_back", "aaos_spine"]),
    _drill(id="mob_drill_wall_angel", name="Wall Angel", category="activation_mobility", phase="warmup_or_recovery", body_regions=["shoulder", "thoracic_spine", "scapula"], addresses=["posture", "overhead_mobility", "older_adults"], equipment=["wall"], summary="Posture and shoulder mobility drill against a wall.", setup="Stand with back near a wall and ribs down.", execution="Slide arms upward and downward in a pain-free range while maintaining posture.", prescription={"reps": "6-12", "sets": "1-3"}, coaching_cues=["Use only the range you own.", "Keep neck relaxed."], common_errors=["Arching back to reach higher.", "Forcing shoulder contact."], use_when=["posture routine", "overhead warm-up", "older adult mobility"], avoid_when=["painful shoulder pinch"], source_ids=["hss_cross_syndrome", "mayo_osteoporosis"]),
]


WORKOUT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "mob_template_general_dynamic_warmup",
        "title": "General Dynamic Warm-Up",
        "category": "mobility_warmup",
        "level": "beginner",
        "summary": "A simple pre-workout sequence for normal users before strength, cardio, or sport practice.",
        "duration_min": 8,
        "drills": ["mob_drill_arm_circles", "mob_drill_leg_swing_front_back", "mob_drill_lateral_leg_swing", "mob_drill_worlds_greatest_stretch", "mob_drill_ankle_knee_to_wall"],
        "sport_tags": ["general_fitness", "warmup", "mobility"],
        "equipment_required": ["bodyweight"],
    },
    {
        "id": "mob_template_post_workout_cooldown",
        "title": "Post-Workout Flexibility Cooldown",
        "category": "mobility_cooldown",
        "level": "beginner",
        "summary": "A post-session static stretching sequence for lower body, shoulders, and breathing.",
        "duration_min": 10,
        "drills": ["mob_drill_calves_wall_stretch", "mob_drill_quad_stretch", "mob_drill_half_kneeling_hip_flexor", "mob_drill_figure_4", "mob_drill_childs_pose_lat"],
        "sport_tags": ["recovery", "flexibility", "cooldown"],
        "equipment_required": ["bodyweight"],
    },
    {
        "id": "mob_template_runner_pre_run",
        "title": "Runner Pre-Run Mobility And Activation",
        "category": "mobility_warmup",
        "level": "beginner",
        "summary": "Dynamic hip, ankle, hamstring, and glute preparation for running.",
        "duration_min": 8,
        "drills": ["mob_drill_leg_swing_front_back", "mob_drill_lateral_leg_swing", "mob_drill_dynamic_hamstring_floor", "mob_drill_ankle_knee_to_wall", "mob_drill_glute_bridge", "mob_drill_short_foot"],
        "sport_tags": ["running", "warmup", "hip", "ankle"],
        "equipment_required": ["bodyweight"],
    },
    {
        "id": "mob_template_overhead_athlete_shoulder",
        "title": "Overhead Athlete Shoulder Prep",
        "category": "activation_mobility",
        "level": "intermediate",
        "summary": "Shoulder, thoracic, scapular, and rotator-cuff preparation for throwing, swimming, volleyball, cricket, and pressing.",
        "duration_min": 10,
        "drills": ["mob_drill_open_book", "mob_drill_wall_slide", "mob_drill_band_external_rotation", "mob_drill_band_pull_apart", "mob_drill_scap_pushup"],
        "sport_tags": ["overhead", "throwing", "volleyball", "cricket", "swimming"],
        "equipment_required": ["resistance_band", "wall"],
    },
    {
        "id": "mob_template_knee_friendly_lower_body",
        "title": "Knee-Friendly Lower-Body Prep",
        "category": "activation_mobility",
        "level": "beginner",
        "summary": "Hip, ankle, hamstring, quad, and glute prep for users with knee sensitivity or field/court sport demands.",
        "duration_min": 10,
        "drills": ["mob_drill_dynamic_hamstring_floor", "mob_drill_half_kneeling_hip_flexor", "mob_drill_ankle_knee_to_wall", "mob_drill_clamshell", "mob_drill_lateral_band_walk"],
        "sport_tags": ["knee", "running", "field_sports", "court_sports"],
        "equipment_required": ["bodyweight", "mini_band"],
    },
    {
        "id": "mob_template_back_friendly_recovery",
        "title": "Back-Friendly Recovery Mobility",
        "category": "recovery_mobility",
        "level": "beginner",
        "summary": "Gentle spine, hip, and trunk control sequence for low-back stiffness when pain-free.",
        "duration_min": 10,
        "drills": ["mob_drill_cat_cow", "mob_drill_dead_bug", "mob_drill_bird_dog", "mob_drill_figure_4", "mob_drill_childs_pose_lat"],
        "sport_tags": ["low_back", "recovery", "core"],
        "equipment_required": ["bodyweight", "mat"],
    },
    {
        "id": "mob_template_older_adult_daily",
        "title": "Older Adult Daily Mobility And Balance",
        "category": "daily_mobility",
        "level": "beginner",
        "summary": "Gentle daily mobility, posture, ankle/hip control, and supported balance work.",
        "duration_min": 8,
        "drills": ["mob_drill_wall_angel", "mob_drill_supported_single_leg_balance", "mob_drill_ankle_knee_to_wall", "mob_drill_neck_side_bend", "mob_drill_short_foot"],
        "sport_tags": ["older_adults", "balance", "mobility"],
        "equipment_required": ["bodyweight", "wall_support_optional"],
    },
    {
        "id": "mob_template_desk_worker_reset",
        "title": "Desk Worker Mobility Reset",
        "category": "daily_mobility",
        "level": "beginner",
        "summary": "Short movement snack for hips, chest, neck, thoracic spine, and shoulders after long sitting.",
        "duration_min": 6,
        "drills": ["mob_drill_half_kneeling_hip_flexor", "mob_drill_doorway_pec", "mob_drill_open_book", "mob_drill_wall_angel", "mob_drill_neck_side_bend"],
        "sport_tags": ["desk_work", "posture", "daily_mobility"],
        "equipment_required": ["bodyweight", "wall"],
    },
]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _source_refs(source_ids: Sequence[str], heading: str) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for source_id in source_ids:
        source = SOURCES[source_id]
        refs.append(
            {
                "source_book_id": SOURCE_PACK_ID,
                "source_id": source_id,
                "section_id": f"mob_src_{source_id}",
                "section_title": source["title"],
                "heading": heading,
                "url": source["url"],
                "source_type": source["type"],
            }
        )
    return refs


def _merge_list(existing: Any, incoming: Any) -> List[Any]:
    result: List[Any] = []
    for value in [existing, incoming]:
        items = value if isinstance(value, list) else [value]
        for item in items:
            if item in (None, "", [], {}):
                continue
            if item not in result:
                result.append(item)
    return result


def _merge_doc(existing: Dict[str, Any], incoming: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    merged = dict(existing)
    list_fields = {
        "aliases",
        "equipment",
        "equipment_required",
        "patterns",
        "movement_patterns",
        "qualities",
        "training_qualities",
        "sport_tags",
        "primary_muscles",
        "secondary_muscles",
        "coaching_cues",
        "common_errors",
        "use_when",
        "avoid_when",
        "contraindications",
        "injury_flags",
        "progressions",
        "regressions",
        "source_refs",
        "source_book_ids",
        "addresses",
        "body_regions",
        "topics",
        "applies_to",
        "recommended_focus",
    }
    for key, value in incoming.items():
        if key == "_id":
            continue
        if key in list_fields:
            merged[key] = _merge_list(merged.get(key), value)
        elif key == "created_at" and merged.get(key):
            continue
        elif value not in (None, "", [], {}):
            merged[key] = value
    merged["source_book_ids"] = _merge_list(merged.get("source_book_ids"), SOURCE_PACK_ID)
    merged["updated_at"] = now
    return merged


async def _upsert_many(db: Any, collection_name: str, docs: Iterable[Dict[str, Any]]) -> int:
    now = datetime.utcnow()
    collection = db[collection_name]
    count = 0
    for doc in docs:
        doc = {**doc, "updated_at": now}
        doc.setdefault("created_at", now)
        if collection_name == "source_sections" and doc.get("source_book_id") == SOURCE_PACK_ID:
            await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
            count += 1
            continue
        existing = await collection.find_one({"id": doc["id"]})
        if not existing and doc.get("name"):
            existing = await collection.find_one({"name": doc["name"]})
        if existing:
            merged = _merge_doc(existing, doc, now)
            await collection.replace_one({"id": existing["id"]}, merged)
        else:
            await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
        count += 1
    return count


def _source_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    order = 8000
    for source_id, source in SOURCES.items():
        order += 1
        docs.append(
            {
                "id": f"mob_src_{source_id}",
                "source_book_id": SOURCE_PACK_ID,
                "section_order": order,
                "section_title": source["title"],
                "domain": "mobility_flexibility",
                "topics": ["mobility", "flexibility", source_id],
                "summary": f"Web reference used for curated mobility and flexibility knowledge: {source['title']}.",
                "url": source["url"],
                "source_type": source["type"],
                "created_at": now,
                "updated_at": now,
            }
        )
    for drill in DRILLS:
        order += 1
        docs.append(
            {
                "id": f"mob_section_drill_{_slug(drill['name'])}",
                "source_book_id": SOURCE_PACK_ID,
                "section_order": order,
                "section_title": drill["name"],
                "domain": "mobility_flexibility",
                "topics": sorted(set(["mobility", drill["category"], drill["phase"], *drill["body_regions"], *drill["addresses"]])),
                "summary": drill["summary"],
                "source_text_hash": hashlib.sha256(f"{drill['setup']} {drill['execution']} {drill['summary']}".encode()).hexdigest(),
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _mobility_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs = []
    for drill in DRILLS:
        docs.append(
            {
                **{k: v for k, v in drill.items() if k != "source_ids"},
                "topics": sorted(set(["mobility", "flexibility", drill["category"], drill["phase"], *drill["addresses"], *drill["body_regions"]])),
                "source_book_id": SOURCE_PACK_ID,
                "source_book_ids": [SOURCE_PACK_ID],
                "source_refs": _source_refs(drill["source_ids"], drill["name"]),
                "expert_validation_status": "pending",
                "ingestion_method": INGESTION_METHOD,
                "version": "v1.0.0",
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _primary_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs = []
    for drill in DRILLS:
        patterns = sorted(set([drill["category"], drill["phase"], *drill["addresses"]]))
        qualities = sorted(set(["mobility", "flexibility", "activation", drill["phase"]]))
        docs.append(
            {
                "id": drill["id"],
                "name": drill["name"],
                "aliases": drill["aliases"],
                "base_exercise": drill["category"],
                "category": "mobility_flexibility",
                "difficulty": drill["difficulty"],
                "default_user_level": drill["difficulty"],
                "technical_complexity": "low" if drill["difficulty"] == "beginner" else "moderate",
                "mobility_requirement": "low",
                "stability_requirement": "moderate" if "activation" in drill["category"] else "low",
                "impact_level": "low",
                "load_scalability": "low",
                "coaching_requirement": "moderate",
                "beginner_usable_as_drill": True,
                "equipment": drill["equipment"],
                "patterns": patterns,
                "qualities": qualities,
                "sport_tags": sorted(set(["mobility", "flexibility", "warmup", "cooldown", *drill["addresses"], *drill["body_regions"]])),
                "primary_muscles": drill["body_regions"],
                "secondary_muscles": [],
                "summary": drill["summary"],
                "coaching_cues": drill["coaching_cues"],
                "common_errors": drill["common_errors"],
                "use_when": drill["use_when"],
                "avoid_when": drill["avoid_when"],
                "progressions": [],
                "regressions": [],
                "sample_prescription": drill["prescription"],
                "source_book_id": SOURCE_PACK_ID,
                "source_book_ids": [SOURCE_PACK_ID],
                "source_refs": _source_refs(drill["source_ids"], drill["name"]),
                "expert_validation_status": "pending",
                "ingestion_method": INGESTION_METHOD,
                "version": "v1.0.0",
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _raw_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs = []
    for drill in DRILLS:
        docs.append(
            {
                "id": f"{drill['id']}_raw",
                "name": drill["name"],
                "aliases": drill["aliases"],
                "definition": drill["summary"],
                "exercise_family": drill["category"],
                "exercise_type": "mobility_flexibility",
                "category": "mobility_flexibility",
                "difficulty": drill["difficulty"],
                "equipment_required": drill["equipment"],
                "movement_patterns": sorted(set([drill["category"], drill["phase"], *drill["addresses"]])),
                "training_qualities": ["mobility", "flexibility", "activation", drill["phase"]],
                "primary_muscles": drill["body_regions"],
                "secondary_muscles": [],
                "coaching_cues": drill["coaching_cues"],
                "common_errors": drill["common_errors"],
                "contraindications": drill["avoid_when"],
                "injury_flags": drill["avoid_when"],
                "progressions": [],
                "regressions": [],
                "sport_tags": sorted(set(["mobility", "flexibility", "warmup", "cooldown", *drill["addresses"], *drill["body_regions"]])),
                "summary": drill["summary"],
                "source_extract": {"setup": drill["setup"], "execution": drill["execution"], "prescription": drill["prescription"]},
                "source_book_id": SOURCE_PACK_ID,
                "source_book_ids": [SOURCE_PACK_ID],
                "source_refs": _source_refs(drill["source_ids"], drill["name"]),
                "expert_validation_status": "pending",
                "ingestion_method": INGESTION_METHOD,
                "version": "v1.0.0",
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _principle_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **{k: v for k, v in item.items() if k != "source_ids"},
            "domain": "mobility_flexibility",
            "knowledge_type": "training_principle",
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(item["source_ids"], item["title"]),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in TRAINING_PRINCIPLES
    ]


def _rule_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **{k: v for k, v in item.items() if k != "source_ids"},
            "knowledge_type": "programming_rule",
            "topics": item.get("applies_to") or [],
            "usage_context": item["rule_text"],
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(item["source_ids"], item["title"]),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in PROGRAMMING_RULES
    ]


def _recovery_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **{k: v for k, v in item.items() if k != "source_ids"},
            "knowledge_type": "recovery_rule",
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(item["source_ids"], item["title"]),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in RECOVERY_RULES
    ]


def _injury_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **{k: v for k, v in item.items() if k != "source_ids"},
            "knowledge_type": "injury_modification",
            "topics": [item["body_area"], "mobility", "flexibility", "modification"],
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(item["source_ids"], item["title"]),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in INJURY_MODIFICATIONS
    ]


def _template_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **item,
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs(["hss_static_dynamic", "mayo_basic_stretches"], item["title"]),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in WORKOUT_TEMPLATES
    ]


async def ingest() -> Dict[str, int]:
    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    await ensure_database_schema(db)

    now = datetime.utcnow()
    source_doc = {
        "id": SOURCE_PACK_ID,
        "title": "Mobility and Flexibility Web Research Pack",
        "source_type": "manual_web_research",
        "domains": ["mobility", "flexibility", "activation", "warmup", "cooldown", "injury_modification"],
        "summary": "Curated mobility and flexibility knowledge for warm-ups, cooldowns, activation, general users, older adults, youth, sports preparation, and injury-sensitive modifications.",
        "source_count": len(SOURCES),
        "drill_count": len(DRILLS),
        "ingestion_method": INGESTION_METHOD,
        "created_at": now,
        "updated_at": now,
    }

    counts: Dict[str, int] = {}
    for collection in ("source_registry", "knowledge_sources"):
        await db[collection].replace_one({"id": SOURCE_PACK_ID}, source_doc, upsert=True)
        counts[collection] = 1

    counts["source_sections"] = await _upsert_many(db, "source_sections", _source_docs())
    counts["mobility_drills"] = await _upsert_many(db, "mobility_drills", _mobility_docs())
    counts["primary_exercise_library"] = await _upsert_many(db, "primary_exercise_library", _primary_docs())
    counts["exercise_library"] = await _upsert_many(db, "exercise_library", _raw_docs())
    counts["training_principles"] = await _upsert_many(db, "training_principles", _principle_docs())
    counts["programming_rules"] = await _upsert_many(db, "programming_rules", _rule_docs())
    counts["recovery_rules"] = await _upsert_many(db, "recovery_rules", _recovery_docs())
    counts["injury_modifications"] = await _upsert_many(db, "injury_modifications", _injury_docs())
    counts["workout_templates"] = await _upsert_many(db, "workout_templates", _template_docs())
    client.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest source-backed mobility and flexibility web research into MongoDB.")
    return parser.parse_args()


def main() -> None:
    parse_args()
    counts = asyncio.run(ingest())
    for collection, count in counts.items():
        print(f"{collection}: {count}")


if __name__ == "__main__":
    main()

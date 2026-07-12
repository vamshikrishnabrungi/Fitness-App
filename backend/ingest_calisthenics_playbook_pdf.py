from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = PROJECT_ROOT / "dokumen.pub_calisthenics-playbook-for-push-pull-squat-9789811879098.pdf"
DEFAULT_OCR_CACHE = Path("/tmp/calisthenics_playbook_ocr_pages.jsonl")
SOURCE_BOOK_ID = "calisthenics_playbook_push_pull_squat_2024"
INGESTION_METHOD = "pdf_ocr_curated_calisthenics_extraction_v1"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _source_ref(section_id: str, pages: Sequence[int], heading: str) -> Dict[str, Any]:
    return {
        "source_book_id": SOURCE_BOOK_ID,
        "section_id": section_id,
        "section_title": heading,
        "page_start": min(pages),
        "page_end": max(pages),
        "heading": heading,
    }


def _first_heading(text: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped and not stripped.isdigit():
            return stripped[:120]
    return "Blank or image-only page"


def _load_ocr_cache(path: Path) -> Dict[int, Dict[str, Any]]:
    if not path.exists():
        return {}
    pages: Dict[int, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            pages[int(record["page"])] = record
    return pages


def _ocr_pdf_to_cache(pdf_path: Path, cache_path: Path) -> Dict[int, Dict[str, Any]]:
    try:
        import fitz
        from PIL import Image
        from ocrmac.ocrmac import OCR
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies missing. Install backend dev dependencies: pip install -r backend/requirements-dev.txt"
        ) from exc

    doc = fitz.open(str(pdf_path))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pages: Dict[int, Dict[str, Any]] = {}
    with cache_path.open("w", encoding="utf-8") as handle:
        for page_number, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            rows = OCR(image, recognition_level="accurate", detail=True).recognize()
            lines = [str(row[0]).strip() for row in rows if row and str(row[0]).strip()]
            text = "\n".join(lines).strip()
            record = {
                "page": page_number,
                "chars": len(text),
                "text_hash": _hash_text(text),
                "text": text,
            }
            pages[page_number] = record
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            if page_number % 10 == 0 or page_number == len(doc):
                print(f"OCR page {page_number}/{len(doc)} chars={len(text)}", flush=True)
    return pages


def load_ocr_pages(pdf_path: Path, cache_path: Path) -> Dict[int, Dict[str, Any]]:
    pages = _load_ocr_cache(cache_path)
    if pages:
        return pages
    return _ocr_pdf_to_cache(pdf_path, cache_path)


SECTIONS: List[Dict[str, Any]] = [
    {
        "id": "cal_section_overview",
        "title": "Playbook Overview",
        "pages": [11],
        "topics": ["overview", "push", "pull", "squat", "routine"],
        "summary": "The playbook is organized around three skills: one-arm push-up, pull-up, and pistol squat. It uses progressions and a routine section to connect exercises into training levels.",
    },
    {
        "id": "cal_section_one_arm_pushup_program",
        "title": "One-Arm Push-Up Program",
        "pages": list(range(12, 44)),
        "topics": ["push", "one_arm_push_up", "upper_body_strength", "bodyweight"],
        "summary": "A push progression that begins with plank control and scapular strength, then builds through eccentric, standard, close-grip, wide, explosive, archer, and one-arm push-up variations.",
    },
    {
        "id": "cal_section_pullup_program",
        "title": "Pull-Up Program",
        "pages": list(range(44, 78)),
        "topics": ["pull", "pull_up", "upper_body_strength", "grip", "scapular_control"],
        "summary": "A pull progression that includes shoulder/back warm-ups, grip exposure, scapular control, horizontal pulling, assisted vertical pulling, eccentric pull-ups, and full pull-ups.",
    },
    {
        "id": "cal_section_pistol_squat_program",
        "title": "Pistol Squat Program",
        "pages": list(range(78, 102)),
        "topics": ["squat", "pistol_squat", "single_leg_strength", "mobility", "balance"],
        "summary": "A squat progression that moves from bilateral squat competence to narrow, deep, split, lateral, assisted single-leg, eccentric, and full pistol squat variations.",
    },
    {
        "id": "cal_section_training_routine",
        "title": "Training Routine",
        "pages": list(range(102, 114)),
        "topics": ["routine", "progression", "sets", "reps", "tempo", "rest", "weekly_schedule"],
        "summary": "The routine section defines five levels for push, pull, and squat skills, progression criteria, tempo/rest conventions, and weekly organization options.",
    },
]


EXERCISES: List[Dict[str, Any]] = [
    {
        "id": "cal_ex_plank_hold",
        "library": "primary",
        "name": "Plank Hold",
        "aliases": ["High Plank Hold"],
        "base_exercise": "plank",
        "category": "core",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["brace", "anti_extension", "shoulder_stability"],
        "qualities": ["trunk_stiffness", "body_control", "push_up_foundation"],
        "primary_muscles": ["abdominals", "trunk", "shoulders"],
        "secondary_muscles": ["glutes", "quadriceps", "serratus_anterior"],
        "summary": "Foundational isometric hold for trunk stiffness, shoulder protraction, glute tension, and full-body push-up alignment.",
        "coaching_cues": [
            "Keep a straight line from head to heels.",
            "Brace the trunk while breathing steadily.",
            "Push the shoulder blades apart instead of hanging passively.",
            "Squeeze the glutes and keep the hips from sagging or piking.",
        ],
        "common_errors": [
            "Sagging the lower back.",
            "Piking the hips too high.",
            "Holding the breath.",
            "Letting the shoulder blades collapse together.",
        ],
        "use_when": ["beginner push-up foundation", "core control warm-up", "bodyweight strength base"],
        "avoid_when": ["wrist pain without support option", "shoulder pain aggravated by plank loading"],
        "progressions": ["cal_ex_scapula_push_up", "cal_ex_negative_push_up"],
        "regressions": ["incline plank hold", "forearm plank hold"],
        "pages": [14, 15],
    },
    {
        "id": "cal_ex_scapula_push_up",
        "library": "primary",
        "name": "Scapula Push-Up",
        "aliases": ["Scapular Push-Up", "Straight-Arm Scapula Push-Up"],
        "base_exercise": "push_up",
        "category": "mobility",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["push", "scapular_control", "brace"],
        "qualities": ["shoulder_stability", "serratus_strength", "push_up_foundation"],
        "primary_muscles": ["serratus_anterior", "shoulders"],
        "secondary_muscles": ["chest", "trunk"],
        "summary": "Straight-arm scapular drill that teaches shoulder blade protraction/retraction while maintaining plank alignment.",
        "coaching_cues": [
            "Keep elbows straight and move only through the shoulder blades.",
            "Round the upper back at the top by pushing the ground away.",
            "Turn biceps slightly outward and keep the trunk braced.",
            "Pause briefly in the protracted top position.",
        ],
        "common_errors": ["Bending the elbows like a push-up.", "Losing plank alignment.", "Shrugging instead of controlling scapular motion."],
        "use_when": ["push-up warm-up", "shoulder stability foundation", "serratus activation"],
        "avoid_when": ["sharp wrist or shoulder pain"],
        "progressions": ["cal_ex_negative_push_up", "cal_ex_push_up"],
        "regressions": ["incline scapula push-up", "quadruped scapula push-up"],
        "pages": [16, 17],
    },
    {
        "id": "cal_ex_negative_push_up",
        "library": "primary",
        "name": "Negative Push-Up",
        "aliases": ["Eccentric Push-Up"],
        "base_exercise": "push_up",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["push", "eccentric_control", "brace"],
        "qualities": ["eccentric_strength", "push_strength", "body_control"],
        "primary_muscles": ["chest", "triceps", "anterior_deltoids"],
        "secondary_muscles": ["trunk", "serratus_anterior"],
        "summary": "Push-up regression emphasizing slow, controlled lowering to build eccentric strength and movement control.",
        "coaching_cues": [
            "Start in a strong plank.",
            "Lower slower than a normal push-up.",
            "Keep elbows controlled and body tension high.",
            "Optionally pause near the bottom before resetting.",
        ],
        "common_errors": ["Dropping quickly to the floor.", "Letting hips sag.", "Losing elbow control."],
        "use_when": ["building toward full push-ups", "eccentric strength block", "beginner upper-body strength"],
        "avoid_when": ["shoulder pain at bottom range", "wrist pain without modification"],
        "progressions": ["cal_ex_push_up"],
        "regressions": ["incline negative push-up"],
        "pages": [18, 19],
    },
    {
        "id": "cal_ex_push_up",
        "library": "primary",
        "name": "Push-Up",
        "aliases": ["Normal Push-Up", "Standard Push-Up"],
        "base_exercise": "push_up",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["push", "brace"],
        "qualities": ["upper_body_strength", "trunk_stiffness", "bodyweight_strength"],
        "primary_muscles": ["chest", "triceps", "anterior_deltoids"],
        "secondary_muscles": ["trunk", "serratus_anterior", "quadriceps"],
        "summary": "Standard bodyweight push pattern and foundation for harder pushing variations.",
        "coaching_cues": [
            "Set hands around shoulder width and brace like a plank.",
            "Lower with control while keeping elbows close enough to stay strong.",
            "Keep the forearm close to vertical near the bottom.",
            "Press back to the plank without losing body tension.",
        ],
        "common_errors": ["Relying too much on shoulders.", "Letting the chest or hips collapse.", "Flaring elbows excessively."],
        "use_when": ["general upper-body strength", "bodyweight strength testing", "push-up progression base"],
        "avoid_when": ["painful shoulder range", "wrist pain without handles or incline option"],
        "progressions": ["cal_ex_diamond_push_up", "cal_ex_wide_push_up", "cal_ex_explosive_push_up", "cal_var_archer_push_up"],
        "regressions": ["cal_ex_negative_push_up", "incline push-up"],
        "pages": [20, 21, 22, 23, 24],
    },
    {
        "id": "cal_ex_wide_push_up",
        "library": "primary",
        "name": "Wide Push-Up",
        "aliases": ["Wide-Grip Push-Up"],
        "base_exercise": "push_up",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["bodyweight"],
        "patterns": ["push", "horizontal_push", "brace"],
        "qualities": ["chest_strength", "shoulder_control", "push_variation"],
        "primary_muscles": ["chest", "anterior_deltoids"],
        "secondary_muscles": ["triceps", "trunk"],
        "summary": "Push-up variation with wider hands to increase chest/shoulder emphasis and vary pushing stress.",
        "coaching_cues": [
            "Place hands wider than shoulders with fingers angled comfortably.",
            "Keep shoulders down and push the ground away.",
            "Maintain a strong plank line throughout.",
        ],
        "common_errors": ["Overreaching too wide.", "Letting shoulders shrug.", "Losing trunk position."],
        "use_when": ["push-up variety", "chest-biased bodyweight work", "one-arm push-up preparation"],
        "avoid_when": ["shoulder pain with wide arm positions"],
        "progressions": ["cal_var_archer_push_up"],
        "regressions": ["cal_ex_push_up", "incline wide push-up"],
        "pages": [26, 27],
    },
    {
        "id": "cal_ex_diamond_push_up",
        "library": "primary",
        "name": "Diamond Push-Up",
        "aliases": ["Close-Grip Push-Up"],
        "base_exercise": "push_up",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["bodyweight"],
        "patterns": ["push", "close_grip_push", "brace"],
        "qualities": ["triceps_strength", "chest_strength", "push_variation"],
        "primary_muscles": ["triceps", "chest"],
        "secondary_muscles": ["anterior_deltoids", "trunk"],
        "summary": "Close-hand push-up variation that increases triceps and inner-chest demand compared with wider hand placements.",
        "coaching_cues": [
            "Start in a high plank with hands close under the chest.",
            "Keep shoulders over wrists and trunk braced.",
            "Use a hand distance that allows pain-free wrists and elbows.",
        ],
        "common_errors": ["Forcing fingertip contact when wrists dislike it.", "Letting elbows flare without control.", "Collapsing at the bottom."],
        "use_when": ["triceps-focused bodyweight strength", "advanced push-up preparation"],
        "avoid_when": ["wrist pain", "elbow pain", "shoulder pain at close grip"],
        "progressions": ["cal_var_archer_push_up", "cal_var_one_arm_push_up"],
        "regressions": ["cal_ex_push_up", "incline close-grip push-up"],
        "pages": [28, 29],
    },
    {
        "id": "cal_ex_bodyweight_triceps_extension",
        "library": "primary",
        "name": "Bodyweight Triceps Extension",
        "aliases": ["Tricep Extension", "Plank Triceps Extension"],
        "base_exercise": "push_up",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["bodyweight", "mat"],
        "patterns": ["push", "elbow_extension", "brace"],
        "qualities": ["triceps_strength", "elbow_extension_strength"],
        "primary_muscles": ["triceps"],
        "secondary_muscles": ["chest", "shoulders", "trunk"],
        "summary": "Bodyweight elbow-extension drill starting from an elbow plank to build triceps strength for push-up progressions.",
        "coaching_cues": [
            "Align elbows under shoulders in an elbow plank.",
            "Press through forearms and palms to extend the elbows.",
            "Lower with control back to the elbow plank.",
            "Use a soft surface if elbows are uncomfortable.",
        ],
        "common_errors": ["Letting wrists or elbows become painful.", "Losing trunk tension.", "Rushing the descent."],
        "use_when": ["triceps strength accessory", "one-arm push-up preparation"],
        "avoid_when": ["elbow pain", "wrist pain", "shoulder pain in plank"],
        "progressions": ["cal_ex_diamond_push_up", "cal_var_one_arm_push_up"],
        "regressions": ["incline bodyweight triceps extension"],
        "pages": [30, 31],
    },
    {
        "id": "cal_ex_explosive_push_up",
        "library": "primary",
        "name": "Explosive Push-Up",
        "aliases": ["Plyometric Push-Up", "Clap Push-Up"],
        "base_exercise": "push_up",
        "category": "power",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["bodyweight"],
        "patterns": ["push", "plyometric", "brace"],
        "qualities": ["upper_body_power", "rate_of_force_development", "athletic_power"],
        "primary_muscles": ["chest", "triceps", "anterior_deltoids"],
        "secondary_muscles": ["trunk", "serratus_anterior"],
        "summary": "Plyometric push-up variant for upper-body power, speed, and neuromuscular efficiency.",
        "coaching_cues": [
            "Start from the bottom of a strong push-up.",
            "Drive the hands hard into the ground.",
            "Land under control and reset body tension.",
            "Start gradually before adding claps or height.",
        ],
        "common_errors": ["Landing stiff or uncontrolled.", "Using power work before owning strict push-ups.", "Turning it into fatigue conditioning."],
        "use_when": ["upper-body power block", "athletic push progression", "intermediate bodyweight training"],
        "avoid_when": ["wrist pain", "shoulder pain", "beginner lacking standard push-up control"],
        "progressions": ["higher explosive push-up", "clap push-up"],
        "regressions": ["fast concentric push-up", "incline explosive push-up"],
        "pages": [32, 33, 34, 35],
    },
    {
        "id": "cal_ex_banded_overhead_pull_apart",
        "library": "primary",
        "name": "Banded Overhead Pull-Apart",
        "aliases": ["Overhead Band Pull-Apart"],
        "base_exercise": "band_pull_apart",
        "category": "warmup",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["resistance_band"],
        "patterns": ["pull", "scapular_control", "overhead_mobility"],
        "qualities": ["shoulder_mobility", "scapular_stability", "pull_up_preparation"],
        "primary_muscles": ["upper_back", "rear_deltoids", "trapezius"],
        "secondary_muscles": ["rotator_cuff", "trunk"],
        "summary": "Band warm-up for shoulder mobility and scapular retraction/depression before pull-up work.",
        "coaching_cues": ["Hold the band overhead with straight arms.", "Keep ribs down and core engaged.", "Pull the band apart while keeping shoulders down and back."],
        "common_errors": ["Shrugging shoulders.", "Rib flare.", "Bending elbows to avoid shoulder motion."],
        "use_when": ["pull-up warm-up", "upper-back activation", "shoulder-prep drill"],
        "avoid_when": ["painful overhead range"],
        "progressions": ["narrower band grip", "slower tempo"],
        "regressions": ["lighter band", "lower arm angle"],
        "pages": [48, 49],
    },
    {
        "id": "cal_ex_banded_horizontal_pull_apart",
        "library": "primary",
        "name": "Banded Horizontal Pull-Apart",
        "aliases": ["Band Pull-Apart"],
        "base_exercise": "band_pull_apart",
        "category": "warmup",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["resistance_band"],
        "patterns": ["pull", "scapular_retraction"],
        "qualities": ["posture_awareness", "upper_back_activation", "pull_up_preparation"],
        "primary_muscles": ["rhomboids", "trapezius", "rear_deltoids"],
        "secondary_muscles": ["rotator_cuff"],
        "summary": "Band warm-up emphasizing retracted shoulders, open chest, and upper-back activation.",
        "coaching_cues": ["Hold the band at chest height.", "Pull apart without bending the elbows.", "Keep chest open and shoulders down."],
        "common_errors": ["Shrugging.", "Bending elbows too much.", "Arching the back."],
        "use_when": ["pull-up warm-up", "posture reset", "upper-back activation"],
        "avoid_when": ["shoulder pain with horizontal abduction"],
        "progressions": ["narrower grip", "stronger band"],
        "regressions": ["lighter band", "smaller range"],
        "pages": [50, 51],
    },
    {
        "id": "cal_ex_banded_pull_down",
        "library": "primary",
        "name": "Banded Pull-Down",
        "aliases": ["Resistance Band Pull-Down"],
        "base_exercise": "vertical_pull",
        "category": "warmup",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["resistance_band", "anchor", "dowel"],
        "patterns": ["vertical_pull", "scapular_depression", "brace"],
        "qualities": ["lat_activation", "pull_up_patterning", "shoulder_prep"],
        "primary_muscles": ["latissimus_dorsi", "upper_back"],
        "secondary_muscles": ["biceps", "trunk"],
        "summary": "Band-assisted vertical pulling drill that mimics pull-up motion without fatiguing the athlete.",
        "coaching_cues": ["Anchor the band high enough to keep tension.", "Pull toward the chest while squeezing shoulder blades.", "Keep trunk and lower body still."],
        "common_errors": ["Leaning back excessively.", "Losing band tension.", "Using momentum instead of lat engagement."],
        "use_when": ["pull-up warm-up", "lat activation", "vertical-pull patterning"],
        "avoid_when": ["unsafe anchor setup"],
        "progressions": ["stronger band", "slower eccentric"],
        "regressions": ["lighter band", "shorter range"],
        "pages": [52, 53],
    },
    {
        "id": "cal_ex_bent_over_barbell_row",
        "library": "primary",
        "name": "Bent-Over Barbell Row",
        "aliases": ["Barbell Row"],
        "base_exercise": "row",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["barbell", "plates"],
        "patterns": ["horizontal_pull", "hinge", "brace"],
        "qualities": ["pull_strength", "upper_back_strength", "pull_up_foundation"],
        "primary_muscles": ["latissimus_dorsi", "rhomboids", "upper_back"],
        "secondary_muscles": ["biceps", "trunk", "hamstrings"],
        "summary": "Horizontal pulling strength exercise used to build the back and arm strength needed for pull-up progression.",
        "coaching_cues": ["Hinge the hips and hold a stable torso.", "Pull shoulder blades back and down.", "Pull the bar toward the abdomen without jerking."],
        "common_errors": ["Standing too upright.", "Using momentum.", "Losing spinal position."],
        "use_when": ["pull-up strength base", "back strength accessory", "gym-supported calisthenics plan"],
        "avoid_when": ["low back pain during hinge", "no barbell access"],
        "progressions": ["heavier row", "slower tempo row"],
        "regressions": ["dumbbell row", "inverted row"],
        "pages": [56, 57, 58],
    },
    {
        "id": "cal_ex_passive_hang",
        "library": "primary",
        "name": "Passive Hang",
        "aliases": ["Dead Hang"],
        "base_exercise": "hang",
        "category": "grip",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["pull_up_bar"],
        "patterns": ["hang", "grip", "shoulder_mobility"],
        "qualities": ["grip_endurance", "shoulder_decompression", "pull_up_foundation"],
        "primary_muscles": ["forearms", "grip"],
        "secondary_muscles": ["shoulders", "upper_back"],
        "summary": "Foundational hang used to build grip endurance and comfort under the pull-up bar.",
        "coaching_cues": ["Grip slightly wider than shoulder width.", "Let arms fully extend.", "Relax the lower body.", "Let the shoulders open without forcing active pulling."],
        "common_errors": ["Actively pulling with the lats during passive hang.", "Using a bar too low for full extension.", "Losing grip suddenly without setup."],
        "use_when": ["pull-up foundation", "grip exposure", "shoulder opening"],
        "avoid_when": ["shoulder instability", "acute elbow/wrist pain"],
        "progressions": ["longer hang", "active hang", "scapula pull-up"],
        "regressions": ["feet-assisted hang"],
        "pages": [59, 60, 61],
    },
    {
        "id": "cal_ex_scapula_pull_up",
        "library": "primary",
        "name": "Scapula Pull-Up",
        "aliases": ["Scapular Pull-Up"],
        "base_exercise": "pull_up",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["pull_up_bar"],
        "patterns": ["vertical_pull", "scapular_depression"],
        "qualities": ["scapular_control", "lat_activation", "pull_up_foundation"],
        "primary_muscles": ["lower_trapezius", "latissimus_dorsi", "upper_back"],
        "secondary_muscles": ["grip", "trunk"],
        "summary": "Straight-arm pull-up drill teaching shoulder blade depression/retraction before elbow-driven pull-up work.",
        "coaching_cues": ["Keep arms straight.", "Pull shoulders down and back.", "Lift the trunk slightly toward the bar.", "Pause briefly at the top and lower with control."],
        "common_errors": ["Bending elbows.", "Shrugging toward ears.", "Swinging the body."],
        "use_when": ["pull-up warm-up", "scapular control drill", "beginner vertical-pull progression"],
        "avoid_when": ["shoulder pain during hanging"],
        "progressions": ["cal_ex_australian_pull_up", "cal_ex_band_assisted_pull_up"],
        "regressions": ["feet-assisted scapula pull-up"],
        "pages": [62, 63],
    },
    {
        "id": "cal_ex_australian_pull_up",
        "library": "primary",
        "name": "Australian Pull-Up",
        "aliases": ["Inverted Row", "Bodyweight Row"],
        "base_exercise": "row",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["low_bar", "rings", "smith_machine"],
        "patterns": ["horizontal_pull", "brace"],
        "qualities": ["back_strength", "pull_up_foundation", "bodyweight_strength"],
        "primary_muscles": ["latissimus_dorsi", "rhomboids", "biceps"],
        "secondary_muscles": ["trunk", "grip"],
        "summary": "Accessible bodyweight horizontal pull that develops back and arm strength before full pull-ups.",
        "coaching_cues": ["Use a waist-height bar.", "Keep body straight.", "Pull chest toward the bar.", "Control the descent until elbows extend."],
        "common_errors": ["Sagging hips.", "Short range of motion.", "Using too upright an angle when ready for more challenge."],
        "use_when": ["pull-up regression", "bodyweight pulling strength", "beginner back strength"],
        "avoid_when": ["no safe low bar or ring setup"],
        "progressions": ["lower bar angle", "feet elevated row", "cal_ex_band_assisted_pull_up"],
        "regressions": ["higher bar angle", "bent-knee inverted row"],
        "pages": [64, 65, 66, 67],
    },
    {
        "id": "cal_ex_negative_pull_up",
        "library": "primary",
        "name": "Negative Pull-Up",
        "aliases": ["Eccentric Pull-Up"],
        "base_exercise": "pull_up",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["pull_up_bar", "box"],
        "patterns": ["vertical_pull", "eccentric_control", "brace"],
        "qualities": ["eccentric_strength", "pull_up_strength", "grip_endurance"],
        "primary_muscles": ["latissimus_dorsi", "biceps", "upper_back"],
        "secondary_muscles": ["grip", "trunk"],
        "summary": "Eccentric pull-up variation that builds pulling strength by controlling the lowering phase from the top position.",
        "coaching_cues": ["Start at the top with chest near the bar.", "Lower slowly with a tight body.", "Step down and reset instead of jumping repeatedly.", "Keep legs together and avoid swinging."],
        "common_errors": ["Dropping too fast.", "Starting inconsistently from a jump.", "Swinging or losing trunk tension."],
        "use_when": ["bridge to first pull-up", "eccentric strength block"],
        "avoid_when": ["elbow pain", "shoulder pain during hanging", "grip unable to control descent"],
        "progressions": ["cal_ex_pull_up"],
        "regressions": ["cal_ex_band_assisted_pull_up", "cal_ex_australian_pull_up"],
        "pages": [68, 69],
    },
    {
        "id": "cal_ex_band_assisted_pull_up",
        "library": "primary",
        "name": "Band-Assisted Pull-Up",
        "aliases": ["Resistance Band Assisted Pull-Up"],
        "base_exercise": "pull_up",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["pull_up_bar", "resistance_band"],
        "patterns": ["vertical_pull", "brace"],
        "qualities": ["pull_up_patterning", "vertical_pull_strength"],
        "primary_muscles": ["latissimus_dorsi", "biceps", "upper_back"],
        "secondary_muscles": ["grip", "trunk"],
        "summary": "Assisted pull-up variation that reduces bodyweight load while preserving pull-up range and technique.",
        "coaching_cues": ["Secure the band to the bar.", "Keep hips and knees straight for steady assistance.", "Drive elbows down toward the hips.", "Keep the body line tight."],
        "common_errors": ["Using a band that provides too much bounce.", "Losing body line.", "Stopping short of full range."],
        "use_when": ["building pull-up reps", "learning vertical pull technique", "transition from rows to pull-ups"],
        "avoid_when": ["unsafe band setup", "band snaps or slips"],
        "progressions": ["thinner band", "cal_ex_negative_pull_up", "cal_ex_pull_up"],
        "regressions": ["stronger band", "cal_ex_australian_pull_up"],
        "pages": [70, 71],
    },
    {
        "id": "cal_ex_pull_up",
        "library": "primary",
        "name": "Pull-Up",
        "aliases": ["Strict Pull-Up"],
        "base_exercise": "pull_up",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["pull_up_bar"],
        "patterns": ["vertical_pull", "brace"],
        "qualities": ["upper_body_strength", "grip_strength", "pulling_power"],
        "primary_muscles": ["latissimus_dorsi", "biceps", "rhomboids"],
        "secondary_muscles": ["trunk", "grip", "lower_trapezius"],
        "summary": "Strict bodyweight vertical pull for upper-body strength, grip, control, and pulling capacity.",
        "coaching_cues": ["Start from a dead hang.", "Set the shoulders before pulling.", "Drive elbows down and keep the trunk tight.", "Lower under control to full extension."],
        "common_errors": ["Kipping unintentionally.", "Cutting range short.", "Losing shoulder control at the bottom."],
        "use_when": ["intermediate pulling strength", "bodyweight strength goal", "upper-body strength benchmark"],
        "avoid_when": ["shoulder or elbow pain under full bodyweight", "insufficient grip capacity"],
        "progressions": ["weighted pull-up", "higher rep pull-up sets"],
        "regressions": ["cal_ex_band_assisted_pull_up", "cal_ex_negative_pull_up"],
        "pages": [72, 73, 74, 75, 76, 77],
    },
    {
        "id": "cal_ex_bodyweight_squat",
        "library": "primary",
        "name": "Bodyweight Squat",
        "aliases": ["Air Squat"],
        "base_exercise": "squat",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["squat", "knee_dominant"],
        "qualities": ["lower_body_strength", "mobility", "movement_quality"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["hamstrings", "calves", "trunk"],
        "summary": "Foundational bilateral squat pattern for leg strength, mobility, and preparation for harder squat variations.",
        "coaching_cues": ["Set feet around shoulder width.", "Sit back and down while keeping a straight back.", "Track knees over toes.", "Drive up through hips and knees."],
        "common_errors": ["Knees collapsing inward.", "Rounding the back.", "Shifting too far onto toes."],
        "use_when": ["beginner lower-body strength", "squat movement assessment", "warm-up"],
        "avoid_when": ["painful knee range without modification"],
        "progressions": ["cal_ex_deep_squat", "cal_ex_narrow_stance_squat", "cal_ex_bulgarian_split_squat"],
        "regressions": ["box squat", "supported squat"],
        "pages": [80, 81, 82, 83],
    },
    {
        "id": "cal_ex_narrow_stance_squat",
        "library": "primary",
        "name": "Narrow-Stance Squat",
        "aliases": ["Close-Stance Squat"],
        "base_exercise": "squat",
        "category": "strength",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["squat", "balance"],
        "qualities": ["quad_strength", "balance", "single_leg_preparation"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["trunk", "calves"],
        "summary": "Close-stance squat that increases quadriceps and balance demand while preparing for single-leg patterns.",
        "coaching_cues": ["Bring feet closer gradually.", "Keep chest lifted and back straight.", "Use arms forward for balance.", "Let knees track naturally with the feet."],
        "common_errors": ["Forcing feet too close too soon.", "Losing balance.", "Collapsing knee position."],
        "use_when": ["pistol-squat preparation", "quad-biased bodyweight squat", "balance progression"],
        "avoid_when": ["knee pain with narrow stance"],
        "progressions": ["cal_ex_deep_squat", "cal_ex_bulgarian_split_squat"],
        "regressions": ["cal_ex_bodyweight_squat"],
        "pages": [84, 85],
    },
    {
        "id": "cal_ex_deep_squat",
        "library": "primary",
        "name": "Deep Squat",
        "aliases": ["Full Squat", "Ass-to-Grass Squat"],
        "base_exercise": "squat",
        "category": "mobility",
        "difficulty": "beginner",
        "default_user_level": "beginner",
        "equipment": ["bodyweight"],
        "patterns": ["squat", "mobility"],
        "qualities": ["hip_mobility", "ankle_mobility", "lower_body_strength"],
        "primary_muscles": ["quadriceps", "glutes", "hamstrings"],
        "secondary_muscles": ["calves", "trunk"],
        "summary": "Full-range squat that develops lower-body mobility and strength needed for advanced squat variations.",
        "coaching_cues": ["Use shoulder-width or slightly wider feet.", "Point toes comfortably outward.", "Keep weight mid-foot or slightly back.", "Descend below parallel only while maintaining control."],
        "common_errors": ["Rounding excessively.", "Heels lifting due to limited ankle mobility.", "Forcing depth through pain."],
        "use_when": ["mobility foundation", "pistol-squat preparation", "lower-body warm-up"],
        "avoid_when": ["painful deep knee flexion", "limited ankle mobility without regression"],
        "progressions": ["cal_ex_bulgarian_split_squat", "cal_ex_cossack_squat"],
        "regressions": ["supported deep squat", "cal_ex_bodyweight_squat"],
        "pages": [86, 87],
    },
    {
        "id": "cal_ex_bulgarian_split_squat",
        "library": "primary",
        "name": "Bulgarian Split Squat",
        "aliases": ["Rear-Foot-Elevated Split Squat"],
        "base_exercise": "split_squat",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["bodyweight", "box", "bench"],
        "patterns": ["lunge", "single_leg", "squat"],
        "qualities": ["unilateral_strength", "balance", "pistol_squat_preparation"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["hamstrings", "adductors", "trunk"],
        "summary": "Single-leg strength exercise that builds unilateral leg capacity and balance for pistol-squat progression.",
        "coaching_cues": ["Place the rear foot on a box or bench for support.", "Keep most weight on the front leg.", "Track the front knee with the foot.", "Use a slight torso lean if helpful."],
        "common_errors": ["Loading the rear foot too much.", "Front knee collapsing inward.", "Standing too close or too far from the box."],
        "use_when": ["unilateral strength block", "pistol-squat preparation", "sport lower-body support"],
        "avoid_when": ["front knee pain", "balance unsafe with rear-foot elevation"],
        "progressions": ["weighted Bulgarian split squat", "cal_ex_cossack_squat", "cal_var_box_pistol_squat"],
        "regressions": ["split squat", "supported split squat"],
        "pages": [88, 89, 90, 91],
    },
    {
        "id": "cal_ex_cossack_squat",
        "library": "primary",
        "name": "Cossack Squat",
        "aliases": ["Side-to-Side Squat", "Lateral Squat"],
        "base_exercise": "lateral_squat",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["bodyweight"],
        "patterns": ["lateral_lunge", "squat", "mobility"],
        "qualities": ["adductor_mobility", "unilateral_strength", "lateral_control"],
        "primary_muscles": ["quadriceps", "glutes", "adductors"],
        "secondary_muscles": ["hamstrings", "calves", "trunk"],
        "summary": "Lateral unilateral squat requiring strength, hamstring/adductor mobility, and control in side-to-side positions.",
        "coaching_cues": ["Stand wider than shoulders.", "Bend one leg while keeping the other leg straight.", "Keep the squatting foot flat.", "Use hands forward for balance."],
        "common_errors": ["Stance too narrow or too wide.", "Heel lifting on the bent leg.", "Collapsing through the trunk."],
        "use_when": ["lateral strength", "adductor mobility", "pistol-squat preparation", "field/court sport support"],
        "avoid_when": ["adductor or groin pain", "painful deep knee flexion"],
        "progressions": ["loaded cossack squat", "cal_var_pistol_squat"],
        "regressions": ["supported cossack squat", "lateral lunge"],
        "pages": [92, 93, 94],
    },
]


VARIATIONS: List[Dict[str, Any]] = [
    {
        "id": "cal_var_archer_push_up",
        "name": "Archer Push-Up",
        "aliases": ["Side-to-Side Push-Up"],
        "base_exercise": "cal_ex_push_up",
        "variation_type": "unilateral_progression",
        "category": "strength",
        "difficulty": "advanced",
        "default_user_level": "advanced",
        "equipment": ["bodyweight"],
        "patterns": ["push", "unilateral", "brace"],
        "qualities": ["unilateral_push_strength", "one_arm_push_up_preparation"],
        "primary_muscles": ["chest", "triceps", "anterior_deltoids"],
        "secondary_muscles": ["trunk", "serratus_anterior"],
        "summary": "Advanced push-up variation that shifts bodyweight toward one arm while the other arm assists from the side.",
        "coaching_cues": ["Start from a wide push-up position.", "Lower toward one arm while the other reaches out.", "Use wider feet for stability if needed.", "Control weight distribution between arms."],
        "common_errors": ["Dumping all weight suddenly onto one arm.", "Twisting shoulders.", "Feet too narrow for current control."],
        "use_when": ["one-arm push-up preparation", "advanced unilateral pushing"],
        "avoid_when": ["beginner", "shoulder pain", "wrist pain", "poor push-up control"],
        "progressions": ["cal_var_one_arm_push_up"],
        "regressions": ["cal_ex_wide_push_up", "cal_ex_push_up"],
        "pages": [36, 37, 38, 39],
    },
    {
        "id": "cal_var_one_arm_push_up",
        "name": "One-Arm Push-Up",
        "aliases": ["OAPU", "One-Arm Pushup"],
        "base_exercise": "cal_ex_push_up",
        "variation_type": "specialist_skill",
        "category": "strength",
        "difficulty": "advanced",
        "default_user_level": "advanced",
        "equipment": ["bodyweight"],
        "patterns": ["push", "unilateral", "anti_rotation"],
        "qualities": ["max_bodyweight_push_strength", "trunk_anti_rotation", "balance"],
        "primary_muscles": ["chest", "triceps", "anterior_deltoids"],
        "secondary_muscles": ["trunk", "glutes", "serratus_anterior"],
        "summary": "Advanced unilateral push-up skill requiring high pressing strength, trunk control, balance, and technical practice.",
        "coaching_cues": ["Spread legs for balance.", "Rest the free hand on the back thigh.", "Keep shoulder level even.", "Use wall/table/chair elevations before floor attempts if needed."],
        "common_errors": ["Twisting through the torso.", "Dropping one shoulder.", "Attempting floor version before enough progressive exposure."],
        "use_when": ["advanced calisthenics skill block", "specific one-arm push-up goal"],
        "avoid_when": ["beginner", "shoulder pain", "wrist pain", "poor strict push-up or archer push-up control"],
        "progressions": ["lower incline one-arm push-up", "more reps"],
        "regressions": ["cal_var_archer_push_up", "incline one-arm push-up"],
        "pages": [40, 41, 42, 43],
    },
    {
        "id": "cal_var_box_pistol_squat",
        "name": "Box Pistol Squat",
        "aliases": ["Chair Pistol Squat"],
        "base_exercise": "cal_var_pistol_squat",
        "variation_type": "regression",
        "category": "strength",
        "difficulty": "intermediate",
        "default_user_level": "intermediate",
        "equipment": ["box", "chair", "bodyweight"],
        "patterns": ["single_leg_squat", "balance"],
        "qualities": ["single_leg_strength", "pistol_squat_preparation", "range_control"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["hamstrings", "trunk", "hip_flexors"],
        "summary": "Pistol-squat regression that uses a box or chair to limit range while preserving single-leg tension.",
        "coaching_cues": ["Stand in front of a box.", "Extend the free leg forward.", "Lower under control without collapsing onto the box.", "Stand by driving through the working heel."],
        "common_errors": ["Relaxing completely onto the box.", "Knee collapsing inward.", "Using a box height too low too soon."],
        "use_when": ["pistol squat progression", "single-leg strength with controlled range"],
        "avoid_when": ["knee pain during single-leg squat"],
        "progressions": ["lower box height", "cal_var_eccentric_pistol_squat", "cal_var_pistol_squat"],
        "regressions": ["cal_ex_bulgarian_split_squat"],
        "pages": [95, 96, 97],
    },
    {
        "id": "cal_var_eccentric_pistol_squat",
        "name": "Eccentric Pistol Squat",
        "aliases": ["Negative Pistol Squat"],
        "base_exercise": "cal_var_pistol_squat",
        "variation_type": "eccentric_progression",
        "category": "strength",
        "difficulty": "advanced",
        "default_user_level": "advanced",
        "equipment": ["bodyweight", "support_optional"],
        "patterns": ["single_leg_squat", "eccentric_control", "balance"],
        "qualities": ["single_leg_eccentric_strength", "knee_control", "balance"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["hamstrings", "calves", "trunk"],
        "summary": "Pistol-squat progression emphasizing a slow, controlled descent before using assistance or both feet to stand.",
        "coaching_cues": ["Stand on one leg.", "Extend the free leg and arms for balance.", "Lower over 3-4 seconds.", "Keep the knee in line with the toes."],
        "common_errors": ["Dropping into the bottom.", "Letting the knee cave inward.", "Trying to stand unassisted before ready."],
        "use_when": ["advanced pistol squat preparation", "single-leg eccentric block"],
        "avoid_when": ["knee pain", "poor single-leg control", "beginner"],
        "progressions": ["cal_var_pistol_squat"],
        "regressions": ["cal_var_box_pistol_squat", "supported eccentric pistol squat"],
        "pages": [95, 96, 97],
    },
    {
        "id": "cal_var_pistol_squat",
        "name": "Pistol Squat",
        "aliases": ["Single-Leg Squat"],
        "base_exercise": "cal_ex_bodyweight_squat",
        "variation_type": "specialist_skill",
        "category": "strength",
        "difficulty": "advanced",
        "default_user_level": "advanced",
        "equipment": ["bodyweight"],
        "patterns": ["single_leg_squat", "balance", "mobility"],
        "qualities": ["single_leg_strength", "balance", "mobility", "body_control"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["hamstrings", "calves", "trunk", "hip_flexors"],
        "summary": "Advanced single-leg squat skill requiring strength, balance, mobility, coordination, and unilateral control.",
        "coaching_cues": ["Stand on one leg and extend the other forward.", "Reach arms forward for balance.", "Descend with control while keeping the knee aligned.", "Stand without bouncing or collapsing."],
        "common_errors": ["Knee valgus.", "Dropping into the bottom.", "Rounding excessively or losing balance."],
        "use_when": ["advanced calisthenics leg strength", "single-leg skill goal"],
        "avoid_when": ["beginner", "knee pain", "poor single-leg control", "limited ankle/hip mobility"],
        "progressions": ["weighted pistol squat", "higher reps"],
        "regressions": ["cal_var_box_pistol_squat", "cal_var_eccentric_pistol_squat", "cal_ex_cossack_squat"],
        "pages": [98, 99, 100, 101],
    },
]


PROGRESSION_EDGES = [
    ("cal_ex_plank_hold", "cal_ex_scapula_push_up", "progression", "beginner"),
    ("cal_ex_scapula_push_up", "cal_ex_negative_push_up", "progression", "beginner"),
    ("cal_ex_negative_push_up", "cal_ex_push_up", "progression", "beginner"),
    ("cal_ex_push_up", "cal_ex_diamond_push_up", "progression", "intermediate"),
    ("cal_ex_push_up", "cal_ex_wide_push_up", "progression", "intermediate"),
    ("cal_ex_push_up", "cal_ex_explosive_push_up", "progression", "intermediate"),
    ("cal_ex_wide_push_up", "cal_var_archer_push_up", "progression", "advanced"),
    ("cal_var_archer_push_up", "cal_var_one_arm_push_up", "progression", "advanced"),
    ("cal_ex_banded_overhead_pull_apart", "cal_ex_scapula_pull_up", "preparation", "beginner"),
    ("cal_ex_banded_horizontal_pull_apart", "cal_ex_scapula_pull_up", "preparation", "beginner"),
    ("cal_ex_banded_pull_down", "cal_ex_band_assisted_pull_up", "preparation", "beginner"),
    ("cal_ex_passive_hang", "cal_ex_scapula_pull_up", "progression", "beginner"),
    ("cal_ex_bent_over_barbell_row", "cal_ex_australian_pull_up", "progression", "beginner"),
    ("cal_ex_australian_pull_up", "cal_ex_band_assisted_pull_up", "progression", "beginner"),
    ("cal_ex_band_assisted_pull_up", "cal_ex_negative_pull_up", "progression", "intermediate"),
    ("cal_ex_negative_pull_up", "cal_ex_pull_up", "progression", "intermediate"),
    ("cal_ex_bodyweight_squat", "cal_ex_narrow_stance_squat", "progression", "beginner"),
    ("cal_ex_bodyweight_squat", "cal_ex_deep_squat", "progression", "beginner"),
    ("cal_ex_deep_squat", "cal_ex_bulgarian_split_squat", "progression", "intermediate"),
    ("cal_ex_bulgarian_split_squat", "cal_ex_cossack_squat", "progression", "intermediate"),
    ("cal_ex_cossack_squat", "cal_var_box_pistol_squat", "progression", "advanced"),
    ("cal_var_box_pistol_squat", "cal_var_eccentric_pistol_squat", "progression", "advanced"),
    ("cal_var_eccentric_pistol_squat", "cal_var_pistol_squat", "progression", "advanced"),
]


ROUTINES: List[Dict[str, Any]] = [
    {
        "id": "cal_tpl_push_level_1",
        "category": "calisthenics_push",
        "level": "level_1",
        "sport_tags": ["bodyweight", "calisthenics", "general_fitness"],
        "equipment_required": ["bodyweight"],
        "title": "Push-Up Routine Level 1",
        "description": "Entry-level push routine using eccentric push-ups, scapular control, and plank holds.",
        "progression_goal": "Move to Level 2 after completing the negative push-up target with control.",
        "sessions_per_week": "2-3",
        "rest_guidance": "At least 48 hours between repeat sessions.",
        "exercises": [
            {"exercise_id": "cal_ex_negative_push_up", "sets": 3, "reps": "8", "tempo": "4 sec eccentric", "rest": "120 sec"},
            {"exercise_id": "cal_ex_scapula_push_up", "sets": 4, "reps": "8", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_plank_hold", "sets": 4, "duration": "60 sec", "rest": "120 sec"},
        ],
        "source_pages": [106, 107],
    },
    {
        "id": "cal_tpl_push_level_2",
        "category": "calisthenics_push",
        "level": "level_2",
        "sport_tags": ["bodyweight", "calisthenics"],
        "equipment_required": ["bodyweight"],
        "title": "Push-Up Routine Level 2",
        "description": "Builds standard push-up volume while retaining eccentric and scapular foundation work.",
        "progression_goal": "Move to Level 3 after performing 12 standard push-ups for the target sets.",
        "sessions_per_week": "2-3",
        "rest_guidance": "At least 48 hours between repeat sessions.",
        "exercises": [
            {"exercise_id": "cal_ex_push_up", "sets": 3, "reps": "12", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_negative_push_up", "sets": 3, "reps": "8", "tempo": "4 sec eccentric", "rest": "120 sec"},
            {"type": "superset", "exercises": [
                {"exercise_id": "cal_ex_scapula_push_up", "reps": "8", "tempo": "2010"},
                {"exercise_id": "cal_ex_plank_hold", "duration": "60 sec"},
            ], "sets": 4, "rest": "180 sec"},
        ],
        "source_pages": [106, 107],
    },
    {
        "id": "cal_tpl_push_level_3",
        "category": "calisthenics_push",
        "level": "level_3",
        "title": "Push-Up Routine Level 3",
        "description": "Intermediate push routine combining triceps, close-grip, wide-grip, and standard/eccentric work.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight"],
        "exercises": [
            {"exercise_id": "cal_ex_bodyweight_triceps_extension", "sets": 3, "reps": "8", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_diamond_push_up", "sets": 3, "reps": "15", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_wide_push_up", "sets": 3, "reps": "6", "tempo": "2010", "rest": "90 sec"},
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_push_up", "reps": "8", "tempo": "2010"},
                {"exercise_id": "cal_ex_negative_push_up", "reps": "4", "tempo": "4 sec eccentric"},
            ]},
        ],
        "source_pages": [106, 107],
    },
    {
        "id": "cal_tpl_push_level_4",
        "category": "calisthenics_push",
        "level": "level_4",
        "title": "Push-Up Routine Level 4",
        "description": "Advanced preparation for one-arm push-ups using archer, explosive, close-grip, and plank volume.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight"],
        "exercises": [
            {"exercise_id": "cal_var_archer_push_up", "sets": 3, "reps": "2 each arm", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_explosive_push_up", "sets": 2, "reps": "6", "tempo": "1010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_diamond_push_up", "sets": 2, "reps": "10", "tempo": "2010", "rest": "120 sec"},
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_push_up", "reps": "10", "tempo": "2010"},
                {"exercise_id": "cal_ex_plank_hold", "duration": "60 sec"},
            ]},
        ],
        "source_pages": [106, 107],
    },
    {
        "id": "cal_tpl_push_level_5",
        "category": "calisthenics_push",
        "level": "level_5",
        "title": "Push-Up Routine Level 5",
        "description": "One-arm push-up skill routine with archer and standard push-up volume to support the main skill.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight"],
        "exercises": [
            {"exercise_id": "cal_var_one_arm_push_up", "sets": 3, "reps": "1 each arm", "tempo": "2010", "rest": "120 sec"},
            {"type": "superset", "sets": 4, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_var_archer_push_up", "reps": "4 each arm", "tempo": "2010"},
                {"exercise_id": "cal_ex_diamond_push_up", "reps": "5", "tempo": "2010"},
            ]},
            {"exercise_id": "cal_ex_push_up", "sets": 5, "reps": "6", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_wide_push_up", "sets": 4, "reps": "5", "tempo": "2010", "rest": "180 sec"},
        ],
        "source_pages": [106, 107],
    },
    {
        "id": "cal_tpl_pull_level_1",
        "category": "calisthenics_pull",
        "level": "level_1",
        "title": "Pull-Up Routine Level 1",
        "description": "Beginner pulling routine pairing barbell rows and passive hangs.",
        "progression_goal": "Progress when row load and passive-hang duration meet target quality.",
        "sessions_per_week": "2-3",
        "equipment_required": ["barbell", "pull_up_bar"],
        "exercises": [
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_bent_over_barbell_row", "reps": "15", "tempo": "2010"},
                {"exercise_id": "cal_ex_passive_hang", "duration": "60 sec"},
            ]},
        ],
        "source_pages": [108, 109],
    },
    {
        "id": "cal_tpl_pull_level_2",
        "category": "calisthenics_pull",
        "level": "level_2",
        "title": "Pull-Up Routine Level 2",
        "description": "Horizontal pull and scapular-control routine for the next pull-up foundation step.",
        "sessions_per_week": "2-3",
        "equipment_required": ["low_bar", "pull_up_bar"],
        "exercises": [
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_australian_pull_up", "reps": "12", "tempo": "2010"},
                {"exercise_id": "cal_ex_scapula_pull_up", "reps": "12", "tempo": "2010"},
            ]},
        ],
        "source_pages": [108, 109],
    },
    {
        "id": "cal_tpl_pull_level_3",
        "category": "calisthenics_pull",
        "level": "level_3",
        "title": "Pull-Up Routine Level 3",
        "description": "Assisted vertical pulling plus horizontal/scapular pulling volume.",
        "sessions_per_week": "2-3",
        "equipment_required": ["pull_up_bar", "resistance_band", "low_bar"],
        "exercises": [
            {"exercise_id": "cal_ex_band_assisted_pull_up", "sets": 3, "reps": "6", "tempo": "2010", "rest": "180 sec"},
            {"type": "superset", "sets": 4, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_australian_pull_up", "reps": "12", "tempo": "2010"},
                {"exercise_id": "cal_ex_scapula_pull_up", "reps": "12", "tempo": "2010"},
            ]},
        ],
        "source_pages": [108, 109],
    },
    {
        "id": "cal_tpl_pull_level_4",
        "category": "calisthenics_pull",
        "level": "level_4",
        "title": "Pull-Up Routine Level 4",
        "description": "Pre-first-pull-up routine using controlled negatives, assisted pull-ups, rows, scapular work, and hangs.",
        "sessions_per_week": "2-3",
        "equipment_required": ["pull_up_bar", "resistance_band", "low_bar"],
        "exercises": [
            {"exercise_id": "cal_ex_negative_pull_up", "sets": 5, "reps": "1", "tempo": "10 sec eccentric", "rest": "60 sec"},
            {"exercise_id": "cal_ex_band_assisted_pull_up", "sets": 3, "reps": "6", "tempo": "2010", "rest": "180 sec"},
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_australian_pull_up", "reps": "8", "tempo": "2010"},
                {"exercise_id": "cal_ex_scapula_pull_up", "reps": "5", "tempo": "2010"},
                {"exercise_id": "cal_ex_passive_hang", "duration": "30 sec"},
            ]},
        ],
        "source_pages": [108, 109],
    },
    {
        "id": "cal_tpl_pull_level_5",
        "category": "calisthenics_pull",
        "level": "level_5",
        "title": "Pull-Up Routine Level 5",
        "description": "Pull-up routine for building reps after achieving strict pull-ups.",
        "progression_goal": "After 3x3 pull-ups, add reps gradually, use thinner bands, or change row angle.",
        "sessions_per_week": "2-3",
        "equipment_required": ["pull_up_bar", "resistance_band", "low_bar"],
        "exercises": [
            {"exercise_id": "cal_ex_pull_up", "sets": 3, "reps": "3", "tempo": "2010", "rest": "180 sec"},
            {"exercise_id": "cal_ex_band_assisted_pull_up", "sets": 3, "reps": "10", "tempo": "2010", "rest": "180 sec"},
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_australian_pull_up", "reps": "8", "tempo": "2010"},
                {"exercise_id": "cal_ex_scapula_pull_up", "reps": "5", "tempo": "2010"},
                {"exercise_id": "cal_ex_passive_hang", "duration": "30 sec"},
            ]},
        ],
        "source_pages": [108, 109],
    },
    {
        "id": "cal_tpl_squat_level_1",
        "category": "calisthenics_squat",
        "level": "level_1",
        "title": "Squat Routine Level 1",
        "description": "Beginner squat routine building bilateral squat range and stance control.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight"],
        "exercises": [
            {"exercise_id": "cal_ex_deep_squat", "sets": 3, "reps": "12", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_narrow_stance_squat", "sets": 3, "reps": "12", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_bodyweight_squat", "sets": 3, "reps": "15", "tempo": "2010", "rest": "120 sec"},
        ],
        "source_pages": [110, 111],
    },
    {
        "id": "cal_tpl_squat_level_2",
        "category": "calisthenics_squat",
        "level": "level_2",
        "title": "Squat Routine Level 2",
        "description": "Introduces Bulgarian split squats while maintaining narrow and deep squat volume.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight", "box"],
        "exercises": [
            {"exercise_id": "cal_ex_bulgarian_split_squat", "sets": 3, "reps": "6 each leg", "tempo": "3010", "rest": "180 sec"},
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_narrow_stance_squat", "reps": "10", "tempo": "2010"},
                {"exercise_id": "cal_ex_deep_squat", "reps": "10", "tempo": "3010"},
            ]},
        ],
        "source_pages": [110, 111],
    },
    {
        "id": "cal_tpl_squat_level_3",
        "category": "calisthenics_squat",
        "level": "level_3",
        "title": "Squat Routine Level 3",
        "description": "Adds cossack squats and higher unilateral strength volume before pistol variants.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight", "box"],
        "exercises": [
            {"exercise_id": "cal_ex_cossack_squat", "sets": 3, "reps": "6 each leg", "tempo": "2010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_bulgarian_split_squat", "sets": 3, "reps": "8 each leg", "tempo": "2010", "rest": "120 sec"},
            {"type": "superset", "sets": 3, "rest": "180 sec", "exercises": [
                {"exercise_id": "cal_ex_narrow_stance_squat", "reps": "8", "tempo": "2010"},
                {"exercise_id": "cal_ex_deep_squat", "reps": "8", "tempo": "3010"},
            ]},
        ],
        "source_pages": [110, 111],
    },
    {
        "id": "cal_tpl_squat_level_4",
        "category": "calisthenics_squat",
        "level": "level_4",
        "title": "Squat Routine Level 4",
        "description": "Pistol-squat variant level with cossack, split squat, and deep squat support work.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight", "box"],
        "exercises": [
            {"exercise_id": "cal_var_box_pistol_squat", "sets": 3, "reps": "10 each leg", "tempo": "3010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_cossack_squat", "sets": 3, "reps": "8 each leg", "tempo": "2010", "rest": "100 sec"},
            {"type": "superset", "sets": 3, "rest": "100 sec", "exercises": [
                {"exercise_id": "cal_ex_bulgarian_split_squat", "reps": "10 each leg", "tempo": "2010"},
                {"exercise_id": "cal_ex_deep_squat", "reps": "12", "tempo": "3010"},
            ]},
        ],
        "source_pages": [110, 111],
    },
    {
        "id": "cal_tpl_squat_level_5",
        "category": "calisthenics_squat",
        "level": "level_5",
        "title": "Squat Routine Level 5",
        "description": "Pistol-squat skill routine with easier variants and unilateral support work.",
        "progression_goal": "After completing Level 5, gradually build pistol squats toward 8 reps.",
        "sessions_per_week": "2-3",
        "equipment_required": ["bodyweight", "box"],
        "exercises": [
            {"exercise_id": "cal_var_pistol_squat", "sets": 3, "reps": "3 each leg", "tempo": "2020", "rest": "120 sec"},
            {"exercise_id": "cal_var_box_pistol_squat", "sets": 2, "reps": "6 each leg", "tempo": "3010", "rest": "120 sec"},
            {"exercise_id": "cal_ex_cossack_squat", "sets": 3, "reps": "8 each leg", "tempo": "2010", "rest": "120 sec"},
            {"type": "superset", "sets": 3, "rest": "120 sec", "exercises": [
                {"exercise_id": "cal_ex_bulgarian_split_squat", "reps": "10 each leg", "tempo": "2010"},
                {"exercise_id": "cal_ex_deep_squat", "reps": "10", "tempo": "3010"},
            ]},
        ],
        "source_pages": [110, 111],
    },
]


PROGRAMMING_RULES: List[Dict[str, Any]] = [
    {
        "id": "cal_rule_train_skill_2_3x_week",
        "title": "Train Skill Routines Two To Three Times Weekly",
        "rule_type": "frequency",
        "applies_to": ["calisthenics", "bodyweight", "skill_progression"],
        "topics": ["frequency", "recovery", "progression"],
        "summary": "Skill routines should usually be repeated two to three times per week with at least 48 hours before repeating the same routine.",
        "rule_text": "Use two to three weekly exposures for a selected calisthenics routine and keep at least 48 hours between repeat exposures.",
        "app_usage": "Use for beginner/intermediate bodyweight plans and calisthenics skill blocks.",
        "source_pages": [103, 112],
    },
    {
        "id": "cal_rule_do_not_skip_levels",
        "title": "Do Not Skip Calisthenics Progression Levels",
        "rule_type": "progression",
        "applies_to": ["calisthenics", "bodyweight", "beginner"],
        "topics": ["progression", "skill_learning", "safety"],
        "summary": "The playbook uses five progressive levels and advises gradual progression instead of jumping to harder skill work too early.",
        "rule_text": "Progress from level to level only after the stated quality/repetition targets are met; do not skip levels unless the athlete already demonstrates the required control.",
        "app_usage": "Use to block one-arm push-ups, full pull-ups, and pistol squats when prerequisites are missing.",
        "source_pages": [103, 104],
    },
    {
        "id": "cal_rule_hardest_exercise_first",
        "title": "Place Hardest Exercise First",
        "rule_type": "session_order",
        "applies_to": ["calisthenics", "strength", "skill_progression"],
        "topics": ["exercise_order", "skill_quality", "fatigue_management"],
        "summary": "Each level starts with the hardest exercise and finishes with easier progressions to preserve skill quality while still building volume.",
        "rule_text": "Place the highest-skill or hardest strength movement early in the session, then use easier variations for additional volume.",
        "app_usage": "Use when arranging bodyweight skill sessions and push/pull/squat progressions.",
        "source_pages": [104],
    },
    {
        "id": "cal_rule_track_modifications",
        "title": "Track Sets Reps Tempo And Rest Changes",
        "rule_type": "tracking",
        "applies_to": ["all_sports", "calisthenics", "bodyweight"],
        "topics": ["tracking", "consistency", "progression"],
        "summary": "Changes to sets, reps, tempo, speed, and rest should be recorded so progress can be measured consistently.",
        "rule_text": "If the user changes prescribed sets, reps, tempo, or rest, record the modification and keep future comparisons consistent.",
        "app_usage": "Use for workout logging and athlete_state updates.",
        "source_pages": [103, 105],
    },
    {
        "id": "cal_rule_weekly_organization_options",
        "title": "Use Stacked Single-Routine Or Triplet Organization",
        "rule_type": "weekly_structure",
        "applies_to": ["calisthenics", "bodyweight", "general_fitness"],
        "topics": ["weekly_schedule", "session_density", "time_efficiency"],
        "summary": "The playbook gives three weekly structures: stacked full routine, one routine per day, or triplets that pair push, pull, and squat exercises for efficiency.",
        "rule_text": "Choose full stacked sessions for maximum rest and longer sessions; choose one-routine days for short focused sessions; choose triplets for 30-45 minute time-efficient full-body sessions.",
        "app_usage": "Use to adapt bodyweight plans to available session duration.",
        "source_pages": [112, 113],
    },
]


def _page_text(pages: Dict[int, Dict[str, Any]], page_numbers: Sequence[int]) -> str:
    return "\n".join((pages.get(page, {}) or {}).get("text", "") for page in page_numbers).strip()


def _page_hash(pages: Dict[int, Dict[str, Any]], page_numbers: Sequence[int]) -> str:
    return _hash_text(_page_text(pages, page_numbers))


def _exercise_source_section_id(record: Dict[str, Any]) -> str:
    return f"cal_section_ex_{_slug(record['name'])}"


def _exercise_doc(record: Dict[str, Any], pages: Dict[int, Dict[str, Any]], *, collection: str) -> Dict[str, Any]:
    page_numbers = record["pages"]
    section_id = _exercise_source_section_id(record)
    source_ref = _source_ref(section_id, page_numbers, record["name"])
    base = {
        "id": record["id"],
        "name": record["name"],
        "aliases": record.get("aliases") or [],
        "base_exercise": record.get("base_exercise"),
        "category": record.get("category"),
        "difficulty": record.get("difficulty"),
        "default_user_level": record.get("default_user_level"),
        "technical_complexity": record.get("difficulty"),
        "mobility_requirement": "moderate" if "mobility" in record.get("qualities", []) else "low",
        "stability_requirement": "high" if "single_leg" in record.get("patterns", []) or "unilateral" in record.get("patterns", []) else "moderate",
        "impact_level": "moderate" if "plyometric" in record.get("patterns", []) else "low",
        "load_scalability": "moderate",
        "coaching_requirement": "moderate" if record.get("difficulty") != "beginner" else "low",
        "equipment": record.get("equipment") or [],
        "patterns": record.get("patterns") or [],
        "qualities": record.get("qualities") or [],
        "primary_muscles": record.get("primary_muscles") or [],
        "secondary_muscles": record.get("secondary_muscles") or [],
        "summary": record.get("summary"),
        "coaching_cues": record.get("coaching_cues") or [],
        "common_errors": record.get("common_errors") or [],
        "use_when": record.get("use_when") or [],
        "avoid_when": record.get("avoid_when") or [],
        "progressions": record.get("progressions") or [],
        "regressions": record.get("regressions") or [],
        "source_book_id": SOURCE_BOOK_ID,
        "source_refs": [source_ref],
        "source_text_hash": _page_hash(pages, page_numbers),
        "expert_validation_status": "pending",
        "ingestion_method": INGESTION_METHOD,
        "version": "v1.0.0",
    }
    if collection == "variation":
        base.update({
            "variation_type": record.get("variation_type"),
            "tier": "specialist_variation" if record.get("difficulty") == "advanced" else "progression_variation",
        })
    return base


def _raw_exercise_doc(record: Dict[str, Any], pages: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    page_numbers = record["pages"]
    return {
        "id": f"{record['id']}_raw",
        "name": record["name"],
        "aliases": record.get("aliases") or [],
        "definition": record.get("summary"),
        "exercise_family": record.get("base_exercise"),
        "exercise_type": record.get("category"),
        "category": record.get("category"),
        "difficulty": record.get("difficulty"),
        "equipment_required": record.get("equipment") or [],
        "movement_patterns": record.get("patterns") or [],
        "training_qualities": record.get("qualities") or [],
        "primary_muscles": record.get("primary_muscles") or [],
        "secondary_muscles": record.get("secondary_muscles") or [],
        "coaching_cues": record.get("coaching_cues") or [],
        "common_errors": record.get("common_errors") or [],
        "contraindications": record.get("avoid_when") or [],
        "injury_flags": record.get("avoid_when") or [],
        "progressions": record.get("progressions") or [],
        "regressions": record.get("regressions") or [],
        "sport_tags": ["bodyweight", "calisthenics", "general_fitness"],
        "summary": record.get("summary"),
        "source_book_id": SOURCE_BOOK_ID,
        "source_refs": [_source_ref(_exercise_source_section_id(record), page_numbers, record["name"])],
        "source_text_hash": _page_hash(pages, page_numbers),
        "expert_validation_status": "pending",
        "ingestion_method": INGESTION_METHOD,
        "version": "v1.0.0",
    }


def _source_sections(pages: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    now = datetime.utcnow()
    for page_number in sorted(pages):
        text = pages[page_number].get("text", "")
        docs.append({
            "id": f"cal_page_{page_number:03d}",
            "source_book_id": SOURCE_BOOK_ID,
            "section_order": page_number,
            "section_title": _first_heading(text),
            "page_start": page_number,
            "page_end": page_number,
            "domain": "calisthenics",
            "topics": ["page_ocr_trace"],
            "summary": f"Page-level OCR trace for {_first_heading(text)}.",
            "source_text_hash": pages[page_number].get("text_hash") or _hash_text(text),
            "text_char_count": len(text),
            "created_at": now,
            "updated_at": now,
        })
    order = 2000
    for section in SECTIONS:
        order += 1
        docs.append({
            "id": section["id"],
            "source_book_id": SOURCE_BOOK_ID,
            "section_order": order,
            "section_title": section["title"],
            "page_start": min(section["pages"]),
            "page_end": max(section["pages"]),
            "domain": "calisthenics",
            "topics": section["topics"],
            "summary": section["summary"],
            "source_text_hash": _page_hash(pages, section["pages"]),
            "text_char_count": len(_page_text(pages, section["pages"])),
            "created_at": now,
            "updated_at": now,
        })
    for record in [*EXERCISES, *VARIATIONS]:
        order += 1
        docs.append({
            "id": _exercise_source_section_id(record),
            "source_book_id": SOURCE_BOOK_ID,
            "section_order": order,
            "section_title": record["name"],
            "page_start": min(record["pages"]),
            "page_end": max(record["pages"]),
            "domain": "calisthenics",
            "topics": list(set([record.get("category"), record.get("base_exercise"), *(record.get("patterns") or []), *(record.get("qualities") or [])])),
            "summary": record["summary"],
            "source_text_hash": _page_hash(pages, record["pages"]),
            "text_char_count": len(_page_text(pages, record["pages"])),
            "created_at": now,
            "updated_at": now,
        })
    return docs


def _merge_list(existing: Any, incoming: Any) -> List[Any]:
    items: List[Any] = []
    for value in [existing, incoming]:
        if not value:
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item not in items:
                items.append(item)
    return items


def _merge_source_backed_doc(existing: Dict[str, Any], incoming: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    merged = dict(existing)
    incoming_source = incoming.get("source_book_id")
    existing_source = existing.get("source_book_id")

    for key, value in incoming.items():
        if key in {"_id", "id", "created_at"}:
            continue
        if key in {
            "aliases",
            "equipment",
            "equipment_required",
            "patterns",
            "movement_patterns",
            "qualities",
            "training_qualities",
            "primary_muscles",
            "secondary_muscles",
            "coaching_cues",
            "common_errors",
            "use_when",
            "avoid_when",
            "progressions",
            "regressions",
            "source_refs",
            "sport_tags",
            "contraindications",
            "injury_flags",
        }:
            merged[key] = _merge_list(existing.get(key), value)
        elif value not in (None, "", [], {}) and existing.get(key) in (None, "", [], {}):
            merged[key] = value

    if incoming.get("summary"):
        summaries = merged.get("source_summaries") or []
        summary_record = {
            "source_book_id": incoming_source,
            "summary": incoming.get("summary"),
        }
        if summary_record not in summaries:
            summaries.append(summary_record)
        merged["source_summaries"] = summaries
        if incoming_source == SOURCE_BOOK_ID:
            merged["summary"] = incoming["summary"]

    ref_source_ids = [
        ref.get("source_book_id")
        for ref in (merged.get("source_refs") or [])
        if isinstance(ref, dict) and ref.get("source_book_id")
    ]
    source_ids = _merge_list(merged.get("source_book_ids"), [existing_source, incoming_source, *ref_source_ids])
    merged["source_book_ids"] = [source_id for source_id in source_ids if source_id]
    if not merged.get("source_book_id"):
        merged["source_book_id"] = incoming_source

    alias_ids = _merge_list(merged.get("alternate_ids"), incoming.get("id"))
    merged["alternate_ids"] = [alias_id for alias_id in alias_ids if alias_id and alias_id != merged.get("id")]
    merged["updated_at"] = now
    return merged


async def _upsert_many(db: Any, collection_name: str, docs: Iterable[Dict[str, Any]]) -> int:
    now = datetime.utcnow()
    count = 0
    collection = db[collection_name]
    for doc in docs:
        doc = {**doc, "updated_at": now}
        doc.setdefault("created_at", now)
        existing = await collection.find_one({"id": doc["id"]})
        if not existing and doc.get("name"):
            existing = await collection.find_one({"name": doc["name"]})
        if existing:
            merged = _merge_source_backed_doc(existing, doc, now)
            await collection.replace_one({"id": existing["id"]}, merged)
        else:
            await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
        count += 1
    return count


def _canonical_id(value: str, id_aliases: Optional[Dict[str, str]] = None) -> str:
    return (id_aliases or {}).get(value, value)


def _remap_exercise_ids(value: Any, id_aliases: Dict[str, str]) -> Any:
    if isinstance(value, list):
        return [_remap_exercise_ids(item, id_aliases) for item in value]
    if isinstance(value, dict):
        remapped = {}
        for key, item in value.items():
            if key == "exercise_id" and isinstance(item, str):
                remapped[key] = _canonical_id(item, id_aliases)
            else:
                remapped[key] = _remap_exercise_ids(item, id_aliases)
        return remapped
    return value


async def _canonical_id_aliases(db: Any) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for collection_name, records in [
        ("primary_exercise_library", EXERCISES),
        ("exercise_variation_library", VARIATIONS),
    ]:
        collection = db[collection_name]
        for record in records:
            existing = await collection.find_one({"name": record["name"]}, {"id": 1})
            if existing and existing.get("id") and existing["id"] != record["id"]:
                aliases[record["id"]] = existing["id"]
    return aliases


def _progression_docs(id_aliases: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    docs = []
    now = datetime.utcnow()
    name_by_id = {record["id"]: record["name"] for record in [*EXERCISES, *VARIATIONS]}
    for from_id, to_id, direction, level in PROGRESSION_EDGES:
        canonical_from_id = _canonical_id(from_id, id_aliases)
        canonical_to_id = _canonical_id(to_id, id_aliases)
        docs.append({
            "id": f"cal_prog_{_slug(canonical_from_id)}_to_{_slug(canonical_to_id)}",
            "base_exercise": name_by_id.get(from_id, from_id),
            "from_exercise_id": canonical_from_id,
            "from_exercise_name": name_by_id.get(from_id),
            "to_exercise_id": canonical_to_id,
            "to_exercise_name": name_by_id.get(to_id),
            "direction": direction,
            "min_user_level": level,
            "source_book_id": SOURCE_BOOK_ID,
            "source_refs": [_source_ref("cal_section_training_routine", [103, 104, 106, 108, 110], "Calisthenics Progression System")],
            "created_at": now,
            "updated_at": now,
        })
    return docs


def _routine_docs(id_aliases: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    docs = []
    now = datetime.utcnow()
    for routine in ROUTINES:
        source_pages = routine.pop("source_pages")
        routine_doc = _remap_exercise_ids(routine, id_aliases or {})
        docs.append({
            **routine_doc,
            "source_book_id": SOURCE_BOOK_ID,
            "source_refs": [_source_ref("cal_section_training_routine", source_pages, routine_doc["title"])],
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        })
        routine["source_pages"] = source_pages
    docs.extend([
        {
            "id": "cal_tpl_weekly_stacked_full_body",
            "category": "weekly_structure",
            "level": "all_levels",
            "title": "Stacked Full-Body Calisthenics Routine",
            "description": "Complete selected push, pull, and squat levels sequentially in one longer session. Best for strength quality and full rest between exercises.",
            "sport_tags": ["bodyweight", "calisthenics"],
            "equipment_required": ["bodyweight"],
            "sessions_per_week": "3",
            "estimated_duration": "about 90 minutes",
            "weekly_pattern": ["Mon full push/pull/squat", "Wed full push/pull/squat", "Fri full push/pull/squat"],
            "source_book_id": SOURCE_BOOK_ID,
            "source_refs": [_source_ref("cal_section_training_routine", [112], "Stacking routine up")],
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "cal_tpl_weekly_one_routine_per_day",
            "category": "weekly_structure",
            "level": "all_levels",
            "title": "One Routine Per Day Calisthenics Split",
            "description": "Train push, pull, and squat routines on separate days, then repeat. Each pattern is trained twice weekly with shorter sessions.",
            "sport_tags": ["bodyweight", "calisthenics"],
            "equipment_required": ["bodyweight"],
            "sessions_per_week": "6",
            "estimated_duration": "about 30 minutes",
            "weekly_pattern": ["Mon push", "Tue pull", "Wed squat", "Thu push", "Fri pull", "Sat squat", "Sun rest"],
            "source_book_id": SOURCE_BOOK_ID,
            "source_refs": [_source_ref("cal_section_training_routine", [112], "One day, one routine")],
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "cal_tpl_weekly_triplet_full_body",
            "category": "weekly_structure",
            "level": "all_levels",
            "title": "Triplet Full-Body Calisthenics Routine",
            "description": "Pair push, pull, and squat exercises into triplets for time efficiency while still giving each same exercise roughly 120 seconds before repeating.",
            "sport_tags": ["bodyweight", "calisthenics"],
            "equipment_required": ["bodyweight"],
            "sessions_per_week": "3",
            "estimated_duration": "30-45 minutes",
            "weekly_pattern": ["Mon triplets", "Wed triplets", "Fri triplets"],
            "source_book_id": SOURCE_BOOK_ID,
            "source_refs": [_source_ref("cal_section_training_routine", [113], "Pair workouts up to triplet")],
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        },
    ])
    return docs


def _programming_rule_docs() -> List[Dict[str, Any]]:
    docs = []
    now = datetime.utcnow()
    for rule in PROGRAMMING_RULES:
        pages = rule.pop("source_pages")
        docs.append({
            **rule,
            "source_book_id": SOURCE_BOOK_ID,
            "source_refs": [_source_ref("cal_section_training_routine", pages, rule["title"])],
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        })
        rule["source_pages"] = pages
    return docs


async def ingest(pdf_path: Path, ocr_cache: Path) -> Dict[str, int]:
    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    await ensure_database_schema(db)

    pages = load_ocr_pages(pdf_path, ocr_cache)
    now = datetime.utcnow()
    source_doc = {
        "id": SOURCE_BOOK_ID,
        "title": "Calisthenics Playbook for Push Pull Squat",
        "author": "Wayne Foong Weng Hui",
        "source_type": "pdf_ocr",
        "file_name": pdf_path.name,
        "page_count": len(pages),
        "domains": ["calisthenics", "bodyweight", "push", "pull", "squat"],
        "summary": "Bodyweight progression playbook for one-arm push-ups, pull-ups, and pistol squats, including exercise instruction and five-level routines.",
        "ingestion_method": INGESTION_METHOD,
        "created_at": now,
        "updated_at": now,
    }

    counts: Dict[str, int] = {}
    for collection in ("source_registry", "knowledge_sources"):
        await db[collection].replace_one({"id": SOURCE_BOOK_ID}, source_doc, upsert=True)
        counts[collection] = 1

    id_aliases = await _canonical_id_aliases(db)

    counts["source_sections"] = await _upsert_many(db, "source_sections", _source_sections(pages))
    primary_docs = [_exercise_doc(record, pages, collection="primary") for record in EXERCISES]
    variation_docs = [_exercise_doc(record, pages, collection="variation") for record in VARIATIONS]
    raw_docs = [_raw_exercise_doc(record, pages) for record in [*EXERCISES, *VARIATIONS]]
    counts["primary_exercise_library"] = await _upsert_many(db, "primary_exercise_library", primary_docs)
    counts["exercise_variation_library"] = await _upsert_many(db, "exercise_variation_library", variation_docs)
    counts["exercise_library"] = await _upsert_many(db, "exercise_library", raw_docs)
    id_aliases = {**id_aliases, **await _canonical_id_aliases(db)}
    counts["exercise_progression_graph"] = await _upsert_many(db, "exercise_progression_graph", _progression_docs(id_aliases))
    counts["workout_templates"] = await _upsert_many(db, "workout_templates", _routine_docs(id_aliases))
    counts["programming_rules"] = await _upsert_many(db, "programming_rules", _programming_rule_docs())
    client.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest the Calisthenics Playbook PDF into MongoDB.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--ocr-cache", type=Path, default=DEFAULT_OCR_CACHE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = asyncio.run(ingest(args.pdf, args.ocr_cache))
    for collection, count in counts.items():
        print(f"{collection}: {count}")


if __name__ == "__main__":
    main()

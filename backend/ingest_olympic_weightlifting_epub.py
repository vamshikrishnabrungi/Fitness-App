from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from zipfile import ZipFile

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


ROOT_DIR = Path(__file__).parent
PROJECT_ROOT = ROOT_DIR.parent
DEFAULT_EPUB = PROJECT_ROOT / "dokumen.pub_olympic-weightlifting-a-complete-guide-for-athletes-amp-coaches-3nbsped.epub"

SOURCE_BOOK_ID = "olympic_weightlifting_complete_guide_3rd_ed"
SOURCE_TITLE = "Olympic Weightlifting: A Complete Guide for Athletes & Coaches, Third Edition"
SOURCE_AUTHOR = "Greg Everett"
SOURCE_PUBLISHER = "Catalyst Athletics"

EXERCISE_FILES = {
    "OEBPS/text00073.html": "snatch",
    "OEBPS/text00074.html": "clean",
    "OEBPS/text00075.html": "jerk",
    "OEBPS/text00076.html": "general",
}

MAJOR_SECTION_FILES = {
    "OEBPS/text00008.html": ("foundations", "Understanding the Lifts"),
    "OEBPS/text00009.html": ("coaching", "Learning & Teaching the Lifts"),
    "OEBPS/text00010.html": ("individualization", "Individual Variation"),
    "OEBPS/text00011.html": ("facility_equipment", "Facility & Equipment"),
    "OEBPS/text00012.html": ("warmup", "Warming Up"),
    "OEBPS/text00013.html": ("bracing", "Breathing & Trunk Rigidity"),
    "OEBPS/text00014.html": ("squat", "The Squat"),
    "OEBPS/text00018.html": ("start_position", "Starting Position Principles"),
    "OEBPS/text00024.html": ("snatch", "Understanding the Snatch"),
    "OEBPS/text00030.html": ("clean", "Understanding the Clean"),
    "OEBPS/text00035.html": ("jerk", "Understanding the Jerk"),
    "OEBPS/text00038.html": ("error_correction", "Introduction to Error Correction"),
    "OEBPS/text00039.html": ("error_correction", "Universal Errors"),
    "OEBPS/text00040.html": ("error_correction", "Snatch Errors"),
    "OEBPS/text00041.html": ("error_correction", "Clean Errors"),
    "OEBPS/text00042.html": ("error_correction", "Jerk Errors"),
    "OEBPS/text00044.html": ("program_design", "Introduction to Program Design"),
    "OEBPS/text00045.html": ("assessment", "Assessment"),
    "OEBPS/text00046.html": ("training_variables", "Training Variables"),
    "OEBPS/text00047.html": ("jump_training", "Jump Training"),
    "OEBPS/text00048.html": ("accessory_work", "Accessory Work"),
    "OEBPS/text00050.html": ("specific_populations", "Specific Populations"),
    "OEBPS/text00051.html": ("program_design", "The Program Design Process"),
    "OEBPS/text00052.html": ("recovery", "Restoration & Recovery"),
    "OEBPS/text00053.html": ("training_practices", "Training Practices"),
    "OEBPS/text00078.html": ("nutrition", "Introduction to Nutrition"),
    "OEBPS/text00079.html": ("bodyweight", "Bodyweight"),
    "OEBPS/text00080.html": ("supplements", "Supplements"),
    "OEBPS/text00082.html": ("mobility", "Introduction to Mobility & Flexibility"),
    "OEBPS/text00083.html": ("mobility", "Stretches"),
    "OEBPS/text00084.html": ("recovery", "Self-Myofascial Release"),
    "OEBPS/text00088.html": ("glossary", "Glossary"),
}

TECHNICAL_MODEL_FILES = {
    "OEBPS/text00008.html": "all_lifts",
    "OEBPS/text00013.html": "all_lifts",
    "OEBPS/text00014.html": "squat",
    "OEBPS/text00015.html": "all_lifts",
    "OEBPS/text00016.html": "snatch_clean",
    "OEBPS/text00017.html": "snatch_clean",
    "OEBPS/text00018.html": "snatch_clean",
    "OEBPS/text00021.html": "snatch",
    "OEBPS/text00024.html": "snatch",
    "OEBPS/text00027.html": "clean",
    "OEBPS/text00030.html": "clean",
    "OEBPS/text00033.html": "jerk",
    "OEBPS/text00035.html": "jerk",
    "OEBPS/text00036.html": "clean_and_jerk",
}

COACHING_PROGRESSION_FILES = {
    "OEBPS/text00009.html": "all_lifts",
    "OEBPS/text00022.html": "snatch",
    "OEBPS/text00023.html": "snatch",
    "OEBPS/text00028.html": "clean",
    "OEBPS/text00029.html": "clean",
    "OEBPS/text00034.html": "jerk",
}

TECHNICAL_ERROR_FILES = {
    "OEBPS/text00039.html": "snatch_clean",
    "OEBPS/text00040.html": "snatch",
    "OEBPS/text00041.html": "clean",
    "OEBPS/text00042.html": "jerk",
}

PROGRAMMING_RULE_FILES = {
    "OEBPS/text00044.html": "program_design",
    "OEBPS/text00045.html": "assessment",
    "OEBPS/text00046.html": "training_variables",
    "OEBPS/text00047.html": "jump_training",
    "OEBPS/text00048.html": "accessory_work",
    "OEBPS/text00050.html": "specific_populations",
    "OEBPS/text00051.html": "program_design_process",
    "OEBPS/text00053.html": "training_practices",
    "OEBPS/text00055.html": "program_skill_level_0",
    "OEBPS/text00056.html": "program_skill_level_1",
    "OEBPS/text00057.html": "program_skill_level_2",
    "OEBPS/text00058.html": "program_skill_level_3",
    "OEBPS/text00059.html": "program_skill_level_4",
    "OEBPS/text00060.html": "program_skill_level_5",
}

RECOVERY_RULE_FILES = {
    "OEBPS/text00052.html": "restoration_recovery",
    "OEBPS/text00084.html": "self_myofascial_release",
}

NUTRITION_FILES = {
    "OEBPS/text00078.html": "nutrition",
    "OEBPS/text00079.html": "bodyweight",
    "OEBPS/text00080.html": "supplements",
}

MOBILITY_FILES = {
    "OEBPS/text00082.html": "mobility_principles",
    "OEBPS/text00083.html": "stretches",
}


@dataclass
class SectionDoc:
    id: str
    file_path: str
    section_order: int
    title: str
    domain: str
    topics: List[str]
    word_count: int
    paragraph_count: int
    content_hash: str


def _slug(value: str) -> str:
    text = value.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sentences(value: str) -> List[str]:
    text = _clean_text(value)
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [_clean_text(piece) for piece in pieces if len(_clean_text(piece)) > 12]


def _short_text(value: str, max_chars: int = 240) -> str:
    text = _clean_text(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "."


def _short_items(values: Iterable[str], *, limit: int = 5, max_chars: int = 180) -> List[str]:
    items: List[str] = []
    seen = set()
    for value in values:
        item = _short_text(value, max_chars=max_chars).strip(" -")
        key = item.lower()
        if item and key not in seen:
            items.append(item)
            seen.add(key)
        if len(items) >= limit:
            break
    return items


def _derived_summary(title: str, body: str, *, max_chars: int = 320) -> str:
    sentence_list = _sentences(body)
    if not sentence_list:
        return f"Reference topic for {title}."
    selected = " ".join(sentence_list[:2])
    return _short_text(selected, max_chars=max_chars)


def _field_sentences(body: str, needles: Sequence[str], *, limit: int = 5, max_chars: int = 180) -> List[str]:
    lowered_needles = [needle.lower() for needle in needles]
    matches = [
        sentence
        for sentence in _sentences(body)
        if any(needle in sentence.lower() for needle in lowered_needles)
    ]
    return _short_items(matches, limit=limit, max_chars=max_chars)


def _coaching_cues(title: str, body: str) -> List[str]:
    cue_sentences = _field_sentences(
        body,
        [
            "keep",
            "maintain",
            "stay",
            "drive",
            "push",
            "pull",
            "finish",
            "receive",
            "balance",
            "position",
            "focus",
            "cue",
        ],
        limit=6,
    )
    if cue_sentences:
        return cue_sentences
    return _short_items(_sentences(body), limit=3)


def _corrections_from_text(body: str) -> List[str]:
    return _field_sentences(
        body,
        ["correct", "fix", "improve", "avoid", "prevent", "reduce", "drill", "exercise", "practice"],
        limit=6,
    )


def _progression_steps_from_text(title: str, body: str) -> List[str]:
    steps = _field_sentences(
        body,
        ["begin", "start", "progress", "advance", "then", "next", "stage", "step", "learn", "teach"],
        limit=6,
    )
    if steps:
        return steps
    return _short_items([f"Use {title} as a progression or teaching checkpoint."], limit=1)


def _usage_context(title: str, body: str, topics: Sequence[str]) -> List[str]:
    contexts = set(topics)
    lower = f"{title} {body}".lower()
    if any(token in lower for token in ["beginner", "learn", "teach", "progression"]):
        contexts.add("teaching_progression")
    if any(token in lower for token in ["error", "mistake", "correct", "fix"]):
        contexts.add("technical_correction")
    if any(token in lower for token in ["program", "volume", "intensity", "frequency", "sets", "reps"]):
        contexts.add("program_design")
    if any(token in lower for token in ["stretch", "mobility", "flexibility", "range of motion"]):
        contexts.add("mobility")
    if any(token in lower for token in ["recovery", "rest", "sleep", "fatigue", "restoration"]):
        contexts.add("recovery")
    if any(token in lower for token in ["nutrition", "protein", "carbohydrate", "bodyweight", "supplement"]):
        contexts.add("nutrition")
    return sorted(contexts)


def _contraindications_from_text(body: str) -> List[str]:
    lower = body.lower()
    flags = set()
    checks = {
        "shoulder_pain": ["shoulder", "overhead", "rack"],
        "wrist_pain": ["wrist", "front rack", "grip"],
        "low_back_pain": ["back", "spine", "trunk", "hinge"],
        "knee_pain": ["knee", "squat", "split", "jump"],
        "ankle_pain": ["ankle", "calf", "jump", "receiving"],
        "hip_pain": ["hip", "squat", "pull"],
        "high_fatigue": ["fatigue", "recovery", "rest"],
    }
    safety_words = ["pain", "injury", "avoid", "risk", "problem", "error", "fault", "excessive", "limited"]
    if any(word in lower for word in safety_words):
        for flag, needles in checks.items():
            if any(needle in lower for needle in needles):
                flags.add(flag)
    return sorted(flags)


def _sport_tags_for_exercise(patterns: Sequence[str], qualities: Sequence[str], family: str) -> List[str]:
    tags = set()
    if "explosive_power" in qualities or "triple_extension" in patterns:
        tags.update(["jumping_sports", "field_sports", "court_sports"])
    if "overhead_stability" in patterns or family == "jerk":
        tags.update(["volleyball", "throwing_sports", "overhead_athletes"])
    if "pull_mechanics" in qualities or family in {"snatch", "clean", "pull"}:
        tags.update(["power_development", "sprint_transfer"])
    if "split_stance" in patterns:
        tags.update(["running", "field_sports", "deceleration"])
    if "squat" in patterns:
        tags.update(["general_strength", "jumping_sports"])
    return sorted(tags or {"general_athletic_development"})


def _variation_links(values: Sequence[str], current_name: str) -> Dict[str, List[str]]:
    text = " ".join(values)
    pieces = [
        _clean_text(piece).strip(".")
        for piece in re.split(r",|;|\band\b|\bor\b", text)
        if _clean_text(piece)
    ]
    names = [piece for piece in pieces if 3 <= len(piece) <= 80 and piece.lower() != current_name.lower()]
    lower = text.lower()
    if any(word in lower for word in ["easier", "simpler", "begin", "progression", "variation"]):
        regressions = names[:4]
    else:
        regressions = []
    progressions = names[:4] if any(word in lower for word in ["heavier", "advanced", "increase", "progress"]) else []
    substitutions = names[:5]
    return {
        "regressions": sorted(set(regressions), key=str.lower),
        "progressions": sorted(set(progressions), key=str.lower),
        "substitutions": sorted(set(substitutions), key=str.lower),
    }


def _normalize_title(value: str) -> str:
    value = _clean_text(value)
    value = re.sub(r"^olyGuide3rdEd-iBook-\d+\s*", "", value)
    return value.strip(" .")


def _paragraphs(soup: BeautifulSoup) -> List[Tuple[str, str, List[str]]]:
    rows: List[Tuple[str, str, List[str]]] = []
    for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
        text = _clean_text(p.get_text(" ", strip=True))
        if not text:
            continue
        classes = p.get("class") or []
        rows.append((str(p.name), text, [str(item) for item in classes]))
    return rows


def _domain_for_file(file_path: str, title: str) -> str:
    if file_path in EXERCISE_FILES:
        return f"{EXERCISE_FILES[file_path]}_exercise_library"
    if file_path in MAJOR_SECTION_FILES:
        return MAJOR_SECTION_FILES[file_path][0]
    title_l = title.lower()
    if "program" in title_l:
        return "program_design"
    if "nutrition" in title_l or "bodyweight" in title_l or "supplement" in title_l:
        return "nutrition"
    if "mobility" in title_l or "stretch" in title_l:
        return "mobility"
    if "competition" in title_l:
        return "competition"
    if "snatch" in title_l:
        return "snatch"
    if "clean" in title_l:
        return "clean"
    if "jerk" in title_l:
        return "jerk"
    return "book_structure"


def _topics_from_text(title: str, text: str) -> List[str]:
    haystack = f"{title} {text}".lower()
    candidates = [
        "snatch",
        "clean",
        "jerk",
        "squat",
        "pull",
        "deadlift",
        "press",
        "overhead",
        "receiving_position",
        "starting_position",
        "warmup",
        "mobility",
        "recovery",
        "nutrition",
        "program_design",
        "training_variables",
        "assessment",
        "jump_training",
        "error_correction",
        "accessory_work",
        "youth",
        "masters",
        "competition",
        "technique",
        "strength",
        "power",
    ]
    checks = {
        "receiving_position": "receiving position",
        "starting_position": "starting position",
        "program_design": "program",
        "training_variables": "training variable",
        "jump_training": "jump",
        "error_correction": "error",
        "accessory_work": "accessory",
    }
    topics = []
    for item in candidates:
        needle = checks.get(item, item)
        if needle in haystack:
            topics.append(item)
    return sorted(set(topics))


def _section_title(file_path: str, soup: BeautifulSoup, paragraphs: List[Tuple[str, str, List[str]]]) -> str:
    chapter = soup.find(class_="chapter-title")
    if chapter:
        return _normalize_title(chapter.get_text(" ", strip=True))
    if file_path in MAJOR_SECTION_FILES:
        return MAJOR_SECTION_FILES[file_path][1]
    for _, text, _ in paragraphs:
        title = _normalize_title(text)
        if len(title) > 2 and not title.startswith("iBook"):
            return title[:140]
    return Path(file_path).name


def parse_sections(epub_path: Path) -> List[SectionDoc]:
    with ZipFile(epub_path) as archive:
        html_files = [name for name in archive.namelist() if name.lower().endswith((".html", ".xhtml", ".htm"))]
        sections: List[SectionDoc] = []
        for index, file_path in enumerate(html_files, start=1):
            soup = BeautifulSoup(archive.read(file_path).decode("utf-8", "ignore"), "html.parser")
            paragraphs = _paragraphs(soup)
            text = _clean_text(" ".join(text for _, text, _ in paragraphs))
            title = _section_title(file_path, soup, paragraphs)
            domain = _domain_for_file(file_path, title)
            topics = _topics_from_text(title, text)
            section_id = f"ow_section_{index:03d}_{_slug(title)[:48]}"
            sections.append(
                SectionDoc(
                    id=section_id,
                    file_path=file_path,
                    section_order=index,
                    title=title,
                    domain=domain,
                    topics=topics,
                    word_count=len(text.split()),
                    paragraph_count=len(paragraphs),
                    content_hash=_hash_text(text),
                )
            )
        return sections


def _extract_labeled_fields(paragraphs: Sequence[str]) -> Tuple[List[str], Dict[str, List[str]]]:
    unlabeled: List[str] = []
    fields: Dict[str, List[str]] = {}
    for text in paragraphs:
        match = re.match(r"^(AKA|Notes|Purpose|Programming|Variations):\s*(.*)$", text, re.IGNORECASE)
        if match:
            key = match.group(1).lower()
            value = _clean_text(match.group(2))
            if value:
                fields.setdefault(key, []).append(value)
            continue
        unlabeled.append(text)
    return unlabeled, fields


def _split_aliases(values: Iterable[str]) -> List[str]:
    aliases: List[str] = []
    for value in values:
        for piece in re.split(r"[,;/]|\bor\b", value):
            piece = _clean_text(piece).strip(".")
            if piece and len(piece) < 80:
                aliases.append(piece)
    return sorted(set(aliases), key=str.lower)


def _equipment_for_name(name: str) -> List[str]:
    lower = name.lower()
    if "chin-up" in lower or "pull-up" in lower:
        return ["bodyweight", "pull-up bar"]
    if "lunge" in lower or "split squat" in lower:
        return ["bodyweight", "dumbbells", "barbell"]
    if "upper back extension" in lower:
        return ["bodyweight", "back extension bench"]
    if "good morning" in lower or "romanian deadlift" in lower or "stiff-legged" in lower or "straight-legged" in lower:
        return ["barbell", "dumbbells"]
    equipment = {"barbell", "plates"}
    if "block" in lower:
        equipment.add("blocks")
    if "riser" in lower:
        equipment.add("riser")
    if "bench pull" in lower:
        equipment.add("bench")
    return sorted(equipment)


def _exercise_family(name: str, section_family: str) -> str:
    lower = name.lower()
    if "squat" in lower:
        return "squat"
    if "deadlift" in lower:
        return "deadlift"
    if "pull" in lower or "high-pull" in lower or "shrug" in lower or "lift-off" in lower:
        return "pull"
    if "press" in lower:
        return "press"
    if "row" in lower:
        return "row"
    if "lunge" in lower or "split squat" in lower:
        return "lunge"
    if "good morning" in lower or "romanian" in lower or "stiff-legged" in lower or "straight-legged" in lower:
        return "hinge"
    if "support" in lower or "recovery" in lower:
        return "support"
    if section_family in {"snatch", "clean", "jerk"}:
        return section_family
    return "general_strength"


def _movement_patterns(name: str, family: str) -> List[str]:
    lower = name.lower()
    patterns = set()
    if family in {"snatch", "clean"}:
        patterns.update(["olympic_lift", "pull", "triple_extension"])
    if family == "jerk":
        patterns.update(["olympic_lift", "vertical_push", "split_stance"])
    if "squat" in lower:
        patterns.add("squat")
    if "overhead" in lower or "snatch" in lower:
        patterns.add("overhead_stability")
    if "pull" in lower or "deadlift" in lower or "lift-off" in lower:
        patterns.add("hinge")
    if "split" in lower or "lunge" in lower:
        patterns.add("split_stance")
    if "press" in lower or "jerk" in lower:
        patterns.add("vertical_push")
    if "row" in lower or "pull-up" in lower or "chin-up" in lower:
        patterns.add("upper_pull")
    if "jump" in lower or "drop" in lower:
        patterns.add("jump_landing")
    return sorted(patterns)


def _muscles_for_patterns(patterns: Sequence[str], family: str) -> Tuple[List[str], List[str]]:
    primary = set()
    secondary = set()
    if any(item in patterns for item in ["olympic_lift", "triple_extension", "hinge"]):
        primary.update(["glutes", "hamstrings", "quadriceps", "upper_back"])
        secondary.update(["calves", "trunk", "grip"])
    if "squat" in patterns:
        primary.update(["quadriceps", "glutes"])
        secondary.update(["adductors", "trunk", "hamstrings"])
    if "overhead_stability" in patterns:
        primary.update(["shoulders", "upper_back", "trunk"])
        secondary.update(["triceps", "serratus_anterior"])
    if "vertical_push" in patterns:
        primary.update(["shoulders", "triceps", "quadriceps"])
        secondary.update(["upper_back", "trunk", "glutes"])
    if "upper_pull" in patterns:
        primary.update(["lats", "upper_back"])
        secondary.update(["biceps", "grip", "rear_delts"])
    if "split_stance" in patterns:
        primary.update(["quadriceps", "glutes"])
        secondary.update(["adductors", "calves", "trunk"])
    if not primary:
        primary.update(["full_body"])
    return sorted(primary), sorted(secondary)


def _training_qualities(name: str, purpose_text: str, family: str) -> List[str]:
    lower = f"{name} {purpose_text}".lower()
    qualities = set()
    if any(word in lower for word in ["power", "aggressive", "extension", "speed", "jump"]):
        qualities.add("explosive_power")
    if any(word in lower for word in ["technique", "position", "balance", "accuracy", "footwork"]):
        qualities.add("technique")
    if any(word in lower for word in ["strength", "heavy", "support", "squat", "deadlift"]):
        qualities.add("strength")
    if any(word in lower for word in ["overhead", "receiving", "rack", "split"]):
        qualities.add("receiving_position")
    if any(word in lower for word in ["pull", "turnover", "extension", "transition"]):
        qualities.add("pull_mechanics")
    if "mobility" in lower or "flexibility" in lower:
        qualities.add("mobility")
    if family in {"snatch", "clean", "jerk"}:
        qualities.add(f"{family}_skill")
    return sorted(qualities or {"general_strength"})


def _category_for_exercise(name: str, family: str, qualities: Sequence[str]) -> str:
    lower = name.lower()
    if "power" in lower or "jump" in lower or "explosive_power" in qualities:
        return "power"
    if "balance" in lower or "drop" in lower or "tall" in lower or "technique" in qualities:
        return "technique"
    if family in {"squat", "deadlift", "hinge", "press", "row", "lunge", "pull"}:
        return "strength"
    if family in {"snatch", "clean", "jerk"}:
        return "weightlifting_skill"
    return "accessory_strength"


def _difficulty_for_exercise(name: str, family: str, section_family: str) -> str:
    lower = name.lower()
    if section_family in {"snatch", "clean", "jerk"} and not any(
        token in lower for token in ["deadlift", "pull", "shrug", "press", "support", "dip", "balance"]
    ):
        return "advanced"
    if any(token in lower for token in ["snatch", "jerk", "overhead", "segment", "stage", "split"]):
        return "advanced"
    if any(token in lower for token in ["squat", "deadlift", "pull", "press", "row", "lunge"]):
        return "intermediate"
    return "intermediate"


def _contraindications(patterns: Sequence[str]) -> List[str]:
    flags = set()
    if "overhead_stability" in patterns or "vertical_push" in patterns:
        flags.update(["shoulder_pain", "limited_overhead_mobility"])
    if "squat" in patterns or "jump_landing" in patterns or "split_stance" in patterns:
        flags.update(["knee_pain"])
    if "hinge" in patterns or "olympic_lift" in patterns:
        flags.update(["low_back_pain", "hamstring_pain"])
    if "jump_landing" in patterns:
        flags.update(["ankle_pain", "achilles_pain"])
    return sorted(flags)


def _parse_programming(values: Sequence[str]) -> Dict[str, Any]:
    text = " ".join(values)
    percent_ranges = sorted(set(re.findall(r"\b\d{1,3}(?:-\d{1,3})?%", text)))
    rep_ranges = sorted(set(re.findall(r"\b\d+(?:-\d+)?\s+reps?\b", text, flags=re.IGNORECASE)))
    set_ranges = sorted(set(re.findall(r"\b\d+(?:-\d+)?\s+sets?\b", text, flags=re.IGNORECASE)))
    placement = []
    lower = text.lower()
    if "after" in lower:
        placement.append("after_primary_lift_or_variant")
    if "before" in lower:
        placement.append("before_strength_or_accessory_work")
    if "maximal effort" in lower or "maximal" in lower:
        placement.append("may_be_loaded_heavily_when_appropriate")
    if "light" in lower:
        placement.append("can_be_used_light_for_technique")
    return {
        "intensity_ranges": percent_ranges,
        "rep_ranges": rep_ranges,
        "set_ranges": set_ranges,
        "placement_tags": sorted(set(placement)),
        "has_programming_guidance": bool(text),
    }


def _definition_for(name: str, family: str, section_family: str, qualities: Sequence[str]) -> str:
    quality_text = ", ".join(qualities[:3]).replace("_", " ")
    if section_family in {"snatch", "clean", "jerk"}:
        return f"Olympic weightlifting {section_family} variation used for {quality_text}."
    return f"{name} variation used for {quality_text}."


def parse_exercises(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, section_family in EXERCISE_FILES.items():
            soup = BeautifulSoup(archive.read(file_path).decode("utf-8", "ignore"), "html.parser")
            section = sections_by_file[file_path]
            current_name: Optional[str] = None
            current_paragraphs: List[str] = []

            def flush() -> None:
                if not current_name:
                    return
                unlabeled, fields = _extract_labeled_fields(current_paragraphs)
                aka = _split_aliases(fields.get("aka", []))
                purpose_text = " ".join(fields.get("purpose", []))
                family = _exercise_family(current_name, section_family)
                patterns = _movement_patterns(current_name, family)
                primary, secondary = _muscles_for_patterns(patterns, family)
                qualities = _training_qualities(current_name, purpose_text, family)
                category = _category_for_exercise(current_name, family, qualities)
                source_text = _clean_text(" ".join(current_paragraphs))
                variation_links = _variation_links(fields.get("variations", []), current_name)
                note_text = " ".join(fields.get("notes", []))
                exercise_summary = _derived_summary(current_name, source_text)
                cues = _coaching_cues(current_name, " ".join([purpose_text, note_text, source_text]))
                common_errors = _field_sentences(
                    source_text,
                    ["avoid", "error", "mistake", "fail", "incorrect", "problem", "excessive"],
                    limit=4,
                )
                injury_flags = _contraindications(patterns)
                records.append(
                    {
                        "id": f"ow_ex_{_slug(current_name)}",
                        "name": current_name,
                        "aliases": aka,
                        "definition": _definition_for(current_name, family, section_family, qualities),
                        "summary": exercise_summary,
                        "category": category,
                        "exercise_type": category,
                        "exercise_family": family,
                        "movement_patterns": patterns,
                        "primary_muscles": primary,
                        "secondary_muscles": secondary,
                        "equipment_required": _equipment_for_name(current_name),
                        "difficulty": _difficulty_for_exercise(current_name, family, section_family),
                        "training_qualities": qualities,
                        "sport_tags": _sport_tags_for_exercise(patterns, qualities, family),
                        "injury_flags": injury_flags,
                        "contraindications": injury_flags,
                        "regressions": variation_links["regressions"],
                        "progressions": variation_links["progressions"],
                        "substitutions": variation_links["substitutions"],
                        "coaching_cues": cues,
                        "common_errors": common_errors,
                        "usage_context": _usage_context(current_name, source_text, qualities),
                        "programming": _parse_programming(fields.get("programming", [])),
                        "source_fields_available": sorted(fields.keys()),
                        "variation_count_hint": len(fields.get("variations", [])),
                        "note_count_hint": len(fields.get("notes", [])),
                        "paragraph_count": len(current_paragraphs),
                        "source_text_hash": _hash_text(source_text),
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "source_refs": [
                            {
                                "source_book_id": SOURCE_BOOK_ID,
                                "section_id": section.id,
                                "section_title": section.title,
                                "epub_file": file_path,
                                "heading": current_name,
                            }
                        ],
                        "ingestion_method": "epub_heading_labeled_field_extraction_v1",
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )

            for paragraph in soup.find_all("p"):
                classes = paragraph.get("class") or []
                text = _clean_text(paragraph.get_text(" ", strip=True))
                if not text:
                    continue
                if "heading-b" in classes:
                    flush()
                    current_name = text
                    current_paragraphs = []
                    continue
                if current_name and "chapter-title" not in classes:
                    current_paragraphs.append(text)
            flush()
    return records


def build_source_record(epub_path: Path, sections: Sequence[SectionDoc], exercises: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": SOURCE_BOOK_ID,
        "title": SOURCE_TITLE,
        "author": SOURCE_AUTHOR,
        "publisher": SOURCE_PUBLISHER,
        "source_type": "epub",
        "file_name": epub_path.name,
        "file_path": str(epub_path),
        "file_sha256": _hash_text(epub_path.read_bytes().hex()),
        "section_count": len(sections),
        "word_count": sum(section.word_count for section in sections),
        "exercise_count": len(exercises),
        "extraction_scope": [
            "complete_epub_section_index",
            "supplemental_exercise_library",
            "major_training_topic_index",
            "technical_models",
            "technical_errors",
            "coaching_progressions",
            "programming_rules",
            "recovery_rules",
            "nutrition_principles",
            "mobility_drills",
            "glossary_terms",
        ],
        "copyright_handling": "Stores normalized metadata, tags, hashes, and source references; does not store full book prose.",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "version": "v1.0.0",
    }


def build_section_records(sections: Sequence[SectionDoc]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            "id": section.id,
            "source_book_id": SOURCE_BOOK_ID,
            "section_order": section.section_order,
            "title": section.title,
            "domain": section.domain,
            "topics": section.topics,
            "epub_file": section.file_path,
            "word_count": section.word_count,
            "paragraph_count": section.paragraph_count,
            "content_hash": section.content_hash,
            "created_at": now,
            "updated_at": now,
        }
        for section in sections
    ]


def build_training_principles(sections: Sequence[SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for section in sections:
        if section.word_count < 300:
            continue
        if section.domain.endswith("_exercise_library") or section.domain == "book_structure":
            continue
        records.append(
            {
                "id": f"ow_principle_{_slug(section.domain)}_{section.section_order:03d}",
                "source_book_id": SOURCE_BOOK_ID,
                "source_section_id": section.id,
                "domain": section.domain,
                "title": section.title,
                "topics": section.topics,
                "knowledge_type": "section_level_training_topic",
                "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
                "source_refs": [
                    {
                        "source_book_id": SOURCE_BOOK_ID,
                        "section_id": section.id,
                        "section_title": section.title,
                        "epub_file": section.file_path,
                    }
                ],
                "expert_validation_status": "pending",
                "version": "v1.0.0",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
    return records


def _read_soup(archive: ZipFile, file_path: str) -> BeautifulSoup:
    return BeautifulSoup(archive.read(file_path).decode("utf-8", "ignore"), "html.parser")


def _source_ref(section: SectionDoc, heading: str) -> Dict[str, str]:
    return {
        "source_book_id": SOURCE_BOOK_ID,
        "section_id": section.id,
        "section_title": section.title,
        "epub_file": section.file_path,
        "heading": heading,
    }


def _knowledge_tags(title: str, body: str) -> List[str]:
    text = f"{title} {body}".lower()
    tags = set(_topics_from_text(title, body))
    keyword_map = {
        "balance": ["balance", "center of mass", "center of pressure", "base of support"],
        "bar_path": ["bar path", "barbell path", "proximity", "separation"],
        "first_pull": ["first pull", "floor", "knee"],
        "second_pull": ["second pull", "extension", "power position"],
        "third_pull": ["third pull", "turnover", "pull under"],
        "receiving_position": ["receiving", "rack", "overhead", "split"],
        "recovery": ["recovery", "stand", "restoration"],
        "mobility": ["mobility", "flexibility", "stretch"],
        "position": ["position", "posture", "stance", "grip"],
        "bracing": ["breath", "trunk", "pressurization", "rigidity", "brace"],
        "loading": ["intensity", "percentage", "volume", "sets", "reps"],
        "fatigue": ["fatigue", "recovery", "rest", "sleep"],
        "nutrition": ["protein", "carbohydrate", "fat", "water", "supplement"],
        "safety": ["pain", "injury", "risk", "aggressive", "severe"],
    }
    for tag, needles in keyword_map.items():
        if any(needle in text for needle in needles):
            tags.add(tag)
    return sorted(tags)


def _sentences(text: str) -> List[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    pieces = re.split(r"(?<=[.!?])\s+", cleaned)
    return [piece.strip() for piece in pieces if len(piece.strip()) > 20]


def _short_text(text: str, limit: int = 240, max_chars: Optional[int] = None) -> str:
    if max_chars is not None:
        limit = max_chars
    cleaned = _clean_text(text)
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return f"{truncated}."


def _compact_summary(title: str, body: str, limit: int = 280) -> str:
    for sentence in _sentences(body):
        if not sentence.lower().startswith(("figure ", "table ")):
            return _short_text(sentence, limit)
    return _short_text(title, limit)


def _action_points(body: str, keywords: Sequence[str], limit: int = 5) -> List[str]:
    points: List[str] = []
    for sentence in _sentences(body):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            points.append(_short_text(sentence, 220))
        if len(points) >= limit:
            break
    return points


def _usage_context(title: str, body: str, topics: Optional[Sequence[str]] = None) -> List[str]:
    text = f"{title} {body}".lower()
    contexts = list(topics or [])
    if any(term in text for term in ["beginner", "new lifter", "learning"]):
        contexts.append("beginner_or_learning_lifter")
    if any(term in text for term in ["advanced", "experienced", "maximal"]):
        contexts.append("advanced_or_heavy_training")
    if any(term in text for term in ["warm-up", "warm up", "primer"]):
        contexts.append("warmup_or_technique_primer")
    if any(term in text for term in ["mobility", "flexibility", "stretch"]):
        contexts.append("mobility_limitation")
    if any(term in text for term in ["pain", "injury", "risk"]):
        contexts.append("pain_or_injury_caution")
    if any(term in text for term in ["program", "sets", "reps", "intensity", "volume"]):
        contexts.append("program_design")
    if any(term in text for term in ["teach", "progression", "stage", "step"]):
        contexts.append("teaching_progression")
    if any(term in text for term in ["error", "mistake", "correct", "fix"]):
        contexts.append("technical_correction")
    if any(term in text for term in ["recovery", "rest", "sleep", "fatigue", "restoration"]):
        contexts.append("recovery")
    if any(term in text for term in ["nutrition", "protein", "carbohydrate", "bodyweight", "supplement"]):
        contexts.append("nutrition")
    return sorted(set(contexts))


def _contraindications_from_body(body: str) -> List[str]:
    text = body.lower()
    flags = []
    if "pain" in text or "injury" in text:
        flags.append("active_pain_or_injury")
    if "shoulder" in text or "overhead" in text:
        flags.append("shoulder_or_overhead_limitation")
    if "wrist" in text or "rack" in text:
        flags.append("wrist_or_rack_limitation")
    if "back" in text or "spine" in text:
        flags.append("back_or_trunk_control_limitation")
    if "knee" in text or "squat" in text:
        flags.append("knee_or_squat_limitation")
    return sorted(set(flags))


def _body_regions_from_text(text: str) -> List[str]:
    lower = text.lower()
    mapping = {
        "wrist": ["wrist", "finger", "thumb", "hook grip"],
        "shoulder": ["shoulder", "overhead", "rack", "rotator", "arm"],
        "thoracic_spine": ["t-spine", "thoracic", "upper back"],
        "hip": ["hip", "glute"],
        "ankle": ["ankle", "calf"],
        "hamstring": ["hamstring"],
        "adductor": ["adductor", "groin"],
        "lat": ["lat", "underarm"],
        "trunk": ["trunk", "core", "spine"],
        "quad": ["quad", "quadriceps"],
    }
    return sorted({region for region, needles in mapping.items() if any(needle in lower for needle in needles)})


def _block_records(
    soup: BeautifulSoup,
    *,
    heading_classes: Sequence[str] = ("heading-a", "heading-b", "heading-c"),
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for p in soup.find_all("p"):
        classes = [str(item) for item in (p.get("class") or [])]
        text = _clean_text(p.get_text(" ", strip=True))
        if not text:
            continue
        heading_class = next((item for item in heading_classes if item in classes), None)
        if heading_class:
            if current:
                records.append(current)
            current = {"title": text, "heading_class": heading_class, "paragraphs": []}
            continue
        if current and "chapter-title" not in classes and not text.startswith("Figure "):
            current["paragraphs"].append({"text": text, "classes": classes})
    if current:
        records.append(current)
    return records


def parse_technical_models(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, lift in TECHNICAL_MODEL_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            for index, block in enumerate(_block_records(soup, heading_classes=("heading-a", "heading-b", "heading-c")), start=1):
                body = _clean_text(" ".join(item["text"] for item in block["paragraphs"]))
                if not body:
                    continue
                phase = _slug(block["title"])
                topics = _knowledge_tags(block["title"], body)
                records.append(
                    {
                        "id": f"ow_tech_{_slug(lift)}_{section.section_order:03d}_{index:03d}_{phase[:40]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "lift": lift,
                        "phase": phase,
                        "title": block["title"],
                        "summary": _derived_summary(block["title"], body),
                        "position_rules": _field_sentences(
                            body,
                            ["position", "posture", "balance", "bar", "feet", "grip", "rack", "overhead"],
                            limit=6,
                        ),
                        "coaching_cues": _coaching_cues(block["title"], body),
                        "common_errors": _field_sentences(
                            body,
                            ["avoid", "error", "fault", "mistake", "problem", "excessive"],
                            limit=5,
                        ),
                        "corrections": _corrections_from_text(body),
                        "usage_context": _usage_context(block["title"], body, topics),
                        "contraindications": _contraindications_from_text(body),
                        "heading_level": block["heading_class"],
                        "topics": topics,
                        "paragraph_count": len(block["paragraphs"]),
                        "content_hash": _hash_text(body),
                        "knowledge_type": "technical_model",
                        "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
                        "source_refs": [_source_ref(section, block["title"])],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )
    return records


def parse_coaching_progressions(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, lift in COACHING_PROGRESSION_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            blocks = _block_records(soup, heading_classes=("heading-a", "heading-b", "heading-c"))
            if not blocks:
                text = _clean_text(" ".join(text for _, text, _ in _paragraphs(soup)))
                if text:
                    blocks = [{"title": section.title, "heading_class": "chapter", "paragraphs": [{"text": text, "classes": []}]}]
            for index, block in enumerate(blocks, start=1):
                body = _clean_text(" ".join(item["text"] for item in block["paragraphs"]))
                if not body:
                    continue
                stage = _slug(block["title"])
                topics = _knowledge_tags(block["title"], body)
                records.append(
                    {
                        "id": f"ow_coach_{_slug(lift)}_{section.section_order:03d}_{index:03d}_{stage[:40]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "lift": lift,
                        "stage": stage,
                        "title": block["title"],
                        "summary": _derived_summary(block["title"], body),
                        "progression_steps": _progression_steps_from_text(block["title"], body),
                        "coaching_cues": _coaching_cues(block["title"], body),
                        "corrections": _corrections_from_text(body),
                        "usage_context": _usage_context(block["title"], body, topics),
                        "contraindications": _contraindications_from_text(body),
                        "heading_level": block["heading_class"],
                        "topics": topics,
                        "paragraph_count": len(block["paragraphs"]),
                        "content_hash": _hash_text(body),
                        "knowledge_type": "coaching_progression",
                        "app_usage": "Use as teaching order, progression, regression, and correction context.",
                        "source_refs": [_source_ref(section, block["title"])],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )
    return records


def parse_technical_errors(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, lift in TECHNICAL_ERROR_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            current_error: Optional[Dict[str, Any]] = None
            current_cause: Optional[Dict[str, Any]] = None

            def flush_cause() -> None:
                nonlocal current_cause
                if current_error and current_cause:
                    current_error["causes"].append(current_cause)
                current_cause = None

            def flush_error() -> None:
                nonlocal current_error
                flush_cause()
                if current_error:
                    body = _clean_text(" ".join(current_error.pop("_paragraphs")))
                    current_error["content_hash"] = _hash_text(body)
                    current_error["topics"] = _knowledge_tags(current_error["error_name"], body)
                    current_error["summary"] = _derived_summary(current_error["error_name"], body)
                    current_error["common_errors"] = _short_items(
                        [point["text"] for point in current_error.get("description_points", [])],
                        limit=5,
                    )
                    current_error["corrections"] = _corrections_from_text(body)
                    current_error["coaching_cues"] = _coaching_cues(current_error["error_name"], body)
                    current_error["usage_context"] = _usage_context(
                        current_error["error_name"],
                        body,
                        current_error["topics"],
                    )
                    current_error["contraindications"] = _contraindications_from_text(body)
                    current_error["paragraph_count"] = len(current_error.get("description_points", [])) + sum(
                        len(cause.get("points", [])) for cause in current_error.get("causes", [])
                    )
                    records.append(current_error)
                current_error = None

            for p in soup.find_all("p"):
                classes = [str(item) for item in (p.get("class") or [])]
                text = _clean_text(p.get_text(" ", strip=True))
                if not text:
                    continue
                if "heading-a" in classes:
                    flush_error()
                    name = text
                    current_error = {
                        "id": f"ow_error_{_slug(lift)}_{section.section_order:03d}_{_slug(name)[:55]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "lift": lift,
                        "error_name": name,
                        "description_points": [],
                        "causes": [],
                        "correction_signal_tags": [],
                        "_paragraphs": [],
                        "knowledge_type": "technical_error",
                        "source_refs": [_source_ref(section, name)],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                    continue
                if "heading-c" in classes and current_error:
                    flush_cause()
                    current_cause = {
                        "name": text,
                        "topics": [],
                        "points": [],
                        "summary": "",
                        "content_hash": "",
                    }
                    current_error["_paragraphs"].append(text)
                    continue
                if current_error and "chapter-title" not in classes:
                    current_error["_paragraphs"].append(text)
                    lower = text.lower()
                    if "exercise" in lower or "drill" in lower:
                        current_error["correction_signal_tags"].append("corrective_exercises")
                    if "cue" in lower:
                        current_error["correction_signal_tags"].append("coaching_cues")
                    if "mobility" in lower:
                        current_error["correction_signal_tags"].append("mobility_intervention")
                    if current_cause:
                        current_cause["points"].append(
                            {
                                "text": _short_text(text),
                                "content_hash": _hash_text(text),
                                "signal_tags": _knowledge_tags(current_cause["name"], text),
                            }
                        )
                    else:
                        current_error["description_points"].append(
                            {
                                "text": _short_text(text),
                                "content_hash": _hash_text(text),
                                "signal_tags": _knowledge_tags(current_error["error_name"], text),
                            }
                        )
            flush_error()

    for record in records:
        record["correction_signal_tags"] = sorted(set(record.get("correction_signal_tags", [])))
        for cause in record.get("causes", []):
            body = " ".join(point.get("text", "") for point in cause.get("points", []))
            cause["content_hash"] = _hash_text(body)
            cause["topics"] = sorted({tag for point in cause.get("points", []) for tag in point.get("signal_tags", [])})
            cause["summary"] = _derived_summary(cause.get("name", "Cause"), body)
    return records


def parse_programming_rules(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, rule_type in PROGRAMMING_RULE_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            blocks = _block_records(soup, heading_classes=("heading-a", "heading-b", "heading-c"))
            if not blocks:
                body = _clean_text(" ".join(text for _, text, _ in _paragraphs(soup)))
                if body:
                    blocks = [{"title": section.title, "heading_class": "chapter", "paragraphs": [{"text": body, "classes": []}]}]
            for index, block in enumerate(blocks, start=1):
                body = _clean_text(" ".join(item["text"] for item in block["paragraphs"]))
                if not body:
                    continue
                title_slug = _slug(block["title"])
                topics = _knowledge_tags(block["title"], body)
                records.append(
                    {
                        "id": f"ow_rule_{_slug(rule_type)}_{section.section_order:03d}_{index:03d}_{title_slug[:38]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "rule_type": rule_type,
                        "title": block["title"],
                        "summary": _derived_summary(block["title"], body),
                        "rule_text": _derived_summary(block["title"], body, max_chars=260),
                        "loading_guidance": _field_sentences(
                            body,
                            ["intensity", "load", "percentage", "%", "heavy", "light", "volume", "sets", "reps"],
                            limit=6,
                        ),
                        "progression_logic": _progression_steps_from_text(block["title"], body),
                        "coaching_cues": _coaching_cues(block["title"], body),
                        "contraindications": _contraindications_from_text(body),
                        "usage_context": _usage_context(block["title"], body, topics),
                        "applies_to": topics,
                        "topics": topics,
                        "paragraph_count": len(block["paragraphs"]),
                        "content_hash": _hash_text(body),
                        "knowledge_type": "programming_rule",
                        "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
                        "source_refs": [_source_ref(section, block["title"])],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )
    return records


def parse_recovery_rules(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, category in RECOVERY_RULE_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            blocks = _block_records(soup, heading_classes=("heading-a", "heading-b", "heading-c"))
            for index, block in enumerate(blocks, start=1):
                body = _clean_text(" ".join(item["text"] for item in block["paragraphs"]))
                if not body:
                    continue
                topics = _knowledge_tags(block["title"], body)
                records.append(
                    {
                        "id": f"ow_recovery_{_slug(category)}_{section.section_order:03d}_{index:03d}_{_slug(block['title'])[:40]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "category": category,
                        "title": block["title"],
                        "summary": _derived_summary(block["title"], body),
                        "rule_text": _derived_summary(block["title"], body, max_chars=260),
                        "recovery_methods": _field_sentences(
                            body,
                            ["sleep", "rest", "recovery", "massage", "restoration", "fatigue", "training"],
                            limit=6,
                        ),
                        "usage_context": _usage_context(block["title"], body, topics),
                        "contraindications": _contraindications_from_text(body),
                        "topics": topics,
                        "paragraph_count": len(block["paragraphs"]),
                        "content_hash": _hash_text(body),
                        "knowledge_type": "recovery_rule",
                        "source_refs": [_source_ref(section, block["title"])],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )
    return records


def parse_nutrition_principles(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, category in NUTRITION_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            blocks = _block_records(soup, heading_classes=("heading-a", "heading-b", "heading-c"))
            for index, block in enumerate(blocks, start=1):
                body = _clean_text(" ".join(item["text"] for item in block["paragraphs"]))
                if not body:
                    continue
                topics = _knowledge_tags(block["title"], body)
                records.append(
                    {
                        "id": f"ow_nutrition_{_slug(category)}_{section.section_order:03d}_{index:03d}_{_slug(block['title'])[:40]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "category": category,
                        "title": block["title"],
                        "summary": _derived_summary(block["title"], body),
                        "principle_text": _derived_summary(block["title"], body, max_chars=260),
                        "action_guidance": _field_sentences(
                            body,
                            ["eat", "consume", "protein", "carbohydrate", "fat", "water", "bodyweight", "supplement"],
                            limit=6,
                        ),
                        "usage_context": _usage_context(block["title"], body, topics),
                        "contraindications": _contraindications_from_text(body),
                        "topics": topics,
                        "paragraph_count": len(block["paragraphs"]),
                        "content_hash": _hash_text(body),
                        "knowledge_type": "nutrition_principle",
                        "source_refs": [_source_ref(section, block["title"])],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )
    return records


def parse_mobility_drills(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        for file_path, category in MOBILITY_FILES.items():
            section = sections_by_file[file_path]
            soup = _read_soup(archive, file_path)
            if category != "stretches":
                blocks = _block_records(soup, heading_classes=("heading-a", "heading-b", "heading-c"))
                for index, block in enumerate(blocks, start=1):
                    body = _clean_text(" ".join(item["text"] for item in block["paragraphs"]))
                    if not body:
                        continue
                    topics = _knowledge_tags(block["title"], body)
                    records.append(
                        {
                            "id": f"ow_mobility_principle_{section.section_order:03d}_{index:03d}_{_slug(block['title'])[:40]}",
                            "source_book_id": SOURCE_BOOK_ID,
                            "source_section_id": section.id,
                            "name": block["title"],
                            "category": category,
                            "addresses": [],
                            "body_regions": _body_regions_from_text(body),
                            "summary": _derived_summary(block["title"], body),
                            "instructions": _short_items(_sentences(body), limit=5),
                            "coaching_cues": _coaching_cues(block["title"], body),
                            "usage_context": _usage_context(block["title"], body, topics),
                            "contraindications": _contraindications_from_text(body),
                            "topics": topics,
                            "paragraph_count": len(block["paragraphs"]),
                            "content_hash": _hash_text(body),
                            "knowledge_type": "mobility_principle",
                            "source_refs": [_source_ref(section, block["title"])],
                            "expert_validation_status": "pending",
                            "version": "v1.0.0",
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                    )
                continue

            current: Optional[Dict[str, Any]] = None
            for p in soup.find_all("p"):
                classes = [str(item) for item in (p.get("class") or [])]
                text = _clean_text(p.get_text(" ", strip=True))
                if not text:
                    continue
                if "heading-a" in classes:
                    if current:
                        records.append(current)
                    current = {
                        "id": f"ow_mobility_{section.section_order:03d}_{_slug(text)[:55]}",
                        "source_book_id": SOURCE_BOOK_ID,
                        "source_section_id": section.id,
                        "name": text,
                        "category": "stretch",
                        "addresses": [],
                        "body_regions": [],
                        "topics": [],
                        "_paragraphs": [],
                        "knowledge_type": "mobility_drill",
                        "source_refs": [_source_ref(section, text)],
                        "expert_validation_status": "pending",
                        "version": "v1.0.0",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                    continue
                if current and "stretch-addresses-text" in classes:
                    addresses = re.sub(r"^Addresses:\s*", "", text, flags=re.IGNORECASE)
                    current["addresses"].extend([_clean_text(item) for item in re.split(r",|;", addresses) if _clean_text(item)])
                    current["_paragraphs"].append(text)
                    continue
                if current and "chapter-title" not in classes and not text.startswith("Figure "):
                    current["_paragraphs"].append(text)
            if current:
                records.append(current)

    for record in records:
        body = _clean_text(" ".join(record.pop("_paragraphs", [])))
        record["body_regions"] = sorted(set([*record.get("body_regions", []), *_body_regions_from_text(f"{record.get('name', '')} {body}")]))
        topics = _knowledge_tags(record.get("name", ""), body)
        record["topics"] = topics
        record["summary"] = record.get("summary") or _derived_summary(record.get("name", "Mobility"), body)
        record["instructions"] = record.get("instructions") or _short_items(_sentences(body), limit=5)
        record["coaching_cues"] = record.get("coaching_cues") or _coaching_cues(record.get("name", ""), body)
        record["usage_context"] = record.get("usage_context") or _usage_context(record.get("name", ""), body, topics)
        record["contraindications"] = record.get("contraindications") or _contraindications_from_text(body)
        record["paragraph_count"] = max(record.get("paragraph_count", 0), len(body.split(". ")) if body else 0)
        record["content_hash"] = _hash_text(body)
    return records


def parse_glossary_terms(epub_path: Path, sections_by_file: Dict[str, SectionDoc]) -> List[Dict[str, Any]]:
    section = sections_by_file["OEBPS/text00088.html"]
    records: List[Dict[str, Any]] = []
    with ZipFile(epub_path) as archive:
        soup = _read_soup(archive, "OEBPS/text00088.html")
        for p in soup.find_all("p"):
            text = _clean_text(p.get_text(" ", strip=True))
            if not text or ":" not in text or text == "Glossary":
                continue
            term, definition = text.split(":", 1)
            term = _clean_text(term)
            definition = _clean_text(definition)
            if not term or len(term) > 80 or not definition:
                continue
            records.append(
                {
                    "id": f"ow_glossary_{_slug(term)}",
                    "source_book_id": SOURCE_BOOK_ID,
                    "source_section_id": section.id,
                    "term": term,
                    "definition": definition,
                    "topics": _knowledge_tags(term, definition),
                    "content_hash": _hash_text(text),
                    "source_refs": [_source_ref(section, term)],
                    "expert_validation_status": "pending",
                    "version": "v1.0.0",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
    return records


async def _upsert_many(collection: Any, records: Sequence[Dict[str, Any]], key: str = "id") -> int:
    count = 0
    for record in records:
        await collection.update_one({key: record[key]}, {"$set": record}, upsert=True)
        count += 1
    return count


async def ingest(epub_path: Path, clear_source: bool) -> Dict[str, int]:
    load_dotenv(ROOT_DIR / ".env")
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "sftc_database")

    sections = parse_sections(epub_path)
    sections_by_file = {section.file_path: section for section in sections}
    exercises = parse_exercises(epub_path, sections_by_file)
    source_record = build_source_record(epub_path, sections, exercises)
    section_records = build_section_records(sections)
    principle_records = build_training_principles(sections)
    technical_models = parse_technical_models(epub_path, sections_by_file)
    technical_errors = parse_technical_errors(epub_path, sections_by_file)
    coaching_progressions = parse_coaching_progressions(epub_path, sections_by_file)
    programming_rules = parse_programming_rules(epub_path, sections_by_file)
    recovery_rules = parse_recovery_rules(epub_path, sections_by_file)
    nutrition_principles = parse_nutrition_principles(epub_path, sections_by_file)
    mobility_drills = parse_mobility_drills(epub_path, sections_by_file)
    glossary_terms = parse_glossary_terms(epub_path, sections_by_file)

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    await ensure_database_schema(db)

    if clear_source:
        source_filter = {"source_book_id": SOURCE_BOOK_ID}
        await db.exercise_library.delete_many(source_filter)
        await db.source_sections.delete_many(source_filter)
        await db.training_principles.delete_many(source_filter)
        await db.programming_rules.delete_many(source_filter)
        await db.technical_models.delete_many(source_filter)
        await db.technical_errors.delete_many(source_filter)
        await db.coaching_progressions.delete_many(source_filter)
        await db.mobility_drills.delete_many(source_filter)
        await db.recovery_rules.delete_many(source_filter)
        await db.nutrition_principles.delete_many(source_filter)
        await db.glossary_terms.delete_many(source_filter)
        await db.knowledge_sources.delete_many({"id": SOURCE_BOOK_ID})

    await db.knowledge_sources.update_one({"id": SOURCE_BOOK_ID}, {"$set": source_record}, upsert=True)
    await _upsert_many(db.source_sections, section_records)
    await _upsert_many(db.exercise_library, exercises)
    await _upsert_many(db.training_principles, principle_records)
    await _upsert_many(db.technical_models, technical_models)
    await _upsert_many(db.technical_errors, technical_errors)
    await _upsert_many(db.coaching_progressions, coaching_progressions)
    await _upsert_many(db.programming_rules, programming_rules)
    await _upsert_many(db.recovery_rules, recovery_rules)
    await _upsert_many(db.nutrition_principles, nutrition_principles)
    await _upsert_many(db.mobility_drills, mobility_drills)
    await _upsert_many(db.glossary_terms, glossary_terms)

    run_record = {
        "id": str(uuid.uuid4()),
        "source_book_id": SOURCE_BOOK_ID,
        "source_file": str(epub_path),
        "created_at": datetime.utcnow(),
        "clear_source": clear_source,
        "section_count": len(section_records),
        "exercise_count": len(exercises),
        "training_principle_count": len(principle_records),
        "technical_model_count": len(technical_models),
        "technical_error_count": len(technical_errors),
        "coaching_progression_count": len(coaching_progressions),
        "programming_rule_count": len(programming_rules),
        "recovery_rule_count": len(recovery_rules),
        "nutrition_principle_count": len(nutrition_principles),
        "mobility_drill_count": len(mobility_drills),
        "glossary_term_count": len(glossary_terms),
        "status": "completed",
    }
    await db.knowledge_extraction_runs.insert_one(run_record)
    client.close()
    return {
        "sections": len(section_records),
        "exercises": len(exercises),
        "training_principles": len(principle_records),
        "technical_models": len(technical_models),
        "technical_errors": len(technical_errors),
        "coaching_progressions": len(coaching_progressions),
        "programming_rules": len(programming_rules),
        "recovery_rules": len(recovery_rules),
        "nutrition_principles": len(nutrition_principles),
        "mobility_drills": len(mobility_drills),
        "glossary_terms": len(glossary_terms),
        "sources": 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Olympic Weightlifting EPUB into MongoDB knowledge collections.")
    parser.add_argument("--epub", type=Path, default=DEFAULT_EPUB)
    parser.add_argument("--no-clear-source", action="store_true", help="Do not clear previous records for this source before ingesting.")
    args = parser.parse_args()

    if not args.epub.exists():
        raise FileNotFoundError(args.epub)

    counts = asyncio.run(ingest(args.epub, clear_source=not args.no_clear_source))
    print("Olympic Weightlifting EPUB ingestion complete")
    for key, value in counts.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

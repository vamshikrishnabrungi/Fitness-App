#!/usr/bin/env python3
"""Generate the next exercise thumbnail batch through OpenRouter Images.

This script intentionally generates contact sheets first, then crops each cell
into the existing frontend thumbnail asset folder. It uses the current
`priority_batches.json`, so run `exercise_thumbnail_pipeline.py` before this
when coverage has changed.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
PRIORITY_BATCHES_PATH = ROOT / "backend" / "thumbnail_generation" / "priority_batches.json"
REVIEW_NOTES_PATH = ROOT / "backend" / "thumbnail_generation" / "review_notes.json"
SHEET_DIR = ROOT / "backend" / "thumbnail_generation" / "openrouter_sheets"
THUMBNAIL_DIR = ROOT / "frontend" / "assets" / "images" / "exercise-thumbnails"
PIPELINE_PATH = ROOT / "backend" / "exercise_thumbnail_pipeline.py"


EXERCISE_DESCRIPTIONS = {
    "push-jerk-in-snatch": "athlete holding wide snatch grip barbell overhead in slight dip/jerk catch",
    "push-jerk-in-split": "athlete driving barbell overhead into split stance",
    "push-press-behind-the-neck": "athlete pressing barbell from behind neck with leg drive",
    "quarter-eagle-chest-pass": "athlete in quarter-squat/eagle stance throwing medicine ball chest pass forward",
    "rebound-jerk": "athlete doing quick dip-and-rebound jerk drive with barbell front rack",
    "ring-dip": "athlete on gymnastic rings lowering into dip, elbows bent",
    "ring-muscle-up": "athlete transitioning from ring pull-up to ring support above rings",
    "ring-turned-out-support-hold": "athlete holding locked-out ring support with rings turned outward",
    "segment-clean": "athlete performing clean with subtle ghosted pause positions from floor to front rack",
    "segment-power-clean": "athlete performing power clean with ghosted pause positions and high front-rack catch",
    "segment-power-snatch": "athlete performing power snatch with ghosted pause positions and overhead quarter-squat catch",
    "segment-snatch": "athlete performing snatch with ghosted pause positions and overhead squat catch",
    "single-leg-bounding": "athlete performing repeated forward bounds on one leg",
    "single-leg-depth-jump": "athlete stepping off low box and landing on one leg",
    "single-leg-hops": "athlete doing small repeated hops on one foot",
    "single-leg-lateral-jump": "athlete jumping sideways from one leg to one-leg landing",
    "single-leg-push-off": "athlete pushing explosively off one leg from low athletic stance",
    "single-leg-squat": "athlete lowering into single-leg squat with free leg forward",
    "skin-the-cat": "athlete hanging from rings rotating legs through and behind body",
    "slow-pull-clean": "athlete slowly pulling barbell from floor before clean turnover",
    "slow-pull-snatch": "athlete slowly pulling wide-grip barbell before snatch turnover",
    "snatch-balance": "athlete dropping under barbell into overhead squat from back rack",
    "snatch-bench-pull": "athlete chest-supported on high bench rowing/pulling wide-grip barbell",
    "snatch-deadlift": "athlete wide-grip deadlifting barbell from floor",
    "snatch-deadlift-on-riser": "athlete standing on low riser doing wide-grip deadlift",
    "snatch-deadlift-to-power-position": "athlete wide-grip deadlifting barbell to upper-thigh power position",
    "snatch-from-power-position": "athlete snatching barbell from upper-thigh power position overhead",
    "snatch-high-pull": "athlete pulling wide-grip barbell high with elbows up",
    "snatch-high-pull-on-riser": "athlete on low riser pulling wide-grip barbell high",
    "snatch-lift-off": "athlete lifting wide-grip barbell from floor to below knee only",
    "snatch-long-pull": "athlete completing long wide-grip snatch pull through full extension",
    "snatch-on-riser": "athlete on riser performing snatch from lower start to overhead catch",
    "snatch-power-jerk": "athlete driving wide-grip barbell overhead into power jerk catch",
    "snatch-press": "athlete pressing wide-grip barbell overhead from back rack",
    "snatch-pull": "athlete performing wide-grip snatch pull from floor",
    "snatch-pull-on-riser": "athlete on low riser performing wide-grip snatch pull",
    "snatch-pull-down": "athlete pulling under wide-grip barbell into overhead receiving position",
    "snatch-push-press": "athlete using leg drive to push-press wide-grip barbell overhead",
    "snatch-segment-deadlift": "athlete doing wide-grip deadlift with ghosted pause positions",
    "snatch-segment-pull": "athlete doing wide-grip snatch pull with ghosted pause positions",
    "snatch-shrug": "athlete standing tall with wide-grip barbell and shrugging shoulders",
    "snatch-transition-deadlift": "athlete holding wide-grip barbell around knee transition position",
    "snatch-with-no-brush": "athlete snatching bar close without thigh brush, overhead catch shown",
    "snatch-with-no-jump": "athlete snatching bar overhead with feet staying planted",
    "split-clean": "athlete catching clean in split stance with bar in front rack",
    "split-snatch": "athlete catching snatch overhead in split stance",
    "split-squat-with-cycle": "athlete in split squat cycling rear knee forward like sprint mechanics",
    "split-pike-jump": "athlete airborne in split/pike jump shape",
    "squat-jerk": "athlete catching jerk overhead in deep squat",
    "stage-clean": "athlete cleaning barbell with staged pause positions",
}


def load_openrouter_key() -> str:
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    if ENV_PATH.exists():
        match = re.search(r'OPENROUTER_API_KEY="?([^"\n]+)"?', ENV_PATH.read_text())
        if match:
            return match.group(1)
    raise RuntimeError("OPENROUTER_API_KEY is not configured")


def load_items(limit: int) -> list[dict[str, Any]]:
    batches = json.loads(PRIORITY_BATCHES_PATH.read_text())
    selected: list[dict[str, Any]] = []
    for batch in batches:
        for item in batch["items"]:
            if len(selected) < limit:
                selected.append(item)
    return selected


def item_description(item: dict[str, Any]) -> str:
    slug = item["slug"]
    return EXERCISE_DESCRIPTIONS.get(slug, f"athlete performing {item['name']} with clear exercise posture")


def build_prompt(chunk: list[dict[str, Any]]) -> str:
    lines = [
        "Create a 2-column by 3-row contact sheet of clean static exercise thumbnails for a mobile fitness app.",
        "Style: black-and-white instructional fitness illustration, warm off-white background, no text, no labels, no numbers, no watermarks.",
        "Each cell must show the exact named movement clearly with generous padding and centered subject.",
        "",
        "Cells in reading order:",
    ]
    for index, item in enumerate(chunk, 1):
        lines.append(f"{index}. {item['name']}: {item_description(item)}.")
    return "\n".join(lines)


def generate_sheet(key: str, model: str, prompt: str, index: int) -> Path:
    response = requests.post(
        "https://openrouter.ai/api/v1/images",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Runlete exercise thumbnail generation",
        },
        json={
            "model": model,
            "prompt": prompt,
            "aspect_ratio": "2:3",
            "resolution": "1K",
            "n": 1,
        },
        timeout=180,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter image generation failed: {response.status_code} {response.text[:1000]}")

    payload = response.json()
    b64 = payload["data"][0]["b64_json"]
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]

    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    path = SHEET_DIR / f"openrouter_batch_sheet_{int(time.time())}_{index:02d}.png"
    path.write_bytes(base64.b64decode(b64))
    return path


def crop_sheet(source: Path, items: list[dict[str, Any]]) -> int:
    image = Image.open(source).convert("RGB")
    width, height = image.size
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for index, item in enumerate(items):
        row = index // 2
        col = index % 2
        box = (
            round(col * width / 2),
            round(row * height / 3),
            round((col + 1) * width / 2),
            round((row + 1) * height / 3),
        )
        image.crop(box).resize((512, 512), Image.Resampling.LANCZOS).save(
            THUMBNAIL_DIR / f"{item['slug']}.png",
            optimize=True,
        )
        count += 1
    return count


def append_review_notes(batch_label: str, source: Path, items: list[dict[str, Any]]) -> None:
    notes = json.loads(REVIEW_NOTES_PATH.read_text()) if REVIEW_NOTES_PATH.exists() else []
    notes.append(
        {
            "batch": batch_label,
            "source_image": str(source),
            "items": items,
            "review_status": "draft_ok",
            "notes": ["Generated through OpenRouter image API for later review."],
        }
    )
    REVIEW_NOTES_PATH.write_text(json.dumps(notes, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--model", default="google/gemini-3.1-flash-image")
    args = parser.parse_args()

    key = load_openrouter_key()
    items = load_items(args.limit)
    if not items:
        print("No missing thumbnails to generate.")
        return 0

    total = 0
    for sheet_index, start in enumerate(range(0, len(items), 6), 1):
        chunk = items[start : start + 6]
        prompt = build_prompt(chunk)
        print(f"Generating sheet {sheet_index}: {', '.join(item['slug'] for item in chunk)}")
        sheet = generate_sheet(key, args.model, prompt, sheet_index)
        total += crop_sheet(sheet, chunk)
        append_review_notes(f"openrouter_{int(time.time())}_{sheet_index:02d}", sheet, chunk)
        print(f"Saved {sheet}")

    subprocess.run([sys.executable, str(PIPELINE_PATH)], check=True, cwd=ROOT)
    print(f"Generated and cropped {total} thumbnails.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

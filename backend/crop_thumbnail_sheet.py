#!/usr/bin/env python3
"""Crop a generated 2x3 exercise thumbnail contact sheet into PNG assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "frontend" / "assets" / "images" / "exercise-thumbnails"
REVIEW_NOTES = ROOT / "backend" / "thumbnail_generation" / "review_notes.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def crop_sheet(source: Path, items: List[Dict[str, str]]) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGB")
    width, height = image.size
    for index, item in enumerate(items):
        row = index // 2
        column = index % 2
        box = (
            round(column * width / 2),
            round(row * height / 3),
            round((column + 1) * width / 2),
            round((row + 1) * height / 3),
        )
        image.crop(box).resize((512, 512), Image.Resampling.LANCZOS).save(
            ASSET_DIR / f"{item['slug']}.png",
            optimize=True,
        )


def append_review_note(batch_label: str, source: Path, items: List[Dict[str, str]], status: str, notes: str) -> None:
    existing = load_json(REVIEW_NOTES) if REVIEW_NOTES.exists() else []
    existing.append(
        {
            "batch": batch_label,
            "source_image": str(source),
            "items": items,
            "review_status": status,
            "notes": [notes] if notes else [],
        }
    )
    write_json(REVIEW_NOTES, existing)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Generated contact sheet PNG path")
    parser.add_argument("--batch-file", default=str(ROOT / "backend" / "thumbnail_generation" / "priority_batches.json"))
    parser.add_argument("--batch-index", type=int, required=True, help="Zero-based index in priority_batches.json")
    parser.add_argument("--label", default="")
    parser.add_argument("--review-status", default="needs_review", choices=["draft_ok", "needs_review", "rejected"])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    source = Path(args.source)
    batches = load_json(Path(args.batch_file))
    batch = batches[args.batch_index]
    items = batch["items"]
    crop_sheet(source, items)
    append_review_note(
        args.label or f"batch_{batch.get('batch_number', args.batch_index + 1)}",
        source,
        items,
        args.review_status,
        args.notes,
    )
    print(f"cropped {len(items)} images from {source}")


if __name__ == "__main__":
    main()

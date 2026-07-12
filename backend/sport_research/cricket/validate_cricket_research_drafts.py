from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


CRICKET_DIR = Path(__file__).resolve().parent
DRAFT_DIR = CRICKET_DIR / "drafts"


REQUIRED_TOP_LEVEL = [
    "sport",
    "domain",
    "executive_summary",
    "key_concepts",
    "technical_models",
    "tactical_rules",
    "physical_demands",
    "injury_or_load_risks",
    "training_implications",
    "backend_records_to_create",
    "open_questions",
    "source_refs",
]

LIST_FIELDS = [
    "key_concepts",
    "technical_models",
    "tactical_rules",
    "physical_demands",
    "injury_or_load_risks",
    "training_implications",
    "backend_records_to_create",
    "open_questions",
    "source_refs",
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Draft must be a JSON object")
    return data


def _validate_source_refs(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for index, ref in enumerate(data.get("source_refs") or []):
        if not isinstance(ref, dict):
            errors.append(f"source_refs[{index}] must be an object")
            continue
        if not ref.get("title"):
            errors.append(f"source_refs[{index}] missing title")
        if not ref.get("url"):
            errors.append(f"source_refs[{index}] missing url")
        if not ref.get("source_type"):
            errors.append(f"source_refs[{index}] missing source_type")
    return errors


def validate_file(path: Path) -> List[str]:
    errors: List[str] = []
    try:
        data = _load_json(path)
    except Exception as exc:
        return [f"invalid JSON: {exc}"]

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    if data.get("sport") != "cricket":
        errors.append("sport must be cricket")

    for key in LIST_FIELDS:
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} must be a list")

    if len(str(data.get("executive_summary") or "").strip()) < 80:
        errors.append("executive_summary is too short")

    source_count = len(data.get("source_refs") or [])
    if source_count < 5:
        errors.append("source_refs should include at least 5 credible sources")

    useful_item_count = sum(len(data.get(key) or []) for key in [
        "key_concepts",
        "technical_models",
        "tactical_rules",
        "physical_demands",
        "injury_or_load_risks",
        "training_implications",
        "backend_records_to_create",
    ])
    if useful_item_count < 25:
        errors.append(f"too few useful research items: {useful_item_count}")

    errors.extend(_validate_source_refs(data))
    return errors


def _paths(paths: Iterable[str]) -> List[Path]:
    explicit = [Path(path) for path in paths]
    if explicit:
        return explicit
    return sorted(DRAFT_DIR.glob("*_draft.json"))


def validate(paths: Iterable[str]) -> int:
    draft_paths = _paths(paths)
    if not draft_paths:
        print("No cricket draft files found.")
        return 0

    total_errors = 0
    for path in draft_paths:
        errors = validate_file(path)
        total_errors += len(errors)
        status = "ok" if not errors else f"{len(errors)} errors"
        print(f"{path}: {status}")
        if not errors:
            data = _load_json(path)
            counts = {
                key: len(data.get(key) or [])
                for key in LIST_FIELDS
            }
            print(f"  counts: {counts}")
        for error in errors[:40]:
            print(f"  - {error}")
        if len(errors) > 40:
            print(f"  ... {len(errors) - 40} more")
    print(f"Total errors: {total_errors}")
    return 1 if total_errors else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate cricket sport research draft JSON files.")
    parser.add_argument("paths", nargs="*", help="Optional explicit draft files. Defaults to drafts/*_draft.json.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(validate(args.paths))


if __name__ == "__main__":
    main()

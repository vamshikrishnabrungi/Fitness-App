from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "backend" / "data" / "exercise_schema" / "general_gym_exercise_taxonomy_v1.json"
DRAFT_DIR = PROJECT_ROOT / "backend" / "data" / "exercise_research_drafts"


REQUIRED_FIELDS = [
    "id",
    "name",
    "base_exercise",
    "tier",
    "category",
    "difficulty",
    "technical_complexity",
    "mobility_requirement",
    "stability_requirement",
    "impact_level",
    "load_scalability",
    "coaching_requirement",
    "equipment",
    "patterns",
    "qualities",
    "primary_muscles",
    "summary",
    "coaching_cues",
    "common_errors",
    "use_when",
    "avoid_when",
    "source_refs",
]

LIST_FIELDS = [
    "aliases",
    "equipment",
    "patterns",
    "qualities",
    "primary_muscles",
    "secondary_muscles",
    "coaching_cues",
    "common_errors",
    "use_when",
    "avoid_when",
    "progressions",
    "regressions",
    "substitutions",
    "source_refs",
]


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _records_from_json(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("records", "exercises", "data"):
            if isinstance(data.get(key), list):
                return [item for item in data[key] if isinstance(item, dict)]
    raise ValueError("Draft JSON must be a list or an object with records/exercises/data list")


def _as_set(schema: Dict[str, Any], key: str) -> set[str]:
    return {str(item) for item in schema.get(key, [])}


def _validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    record_id = record.get("id") or record.get("name") or "<unknown>"

    for field in REQUIRED_FIELDS:
        if field not in record or record[field] in (None, "", [], {}):
            errors.append(f"{record_id}: missing {field}")

    for field in LIST_FIELDS:
        if field in record and not isinstance(record[field], list):
            errors.append(f"{record_id}: {field} must be a list")

    enum_checks = {
        "tier": set(schema["classification_rules"].keys()),
        "category": {"strength", "hypertrophy", "power", "accessory", "mobility_activation", "conditioning"},
        "difficulty": {"beginner", "intermediate", "advanced"},
        "technical_complexity": {"low", "moderate", "high"},
        "mobility_requirement": {"low", "moderate", "high"},
        "stability_requirement": {"low", "moderate", "high"},
        "impact_level": {"low", "moderate", "high"},
        "load_scalability": {"low", "moderate", "high"},
        "coaching_requirement": {"low", "moderate", "high"},
    }
    for field, allowed in enum_checks.items():
        value = record.get(field)
        if value not in allowed:
            errors.append(f"{record_id}: invalid {field}={value!r}")

    allowed_patterns = _as_set(schema, "movement_patterns")
    for pattern in record.get("patterns") or []:
        if pattern not in allowed_patterns:
            errors.append(f"{record_id}: unknown pattern={pattern!r}")

    allowed_qualities = _as_set(schema, "training_qualities")
    for quality in record.get("qualities") or []:
        if quality not in allowed_qualities:
            errors.append(f"{record_id}: unknown quality={quality!r}")

    allowed_equipment = _as_set(schema, "equipment_tags")
    for equipment in record.get("equipment") or []:
        if equipment not in allowed_equipment:
            errors.append(f"{record_id}: unknown equipment={equipment!r}")

    allowed_muscles = _as_set(schema, "body_region_tags")
    for muscle in [*(record.get("primary_muscles") or []), *(record.get("secondary_muscles") or [])]:
        if muscle not in allowed_muscles:
            errors.append(f"{record_id}: unknown muscle/body region={muscle!r}")

    for source_ref in record.get("source_refs") or []:
        if not isinstance(source_ref, dict):
            errors.append(f"{record_id}: source_ref must be object")
            continue
        if not source_ref.get("title") or not source_ref.get("url"):
            errors.append(f"{record_id}: source_ref missing title/url")

    return errors


def _iter_draft_paths(paths: Iterable[str]) -> List[Path]:
    explicit = [Path(path) for path in paths]
    if explicit:
        return explicit
    return sorted(DRAFT_DIR.glob("*_draft.json"))


def validate(paths: Iterable[str]) -> int:
    schema = _load_json(SCHEMA_PATH)
    draft_paths = _iter_draft_paths(paths)
    if not draft_paths:
        print("No draft files found.")
        return 0

    total_records = 0
    total_errors = 0
    seen_ids: Dict[str, Path] = {}
    seen_names: Dict[str, Path] = {}

    for path in draft_paths:
        data = _load_json(path)
        records = _records_from_json(data)
        total_records += len(records)
        errors: List[str] = []
        for record in records:
            record_id = str(record.get("id") or "")
            record_name = str(record.get("name") or "").strip().lower()
            if record_id:
                if record_id in seen_ids:
                    errors.append(f"{record_id}: duplicate id also in {seen_ids[record_id]}")
                seen_ids[record_id] = path
            if record_name:
                if record_name in seen_names:
                    errors.append(f"{record.get('name')}: duplicate name also in {seen_names[record_name]}")
                seen_names[record_name] = path
            errors.extend(_validate_record(record, schema))
        total_errors += len(errors)
        status = "ok" if not errors else f"{len(errors)} errors"
        print(f"{path}: {len(records)} records, {status}")
        for error in errors[:40]:
            print(f"  - {error}")
        if len(errors) > 40:
            print(f"  ... {len(errors) - 40} more")

    print(f"Total records: {total_records}")
    print(f"Total errors: {total_errors}")
    return 1 if total_errors else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate draft exercise research JSON files before catalog merge.")
    parser.add_argument("paths", nargs="*", help="Optional explicit draft JSON paths. Defaults to backend/data/exercise_research_drafts/*_draft.json.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(validate(args.paths))


if __name__ == "__main__":
    main()

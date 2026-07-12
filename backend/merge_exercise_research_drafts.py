from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from backend.normalize_exercise_research_drafts import normalize_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = PROJECT_ROOT / "backend" / "data" / "exercise_research_drafts"
NORMALIZED_DIR = DRAFT_DIR / "normalized"
OUTPUT_PATH = DRAFT_DIR / "merged_general_gym_exercises.json"


LIST_FIELDS = {
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
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _dedupe_list(items: Iterable[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for item in items:
        if item in (None, "", [], {}):
            continue
        if isinstance(item, dict):
            key = json.dumps(item, sort_keys=True)
        else:
            key = str(item).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _records(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("records", "exercises", "data"):
            if isinstance(data.get(key), list):
                return [item for item in data[key] if isinstance(item, dict)]
    raise ValueError("Draft JSON must be a list or an object with records/exercises/data")


def _load_records(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in _records(data):
            normalized = normalize_record(record)
            normalized["_draft_source_file"] = str(path)
            records.append(normalized)
    return records


def _merge_record(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "id":
            continue
        if key in LIST_FIELDS:
            merged[key] = _dedupe_list([*(merged.get(key) or []), *(value or [])])
        elif key == "_draft_source_file":
            merged[key] = _dedupe_list([*(merged.get(key) if isinstance(merged.get(key), list) else [merged.get(key)]), value])
        elif merged.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
            merged[key] = value
    return merged


def merge_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name: Dict[str, Dict[str, Any]] = {}
    for record in records:
        name_key = str(record.get("name") or "").strip().lower()
        if not name_key:
            continue
        record["id"] = record.get("id") or f"ex_{_slug(name_key)}"
        if name_key in by_name:
            by_name[name_key] = _merge_record(by_name[name_key], record)
        else:
            by_name[name_key] = record

    merged_records = list(by_name.values())
    merged_records.sort(key=lambda item: (str(item.get("base_exercise") or ""), str(item.get("name") or "")))
    for record in merged_records:
        source_file = record.get("_draft_source_file")
        if source_file:
            record["draft_source_files"] = source_file if isinstance(source_file, list) else [source_file]
        record.pop("_draft_source_file", None)
    return merged_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge normalized exercise research drafts into one deduplicated general gym dataset.")
    parser.add_argument("paths", nargs="*", help="Optional draft paths. Defaults to normalized/*_draft.json.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSON path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = [Path(path) for path in args.paths] or sorted(NORMALIZED_DIR.glob("*_draft.json"))
    merged = merge_records(_load_records(paths))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"merged_records: {len(merged)}")
    print(f"output: {output_path}")


if __name__ == "__main__":
    main()

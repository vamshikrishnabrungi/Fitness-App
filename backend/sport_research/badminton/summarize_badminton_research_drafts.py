from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


BADMINTON_DIR = Path(__file__).resolve().parent
DRAFT_DIR = BADMINTON_DIR / "drafts"
OUTPUT_PATH = BADMINTON_DIR / "BADMINTON_RESEARCH_DRAFT_SUMMARY.md"

SUMMARY_FIELDS = [
    "key_concepts",
    "technical_models",
    "tactical_rules",
    "physical_demands",
    "injury_or_load_risks",
    "training_implications",
    "backend_records_to_create",
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _item_title(item: Any) -> str:
    if isinstance(item, dict):
        for key in ("name", "title", "id", "record_id", "rule", "concept", "model", "quality", "record_type", "collection"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(item, ensure_ascii=False)[:140]
    return str(item)[:140]


def _source_domain(url: str) -> str:
    cleaned = url.replace("https://", "").replace("http://", "")
    return cleaned.split("/", 1)[0].lower()


def _render_domain(path: Path, data: Dict[str, Any]) -> List[str]:
    metadata = data.get("metadata") or {}
    domain = metadata.get("domain") or path.stem
    research_goal = str(metadata.get("research_goal") or "").strip()
    lines = [
        f"## {domain}",
        "",
        f"- File: `{path.relative_to(BADMINTON_DIR)}`",
        f"- Research goal: {research_goal}",
    ]

    sources = data.get("source_refs") or []
    domains = Counter(
        _source_domain(str(ref.get("url") or ""))
        for ref in sources
        if isinstance(ref, dict) and ref.get("url")
    )
    if domains:
        lines.append(f"- Source domains: {', '.join(f'{domain} ({count})' for domain, count in domains.most_common())}")

    for field in SUMMARY_FIELDS:
        items = data.get(field) or []
        lines.append(f"- {field}: {len(items)}")

    lines.extend(["", "### Notable Items", ""])
    for field in SUMMARY_FIELDS:
        items = data.get(field) or []
        if not items:
            continue
        lines.append(f"**{field.replace('_', ' ').title()}**")
        for item in items[:6]:
            lines.append(f"- {_item_title(item)}")
        if len(items) > 6:
            lines.append(f"- ... {len(items) - 6} more")
        lines.append("")
    return lines


def build_summary(paths: Iterable[Path]) -> str:
    draft_paths = sorted(paths)
    lines = [
        "# Badminton Research Draft Summary",
        "",
        "This file is generated from the structured badminton research drafts. It is a review index, not the final sport database.",
        "",
        f"Draft files: {len(draft_paths)}",
        "",
    ]

    total_counts: Counter[str] = Counter()
    domain_docs: List[tuple[Path, Dict[str, Any]]] = []
    for path in draft_paths:
        data = _load_json(path)
        domain_docs.append((path, data))
        for field in SUMMARY_FIELDS:
            total_counts[field] += len(data.get(field) or [])

    if total_counts:
        lines.extend(["## Total Counts", ""])
        for field in SUMMARY_FIELDS:
            lines.append(f"- {field}: {total_counts[field]}")
        lines.append("")

    for path, data in domain_docs:
        lines.extend(_render_domain(path, data))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    draft_paths = sorted(DRAFT_DIR.glob("*_draft.json"))
    if not draft_paths:
        raise SystemExit("No badminton draft files found.")
    OUTPUT_PATH.write_text(build_summary(draft_paths), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

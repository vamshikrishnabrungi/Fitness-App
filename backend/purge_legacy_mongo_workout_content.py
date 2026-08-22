#!/usr/bin/env python3
"""Safely remove only Runlete's legacy Mongo workout-planning seed records.

This tool never drops a database or collection. It removes documents only when
both the collection and seed_source match the fixed allow-list below.

Dry run:
    python -m backend.purge_legacy_mongo_workout_content

Execute after verifying the dry run:
    python -m backend.purge_legacy_mongo_workout_content --execute --expected-total 31
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from pymongo import MongoClient


SEED_SOURCE = "sftc_backend_planning_collections.json"
TARGET_COLLECTIONS = (
    "macro_plan_templates",
    "planning_rules",
    "competition_week_rules",
    "sport_profiles",
)


def load_env(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--expected-total", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_env(Path(__file__).resolve().parent / ".env")
    mongo_url = config.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = config.get("DB_NAME", "test_database")

    client = MongoClient(
        mongo_url,
        serverSelectionTimeoutMS=5_000,
        connectTimeoutMS=5_000,
    )
    client.admin.command("ping")
    db = client[db_name]
    selector = {"seed_source": SEED_SOURCE}

    counts = {
        collection: db[collection].count_documents(selector)
        for collection in TARGET_COLLECTIONS
    }
    total = sum(counts.values())
    print(f"database={db_name}")
    print(f"seed_source={SEED_SOURCE}")
    for collection, count in counts.items():
        print(f"{collection}={count}")
    print(f"total={total}")

    if not args.execute:
        print("dry_run=true")
        return 0

    if args.expected_total is None:
        raise SystemExit("--expected-total is required with --execute")
    if total != args.expected_total:
        raise SystemExit(
            f"Refusing purge: expected {args.expected_total} matching records, found {total}"
        )

    deleted = 0
    for collection in TARGET_COLLECTIONS:
        deleted += db[collection].delete_many(selector).deleted_count
    if deleted != args.expected_total:
        raise SystemExit(
            f"Purge count mismatch: expected {args.expected_total}, deleted {deleted}"
        )

    remaining = sum(
        db[collection].count_documents(selector)
        for collection in TARGET_COLLECTIONS
    )
    if remaining:
        raise SystemExit(f"Purge verification failed: {remaining} matching records remain")
    print(f"deleted={deleted}")
    print("verified_remaining=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

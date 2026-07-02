#!/usr/bin/env python3
"""One-shot bootstrap for a fresh environment.

Creates the DB schema (collections + indexes) and loads the data the adaptive workout engine
needs that is NOT produced by the exercise/sport ingest pipeline:
  1. schema (all collections + indexes)
  2. training_protocols        (decision layer)
  3. macro_plan_templates      (the 5 research-backed templates)
  4. exercise embeddings       (semantic retrieval; needs `pip install fastembed`)

Idempotent — safe to re-run. Usage:
    python -m backend.seed_all
"""
from __future__ import annotations

import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient

from backend import build_exercise_embeddings, seed_macro_plan_templates, seed_training_protocols
from backend.db_setup import ensure_database_schema
from backend.embeddings import embeddings_enabled


def _env() -> tuple[str, str]:
    mongo_url, db_name = "mongodb://localhost:27017", "test_database"
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, errors="ignore"):
            line = line.strip()
            if line.startswith("MONGO_URL="):
                mongo_url = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("DB_NAME="):
                db_name = line.split("=", 1)[1].strip().strip('"').strip("'")
    return mongo_url, db_name


async def _ensure_schema(url: str, name: str) -> None:
    await ensure_database_schema(AsyncIOMotorClient(url)[name])


def main() -> None:
    url, name = _env()
    print(f"Bootstrapping {name} @ {url}")

    print("1/4 ensuring schema (collections + indexes)…")
    asyncio.run(_ensure_schema(url, name))

    print("2/4 seeding training_protocols…")
    print("     protocols in collection:", seed_training_protocols.seed(seed_training_protocols._db()))

    print("3/4 seeding macro_plan_templates…")
    print("     macro templates in collection:", seed_macro_plan_templates.seed(seed_macro_plan_templates._db()))

    if embeddings_enabled():
        print("4/4 building exercise embeddings (first run downloads the model, ~130MB)…")
        embedded, skipped = build_exercise_embeddings.build(build_exercise_embeddings._db())
        print(f"     embedded {embedded}, already up-to-date {skipped}")
    else:
        print("4/4 embeddings disabled (EXERCISE_EMBEDDINGS_ENABLED=false) — skipping; "
              "semantic retrieval will fall back to keyword matching.")

    print("Bootstrap complete ✅")


if __name__ == "__main__":
    main()

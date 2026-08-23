#!/usr/bin/env python3
"""Precompute and store semantic embeddings on exercise docs (Stage-2 of two-stage retrieval).

Embeds name + summary + muscles + patterns + qualities + equipment + tags for every exercise, and
stores the vector on the doc (`embedding`, `embedding_model`, `embedding_text_hash`). Idempotent:
re-running only re-embeds docs whose text changed. Run:  python -m backend.build_exercise_embeddings
"""
from __future__ import annotations

import hashlib
import os

from pymongo import MongoClient

from backend.embeddings import embed_texts, embedding_model_name, embeddings_enabled

COLLECTIONS = ["primary_exercise_library", "exercise_variation_library", "exercise_library", "mobility_drills"]


def _db():
    mongo_url, db_name = "mongodb://localhost:27017", "test_database"
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, errors="ignore"):
            line = line.strip()
            if line.startswith("MONGO_URL="):
                mongo_url = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("DB_NAME="):
                db_name = line.split("=", 1)[1].strip().strip('"').strip("'")
    return MongoClient(mongo_url)[db_name]


def _embedding_text(doc: dict) -> str:
    parts = [
        doc.get("name"),
        doc.get("summary") or doc.get("definition"),
        " ".join(str(x) for x in (doc.get("primary_muscles") or [])),
        " ".join(str(x) for x in (doc.get("patterns") or doc.get("movement_patterns") or [])),
        " ".join(str(x) for x in (doc.get("qualities") or doc.get("training_qualities") or [])),
        " ".join(str(x) for x in (doc.get("equipment") or doc.get("equipment_required") or [])),
        doc.get("category"),
        " ".join(str(x) for x in (doc.get("aliases") or [])),
        " ".join(str(x) for x in (doc.get("sport_tags") or [])),
    ]
    return " | ".join(str(p) for p in parts if p)


def build(db) -> tuple[int, int]:
    model = embedding_model_name()
    embedded, skipped = 0, 0
    for col in COLLECTIONS:
        docs = list(db[col].find({}, {
            "id": 1, "name": 1, "summary": 1, "definition": 1, "primary_muscles": 1,
            "patterns": 1, "movement_patterns": 1, "qualities": 1, "training_qualities": 1,
            "equipment": 1, "equipment_required": 1, "category": 1, "aliases": 1, "sport_tags": 1,
            "embedding_text_hash": 1, "embedding": 1,
        }))
        pending = []
        for doc in docs:
            if not doc.get("id"):
                continue
            text = _embedding_text(doc)
            digest = hashlib.sha1((model + "::" + text).encode("utf-8")).hexdigest()
            if doc.get("embedding") and doc.get("embedding_text_hash") == digest:
                skipped += 1
                continue
            pending.append((doc["id"], text, digest))

        for i in range(0, len(pending), 128):
            batch = pending[i:i + 128]
            vectors = embed_texts([t for _, t, _ in batch])
            if not vectors:
                raise RuntimeError("Embedding failed — is fastembed installed and enabled?")
            for (eid, _, digest), vec in zip(batch, vectors):
                db[col].update_one(
                    {"id": eid},
                    {"$set": {"embedding": vec, "embedding_model": model, "embedding_text_hash": digest}},
                )
                embedded += 1
        print(f"  {col}: embedded {len([p for p in pending])} (skipped {len(docs) - len(pending)} up-to-date)")
    return embedded, skipped


if __name__ == "__main__":
    if not embeddings_enabled():
        raise SystemExit("Embeddings disabled (EXERCISE_EMBEDDINGS_ENABLED=false).")
    total_embedded, total_skipped = build(_db())
    print(f"Done. Newly embedded: {total_embedded}, already up-to-date: {total_skipped}")

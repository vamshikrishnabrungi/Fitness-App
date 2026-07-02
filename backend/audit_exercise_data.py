#!/usr/bin/env python3
"""Data-quality audit for the exercise catalog (strength / variations / mobility / plyometrics).

Read-only. Surfaces field-completeness gaps, duplicate ids, cross-collection category conflicts,
non-movement entries, likely muscle mislabels, lazy muscle labels, progression-graph orphans, and
equipment coverage. Run:  python -m backend.audit_exercise_data
"""
from __future__ import annotations

import os
import re
from collections import Counter, defaultdict

from pymongo import MongoClient

COLLECTIONS = ["primary_exercise_library", "exercise_variation_library", "exercise_library", "mobility_drills"]

MUSCLE_RULES = [
    ("pull/row", re.compile(r"\b(pull-?up|chin-?up|\brow\b|pulldown|face pull)\b", re.I),
     {"lat", "lats", "back", "upper_back", "biceps", "rhomboid", "trap", "posterior"}),
    ("press/push", re.compile(r"\b(bench press|push-?up|overhead press|shoulder press|chest press|incline press)\b", re.I),
     {"chest", "pec", "pecs", "shoulder", "shoulders", "triceps", "deltoid", "delt", "anterior"}),
    ("squat", re.compile(r"\bsquat\b", re.I), {"quad", "quadriceps", "glute", "glutes", "adductor"}),
    ("hinge", re.compile(r"\b(deadlift|romanian|\brdl\b|good morning|hip thrust|hip hinge)\b", re.I),
     {"hamstring", "glute", "glutes", "posterior", "erector", "back"}),
]


def _db():
    url, name = "mongodb://localhost:27017", "test_database"
    env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env):
        for line in open(env, errors="ignore"):
            line = line.strip()
            if line.startswith("MONGO_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("DB_NAME="):
                name = line.split("=", 1)[1].strip().strip('"').strip("'")
    return MongoClient(url)[name]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def _field(d, *names):
    for n in names:
        v = d.get(n)
        if v not in (None, "", [], {}):
            return v
    return None


def audit(db) -> int:
    issues = 0
    byid = defaultdict(list)
    names = defaultdict(list)

    print("== COMPLETENESS ==")
    for col in COLLECTIONS:
        docs = list(db[col].find({}))
        miss = Counter()
        for d in docs:
            if d.get("id"):
                byid[d["id"]].append((col, d))
            if _field(d, "name"):
                names[_norm(d["name"])].append((col, d))
            for f, keys in [("name", ("name",)), ("category", ("category",)),
                            ("cues", ("coaching_cues", "instructions")), ("summary", ("summary", "definition"))]:
                if not _field(d, *keys):
                    miss[f] += 1
            if col != "mobility_drills" and not _field(d, "primary_muscles"):
                miss["primary_muscles"] += 1
        print(f"  {col}: {len(docs)} docs; missing={dict(miss) or 'none'}")
        issues += sum(miss.values())

    print("\n== DUPLICATE IDS ACROSS COLLECTIONS ==")
    dup = {i: v for i, v in byid.items() if len(v) > 1}
    print(f"  {len(dup)} ids shared across collections (dedup opportunity)")
    issues += len(dup)

    print("\n== NON-MOVEMENT ENTRIES (not real drills) ==")
    nm = list(db.mobility_drills.find({"category": {"$in": ["mobility_principles", "principle", "knowledge", "concept"]}}, {"name": 1}))
    print(f"  {len(nm)}: {[d.get('name') for d in nm][:8]}")
    issues += len(nm)

    print("\n== LIKELY MUSCLE MISLABELS (total mismatch of pattern vs primary_muscles) ==")
    seen, flagged = set(), []
    for col in COLLECTIONS:
        for d in db[col].find({"primary_muscles": {"$exists": True, "$ne": []}}, {"name": 1, "primary_muscles": 1}):
            name = str(d.get("name") or "")
            if _norm(name) in seen:
                continue
            pm = " ".join(str(m).lower() for m in (d.get("primary_muscles") or []))
            for label, rx, expected in MUSCLE_RULES:
                if rx.search(name):
                    if not any(e in pm for e in expected):
                        flagged.append((name, label, d.get("primary_muscles")))
                        seen.add(_norm(name))
                    break
    for name, label, pm in flagged:
        print(f"  [{label}] {name} -> {pm}")
    print(f"  ({len(flagged)} flagged)")
    issues += len(flagged)

    print("\n== LAZY MUSCLE LABELS (full_body as primary) ==")
    lazy = set()
    for col in COLLECTIONS:
        for d in db[col].find({"primary_muscles": {"$in": ["full_body", "fullbody", "whole_body", "general"]}}, {"name": 1}):
            lazy.add(d.get("name"))
    print(f"  {len(lazy)}: {sorted(lazy)}")
    issues += len(lazy)

    print("\n== PROGRESSION GRAPH ORPHANS ==")
    known = set()
    for col in COLLECTIONS:
        for d in db[col].find({}, {"name": 1, "id": 1}):
            known.add(_norm(d.get("name")))
            known.add(str(d.get("id")))
    orphans = 0
    for e in db.exercise_progression_graph.find({}):
        frm = e.get("from_exercise_name") or e.get("from_exercise_id") or e.get("from")
        to = e.get("to_exercise_name") or e.get("to_exercise_id") or e.get("to")
        if not ((_norm(frm) in known or str(frm) in known) and (_norm(to) in known or str(to) in known)):
            orphans += 1
    print(f"  {orphans} edges reference unknown exercises")
    issues += orphans

    print(f"\n== TOTAL FLAGGED ITEMS: {issues} ==")
    return issues


if __name__ == "__main__":
    audit(_db())

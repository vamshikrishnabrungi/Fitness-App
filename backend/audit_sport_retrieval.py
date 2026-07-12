from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.generate_sport_database_status_report import SPORT_COLLECTIONS, TEST_PROFILES
from backend.knowledge_retrieval import (
    build_generation_knowledge_context,
    compact_context_for_ai,
    retrieve_sport_teaching_context,
    _profile_sports,
    _sport_domains_for_profile,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "backend" / "SPORT_RETRIEVAL_AUDIT.json"

SPORT_EQUIVALENTS: Dict[str, Set[str]] = {
    "soccer": {"soccer", "football", "soccer_football"},
    "football": {"soccer", "football", "soccer_football"},
    "running_endurance": {"running_endurance", "running", "runner"},
}


def _allowed_sports(sports: List[str]) -> Set[str]:
    allowed: Set[str] = set(sports)
    for sport in sports:
        allowed.update(SPORT_EQUIVALENTS.get(sport, {sport}))
    return allowed


def _record_sport(record: Dict[str, Any]) -> str | None:
    value = record.get("sport")
    return str(value).strip().lower() if value else None


def _record_applies_to(record: Dict[str, Any]) -> Set[str]:
    value = record.get("applies_to") or []
    items = value if isinstance(value, list) else [value]
    return {str(item).strip().lower() for item in items if str(item).strip()}


async def _collection_count(db: Any, collection: str, sports: List[str]) -> int:
    allowed = sorted(_allowed_sports(sports))
    if not allowed:
        return 0
    if collection == "planning_rules":
        query = {"$or": [{"sport": {"$in": allowed}}, {"applies_to": {"$in": allowed}}]}
    else:
        query = {"sport": {"$in": allowed}}
    return await db[collection].count_documents(query)


async def _audit_profile(db: Any, profile_name: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    sports = _profile_sports(profile)
    allowed_sports = _allowed_sports(sports)
    domains = _sport_domains_for_profile(profile)
    sport_counts = {
        collection: await _collection_count(db, collection, sports)
        for collection in SPORT_COLLECTIONS
    }

    teaching = await retrieve_sport_teaching_context(db, profile)
    context = await build_generation_knowledge_context(db, profile)
    compact = compact_context_for_ai(context)

    issues: List[str] = []

    if not sports:
        issues.append("profile did not normalize to any sport")

    sport_teaching = compact.get("sport_teaching_context") or {}
    for section_key in ("teaching_progressions", "skill_assessments", "level_transition_rules"):
        for record in sport_teaching.get(section_key) or []:
            record_sport = _record_sport(record)
            if record_sport and record_sport not in allowed_sports:
                issues.append(f"{section_key} leaked sport={record_sport} id={record.get('id')}")

    sport_specific_programming = []
    for record in compact.get("programming_rules") or []:
        record_sport = _record_sport(record)
        applies_to = _record_applies_to(record)
        if record_sport and record_sport not in allowed_sports:
            issues.append(f"programming_rules leaked sport={record_sport} id={record.get('id')}")
        if record_sport in allowed_sports or applies_to.intersection(allowed_sports):
            sport_specific_programming.append(record)

    available_sport_rules = sport_counts.get("sport_training_rules", 0) + sport_counts.get("planning_rules", 0)
    if available_sport_rules > 0 and not sport_specific_programming:
        issues.append("compact programming_rules did not include any sport-specific rule despite available sport rules")

    if sport_counts.get("sport_profiles", 0) > 0 and not any(
        (record.get("sport") in allowed_sports)
        for record in teaching.get("teaching_progressions", []) + teaching.get("skill_assessments", [])
    ):
        issues.append("sport teaching retrieval returned no profile-matched progressions or assessments")

    return {
        "profile": profile_name,
        "sports": sports,
        "allowed_sports": sorted(allowed_sports),
        "domain_count": len(domains),
        "first_domains": domains[:20],
        "collection_counts": sport_counts,
        "compact_programming_rule_ids": [record.get("id") for record in (compact.get("programming_rules") or [])],
        "compact_programming_rule_sports": [record.get("sport") for record in (compact.get("programming_rules") or [])],
        "teaching_counts": {
            "teaching_progressions": len(teaching.get("teaching_progressions") or []),
            "skill_assessments": len(teaching.get("skill_assessments") or []),
            "level_transition_rules": len(teaching.get("level_transition_rules") or []),
        },
        "compact_teaching_counts": {
            key: len(sport_teaching.get(key) or [])
            for key in ("teaching_progressions", "skill_assessments", "level_transition_rules")
        },
        "issues": issues,
        "status": "pass" if not issues else "fail",
    }


async def audit() -> Dict[str, Any]:
    load_dotenv(ROOT / "backend" / ".env")
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        profiles = [
            await _audit_profile(db, profile_name, profile)
            for profile_name, profile in TEST_PROFILES.items()
        ]
        failures = [profile for profile in profiles if profile["status"] != "pass"]
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "database": db_name,
            "profile_count": len(profiles),
            "failure_count": len(failures),
            "status": "pass" if not failures else "fail",
            "profiles": profiles,
        }
        OUTPUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report
    finally:
        client.close()


def main() -> None:
    report = asyncio.run(audit())
    print(json.dumps({
        "output_path": str(OUTPUT_PATH),
        "status": report["status"],
        "profile_count": report["profile_count"],
        "failure_count": report["failure_count"],
        "failures": [
            {"profile": item["profile"], "issues": item["issues"]}
            for item in report["profiles"]
            if item["issues"]
        ],
    }, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

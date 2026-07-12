from __future__ import annotations

import argparse
import asyncio
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.ai_workout_service import generate_ai_training_program
from backend.generate_sport_database_status_report import TEST_PROFILES
from backend.knowledge_retrieval import build_generation_knowledge_context, compact_context_for_ai, _profile_sports


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "backend" / "sport_generation_samples"
SUMMARY_PATH = OUTPUT_DIR / "sample_generation_summary.json"

DEFAULT_PROFILE_ORDER = [
    "cricket_beginner_batter",
    "volleyball_intermediate_outside_hitter",
    "football_intermediate_winger",
    "basketball_beginner_point_guard",
    "boxing_beginner_out_boxer",
    "kickboxing_beginner_k1",
    "mma_beginner_generalist",
    "wrestling_beginner_freestyle",
    "running_beginner_5k",
    "badminton_intermediate_doubles",
    "tennis_intermediate_all_court",
    "swimming_beginner_fitness",
    "cycling_beginner_fitness",
]


def _model_dump(value: Any) -> Dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _sample_profile(profile_name: str) -> Dict[str, Any]:
    profile = deepcopy(TEST_PROFILES[profile_name])
    profile["user_id"] = f"sample_{profile_name}"
    profile["training_days_per_week"] = 1
    profile["preferred_training_days"] = ["Monday"]
    profile["session_duration_min"] = min(60, int(profile.get("session_duration_min") or 60))
    profile.setdefault("sleep_avg_hours", 7)
    profile.setdefault("stress_level", "moderate")
    return profile


async def _generate_one(
    db: Any,
    profile_name: str,
    *,
    anthropic_key: str | None,
    openrouter_key: str | None,
    model: str,
) -> Dict[str, Any]:
    profile = _sample_profile(profile_name)
    knowledge_context = compact_context_for_ai(await build_generation_knowledge_context(db, profile))
    result = await generate_ai_training_program(
        profile,
        knowledge_context=knowledge_context,
        anthropic_key=anthropic_key,
        openrouter_key=openrouter_key,
        model=model,
        max_weeks=1,
        max_attempts=1,
        strict_library_matches=False,
    )
    program = _model_dump(result["program"])
    workouts = ((program.get("weeks") or [{}])[0].get("workouts") or [])
    output = {
        "profile_name": profile_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "source": result.get("source"),
        "sports": _profile_sports(profile),
        "input_profile": profile,
        "knowledge_context_summary": {
            "programming_rule_ids": [item.get("id") for item in knowledge_context.get("programming_rules", [])],
            "teaching_progression_ids": [
                item.get("id")
                for item in (knowledge_context.get("sport_teaching_context") or {}).get("teaching_progressions", [])
            ],
            "assessment_ids": [
                item.get("id")
                for item in (knowledge_context.get("sport_teaching_context") or {}).get("skill_assessments", [])
            ],
        },
        "program": program,
        "workout_titles": [workout.get("title") for workout in workouts],
    }
    output_path = OUTPUT_DIR / f"{profile_name}.json"
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "profile_name": profile_name,
        "status": "pass",
        "output_path": str(output_path),
        "sports": output["sports"],
        "workout_titles": output["workout_titles"],
        "programming_rule_ids": output["knowledge_context_summary"]["programming_rule_ids"],
    }


async def generate_samples(profile_names: List[str]) -> Dict[str, Any]:
    load_dotenv(ROOT / "backend" / ".env")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    model = os.environ.get("WORKOUT_AI_MODEL", "claude-haiku-4-5-20251001")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    client = AsyncIOMotorClient(mongo_url)
    results: List[Dict[str, Any]] = []
    try:
        db = client[db_name]
        for profile_name in profile_names:
            try:
                results.append(
                    await _generate_one(
                        db,
                        profile_name,
                        anthropic_key=anthropic_key,
                        openrouter_key=openrouter_key,
                        model=model,
                    )
                )
            except Exception as exc:
                results.append({
                    "profile_name": profile_name,
                    "status": "fail",
                    "error": str(exc),
                })
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "database": db_name,
            "requested_profiles": profile_names,
            "success_count": len([item for item in results if item["status"] == "pass"]),
            "failure_count": len([item for item in results if item["status"] != "pass"]),
            "results": results,
        }
        SUMMARY_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report
    finally:
        client.close()


def _parse_profile_names(raw: str | None, limit: int | None) -> List[str]:
    if raw:
        names = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        names = list(DEFAULT_PROFILE_ORDER)
    unknown = [name for name in names if name not in TEST_PROFILES]
    if unknown:
        raise SystemExit(f"Unknown profile name(s): {', '.join(unknown)}")
    return names[:limit] if limit else names


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one real AI workout sample per sport profile.")
    parser.add_argument("--profiles", help="Comma-separated TEST_PROFILES keys. Defaults to all single-sport major profiles.")
    parser.add_argument("--limit", type=int, help="Optional number of profiles to run from the selected list.")
    args = parser.parse_args()
    profile_names = _parse_profile_names(args.profiles, args.limit)
    report = asyncio.run(generate_samples(profile_names))
    print(json.dumps({
        "summary_path": str(SUMMARY_PATH),
        "model": report["model"],
        "success_count": report["success_count"],
        "failure_count": report["failure_count"],
        "results": report["results"],
    }, indent=2))
    if report["failure_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

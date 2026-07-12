from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.knowledge_retrieval import (
    build_generation_knowledge_context,
    compact_context_for_ai,
    retrieve_sport_teaching_context,
)
from backend.macro_plan_service import create_user_macro_plan


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "backend" / "SPORT_DATABASE_STATUS_REPORT.md"

SPORTS = ["cricket", "volleyball", "soccer", "basketball", "boxing", "kickboxing", "mma", "wrestling", "running_endurance", "badminton", "tennis", "swimming", "cycling"]
SPORT_COLLECTIONS = [
    "sport_profiles",
    "sport_roles",
    "sport_training_rules",
    "planning_rules",
    "sport_teaching_progressions",
    "sport_skill_assessments",
    "sport_level_transition_rules",
]


TEST_PROFILES: Dict[str, Dict[str, Any]] = {
    "cricket_beginner_batter": {
        "user_id": "report_cricket_beginner_batter",
        "sports": ["Cricket"],
        "sport_details": [{"sport": "Cricket", "role": "Batter"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "barbell", "cable machine"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": [],
        "current_injuries": [],
    },
    "volleyball_intermediate_outside_hitter": {
        "user_id": "report_volleyball_intermediate_outside",
        "sports": ["Volleyball"],
        "sport_details": [{"sport": "Volleyball", "role": "Outside Hitter"}],
        "experience": "intermediate",
        "selected_goals": ["Sport Performance", "Jump Higher"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "barbell", "bands"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["knee"],
        "current_injuries": [{"area": "knee", "severity": "mild", "note": "occasional landing discomfort"}],
    },
    "football_intermediate_winger": {
        "user_id": "report_football_intermediate_winger",
        "sports": ["Football"],
        "sport_details": [{"sport": "Football", "role": "Winger"}],
        "experience": "intermediate",
        "selected_goals": ["Sport Performance", "Run Fast"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "barbell", "sled", "turf"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["hamstring"],
        "current_injuries": [{"area": "hamstring", "severity": "mild", "note": "previous tightness"}],
    },
    "basketball_beginner_point_guard": {
        "user_id": "report_basketball_beginner_pg",
        "sports": ["Basketball"],
        "sport_details": [{"sport": "Basketball", "role": "Point Guard"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance", "Conditioning"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "bands", "court"],
        "training_days_per_week": 3,
        "session_duration_min": 60,
        "pain_areas": ["ankle"],
        "current_injuries": [{"area": "ankle", "severity": "mild", "note": "history of rolling ankle"}],
    },
    "boxing_beginner_out_boxer": {
        "user_id": "report_boxing_beginner_out_boxer",
        "sports": ["Boxing"],
        "sport_details": [{"sport": "Boxing", "style": "Out Boxer"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance", "Conditioning"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "bands", "heavy bag"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["shoulder"],
        "current_injuries": [{"area": "shoulder", "severity": "mild", "note": "occasional bag-work irritation"}],
    },
    "kickboxing_beginner_k1": {
        "user_id": "report_kickboxing_beginner_k1",
        "sports": ["Kickboxing"],
        "sport_details": [{"sport": "Kickboxing", "role": "Beginner Kickboxer", "style": "K1 Fighter"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance", "Conditioning"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "bands", "heavy bag", "pads"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["knee"],
        "current_injuries": [{"area": "knee", "severity": "mild", "note": "occasional discomfort after kicking"}],
    },
    "mma_beginner_generalist": {
        "user_id": "report_mma_beginner_generalist",
        "sports": ["MMA"],
        "sport_details": [{"sport": "MMA", "role": "Beginner MMA"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance", "Conditioning"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "bands", "heavy bag", "mat"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["shoulder"],
        "current_injuries": [{"area": "shoulder", "severity": "mild", "note": "occasional irritation after striking"}],
    },
    "wrestling_beginner_freestyle": {
        "user_id": "report_wrestling_beginner_freestyle",
        "sports": ["Wrestling"],
        "sport_details": [{"sport": "Wrestling", "role": "Beginner Wrestler", "style": "Freestyle"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance", "Strength"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "barbell", "mat"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["knee"],
        "current_injuries": [{"area": "knee", "severity": "mild", "note": "occasional discomfort on shots"}],
    },
    "running_beginner_5k": {
        "user_id": "report_running_beginner_5k",
        "sports": ["Running"],
        "sport_details": [{"sport": "Running", "role": "5K"}],
        "experience": "beginner",
        "selected_goals": ["Sport Performance", "Endurance"],
        "primary_goal": "5K",
        "training_location": "outdoors",
        "equipment": ["running shoes"],
        "training_days_per_week": 4,
        "session_duration_min": 45,
        "pain_areas": ["shin"],
        "current_injuries": [{"area": "shin", "severity": "mild", "note": "previous shin soreness"}],
    },
    "badminton_intermediate_doubles": {
        "user_id": "report_badminton_intermediate_doubles",
        "sports": ["Badminton"],
        "sport_details": [{"sport": "Badminton", "role": "Doubles"}],
        "experience": "intermediate",
        "selected_goals": ["Sport Performance", "Agility"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "bands", "court"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["shoulder"],
        "current_injuries": [{"area": "shoulder", "severity": "mild", "note": "occasional soreness after smashes"}],
    },
    "tennis_intermediate_all_court": {
        "user_id": "report_tennis_intermediate_all_court",
        "sports": ["Tennis"],
        "sport_details": [{"sport": "Tennis", "role": "All Court Player"}],
        "experience": "intermediate",
        "selected_goals": ["Sport Performance", "Agility"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "bands", "court", "medicine ball"],
        "training_days_per_week": 4,
        "session_duration_min": 60,
        "pain_areas": ["shoulder"],
        "current_injuries": [{"area": "shoulder", "severity": "mild", "note": "occasional soreness after serving"}],
    },
    "swimming_beginner_fitness": {
        "user_id": "report_swimming_beginner_fitness",
        "sports": ["Swimming"],
        "sport_details": [{"sport": "Swimming", "role": "Beginner Swimmer"}],
        "experience": "beginner",
        "selected_goals": ["General Fitness", "Endurance"],
        "primary_goal": "General Fitness",
        "training_location": "pool",
        "equipment": ["pool", "kickboard"],
        "training_days_per_week": 3,
        "session_duration_min": 45,
        "pain_areas": ["shoulder"],
        "current_injuries": [{"area": "shoulder", "severity": "mild", "note": "occasional discomfort after swimming"}],
    },
    "cycling_beginner_fitness": {
        "user_id": "report_cycling_beginner_fitness",
        "sports": ["Cycling"],
        "sport_details": [{"sport": "Cycling", "role": "Fitness Cyclist"}],
        "experience": "beginner",
        "selected_goals": ["General Fitness", "Endurance"],
        "primary_goal": "General Fitness",
        "training_location": "outdoors",
        "equipment": ["bike", "helmet"],
        "training_days_per_week": 3,
        "session_duration_min": 45,
        "pain_areas": ["knee"],
        "current_injuries": [{"area": "knee", "severity": "mild", "note": "occasional discomfort on hills"}],
    },
    "hybrid_cricket_basketball_intermediate": {
        "user_id": "report_hybrid_cricket_basketball",
        "sports": ["Cricket", "Basketball"],
        "sport_details": [
            {"sport": "Cricket", "role": "Batter"},
            {"sport": "Basketball", "role": "Wing"},
        ],
        "experience": "intermediate",
        "selected_goals": ["Sport Performance", "Build Muscle"],
        "primary_goal": "Sport Performance",
        "training_location": "gym",
        "equipment": ["dumbbells", "barbell", "bands", "court", "nets"],
        "training_days_per_week": 4,
        "session_duration_min": 75,
        "pain_areas": ["knee"],
        "current_injuries": [{"area": "knee", "severity": "mild", "note": "occasional discomfort"}],
    },
}


def _strip_mongo(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in doc.items() if key != "_id"}


def _first_ids(records: Sequence[Dict[str, Any]], limit: int = 5) -> List[str]:
    return [str(record.get("id") or record.get("name") or "") for record in records[:limit]]


async def _collection_count(db: Any, collection: str, sport: str) -> int:
    sport_values = [sport]
    if sport == "soccer":
        sport_values.append("soccer_football")
    if sport == "running_endurance":
        sport_values.extend(["running", "runner"])
    if collection in {"planning_rules"}:
        query = {
            "$or": [
                {"sport": {"$in": sport_values}},
                {"applies_to": {"$in": sport_values}},
            ]
        }
    else:
        query = {"sport": {"$in": sport_values}}
    return await db[collection].count_documents(query)


async def _sport_counts(db: Any) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
    for sport in SPORTS:
        counts[sport] = {}
        for collection in SPORT_COLLECTIONS:
            counts[sport][collection] = await _collection_count(db, collection, sport)
    return counts


async def _source_pack_counts(db: Any) -> List[Dict[str, Any]]:
    packs = await db.source_registry.find({}).sort("source_book_id", 1).to_list(100)
    output = []
    for pack in packs:
        source_book_id = pack.get("source_book_id") or pack.get("id")
        output.append(
            {
                "source_book_id": source_book_id,
                "title": pack.get("title"),
                "source_sections": await db.source_sections.count_documents({"source_book_id": source_book_id}),
                "knowledge_sources": await db.knowledge_sources.count_documents(
                    {
                        "$or": [
                            {"id": source_book_id},
                            {"source_book_id": source_book_id},
                        ]
                    }
                ),
            }
        )
    return output


async def _retrieval_result(db: Any, profile: Dict[str, Any]) -> Dict[str, Any]:
    sport_context = await retrieve_sport_teaching_context(
        db,
        profile,
        progression_limit=6,
        assessment_limit=3,
        transition_limit=3,
    )
    generation_context = await build_generation_knowledge_context(
        db,
        profile,
        limits={
            "primary_exercises": 15,
            "variations": 4,
            "progression_paths": 6,
            "programming_rules": 6,
            "sport_teaching_progressions": 6,
            "sport_skill_assessments": 3,
            "sport_level_transition_rules": 3,
            "source_refs": 10,
        },
    )
    compact = compact_context_for_ai(generation_context)
    return {
        "sport_teaching_counts": {
            "teaching_progressions": len(sport_context["teaching_progressions"]),
            "skill_assessments": len(sport_context["skill_assessments"]),
            "level_transition_rules": len(sport_context["level_transition_rules"]),
        },
        "generation_counts": generation_context.get("counts", {}),
        "top_teaching_progressions": _first_ids(sport_context["teaching_progressions"]),
        "top_skill_assessments": _first_ids(sport_context["skill_assessments"]),
        "top_transition_rules": _first_ids(sport_context["level_transition_rules"]),
        "allowed_primary_exercises": _first_ids(compact.get("allowed_primary_exercises") or []),
        "allowed_variations": _first_ids(compact.get("allowed_variations") or []),
        "sport_teaching_compact_counts": {
            key: len(value or [])
            for key, value in (compact.get("sport_teaching_context") or {}).items()
        },
    }


async def _macro_plan_smoke_test(db: Any, profile: Dict[str, Any]) -> Dict[str, Any]:
    user_id = "report_macro_plan_smoke_test"
    await db.macro_plans.delete_many({"user_id": user_id})
    await db.athlete_states.delete_many({"user_id": user_id})
    plan = await create_user_macro_plan(db, user_id=user_id, profile=profile, status="test")
    await db.macro_plans.delete_many({"user_id": user_id})
    await db.athlete_states.delete_many({"user_id": user_id})
    return {
        "template_id": plan.get("template_id"),
        "template_name": plan.get("template_name"),
        "duration_weeks": plan.get("duration_weeks"),
        "sports": plan.get("sports"),
        "phase_count": len(plan.get("phases") or []),
        "planning_rule_count": len(plan.get("planning_rules") or []),
        "competition_week_rule_count": len(plan.get("competition_week_rules") or []),
        "assumptions": plan.get("assumptions") or [],
    }


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _format_report(
    *,
    generated_at: str,
    sport_counts: Dict[str, Dict[str, int]],
    source_counts: List[Dict[str, Any]],
    retrieval_results: Dict[str, Dict[str, Any]],
    macro_plan: Dict[str, Any],
) -> str:
    rows = [
        [
            sport,
            counts["sport_profiles"],
            counts["sport_roles"],
            counts["sport_training_rules"],
            counts["planning_rules"],
            counts["sport_teaching_progressions"],
            counts["sport_skill_assessments"],
            counts["sport_level_transition_rules"],
        ]
        for sport, counts in sport_counts.items()
    ]
    source_rows = [
        [
            item["source_book_id"],
            item["title"],
            item["source_sections"],
            item["knowledge_sources"],
        ]
        for item in source_counts
    ]

    lines = [
        "# Sport Database Status Report",
        "",
        f"Generated: {generated_at}",
        "",
        "This report checks the current app-facing sport teaching database and retrieval layer. It does not call an AI model.",
        "",
        "## Source Packs",
        "",
        _markdown_table(["source_book_id", "title", "source_sections", "knowledge_sources"], source_rows),
        "",
        "## Sport Collection Counts",
        "",
        _markdown_table(
            [
                "sport",
                "profiles",
                "roles",
                "training_rules",
                "planning_rules",
                "teaching_progressions",
                "skill_assessments",
                "transition_rules",
            ],
            rows,
        ),
        "",
        "## Retrieval Smoke Tests",
        "",
    ]

    for name, result in retrieval_results.items():
        counts = result["generation_counts"]
        lines.extend(
            [
                f"### {name}",
                "",
                f"- sport teaching counts: `{result['sport_teaching_counts']}`",
                f"- generation counts: `{counts}`",
                f"- top progressions: `{result['top_teaching_progressions']}`",
                f"- top assessments: `{result['top_skill_assessments']}`",
                f"- top transition rules: `{result['top_transition_rules']}`",
                f"- compact primary exercises: `{result['allowed_primary_exercises']}`",
                f"- compact variations: `{result['allowed_variations']}`",
                f"- compact sport teaching counts: `{result['sport_teaching_compact_counts']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Macro Plan Smoke Test",
            "",
            f"- template: `{macro_plan.get('template_id')}` / `{macro_plan.get('template_name')}`",
            f"- duration weeks: `{macro_plan.get('duration_weeks')}`",
            f"- sports: `{macro_plan.get('sports')}`",
            f"- phases: `{macro_plan.get('phase_count')}`",
            f"- planning rules: `{macro_plan.get('planning_rule_count')}`",
            f"- competition week rules: `{macro_plan.get('competition_week_rule_count')}`",
            f"- assumptions: `{macro_plan.get('assumptions')}`",
            "",
            "## Read",
            "",
            "- All retrieval test profiles should return sport teaching progressions, assessments, and transition rules.",
            "- Football is stored as `soccer` internally and retrieved through the football alias.",
            "- The compact context intentionally shows only selected IDs/names. Full descriptions are hydrated from Mongo later.",
        ]
    )
    return "\n".join(lines) + "\n"


async def main() -> None:
    load_dotenv(ROOT / "backend" / ".env")
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        sport_counts = await _sport_counts(db)
        source_counts = await _source_pack_counts(db)
        retrieval_results = {
            name: await _retrieval_result(db, profile)
            for name, profile in TEST_PROFILES.items()
        }
        macro_plan = await _macro_plan_smoke_test(
            db,
            TEST_PROFILES["hybrid_cricket_basketball_intermediate"],
        )
        report = _format_report(
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            sport_counts=sport_counts,
            source_counts=source_counts,
            retrieval_results=retrieval_results,
            macro_plan=macro_plan,
        )
        OUTPUT_PATH.write_text(report, encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())

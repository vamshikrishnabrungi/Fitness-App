from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend.club_domain import (
    CLUB_EDGE_MEMBER_CAP,
    MIN_EDGE_COVERAGE,
    MIN_MATCH_CONFIDENCE,
    aggregate_club_edge_score,
    choose_controller,
    score_controller_traversals,
    territory_daily_points,
)
from backend.platform_ids import uuid7
from backend.territory_engine import (
    normalized_valhalla_confidence,
    valhalla_way_ids,
)


def test_uuid7_is_rfc_version_seven_and_time_sortable():
    first = uuid7()
    second = uuid7()
    assert first.version == 7
    assert second.version == 7
    assert first.int < second.int


def test_territory_thresholds_reject_unverified_edge_coverage():
    assert (
        territory_daily_points(
            confidence=MIN_MATCH_CONFIDENCE - 0.01,
            coverage=1,
            age_days=0,
        )
        == 0
    )
    assert (
        territory_daily_points(
            confidence=1,
            coverage=MIN_EDGE_COVERAGE - 0.01,
            age_days=0,
        )
        == 0
    )
    assert territory_daily_points(confidence=1, coverage=1, age_days=0) == 100
    assert territory_daily_points(confidence=1, coverage=1, age_days=14) == 50
    assert territory_daily_points(confidence=1, coverage=1, age_days=28) == 0


def test_territory_uses_one_best_effort_per_day_and_only_seven_days():
    now = datetime(2026, 7, 28, 12, tzinfo=timezone.utc)
    traversals = []
    for day_ago in range(10):
        activity_time = now - timedelta(days=day_ago)
        traversals.extend(
            [
                {
                    "local_activity_date": activity_time.date(),
                    "matched_at": activity_time,
                    "coverage": 0.9,
                    "confidence": 0.9,
                    "elapsed_time_sec": 60,
                    "qualified": True,
                },
                {
                    "local_activity_date": activity_time.date(),
                    "matched_at": activity_time,
                    "coverage": 1,
                    "confidence": 1,
                    "elapsed_time_sec": 55,
                    "qualified": True,
                },
            ]
        )
    score = score_controller_traversals(traversals, now=now)
    assert score["scoring_days"] == 7
    assert len(score["selected"]) == 7
    assert all(item["coverage"] == 1 for item in score["selected"])
    assert score["fastest_time_sec"] == 55
    assert score["expires_at"] == now + timedelta(days=28)


def test_club_edge_score_caps_raw_membership_advantage():
    scores = [
        {
            "controller_id": f"member-{index}",
            "score": float(100 - index),
            "fastest_time_sec": float(60 + index),
            "expires_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
        }
        for index in range(12)
    ]
    club = aggregate_club_edge_score(scores)
    assert club["member_count"] == CLUB_EDGE_MEMBER_CAP
    assert club["score"] == sum(100 - index for index in range(CLUB_EDGE_MEMBER_CAP))


def test_controller_tie_breaks_on_fastest_verified_effort():
    winner = choose_controller(
        [
            {"controller_id": "slow", "score": 250, "fastest_time_sec": 70},
            {"controller_id": "fast", "score": 250, "fastest_time_sec": 60},
        ]
    )
    assert winner
    assert winner["controller_id"] == "fast"


def test_controller_final_tie_break_is_earliest_score_reached():
    early = datetime(2026, 7, 27, tzinfo=timezone.utc)
    late = datetime(2026, 7, 28, tzinfo=timezone.utc)
    winner = choose_controller(
        [
            {
                "controller_id": "late",
                "score": 250,
                "fastest_time_sec": 60,
                "score_reached_at": late,
            },
            {
                "controller_id": "early",
                "score": 250,
                "fastest_time_sec": 60,
                "score_reached_at": early,
            },
        ]
    )
    assert winner
    assert winner["controller_id"] == "early"


def test_valhalla_response_is_normalized_without_mapbox_matching():
    result = {
        "confidence_score": 92,
        "edges": [{"way_id": 101}, {"way_id": "101"}, {"way_id": 202}],
    }
    assert normalized_valhalla_confidence(result) == pytest.approx(0.92)
    assert valhalla_way_ids(result) == [101, 202]


def test_competition_migration_declares_single_sources_and_constraints():
    migration = (
        Path(__file__).resolve().parents[1]
        / "backend"
        / "migrations"
        / "002_run_club_competition_platform.sql"
    ).read_text(encoding="utf-8")
    assert "UNIQUE (club_id, user_id)" in migration
    assert "club_one_active_owner_idx" in migration
    assert "activity_id UUID PRIMARY KEY" in migration
    assert "activity_club_attributions" in migration
    assert "territory_current_control" in migration
    assert "controller_type controller_type" in migration
    assert "idempotency_records" in migration
    assert "idempotency_key TEXT NOT NULL UNIQUE" in migration
    assert "public_route GEOMETRY(MultiLineString, 4326)" in migration
    assert "public_competition_eligible BOOLEAN NOT NULL DEFAULT FALSE" in migration
    assert "territory_history_source_identity_idx" in migration
    assert "notifications_outbox_recipient_idx" in migration
    assert "moderation_appeals" in migration
    assert "athlete_one_open_primary_history_idx" in migration


def test_expired_and_future_traversals_cannot_score():
    now = datetime(2026, 7, 28, 12, tzinfo=timezone.utc)
    score = score_controller_traversals(
        [
            {
                "local_activity_date": (now - timedelta(days=28)).date(),
                "matched_at": now - timedelta(days=28),
                "coverage": 1,
                "confidence": 1,
                "elapsed_time_sec": 50,
                "qualified": True,
            },
            {
                "local_activity_date": (now + timedelta(days=1)).date(),
                "matched_at": now + timedelta(days=1),
                "coverage": 1,
                "confidence": 1,
                "elapsed_time_sec": 50,
                "qualified": True,
            },
        ],
        now=now,
    )
    assert score["score"] == 0
    assert score["scoring_days"] == 0


def test_reprocessing_does_not_refresh_an_old_territory_effort():
    now = datetime(2026, 7, 28, 12, tzinfo=timezone.utc)
    activity_started_at = now - timedelta(days=20)
    score = score_controller_traversals(
        [
            {
                "local_activity_date": activity_started_at.date(),
                "activity_started_at": activity_started_at,
                # A retry may map the activity today, but decay must still use
                # the time the athlete actually ran.
                "matched_at": now,
                "coverage": 1,
                "confidence": 1,
                "elapsed_time_sec": 50,
                "qualified": True,
            }
        ],
        now=now,
    )
    assert score["score"] == territory_daily_points(
        confidence=1,
        coverage=1,
        age_days=20,
    )
    assert score["expires_at"] == activity_started_at + timedelta(days=28)

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from sqlalchemy import text

from backend.club_domain import (
    MIN_EDGE_COVERAGE,
    MIN_MATCH_CONFIDENCE,
    MIN_TERRITORY_ACTIVITY_M,
    TERRITORY_WINDOW_DAYS,
    aggregate_club_edge_score,
    choose_controller,
    score_controller_traversals,
)
from backend.geo_db import get_geo_engine
from backend.platform_ids import new_id


logger = logging.getLogger(__name__)
VALHALLA_URL = (os.environ.get("VALHALLA_URL") or "").rstrip("/")
MATCHER_VERSION = os.environ.get("TERRITORY_MATCHER_VERSION", "valhalla-v1")


class TerritoryMatcherUnavailable(RuntimeError):
    pass


def _shape(stream: Iterable[Dict[str, Any]]) -> List[Dict[str, float]]:
    shape = []
    for point in stream:
        try:
            lat = float(point["latitude"])
            lon = float(point["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            shape.append({"lat": lat, "lon": lon})
    return shape


async def valhalla_trace_attributes(stream: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not VALHALLA_URL:
        raise TerritoryMatcherUnavailable("VALHALLA_URL is not configured")
    shape = _shape(stream)
    if len(shape) < 2:
        return {"edges": [], "confidence_score": 0.0}
    payload = {
        "shape": shape,
        "costing": "pedestrian",
        "shape_match": "map_snap",
        "filters": {
            "attributes": [
                "edge.way_id",
                "edge.begin_shape_index",
                "edge.end_shape_index",
                "edge.length",
                "edge.speed",
                "matched.point",
            ],
            "action": "include",
        },
        "trace_options": {
            "search_radius": 50,
            "gps_accuracy": 15,
            "breakage_distance": 100,
        },
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(f"{VALHALLA_URL}/trace_attributes", json=payload)
        response.raise_for_status()
        return response.json()


def normalized_valhalla_confidence(result: Dict[str, Any]) -> float:
    raw = result.get("confidence_score")
    if raw is None:
        raw_score = float(result.get("raw_score") or 0)
        return max(0.0, min(1.0, 1.0 / (1.0 + raw_score / 10.0)))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    # Valhalla confidence is normally 0..1. Guard older builds returning percentages.
    if value > 1:
        value /= 100.0
    return max(0.0, min(1.0, value))


def valhalla_way_ids(result: Dict[str, Any]) -> List[int]:
    way_ids = []
    for edge in result.get("edges") or []:
        value = edge.get("way_id")
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed not in way_ids:
            way_ids.append(parsed)
    return way_ids


async def match_activity_to_edges(activity: Dict[str, Any]) -> Dict[str, Any]:
    engine = get_geo_engine()
    if engine is None:
        raise TerritoryMatcherUnavailable("PostGIS is not configured")
    distance_m = float(
        activity.get("distance_m")
        or float(activity.get("distance_km") or 0) * 1000
    )
    if distance_m < MIN_TERRITORY_ACTIVITY_M:
        return {"status": "not_eligible", "traversals": [], "reason": "minimum_distance"}
    if not activity.get("leaderboard_eligible"):
        return {"status": "not_eligible", "traversals": [], "reason": "activity_quality"}

    result = await valhalla_trace_attributes(activity.get("cleaned_stream") or [])
    confidence = normalized_valhalla_confidence(result)
    way_ids = valhalla_way_ids(result)
    if confidence < MIN_MATCH_CONFIDENCE or not way_ids:
        return {
            "status": "failed_match",
            "traversals": [],
            "reason": "low_confidence" if way_ids else "no_matched_edges",
            "confidence": confidence,
        }

    started_at = activity.get("started_at") or activity.get("start_time")
    if isinstance(started_at, str):
        started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    if not isinstance(started_at, datetime):
        started_at = datetime.now(timezone.utc)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    async with engine.begin() as connection:
        rows = await connection.execute(
            text(
                """
                WITH activity AS (
                    SELECT public_route AS route
                    FROM activities
                    WHERE id = CAST(:activity AS uuid)
                )
                SELECT e.id AS street_edge_id, e.graph_version_id, e.distance_m,
                       LEAST(
                           1.0,
                           ST_Length(
                               ST_Intersection(
                                   ST_Transform(e.edge, 3857),
                                   ST_Buffer(ST_Transform(activity.route, 3857), 20)
                               )
                           ) / NULLIF(ST_Length(ST_Transform(e.edge, 3857)), 0)
                       ) AS coverage
                FROM street_edges e
                CROSS JOIN activity
                WHERE e.status = 'active'
                  AND e.osm_way_id = ANY(:way_ids)
                  AND activity.route IS NOT NULL
                  AND ST_DWithin(e.edge::geography, activity.route::geography, 50)
                """
            ),
            {"activity": activity["id"], "way_ids": way_ids},
        )
        attribution_row = (
            await connection.execute(
                text(
                    """
                    SELECT attribution.club_id, activity.local_timezone,
                           club.timezone AS club_timezone
                    FROM activities activity
                    LEFT JOIN activity_club_attributions attribution
                      ON attribution.activity_id=activity.id
                    LEFT JOIN clubs club ON club.id=attribution.club_id
                    WHERE activity.id=CAST(:activity AS uuid)
                    """
                ),
                {"activity": activity["id"]},
            )
        ).first()
        attribution = attribution_row.club_id if attribution_row else None
        local_timezone = (
            attribution_row.local_timezone
            if attribution_row and attribution_row.local_timezone
            else attribution_row.club_timezone
            if attribution_row and attribution_row.club_timezone
            else "UTC"
        )
        try:
            local_activity_date = started_at.astimezone(ZoneInfo(local_timezone)).date()
        except ZoneInfoNotFoundError:
            local_activity_date = started_at.date()
        traversals = []
        for row in rows:
            coverage = max(0.0, min(1.0, float(row.coverage or 0)))
            qualified = coverage >= MIN_EDGE_COVERAGE and confidence >= MIN_MATCH_CONFIDENCE
            elapsed = max(
                1.0,
                float(activity.get("moving_time_sec") or activity.get("elapsed_time_sec") or 1)
                * (float(row.distance_m or 0) / max(distance_m, 1)),
            )
            traversal = {
                "id": new_id(),
                "activity_id": activity["id"],
                "street_edge_id": row.street_edge_id,
                "user_id": activity["user_id"],
                "club_id": str(attribution) if attribution else None,
                "graph_version_id": str(row.graph_version_id) if row.graph_version_id else None,
                "local_activity_date": local_activity_date,
                "coverage": coverage,
                "confidence": confidence,
                "distance_m": float(row.distance_m or 0),
                "elapsed_time_sec": elapsed,
                "speed_mps": float(row.distance_m or 0) / elapsed,
                "qualified": qualified,
                "rejection_reasons": [] if qualified else ["insufficient_edge_coverage"],
            }
            await connection.execute(
                text(
                    """
                    INSERT INTO matched_edge_traversals (
                        id, activity_id, street_edge_id, user_id, club_id,
                        graph_version_id, local_activity_date, coverage, confidence,
                        elapsed_time_sec, speed_mps, qualified, rejection_reasons
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:activity AS uuid), :edge,
                        CAST(:user AS uuid), CAST(:club AS uuid), CAST(:graph AS uuid),
                        :local_date, :coverage, :confidence, :elapsed, :speed,
                        :qualified, CAST(:reasons AS jsonb)
                    )
                    ON CONFLICT (activity_id, street_edge_id) DO UPDATE SET
                        graph_version_id = EXCLUDED.graph_version_id,
                        coverage = EXCLUDED.coverage,
                        confidence = EXCLUDED.confidence,
                        elapsed_time_sec = EXCLUDED.elapsed_time_sec,
                        speed_mps = EXCLUDED.speed_mps,
                        qualified = EXCLUDED.qualified,
                        rejection_reasons = EXCLUDED.rejection_reasons,
                        matched_at = NOW()
                    """
                ),
                {
                    "id": traversal["id"],
                    "activity": traversal["activity_id"],
                    "edge": traversal["street_edge_id"],
                    "user": traversal["user_id"],
                    "club": traversal["club_id"],
                    "graph": traversal["graph_version_id"],
                    "local_date": traversal["local_activity_date"],
                    "coverage": coverage,
                    "confidence": confidence,
                    "elapsed": elapsed,
                    "speed": traversal["speed_mps"],
                    "qualified": qualified,
                    "reasons": json.dumps(traversal["rejection_reasons"]),
                },
            )
            if qualified:
                traversals.append(traversal)
    return {
        "status": "matched" if traversals else "rejected",
        "traversals": traversals,
        "confidence": confidence,
        "reason": None if traversals else "insufficient_edge_coverage",
        "matcher_version": MATCHER_VERSION,
    }


async def recompute_edges(
    street_edge_ids: Iterable[str],
    now: Optional[datetime] = None,
    source_activity_id: Optional[str] = None,
) -> None:
    engine = get_geo_engine()
    if engine is None:
        raise TerritoryMatcherUnavailable("PostGIS is not configured")
    reference = now or datetime.now(timezone.utc)
    for edge_id in set(street_edge_ids):
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    DELETE FROM territory_scores
                    WHERE street_edge_id=:edge
                    """
                ),
                {"edge": edge_id},
            )
            rows = [
                dict(row._mapping)
                for row in await connection.execute(
                    text(
                        """
                        SELECT t.user_id, membership.club_id,
                               t.local_activity_date,
                               t.coverage, t.confidence, t.elapsed_time_sec,
                               a.started_at AS activity_started_at,
                               t.matched_at, t.qualified
                        FROM matched_edge_traversals t
                        JOIN activities a ON a.id = t.activity_id
                        JOIN street_edges edge
                          ON edge.id=t.street_edge_id AND edge.status='active'
                        LEFT JOIN club_memberships membership
                          ON membership.club_id=t.club_id
                         AND membership.user_id=t.user_id
                         AND membership.status='active'
                         AND EXISTS (
                           SELECT 1 FROM clubs active_club
                           WHERE active_club.id=membership.club_id
                             AND active_club.status='active'
                         )
                        WHERE t.street_edge_id = :edge
                          AND t.local_activity_date >= CAST(:cutoff AS date)
                          AND t.qualified
                          AND a.status = 'complete'
                          AND a.verification = 'verified'
                          AND a.visibility != 'private'
                          AND a.deleted_at IS NULL
                          AND NOT EXISTS (
                            SELECT 1 FROM competition_flags f
                            WHERE f.activity_id = a.id
                              AND f.status IN ('open', 'reviewing', 'upheld', 'appealed')
                          )
                        """
                    ),
                    {
                        "edge": edge_id,
                        "cutoff": reference - timedelta(days=TERRITORY_WINDOW_DAYS),
                    },
                )
            ]

            by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            by_user_club: Dict[tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
            for row in rows:
                user_id = str(row["user_id"])
                by_user[user_id].append(row)
                if row.get("club_id"):
                    by_user_club[(user_id, str(row["club_id"]))].append(row)

            personal_scores = []
            for user_id, user_rows in by_user.items():
                result = score_controller_traversals(user_rows, now=reference)
                if result["score"] <= 0:
                    continue
                score = {
                    "controller_id": user_id,
                    "score": result["score"],
                    "scoring_days": result["scoring_days"],
                    "fastest_time_sec": result["fastest_time_sec"],
                    "score_reached_at": result["score_reached_at"],
                    "expires_at": result["expires_at"],
                }
                personal_scores.append(score)
                await _upsert_score(connection, edge_id, "athlete", score, reference)

            club_members: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for (user_id, club_id), attributed_rows in by_user_club.items():
                result = score_controller_traversals(attributed_rows, now=reference)
                if result["score"] <= 0:
                    continue
                club_members[club_id].append(
                    {
                        "controller_id": user_id,
                        "score": result["score"],
                        "scoring_days": result["scoring_days"],
                        "fastest_time_sec": result["fastest_time_sec"],
                        "score_reached_at": result["score_reached_at"],
                        "expires_at": result["expires_at"],
                    }
                )
            club_scores = []
            for club_id, members in club_members.items():
                result = aggregate_club_edge_score(members)
                score = {
                    "controller_id": club_id,
                    "score": result["score"],
                    "scoring_days": result["scoring_days"],
                    "fastest_time_sec": result["fastest_time_sec"],
                    "score_reached_at": result["score_reached_at"],
                    "expires_at": result["expires_at"],
                }
                club_scores.append(score)
                await _upsert_score(connection, edge_id, "club", score, reference)

            await _apply_controller(
                connection,
                edge_id,
                "athlete",
                personal_scores,
                reference,
                source_activity_id=source_activity_id,
            )
            await _apply_controller(
                connection,
                edge_id,
                "club",
                club_scores,
                reference,
                source_activity_id=source_activity_id,
            )
    if source_activity_id:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    UPDATE leaderboard_facts f
                    SET territory_gain_m=COALESCE((
                      SELECT SUM(e.distance_m)
                      FROM territory_control_history h
                      JOIN street_edges e ON e.id=h.street_edge_id
                      JOIN activities a ON a.id=h.source_activity_id
                      WHERE h.source_activity_id=CAST(:activity AS uuid)
                        AND h.controller_type='athlete'
                        AND h.event_type='claim'
                        AND h.controller_id=a.user_id
                    ), 0)
                    WHERE f.activity_id=CAST(:activity AS uuid)
                      AND f.subject_type='athlete'
                    """
                ),
                {"activity": source_activity_id},
            )


async def _upsert_score(
    connection: Any,
    edge_id: str,
    controller_type: str,
    score: Dict[str, Any],
    reference: datetime,
) -> None:
    await connection.execute(
        text(
            """
            INSERT INTO territory_scores (
                id, street_edge_id, controller_type, controller_id, score,
                fastest_time_sec, scoring_days, window_started_at,
                score_reached_at, window_ends_at, computation_version
            ) VALUES (
                CAST(:id AS uuid), :edge, CAST(:type AS controller_type),
                CAST(:controller AS uuid), :score, :fastest, :days,
                :window_start, :score_reached_at, :window_end, :version
            )
            ON CONFLICT (street_edge_id, controller_type, controller_id) DO UPDATE SET
                score = EXCLUDED.score,
                fastest_time_sec = EXCLUDED.fastest_time_sec,
                scoring_days = EXCLUDED.scoring_days,
                window_started_at = EXCLUDED.window_started_at,
                score_reached_at = EXCLUDED.score_reached_at,
                window_ends_at = EXCLUDED.window_ends_at,
                computation_version = EXCLUDED.computation_version,
                computed_at = NOW()
            """
        ),
        {
            "id": new_id(),
            "edge": edge_id,
            "type": controller_type,
            "controller": score["controller_id"],
            "score": score["score"],
            "fastest": score["fastest_time_sec"],
            "days": score["scoring_days"],
            "window_start": reference - timedelta(days=TERRITORY_WINDOW_DAYS),
            "score_reached_at": score.get("score_reached_at"),
            "window_end": score["expires_at"],
            "version": "rolling-28d-v1",
        },
    )


async def _apply_controller(
    connection: Any,
    edge_id: str,
    controller_type: str,
    scores: List[Dict[str, Any]],
    reference: datetime,
    source_activity_id: Optional[str] = None,
) -> None:
    winner = choose_controller(scores)
    previous = (
        await connection.execute(
            text(
                """
                SELECT controller_id, score, controlled_since
                FROM territory_current_control
                WHERE street_edge_id = :edge
                  AND controller_type = CAST(:type AS controller_type)
                FOR UPDATE
                """
            ),
            {"edge": edge_id, "type": controller_type},
        )
    ).first()
    if winner is None:
        if previous:
            await connection.execute(
                text(
                    """
                    DELETE FROM territory_current_control
                    WHERE street_edge_id=:edge
                      AND controller_type=CAST(:type AS controller_type)
                    """
                ),
                {"edge": edge_id, "type": controller_type},
            )
            await _history(
                connection,
                edge_id,
                controller_type,
                str(previous.controller_id),
                None,
                "expiry",
                float(previous.score),
                None,
                source_activity_id,
            )
        return
    changed = not previous or str(previous.controller_id) != winner["controller_id"]
    controlled_since = reference if changed else previous.controlled_since
    await connection.execute(
        text(
            """
            INSERT INTO territory_current_control (
                street_edge_id, controller_type, controller_id, score,
                fastest_time_sec, score_reached_at, controlled_since, expires_at
            ) VALUES (
                :edge, CAST(:type AS controller_type), CAST(:controller AS uuid),
                :score, :fastest, :score_reached_at, :controlled_since, :expires
            )
            ON CONFLICT (street_edge_id, controller_type) DO UPDATE SET
                controller_id = EXCLUDED.controller_id,
                score = EXCLUDED.score,
                fastest_time_sec = EXCLUDED.fastest_time_sec,
                score_reached_at = EXCLUDED.score_reached_at,
                controlled_since = EXCLUDED.controlled_since,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            """
        ),
        {
            "edge": edge_id,
            "type": controller_type,
            "controller": winner["controller_id"],
            "score": winner["score"],
            "fastest": winner.get("fastest_time_sec"),
            "score_reached_at": winner.get("score_reached_at"),
            "controlled_since": controlled_since,
            "expires": winner["expires_at"],
        },
    )
    if changed:
        if previous:
            await _history(
                connection,
                edge_id,
                controller_type,
                str(previous.controller_id),
                None,
                "loss",
                float(previous.score),
                None,
                source_activity_id,
            )
        await _history(
            connection,
            edge_id,
            controller_type,
            None,
            winner["controller_id"],
            "claim",
            None,
            winner["score"],
            source_activity_id,
        )
    elif source_activity_id:
        await _history(
            connection,
            edge_id,
            controller_type,
            winner["controller_id"],
            winner["controller_id"],
            "defence",
            float(previous.score) if previous else None,
            winner["score"],
            source_activity_id,
        )


async def _history(
    connection: Any,
    edge_id: str,
    controller_type: str,
    previous_controller_id: Optional[str],
    controller_id: Optional[str],
    event_type: str,
    previous_score: Optional[float],
    score: Optional[float],
    source_activity_id: Optional[str] = None,
) -> None:
    history_id = new_id()
    inserted = await connection.scalar(
        text(
            """
            INSERT INTO territory_control_history (
                id, street_edge_id, controller_type, previous_controller_id,
                controller_id, event_type, previous_score, score, source_activity_id
            ) VALUES (
                CAST(:id AS uuid), :edge, CAST(:type AS controller_type),
                CAST(:previous AS uuid), CAST(:controller AS uuid),
                :event, :previous_score, :score, CAST(:source_activity AS uuid)
            )
            ON CONFLICT DO NOTHING
            RETURNING id
            """
        ),
        {
            "id": history_id,
            "edge": edge_id,
            "type": controller_type,
            "previous": previous_controller_id,
            "controller": controller_id,
            "event": event_type,
            "previous_score": previous_score,
            "score": score,
            "source_activity": source_activity_id,
        },
    )
    if not inserted or controller_type != "club":
        return
    affected_club_id = controller_id or previous_controller_id
    if not affected_club_id:
        return
    timeline_event_id = new_id()
    await connection.execute(
        text(
            """
            INSERT INTO system_activity_events (
                id, club_id, event_type, visibility, source_type, source_id,
                payload, idempotency_key
            ) VALUES (
                CAST(:id AS uuid), CAST(:club AS uuid), :event, 'club',
                'territory_control', CAST(:edge AS uuid),
                CAST(:payload AS jsonb), :key
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            """
        ),
        {
            "id": timeline_event_id,
            "club": affected_club_id,
            "event": f"territory_{event_type}",
            "edge": edge_id,
            "payload": json.dumps(
                {
                    "history_id": str(inserted),
                    "street_edge_id": str(edge_id),
                    "event_type": event_type,
                    "previous_controller_id": previous_controller_id,
                    "controller_id": controller_id,
                    "score": score,
                }
            ),
            "key": f"territory:{inserted}:{affected_club_id}:timeline",
        },
    )
    await connection.execute(
        text(
            """
            INSERT INTO outbox_events (
                id, idempotency_key, aggregate_type, aggregate_id,
                event_type, payload
            ) VALUES (
                CAST(:id AS uuid), :key, 'territory_history',
                CAST(:history AS uuid),
                'territory.control_changed', CAST(:payload AS jsonb)
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            """
        ),
        {
            "id": new_id(),
            "key": f"territory-history:{inserted}:control-changed",
            "history": inserted,
            "payload": json.dumps(
                {
                    "history_id": str(inserted),
                    "club_id": str(affected_club_id),
                    "street_edge_id": str(edge_id),
                    "event_type": event_type,
                }
            ),
        },
    )


async def expire_territory_scores() -> Dict[str, int]:
    engine = get_geo_engine()
    if engine is None:
        return {"expired_edges": 0}
    async with engine.connect() as connection:
        edge_ids = [
            row[0]
            for row in await connection.execute(
                text(
                    """
                    SELECT DISTINCT street_edge_id
                    FROM territory_current_control
                    WHERE expires_at <= NOW() + INTERVAL '1 day'
                    """
                )
            )
        ]
    await recompute_edges(edge_ids)
    return {"expired_edges": len(edge_ids)}

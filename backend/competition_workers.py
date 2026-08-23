from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from cryptography.fernet import Fernet
from sqlalchemy import text

from backend.geo_db import get_geo_engine
from backend.platform_ids import new_id
from backend.territory_engine import expire_territory_scores


logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 8
LEASE_SECONDS = 300


async def _claim_outbox(limit: int) -> List[Dict[str, Any]]:
    engine = get_geo_engine()
    if engine is None:
        return []
    async with engine.begin() as connection:
        rows = await connection.execute(
            text(
                """
                WITH selected AS (
                    SELECT id
                    FROM outbox_events
                    WHERE available_at <= NOW()
                      AND (
                        status IN ('pending', 'retry')
                        OR (status = 'processing' AND lease_expires_at <= NOW())
                      )
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT :limit
                )
                UPDATE outbox_events o
                SET status='processing',
                    lease_expires_at=NOW() + (:lease * INTERVAL '1 second'),
                    attempts=o.attempts + 1
                FROM selected
                WHERE o.id=selected.id
                RETURNING o.id, o.aggregate_type, o.aggregate_id,
                          o.event_type, o.payload, o.attempts
                """
            ),
            {"limit": max(1, min(limit, 100)), "lease": LEASE_SECONDS},
        )
        return [dict(row._mapping) for row in rows]


async def _notification_recipients(
    connection: Any, event: Dict[str, Any]
) -> List[str]:
    payload = event.get("payload") or {}
    event_type = event["event_type"]
    if event_type in {
        "club.membership_active",
        "club.membership_rejected",
        "achievement.awarded",
        "club.primary_changed",
        "race.result_verified",
        "race.result_rejected",
        "moderation.upheld",
        "moderation.dismissed",
        "moderation.appealed",
    }:
        return [str(payload["user_id"])] if payload.get("user_id") else []
    if event_type == "race.reminder":
        race_id = payload.get("race_id")
        if not race_id:
            return []
        return [
            str(row[0])
            for row in await connection.execute(
                text(
                    """
                    SELECT user_id FROM race_entries
                    WHERE race_id=CAST(:race AS uuid)
                    """
                ),
                {"race": race_id},
            )
        ]
    if event_type == "challenge.milestone":
        return [str(payload["user_id"])] if payload.get("user_id") else []
    if event_type == "territory.control_changed":
        club_id = payload.get("club_id")
        if not club_id:
            return []
        return [
            str(row[0])
            for row in await connection.execute(
                text(
                    """
                    SELECT user_id FROM club_memberships
                    WHERE club_id=CAST(:club AS uuid) AND status='active'
                    """
                ),
                {"club": club_id},
            )
        ]
    return []


def _notification_copy(event: Dict[str, Any]) -> tuple[str, str]:
    event_type = event["event_type"]
    if event_type == "club.membership_active":
        return "Membership approved", "You are now an active club member."
    if event_type == "club.membership_rejected":
        return "Membership request updated", "Your club membership request was not approved."
    if event_type == "territory.control_changed":
        return "Territory changed", "Road control changed in your primary club."
    if event_type == "challenge.milestone":
        return "Challenge milestone", "You reached a new club challenge milestone."
    if event_type == "race.reminder":
        return "Race reminder", "Your club race starts soon."
    if event_type == "achievement.awarded":
        return "Achievement unlocked", str(
            (event.get("payload") or {}).get("title")
            or "You earned a new running achievement."
        )
    if event_type == "club.primary_changed":
        return "Primary club changed", "Future eligible runs will now count for your selected club."
    if event_type == "race.result_verified":
        return "Race result verified", "Your club race result is now official."
    if event_type == "race.result_rejected":
        return "Race result needs attention", "Your club race result did not pass verification."
    if event_type == "moderation.upheld":
        return "Activity review completed", "The competition flag was upheld. You may appeal the decision."
    if event_type == "moderation.dismissed":
        return "Activity restored", "The competition flag was dismissed and your results are being rebuilt."
    if event_type == "moderation.appealed":
        return "Appeal received", "Your activity appeal is awaiting administrator review."
    return "Runlete update", "Your club competition has an update."


async def _handle_event(event: Dict[str, Any]) -> None:
    engine = get_geo_engine()
    if engine is None:
        return
    territory_edges: List[str] = []
    async with engine.begin() as connection:
        if event["event_type"] == "activity.competition_verified":
            await _award_activity_achievements(connection, event)
        if event["event_type"] == "territory.membership_changed":
            payload = event.get("payload") or {}
            territory_edges = [
                str(row[0])
                for row in await connection.execute(
                    text(
                        """
                        SELECT DISTINCT street_edge_id
                        FROM matched_edge_traversals
                        WHERE user_id=CAST(:user AS uuid)
                          AND club_id=CAST(:club AS uuid)
                          AND local_activity_date>=CURRENT_DATE - 28
                        """
                    ),
                    {"user": payload.get("user_id"), "club": payload.get("club_id")},
                )
            ]
        elif event["event_type"] == "territory.club_status_changed":
            territory_edges = [
                str(row[0])
                for row in await connection.execute(
                    text(
                        """
                        SELECT DISTINCT street_edge_id
                        FROM matched_edge_traversals
                        WHERE club_id=CAST(:club AS uuid)
                          AND local_activity_date>=CURRENT_DATE - 28
                        """
                    ),
                    {"club": (event.get("payload") or {}).get("club_id")},
                )
            ]
        recipients = await _notification_recipients(connection, event)
        title, body = _notification_copy(event)
        for user_id in recipients:
            event_id = await connection.scalar(
                text(
                    """
                    SELECT id FROM system_activity_events
                    WHERE source_id=CAST(:source AS uuid)
                       OR payload->>'history_id'=:source
                    ORDER BY occurred_at DESC LIMIT 1
                    """
                ),
                {"source": str(event["aggregate_id"])},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO notifications (
                        id, user_id, event_id, outbox_event_id, notification_type,
                        title, body, data
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:user AS uuid), :event,
                        :outbox, :type, :title, :body, CAST(:data AS jsonb)
                    )
                    ON CONFLICT (user_id, outbox_event_id, notification_type)
                    WHERE outbox_event_id IS NOT NULL DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "user": user_id,
                    "event": event_id,
                    "outbox": event["id"],
                    "type": event["event_type"],
                    "title": title,
                    "body": body,
                    "data": json.dumps(event.get("payload") or {}, default=str),
                },
            )
    if territory_edges:
        from backend.territory_engine import recompute_edges

        await recompute_edges(territory_edges)


async def _award_activity_achievements(connection: Any, event: Dict[str, Any]) -> None:
    payload = event.get("payload") or {}
    activity_id = payload.get("activity_id")
    if not activity_id:
        return
    activity = (
        await connection.execute(
            text(
                """
                SELECT a.user_id, a.distance_m, a.started_at,
                       a.visibility::text AS visibility, attribution.club_id
                FROM activities a
                LEFT JOIN activity_club_attributions attribution
                  ON attribution.activity_id=a.id
                WHERE a.id=CAST(:activity AS uuid)
                  AND a.status='complete'
                  AND a.verification='verified'
                  AND a.visibility!='private'
                  AND a.deleted_at IS NULL
                """
            ),
            {"activity": activity_id},
        )
    ).first()
    if not activity:
        return
    candidates = [("first-verified-run", "first_run", "First verified run")]
    distance_m = float(activity.distance_m or 0)
    for threshold, key, title in (
        (5_000, "single-run-5k", "5K finisher"),
        (10_000, "single-run-10k", "10K finisher"),
        (21_097.5, "single-run-half-marathon", "Half marathon finisher"),
        (42_195, "single-run-marathon", "Marathon finisher"),
    ):
        if distance_m >= threshold:
            candidates.append((key, "distance", title))
    for key, achievement_type, title in candidates:
        achievement_id = new_id()
        awarded = (
            await connection.execute(
                text(
                    """
                    INSERT INTO achievements (
                        id, user_id, club_id, activity_id, achievement_type,
                        key, title, metadata, awarded_at
                    ) VALUES (
                        CAST(:id AS uuid), :user, :club, CAST(:activity AS uuid),
                        :type, :key, :title, CAST(:metadata AS jsonb), :awarded_at
                    )
                    ON CONFLICT (user_id, key) DO NOTHING
                    RETURNING id
                    """
                ),
                {
                    "id": achievement_id,
                    "user": activity.user_id,
                    "club": activity.club_id,
                    "activity": activity_id,
                    "type": achievement_type,
                    "key": key,
                    "title": title,
                    "metadata": json.dumps({"distance_m": distance_m}),
                    "awarded_at": activity.started_at,
                },
            )
        ).scalar()
        if not awarded:
            continue
        if activity.club_id:
            await connection.execute(
                text(
                    """
                    INSERT INTO system_activity_events (
                        id, club_id, actor_user_id, event_type, visibility,
                        source_type, source_id, payload, idempotency_key, occurred_at
                    ) VALUES (
                        CAST(:id AS uuid), :club, :user, 'achievement_awarded',
                        CAST(:visibility AS activity_visibility), 'achievement',
                        CAST(:achievement AS uuid), CAST(:payload AS jsonb), :key, NOW()
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "club": activity.club_id,
                    "user": activity.user_id,
                    "visibility": activity.visibility,
                    "achievement": awarded,
                    "payload": json.dumps(
                        {"achievement_id": str(awarded), "title": title}
                    ),
                    "key": f"achievement:{awarded}:timeline",
                },
            )
        await connection.execute(
            text(
                """
                INSERT INTO outbox_events (
                    id, idempotency_key, aggregate_type, aggregate_id,
                    event_type, payload
                ) VALUES (
                    CAST(:id AS uuid), :key, 'achievement',
                    CAST(:achievement AS uuid),
                    'achievement.awarded', CAST(:payload AS jsonb)
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """
            ),
            {
                "id": new_id(),
                "key": f"achievement:{awarded}:awarded",
                "achievement": awarded,
                "payload": json.dumps(
                    {
                        "achievement_id": str(awarded),
                        "user_id": str(activity.user_id),
                        "club_id": str(activity.club_id) if activity.club_id else None,
                        "title": title,
                    }
                ),
            },
        )


async def _complete(event_id: Any) -> None:
    engine = get_geo_engine()
    if engine is None:
        return
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                UPDATE outbox_events
                SET status='completed', completed_at=NOW(), lease_expires_at=NULL
                WHERE id=:id
                """
            ),
            {"id": event_id},
        )


async def _fail(event: Dict[str, Any], exc: Exception) -> None:
    engine = get_geo_engine()
    if engine is None:
        return
    attempts = int(event.get("attempts") or 1)
    terminal = attempts >= MAX_ATTEMPTS
    delay = min(3600, 15 * (2 ** max(0, attempts - 1)))
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                UPDATE outbox_events
                SET status=:status, last_error=:error,
                    available_at=NOW() + (:delay * INTERVAL '1 second'),
                    lease_expires_at=NULL
                WHERE id=:id
                """
            ),
            {
                "id": event["id"],
                "status": "dead_letter" if terminal else "retry",
                "error": str(exc)[:2_000],
                "delay": delay,
            },
        )


async def process_competition_outbox(limit: int = 50) -> Dict[str, int]:
    events = await _claim_outbox(limit)
    completed = 0
    failed = 0
    for event in events:
        try:
            await _handle_event(event)
            await _complete(event["id"])
            completed += 1
        except Exception as exc:
            logger.exception("Competition outbox event %s failed", event["id"])
            await _fail(event, exc)
            failed += 1
    return {"selected": len(events), "completed": completed, "failed": failed}


async def send_pending_push_notifications(limit: int = 100) -> Dict[str, int]:
    engine = get_geo_engine()
    encryption_key = (os.environ.get("PUSH_TOKEN_ENCRYPTION_KEY") or "").strip()
    if engine is None or not encryption_key:
        return {"selected": 0, "sent": 0, "failed": 0}
    cipher = Fernet(encryption_key.encode())
    async with engine.connect() as connection:
        rows = [
            dict(row._mapping)
            for row in await connection.execute(
                text(
                    """
                    SELECT n.id, n.title, n.body, n.data, p.encrypted_token
                    FROM notifications n
                    JOIN push_tokens p ON p.user_id=n.user_id AND p.disabled_at IS NULL
                    WHERE n.push_status='pending'
                    ORDER BY n.created_at
                    LIMIT :limit
                    """
                ),
                {"limit": max(1, min(limit, 100))},
            )
        ]
    if not rows:
        return {"selected": 0, "sent": 0, "failed": 0}
    messages = []
    valid_ids = []
    failed_ids = []
    for row in rows:
        try:
            token = cipher.decrypt(row["encrypted_token"].encode()).decode()
            messages.append(
                {
                    "to": token,
                    "title": row["title"],
                    "body": row["body"],
                    "data": row.get("data") or {},
                    "channelId": "club-competition",
                }
            )
            valid_ids.append(row["id"])
        except Exception:
            failed_ids.append(row["id"])
    sent_ids: List[Any] = []
    if messages:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        access_token = (os.environ.get("EXPO_PUSH_ACCESS_TOKEN") or "").strip()
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    "https://exp.host/--/api/v2/push/send",
                    headers=headers,
                    json=messages,
                )
                response.raise_for_status()
            sent_ids = valid_ids
        except Exception:
            logger.exception("Expo push batch failed")
            failed_ids.extend(valid_ids)
    async with engine.begin() as connection:
        if sent_ids:
            await connection.execute(
                text("UPDATE notifications SET push_status='sent' WHERE id=ANY(CAST(:ids AS uuid[]))"),
                {"ids": sent_ids},
            )
        if failed_ids:
            await connection.execute(
                text("UPDATE notifications SET push_status='failed' WHERE id=ANY(CAST(:ids AS uuid[]))"),
                {"ids": failed_ids},
            )
    return {
        "selected": len(rows),
        "sent": len(sent_ids),
        "failed": len(failed_ids),
    }


async def _emit_challenge_milestones(
    connection: Any,
    challenge: Dict[str, Any],
) -> None:
    target = float(challenge.get("target") or 0)
    if target <= 0:
        return
    entries = await connection.execute(
        text(
            """
            SELECT user_id, score FROM challenge_entries
            WHERE challenge_id=CAST(:challenge AS uuid)
            """
        ),
        {"challenge": challenge["id"]},
    )
    for entry in entries:
        score = float(entry.score or 0)
        if challenge["metric"] == "fastest_segment_sec":
            reached = [100] if 0 < score <= target else []
        else:
            percent = max(0, min(100, int(score / target * 100)))
            reached = [milestone for milestone in (25, 50, 75, 100) if percent >= milestone]
        for milestone in reached:
            key = f"challenge:{challenge['id']}:{entry.user_id}:milestone:{milestone}"
            payload = {
                "challenge_id": str(challenge["id"]),
                "club_id": str(challenge["club_id"]),
                "user_id": str(entry.user_id),
                "milestone": milestone,
                "score": score,
                "target": target,
            }
            await connection.execute(
                text(
                    """
                    INSERT INTO system_activity_events (
                        id, club_id, actor_user_id, event_type, visibility,
                        source_type, source_id, payload, idempotency_key
                    ) VALUES (
                        CAST(:id AS uuid), :club, :user, 'challenge_milestone',
                        'club', 'challenge', :challenge, CAST(:payload AS jsonb), :key
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "club": challenge["club_id"],
                    "user": entry.user_id,
                    "challenge": challenge["id"],
                    "payload": json.dumps(payload),
                    "key": key,
                },
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO outbox_events (
                        id, idempotency_key, aggregate_type, aggregate_id,
                        event_type, payload
                    ) VALUES (
                        CAST(:id AS uuid), :key, 'challenge', :challenge,
                        'challenge.milestone', CAST(:payload AS jsonb)
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "key": f"{key}:notification",
                    "challenge": challenge["id"],
                    "payload": json.dumps(payload),
                },
            )


async def rebuild_challenge_scores() -> Dict[str, int]:
    engine = get_geo_engine()
    if engine is None:
        return {"challenges": 0, "entries": 0}
    async with engine.begin() as connection:
        challenges = [
            dict(row._mapping)
            for row in await connection.execute(
                text(
                    """
                    SELECT id, club_id, metric, target, segment_id, starts_at, ends_at
                    FROM challenges
                    WHERE status IN ('scheduled', 'active')
                      AND starts_at <= NOW() AND ends_at > NOW()
                    FOR UPDATE
                    """
                )
            )
        ]
        await connection.execute(
            text(
                """
                UPDATE challenges SET status='active', updated_at=NOW()
                WHERE status='scheduled' AND starts_at <= NOW() AND ends_at > NOW()
                """
            )
        )
        updated = 0
        metric_sql = {
            "distance_m": "COALESCE(SUM(f.distance_m), 0)",
            "moving_time_sec": "COALESCE(SUM(f.moving_time_sec), 0)",
            "run_count": "COALESCE(SUM(f.run_count), 0)",
            "consistency_days": "COUNT(DISTINCT f.consistency_date)",
            "territory_gain_m": "COALESCE(SUM(f.territory_gain_m), 0)",
        }
        for challenge in challenges:
            if challenge["metric"] == "fastest_segment_sec":
                result = await connection.execute(
                    text(
                        """
                        UPDATE challenge_entries e SET
                            score=scores.score,
                            progress=jsonb_build_object('score', scores.score),
                            updated_at=NOW()
                        FROM (
                            SELECT e2.user_id, MIN(se.elapsed_time_sec)::float AS score
                            FROM challenge_entries e2
                            JOIN club_memberships membership
                              ON membership.club_id=CAST(:club AS uuid)
                             AND membership.user_id=e2.user_id
                             AND membership.status='active'
                            LEFT JOIN segment_efforts se
                              ON se.user_id=e2.user_id
                             AND se.segment_id=CAST(:segment AS uuid)
                             AND se.leaderboard_eligible=TRUE
                             AND se.started_at BETWEEN :starts AND :ends
                            WHERE e2.challenge_id=CAST(:challenge AS uuid)
                            GROUP BY e2.user_id
                        ) scores
                        WHERE e.challenge_id=CAST(:challenge AS uuid)
                          AND e.user_id=scores.user_id
                        """
                    ),
                    {
                        "segment": challenge["segment_id"],
                        "club": challenge["club_id"],
                        "challenge": challenge["id"],
                        "starts": challenge["starts_at"],
                        "ends": challenge["ends_at"],
                    },
                )
                updated += int(result.rowcount or 0)
                await _emit_challenge_milestones(connection, challenge)
                continue
            expression = metric_sql.get(challenge["metric"])
            if not expression:
                continue
            result = await connection.execute(
                text(
                    f"""
                    UPDATE challenge_entries e SET
                        score = scores.score,
                        progress = jsonb_build_object('score', scores.score),
                        updated_at = NOW()
                    FROM (
                        SELECT e2.user_id, {expression}::float AS score
                        FROM challenge_entries e2
                        JOIN club_memberships membership
                          ON membership.club_id=CAST(:club AS uuid)
                         AND membership.user_id=e2.user_id
                         AND membership.status='active'
                        LEFT JOIN leaderboard_facts f
                          ON f.subject_type='athlete'
                         AND f.subject_id=e2.user_id
                         AND f.club_id=CAST(:club AS uuid)
                         AND f.occurred_at BETWEEN :starts AND :ends
                        WHERE e2.challenge_id=CAST(:challenge AS uuid)
                        GROUP BY e2.user_id
                    ) scores
                    WHERE e.challenge_id=CAST(:challenge AS uuid)
                      AND e.user_id=scores.user_id
                    """
                ),
                {
                    "club": challenge["club_id"],
                    "challenge": challenge["id"],
                    "starts": challenge["starts_at"],
                    "ends": challenge["ends_at"],
                },
            )
            updated += int(result.rowcount or 0)
            await _emit_challenge_milestones(connection, challenge)
        return {"challenges": len(challenges), "entries": updated}


async def ensure_quarterly_seasons() -> Dict[str, int]:
    engine = get_geo_engine()
    if engine is None:
        return {"created": 0}
    now = datetime.now(timezone.utc)
    quarter_month = ((now.month - 1) // 3) * 3 + 1
    current = datetime(now.year, quarter_month, 1, tzinfo=timezone.utc)
    starts: List[datetime] = []
    year, month = current.year, current.month
    for offset in range(-4, 5):
        absolute_month = year * 12 + (month - 1) + offset * 3
        starts.append(
            datetime(
                absolute_month // 12,
                absolute_month % 12 + 1,
                1,
                tzinfo=timezone.utc,
            )
        )
    created = 0
    async with engine.begin() as connection:
        for start in starts:
            end_month = start.year * 12 + (start.month - 1) + 3
            end = datetime(
                end_month // 12,
                end_month % 12 + 1,
                1,
                tzinfo=timezone.utc,
            )
            quarter = ((start.month - 1) // 3) + 1
            status = "active" if start <= now < end else (
                "closed" if end <= now else "scheduled"
            )
            result = await connection.execute(
                text(
                    """
                    INSERT INTO seasons (
                        id, code, name, starts_at, ends_at, status
                    ) VALUES (
                        CAST(:id AS uuid), :code, :name, :starts, :ends, :status
                    )
                    ON CONFLICT (code) DO UPDATE SET
                        name=EXCLUDED.name,
                        starts_at=EXCLUDED.starts_at,
                        ends_at=EXCLUDED.ends_at,
                        status=EXCLUDED.status
                    """
                ),
                {
                    "id": new_id(),
                    "code": f"{start.year}-Q{quarter}",
                    "name": f"{start.year} Season {quarter}",
                    "starts": start,
                    "ends": end,
                    "status": status,
                },
            )
            created += max(0, int(result.rowcount or 0))
    return {"created": created}


async def snapshot_daily_leaderboards() -> Dict[str, int]:
    """Persist immutable end-of-day club standings for audit and replay."""
    engine = get_geo_engine()
    if engine is None:
        return {"snapshots": 0}
    period_key = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    starts_at = datetime.fromisoformat(f"{period_key}T00:00:00+00:00")
    ends_at = starts_at + timedelta(days=1)
    created = 0
    async with engine.begin() as connection:
        clubs = [
            row[0]
            for row in await connection.execute(
                text("SELECT id FROM clubs WHERE status='active'")
            )
        ]
        for club_id in clubs:
            rows = [
                dict(row._mapping)
                for row in await connection.execute(
                    text(
                        """
                        SELECT f.subject_id AS user_id,
                               SUM(f.distance_m)::float AS distance_m,
                               SUM(f.moving_time_sec)::bigint AS moving_time_sec,
                               SUM(f.run_count)::bigint AS run_count,
                               COUNT(DISTINCT f.consistency_date)::int AS consistency_days,
                               SUM(f.territory_gain_m)::float AS territory_gain_m
                        FROM leaderboard_facts f
                        JOIN club_memberships membership
                          ON membership.club_id=f.club_id
                         AND membership.user_id=f.subject_id
                         AND membership.status='active'
                        WHERE f.subject_type='athlete'
                          AND f.club_id=:club
                          AND f.occurred_at>=:starts
                          AND f.occurred_at<:ends
                        GROUP BY f.subject_id
                        ORDER BY distance_m DESC, f.subject_id
                        LIMIT 100
                        """
                    ),
                    {"club": club_id, "starts": starts_at, "ends": ends_at},
                )
            ]
            for rank, row in enumerate(rows, start=1):
                row["rank"] = rank
                row["user_id"] = str(row["user_id"])
            result = await connection.execute(
                text(
                    """
                    INSERT INTO leaderboard_snapshots (
                        id, leaderboard_key, period_key, version, rows, immutable
                    ) VALUES (
                        CAST(:id AS uuid), :key, :period, 1,
                        CAST(:rows AS jsonb), TRUE
                    )
                    ON CONFLICT (leaderboard_key, period_key, version) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "key": f"club:{club_id}:daily",
                    "period": period_key,
                    "rows": json.dumps(rows, default=str),
                },
            )
            created += max(0, int(result.rowcount or 0))
    return {"snapshots": created}


async def schedule_competition_events() -> Dict[str, int]:
    """Advance lifecycle states and emit idempotent participant reminders."""
    engine = get_geo_engine()
    if engine is None:
        return {"reminders": 0}
    reminders = 0
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                UPDATE races SET status=CASE
                    WHEN result_cutoff_at < NOW() THEN 'completed'
                    WHEN starts_at <= NOW() THEN 'active'
                    ELSE status
                END, updated_at=NOW()
                WHERE status IN ('scheduled', 'active')
                """
            )
        )
        await connection.execute(
            text(
                """
                UPDATE challenges SET status=CASE
                    WHEN ends_at < NOW() THEN 'completed'
                    WHEN starts_at <= NOW() THEN 'active'
                    ELSE status
                END, updated_at=NOW()
                WHERE status IN ('scheduled', 'active')
                """
            )
        )
        races = [
            dict(row._mapping)
            for row in await connection.execute(
                text(
                    """
                    SELECT id, club_id, name, starts_at
                    FROM races
                    WHERE status='scheduled'
                      AND starts_at BETWEEN NOW() AND NOW() + INTERVAL '24 hours'
                      AND EXISTS (
                        SELECT 1 FROM race_entries e WHERE e.race_id=races.id
                      )
                    """
                )
            )
        ]
        for race in races:
            seconds = (race["starts_at"] - datetime.now(timezone.utc)).total_seconds()
            window = "1h" if seconds <= 3_600 else "24h"
            key = f"race:{race['id']}:reminder:{window}"
            result = await connection.execute(
                text(
                    """
                    INSERT INTO outbox_events (
                        id, idempotency_key, aggregate_type, aggregate_id,
                        event_type, payload
                    ) VALUES (
                        CAST(:id AS uuid), :key, 'race', :race,
                        'race.reminder', CAST(:payload AS jsonb)
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "key": key,
                    "race": race["id"],
                    "payload": json.dumps(
                        {
                            "race_id": str(race["id"]),
                            "club_id": str(race["club_id"]),
                            "name": race["name"],
                            "starts_at": race["starts_at"].isoformat(),
                            "window": window,
                        }
                    ),
                },
            )
            reminders += max(0, int(result.rowcount or 0))
    return {"reminders": reminders}


async def verify_activity_race_results(activity_id: str) -> Dict[str, int]:
    """Evaluate one completed activity against races the athlete entered."""
    engine = get_geo_engine()
    if engine is None:
        return {"evaluated": 0, "verified": 0}
    evaluated = 0
    verified = 0
    async with engine.begin() as connection:
        rows = await connection.execute(
            text(
                """
                SELECT r.id AS race_id, r.club_id, r.name AS race_name,
                       a.user_id, a.id AS activity_id,
                       a.elapsed_time_sec, a.verification::text AS activity_verification,
                       r.minimum_route_coverage, r.start_radius_m, r.end_radius_m,
                       LEAST(
                         1.0,
                         ST_Length(
                           ST_Intersection(
                             ST_Transform(r.route, 3857),
                             ST_Buffer(ST_Transform(a.route, 3857), 20)
                           )
                         ) / NULLIF(ST_Length(ST_Transform(r.route, 3857)), 0)
                       ) AS route_coverage,
                       ST_Distance(
                         ST_StartPoint(r.route)::geography,
                         ST_StartPoint(a.route)::geography
                       ) AS start_distance_m,
                       ST_Distance(
                         ST_EndPoint(r.route)::geography,
                         ST_EndPoint(a.route)::geography
                       ) AS end_distance_m,
                       EXISTS(
                         SELECT 1 FROM competition_flags f
                         WHERE f.activity_id=a.id
                           AND f.status IN ('open','reviewing','upheld','appealed')
                       ) AS has_flag
                FROM activities a
                JOIN race_entries e ON e.user_id=a.user_id
                JOIN races r ON r.id=e.race_id
                WHERE a.id=CAST(:activity AS uuid)
                  AND a.status='complete' AND a.deleted_at IS NULL
                  AND a.started_at >= r.starts_at
                  AND a.started_at <= r.starts_at + (r.start_window_minutes * INTERVAL '1 minute')
                  AND COALESCE(a.ended_at, a.started_at) <= r.result_cutoff_at
                  AND r.status IN ('scheduled','active')
                """
            ),
            {"activity": activity_id},
        )
        for row in rows:
            evaluated += 1
            coverage = float(row.route_coverage or 0)
            reasons = []
            if coverage < float(row.minimum_route_coverage):
                reasons.append("route_coverage")
            if float(row.start_distance_m or float("inf")) > float(row.start_radius_m):
                reasons.append("start_proximity")
            if float(row.end_distance_m or float("inf")) > float(row.end_radius_m):
                reasons.append("finish_proximity")
            if row.activity_verification != "verified":
                reasons.append("activity_verification")
            if row.has_flag:
                reasons.append("competition_flag")
            result_status = "verified" if not reasons else (
                "provisional"
                if set(reasons) <= {"activity_verification", "competition_flag"}
                else "rejected"
            )
            if result_status == "verified":
                verified += 1
            result_row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO race_results (
                            id, race_id, user_id, activity_id, elapsed_time_sec,
                            route_coverage, verification, rejection_reasons, verified_at
                        ) VALUES (
                            CAST(:id AS uuid), :race, :user, :activity, :elapsed,
                            :coverage, CAST(:verification AS verification_status),
                            CAST(:reasons AS jsonb),
                            CASE WHEN :verification='verified' THEN NOW() ELSE NULL END
                        )
                        ON CONFLICT (race_id, user_id) DO UPDATE SET
                            activity_id=EXCLUDED.activity_id,
                            elapsed_time_sec=EXCLUDED.elapsed_time_sec,
                            route_coverage=EXCLUDED.route_coverage,
                            verification=EXCLUDED.verification,
                            rejection_reasons=EXCLUDED.rejection_reasons,
                            verified_at=EXCLUDED.verified_at
                        RETURNING id
                        """
                    ),
                    {
                        "id": new_id(),
                        "race": row.race_id,
                        "user": row.user_id,
                        "activity": row.activity_id,
                        "elapsed": row.elapsed_time_sec,
                        "coverage": coverage,
                        "verification": result_status,
                        "reasons": json.dumps(reasons),
                    },
                )
            ).first()
            result_id = str(result_row.id)
            event_type = (
                "race_result_verified"
                if result_status == "verified"
                else "race_result_rejected"
                if result_status == "rejected"
                else "race_result_provisional"
            )
            event_key = f"race-result:{result_id}:{result_status}"
            payload = {
                "race_id": str(row.race_id),
                "race_result_id": result_id,
                "activity_id": str(row.activity_id),
                "user_id": str(row.user_id),
                "race_name": row.race_name,
                "verification": result_status,
                "rejection_reasons": reasons,
            }
            await connection.execute(
                text(
                    """
                    INSERT INTO system_activity_events (
                        id, club_id, actor_user_id, event_type, visibility,
                        source_type, source_id, payload, idempotency_key
                    ) VALUES (
                        CAST(:id AS uuid), :club, :user, :event_type, 'club',
                        'race_result', CAST(:result AS uuid),
                        CAST(:payload AS jsonb), :key
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "club": row.club_id,
                    "user": row.user_id,
                    "event_type": event_type,
                    "result": result_id,
                    "payload": json.dumps(payload),
                    "key": event_key,
                },
            )
            if result_status in {"verified", "rejected"}:
                await connection.execute(
                    text(
                        """
                        INSERT INTO outbox_events (
                            id, idempotency_key, aggregate_type, aggregate_id,
                            event_type, payload
                        ) VALUES (
                            CAST(:id AS uuid), :key, 'race_result',
                            CAST(:result AS uuid), :event_type, CAST(:payload AS jsonb)
                        )
                        ON CONFLICT (idempotency_key) DO NOTHING
                        """
                    ),
                    {
                        "id": new_id(),
                        "key": f"{event_key}:notification",
                        "result": result_id,
                        "event_type": f"race.result_{result_status}",
                        "payload": json.dumps(payload),
                    },
                )
    return {"evaluated": evaluated, "verified": verified}

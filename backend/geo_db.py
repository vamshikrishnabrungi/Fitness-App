from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from backend.platform_ids import new_id


_engine: Optional[AsyncEngine] = None


def _postgres_url() -> str:
    url = (os.environ.get('POSTGRES_URL') or '').strip()
    if url.startswith('postgres://'):
        return 'postgresql+asyncpg://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        return 'postgresql+asyncpg://' + url[len('postgresql://'):]
    return url


def postgis_configured() -> bool:
    return bool(_postgres_url())


def get_geo_engine() -> Optional[AsyncEngine]:
    global _engine
    url = _postgres_url()
    if not url:
        return None
    if _engine is None:
        _engine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=5,
        )
    return _engine


async def ping_postgis() -> bool:
    engine = get_geo_engine()
    if engine is None:
        return False
    async with engine.connect() as connection:
        return bool(await connection.scalar(text('SELECT PostGIS_Version() IS NOT NULL')))


async def mirror_activity_geometry(activity: Dict[str, Any]) -> bool:
    """Idempotently mirror a canonical activity geometry into PostGIS."""
    engine = get_geo_engine()
    geometry = activity.get('route_geojson')
    if engine is None or not geometry:
        return False
    statement = text(
        """
        INSERT INTO activity_geometries (
            activity_id, user_id, source, status, started_at, distance_m,
            computation_version, quality, route, updated_at
        )
        VALUES (
            CAST(:activity_id AS uuid), CAST(:user_id AS uuid), :source, :status,
            :started_at, :distance_m, :computation_version,
            CAST(:quality AS jsonb),
            ST_SetSRID(ST_GeomFromGeoJSON(:route_geojson), 4326),
            NOW()
        )
        ON CONFLICT (activity_id) DO UPDATE SET
            source = EXCLUDED.source,
            status = EXCLUDED.status,
            started_at = EXCLUDED.started_at,
            distance_m = EXCLUDED.distance_m,
            computation_version = EXCLUDED.computation_version,
            quality = EXCLUDED.quality,
            route = EXCLUDED.route,
            updated_at = NOW()
        """
    )
    async with engine.begin() as connection:
        await connection.execute(statement, {
            'activity_id': activity['id'],
            'user_id': activity['user_id'],
            'source': activity.get('source') or 'runlete',
            'status': activity.get('status') or 'complete',
            'started_at': activity.get('started_at'),
            'distance_m': float(activity.get('distance_m') or 0),
            'computation_version': str(activity.get('computation_version') or 'unknown'),
            'quality': json.dumps(activity.get('quality') or {}),
            'route_geojson': json.dumps(geometry),
        })
    return True


async def sync_competition_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert the canonical relational activity and freeze its club attribution."""
    engine = get_geo_engine()
    geometry = activity.get('route_geojson')
    if engine is None:
        return {'synced': False, 'club_id': None}
    visibility = str(activity.get('visibility') or 'club').lower()
    if visibility == 'clubs':
        visibility = 'club'
    if visibility not in {'public', 'club', 'private'}:
        visibility = 'private'
    quality = activity.get('quality') or {}
    eligible = bool(activity.get('leaderboard_eligible'))
    checks_complete = bool(activity.get('competition_checks_complete'))
    verification = 'verified' if eligible and checks_complete else (
        'rejected' if quality.get('flags') else 'provisional'
    )
    status = str(activity.get('status') or 'complete')
    privacy_snapshot = activity.get('privacy_snapshot') or {}
    hide_start_end_m = max(0, int(privacy_snapshot.get('hide_start_end_m') or 0))
    public_competition_eligible = bool(
        eligible
        and checks_complete
        and visibility == 'public'
        and privacy_snapshot.get('allow_leaderboards', True)
        and not privacy_snapshot.get('minor_safe_defaults')
    )
    async with engine.begin() as connection:
        await connection.execute(text(
            """
            INSERT INTO activities (
                id, user_id, source, source_activity_id, idempotency_key,
                status, verification, visibility, started_at, local_timezone, ended_at,
                elapsed_time_sec, moving_time_sec, distance_m, elevation_gain_m,
                quality_score, quality, computation_version,
                hide_start_end_m, public_competition_eligible, route, public_route
            ) VALUES (
                CAST(:id AS uuid), CAST(:user_id AS uuid), :source,
                :source_activity_id, :idempotency_key, :status,
                CAST(:verification AS verification_status),
                CAST(:visibility AS activity_visibility),
                :started_at, :timezone, :ended_at, :elapsed, :moving, :distance,
                :elevation, :quality_score, CAST(:quality AS jsonb),
                :computation_version, :hide_start_end_m, :public_eligible,
                CASE WHEN :route IS NULL THEN NULL
                     ELSE ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326) END,
                CASE
                  WHEN :route IS NULL THEN NULL
                  WHEN :hide_start_end_m <= 0 THEN
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326))
                  WHEN ST_Length(
                    ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326)::geography
                  ) <= (:hide_start_end_m * 2) THEN NULL
                  ELSE ST_Multi(
                    ST_LineSubstring(
                      ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326),
                      :hide_start_end_m / ST_Length(
                        ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326)::geography
                      ),
                      1 - (:hide_start_end_m / ST_Length(
                        ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326)::geography
                      ))
                    )
                  )
                END
            )
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                verification = EXCLUDED.verification,
                visibility = EXCLUDED.visibility,
                local_timezone = EXCLUDED.local_timezone,
                ended_at = EXCLUDED.ended_at,
                elapsed_time_sec = EXCLUDED.elapsed_time_sec,
                moving_time_sec = EXCLUDED.moving_time_sec,
                distance_m = EXCLUDED.distance_m,
                elevation_gain_m = EXCLUDED.elevation_gain_m,
                quality_score = EXCLUDED.quality_score,
                quality = EXCLUDED.quality,
                computation_version = EXCLUDED.computation_version,
                hide_start_end_m = EXCLUDED.hide_start_end_m,
                public_competition_eligible = EXCLUDED.public_competition_eligible,
                route = EXCLUDED.route,
                public_route = EXCLUDED.public_route,
                version = activities.version + 1,
                updated_at = NOW()
            """
        ), {
            'id': activity['id'],
            'user_id': activity['user_id'],
            'source': activity.get('source') or 'runlete',
            'source_activity_id': activity.get('source_activity_id'),
            'idempotency_key': activity.get('idempotency_key'),
            'status': status,
            'verification': verification,
            'visibility': visibility,
            'started_at': activity.get('started_at') or activity.get('start_time'),
            'timezone': activity.get('local_timezone') or 'UTC',
            'ended_at': activity.get('ended_at') or activity.get('end_time'),
            'elapsed': int(activity.get('elapsed_time_sec') or activity.get('duration_sec') or 0),
            'moving': int(activity.get('moving_time_sec') or 0),
            'distance': float(activity.get('distance_m') or float(activity.get('distance_km') or 0) * 1000),
            'elevation': float(activity.get('elevation_gain_m') or 0),
            'quality_score': float(quality.get('score') or 0),
            'quality': json.dumps(quality),
            'computation_version': str(activity.get('computation_version') or 'unknown'),
            'hide_start_end_m': hide_start_end_m,
            'public_eligible': public_competition_eligible,
            'route': json.dumps(geometry) if geometry else None,
        })

        club_id = None
        if eligible and visibility != 'private':
            club_id = await connection.scalar(text(
                """
                SELECT history.club_id
                FROM athlete_primary_club_history history
                JOIN club_memberships m
                  ON m.club_id = history.club_id AND m.user_id = history.user_id
                WHERE history.user_id = CAST(:user_id AS uuid)
                  AND history.effective_from <= CAST(:started_at AS timestamptz)
                  AND (
                    history.effective_to IS NULL
                    OR history.effective_to > CAST(:started_at AS timestamptz)
                  )
                  AND m.joined_at <= CAST(:started_at AS timestamptz)
                  AND (
                    m.ended_at IS NULL
                    OR m.ended_at > CAST(:started_at AS timestamptz)
                  )
                ORDER BY history.effective_from DESC
                LIMIT 1
                """
            ), {
                'user_id': activity['user_id'],
                'started_at': activity.get('started_at') or activity.get('start_time'),
            })
            if club_id:
                # ON CONFLICT intentionally preserves the original attribution forever.
                await connection.execute(text(
                    """
                    INSERT INTO activity_club_attributions (
                        activity_id, club_id, user_id, visibility
                    ) VALUES (
                        CAST(:activity AS uuid), :club, CAST(:user_id AS uuid),
                        CAST(:visibility AS activity_visibility)
                    )
                    ON CONFLICT (activity_id) DO NOTHING
                    """
                ), {
                    'activity': activity['id'],
                    'club': club_id,
                    'user_id': activity['user_id'],
                    'visibility': visibility,
                })
                club_id = await connection.scalar(text(
                    "SELECT club_id FROM activity_club_attributions WHERE activity_id=CAST(:id AS uuid)"
                ), {'id': activity['id']})

        if (
            eligible
            and checks_complete
            and verification == 'verified'
            and status == 'complete'
            and visibility != 'private'
        ):
            region_id = await connection.scalar(text(
                """
                SELECT r.id
                FROM regions r
                JOIN activities a ON a.id=CAST(:activity AS uuid)
                WHERE r.kind='city'
                  AND r.boundary IS NOT NULL
                  AND a.route IS NOT NULL
                  AND ST_Covers(r.boundary, ST_StartPoint(a.route))
                ORDER BY ST_Area(r.boundary::geography)
                LIMIT 1
                """
            ), {'activity': activity['id']})
            fact_id = new_id()
            await connection.execute(text(
                """
                INSERT INTO leaderboard_facts (
                    id, subject_type, subject_id, club_id, region_id, activity_id,
                    visibility, occurred_at, distance_m, moving_time_sec, run_count,
                    consistency_date
                ) VALUES (
                    CAST(:id AS uuid), 'athlete', CAST(:user AS uuid), :club,
                    :region, CAST(:activity AS uuid),
                    CAST(:visibility AS activity_visibility),
                    :occurred_at, :distance, :moving, 1,
                    CAST(:occurred_at AS date)
                )
                ON CONFLICT (subject_type, subject_id, activity_id) DO UPDATE SET
                    club_id = EXCLUDED.club_id,
                    region_id = EXCLUDED.region_id,
                    visibility = EXCLUDED.visibility,
                    distance_m = EXCLUDED.distance_m,
                    moving_time_sec = EXCLUDED.moving_time_sec,
                    consistency_date = EXCLUDED.consistency_date
                """
            ), {
                'id': fact_id,
                'user': activity['user_id'],
                'club': club_id,
                'region': region_id,
                'activity': activity['id'],
                'visibility': visibility,
                'occurred_at': activity.get('started_at') or activity.get('start_time'),
                'distance': float(activity.get('distance_m') or float(activity.get('distance_km') or 0) * 1000),
                'moving': int(activity.get('moving_time_sec') or 0),
            })
            if club_id:
                await connection.execute(text(
                    """
                    INSERT INTO system_activity_events (
                        id, club_id, actor_user_id, event_type, visibility,
                        source_type, source_id, payload, idempotency_key, occurred_at
                    ) VALUES (
                        CAST(:id AS uuid), :club, CAST(:user AS uuid), 'eligible_run',
                        CAST(:visibility AS activity_visibility), 'activity',
                        CAST(:activity AS uuid), CAST(:payload AS jsonb), :key, :occurred_at
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ), {
                    'id': new_id(),
                    'club': club_id,
                    'user': activity['user_id'],
                    'visibility': visibility,
                    'activity': activity['id'],
                    'payload': json.dumps({
                        'activity_id': activity['id'],
                        'distance_m': float(activity.get('distance_m') or float(activity.get('distance_km') or 0) * 1000),
                        'moving_time_sec': int(activity.get('moving_time_sec') or 0),
                        'verification': verification,
                    }),
                    'key': f"activity:{activity['id']}:club-timeline",
                    'occurred_at': activity.get('started_at') or activity.get('start_time'),
                })
            await connection.execute(text(
                """
                INSERT INTO outbox_events (
                    id, idempotency_key, aggregate_type, aggregate_id,
                    event_type, payload
                ) VALUES (
                    CAST(:id AS uuid), :key, 'activity', CAST(:activity AS uuid),
                    'activity.competition_verified', CAST(:payload AS jsonb)
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """
            ), {
                'id': new_id(),
                'key': f"activity:{activity['id']}:competition-verified",
                'activity': activity['id'],
                'payload': json.dumps({
                    'activity_id': activity['id'],
                    'user_id': activity['user_id'],
                    'club_id': str(club_id) if club_id else None,
                    'visibility': visibility,
                }),
            })
        return {'synced': True, 'club_id': str(club_id) if club_id else None}


async def sync_segment_effort(effort: Dict[str, Any]) -> bool:
    """Persist a verified segment effort in the relational competition store."""
    engine = get_geo_engine()
    if engine is None:
        return False
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                INSERT INTO segment_efforts (
                    id, activity_id, segment_id, user_id,
                    elapsed_time_sec, quality_score, leaderboard_eligible,
                    started_at
                ) VALUES (
                    CAST(:id AS uuid), CAST(:activity AS uuid),
                    CAST(:segment AS uuid), CAST(:user AS uuid),
                    :elapsed, :quality, :eligible, :started
                )
                ON CONFLICT (activity_id, segment_id) DO UPDATE SET
                    elapsed_time_sec=EXCLUDED.elapsed_time_sec,
                    quality_score=EXCLUDED.quality_score,
                    leaderboard_eligible=EXCLUDED.leaderboard_eligible,
                    started_at=EXCLUDED.started_at
                """
            ),
            {
                "id": effort["id"],
                "activity": effort["activity_id"],
                "segment": effort["segment_id"],
                "user": effort["user_id"],
                "elapsed": effort["elapsed_time_sec"],
                "quality": effort.get("quality_score"),
                "eligible": bool(effort.get("leaderboard_eligible")),
                "started": effort.get("started_at"),
            },
        )
    return True


async def release_competition_activity(activity_id: str) -> list[str]:
    """Remove mutable competition projections while retaining the activity audit row."""
    engine = get_geo_engine()
    if engine is None:
        return []
    async with engine.begin() as connection:
        edge_ids = [
            str(row[0])
            for row in await connection.execute(text(
                """
                SELECT DISTINCT street_edge_id FROM matched_edge_traversals
                WHERE activity_id = CAST(:activity_id AS uuid)
                """
            ), {'activity_id': activity_id})
        ]
        await connection.execute(text(
            "DELETE FROM leaderboard_facts WHERE activity_id = CAST(:activity_id AS uuid)"
        ), {'activity_id': activity_id})
        await connection.execute(text(
            "DELETE FROM segment_efforts WHERE activity_id=CAST(:activity_id AS uuid)"
        ), {'activity_id': activity_id})
        await connection.execute(text(
            "DELETE FROM matched_edge_traversals WHERE activity_id = CAST(:activity_id AS uuid)"
        ), {'activity_id': activity_id})
        await connection.execute(text(
            """
            DELETE FROM system_activity_events
            WHERE source_type='activity' AND source_id=CAST(:activity_id AS uuid)
            """
        ), {'activity_id': activity_id})
        await connection.execute(text(
            "DELETE FROM race_results WHERE activity_id=CAST(:activity_id AS uuid)"
        ), {'activity_id': activity_id})
        await connection.execute(text(
            """
            UPDATE activities SET verification='provisional', updated_at=NOW()
            WHERE id = CAST(:activity_id AS uuid)
            """
        ), {'activity_id': activity_id})
        return edge_ids


async def mirror_street_edge(edge: Dict[str, Any]) -> bool:
    engine = get_geo_engine()
    geometry = edge.get('geometry')
    if engine is None or not geometry:
        return False
    async with engine.begin() as connection:
        await connection.execute(text(
            """
            INSERT INTO street_edges (
                street_edge_id, id, name, highway, surface, distance_m, edge, metadata, updated_at
            )
            VALUES (
                :street_edge_id, CAST(:id AS uuid), :name, :highway, :surface, :distance_m,
                ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                CAST(:metadata AS jsonb), NOW()
            )
            ON CONFLICT (street_edge_id) DO UPDATE SET
                name = EXCLUDED.name,
                highway = EXCLUDED.highway,
                surface = EXCLUDED.surface,
                distance_m = EXCLUDED.distance_m,
                edge = EXCLUDED.edge,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """
        ), {
            'street_edge_id': edge['id'],
            'id': str(
                uuid.UUID(str(edge.get('uuid')))
                if edge.get('uuid')
                else uuid.uuid5(uuid.NAMESPACE_URL, f"runlete:legacy-edge:{edge['id']}")
            ),
            'name': edge.get('name'),
            'highway': edge.get('highway'),
            'surface': edge.get('surface'),
            'distance_m': float(edge.get('distance_m') or 0),
            'geometry': json.dumps(geometry),
            'metadata': json.dumps({'status': edge.get('status') or 'active'}),
        })
    return True


async def mirror_segment_geometry(segment: Dict[str, Any]) -> bool:
    engine = get_geo_engine()
    geometry = segment.get('geometry')
    if engine is None or not geometry:
        return False
    async with engine.begin() as connection:
        await connection.execute(text(
            """
            INSERT INTO segment_geometries (
                segment_id, status, distance_m, segment, metadata, updated_at
            )
            VALUES (
                CAST(:segment_id AS uuid), :status, :distance_m,
                ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                CAST(:metadata AS jsonb), NOW()
            )
            ON CONFLICT (segment_id) DO UPDATE SET
                status = EXCLUDED.status,
                distance_m = EXCLUDED.distance_m,
                segment = EXCLUDED.segment,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """
        ), {
            'segment_id': segment['id'],
            'status': segment.get('status') or 'active',
            'distance_m': float(segment.get('distance_m') or 0),
            'geometry': json.dumps(geometry),
            'metadata': json.dumps({'name': segment.get('name')}),
        })
    return True


async def candidate_street_edge_ids(activity_id: str, tolerance_m: float = 75) -> Optional[list[str]]:
    engine = get_geo_engine()
    if engine is None:
        return None
    async with engine.connect() as connection:
        result = await connection.execute(text(
            """
            SELECT edge.id
            FROM street_edges AS edge
            JOIN activity_geometries AS activity
              ON activity.activity_id = CAST(:activity_id AS uuid)
            WHERE ST_DWithin(edge.edge::geography, activity.route::geography, :tolerance_m)
            """
        ), {'activity_id': activity_id, 'tolerance_m': tolerance_m})
        return [str(row[0]) for row in result]


async def candidate_segment_ids(activity_id: str, tolerance_m: float = 100) -> Optional[list[str]]:
    engine = get_geo_engine()
    if engine is None:
        return None
    async with engine.connect() as connection:
        result = await connection.execute(text(
            """
            SELECT segment.segment_id
            FROM segment_geometries AS segment
            JOIN activity_geometries AS activity
              ON activity.activity_id = CAST(:activity_id AS uuid)
            WHERE segment.status = 'active'
              AND ST_DWithin(segment.segment::geography, activity.route::geography, :tolerance_m)
            """
        ), {'activity_id': activity_id, 'tolerance_m': tolerance_m})
        return [str(row[0]) for row in result]

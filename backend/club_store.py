from __future__ import annotations

import base64
import hashlib
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from backend.club_domain import (
    PRIMARY_CLUB_COOLDOWN_DAYS,
    aggregate_club_edge_score,
    choose_controller,
    score_controller_traversals,
    slugify,
    utc_now,
)
from backend.geo_db import get_geo_engine
from backend.platform_cache import cache_get_bytes, cache_set_bytes
from backend.platform_ids import new_id


class PlatformUnavailable(RuntimeError):
    pass


class DomainConflict(RuntimeError):
    pass


class DomainForbidden(RuntimeError):
    pass


class DomainNotFound(RuntimeError):
    pass


def _uuid(value: Any) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise DomainNotFound("Resource not found") from exc


def _dict(row: Any) -> Dict[str, Any]:
    value = dict(row._mapping if hasattr(row, "_mapping") else row)
    for key, item in list(value.items()):
        if isinstance(item, UUID):
            value[key] = str(item)
    return value


def _json(value: Any) -> str:
    return json.dumps(value, default=str, separators=(",", ":"))


def encode_cursor(created_at: datetime, entity_id: str) -> str:
    payload = f"{created_at.astimezone(timezone.utc).isoformat()}|{entity_id}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: Optional[str]) -> tuple[Optional[datetime], Optional[UUID]]:
    if not cursor:
        return None, None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        created, entity_id = base64.urlsafe_b64decode(padded).decode().split("|", 1)
        parsed = datetime.fromisoformat(created)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed, UUID(entity_id)
    except (ValueError, TypeError):
        raise DomainConflict("Invalid pagination cursor")


class ClubStore:
    def __init__(self):
        self.engine = get_geo_engine()
        if self.engine is None:
            raise PlatformUnavailable("POSTGRES_URL is required for club competition")

    @asynccontextmanager
    async def idempotency_lock(self, user_id: str, scope: str, key: str):
        """Serialize equal mutation keys even when requests hit different API tasks."""
        lock_key = f"{user_id}:{scope}:{key}"
        async with self.engine.connect() as connection:
            await connection.execute(
                text("SELECT pg_advisory_lock(hashtextextended(:key, 0))"),
                {"key": lock_key},
            )
            try:
                yield
            finally:
                await connection.execute(
                    text("SELECT pg_advisory_unlock(hashtextextended(:key, 0))"),
                    {"key": lock_key},
                )

    async def idempotency_result(
        self, user_id: str, scope: str, key: str, request_hash: str
    ) -> Optional[Any]:
        async with self.engine.connect() as connection:
            row = (
                await connection.execute(
                    text(
                        """
                        SELECT request_hash, response_body
                        FROM idempotency_records
                        WHERE user_id=CAST(:user AS uuid) AND scope=:scope
                          AND idempotency_key=:key AND expires_at>NOW()
                        """
                    ),
                    {"user": user_id, "scope": scope, "key": key},
                )
            ).first()
        if not row:
            return None
        if row.request_hash != request_hash:
            raise DomainConflict("Idempotency-Key was already used with a different request")
        return row.response_body

    async def save_idempotency_result(
        self,
        user_id: str,
        scope: str,
        key: str,
        request_hash: str,
        response_body: Any,
        response_status: int = 200,
    ) -> None:
        async with self.engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO idempotency_records (
                        user_id, scope, idempotency_key, request_hash,
                        response_status, response_body
                    ) VALUES (
                        CAST(:user AS uuid), :scope, :key, :request_hash,
                        :status, CAST(:body AS jsonb)
                    )
                    ON CONFLICT (user_id, scope, idempotency_key) DO NOTHING
                    """
                ),
                {
                    "user": user_id,
                    "scope": scope,
                    "key": key,
                    "request_hash": request_hash,
                    "status": response_status,
                    "body": _json(response_body),
                },
            )

    async def _membership(
        self,
        connection: AsyncConnection,
        club_id: str,
        user_id: str,
        *,
        lock: bool = False,
    ) -> Optional[Dict[str, Any]]:
        suffix = " FOR UPDATE" if lock else ""
        row = (
            await connection.execute(
                text(
                    """
                    SELECT id, club_id, user_id, role::text AS role, status::text AS status,
                           requested_at, joined_at, ended_at, version, created_at, updated_at
                    FROM club_memberships
                    WHERE club_id = CAST(:club_id AS uuid) AND user_id = CAST(:user_id AS uuid)
                    """
                    + suffix
                ),
                {"club_id": club_id, "user_id": user_id},
            )
        ).first()
        return _dict(row) if row else None

    async def _ensure_primary_club(
        self,
        connection: AsyncConnection,
        user_id: str,
        preferred_club_id: Optional[str] = None,
    ) -> Optional[str]:
        """Maintain one primary club whenever the athlete has an active membership."""
        current = await connection.scalar(
            text(
                """
                SELECT p.primary_club_id
                FROM athlete_competitive_profiles p
                JOIN club_memberships m
                  ON m.club_id=p.primary_club_id AND m.user_id=p.user_id
                JOIN clubs c ON c.id=m.club_id
                WHERE p.user_id=CAST(:user AS uuid)
                  AND m.status='active' AND c.status='active'
                """
            ),
            {"user": user_id},
        )
        if current:
            return str(current)
        previous_profile = await connection.scalar(
            text(
                """
                SELECT primary_club_id FROM athlete_competitive_profiles
                WHERE user_id=CAST(:user AS uuid)
                """
            ),
            {"user": user_id},
        )
        selected = None
        if preferred_club_id:
            selected = await connection.scalar(
                text(
                    """
                    SELECT m.club_id
                    FROM club_memberships m
                    JOIN clubs c ON c.id=m.club_id
                    WHERE m.user_id=CAST(:user AS uuid)
                      AND m.club_id=CAST(:club AS uuid)
                      AND m.status='active' AND c.status='active'
                    """
                ),
                {"user": user_id, "club": preferred_club_id},
            )
        if not selected:
            selected = await connection.scalar(
                text(
                    """
                    SELECT m.club_id
                    FROM club_memberships m
                    JOIN clubs c ON c.id=m.club_id
                    WHERE m.user_id=CAST(:user AS uuid)
                      AND m.status='active' AND c.status='active'
                    ORDER BY m.joined_at, m.created_at, m.club_id
                    LIMIT 1
                    """
                ),
                {"user": user_id},
            )
        if not selected:
            await connection.execute(
                text(
                    """
                    UPDATE athlete_competitive_profiles
                    SET primary_club_id=NULL, primary_selected_at=NULL,
                        primary_switch_available_at=NULL, updated_at=NOW()
                    WHERE user_id=CAST(:user AS uuid)
                    """
                ),
                {"user": user_id},
            )
            if previous_profile:
                await connection.execute(
                    text(
                        """
                        UPDATE athlete_primary_club_history
                        SET effective_to=NOW()
                        WHERE user_id=CAST(:user AS uuid) AND effective_to IS NULL
                        """
                    ),
                    {"user": user_id},
                )
            return None
        if str(previous_profile) != str(selected):
            await connection.execute(
                text(
                    """
                    UPDATE athlete_primary_club_history SET effective_to=NOW()
                    WHERE user_id=CAST(:user AS uuid) AND effective_to IS NULL
                    """
                ),
                {"user": user_id},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO athlete_primary_club_history (
                        id, user_id, club_id, effective_from, reason
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:user AS uuid), :club, NOW(), :reason
                    )
                    """
                ),
                {
                    "id": new_id(),
                    "user": user_id,
                    "club": selected,
                    "reason": "automatic_assignment"
                    if previous_profile is None
                    else "membership_change",
                },
            )
        await connection.execute(
            text(
                """
                INSERT INTO athlete_competitive_profiles (
                    user_id, primary_club_id, primary_selected_at,
                    primary_switch_available_at
                ) VALUES (
                    CAST(:user AS uuid), :club, NOW(), NOW()
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    primary_club_id=EXCLUDED.primary_club_id,
                    primary_selected_at=EXCLUDED.primary_selected_at,
                    primary_switch_available_at=EXCLUDED.primary_switch_available_at,
                    updated_at=NOW()
                """
            ),
            {"user": user_id, "club": selected},
        )
        return str(selected)

    async def _require_role(
        self,
        connection: AsyncConnection,
        club_id: str,
        user_id: str,
        roles: Iterable[str],
    ) -> Dict[str, Any]:
        membership = await self._membership(connection, club_id, user_id, lock=True)
        if (
            not membership
            or membership["status"] != "active"
            or membership["role"] not in set(roles)
        ):
            raise DomainForbidden("Insufficient club permission")
        return membership

    async def _audit(
        self,
        connection: AsyncConnection,
        *,
        actor_user_id: Optional[str],
        club_id: Optional[str],
        action: str,
        target_type: str,
        target_id: Optional[str],
        before: Any = None,
        after: Any = None,
        request_id: Optional[str] = None,
    ) -> None:
        await connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    id, actor_user_id, club_id, action, target_type, target_id,
                    request_id, before_state, after_state
                ) VALUES (
                    CAST(:id AS uuid), CAST(:actor AS uuid), CAST(:club_id AS uuid),
                    :action, :target_type, CAST(:target_id AS uuid), :request_id,
                    CAST(:before AS jsonb), CAST(:after AS jsonb)
                )
                """
            ),
            {
                "id": new_id(),
                "actor": actor_user_id,
                "club_id": club_id,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "request_id": request_id,
                "before": _json(before) if before is not None else None,
                "after": _json(after) if after is not None else None,
            },
        )

    async def _event(
        self,
        connection: AsyncConnection,
        *,
        club_id: Optional[str],
        actor_user_id: Optional[str],
        event_type: str,
        source_type: str,
        source_id: Optional[str],
        payload: Dict[str, Any],
        visibility: str = "club",
        idempotency_key: str,
    ) -> str:
        event_id = new_id()
        result = await connection.execute(
            text(
                """
                INSERT INTO system_activity_events (
                    id, club_id, actor_user_id, event_type, visibility,
                    source_type, source_id, payload, idempotency_key
                ) VALUES (
                    CAST(:id AS uuid), CAST(:club_id AS uuid), CAST(:actor AS uuid),
                    :event_type, CAST(:visibility AS activity_visibility), :source_type,
                    CAST(:source_id AS uuid), CAST(:payload AS jsonb), :key
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING id
                """
            ),
            {
                "id": event_id,
                "club_id": club_id,
                "actor": actor_user_id,
                "event_type": event_type,
                "visibility": visibility,
                "source_type": source_type,
                "source_id": source_id,
                "payload": _json(payload),
                "key": idempotency_key,
            },
        )
        row = result.first()
        return str(row[0]) if row else event_id

    async def _outbox(
        self,
        connection: AsyncConnection,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        encoded_payload = _json(payload)
        identity = hashlib.sha256(
            f"{aggregate_type}:{aggregate_id}:{event_type}:{encoded_payload}".encode()
        ).hexdigest()
        await connection.execute(
            text(
                """
                INSERT INTO outbox_events (
                    id, idempotency_key, aggregate_type, aggregate_id,
                    event_type, payload
                ) VALUES (
                    CAST(:id AS uuid), :key, :aggregate_type,
                    CAST(:aggregate_id AS uuid), :event_type, CAST(:payload AS jsonb)
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """
            ),
            {
                "id": new_id(),
                "key": identity,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "event_type": event_type,
                "payload": encoded_payload,
            },
        )

    async def create_club(
        self,
        payload: Dict[str, Any],
        user_id: str,
        *,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        _uuid(user_id)
        club_id, membership_id = new_id(), new_id()
        requested_slug = slugify(payload.get("slug") or payload["name"])
        location = None
        if payload.get("latitude") is not None:
            location = json.dumps(
                {
                    "type": "Point",
                    "coordinates": [payload["longitude"], payload["latitude"]],
                }
            )
        async with self.engine.begin() as connection:
            slug = requested_slug
            for attempt in range(20):
                exists = await connection.scalar(
                    text("SELECT EXISTS(SELECT 1 FROM clubs WHERE slug = :slug)"),
                    {"slug": slug},
                )
                if not exists:
                    break
                slug = f"{requested_slug[:72]}-{attempt + 2}"
            else:
                raise DomainConflict("Unable to allocate a unique club slug")

            await connection.execute(
                text(
                    """
                    INSERT INTO clubs (
                        id, slug, name, description, rules, visibility, owner_user_id,
                        home_region_id, timezone, home_location, primary_color, emoji,
                        avatar_url, banner_url
                    ) VALUES (
                        CAST(:id AS uuid), :slug, :name, :description, :rules,
                        CAST(:visibility AS club_visibility), CAST(:owner AS uuid),
                        CAST(:region AS uuid), :timezone,
                        CASE WHEN :location IS NULL THEN NULL
                             ELSE ST_SetSRID(ST_GeomFromGeoJSON(:location), 4326) END,
                        :color, :emoji, :avatar, :banner
                    )
                    """
                ),
                {
                    "id": club_id,
                    "slug": slug,
                    "name": payload["name"].strip(),
                    "description": payload.get("description"),
                    "rules": payload.get("rules"),
                    "visibility": payload.get("visibility", "public"),
                    "owner": user_id,
                    "region": payload.get("home_region_id"),
                    "timezone": payload.get("timezone") or "UTC",
                    "location": location,
                    "color": payload.get("primary_color") or "#FF4F2E",
                    "emoji": payload.get("emoji") or "🏃",
                    "avatar": payload.get("avatar_url"),
                    "banner": payload.get("banner_url"),
                },
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO club_memberships (
                        id, club_id, user_id, role, status, joined_at
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:club AS uuid), CAST(:user AS uuid),
                        'owner', 'active', NOW()
                    )
                    """
                ),
                {"id": membership_id, "club": club_id, "user": user_id},
            )
            await self._ensure_primary_club(connection, user_id, club_id)
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=user_id,
                event_type="club_created",
                source_type="club",
                source_id=club_id,
                payload={"club_id": club_id, "name": payload["name"].strip()},
                idempotency_key=f"club:{club_id}:created",
            )
            await self._audit(
                connection,
                actor_user_id=user_id,
                club_id=club_id,
                action="club.create",
                target_type="club",
                target_id=club_id,
                after={"name": payload["name"].strip(), "slug": slug},
                request_id=request_id,
            )
            await self._outbox(
                connection,
                "club",
                club_id,
                "club.created",
                {"club_id": club_id, "owner_user_id": user_id},
            )
        return await self.get_club(club_id, user_id)

    async def get_club(self, club_id: str, viewer_user_id: str) -> Dict[str, Any]:
        async with self.engine.connect() as connection:
            row = (
                await connection.execute(
                    text(
                        """
                        SELECT c.id, c.slug, c.name, c.description, c.rules,
                               c.visibility::text AS visibility, c.status::text AS status,
                               c.owner_user_id, c.home_region_id, c.timezone,
                               c.primary_color, c.emoji, c.avatar_url, c.banner_url,
                               c.version, c.created_at, c.updated_at,
                               ST_Y(c.home_location) AS latitude,
                               ST_X(c.home_location) AS longitude,
                               COUNT(m.id) FILTER (WHERE m.status = 'active')::int AS member_count,
                               vm.role::text AS viewer_role,
                               vm.status::text AS viewer_membership_status,
                               (p.primary_club_id = c.id) AS is_primary
                        FROM clubs c
                        LEFT JOIN club_memberships m ON m.club_id = c.id
                        LEFT JOIN club_memberships vm
                          ON vm.club_id = c.id AND vm.user_id = CAST(:viewer AS uuid)
                        LEFT JOIN athlete_competitive_profiles p
                          ON p.user_id = CAST(:viewer AS uuid)
                        WHERE c.id = CAST(:club AS uuid)
                        GROUP BY c.id, vm.role, vm.status, p.primary_club_id
                        """
                    ),
                    {"club": club_id, "viewer": viewer_user_id},
                )
            ).first()
        if not row:
            raise DomainNotFound("Club not found")
        club = _dict(row)
        if club["status"] != "active" and club.get("viewer_role") not in {"owner", "admin"}:
            raise DomainNotFound("Club not found")
        if club["visibility"] == "private" and club.get("viewer_membership_status") != "active":
            # Private clubs remain discoverable and joinable, but their rules and
            # descriptive content are membership-only.
            club["description"] = None
            club["rules"] = None
        return club

    async def list_clubs(
        self,
        viewer_user_id: str,
        *,
        query: Optional[str] = None,
        region_id: Optional[str] = None,
        membership: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        cursor_time, cursor_id = decode_cursor(cursor)
        where = ["c.status = 'active'"]
        params: Dict[str, Any] = {
            "viewer": viewer_user_id,
            "limit": max(1, min(limit, 100)) + 1,
            "query": f"%{(query or '').strip()}%",
            "region": region_id,
            "cursor_time": cursor_time,
            "cursor_id": cursor_id,
        }
        if query:
            where.append("(c.name ILIKE :query OR c.slug ILIKE :query)")
        if region_id:
            where.append("c.home_region_id = CAST(:region AS uuid)")
        if membership == "mine":
            where.append("vm.status = 'active'")
        if cursor_time:
            where.append("(c.created_at, c.id) < (:cursor_time, CAST(:cursor_id AS uuid))")
        statement = f"""
            SELECT c.id, c.slug, c.name, c.description, c.visibility::text AS visibility,
                   c.status::text AS status, c.home_region_id, c.timezone,
                   c.primary_color, c.emoji, c.avatar_url, c.banner_url,
                   c.version, c.created_at,
                   COUNT(m.id) FILTER (WHERE m.status = 'active')::int AS member_count,
                   vm.role::text AS viewer_role,
                   vm.status::text AS viewer_membership_status,
                   (p.primary_club_id = c.id) AS is_primary
            FROM clubs c
            LEFT JOIN club_memberships m ON m.club_id = c.id
            LEFT JOIN club_memberships vm
              ON vm.club_id = c.id AND vm.user_id = CAST(:viewer AS uuid)
            LEFT JOIN athlete_competitive_profiles p
              ON p.user_id = CAST(:viewer AS uuid)
            WHERE {" AND ".join(where)}
            GROUP BY c.id, vm.role, vm.status, p.primary_club_id
            ORDER BY c.created_at DESC, c.id DESC
            LIMIT :limit
        """
        async with self.engine.connect() as connection:
            rows = [_dict(row) for row in (await connection.execute(text(statement), params))]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["created_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def update_club(
        self,
        club_id: str,
        user_id: str,
        payload: Dict[str, Any],
        *,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, user_id, {"owner", "admin"})
            current = (
                await connection.execute(
                    text("SELECT * FROM clubs WHERE id = CAST(:id AS uuid) FOR UPDATE"),
                    {"id": club_id},
                )
            ).first()
            if not current:
                raise DomainNotFound("Club not found")
            before = _dict(current)
            if before["version"] != payload["version"]:
                raise DomainConflict("Club was changed by another administrator")
            location = None
            if payload.get("latitude") is not None:
                location = _json(
                    {
                        "type": "Point",
                        "coordinates": [payload["longitude"], payload["latitude"]],
                    }
                )
            await connection.execute(
                text(
                    """
                    UPDATE clubs SET
                        name = COALESCE(:name, name),
                        description = CASE WHEN :has_description THEN :description ELSE description END,
                        rules = CASE WHEN :has_rules THEN :rules ELSE rules END,
                        visibility = COALESCE(CAST(:visibility AS club_visibility), visibility),
                        home_region_id = CASE WHEN :has_region THEN CAST(:region AS uuid) ELSE home_region_id END,
                        timezone = COALESCE(:timezone, timezone),
                        home_location = CASE WHEN :location IS NOT NULL
                            THEN ST_SetSRID(ST_GeomFromGeoJSON(:location), 4326)
                            ELSE home_location END,
                        primary_color = COALESCE(:color, primary_color),
                        emoji = COALESCE(:emoji, emoji),
                        avatar_url = CASE WHEN :has_avatar THEN :avatar ELSE avatar_url END,
                        banner_url = CASE WHEN :has_banner THEN :banner ELSE banner_url END,
                        version = version + 1, updated_at = NOW()
                    WHERE id = CAST(:id AS uuid) AND version = :version
                    """
                ),
                {
                    "id": club_id,
                    "version": payload["version"],
                    "name": payload.get("name"),
                    "description": payload.get("description"),
                    "has_description": "description" in payload,
                    "rules": payload.get("rules"),
                    "has_rules": "rules" in payload,
                    "visibility": payload.get("visibility"),
                    "region": payload.get("home_region_id"),
                    "has_region": "home_region_id" in payload,
                    "timezone": payload.get("timezone"),
                    "location": location,
                    "color": payload.get("primary_color"),
                    "emoji": payload.get("emoji"),
                    "avatar": payload.get("avatar_url"),
                    "has_avatar": "avatar_url" in payload,
                    "banner": payload.get("banner_url"),
                    "has_banner": "banner_url" in payload,
                },
            )
            await self._audit(
                connection,
                actor_user_id=user_id,
                club_id=club_id,
                action="club.update",
                target_type="club",
                target_id=club_id,
                before=before,
                after=payload,
                request_id=request_id,
            )
        return await self.get_club(club_id, user_id)

    async def join(self, club_id: str, user_id: str) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            club = (
                await connection.execute(
                    text(
                        """
                        SELECT id, name, visibility::text AS visibility, status::text AS status
                        FROM clubs WHERE id = CAST(:id AS uuid) FOR UPDATE
                        """
                    ),
                    {"id": club_id},
                )
            ).first()
            if not club or club.status != "active":
                raise DomainNotFound("Club not found")
            banned = await connection.scalar(
                text(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM club_bans
                        WHERE club_id = CAST(:club AS uuid)
                          AND user_id = CAST(:user AS uuid)
                          AND revoked_at IS NULL
                          AND (expires_at IS NULL OR expires_at > NOW())
                    )
                    """
                ),
                {"club": club_id, "user": user_id},
            )
            if banned:
                raise DomainForbidden("You cannot join this club")
            membership = await self._membership(connection, club_id, user_id, lock=True)
            desired = "active" if club.visibility == "public" else "pending"
            if membership and membership["status"] in {"active", "pending"}:
                return membership
            membership_id = membership["id"] if membership else new_id()
            await connection.execute(
                text(
                    """
                    INSERT INTO club_memberships (
                        id, club_id, user_id, role, status, requested_at, joined_at
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:club AS uuid), CAST(:user AS uuid),
                        'member', CAST(:status AS membership_status), NOW(),
                        CASE WHEN :status = 'active' THEN NOW() ELSE NULL END
                    )
                    ON CONFLICT (club_id, user_id) DO UPDATE SET
                        role = 'member',
                        status = EXCLUDED.status,
                        requested_at = NOW(),
                        joined_at = CASE WHEN EXCLUDED.status = 'active' THEN NOW() ELSE NULL END,
                        ended_at = NULL,
                        review_reason = NULL,
                        version = club_memberships.version + 1,
                        updated_at = NOW()
                    """
                ),
                {
                    "id": membership_id,
                    "club": club_id,
                    "user": user_id,
                    "status": desired,
                },
            )
            if desired == "active":
                await self._ensure_primary_club(connection, user_id, club_id)
            event_type = "member_joined" if desired == "active" else "membership_requested"
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=user_id,
                event_type=event_type,
                source_type="membership",
                source_id=membership_id,
                payload={"club_id": club_id, "user_id": user_id},
                idempotency_key=f"membership:{membership_id}:{desired}",
            )
            await self._outbox(
                connection,
                "membership",
                membership_id,
                f"club.{event_type}",
                {"club_id": club_id, "user_id": user_id},
            )
        async with self.engine.connect() as connection:
            result = await self._membership(connection, club_id, user_id)
            assert result
            return result

    async def review_membership(
        self,
        club_id: str,
        target_user_id: str,
        actor_user_id: str,
        *,
        approve: bool,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, actor_user_id, {"owner", "admin"})
            target = await self._membership(connection, club_id, target_user_id, lock=True)
            if not target or target["status"] != "pending":
                raise DomainNotFound("Pending membership not found")
            status = "active" if approve else "rejected"
            result = await connection.execute(
                text(
                    """
                    UPDATE club_memberships SET
                        status = CAST(:status AS membership_status),
                        joined_at = CASE WHEN :status = 'active' THEN NOW() ELSE joined_at END,
                        ended_at = CASE WHEN :status = 'rejected' THEN NOW() ELSE NULL END,
                        reviewed_by_user_id = CAST(:actor AS uuid),
                        review_reason = :reason,
                        version = version + 1,
                        updated_at = NOW()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING id, club_id, user_id, role::text AS role,
                              status::text AS status, joined_at, version, updated_at
                    """
                ),
                {
                    "status": status,
                    "actor": actor_user_id,
                    "reason": reason,
                    "id": target["id"],
                },
            )
            reviewed = _dict(result.first())
            if approve:
                await self._ensure_primary_club(
                    connection, target_user_id, club_id
                )
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=actor_user_id,
                event_type=f"membership_{'approved' if approve else 'rejected'}",
                source_type="membership",
                source_id=target["id"],
                payload={"user_id": target_user_id, "reason": reason},
                idempotency_key=f"membership:{target['id']}:{status}:{reviewed['version']}",
            )
            await self._outbox(
                connection,
                "membership",
                target["id"],
                f"club.membership_{status}",
                {"club_id": club_id, "user_id": target_user_id},
            )
            return reviewed

    async def end_membership(
        self,
        club_id: str,
        target_user_id: str,
        actor_user_id: str,
        *,
        ban: bool = False,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            target = await self._membership(connection, club_id, target_user_id, lock=True)
            if not target or target["status"] not in {"active", "pending"}:
                raise DomainNotFound("Membership not found")
            if target["role"] == "owner":
                raise DomainConflict("Transfer ownership before removing the owner")
            if actor_user_id != target_user_id:
                actor = await self._require_role(
                    connection, club_id, actor_user_id, {"owner", "admin"}
                )
                if target["role"] == "admin" and actor["role"] != "owner":
                    raise DomainForbidden("Only the owner can remove an administrator")
            status = "banned" if ban else "removed"
            await connection.execute(
                text(
                    """
                    UPDATE club_memberships SET status = CAST(:status AS membership_status),
                        ended_at = NOW(), review_reason = :reason,
                        version = version + 1, updated_at = NOW()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"status": status, "reason": reason, "id": target["id"]},
            )
            await connection.execute(
                text(
                    """
                    UPDATE athlete_competitive_profiles
                    SET primary_club_id = NULL, updated_at = NOW()
                    WHERE user_id = CAST(:user AS uuid)
                      AND primary_club_id = CAST(:club AS uuid)
                    """
                ),
                {"user": target_user_id, "club": club_id},
            )
            await self._ensure_primary_club(connection, target_user_id)
            if ban:
                await connection.execute(
                    text(
                        """
                        INSERT INTO club_bans (
                            id, club_id, user_id, reason, created_by_user_id
                        ) VALUES (
                            CAST(:id AS uuid), CAST(:club AS uuid), CAST(:user AS uuid),
                            :reason, CAST(:actor AS uuid)
                        )
                        ON CONFLICT (club_id, user_id) WHERE revoked_at IS NULL
                        DO UPDATE SET reason = EXCLUDED.reason,
                                      created_by_user_id = EXCLUDED.created_by_user_id
                        """
                    ),
                    {
                        "id": new_id(),
                        "club": club_id,
                        "user": target_user_id,
                        "reason": reason,
                        "actor": actor_user_id,
                    },
                )
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=actor_user_id,
                event_type="member_banned" if ban else "member_left",
                source_type="membership",
                source_id=target["id"],
                payload={"user_id": target_user_id, "reason": reason},
                idempotency_key=f"membership:{target['id']}:{status}:{target['version'] + 1}",
            )
            await self._outbox(
                connection,
                "membership",
                target["id"],
                "territory.membership_changed",
                {
                    "club_id": club_id,
                    "user_id": target_user_id,
                    "status": status,
                },
            )
        return {"status": status, "user_id": target_user_id}

    async def revoke_ban(
        self,
        club_id: str,
        target_user_id: str,
        actor_user_id: str,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, actor_user_id, {"owner", "admin"})
            result = await connection.execute(
                text(
                    """
                    UPDATE club_bans
                    SET revoked_at=NOW()
                    WHERE club_id=CAST(:club AS uuid)
                      AND user_id=CAST(:user AS uuid)
                      AND revoked_at IS NULL
                    RETURNING id
                    """
                ),
                {"club": club_id, "user": target_user_id},
            )
            if not result.first():
                raise DomainNotFound("Active ban not found")
            await self._audit(
                connection,
                actor_user_id=actor_user_id,
                club_id=club_id,
                action="club.unban_member",
                target_type="membership",
                target_id=target_user_id,
                after={"status": "unbanned"},
            )
            await self._outbox(
                connection,
                "club",
                club_id,
                "club.member_unbanned",
                {"club_id": club_id, "user_id": target_user_id},
            )
        return {"status": "unbanned", "user_id": target_user_id}

    async def update_role(
        self,
        club_id: str,
        target_user_id: str,
        actor_user_id: str,
        role: str,
        version: int,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, actor_user_id, {"owner"})
            target = await self._membership(connection, club_id, target_user_id, lock=True)
            if not target or target["status"] != "active" or target["role"] == "owner":
                raise DomainNotFound("Eligible member not found")
            if target["version"] != version:
                raise DomainConflict("Membership was changed by another administrator")
            row = (
                await connection.execute(
                    text(
                        """
                        UPDATE club_memberships SET role = CAST(:role AS club_role),
                            version = version + 1, updated_at = NOW()
                        WHERE id = CAST(:id AS uuid) AND version = :version
                        RETURNING id, club_id, user_id, role::text AS role,
                                  status::text AS status, version, updated_at
                        """
                    ),
                    {"role": role, "id": target["id"], "version": version},
                )
            ).first()
            return _dict(row)

    async def transfer_ownership(
        self,
        club_id: str,
        actor_user_id: str,
        target_user_id: str,
        version: int,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            owner = await self._require_role(connection, club_id, actor_user_id, {"owner"})
            if owner["version"] != version:
                raise DomainConflict("Owner membership changed; refresh and retry")
            target = await self._membership(connection, club_id, target_user_id, lock=True)
            if not target or target["status"] != "active":
                raise DomainNotFound("New owner must be an active club member")
            await connection.execute(
                text(
                    """
                    UPDATE club_memberships SET role = 'member',
                        version = version + 1, updated_at = NOW()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": owner["id"]},
            )
            await connection.execute(
                text(
                    """
                    UPDATE club_memberships SET role = 'owner',
                        version = version + 1, updated_at = NOW()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": target["id"]},
            )
            await connection.execute(
                text(
                    """
                    UPDATE clubs SET owner_user_id = CAST(:owner AS uuid),
                        version = version + 1, updated_at = NOW()
                    WHERE id = CAST(:club AS uuid)
                    """
                ),
                {"owner": target_user_id, "club": club_id},
            )
            await self._audit(
                connection,
                actor_user_id=actor_user_id,
                club_id=club_id,
                action="club.transfer_ownership",
                target_type="membership",
                target_id=target["id"],
                before={"owner_user_id": actor_user_id},
                after={"owner_user_id": target_user_id},
            )
        return await self.get_club(club_id, actor_user_id)

    async def set_primary_club(self, user_id: str, club_id: str) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            membership = await self._membership(connection, club_id, user_id, lock=True)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Primary club must be an active membership")
            profile = (
                await connection.execute(
                    text(
                        """
                        SELECT user_id, primary_club_id, primary_selected_at,
                               primary_switch_available_at
                        FROM athlete_competitive_profiles
                        WHERE user_id = CAST(:user AS uuid)
                        FOR UPDATE
                        """
                    ),
                    {"user": user_id},
                )
            ).first()
            if profile and profile.primary_club_id == _uuid(club_id):
                return _dict(profile)
            now = utc_now()
            if (
                profile
                and profile.primary_switch_available_at
                and profile.primary_switch_available_at > now
            ):
                raise DomainConflict(
                    f"Primary club can be changed after "
                    f"{profile.primary_switch_available_at.isoformat()}"
                )
            available = now + timedelta(days=PRIMARY_CLUB_COOLDOWN_DAYS)
            await connection.execute(
                text(
                    """
                    UPDATE athlete_primary_club_history SET effective_to=:now
                    WHERE user_id=CAST(:user AS uuid) AND effective_to IS NULL
                    """
                ),
                {"user": user_id, "now": now},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO athlete_primary_club_history (
                        id, user_id, club_id, effective_from, reason
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:user AS uuid),
                        CAST(:club AS uuid), :now, 'athlete_selection'
                    )
                    """
                ),
                {"id": new_id(), "user": user_id, "club": club_id, "now": now},
            )
            result = await connection.execute(
                text(
                    """
                    INSERT INTO athlete_competitive_profiles (
                        user_id, primary_club_id, primary_selected_at,
                        primary_switch_available_at
                    ) VALUES (
                        CAST(:user AS uuid), CAST(:club AS uuid), :now, :available
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        primary_club_id = EXCLUDED.primary_club_id,
                        primary_selected_at = EXCLUDED.primary_selected_at,
                        primary_switch_available_at = EXCLUDED.primary_switch_available_at,
                        updated_at = NOW()
                    RETURNING user_id, primary_club_id, primary_selected_at,
                              primary_switch_available_at
                    """
                ),
                {
                    "user": user_id,
                    "club": club_id,
                    "now": now,
                    "available": available,
                },
            )
            selected = _dict(result.first())
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=user_id,
                event_type="primary_club_selected",
                source_type="club",
                source_id=club_id,
                payload={"user_id": user_id},
                idempotency_key=f"primary:{user_id}:{club_id}:{now.isoformat()}",
            )
            await self._audit(
                connection,
                actor_user_id=user_id,
                club_id=club_id,
                action="club.select_primary",
                target_type="competitive_profile",
                target_id=user_id,
                before={
                    "primary_club_id": str(profile.primary_club_id)
                    if profile and profile.primary_club_id
                    else None
                },
                after={"primary_club_id": club_id},
            )
            await self._outbox(
                connection,
                "competitive_profile",
                user_id,
                "club.primary_changed",
                {
                    "user_id": user_id,
                    "previous_club_id": str(profile.primary_club_id)
                    if profile and profile.primary_club_id
                    else None,
                    "club_id": club_id,
                },
            )
            return selected

    async def members(
        self,
        club_id: str,
        viewer_user_id: str,
        *,
        status: str = "active",
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        async with self.engine.connect() as connection:
            viewer = await self._membership(connection, club_id, viewer_user_id)
            club = (
                await connection.execute(
                    text("SELECT visibility::text AS visibility FROM clubs WHERE id=CAST(:id AS uuid)"),
                    {"id": club_id},
                )
            ).first()
            if not club:
                raise DomainNotFound("Club not found")
            if status != "active" and (
                not viewer
                or viewer["status"] != "active"
                or viewer["role"] not in {"owner", "admin"}
            ):
                raise DomainForbidden("Only administrators can view membership requests")
            if club.visibility == "private" and (not viewer or viewer["status"] != "active"):
                raise DomainForbidden("Active membership is required")
            cursor_time, cursor_id = decode_cursor(cursor)
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, club_id, user_id, role::text AS role,
                               status::text AS status, requested_at, joined_at,
                               version, created_at, updated_at
                        FROM club_memberships
                        WHERE club_id = CAST(:club AS uuid)
                          AND status = CAST(:status AS membership_status)
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (created_at, id) < (
                                CAST(:cursor_time AS timestamptz),
                                CAST(:cursor_id AS uuid)
                            )
                          )
                        ORDER BY created_at DESC, id DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "club": club_id,
                        "status": status,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["created_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def archive(self, club_id: str, user_id: str, archived: bool) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, user_id, {"owner"})
            await connection.execute(
                text(
                    """
                    UPDATE clubs SET
                        status = CAST(:status AS club_status),
                        archived_at = CASE WHEN :archived THEN NOW() ELSE NULL END,
                        version = version + 1, updated_at = NOW()
                    WHERE id = CAST(:club AS uuid)
                    """
                ),
                {
                    "status": "archived" if archived else "active",
                    "archived": archived,
                    "club": club_id,
                },
            )
            member_ids = [
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
            for member_id in member_ids:
                await self._ensure_primary_club(
                    connection, member_id, None if archived else club_id
                )
            await self._audit(
                connection,
                actor_user_id=user_id,
                club_id=club_id,
                action="club.archive" if archived else "club.restore",
                target_type="club",
                target_id=club_id,
                after={"status": "archived" if archived else "active"},
            )
            await self._outbox(
                connection,
                "club",
                club_id,
                "territory.club_status_changed",
                {"club_id": club_id, "archived": archived},
            )
        return await self.get_club(club_id, user_id)

    async def create_invitation(
        self,
        club_id: str,
        actor_user_id: str,
        payload: Dict[str, Any],
        token_hash: str,
    ) -> Dict[str, Any]:
        invitation_id = new_id()
        email_hash = (
            hashlib.sha256(payload["email"].strip().lower().encode()).hexdigest()
            if payload.get("email")
            else None
        )
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, actor_user_id, {"owner", "admin"})
            result = await connection.execute(
                text(
                    """
                    INSERT INTO club_invitations (
                        id, club_id, token_hash, invited_user_id, invited_email_hash,
                        role, created_by_user_id, expires_at
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:club AS uuid), :token,
                        CAST(:user AS uuid), :email_hash, CAST(:role AS club_role),
                        CAST(:actor AS uuid), NOW() + (:days * INTERVAL '1 day')
                    )
                    RETURNING id, club_id, invited_user_id, role::text AS role,
                              expires_at, created_at
                    """
                ),
                {
                    "id": invitation_id,
                    "club": club_id,
                    "token": token_hash,
                    "user": payload.get("invited_user_id"),
                    "email_hash": email_hash,
                    "role": payload.get("role", "member"),
                    "actor": actor_user_id,
                    "days": payload.get("expires_in_days", 7),
                },
            )
            invitation = _dict(result.first())
            await self._audit(
                connection,
                actor_user_id=actor_user_id,
                club_id=club_id,
                action="club.invitation_create",
                target_type="invitation",
                target_id=invitation_id,
                after={
                    "invited_user_id": payload.get("invited_user_id"),
                    "role": payload.get("role", "member"),
                    "expires_at": invitation.get("expires_at"),
                },
            )
            return invitation

    async def invitations(
        self, club_id: str, actor_user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        async with self.engine.connect() as connection:
            await self._require_role(
                connection, club_id, actor_user_id, {"owner", "admin"}
            )
            return [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, club_id, invited_user_id, role::text AS role,
                               expires_at, accepted_at, revoked_at, created_at
                        FROM club_invitations
                        WHERE club_id=CAST(:club AS uuid)
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"club": club_id, "limit": max(1, min(limit, 100))},
                )
            ]

    async def revoke_invitation(
        self, club_id: str, invitation_id: str, actor_user_id: str
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            await self._require_role(
                connection, club_id, actor_user_id, {"owner", "admin"}
            )
            result = await connection.execute(
                text(
                    """
                    UPDATE club_invitations SET revoked_at=NOW()
                    WHERE id=CAST(:invitation AS uuid)
                      AND club_id=CAST(:club AS uuid)
                      AND accepted_at IS NULL AND revoked_at IS NULL
                    """
                ),
                {"invitation": invitation_id, "club": club_id},
            )
            if not result.rowcount:
                raise DomainNotFound("Active invitation not found")
            await self._audit(
                connection,
                actor_user_id=actor_user_id,
                club_id=club_id,
                action="club.invitation_revoke",
                target_type="invitation",
                target_id=invitation_id,
            )
            return {"id": invitation_id, "revoked": True}

    async def accept_invitation(
        self, token_hash: str, user_id: str, email_hash: Optional[str]
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            invitation = (
                await connection.execute(
                    text(
                        """
                        SELECT id, club_id, invited_user_id, invited_email_hash,
                               role::text AS role
                        FROM club_invitations
                        WHERE token_hash=:token AND accepted_at IS NULL
                          AND revoked_at IS NULL AND expires_at>NOW()
                        FOR UPDATE
                        """
                    ),
                    {"token": token_hash},
                )
            ).first()
            if not invitation:
                raise DomainNotFound("Invitation is invalid or expired")
            if invitation.invited_user_id and str(invitation.invited_user_id) != user_id:
                raise DomainForbidden("Invitation belongs to another athlete")
            if (
                invitation.invited_email_hash
                and invitation.invited_email_hash != email_hash
            ):
                raise DomainForbidden("Invitation belongs to another email address")
            banned = await connection.scalar(
                text(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM club_bans
                        WHERE club_id=:club AND user_id=CAST(:user AS uuid)
                          AND revoked_at IS NULL
                          AND (expires_at IS NULL OR expires_at>NOW())
                    )
                    """
                ),
                {"club": invitation.club_id, "user": user_id},
            )
            if banned:
                raise DomainForbidden("You cannot join this club")
            membership_id = new_id()
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO club_memberships (
                            id, club_id, user_id, role, status, joined_at
                        ) VALUES (
                            CAST(:id AS uuid), :club, CAST(:user AS uuid),
                            CAST(:role AS club_role), 'active', NOW()
                        )
                        ON CONFLICT (club_id, user_id) DO UPDATE SET
                            role=EXCLUDED.role, status='active', joined_at=NOW(),
                            ended_at=NULL, version=club_memberships.version+1,
                            updated_at=NOW()
                        RETURNING id, club_id, user_id, role::text AS role,
                                  status::text AS status, joined_at, version
                        """
                    ),
                    {
                        "id": membership_id,
                        "club": invitation.club_id,
                        "user": user_id,
                        "role": invitation.role,
                    },
                )
            ).first()
            await connection.execute(
                text("UPDATE club_invitations SET accepted_at=NOW() WHERE id=:id"),
                {"id": invitation.id},
            )
            await self._ensure_primary_club(
                connection, user_id, str(invitation.club_id)
            )
            accepted = _dict(row)
            await self._event(
                connection,
                club_id=str(invitation.club_id),
                actor_user_id=user_id,
                event_type="member_joined",
                source_type="membership",
                source_id=accepted["id"],
                payload={"club_id": str(invitation.club_id), "user_id": user_id},
                idempotency_key=f"membership:{accepted['id']}:invitation-accepted",
            )
            await self._outbox(
                connection,
                "membership",
                accepted["id"],
                "club.member_joined",
                {"club_id": str(invitation.club_id), "user_id": user_id},
            )
            return accepted

    async def club_timeline(
        self,
        club_id: str,
        viewer_user_id: str,
        cursor: Optional[str],
        limit: int,
    ) -> Dict[str, Any]:
        async with self.engine.connect() as connection:
            membership = await self._membership(connection, club_id, viewer_user_id)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active membership is required")
            cursor_time, cursor_id = decode_cursor(cursor)
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, club_id, actor_user_id, event_type,
                               visibility::text AS visibility, source_type,
                               source_id, payload, occurred_at
                        FROM system_activity_events
                        WHERE club_id = CAST(:club AS uuid)
                          AND visibility IN ('club', 'public')
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (occurred_at, id) < (
                                CAST(:cursor_time AS timestamptz),
                                CAST(:cursor_id AS uuid)
                            )
                          )
                        ORDER BY occurred_at DESC, id DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "club": club_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["occurred_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def leaderboard(
        self,
        club_id: str,
        viewer_user_id: str,
        *,
        period: str,
        metric: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        allowed_periods = {
            "week": "date_trunc('week', NOW())",
            "month": "date_trunc('month', NOW())",
            "season": "COALESCE((SELECT starts_at FROM seasons WHERE status='active' LIMIT 1), date_trunc('quarter', NOW()))",
            "all": "'1970-01-01'::timestamptz",
        }
        metric_columns = {
            "distance": "SUM(distance_m)",
            "moving_time": "SUM(moving_time_sec)",
            "runs": "SUM(run_count)",
            "territory_gain": "SUM(territory_gain_m)",
            "consistency": "COUNT(DISTINCT consistency_date)",
        }
        if period not in allowed_periods or metric not in metric_columns:
            raise DomainConflict("Unsupported leaderboard period or metric")
        async with self.engine.connect() as connection:
            membership = await self._membership(connection, club_id, viewer_user_id)
            club = (
                await connection.execute(
                    text("SELECT visibility::text AS visibility FROM clubs WHERE id=CAST(:id AS uuid)"),
                    {"id": club_id},
                )
            ).first()
            if not club:
                raise DomainNotFound("Club not found")
            if club.visibility == "private" and (
                not membership or membership["status"] != "active"
            ):
                raise DomainForbidden("Active membership is required")
        cache_key = f"leaderboard:v1:club:{club_id}:{period}:{metric}:{limit}"
        cached = await cache_get_bytes(cache_key)
        if cached is not None:
            rows = json.loads(cached.decode())
            for row in rows:
                row["is_me"] = row["user_id"] == viewer_user_id
            return rows
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        f"""
                        SELECT f.subject_id AS user_id, {metric_columns[metric]}::float AS score,
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
                        WHERE f.subject_type = 'athlete'
                          AND f.club_id = CAST(:club AS uuid)
                          AND f.occurred_at >= {allowed_periods[period]}
                        GROUP BY f.subject_id
                        ORDER BY score DESC, f.subject_id
                        LIMIT :limit
                        """
                    ),
                    {"club": club_id, "limit": max(1, min(limit, 100))},
                )
            ]
        for index, row in enumerate(rows):
            row["rank"] = index + 1
            row["is_me"] = row["user_id"] == viewer_user_id
        await cache_set_bytes(
            cache_key,
            _json([{**row, "is_me": False} for row in rows]).encode(),
            ttl_seconds=60,
        )
        return rows

    async def seasons(self, limit: int = 12) -> List[Dict[str, Any]]:
        async with self.engine.connect() as connection:
            return [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, code, name, starts_at, ends_at, status, created_at
                        FROM seasons
                        ORDER BY starts_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"limit": max(1, min(limit, 40))},
                )
            ]

    async def public_leaderboard(
        self,
        viewer_user_id: str,
        *,
        scope: str,
        region_id: Optional[str],
        subject: str,
        period: str,
        metric: str,
        normalized: bool,
        limit: int,
    ) -> List[Dict[str, Any]]:
        periods = {
            "week": "date_trunc('week', NOW())",
            "month": "date_trunc('month', NOW())",
            "season": "COALESCE((SELECT starts_at FROM seasons WHERE status='active' LIMIT 1), date_trunc('quarter', NOW()))",
            "all": "'1970-01-01'::timestamptz",
        }
        metrics = {
            "distance": "SUM(f.distance_m)",
            "moving_time": "SUM(f.moving_time_sec)",
            "runs": "SUM(f.run_count)",
            "consistency": "COUNT(DISTINCT f.consistency_date)",
            "territory_gain": "SUM(f.territory_gain_m)",
        }
        if scope not in {"global", "city", "country"}:
            raise DomainConflict("Unsupported leaderboard scope")
        if subject not in {"athlete", "club"}:
            raise DomainConflict("Unsupported leaderboard subject")
        if period not in periods or metric not in metrics:
            raise DomainConflict("Unsupported leaderboard period or metric")
        if scope != "global" and not region_id:
            raise DomainConflict("region_id is required for geographic leaderboards")
        region_filter = ""
        params: Dict[str, Any] = {"limit": max(1, min(limit, 100))}
        if region_id:
            _uuid(region_id)
            params["region"] = region_id
            region_filter = """
              AND f.region_id IN (
                WITH RECURSIVE descendants AS (
                  SELECT id FROM regions WHERE id=CAST(:region AS uuid)
                  UNION ALL
                  SELECT r.id FROM regions r
                  JOIN descendants d ON r.parent_id=d.id
                )
                SELECT id FROM descendants
              )
            """
        group_column = "f.subject_id" if subject == "athlete" else "f.club_id"
        subject_filter = "" if subject == "athlete" else "AND f.club_id IS NOT NULL"
        member_join = ""
        denominator = "1"
        if subject == "club":
            member_join = """
              JOIN club_memberships active_contributor
                ON active_contributor.club_id=f.club_id
               AND active_contributor.user_id=f.subject_id
               AND active_contributor.status='active'
              LEFT JOIN (
                SELECT club_id, COUNT(*)::float AS active_members
                FROM club_memberships
                WHERE status='active'
                GROUP BY club_id
              ) membership_count ON membership_count.club_id=f.club_id
            """
            denominator = (
                "GREATEST(COALESCE(membership_count.active_members, 1), 1)"
                if normalized
                else "1"
            )
        cache_key = (
            f"leaderboard:v1:{scope}:{region_id or 'global'}:{subject}:"
            f"{period}:{metric}:{int(normalized)}:{limit}"
        )
        cached = await cache_get_bytes(cache_key)
        if cached is not None:
            rows = json.loads(cached.decode())
            for row in rows:
                row["is_me"] = (
                    subject == "athlete" and row["subject_id"] == viewer_user_id
                )
            return rows
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        f"""
                        SELECT {group_column} AS subject_id,
                               ({metrics[metric]})::float / {denominator} AS score,
                               SUM(f.distance_m)::float AS distance_m,
                               SUM(f.moving_time_sec)::bigint AS moving_time_sec,
                               SUM(f.run_count)::bigint AS run_count,
                               COUNT(DISTINCT f.consistency_date)::int AS consistency_days,
                               SUM(f.territory_gain_m)::float AS territory_gain_m
                        FROM leaderboard_facts f
                        JOIN activities a ON a.id=f.activity_id
                        {member_join}
                        WHERE f.subject_type='athlete'
                          AND f.visibility='public'
                          AND a.public_competition_eligible
                          AND a.verification='verified'
                          AND a.deleted_at IS NULL
                          AND f.occurred_at >= {periods[period]}
                          {subject_filter}
                          {region_filter}
                        GROUP BY {group_column}{', membership_count.active_members' if subject == 'club' else ''}
                        ORDER BY score DESC, {group_column}
                        LIMIT :limit
                        """
                    ),
                    params,
                )
            ]
        for index, row in enumerate(rows):
            row["rank"] = index + 1
            row["is_me"] = subject == "athlete" and row["subject_id"] == viewer_user_id
            row["normalized_per_active_member"] = normalized and subject == "club"
        await cache_set_bytes(
            cache_key,
            _json([{**row, "is_me": False} for row in rows]).encode(),
            ttl_seconds=60,
        )
        return rows

    async def achievements(
        self,
        viewer_user_id: str,
        *,
        club_id: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        if club_id:
            async with self.engine.connect() as connection:
                club = (
                    await connection.execute(
                        text("SELECT visibility::text AS visibility FROM clubs WHERE id=CAST(:club AS uuid)"),
                        {"club": club_id},
                    )
                ).first()
                membership = await self._membership(connection, club_id, viewer_user_id)
                if not club:
                    raise DomainNotFound("Club not found")
                if club.visibility == "private" and (
                    not membership or membership["status"] != "active"
                ):
                    raise DomainForbidden("Active club membership is required")
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, user_id, club_id, activity_id, achievement_type,
                               key, title, metadata, awarded_at
                        FROM achievements
                        WHERE (
                          CAST(:club AS uuid) IS NOT NULL
                          AND club_id=CAST(:club AS uuid)
                        ) OR (
                          CAST(:club AS uuid) IS NULL
                          AND user_id=CAST(:viewer AS uuid)
                        )
                        ORDER BY awarded_at DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "club": club_id,
                        "viewer": viewer_user_id,
                        "limit": max(1, min(limit, 100)),
                    },
                )
            ]
        return rows

    async def create_challenge(
        self, club_id: str, actor_user_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        challenge_id = new_id()
        now = utc_now()
        status = "active" if payload["starts_at"] <= now < payload["ends_at"] else "scheduled"
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, actor_user_id, {"owner", "admin"})
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO challenges (
                            id, club_id, created_by_user_id, name, description, metric,
                            target, segment_id, starts_at, ends_at, status, visibility
                        ) VALUES (
                            CAST(:id AS uuid), CAST(:club AS uuid), CAST(:actor AS uuid),
                            :name, :description, :metric, :target, CAST(:segment AS uuid),
                            :starts, :ends, :status, 'club'
                        )
                        RETURNING id, club_id, name, description, metric, target,
                                  segment_id, starts_at, ends_at, status, version, created_at
                        """
                    ),
                    {
                        "id": challenge_id,
                        "club": club_id,
                        "actor": actor_user_id,
                        "name": payload["name"],
                        "description": payload.get("description"),
                        "metric": payload["metric"],
                        "target": payload.get("target"),
                        "segment": payload.get("segment_id"),
                        "starts": payload["starts_at"],
                        "ends": payload["ends_at"],
                        "status": status,
                    },
                )
            ).first()
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=actor_user_id,
                event_type="challenge_created",
                source_type="challenge",
                source_id=challenge_id,
                payload={"name": payload["name"], "starts_at": str(payload["starts_at"])},
                idempotency_key=f"challenge:{challenge_id}:created",
            )
            return _dict(row)

    async def list_challenges(
        self,
        club_id: str,
        viewer_user_id: str,
        cursor: Optional[str],
        limit: int,
    ) -> Dict[str, Any]:
        cursor_time, cursor_id = decode_cursor(cursor)
        async with self.engine.connect() as connection:
            membership = await self._membership(connection, club_id, viewer_user_id)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active membership is required")
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT c.id, c.club_id, c.name, c.description, c.metric, c.target,
                               c.segment_id, c.starts_at, c.ends_at, c.status, c.version,
                               COUNT(e.id)::int AS participant_count,
                               BOOL_OR(e.user_id = CAST(:viewer AS uuid)) AS is_joined
                        FROM challenges c
                        LEFT JOIN challenge_entries e ON e.challenge_id = c.id
                        WHERE c.club_id = CAST(:club AS uuid) AND c.status != 'cancelled'
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (c.starts_at, c.id) < (
                              CAST(:cursor_time AS timestamptz),
                              CAST(:cursor_id AS uuid)
                            )
                          )
                        GROUP BY c.id
                        ORDER BY c.starts_at DESC, c.id DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "club": club_id,
                        "viewer": viewer_user_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["starts_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def athlete_challenges(
        self,
        user_id: str,
        cursor: Optional[str],
        limit: int,
    ) -> Dict[str, Any]:
        cursor_time, cursor_id = decode_cursor(cursor)
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT c.id, c.club_id, club.name AS club_name,
                               c.name, c.description, c.metric,
                               c.metric AS challenge_type, c.target,
                               c.starts_at, c.ends_at, c.status,
                               (entry.id IS NOT NULL) AS joined,
                               entry.score, entry.progress
                        FROM challenges c
                        JOIN clubs club ON club.id=c.club_id AND club.status='active'
                        JOIN club_memberships membership
                          ON membership.club_id=c.club_id
                         AND membership.user_id=CAST(:user AS uuid)
                         AND membership.status='active'
                        LEFT JOIN challenge_entries entry
                          ON entry.challenge_id=c.id
                         AND entry.user_id=CAST(:user AS uuid)
                        WHERE c.status IN ('scheduled','active')
                          AND c.ends_at>NOW()
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (c.starts_at, c.id) > (
                              CAST(:cursor_time AS timestamptz),
                              CAST(:cursor_id AS uuid)
                            )
                          )
                        ORDER BY c.starts_at, c.id
                        LIMIT :limit
                        """
                    ),
                    {
                        "user": user_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["starts_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def join_challenge(
        self, challenge_id: str, user_id: str
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            challenge = (
                await connection.execute(
                    text(
                        """
                        SELECT id, club_id, status FROM challenges
                        WHERE id = CAST(:id AS uuid) FOR UPDATE
                        """
                    ),
                    {"id": challenge_id},
                )
            ).first()
            if not challenge or challenge.status not in {"scheduled", "active"}:
                raise DomainNotFound("Open challenge not found")
            membership = await self._membership(connection, str(challenge.club_id), user_id)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active club membership is required")
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO challenge_entries (id, challenge_id, user_id)
                        VALUES (CAST(:id AS uuid), CAST(:challenge AS uuid), CAST(:user AS uuid))
                        ON CONFLICT (challenge_id, user_id) DO UPDATE SET updated_at = NOW()
                        RETURNING id, challenge_id, user_id, score, progress, joined_at, updated_at
                        """
                    ),
                    {"id": new_id(), "challenge": challenge_id, "user": user_id},
                )
            ).first()
            return _dict(row)

    async def challenge_leaderboard(
        self, challenge_id: str, viewer_user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        async with self.engine.connect() as connection:
            challenge = (
                await connection.execute(
                    text("SELECT club_id FROM challenges WHERE id=CAST(:id AS uuid)"),
                    {"id": challenge_id},
                )
            ).first()
            if not challenge:
                raise DomainNotFound("Challenge not found")
            membership = await self._membership(
                connection, str(challenge.club_id), viewer_user_id
            )
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active club membership is required")
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT user_id, score, progress, joined_at, updated_at
                        FROM challenge_entries
                        WHERE challenge_id=CAST(:challenge AS uuid)
                        ORDER BY score DESC, updated_at
                        LIMIT :limit
                        """
                    ),
                    {"challenge": challenge_id, "limit": max(1, min(limit, 100))},
                )
            ]
        for index, row in enumerate(rows):
            row["rank"] = index + 1
            row["is_me"] = row["user_id"] == viewer_user_id
        return rows

    async def create_race(
        self, club_id: str, actor_user_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        race_id = new_id()
        route = _json({"type": "LineString", "coordinates": payload["route"]})
        async with self.engine.begin() as connection:
            await self._require_role(connection, club_id, actor_user_id, {"owner", "admin"})
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO races (
                            id, club_id, created_by_user_id, name, description, timezone,
                            starts_at, start_window_minutes, result_cutoff_at,
                            participant_capacity, route, route_distance_m, status
                        ) VALUES (
                            CAST(:id AS uuid), CAST(:club AS uuid), CAST(:actor AS uuid),
                            :name, :description, :timezone, :starts, :window, :cutoff,
                            :capacity, ST_SetSRID(ST_GeomFromGeoJSON(:route), 4326),
                            :distance, 'scheduled'
                        )
                        RETURNING id, club_id, name, description, timezone, starts_at,
                                  start_window_minutes, result_cutoff_at,
                                  participant_capacity, route_distance_m, status, version, created_at
                        """
                    ),
                    {
                        "id": race_id,
                        "club": club_id,
                        "actor": actor_user_id,
                        "name": payload["name"],
                        "description": payload.get("description"),
                        "timezone": payload["timezone"],
                        "starts": payload["starts_at"],
                        "window": payload["start_window_minutes"],
                        "cutoff": payload["result_cutoff_at"],
                        "capacity": payload.get("participant_capacity"),
                        "route": route,
                        "distance": payload["route_distance_m"],
                    },
                )
            ).first()
            await self._event(
                connection,
                club_id=club_id,
                actor_user_id=actor_user_id,
                event_type="race_created",
                source_type="race",
                source_id=race_id,
                payload={"name": payload["name"], "starts_at": str(payload["starts_at"])},
                idempotency_key=f"race:{race_id}:created",
            )
            return _dict(row)

    async def list_races(
        self,
        club_id: str,
        viewer_user_id: str,
        cursor: Optional[str],
        limit: int,
    ) -> Dict[str, Any]:
        cursor_time, cursor_id = decode_cursor(cursor)
        async with self.engine.connect() as connection:
            membership = await self._membership(connection, club_id, viewer_user_id)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active membership is required")
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT r.id, r.club_id, r.name, r.description, r.timezone,
                               r.starts_at, r.start_window_minutes, r.result_cutoff_at,
                               r.participant_capacity, r.route_distance_m, r.status,
                               r.version, COUNT(e.id)::int AS participant_count,
                               BOOL_OR(e.user_id = CAST(:viewer AS uuid)) AS is_joined
                        FROM races r
                        LEFT JOIN race_entries e ON e.race_id = r.id
                        WHERE r.club_id = CAST(:club AS uuid) AND r.status != 'cancelled'
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (r.starts_at, r.id) < (
                              CAST(:cursor_time AS timestamptz),
                              CAST(:cursor_id AS uuid)
                            )
                          )
                        GROUP BY r.id
                        ORDER BY r.starts_at DESC, r.id DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "club": club_id,
                        "viewer": viewer_user_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["starts_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def athlete_races(
        self,
        user_id: str,
        cursor: Optional[str],
        limit: int,
    ) -> Dict[str, Any]:
        cursor_time, cursor_id = decode_cursor(cursor)
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT race.id, race.club_id, club.name AS club_name,
                               race.name, race.description, race.timezone,
                               race.starts_at, race.start_window_minutes,
                               race.result_cutoff_at, race.participant_capacity,
                               race.route_distance_m, race.status,
                               (entry.id IS NOT NULL) AS joined
                        FROM races race
                        JOIN clubs club
                          ON club.id=race.club_id AND club.status='active'
                        JOIN club_memberships membership
                          ON membership.club_id=race.club_id
                         AND membership.user_id=CAST(:user AS uuid)
                         AND membership.status='active'
                        LEFT JOIN race_entries entry
                          ON entry.race_id=race.id
                         AND entry.user_id=CAST(:user AS uuid)
                        WHERE race.status IN ('scheduled','active')
                          AND race.result_cutoff_at>NOW()
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (race.starts_at, race.id) > (
                              CAST(:cursor_time AS timestamptz),
                              CAST(:cursor_id AS uuid)
                            )
                          )
                        ORDER BY race.starts_at, race.id
                        LIMIT :limit
                        """
                    ),
                    {
                        "user": user_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["starts_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def join_race(self, race_id: str, user_id: str) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            race = (
                await connection.execute(
                    text(
                        """
                        SELECT id, club_id, status, participant_capacity,
                               (SELECT COUNT(*) FROM race_entries WHERE race_id = races.id) AS entries
                        FROM races WHERE id = CAST(:id AS uuid) FOR UPDATE
                        """
                    ),
                    {"id": race_id},
                )
            ).first()
            if not race or race.status not in {"scheduled", "active"}:
                raise DomainNotFound("Open race not found")
            membership = await self._membership(connection, str(race.club_id), user_id)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active club membership is required")
            if race.participant_capacity and race.entries >= race.participant_capacity:
                raise DomainConflict("Race capacity has been reached")
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO race_entries (id, race_id, user_id)
                        VALUES (CAST(:id AS uuid), CAST(:race AS uuid), CAST(:user AS uuid))
                        ON CONFLICT (race_id, user_id) DO UPDATE SET joined_at = race_entries.joined_at
                        RETURNING id, race_id, user_id, joined_at
                        """
                    ),
                    {"id": new_id(), "race": race_id, "user": user_id},
                )
            ).first()
            return _dict(row)

    async def race_results(
        self, race_id: str, viewer_user_id: str, limit: int
    ) -> List[Dict[str, Any]]:
        async with self.engine.connect() as connection:
            race = (
                await connection.execute(
                    text("SELECT club_id FROM races WHERE id=CAST(:id AS uuid)"),
                    {"id": race_id},
                )
            ).first()
            if not race:
                raise DomainNotFound("Race not found")
            membership = await self._membership(connection, str(race.club_id), viewer_user_id)
            if not membership or membership["status"] != "active":
                raise DomainForbidden("Active club membership is required")
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT user_id, activity_id, elapsed_time_sec, route_coverage,
                               verification::text AS verification, rejection_reasons,
                               submitted_at, verified_at
                        FROM race_results
                        WHERE race_id=CAST(:race AS uuid)
                        ORDER BY
                          CASE verification WHEN 'verified' THEN 0 WHEN 'provisional' THEN 1 ELSE 2 END,
                          elapsed_time_sec ASC NULLS LAST
                        LIMIT :limit
                        """
                    ),
                    {"race": race_id, "limit": max(1, min(limit, 100))},
                )
            ]
        rank = 0
        for row in rows:
            if row["verification"] == "verified":
                rank += 1
                row["rank"] = rank
            else:
                row["rank"] = None
            row["is_me"] = row["user_id"] == viewer_user_id
        return rows

    async def territory_geojson(
        self,
        viewer_user_id: str,
        *,
        controller_type: str,
        controller_id: str,
        bbox: Optional[List[float]],
        limit: int = 5_000,
    ) -> Dict[str, Any]:
        if controller_type not in {"athlete", "club"}:
            raise DomainConflict("controller_type must be athlete or club")
        if controller_type == "athlete" and controller_id != viewer_user_id:
            raise DomainForbidden("Personal territory is private to its athlete")
        if controller_type == "club":
            async with self.engine.connect() as connection:
                membership = await self._membership(connection, controller_id, viewer_user_id)
                if not membership or membership["status"] != "active":
                    raise DomainForbidden("Active club membership is required")
        bbox_clause = ""
        params: Dict[str, Any] = {
            "type": controller_type,
            "controller": controller_id,
            "limit": max(1, min(limit, 20_000)),
        }
        if bbox:
            if len(bbox) != 4:
                raise DomainConflict("bbox must be west,south,east,north")
            bbox_clause = (
                "AND e.edge && ST_MakeEnvelope(:west, :south, :east, :north, 4326)"
            )
            params.update(
                {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]}
            )
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        f"""
                        SELECT c.street_edge_id, c.controller_id, c.score,
                               c.controlled_since, c.expires_at,
                               e.name, e.distance_m, ST_AsGeoJSON(e.edge)::json AS geometry
                        FROM territory_current_control c
                        JOIN street_edges e ON e.id = c.street_edge_id
                        WHERE c.controller_type = CAST(:type AS controller_type)
                          AND c.controller_id = CAST(:controller AS uuid)
                          AND c.expires_at > NOW()
                          {bbox_clause}
                        ORDER BY c.updated_at DESC
                        LIMIT :limit
                        """
                    ),
                    params,
                )
            ]
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": row["street_edge_id"],
                    "geometry": row.pop("geometry"),
                    "properties": row,
                }
                for row in rows
            ],
            "verified": True,
        }

    async def territory_tile(
        self,
        viewer_user_id: str,
        *,
        z: int,
        x: int,
        y: int,
        layer: str,
        club_id: Optional[str],
    ) -> bytes:
        if not (0 <= z <= 22 and 0 <= x < 2**z and 0 <= y < 2**z):
            raise DomainNotFound("Tile not found")
        if layer == "me":
            controller_type, controller_id = "athlete", viewer_user_id
        elif layer == "club" and club_id:
            controller_type, controller_id = "club", club_id
            async with self.engine.connect() as connection:
                membership = await self._membership(connection, club_id, viewer_user_id)
                if not membership or membership["status"] != "active":
                    raise DomainForbidden("Active club membership is required")
        elif layer == "competitors":
            controller_type, controller_id = "athlete", None
        else:
            raise DomainConflict("Unsupported territory layer")
        cache_controller = controller_id or "public"
        cache_key = f"territory:mvt:v1:{layer}:{cache_controller}:{z}:{x}:{y}"
        cached = await cache_get_bytes(cache_key)
        if cached is not None:
            return cached
        async with self.engine.connect() as connection:
            tile = await connection.scalar(
                text(
                    """
                    WITH bounds AS (
                        SELECT ST_TileEnvelope(:z, :x, :y) AS geom
                    ), private_features AS (
                        SELECT c.street_edge_id::text AS street_edge_id,
                               c.controller_id::text AS controller_id,
                               c.score,
                               EXTRACT(EPOCH FROM c.expires_at)::bigint AS expires_at,
                               CASE
                                 WHEN c.expires_at < NOW() + INTERVAL '7 days' THEN 'expiring'
                                 WHEN EXISTS (
                                   SELECT 1 FROM territory_scores challenger
                                   WHERE challenger.street_edge_id=c.street_edge_id
                                     AND challenger.controller_type=c.controller_type
                                     AND challenger.controller_id!=c.controller_id
                                     AND challenger.window_ends_at>NOW()
                                     AND challenger.score >= c.score * 0.90
                                 ) THEN 'contested'
                                 ELSE 'controlled'
                               END AS control_state,
                               ST_AsMVTGeom(
                                   ST_Transform(e.edge, 3857),
                                   bounds.geom, 4096, 64, true
                               ) AS geom
                        FROM territory_current_control c
                        JOIN street_edges e ON e.id = c.street_edge_id
                        CROSS JOIN bounds
                        WHERE :layer != 'competitors'
                          AND c.controller_type = CAST(:type AS controller_type)
                          AND (:controller_id IS NULL OR c.controller_id = CAST(:controller_id AS uuid))
                          AND c.expires_at > NOW()
                          AND ST_Transform(e.edge, 3857) && bounds.geom
                    ), public_daily AS (
                        SELECT DISTINCT ON (
                                 traversal.street_edge_id,
                                 traversal.user_id,
                                 traversal.local_activity_date
                               )
                               traversal.street_edge_id,
                               traversal.user_id,
                               traversal.local_activity_date,
                               (
                                 100.0 * traversal.confidence * traversal.coverage
                                 * POWER(
                                     0.5,
                                     EXTRACT(EPOCH FROM (NOW() - activity.started_at))
                                     / 86400.0 / 14.0
                                   )
                               )::float AS points,
                               traversal.elapsed_time_sec,
                               activity.started_at AS activity_started_at
                        FROM matched_edge_traversals traversal
                        JOIN activities activity ON activity.id=traversal.activity_id
                        JOIN street_edges edge ON edge.id=traversal.street_edge_id
                        CROSS JOIN bounds
                        WHERE :layer='competitors'
                          AND traversal.qualified
                          AND traversal.local_activity_date>=CURRENT_DATE - 28
                          AND traversal.matched_at<=NOW()
                          AND activity.status='complete'
                          AND activity.visibility='public'
                          AND activity.public_competition_eligible
                          AND activity.verification='verified'
                          AND activity.public_route IS NOT NULL
                          AND activity.deleted_at IS NULL
                          AND NOT EXISTS (
                            SELECT 1
                            FROM competition_flags flag
                            WHERE flag.activity_id=activity.id
                              AND flag.status IN (
                                'open', 'reviewing', 'upheld', 'appealed'
                              )
                          )
                          AND ST_Transform(edge.edge, 3857) && bounds.geom
                        ORDER BY traversal.street_edge_id, traversal.user_id,
                                 traversal.local_activity_date,
                                 points DESC, traversal.elapsed_time_sec
                    ), public_limited AS (
                        SELECT daily.*,
                               ROW_NUMBER() OVER (
                                 PARTITION BY street_edge_id, user_id
                                 ORDER BY points DESC, elapsed_time_sec
                               ) AS scoring_rank
                        FROM public_daily daily
                    ), public_scores AS (
                        SELECT street_edge_id, user_id,
                               SUM(points)::float AS score,
                               MIN(elapsed_time_sec)::float AS fastest_time_sec,
                               MAX(activity_started_at) AS score_reached_at,
                               MAX(activity_started_at + INTERVAL '28 days') AS expires_at
                        FROM public_limited
                        WHERE scoring_rank<=7
                        GROUP BY street_edge_id, user_id
                    ), public_ranked AS (
                        SELECT score.*,
                               ROW_NUMBER() OVER (
                                 PARTITION BY street_edge_id
                                 ORDER BY score DESC, fastest_time_sec,
                                          score_reached_at, user_id
                               ) AS controller_rank,
                               LEAD(score) OVER (
                                 PARTITION BY street_edge_id
                                 ORDER BY score DESC, fastest_time_sec,
                                          score_reached_at, user_id
                               ) AS challenger_score
                        FROM public_scores score
                    ), public_features AS (
                        SELECT winner.street_edge_id::text AS street_edge_id,
                               NULL::text AS controller_id,
                               winner.score,
                               EXTRACT(EPOCH FROM winner.expires_at)::bigint AS expires_at,
                               CASE
                                 WHEN winner.expires_at<NOW() + INTERVAL '7 days' THEN 'expiring'
                                 WHEN winner.challenger_score>=winner.score * 0.90 THEN 'contested'
                                 ELSE 'controlled'
                               END AS control_state,
                               ST_AsMVTGeom(
                                 ST_Transform(edge.edge, 3857),
                                 bounds.geom, 4096, 64, true
                               ) AS geom
                        FROM public_ranked winner
                        JOIN street_edges edge ON edge.id=winner.street_edge_id
                        CROSS JOIN bounds
                        WHERE winner.controller_rank=1 AND winner.expires_at>NOW()
                    ), features AS (
                        SELECT * FROM private_features
                        UNION ALL
                        SELECT * FROM public_features
                    )
                    SELECT ST_AsMVT(features, 'territory', 4096, 'geom')
                    FROM features
                    """
                ),
                {
                    "z": z,
                    "x": x,
                    "y": y,
                    "type": controller_type,
                    "controller_id": controller_id,
                    "layer": layer,
                },
            )
        result = bytes(tile or b"")
        await cache_set_bytes(cache_key, result, ttl_seconds=60)
        return result

    async def territory_edge(
        self, viewer_user_id: str, street_edge_id: str
    ) -> Dict[str, Any]:
        _uuid(street_edge_id)
        async with self.engine.connect() as connection:
            row = (
                await connection.execute(
                    text(
                        """
                        WITH public_daily AS (
                          SELECT DISTINCT ON (
                                   traversal.user_id,
                                   traversal.local_activity_date
                                 )
                                 traversal.user_id,
                                 traversal.local_activity_date,
                                 (
                                   100.0 * traversal.confidence * traversal.coverage
                                   * POWER(
                                       0.5,
                                       EXTRACT(EPOCH FROM (
                                         NOW() - activity.started_at
                                       )) / 86400.0 / 14.0
                                     )
                                 )::float AS points,
                                 traversal.elapsed_time_sec,
                                 activity.started_at AS activity_started_at
                          FROM matched_edge_traversals traversal
                          JOIN activities activity
                            ON activity.id=traversal.activity_id
                          WHERE traversal.street_edge_id=CAST(:edge AS uuid)
                            AND traversal.qualified
                            AND traversal.local_activity_date>=CURRENT_DATE - 28
                            AND activity.status='complete'
                            AND activity.visibility='public'
                            AND activity.public_competition_eligible
                            AND activity.verification='verified'
                            AND activity.public_route IS NOT NULL
                            AND activity.deleted_at IS NULL
                            AND NOT EXISTS (
                              SELECT 1
                              FROM competition_flags flag
                              WHERE flag.activity_id=activity.id
                                AND flag.status IN (
                                  'open', 'reviewing', 'upheld', 'appealed'
                                )
                            )
                          ORDER BY traversal.user_id,
                                   traversal.local_activity_date,
                                   points DESC, traversal.elapsed_time_sec
                        ), public_limited AS (
                          SELECT daily.*,
                                 ROW_NUMBER() OVER (
                                   PARTITION BY user_id
                                   ORDER BY points DESC, elapsed_time_sec
                                 ) AS scoring_rank
                          FROM public_daily daily
                        ), public_scores AS (
                          SELECT user_id,
                                 SUM(points)::float AS score,
                                 MIN(elapsed_time_sec)::float AS fastest_time_sec,
                                 MAX(activity_started_at) AS score_reached_at,
                                 MAX(
                                   activity_started_at + INTERVAL '28 days'
                                 ) AS expires_at
                          FROM public_limited
                          WHERE scoring_rank<=7
                          GROUP BY user_id
                        ), public_winner AS (
                          SELECT score.*,
                                 ROW_NUMBER() OVER (
                                   ORDER BY score DESC, fastest_time_sec,
                                            score_reached_at, user_id
                                 ) AS controller_rank
                          FROM public_scores score
                        )
                        SELECT e.id, e.name, e.highway, e.surface, e.distance_m,
                               ST_AsGeoJSON(e.edge)::json AS geometry,
                               mine.score AS my_score,
                               mine.scoring_days AS my_scoring_days,
                               mine.window_ends_at AS my_score_expires_at,
                               NULL::uuid AS public_controller_id,
                               public_winner.score AS public_score,
                               public_winner.score_reached_at
                                 AS public_controlled_since,
                               public_winner.expires_at AS public_expires_at,
                               club_control.controller_id AS primary_club_id,
                               club_control.score AS primary_club_score,
                               club_control.controlled_since AS primary_club_controlled_since,
                               club_control.expires_at AS primary_club_expires_at
                        FROM street_edges e
                        LEFT JOIN territory_scores mine
                          ON mine.street_edge_id=e.id
                         AND mine.controller_type='athlete'
                         AND mine.controller_id=CAST(:viewer AS uuid)
                         AND mine.window_ends_at>NOW()
                        LEFT JOIN public_winner
                          ON public_winner.controller_rank=1
                         AND public_winner.expires_at>NOW()
                        LEFT JOIN athlete_competitive_profiles profile
                          ON profile.user_id=CAST(:viewer AS uuid)
                        LEFT JOIN club_memberships membership
                          ON membership.club_id=profile.primary_club_id
                         AND membership.user_id=CAST(:viewer AS uuid)
                         AND membership.status='active'
                        LEFT JOIN territory_current_control club_control
                          ON club_control.street_edge_id=e.id
                         AND club_control.controller_type='club'
                         AND club_control.controller_id=membership.club_id
                        WHERE e.id=CAST(:edge AS uuid) AND e.status='active'
                        """
                    ),
                    {"viewer": viewer_user_id, "edge": street_edge_id},
                )
            ).first()
            if not row:
                raise DomainNotFound("Road edge not found")
            history = [
                _dict(item)
                for item in await connection.execute(
                    text(
                        """
                        SELECT h.id, h.controller_type::text AS controller_type,
                               h.previous_controller_id, h.controller_id,
                               h.event_type, h.previous_score, h.score,
                               h.occurred_at
                        FROM territory_control_history h
                        LEFT JOIN athlete_competitive_profiles profile
                          ON profile.user_id=CAST(:viewer AS uuid)
                        WHERE h.street_edge_id=CAST(:edge AS uuid)
                          AND (
                            (h.controller_type='athlete' AND (
                              h.controller_id=CAST(:viewer AS uuid)
                              OR h.previous_controller_id=CAST(:viewer AS uuid)
                            ))
                            OR (h.controller_type='club' AND (
                              h.controller_id=profile.primary_club_id
                              OR h.previous_controller_id=profile.primary_club_id
                            ))
                          )
                        ORDER BY h.occurred_at DESC, h.id DESC
                        LIMIT 10
                        """
                    ),
                    {"viewer": viewer_user_id, "edge": street_edge_id},
                )
            ]
        result = _dict(row)
        result["recent_history"] = history
        return result

    async def territory_history(
        self,
        viewer_user_id: str,
        *,
        street_edge_id: str,
        controller_type: str,
        controller_id: str,
        cursor: Optional[str],
        limit: int,
    ) -> Dict[str, Any]:
        if controller_type == "athlete":
            if controller_id != viewer_user_id:
                raise DomainForbidden("Personal territory history is private")
        elif controller_type == "club":
            async with self.engine.connect() as connection:
                membership = await self._membership(connection, controller_id, viewer_user_id)
                if not membership or membership["status"] != "active":
                    raise DomainForbidden("Active club membership is required")
        else:
            raise DomainConflict("Unsupported territory controller")
        cursor_time, cursor_id = decode_cursor(cursor)
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT h.id, h.street_edge_id,
                               h.controller_type::text AS controller_type,
                               h.previous_controller_id, h.controller_id,
                               h.event_type, h.previous_score, h.score,
                               h.source_activity_id, h.occurred_at
                        FROM territory_control_history h
                        WHERE h.street_edge_id=CAST(:edge AS uuid)
                          AND h.controller_type=CAST(:type AS controller_type)
                          AND (
                            h.controller_id=CAST(:controller AS uuid)
                            OR h.previous_controller_id=CAST(:controller AS uuid)
                          )
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (h.occurred_at, h.id) < (
                              CAST(:cursor_time AS timestamptz), CAST(:cursor_id AS uuid)
                            )
                          )
                        ORDER BY h.occurred_at DESC, h.id DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "edge": street_edge_id,
                        "type": controller_type,
                        "controller": controller_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["occurred_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def create_flag(
        self, reporter_user_id: str, activity_id: str, reason_code: str, details: Optional[str]
    ) -> Dict[str, Any]:
        flag_id = new_id()
        async with self.engine.begin() as connection:
            activity = (
                await connection.execute(
                    text("SELECT user_id FROM activities WHERE id=CAST(:id AS uuid)"),
                    {"id": activity_id},
                )
            ).first()
            if not activity:
                raise DomainNotFound("Activity not found")
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO competition_flags (
                            id, activity_id, user_id, reported_by_user_id,
                            reason_code, evidence, status
                        ) VALUES (
                            CAST(:id AS uuid), CAST(:activity AS uuid), :user,
                            CAST(:reporter AS uuid), :reason,
                            jsonb_build_object('details', :details), 'open'
                        )
                        RETURNING id, activity_id, user_id, reason_code,
                                  evidence, status, created_at, updated_at
                        """
                    ),
                    {
                        "id": flag_id,
                        "activity": activity_id,
                        "user": activity.user_id,
                        "reporter": reporter_user_id,
                        "reason": reason_code,
                        "details": details,
                    },
                )
            ).first()
            return _dict(row)

    async def moderation_queue(self, status: str, limit: int) -> List[Dict[str, Any]]:
        async with self.engine.connect() as connection:
            return [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, activity_id, user_id, reported_by_user_id,
                               reason_code, evidence, status, created_at, updated_at
                        FROM competition_flags
                        WHERE status=:status
                        ORDER BY created_at
                        LIMIT :limit
                        """
                    ),
                    {"status": status, "limit": max(1, min(limit, 200))},
                )
            ]

    async def decide_flag(
        self,
        flag_id: str,
        moderator_user_id: str,
        decision: str,
        notes: Optional[str],
    ) -> Dict[str, Any]:
        affected_edge_ids: List[str] = []
        async with self.engine.begin() as connection:
            flag = (
                await connection.execute(
                    text(
                        """
                        SELECT id, activity_id, user_id, status
                        FROM competition_flags
                        WHERE id=CAST(:id AS uuid) FOR UPDATE
                        """
                    ),
                    {"id": flag_id},
                )
            ).first()
            if not flag:
                raise DomainNotFound("Competition flag not found")
            next_status = {
                "uphold": "upheld",
                "dismiss": "dismissed",
                "reopen": "open",
            }[decision]
            await connection.execute(
                text(
                    """
                    INSERT INTO moderation_decisions (
                        id, flag_id, moderator_user_id, decision, notes
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:flag AS uuid),
                        CAST(:moderator AS uuid), :decision, :notes
                    )
                    """
                ),
                {
                    "id": new_id(),
                    "flag": flag_id,
                    "moderator": moderator_user_id,
                    "decision": decision,
                    "notes": notes,
                },
            )
            await connection.execute(
                text(
                    """
                    UPDATE competition_flags SET status=:status, updated_at=NOW()
                    WHERE id=CAST(:id AS uuid)
                    """
                ),
                {"status": next_status, "id": flag_id},
            )
            if flag.status == "appealed":
                await connection.execute(
                    text(
                        """
                        UPDATE moderation_appeals
                        SET status=CASE
                              WHEN :decision='uphold' THEN 'rejected'
                              ELSE 'accepted'
                            END,
                            resolved_by_user_id=CAST(:moderator AS uuid),
                            resolved_at=NOW()
                        WHERE flag_id=CAST(:flag AS uuid) AND status='pending'
                        """
                    ),
                    {
                        "decision": decision,
                        "moderator": moderator_user_id,
                        "flag": flag_id,
                    },
                )
            if decision == "uphold":
                affected_edge_ids = [
                    str(row[0])
                    for row in await connection.execute(
                        text(
                            """
                            SELECT DISTINCT street_edge_id
                            FROM matched_edge_traversals
                            WHERE activity_id=:activity
                            """
                        ),
                        {"activity": flag.activity_id},
                    )
                ]
                await connection.execute(
                    text(
                        """
                        UPDATE activities SET verification='rejected', updated_at=NOW()
                        WHERE id=:activity
                        """
                    ),
                    {"activity": flag.activity_id},
                )
                await connection.execute(
                    text("DELETE FROM leaderboard_facts WHERE activity_id=:activity"),
                    {"activity": flag.activity_id},
                )
                await connection.execute(
                    text("DELETE FROM matched_edge_traversals WHERE activity_id=:activity"),
                    {"activity": flag.activity_id},
                )
                await connection.execute(
                    text("DELETE FROM race_results WHERE activity_id=:activity"),
                    {"activity": flag.activity_id},
                )
                await connection.execute(
                    text(
                        """
                        DELETE FROM system_activity_events
                        WHERE source_type='activity' AND source_id=:activity
                        """
                    ),
                    {"activity": flag.activity_id},
                )
            elif decision == "dismiss":
                remaining = await connection.scalar(
                    text(
                        """
                        SELECT EXISTS(
                            SELECT 1 FROM competition_flags
                            WHERE activity_id=:activity
                              AND id != CAST(:flag AS uuid)
                              AND status IN ('open', 'reviewing', 'upheld', 'appealed')
                        )
                        """
                    ),
                    {"activity": flag.activity_id, "flag": flag_id},
                )
                if not remaining:
                    await connection.execute(
                        text(
                            """
                            UPDATE activities SET verification='verified', updated_at=NOW()
                            WHERE id=:activity AND status='complete'
                            """
                        ),
                        {"activity": flag.activity_id},
                    )
            await self._outbox(
                connection,
                "activity",
                str(flag.activity_id),
                f"moderation.{next_status}",
                {
                    "flag_id": flag_id,
                    "activity_id": str(flag.activity_id),
                    "user_id": str(flag.user_id),
                    "status": next_status,
                },
            )
            response = {
                "id": flag_id,
                "activity_id": str(flag.activity_id),
                "user_id": str(flag.user_id),
                "status": next_status,
                "decision": decision,
            }
        if affected_edge_ids:
            from backend.territory_engine import recompute_edges

            await recompute_edges(affected_edge_ids)
        return response

    async def athlete_flags(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        async with self.engine.connect() as connection:
            return [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT f.id, f.activity_id, f.reason_code, f.evidence,
                               f.status, f.created_at, f.updated_at,
                               a.id AS appeal_id, a.reason AS appeal_reason,
                               a.status AS appeal_status, a.created_at AS appealed_at
                        FROM competition_flags f
                        LEFT JOIN moderation_appeals a
                          ON a.flag_id=f.id AND a.user_id=f.user_id
                        WHERE f.user_id=CAST(:user AS uuid)
                        ORDER BY f.created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"user": user_id, "limit": max(1, min(limit, 100))},
                )
            ]

    async def appeal_flag(
        self,
        flag_id: str,
        user_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            flag = (
                await connection.execute(
                    text(
                        """
                        SELECT id, activity_id, user_id, status
                        FROM competition_flags
                        WHERE id=CAST(:id AS uuid)
                        FOR UPDATE
                        """
                    ),
                    {"id": flag_id},
                )
            ).first()
            if not flag or str(flag.user_id) != user_id:
                raise DomainNotFound("Eligible moderation flag not found")
            if flag.status != "upheld":
                raise DomainConflict("Only an upheld decision can be appealed")
            appeal_id = new_id()
            try:
                await connection.execute(
                    text(
                        """
                        INSERT INTO moderation_appeals (id, flag_id, user_id, reason)
                        VALUES (
                            CAST(:id AS uuid), CAST(:flag AS uuid),
                            CAST(:user AS uuid), :reason
                        )
                        """
                    ),
                    {
                        "id": appeal_id,
                        "flag": flag_id,
                        "user": user_id,
                        "reason": reason,
                    },
                )
            except IntegrityError as exc:
                raise DomainConflict("This decision has already been appealed") from exc
            await connection.execute(
                text(
                    """
                    UPDATE competition_flags SET status='appealed', updated_at=NOW()
                    WHERE id=CAST(:flag AS uuid)
                    """
                ),
                {"flag": flag_id},
            )
            await self._outbox(
                connection,
                "activity",
                str(flag.activity_id),
                "moderation.appealed",
                {
                    "flag_id": flag_id,
                    "appeal_id": appeal_id,
                    "activity_id": str(flag.activity_id),
                    "user_id": user_id,
                },
            )
            return {
                "id": appeal_id,
                "flag_id": flag_id,
                "activity_id": str(flag.activity_id),
                "status": "pending",
            }

    async def notifications(
        self, user_id: str, cursor: Optional[str], limit: int
    ) -> Dict[str, Any]:
        cursor_time, cursor_id = decode_cursor(cursor)
        async with self.engine.connect() as connection:
            rows = [
                _dict(row)
                for row in await connection.execute(
                    text(
                        """
                        SELECT id, notification_type, title, body, data,
                               read_at, push_status, created_at
                        FROM notifications
                        WHERE user_id = CAST(:user AS uuid)
                          AND (
                            CAST(:cursor_time AS timestamptz) IS NULL
                            OR (created_at, id) < (
                                CAST(:cursor_time AS timestamptz),
                                CAST(:cursor_id AS uuid)
                            )
                          )
                        ORDER BY created_at DESC, id DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "user": user_id,
                        "cursor_time": cursor_time,
                        "cursor_id": cursor_id,
                        "limit": max(1, min(limit, 100)) + 1,
                    },
                )
            ]
        has_more = len(rows) > limit
        rows = rows[:limit]
        return {
            "items": rows,
            "next_cursor": encode_cursor(rows[-1]["created_at"], rows[-1]["id"])
            if has_more and rows
            else None,
        }

    async def mark_notification_read(self, user_id: str, notification_id: str) -> None:
        async with self.engine.begin() as connection:
            result = await connection.execute(
                text(
                    """
                    UPDATE notifications SET read_at = COALESCE(read_at, NOW())
                    WHERE id = CAST(:id AS uuid) AND user_id = CAST(:user AS uuid)
                    """
                ),
                {"id": notification_id, "user": user_id},
            )
            if result.rowcount == 0:
                raise DomainNotFound("Notification not found")

    async def register_push_token(
        self, user_id: str, token_hash: str, encrypted_token: str, platform: str
    ) -> Dict[str, Any]:
        async with self.engine.begin() as connection:
            row = (
                await connection.execute(
                    text(
                        """
                        INSERT INTO push_tokens (
                            id, user_id, token_hash, encrypted_token, platform
                        ) VALUES (
                            CAST(:id AS uuid), CAST(:user AS uuid),
                            :hash, :token, :platform
                        )
                        ON CONFLICT (token_hash) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            encrypted_token = EXCLUDED.encrypted_token,
                            platform = EXCLUDED.platform,
                            disabled_at = NULL,
                            updated_at = NOW()
                        RETURNING id, user_id, platform, created_at, updated_at
                        """
                    ),
                    {
                        "id": new_id(),
                        "user": user_id,
                        "hash": token_hash,
                        "token": encrypted_token,
                        "platform": platform,
                    },
                )
            ).first()
            return _dict(row)

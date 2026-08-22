from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text

from backend.geo_db import get_geo_engine
from backend.platform_ids import new_id


def canonical_uuid(value: Any, namespace: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"runlete:legacy:{namespace}:{value}"))


def naive_to_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


async def build_plan(mongo: Any) -> Dict[str, Any]:
    clubs = await mongo.run_clubs.find({}).to_list(None)
    memberships = await mongo.run_club_memberships.find({}).to_list(None)
    by_club_user: Dict[tuple[str, str], Dict[str, Any]] = {}
    conflicts: List[Dict[str, Any]] = []

    for membership in memberships:
        club_id = canonical_uuid(membership.get("club_id"), "club")
        user_id = canonical_uuid(membership.get("user_id"), "user")
        key = (club_id, user_id)
        current = by_club_user.get(key)
        if current:
            conflicts.append(
                {
                    "type": "duplicate_membership",
                    "club_id": club_id,
                    "user_id": user_id,
                    "kept": str(current.get("id")),
                    "discarded": str(membership.get("id")),
                }
            )
            current_rank = {"active": 5, "pending": 4, "banned": 3, "removed": 2, "rejected": 1}.get(
                current.get("status"), 0
            )
            next_rank = {"active": 5, "pending": 4, "banned": 3, "removed": 2, "rejected": 1}.get(
                membership.get("status"), 0
            )
            if next_rank <= current_rank:
                continue
        by_club_user[key] = membership

    normalized_clubs = []
    allocated_slugs: set[str] = set()
    for club in clubs:
        club_id = canonical_uuid(club.get("id"), "club")
        owner_id = canonical_uuid(
            club.get("owner_id")
            or club.get("created_by_user_id")
            or f"missing-owner:{club_id}",
            "user",
        )
        slug_base = (
            str(club.get("slug") or club.get("name") or "run-club")
            .strip()
            .lower()
            .replace(" ", "-")[:72]
            or "run-club"
        )
        slug = slug_base
        suffix = 2
        while slug in allocated_slugs:
            slug = f"{slug_base}-{suffix}"
            suffix += 1
        allocated_slugs.add(slug)
        if slug != slug_base:
            conflicts.append(
                {
                    "type": "duplicate_slug",
                    "club_id": club_id,
                    "legacy_slug": slug_base,
                    "repaired_slug": slug,
                }
            )
        normalized_clubs.append(
            {
                "id": club_id,
                "slug": slug,
                "name": str(club.get("name") or "Run club").strip()[:120],
                "description": club.get("description"),
                "visibility": "public" if club.get("is_public", True) else "private",
                "status": "archived" if club.get("status") == "archived" else "active",
                "owner_user_id": owner_id,
                "timezone": club.get("timezone") or "UTC",
                "emoji": club.get("emoji") or "🏃",
                "created_at": naive_to_utc(club.get("created_at")),
            }
        )
        owner_key = (club_id, owner_id)
        owner_membership = by_club_user.get(owner_key, {})
        by_club_user[owner_key] = {
            **owner_membership,
            "id": owner_membership.get("id") or new_id(),
            "club_id": club_id,
            "user_id": owner_id,
            "role": "owner",
            "status": "active",
            "joined_at": owner_membership.get("joined_at") or club.get("created_at"),
        }
        for legacy_user_id in club.get("member_ids") or []:
            user_id = canonical_uuid(legacy_user_id, "user")
            key = (club_id, user_id)
            if key not in by_club_user:
                by_club_user[key] = {
                    "id": new_id(),
                    "club_id": club_id,
                    "user_id": user_id,
                    "role": "member",
                    "status": "active",
                    "joined_at": club.get("created_at"),
                    "repair": "member_ids_only",
                }
                conflicts.append(
                    {
                        "type": "member_ids_only",
                        "club_id": club_id,
                        "user_id": user_id,
                    }
                )

    normalized_memberships = []
    active_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for (club_id, user_id), membership in by_club_user.items():
        status = membership.get("status") or "removed"
        if status not in {"pending", "active", "rejected", "removed", "banned"}:
            status = "removed"
        role = membership.get("role") or "member"
        if role not in {"owner", "admin", "member"}:
            role = "member"
        normalized = {
            "id": canonical_uuid(membership.get("id") or new_id(), "membership"),
            "club_id": club_id,
            "user_id": user_id,
            "role": role,
            "status": status,
            "requested_at": naive_to_utc(membership.get("requested_at"))
            if membership.get("requested_at")
            else None,
            "joined_at": naive_to_utc(membership.get("joined_at"))
            if membership.get("joined_at")
            else None,
            "created_at": naive_to_utc(
                membership.get("created_at")
                or membership.get("joined_at")
                or membership.get("requested_at")
            ),
        }
        normalized_memberships.append(normalized)
        if status == "active":
            active_by_user[user_id].append(normalized)

    primary_profiles = []
    for user_id, active in active_by_user.items():
        selected = min(
            active,
            key=lambda item: (
                item["joined_at"] or item["created_at"],
                item["club_id"],
            ),
        )
        primary_profiles.append(
            {
                "user_id": user_id,
                "club_id": selected["club_id"],
                "selected_at": selected["joined_at"] or selected["created_at"],
            }
        )
        if len(active) > 1:
            conflicts.append(
                {
                    "type": "primary_club_inferred",
                    "user_id": user_id,
                    "selected_club_id": selected["club_id"],
                    "active_club_ids": sorted(item["club_id"] for item in active),
                }
            )

    return {
        "clubs": normalized_clubs,
        "memberships": normalized_memberships,
        "primary_profiles": primary_profiles,
        "conflicts": conflicts,
    }


async def apply_plan(plan: Dict[str, Any]) -> None:
    engine = get_geo_engine()
    if engine is None:
        raise RuntimeError("POSTGRES_URL is required")
    async with engine.begin() as connection:
        for club in plan["clubs"]:
                await connection.execute(
                text(
                    """
                    INSERT INTO clubs (
                        id, slug, name, description, visibility, status,
                        owner_user_id, timezone, emoji, created_at, updated_at
                    ) VALUES (
                        CAST(:id AS uuid), :slug, :name, :description,
                        CAST(:visibility AS club_visibility),
                        CAST(:status AS club_status), CAST(:owner AS uuid),
                        :timezone, :emoji, :created_at, NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name=EXCLUDED.name, description=EXCLUDED.description,
                        visibility=EXCLUDED.visibility, status=EXCLUDED.status,
                        owner_user_id=EXCLUDED.owner_user_id,
                        timezone=EXCLUDED.timezone, emoji=EXCLUDED.emoji,
                        updated_at=NOW()
                    """
                ),
                {
                    **club,
                    "owner": club["owner_user_id"],
                },
            )
        # Insert owners first to satisfy the one-owner invariant deterministically.
        ordered = sorted(plan["memberships"], key=lambda item: item["role"] != "owner")
        for membership in ordered:
            await connection.execute(
                text(
                    """
                    INSERT INTO club_memberships (
                        id, club_id, user_id, role, status,
                        requested_at, joined_at, created_at
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:club_id AS uuid),
                        CAST(:user_id AS uuid), CAST(:role AS club_role),
                        CAST(:status AS membership_status),
                        :requested_at, :joined_at, :created_at
                    )
                    ON CONFLICT (club_id, user_id) DO UPDATE SET
                        role=EXCLUDED.role, status=EXCLUDED.status,
                        requested_at=EXCLUDED.requested_at,
                        joined_at=EXCLUDED.joined_at,
                        version=club_memberships.version+1, updated_at=NOW()
                    """
                ),
                membership,
            )
        for profile in plan["primary_profiles"]:
            await connection.execute(
                text(
                    """
                    INSERT INTO athlete_competitive_profiles (
                        user_id, primary_club_id, primary_selected_at,
                        primary_switch_available_at
                    ) VALUES (
                        CAST(:user_id AS uuid), CAST(:club_id AS uuid),
                        :selected_at, CAST(:selected_at AS timestamptz) + INTERVAL '7 days'
                    )
                    ON CONFLICT (user_id) DO NOTHING
                    """
                ),
                profile,
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO athlete_primary_club_history (
                        id, user_id, club_id, effective_from, reason
                    ) VALUES (
                        CAST(:id AS uuid), CAST(:user_id AS uuid),
                        CAST(:club_id AS uuid), :selected_at, 'legacy_migration'
                    )
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"id": new_id(), **profile},
            )


async def main_async(args: argparse.Namespace) -> None:
    mongo_client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    try:
        plan = await build_plan(mongo_client[os.environ.get("DB_NAME", "sftc_database")])
        args.report.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
        print(
            f"planned {len(plan['clubs'])} clubs, {len(plan['memberships'])} memberships, "
            f"{len(plan['conflicts'])} repairs"
        )
        if args.apply:
            await apply_plan(plan)
            print("migration applied")
        else:
            print("dry run only; pass --apply after reviewing the report")
    finally:
        mongo_client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy Runlete clubs into PostgreSQL")
    parser.add_argument("--report", type=Path, default=Path("run_club_migration_report.json"))
    parser.add_argument("--apply", action="store_true")
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()

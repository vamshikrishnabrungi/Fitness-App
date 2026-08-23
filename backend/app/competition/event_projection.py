from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.models import Activity, ActivityClubAttribution, BestEffort
from backend.app.athletes.models import AthleteProfile
from backend.app.identity.models import User
from backend.app.notifications.models import Notification
from backend.app.core.ids import uuid7
from backend.app.operations.models import OutboxEvent
from backend.app.operations.outbox import enqueue_event

from .models import (
    Achievement,
    Club,
    ClubMembership,
    SystemActivityEvent,
    TerritoryControlHistory,
    Race,
    RaceResult,
)
from .progress import project_activity_leaderboard_facts, recompute_challenge_entries_for_athlete
from .leaderboards import rebuild_activity_club_snapshots
from .race_results import create_provisional_race_results, verify_race_result


async def _user_for_athlete(session: AsyncSession, athlete_id: UUID | None) -> User | None:
    if athlete_id is None:
        return None
    return await session.scalar(
        select(User)
        .join(AthleteProfile, AthleteProfile.user_id == User.id)
        .where(AthleteProfile.id == athlete_id)
    )


async def _add_timeline_event(
    session: AsyncSession,
    *,
    source_event_id: UUID,
    club_id: UUID,
    athlete_id: UUID | None,
    event_type: str,
    visibility: str,
    payload: dict,
    occurred_at: datetime,
) -> SystemActivityEvent:
    semantic_source = str(payload.get("activity_id") or source_event_id)
    deduplication_key = f"{club_id}:{event_type}:{semantic_source}"
    existing_query = select(SystemActivityEvent).where(
            SystemActivityEvent.deduplication_key == deduplication_key,
        )
    existing = await session.scalar(existing_query)
    if existing is not None:
        return existing
    row = SystemActivityEvent(
        club_id=club_id,
        athlete_id=athlete_id,
        event_type=event_type,
        visibility=visibility,
        source_event_id=source_event_id,
        deduplication_key=deduplication_key,
        payload_json=payload,
        occurred_at=occurred_at,
    )
    session.add(row)
    return row


async def _add_notification(
    session: AsyncSession,
    *,
    source_event_id: UUID,
    recipient_user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    payload: dict,
) -> Notification:
    semantic_source = str(payload.get("activity_id") or source_event_id)
    deduplication_key = f"{recipient_user_id}:{notification_type}:{semantic_source}"
    existing = await session.scalar(
        select(Notification).where(
            Notification.deduplication_key == deduplication_key,
        )
    )
    if existing is not None:
        return existing
    row = Notification(
        id=uuid7(),
        recipient_user_id=recipient_user_id,
        source_event_id=source_event_id,
        notification_type=notification_type,
        deduplication_key=deduplication_key,
        title=title[:160],
        body=body[:500],
        payload_json=payload,
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    await enqueue_event(
        session,
        topic="notifications",
        event_type="notification.delivery.requested",
        aggregate_type="notification",
        aggregate_id=row.id,
        payload={"notification_id": str(row.id)},
    )
    return row


async def _project_activity(session: AsyncSession, event: OutboxEvent) -> None:
    activity = await session.get(Activity, event.aggregate_id)
    if activity is None:
        from sqlalchemy import delete

        from .models import LeaderboardFact

        await session.execute(
            delete(LeaderboardFact).where(
                LeaderboardFact.source_type == "activity",
                LeaderboardFact.source_id == event.aggregate_id,
            )
        )
        athlete_id = (event.payload or {}).get("athlete_id")
        if athlete_id:
            await recompute_challenge_entries_for_athlete(session, UUID(str(athlete_id)))
        club_id = (event.payload or {}).get("club_id")
        started_at = (event.payload or {}).get("started_at")
        if club_id and started_at:
            await session.flush()
            await rebuild_activity_club_snapshots(
                session,
                UUID(str(club_id)),
                datetime.fromisoformat(str(started_at).replace("Z", "+00:00")),
            )
        return
    await project_activity_leaderboard_facts(session, activity)
    await recompute_challenge_entries_for_athlete(session, activity.athlete_id)
    await create_provisional_race_results(session, activity)
    attribution = await session.scalar(
        select(ActivityClubAttribution).where(ActivityClubAttribution.activity_id == activity.id)
    )
    if attribution and attribution.club_id:
        await session.flush()
        await rebuild_activity_club_snapshots(session, attribution.club_id, activity.started_at)
    if activity.status != "complete" or activity.visibility == "private":
        return
    if attribution and attribution.club_id:
        await _add_timeline_event(
            session,
            source_event_id=event.id,
            club_id=attribution.club_id,
            athlete_id=activity.athlete_id,
            event_type="eligible_run",
            visibility=activity.visibility,
            payload={
                "activity_id": str(activity.id),
                "distance_m": float(activity.distance_m or 0),
                "moving_seconds": float(activity.moving_seconds or 0),
                "started_at": activity.started_at.isoformat(),
            },
            occurred_at=activity.started_at,
        )

    personal_records = (
        await session.scalars(
            select(BestEffort).where(
                BestEffort.activity_id == activity.id,
                BestEffort.quality_passed.is_(True),
                BestEffort.is_personal_record.is_(True),
            )
        )
    ).all()
    athlete_user = await _user_for_athlete(session, activity.athlete_id)
    for effort in personal_records:
        code = f"personal_record_{effort.distance_code}"
        achievement = await session.scalar(
            select(Achievement).where(
                Achievement.athlete_id == activity.athlete_id,
                Achievement.achievement_code == code,
                Achievement.source_type == "activity",
                Achievement.source_id == activity.id,
            )
        )
        if achievement is None:
            title = f"New {effort.distance_code.upper()} personal record"
            achievement = Achievement(
                id=uuid7(),
                athlete_id=activity.athlete_id,
                club_id=attribution.club_id if attribution else None,
                achievement_code=code,
                source_type="activity",
                source_id=activity.id,
                title=title,
                visibility=activity.visibility,
                payload_json={
                    "activity_id": str(activity.id),
                    "distance_code": effort.distance_code,
                    "elapsed_seconds": float(effort.elapsed_seconds),
                },
                achieved_at=activity.started_at,
            )
            session.add(achievement)
        if attribution and attribution.club_id:
            await _add_timeline_event(
                session,
                source_event_id=event.id,
                club_id=attribution.club_id,
                athlete_id=activity.athlete_id,
                event_type=code[:40],
                visibility=activity.visibility,
                payload={
                    "achievement_id": str(achievement.id),
                    "activity_id": str(activity.id),
                    "distance_code": effort.distance_code,
                    "elapsed_seconds": float(effort.elapsed_seconds),
                },
                occurred_at=activity.started_at,
            )
        if athlete_user:
            await _add_notification(
                session,
                source_event_id=event.id,
                recipient_user_id=athlete_user.id,
                notification_type=code,
                title="New personal record",
                body=f"You set a new {effort.distance_code.upper()} best effort.",
                payload={"activity_id": str(activity.id), "achievement_id": str(achievement.id)},
            )

    histories = (
        await session.scalars(
            select(TerritoryControlHistory).where(
                TerritoryControlHistory.reason_activity_id == activity.id,
                TerritoryControlHistory.controller_type == "club",
            )
        )
    ).all()
    territory_by_club: dict[UUID, dict[str, int]] = defaultdict(
        lambda: {"claimed": 0, "defended": 0, "lost": 0}
    )
    for history in histories:
        if history.event_type == "claim" and history.new_controller_id:
            territory_by_club[history.new_controller_id]["claimed"] += 1
        elif history.event_type == "defence" and history.new_controller_id:
            territory_by_club[history.new_controller_id]["defended"] += 1
        elif history.event_type == "loss":
            if history.previous_controller_id:
                territory_by_club[history.previous_controller_id]["lost"] += 1
            if history.new_controller_id:
                territory_by_club[history.new_controller_id]["claimed"] += 1
    for club_id, counts in territory_by_club.items():
        await _add_timeline_event(
            session,
            source_event_id=event.id,
            club_id=club_id,
            athlete_id=activity.athlete_id,
            event_type=f"territory_{str(club_id)[:8]}",
            visibility="club",
            payload={"activity_id": str(activity.id), **counts},
            occurred_at=datetime.now(timezone.utc),
        )
    own_counts = territory_by_club.get(attribution.club_id) if attribution and attribution.club_id else None
    if athlete_user and own_counts and (own_counts["claimed"] or own_counts["defended"]):
        await _add_notification(
            session,
            source_event_id=event.id,
            recipient_user_id=athlete_user.id,
            notification_type="territory_updated",
            title="Territory updated",
            body=f"Your run claimed {own_counts['claimed']} and defended {own_counts['defended']} road edges for your club.",
            payload={"activity_id": str(activity.id), "club_id": str(attribution.club_id), **own_counts},
        )


async def _project_club_event(session: AsyncSession, event: OutboxEvent) -> None:
    payload = event.payload or {}
    club_id_value = payload.get("club_id")
    club_id = UUID(str(club_id_value)) if club_id_value else (
        event.aggregate_id if event.aggregate_type == "club" else None
    )
    club = await session.get(Club, club_id) if club_id else None

    if event.event_type == "club.created" and club:
        athlete_id = UUID(str(payload["owner_athlete_id"]))
        await _add_timeline_event(
            session,
            source_event_id=event.id,
            club_id=club.id,
            athlete_id=athlete_id,
            event_type="club_created",
            visibility="public" if club.visibility == "public" else "club",
            payload={"club_id": str(club.id), "club_name": club.name},
            occurred_at=event.created_at,
        )
        return

    membership: ClubMembership | None = None
    membership_id = payload.get("membership_id")
    athlete_id_value = payload.get("athlete_id")
    if membership_id:
        membership = await session.get(ClubMembership, UUID(str(membership_id)))
    elif club_id and athlete_id_value:
        membership = await session.scalar(
            select(ClubMembership).where(
                ClubMembership.club_id == club_id,
                ClubMembership.athlete_id == UUID(str(athlete_id_value)),
            )
        )
    if membership and club is None:
        club = await session.get(Club, membership.club_id)
    if membership and club:
        member_user = await _user_for_athlete(session, membership.athlete_id)
        if event.event_type == "club.membership.requested":
            admin_user_ids = tuple(
                await session.scalars(
                    select(AthleteProfile.user_id)
                    .join(ClubMembership, ClubMembership.athlete_id == AthleteProfile.id)
                    .where(
                        ClubMembership.club_id == club.id,
                        ClubMembership.status == "active",
                        ClubMembership.role.in_(("owner", "admin")),
                    )
                )
            )
            for recipient_id in admin_user_ids:
                await _add_notification(
                    session,
                    source_event_id=event.id,
                    recipient_user_id=recipient_id,
                    notification_type="club_join_requested",
                    title="New club request",
                    body=f"An athlete requested to join {club.name}.",
                    payload={"club_id": str(club.id), "membership_id": str(membership.id)},
                )
        elif event.event_type in {"club.membership.active", "club.invitation.accepted"} or (
            event.event_type == "club.membership.decided" and bool(payload.get("approved"))
        ):
            await _add_timeline_event(
                session,
                source_event_id=event.id,
                club_id=club.id,
                athlete_id=membership.athlete_id,
                event_type="membership_joined",
                visibility="public" if club.visibility == "public" else "club",
                payload={"club_id": str(club.id), "athlete_id": str(membership.athlete_id)},
                occurred_at=membership.joined_at or event.created_at,
            )
            if member_user:
                await _add_notification(
                    session,
                    source_event_id=event.id,
                    recipient_user_id=member_user.id,
                    notification_type="club_membership_approved",
                    title="Club membership active",
                    body=f"You are now a member of {club.name}.",
                    payload={"club_id": str(club.id)},
                )
        elif event.event_type == "club.membership.decided" and member_user:
            await _add_notification(
                session,
                source_event_id=event.id,
                recipient_user_id=member_user.id,
                notification_type="club_membership_rejected",
                title="Club request update",
                body=f"Your request to join {club.name} was not approved.",
                payload={"club_id": str(club.id)},
            )
        elif event.event_type in {"club.membership.left", "club.member.removed"}:
            await _add_timeline_event(
                session,
                source_event_id=event.id,
                club_id=club.id,
                athlete_id=membership.athlete_id,
                event_type="membership_left",
                visibility="club",
                payload={"club_id": str(club.id), "athlete_id": str(membership.athlete_id)},
                occurred_at=event.created_at,
            )
            if event.event_type == "club.member.removed" and member_user:
                await _add_notification(
                    session,
                    source_event_id=event.id,
                    recipient_user_id=member_user.id,
                    notification_type="club_member_removed",
                    title="Club membership ended",
                    body=f"Your membership in {club.name} was ended by a club administrator.",
                    payload={"club_id": str(club.id)},
                )

    if event.event_type == "club.primary.changed":
        athlete_id = UUID(str(payload["athlete_id"]))
        athlete_user = await _user_for_athlete(session, athlete_id)
        selected_club_id = UUID(str(payload["club_id"]))
        selected_club = await session.get(Club, selected_club_id)
        if athlete_user and selected_club:
            await _add_notification(
                session,
                source_event_id=event.id,
                recipient_user_id=athlete_user.id,
                notification_type="primary_club_changed",
                title="Primary club changed",
                body=f"Future eligible activities will count for {selected_club.name}.",
                payload={"club_id": str(selected_club.id)},
            )


async def _project_race_result_event(session: AsyncSession, event: OutboxEvent) -> None:
    result = await session.get(RaceResult, event.aggregate_id)
    if result is None:
        return
    race = await session.get(Race, result.race_id)
    athlete_user = await _user_for_athlete(session, result.athlete_id)
    if race and race.club_id:
        await _add_timeline_event(
            session,
            source_event_id=event.id,
            club_id=race.club_id,
            athlete_id=result.athlete_id,
            event_type=f"race_result_{result.status}",
            visibility="club",
            payload={
                "race_id": str(race.id),
                "race_result_id": str(result.id),
                "elapsed_seconds": float(result.elapsed_seconds),
                "route_coverage": float(result.route_coverage),
                "rank": result.rank,
            },
            occurred_at=event.created_at,
        )
    if athlete_user:
        verified = result.status == "verified"
        await _add_notification(
            session,
            source_event_id=event.id,
            recipient_user_id=athlete_user.id,
            notification_type=f"race_result_{result.status}",
            title="Race result verified" if verified else "Race result not verified",
            body=(
                f"Your result for {race.name if race else 'the race'} is verified."
                if verified
                else f"Your result for {race.name if race else 'the race'} did not meet the verification rules."
            ),
            payload={"race_id": str(result.race_id), "race_result_id": str(result.id)},
        )


async def _project_moderation_event(session: AsyncSession, event: OutboxEvent) -> None:
    athlete_id = (event.payload or {}).get("athlete_id")
    if not athlete_id:
        return
    athlete_user = await _user_for_athlete(session, UUID(str(athlete_id)))
    if athlete_user is None:
        return
    if event.event_type == "moderation.flag.decided":
        status = str((event.payload or {}).get("status", "updated"))
        title = "Activity verification restored" if status == "cleared" else "Moderation decision available"
        body = (
            "The competition flag was cleared and eligible results will be reprocessed."
            if status == "cleared"
            else "A competition flag was confirmed. You may appeal from the moderation screen."
        )
    elif event.event_type == "moderation.appeal.decided":
        status = str((event.payload or {}).get("status", "updated"))
        title = "Appeal decision available"
        body = "Your appeal was overturned and the activity will be reprocessed." if status == "overturned" else "Your moderation appeal was upheld."
    else:
        return
    await _add_notification(
        session,
        source_event_id=event.id,
        recipient_user_id=athlete_user.id,
        notification_type=event.event_type.replace(".", "_")[:80],
        title=title,
        body=body,
        payload=event.payload or {},
    )


async def project_domain_event(session: AsyncSession, event: OutboxEvent) -> None:
    """Build idempotent, privacy-filtered read models from durable domain events."""

    if event.event_type in {
        "territory.activity.projected",
        "activity.competition.recompute",
        "activity.competition.disqualified",
    }:
        await _project_activity(session, event)
    elif event.event_type == "race.result.verify.requested":
        await verify_race_result(session, event.aggregate_id)
    elif event.event_type in {"race.result.verified", "race.result.rejected"}:
        await _project_race_result_event(session, event)
    elif event.event_type in {"moderation.flag.decided", "moderation.appeal.decided"}:
        await _project_moderation_event(session, event)
    elif event.topic == "club" or event.event_type == "club.primary.changed":
        await _project_club_event(session, event)
    await session.commit()

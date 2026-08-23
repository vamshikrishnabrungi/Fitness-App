from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Club(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clubs"
    __table_args__ = (UniqueConstraint("slug", name="uq_club_slug"), {"schema": "competition"})
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    home_region_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.geographic_regions.id"))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(7), nullable=False)
    emoji: Mapped[str] = mapped_column(String(16), default="🏃", server_default="🏃", nullable=False)
    avatar_object: Mapped[str | None] = mapped_column(String(500))
    banner_object: Mapped[str | None] = mapped_column(String(500))
    rules: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class ClubMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_memberships"
    __table_args__ = (
        UniqueConstraint("club_id", "athlete_id", name="uq_club_athlete_membership"),
        Index("uq_club_active_owner", "club_id", unique=True, postgresql_where=text("status = 'active' AND role = 'owner'")),
        {"schema": "competition"},
    )
    club_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), default="member", nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id"))


class CompetitiveProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "athlete_competitive_profiles"
    __table_args__ = (UniqueConstraint("athlete_id", name="uq_competitive_profile_athlete"), {"schema": "competition"})
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    primary_club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id"))
    primary_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClubInvitation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_invitations"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_club_invitation_token"), {"schema": "competition"})
    club_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    maximum_uses: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClubBan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_bans"
    __table_args__ = (UniqueConstraint("club_id", "athlete_id", name="uq_club_ban"), {"schema": "competition"})
    club_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    banned_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Season(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("code", name="uq_season_code"), {"schema": "competition"})
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class TerritoryScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "territory_scores"
    __table_args__ = (UniqueConstraint("edge_id", "athlete_id", "local_date", name="uq_daily_edge_athlete_score"), {"schema": "competition"})
    edge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.street_edges.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id"), index=True)
    traversal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.matched_edge_traversals.id", ondelete="CASCADE"), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    coverage: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    speed_mps: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    base_points: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)


class TerritoryCurrentControl(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "territory_current_control"
    __table_args__ = (UniqueConstraint("edge_id", "controller_type", name="uq_current_edge_controller_type"), {"schema": "competition"})
    edge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.street_edges.id", ondelete="CASCADE"), nullable=False, index=True)
    controller_type: Mapped[str] = mapped_column(String(16), nullable=False)
    athlete_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id"))
    club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id"))
    score: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    speed_tiebreaker: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    winning_score_reached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class TerritoryControlHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "territory_control_history"
    __table_args__ = ({"schema": "competition"},)
    edge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.street_edges.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    controller_type: Mapped[str] = mapped_column(String(16), nullable=False)
    previous_controller_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    new_controller_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    score: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    reason_activity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Challenge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "challenges"
    __table_args__ = ({"schema": "competition"},)
    club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"))
    season_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.seasons.id"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(30), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rules_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class ChallengeEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "challenge_entries"
    __table_args__ = (UniqueConstraint("challenge_id", "athlete_id", name="uq_challenge_entry"), {"schema": "competition"})
    challenge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.challenges.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    progress_value: Mapped[float] = mapped_column(Numeric(16, 3), default=0, nullable=False)
    result_status: Mapped[str] = mapped_column(String(20), default="provisional", nullable=False)


class Race(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "races"
    __table_args__ = ({"schema": "competition"},)
    club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"))
    route_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.routes.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_window_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    result_cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    eligibility_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class RaceResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "race_results"
    __table_args__ = (UniqueConstraint("race_id", "athlete_id", name="uq_race_result_athlete"), UniqueConstraint("race_id", "activity_id", name="uq_race_result_activity"), {"schema": "competition"})
    race_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.races.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    elapsed_seconds: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    route_coverage: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="provisional", nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer)


class RaceEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "race_entries"
    __table_args__ = (UniqueConstraint("race_id", "athlete_id", name="uq_race_entry_athlete"), {"schema": "competition"})
    race_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.races.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="registered", nullable=False)


class LeaderboardFact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "leaderboard_facts"
    __table_args__ = (UniqueConstraint("source_type", "source_id", "metric_code", "period_code", name="uq_leaderboard_fact"), {"schema": "competition"})
    source_type: Mapped[str] = mapped_column(String(24), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    athlete_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"))
    club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"))
    region_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.geographic_regions.id"))
    metric_code: Mapped[str] = mapped_column(String(40), nullable=False)
    period_code: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)


class LeaderboardSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "leaderboard_snapshots"
    __table_args__ = (UniqueConstraint("scope_type", "scope_id", "metric_code", "period_code", "computed_at", name="uq_leaderboard_snapshot"), {"schema": "competition"})
    scope_type: Mapped[str] = mapped_column(String(24), nullable=False)
    scope_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    metric_code: Mapped[str] = mapped_column(String(40), nullable=False)
    period_code: Mapped[str] = mapped_column(String(40), nullable=False)
    entries_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    computation_version: Mapped[str] = mapped_column(String(40), nullable=False)


class SystemActivityEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "system_activity_events"
    __table_args__ = (
        UniqueConstraint("source_event_id", "event_type", name="uq_system_activity_source"),
        UniqueConstraint("deduplication_key", name="uq_system_activity_deduplication"),
        {"schema": "competition"},
    )
    club_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    source_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    deduplication_key: Mapped[str] = mapped_column(String(240), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Achievement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint(
            "athlete_id",
            "achievement_code",
            "source_type",
            "source_id",
            name="uq_achievement_source",
        ),
        {"schema": "competition"},
    )
    athlete_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("athlete.profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    club_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competition.clubs.id", ondelete="SET NULL"), index=True
    )
    achievement_code: Mapped[str] = mapped_column(String(80), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

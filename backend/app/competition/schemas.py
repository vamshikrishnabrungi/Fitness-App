from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, model_validator


class ClubCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=180, pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(default="", max_length=5000)
    visibility: str = Field(pattern="^(public|private)$")
    timezone: str = "UTC"
    primary_color: str = Field(default="#FF5533", pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#111827", pattern="^#[0-9A-Fa-f]{6}$")
    emoji: str = Field(default="🏃", min_length=1, max_length=16)
    rules: str = Field(default="", max_length=10000)


class ClubView(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str
    rules: str
    visibility: str
    timezone: str
    primary_color: str
    secondary_color: str
    emoji: str
    status: str
    membership_status: str | None
    membership_role: str | None
    is_primary: bool
    member_count: int
    competitive_profile_version: int
    version: int


class MembershipDecision(BaseModel):
    approve: bool
    expected_version: int = Field(ge=1)


class PrimaryClubCommand(BaseModel):
    club_id: UUID
    expected_version: int = Field(ge=1)


class ClubUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    visibility: Literal["public", "private"] | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    primary_color: str | None = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")
    emoji: str | None = Field(default=None, min_length=1, max_length=16)
    rules: str | None = Field(default=None, max_length=10000)
    expected_version: int = Field(ge=1)


class MembershipRoleCommand(BaseModel):
    role: Literal["admin", "member"]
    expected_version: int = Field(ge=1)


class MembershipMutationCommand(BaseModel):
    expected_version: int = Field(ge=1)


class BanCommand(MembershipMutationCommand):
    reason: str = Field(min_length=2, max_length=5000)
    expires_at: datetime | None = None


class InvitationCreate(BaseModel):
    expires_days: int = Field(default=7, ge=1, le=30)
    maximum_uses: int = Field(default=1, ge=1, le=100)


class OwnershipTransferCommand(BaseModel):
    membership_id: UUID
    owner_expected_version: int = Field(ge=1)
    target_expected_version: int = Field(ge=1)


class ClubStatusCommand(BaseModel):
    expected_version: int = Field(ge=1)


class LeaderboardEntry(BaseModel):
    rank: int
    athlete_id: UUID | None = None
    club_id: UUID | None = None
    display_name: str
    value: float


class LeaderboardView(BaseModel):
    metric_code: str
    period_code: str
    computed_at: datetime
    entries: list[LeaderboardEntry]


ChallengeType = Literal[
    "distance",
    "duration",
    "run_count",
    "consistency",
    "territory_gain",
    "fastest_segment",
]


class ChallengeCreate(BaseModel):
    """Closed challenge contract; values are stored in canonical SI/count units."""

    name: str = Field(min_length=2, max_length=160)
    challenge_type: ChallengeType
    starts_at: datetime
    ends_at: datetime
    target: float | None = Field(default=None, gt=0)
    segment_id: UUID | None = None
    minimum_activity_distance_m: float = Field(default=0, ge=0, le=100_000)

    @model_validator(mode="after")
    def validate_window_and_target(self) -> "ChallengeCreate":
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Challenge timestamps must include a timezone")
        if self.ends_at <= self.starts_at:
            raise ValueError("Challenge end must be after its start")
        if self.ends_at - self.starts_at > timedelta(days=366):
            raise ValueError("Challenge duration cannot exceed 366 days")
        if self.challenge_type == "fastest_segment":
            if self.segment_id is None:
                raise ValueError("Fastest-segment challenges require a segment_id")
            if self.target is not None:
                raise ValueError("Fastest-segment challenges are ranked and do not accept a target")
        else:
            if self.target is None:
                raise ValueError("This challenge type requires a positive target")
            if self.segment_id is not None:
                raise ValueError("segment_id is only valid for fastest-segment challenges")
        if self.challenge_type == "consistency" and self.target and self.target > 366:
            raise ValueError("Consistency target cannot exceed 366 distinct days")
        if self.challenge_type == "run_count" and self.target and self.target > 10_000:
            raise ValueError("Run-count target is outside the supported range")
        return self

    def canonical_rules(self) -> dict:
        units = {
            "distance": "metres",
            "duration": "seconds",
            "run_count": "activities",
            "consistency": "distinct_days",
            "territory_gain": "metres",
            "fastest_segment": "seconds_ascending",
        }
        return {
            "schema_version": 1,
            "target": self.target,
            "unit": units[self.challenge_type],
            "segment_id": str(self.segment_id) if self.segment_id else None,
            "minimum_activity_distance_m": self.minimum_activity_distance_m,
        }


class RaceEligibility(BaseModel):
    minimum_age: int = Field(default=16, ge=16, le=100)
    maximum_age: int | None = Field(default=None, ge=16, le=100)
    competition_level: Literal["any", "beginner", "intermediate", "advanced"] = "any"

    @model_validator(mode="after")
    def validate_age_range(self) -> "RaceEligibility":
        if self.maximum_age is not None and self.maximum_age < self.minimum_age:
            raise ValueError("maximum_age must be greater than or equal to minimum_age")
        return self


class RaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    route_id: UUID
    timezone: str = Field(min_length=1, max_length=64)
    starts_at: datetime
    start_window_minutes: int = Field(default=30, ge=5, le=1440)
    result_cutoff_at: datetime
    participant_capacity: int = Field(default=100, ge=2, le=100_000)
    eligibility: RaceEligibility = Field(default_factory=RaceEligibility)

    @model_validator(mode="after")
    def validate_schedule(self) -> "RaceCreate":
        if self.starts_at.tzinfo is None or self.result_cutoff_at.tzinfo is None:
            raise ValueError("Race timestamps must include a timezone")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        registration_end = self.starts_at + timedelta(minutes=self.start_window_minutes)
        if self.result_cutoff_at <= registration_end:
            raise ValueError("Result cutoff must be after the start window")
        if self.result_cutoff_at - self.starts_at > timedelta(days=7):
            raise ValueError("Race result window cannot exceed seven days")
        return self

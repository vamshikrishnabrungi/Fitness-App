from __future__ import annotations

import hashlib
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Literal, Optional, Sequence

from pydantic import BaseModel, Field, field_validator, model_validator


PRIMARY_CLUB_COOLDOWN_DAYS = 7
TERRITORY_WINDOW_DAYS = 28
TERRITORY_HALF_LIFE_DAYS = 14
TERRITORY_MAX_SCORING_DAYS = 7
CLUB_EDGE_MEMBER_CAP = 5
MIN_TERRITORY_ACTIVITY_M = 2_500
MIN_EDGE_COVERAGE = 0.80
MIN_MATCH_CONFIDENCE = 0.85


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return value[:80] or "run-club"


def invitation_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode("utf-8")).hexdigest()


class CursorPage(BaseModel):
    items: List[Dict[str, Any]]
    next_cursor: Optional[str] = None


class ClubCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: Optional[str] = Field(default=None, max_length=80)
    description: Optional[str] = Field(default=None, max_length=2_000)
    rules: Optional[str] = Field(default=None, max_length=4_000)
    visibility: Literal["public", "private"] = "public"
    home_region_id: Optional[str] = None
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    primary_color: str = Field(default="#FF4F2E", pattern=r"^#[0-9A-Fa-f]{6}$")
    emoji: str = Field(default="🏃", min_length=1, max_length=8)
    avatar_url: Optional[str] = Field(default=None, max_length=2_000)
    banner_url: Optional[str] = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def location_is_complete(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class ClubUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2_000)
    rules: Optional[str] = Field(default=None, max_length=4_000)
    visibility: Optional[Literal["public", "private"]] = None
    home_region_id: Optional[str] = None
    timezone: Optional[str] = Field(default=None, min_length=1, max_length=80)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    primary_color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    emoji: Optional[str] = Field(default=None, min_length=1, max_length=8)
    avatar_url: Optional[str] = Field(default=None, max_length=2_000)
    banner_url: Optional[str] = Field(default=None, max_length=2_000)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def location_is_complete(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class MembershipDecision(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=1_000)


class RoleUpdate(BaseModel):
    role: Literal["admin", "member"]
    version: int = Field(ge=1)


class OwnershipTransfer(BaseModel):
    new_owner_user_id: str
    version: int = Field(ge=1)


class ClubInvitationCreate(BaseModel):
    invited_user_id: Optional[str] = None
    email: Optional[str] = Field(default=None, max_length=320)
    role: Literal["admin", "member"] = "member"
    expires_in_days: int = Field(default=7, ge=1, le=30)

    @model_validator(mode="after")
    def has_recipient(self):
        if not self.invited_user_id and not self.email:
            raise ValueError("invited_user_id or email is required")
        return self


class PrimaryClubUpdate(BaseModel):
    club_id: str


ChallengeMetric = Literal[
    "distance_m",
    "moving_time_sec",
    "run_count",
    "consistency_days",
    "territory_gain_m",
    "fastest_segment_sec",
]


class ClubChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2_000)
    metric: ChallengeMetric
    target: Optional[float] = Field(default=None, gt=0)
    segment_id: Optional[str] = None
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timezone-aware datetime is required")
        return value

    @model_validator(mode="after")
    def valid_window(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if self.metric == "fastest_segment_sec" and not self.segment_id:
            raise ValueError("segment_id is required for fastest segment challenges")
        return self


class ClubRaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2_000)
    timezone: str = Field(min_length=1, max_length=80)
    starts_at: datetime
    start_window_minutes: int = Field(default=30, ge=5, le=180)
    result_cutoff_at: datetime
    participant_capacity: Optional[int] = Field(default=None, gt=0, le=100_000)
    route: List[List[float]] = Field(min_length=2, max_length=20_000)
    route_distance_m: float = Field(gt=0)

    @field_validator("route")
    @classmethod
    def valid_coordinates(cls, value: List[List[float]]) -> List[List[float]]:
        for point in value:
            if len(point) != 2 or not -180 <= point[0] <= 180 or not -90 <= point[1] <= 90:
                raise ValueError("route coordinates must be [longitude, latitude]")
        return value

    @model_validator(mode="after")
    def valid_window(self):
        if self.result_cutoff_at <= self.starts_at:
            raise ValueError("result_cutoff_at must be after starts_at")
        return self


class CompetitionFlagCreate(BaseModel):
    activity_id: str
    reason_code: Literal[
        "vehicle_suspected",
        "duplicate_activity",
        "gps_manipulation",
        "wrong_athlete",
        "route_violation",
        "other",
    ]
    details: Optional[str] = Field(default=None, max_length=2_000)


class ModerationDecisionCreate(BaseModel):
    decision: Literal["uphold", "dismiss", "reopen"]
    notes: Optional[str] = Field(default=None, max_length=4_000)


class ModerationAppealCreate(BaseModel):
    reason: str = Field(min_length=10, max_length=4_000)


class PushTokenCreate(BaseModel):
    token: str = Field(min_length=20, max_length=4_096)
    platform: Literal["ios", "android"]


class TerritoryTileSessionCreate(BaseModel):
    layer: Literal["me", "club", "competitors"] = "me"
    club_id: Optional[str] = None

    @model_validator(mode="after")
    def club_layer_has_club(self):
        if self.layer == "club" and not self.club_id:
            raise ValueError("club_id is required for the club layer")
        return self


def territory_daily_points(
    *,
    confidence: float,
    coverage: float,
    age_days: float,
) -> float:
    if confidence < MIN_MATCH_CONFIDENCE or coverage < MIN_EDGE_COVERAGE:
        return 0.0
    if age_days < 0 or age_days >= TERRITORY_WINDOW_DAYS:
        return 0.0
    decay = 0.5 ** (age_days / TERRITORY_HALF_LIFE_DAYS)
    return round(100.0 * min(1.0, confidence) * min(1.0, coverage) * decay, 6)


def score_controller_traversals(
    traversals: Iterable[Dict[str, Any]],
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    reference = now or utc_now()
    best_by_day: Dict[date, Dict[str, Any]] = {}
    for traversal in traversals:
        if not traversal.get("qualified", True):
            continue
        local_day = traversal.get("local_activity_date")
        if isinstance(local_day, str):
            local_day = date.fromisoformat(local_day[:10])
        if not isinstance(local_day, date):
            continue
        activity_time = traversal.get("activity_started_at") or traversal.get("matched_at")
        if isinstance(activity_time, str):
            activity_time = datetime.fromisoformat(activity_time.replace("Z", "+00:00"))
        if not isinstance(activity_time, datetime):
            activity_time = datetime.combine(local_day, datetime.min.time(), tzinfo=timezone.utc)
        if activity_time.tzinfo is None:
            activity_time = activity_time.replace(tzinfo=timezone.utc)
        age_days = (
            reference - activity_time.astimezone(timezone.utc)
        ).total_seconds() / 86400
        points = territory_daily_points(
            confidence=float(traversal.get("confidence") or 0),
            coverage=float(traversal.get("coverage") or 0),
            age_days=age_days,
        )
        if points <= 0:
            continue
        candidate = {**traversal, "points": points, "activity_time": activity_time}
        current = best_by_day.get(local_day)
        if current is None or (
            points,
            -float(traversal.get("elapsed_time_sec") or float("inf")),
        ) > (
            current["points"],
            -float(current.get("elapsed_time_sec") or float("inf")),
        ):
            best_by_day[local_day] = candidate

    selected = sorted(
        best_by_day.values(),
        key=lambda item: (item["points"], -float(item.get("elapsed_time_sec") or float("inf"))),
        reverse=True,
    )[:TERRITORY_MAX_SCORING_DAYS]
    fastest = min(
        (float(item["elapsed_time_sec"]) for item in selected if item.get("elapsed_time_sec")),
        default=None,
    )
    return {
        "score": round(sum(item["points"] for item in selected), 6),
        "scoring_days": len(selected),
        "fastest_time_sec": fastest,
        "selected": selected,
        "score_reached_at": max(
            (item["activity_time"] for item in selected),
            default=None,
        ),
        "expires_at": max(
            (item["activity_time"] + timedelta(days=TERRITORY_WINDOW_DAYS) for item in selected),
            default=None,
        ),
    }


def choose_controller(scores: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    eligible = [item for item in scores if float(item.get("score") or 0) > 0]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda item: (
            -float(item["score"]),
            float(item.get("fastest_time_sec") or float("inf")),
            item.get("score_reached_at")
            or item.get("controlled_since")
            or datetime.max.replace(tzinfo=timezone.utc),
            str(item.get("controller_id")),
        ),
    )[0]


def aggregate_club_edge_score(member_scores: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    strongest = sorted(
        [item for item in member_scores if float(item.get("score") or 0) > 0],
        key=lambda item: float(item["score"]),
        reverse=True,
    )[:CLUB_EDGE_MEMBER_CAP]
    return {
        "score": round(sum(float(item["score"]) for item in strongest), 6),
        "member_count": len(strongest),
        "scoring_days": sum(int(item.get("scoring_days") or 0) for item in strongest),
        "fastest_time_sec": min(
            (float(item["fastest_time_sec"]) for item in strongest if item.get("fastest_time_sec")),
            default=None,
        ),
        "score_reached_at": max(
            (item["score_reached_at"] for item in strongest if item.get("score_reached_at")),
            default=None,
        ),
        "expires_at": max(
            (item["expires_at"] for item in strongest if item.get("expires_at")),
            default=None,
        ),
    }

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from backend.activity_domain import ActivityCreate, ActivityPoint


class LiveLocationStart(BaseModel):
    activity_id: Optional[str] = None
    trusted_contact_name: Optional[str] = Field(default=None, max_length=120)
    duration_minutes: int = Field(default=180, ge=15, le=720)


class LiveLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timestamp: datetime
    accuracy_m: Optional[float] = Field(default=None, ge=0, le=5_000)
    battery_percent: Optional[int] = Field(default=None, ge=0, le=100)


class SafetyReportCreate(BaseModel):
    target_type: Literal["activity", "user", "segment", "route", "club", "other"]
    target_id: Optional[str] = Field(default=None, max_length=160)
    category: Literal[
        "cheating",
        "unsafe_content",
        "privacy",
        "harassment",
        "incorrect_data",
        "other",
    ]
    detail: str = Field(min_length=10, max_length=4_000)


class AccountDeletionCreate(BaseModel):
    confirmation: Literal["DELETE"]
    reason: Optional[str] = Field(default=None, max_length=1_000)


class HealthActivityItem(BaseModel):
    external_id: str = Field(min_length=1, max_length=240)
    activity: ActivityCreate


class HealthActivityBatch(BaseModel):
    provider: Literal["apple_health", "health_connect"]
    cursor: Optional[str] = Field(default=None, max_length=1_000)
    activities: List[HealthActivityItem] = Field(min_length=1, max_length=100)

    @field_validator("activities")
    @classmethod
    def unique_external_ids(cls, value: List[HealthActivityItem]) -> List[HealthActivityItem]:
        external_ids = [item.external_id for item in value]
        if len(external_ids) != len(set(external_ids)):
            raise ValueError("external_id values must be unique within a batch")
        return value


class ActivityUploadStart(BaseModel):
    start_time: datetime
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
    activity_type: Literal["run", "treadmill"] = "run"
    run_type: Literal["training", "race", "workout", "commute"] = "training"
    title: Optional[str] = Field(default=None, max_length=120)
    visibility: Optional[Literal["private", "clubs", "public"]] = None


class ActivityUploadChunk(BaseModel):
    sequence: int = Field(ge=0, le=100_000)
    points: List[ActivityPoint] = Field(min_length=1, max_length=500)


class ActivityUploadComplete(BaseModel):
    end_time: datetime
    paused_duration_sec: int = Field(default=0, ge=0)

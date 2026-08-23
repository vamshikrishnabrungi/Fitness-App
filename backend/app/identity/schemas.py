from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(default="login", pattern="^(login|register)$")


class OTPRequestResult(BaseModel):
    challenge_id: UUID
    expires_at: datetime
    debug_code: str | None = None


class OTPVerify(BaseModel):
    challenge_id: UUID
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern="^[0-9]{6}$")
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_date: date | None = None
    device_name: str | None = Field(default=None, max_length=160)

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=500)
    device_name: str | None = Field(default=None, max_length=160)


class UserView(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    birth_date: date | None
    onboarding_completed: bool
    roles: list[str]
    version: int


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserView


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_date: date | None = None
    expected_version: int = Field(ge=1)


class PrivacyView(BaseModel):
    default_activity_visibility: str
    public_leaderboards: bool
    live_location_enabled: bool
    profile_discoverable: bool
    version: int


class PrivacyUpdate(BaseModel):
    default_activity_visibility: str | None = Field(default=None, pattern="^(public|club|private)$")
    public_leaderboards: bool | None = None
    live_location_enabled: bool | None = None
    profile_discoverable: bool | None = None
    expected_version: int = Field(ge=1)


class ConsentUpdate(BaseModel):
    consent_type: str = Field(pattern="^(connected_health|food_image_analysis|ai_explanations)$")
    policy_version: str = Field(min_length=1, max_length=40)
    granted: bool


class HiddenZoneCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: int = Field(default=400, ge=200, le=2000)


class HiddenZoneView(BaseModel):
    id: UUID
    label: str
    radius_m: int
    version: int


class SessionView(BaseModel):
    id: UUID
    device_name: str | None
    user_agent: str | None
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime
    revoked_at: datetime | None


class AccountDeletionCommand(BaseModel):
    expected_version: int = Field(ge=1)


class AccountDeletionView(BaseModel):
    id: UUID
    status: str
    requested_at: datetime
    execute_after: datetime


class DataExportView(BaseModel):
    id: UUID
    status: str
    requested_at: datetime
    completed_at: datetime | None = None
    download_url: str | None = None
    expires_at: datetime | None = None

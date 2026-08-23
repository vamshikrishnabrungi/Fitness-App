from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SportInput(BaseModel):
    sport_code: str
    event_code: str | None = None
    role_code: str | None = None
    discipline_code: str | None = None
    format_code: str | None = None
    weight_class_code: str | None = None
    is_primary: bool = False
    weekly_external_minutes: int = Field(default=0, ge=0, le=2400)
    sessions_per_week: int = Field(default=0, ge=0, le=21)


class AvailabilityInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_minute: int = Field(ge=0, le=1439)
    duration_minutes: int = Field(ge=15, le=360)


class GoalInput(BaseModel):
    goal_type: str
    target_value: float | None = None
    target_unit: str | None = None
    target_date: date | None = None


class OnboardingCommand(BaseModel):
    timezone: str = "UTC"
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    height_cm: float | None = Field(default=None, ge=100, le=260)
    weight_kg: float | None = Field(default=None, ge=30, le=350)
    competition_level: str = Field(pattern="^(recreational|club|regional|national|international)$")
    training_age_years: int = Field(ge=0, le=60)
    maximum_session_minutes: int = Field(ge=20, le=300)
    sports: list[SportInput] = Field(min_length=1, max_length=4)
    availability: list[AvailabilityInput] = Field(min_length=1, max_length=21)
    equipment_codes: list[str] = Field(default_factory=list, max_length=100)
    environments: list[str] = Field(default_factory=list, max_length=10)
    goal: GoalInput

    @model_validator(mode="after")
    def one_primary(self):
        if sum(1 for sport in self.sports if sport.is_primary) != 1:
            raise ValueError("exactly one sport must be primary")
        return self


class AthleteProfileView(BaseModel):
    id: UUID
    timezone: str
    country_code: str | None
    height_cm: float | None
    weight_kg: float | None
    competition_level: str
    training_age_years: int
    maximum_session_minutes: int
    sports: list[SportInput]
    availability: list[AvailabilityInput]
    equipment_codes: list[str]
    active_goal: GoalInput | None
    version: int

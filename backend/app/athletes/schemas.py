from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.knowledge.sports import SUPPORTED_TRAINING_SPORTS
from backend.app.knowledge.training_contract import normalize_goal, normalize_phase, sport_scope_key


TRAINING_VENUES = frozenset({
    "home",
    "gym",
    "pool",
    "track",
    "field",
    "court",
    "road",
    "trail",
    "combat_gym",
})
VENUE_ALIASES = {
    "combat": "combat_gym",
    "boxing_gym": "combat_gym",
    "mma_gym": "combat_gym",
    "ring": "combat_gym",
    "mat": "combat_gym",
    "trail_supported": "trail",
}


def normalize_venue(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    normalized = VENUE_ALIASES.get(normalized, normalized)
    if normalized not in TRAINING_VENUES:
        raise ValueError(f"unsupported training venue: {value}")
    return normalized


def normalize_venues(values: list[str]) -> list[str]:
    normalized = sorted({normalize_venue(value) for value in values})
    if not normalized:
        raise ValueError("at least one training venue is required")
    return normalized


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

    @field_validator("sport_code")
    @classmethod
    def validate_sport_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_TRAINING_SPORTS:
            raise ValueError("sport is not supported by the training dataset")
        return normalized

    @model_validator(mode="after")
    def validate_training_scope(self):
        sport_scope_key(
            self.sport_code,
            event_code=self.event_code,
            role_code=self.role_code,
            discipline_code=self.discipline_code,
            format_code=self.format_code,
        )
        return self


class AvailabilityInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_minute: int = Field(ge=0, le=1439)
    duration_minutes: int = Field(ge=15, le=360)
    environments: list[str] = Field(min_length=1, max_length=9)

    @field_validator("environments")
    @classmethod
    def validate_environments(cls, value: list[str]) -> list[str]:
        return normalize_venues(value)


class EquipmentAccessInput(BaseModel):
    equipment_code: str = Field(min_length=1, max_length=60)
    environments: list[str] = Field(min_length=1, max_length=9)

    @field_validator("equipment_code")
    @classmethod
    def normalize_equipment(cls, value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")

    @field_validator("environments")
    @classmethod
    def validate_environments(cls, value: list[str]) -> list[str]:
        return normalize_venues(value)


class MethodFamiliarityInput(BaseModel):
    method_code: str = Field(min_length=1, max_length=100)
    familiarity: Literal["familiar", "previously_exposed", "unfamiliar", "unknown"]
    successful_exposures: int = Field(default=0, ge=0, le=100000)
    last_performed_on: date | None = None

    @field_validator("method_code")
    @classmethod
    def normalize_method_code(cls, value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")

    @model_validator(mode="after")
    def validate_exposure_claim(self):
        if self.familiarity == "familiar" and self.successful_exposures == 0:
            raise ValueError("familiar methods require at least one successful exposure")
        if self.familiarity == "unfamiliar" and self.successful_exposures > 0:
            raise ValueError("unfamiliar methods cannot have successful exposures")
        return self


class WeeklyRecurrenceInput(BaseModel):
    frequency: Literal["weekly"] = "weekly"
    interval_weeks: int = Field(default=1, ge=1, le=12)
    until: date | None = None


class ExternalLoadInput(BaseModel):
    sport_code: str
    load_type: Literal["practice", "competition", "conditioning", "other"]
    starts_at: datetime
    duration_minutes: int = Field(ge=1, le=600)
    intensity: Literal["recovery", "easy", "moderate", "hard", "high", "maximal"]
    recurrence: WeeklyRecurrenceInput | None = None

    @field_validator("sport_code")
    @classmethod
    def validate_sport_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_TRAINING_SPORTS:
            raise ValueError("external load sport is not supported")
        return normalized

    @field_validator("starts_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("external load starts_at must include a timezone")
        return value

    @model_validator(mode="after")
    def recurrence_must_not_end_before_first_session(self):
        if self.recurrence and self.recurrence.until and self.recurrence.until < self.starts_at.date():
            raise ValueError("external load recurrence cannot end before starts_at")
        return self


class GoalInput(BaseModel):
    goal_type: str
    target_value: float | None = None
    target_unit: str | None = None
    target_date: date | None = None

    @field_validator("goal_type")
    @classmethod
    def validate_goal_type(cls, value: str) -> str:
        return normalize_goal(value)


class OnboardingCommand(BaseModel):
    timezone: str = "UTC"
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    height_cm: float | None = Field(default=None, ge=100, le=260)
    weight_kg: float | None = Field(default=None, ge=30, le=350)
    competition_level: str = Field(pattern="^(recreational|club|regional|national|international)$")
    fitness_level: Literal["beginner", "intermediate", "advanced"] | None = None
    training_age_years: int = Field(ge=0, le=60)
    maximum_session_minutes: int = Field(ge=20, le=300)
    season_phase: str = "general_preparation"
    sports: list[SportInput] = Field(min_length=1, max_length=4)
    availability: list[AvailabilityInput] = Field(min_length=1, max_length=21)
    external_loads: list[ExternalLoadInput] = Field(default_factory=list, max_length=100)
    equipment_access: list[EquipmentAccessInput] = Field(default_factory=list, max_length=100)
    method_familiarity: list[MethodFamiliarityInput] = Field(default_factory=list, max_length=500)
    cross_training_consent: bool = False
    health_context: dict[str, Any] = Field(default_factory=dict)
    goal: GoalInput

    @model_validator(mode="after")
    def one_primary(self):
        if sum(1 for sport in self.sports if sport.is_primary) != 1:
            raise ValueError("exactly one sport must be primary")
        equipment_codes = [row.equipment_code for row in self.equipment_access]
        if len(equipment_codes) != len(set(equipment_codes)):
            raise ValueError("equipment access must contain unique equipment codes")
        method_codes = [row.method_code for row in self.method_familiarity]
        if len(method_codes) != len(set(method_codes)):
            raise ValueError("method familiarity must contain unique method codes")
        return self

    @field_validator("season_phase")
    @classmethod
    def validate_season_phase(cls, value: str) -> str:
        return normalize_phase(value)


class AthleteProfileView(BaseModel):
    id: UUID
    timezone: str
    country_code: str | None
    height_cm: float | None
    weight_kg: float | None
    competition_level: str
    training_age_years: int
    maximum_session_minutes: int
    season_phase: str
    sports: list[SportInput]
    availability: list[AvailabilityInput]
    external_loads: list[ExternalLoadInput]
    equipment_access: list[EquipmentAccessInput]
    method_familiarity: list[MethodFamiliarityInput]
    cross_training_consent: bool
    health_context: dict[str, Any] = Field(default_factory=dict)
    active_goal: GoalInput | None
    version: int

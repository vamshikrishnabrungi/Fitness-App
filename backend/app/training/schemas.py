from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    weeks: Literal[4] = 4
    starts_on: date | None = None
    fitness_level: Literal["beginner", "intermediate", "advanced"] | None = None
    training_days_per_week: int | None = Field(default=None, ge=5, le=7)
    health_context: dict[str, Any] = Field(default_factory=dict)
    schedule_constraints: str | None = Field(default=None, max_length=2000)


class SessionItemView(BaseModel):
    id: UUID
    source: Literal["catalog", "generated"] = "catalog"
    method_id: UUID | None = None
    method_name: str
    method_version: int | None = None
    block_type: str
    prescription: dict[str, Any]
    alternatives: list[UUID]
    instructions: list[str] = Field(default_factory=list)
    coaching_cues: list[str] = Field(default_factory=list)
    common_errors: list[str] = Field(default_factory=list)
    safety_boundaries: list[str] = Field(default_factory=list)
    description: str | None = None
    equipment: list[str] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)
    progressions: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)


class SessionView(BaseModel):
    id: UUID
    scheduled_for: datetime
    session_type: str
    purpose: str
    estimated_minutes: int
    venue_code: str | None = None
    status: str
    explanation: str
    week_number: int | None = None
    week_theme: str | None = None
    progression_rule: str | None = None
    items: list[SessionItemView]
    version: int


class CompletionCommand(BaseModel):
    duration_minutes: int = Field(ge=1, le=600)
    session_rpe: float = Field(ge=0, le=10)
    completion_ratio: float = Field(ge=0, le=1)
    pain_flag: bool = False
    notes: str | None = Field(default=None, max_length=2000)
    expected_version: int = Field(ge=1)


class PlanWeekView(BaseModel):
    week_number: int
    starts_on: date
    planned_load: float
    deload: bool
    intent: str


class PlanView(BaseModel):
    id: UUID
    status: str
    starts_on: str
    ends_on: str
    planner_version: str
    content_release_id: UUID | None
    dataset_hash: str | None = None
    materialized_through: date | None
    sport_code: str | None = None
    scope_code: str | None = None
    phase_code: str | None = None
    goal_code: str | None = None
    decision_trace: list[dict[str, Any]] = Field(default_factory=list)
    weeks: list[PlanWeekView] = Field(default_factory=list)
    sessions: list[SessionView]

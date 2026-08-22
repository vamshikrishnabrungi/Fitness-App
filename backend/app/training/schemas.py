from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    weeks: int = Field(default=4, ge=1, le=52)
    starts_on: date | None = None


class SessionItemView(BaseModel):
    id: UUID
    method_id: UUID
    method_name: str
    method_version: int
    block_type: str
    prescription: dict[str, Any]
    alternatives: list[UUID]


class SessionView(BaseModel):
    id: UUID
    scheduled_for: datetime
    session_type: str
    purpose: str
    estimated_minutes: int
    status: str
    explanation: str
    items: list[SessionItemView]
    version: int


class CompletionCommand(BaseModel):
    duration_minutes: int = Field(ge=1, le=600)
    session_rpe: float = Field(ge=0, le=10)
    completion_ratio: float = Field(ge=0, le=1)
    pain_flag: bool = False
    notes: str | None = Field(default=None, max_length=2000)
    expected_version: int = Field(ge=1)


class PlanView(BaseModel):
    id: UUID
    status: str
    starts_on: str
    ends_on: str
    planner_version: str
    content_release_id: UUID
    materialized_through: date | None
    sessions: list[SessionView]

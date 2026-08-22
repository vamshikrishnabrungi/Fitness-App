from typing import Literal

from pydantic import BaseModel, Field


class AppealCreate(BaseModel):
    reason: str = Field(min_length=20, max_length=5000)


class FlagDecisionCommand(BaseModel):
    decision: Literal["confirm_violation", "clear_flag"]
    rationale: str = Field(min_length=20, max_length=5000)
    expected_version: int = Field(ge=1)


class AppealDecisionCommand(BaseModel):
    decision: Literal["uphold", "overturn"]
    rationale: str = Field(min_length=20, max_length=5000)
    expected_version: int = Field(ge=1)

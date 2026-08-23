from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.config import get_settings
from backend.app.core.openai_responses import create_structured_response

from .planner import MethodSelection, PlanDraft, PlannerInput

PROMPT_VERSION = "workout-selection-openai-v1"
RESPONSE_SCHEMA_VERSION = "1.0"


class AISelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurrence_id: str
    slot_id: UUID
    method_id: UUID
    prescription: dict[str, Any]
    alternative_method_ids: list[UUID] = Field(default_factory=list, max_length=3)
    rationale_code: Literal[
        "objective_fit",
        "fatigue_management",
        "technical_fit",
        "equipment_fit",
        "progression_fit",
        "variation",
    ]


class AIWorkoutSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    selections: list[AISelection]

    def to_domain(self) -> list[MethodSelection]:
        return [
            MethodSelection(
                occurrence_id=item.occurrence_id,
                slot_id=item.slot_id,
                method_id=item.method_id,
                prescription=dict(item.prescription),
                alternative_method_ids=tuple(item.alternative_method_ids),
                rationale_code=item.rationale_code,
            )
            for item in self.selections
        ]


@dataclass(frozen=True)
class SelectionProviderResult:
    output: AIWorkoutSelection
    provider: str
    model_id: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None


class WorkoutSelectionProvider(ABC):
    @abstractmethod
    async def select(
        self,
        *,
        packet: dict[str, Any],
        validation_errors: list[str] | None = None,
    ) -> SelectionProviderResult: ...


def build_selection_packet(state: PlannerInput, draft: PlanDraft) -> dict[str, Any]:
    """Return only the reviewed candidate projection and planning context the model needs."""
    return {
        "schema_version": RESPONSE_SCHEMA_VERSION,
        "input_hash": draft.input_hash,
        "athlete_context": {
            "level_rank": state.level_rank,
            "goal_code": state.goal_code,
            "primary_sport": state.primary_sport,
            "event_code": state.event_code,
            "role_code": state.role_code,
            "discipline_code": state.discipline_code,
            "format_code": state.format_code,
            "weight_class_code": state.weight_class_code,
            "target_date": state.target_date.isoformat() if state.target_date else None,
            "maximum_session_minutes": state.maximum_session_minutes,
        },
        "sessions": [
            {
                "scheduled_for": session.scheduled_for.isoformat(),
                "recipe_id": str(session.definition.recipe_id),
                "recipe_version": session.definition.recipe_version,
                "session_type": session.definition.session_type,
                "purpose": session.definition.purpose,
                "load_class": session.definition.load_class,
                "estimated_minutes": session.definition.estimated_minutes,
                "slots": [
                    {
                        "occurrence_id": slot.occurrence_id,
                        "slot_id": str(slot.definition.id),
                        "slot_code": slot.definition.code,
                        "quality": slot.definition.quality,
                        "training_role": slot.definition.role,
                        "block_type": slot.definition.block_type,
                        "dose_bounds": slot.definition.dose,
                        "candidates": [
                            {
                                "method_id": str(method.id),
                                "method_version": method.method_version,
                                "code": method.code,
                                "technical_cost": method.technical_cost,
                                "impact_cost": method.impact_cost,
                                "fatigue_cost": method.fatigue_cost,
                            }
                            for method in slot.candidates
                        ],
                    }
                    for slot in session.slots
                ],
            }
            for session in draft.sessions
        ],
    }


class OpenAIWorkoutSelectionProvider(WorkoutSelectionProvider):
    """Constrained OpenAI selector. PostgreSQL and deterministic validators stay authoritative."""

    async def select(
        self,
        *,
        packet: dict[str, Any],
        validation_errors: list[str] | None = None,
    ) -> SelectionProviderResult:
        settings = get_settings()
        repair = {"previous_validation_errors": validation_errors} if validation_errors else None
        started = perf_counter()
        response = await create_structured_response(
            model=settings.openai_workout_model,
            system=SYSTEM_CONSTRAINTS,
            user_content=(
                "Select one method for every slot occurrence and choose only dose values allowed by dose_bounds. "
                f"Candidate packet: {json.dumps(packet, sort_keys=True, separators=(',', ':'))}. "
                f"Repair context: {json.dumps(repair, sort_keys=True, separators=(',', ':'))}."
            ),
            schema_name="runlete_workout_selection",
            schema=AIWorkoutSelection.model_json_schema(),
            # prescription is deliberately an open object because each released
            # method has different registered dose fields. The backend validates
            # every field and bound after the model responds.
            strict=False,
            max_output_tokens=8_000,
        )
        output = AIWorkoutSelection.model_validate_json(response.text)
        return SelectionProviderResult(
            output=output,
            provider="openai",
            model_id=response.model,
            latency_ms=int((perf_counter() - started) * 1000),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )


SYSTEM_CONSTRAINTS = """You are Runlete's constrained workout-selection component. The reviewed recipe already defines the session structure. Select only method_id values supplied inside that exact slot. Return exactly one selection for every occurrence_id and no others. Use only the supplied prescription fields and values within their fixed values or bounds. Alternatives must come from the same slot and must not repeat the selected method. Never invent an exercise, identifier, dose field, medical instruction, rehabilitation plan, sport technique, or extra session. Return the JSON schema only and use a permitted rationale_code; do not provide chain-of-thought."""


def get_workout_selection_provider() -> WorkoutSelectionProvider:
    return OpenAIWorkoutSelectionProvider()

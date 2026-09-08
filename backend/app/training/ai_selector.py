from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.config import get_settings
from backend.app.core.openai_responses import create_structured_response

from .planner import PlanDraft, PlannerInput

PROMPT_VERSION = "hybrid-full-program-v3"
RESPONSE_SCHEMA_VERSION = "3.0"


class GeneratedMistake(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mistake: str = Field(min_length=1, max_length=300)
    correction: str = Field(min_length=1, max_length=300)


class GeneratedExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_exercise_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=700)
    reason_catalog_is_insufficient: str = Field(min_length=1, max_length=700)
    equipment: list[str]
    movement_pattern: str
    physical_qualities: list[str]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    instructions: list[str] = Field(min_length=1)
    coaching_cues: list[str] = Field(min_length=1)
    common_mistakes: list[GeneratedMistake] = Field(min_length=1)
    safety_information: list[str] = Field(min_length=1)
    contraindications: list[str]
    regressions: list[str]
    progressions: list[str]


class CatalogExerciseRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["catalog"]
    method_id: UUID
    method_version: int = Field(ge=1)


class GeneratedExerciseRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["generated"]
    generated_exercise_id: str = Field(min_length=1, max_length=80)


ExerciseRef = Annotated[CatalogExerciseRef | GeneratedExerciseRef, Field(discriminator="source")]


class CircuitDose(BaseModel):
    model_config = ConfigDict(extra="forbid")
    circuit_id: str = Field(min_length=1, max_length=40)
    order: int = Field(ge=1, le=30)
    rounds: int = Field(ge=1, le=20)
    work_seconds: int = Field(ge=5, le=600)
    transition_seconds: int = Field(ge=0, le=180)
    rest_between_exercises_seconds: int = Field(ge=0, le=300)
    rest_between_rounds_seconds: int = Field(ge=0, le=900)


class ExerciseOccurrence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exercise: ExerciseRef
    prescription: dict[str, Any]
    estimated_minutes: int = Field(ge=1, le=90)
    circuit: CircuitDose | None = None
    coaching_note: str = Field(default="", max_length=500)


class ProgramBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Coaches may use a more specific label than the standard display groups.
    # The mobile app maps known labels and humanizes unfamiliar ones.
    block_type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    purpose: str = Field(min_length=1, max_length=500)
    estimated_minutes: int = Field(ge=1, le=120)
    exercises: list[ExerciseOccurrence] = Field(min_length=1)


class ProgramSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    week_number: int = Field(ge=1, le=4)
    session_number: int = Field(ge=1, le=7)
    scheduled_for: str
    title: str = Field(min_length=1, max_length=180)
    purpose: str = Field(min_length=1, max_length=1000)
    load_class: Literal["recovery", "light", "moderate", "hard"]
    estimated_minutes: int = Field(ge=1, le=180)
    blocks: list[ProgramBlock] = Field(min_length=1)


class ProgramWeek(BaseModel):
    model_config = ConfigDict(extra="forbid")
    week_number: int = Field(ge=1, le=4)
    theme: str = Field(min_length=1, max_length=500)
    progression_rule: str = Field(min_length=1, max_length=700)
    deload: bool
    sessions: list[ProgramSession] = Field(min_length=1)


class AIWorkoutProgram(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["3.0"]
    program_title: str = Field(min_length=1, max_length=180)
    program_summary: str = Field(min_length=1, max_length=1200)
    generated_exercises: list[GeneratedExercise]
    weeks: list[ProgramWeek] = Field(min_length=4, max_length=4)


@dataclass(frozen=True)
class GenerationProviderResult:
    output: AIWorkoutProgram
    provider: str
    model_id: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None


class WorkoutGenerationProvider(ABC):
    @abstractmethod
    async def generate(self, *, packet: dict[str, Any], repair_context: dict[str, Any] | None = None) -> GenerationProviderResult: ...


def build_generation_packet(state: PlannerInput, draft: PlanDraft) -> dict[str, Any]:
    """Build compact athlete, template, schedule and catalog context for one full-plan call."""
    candidate_catalog: dict[str, dict[str, Any]] = {}
    reference_sessions: list[dict[str, Any]] = []
    for session in draft.sessions:
        reference_slots: list[dict[str, Any]] = []
        for slot in session.slots:
            keys: list[str] = []
            for method in slot.candidates:
                key = f"{method.id}:{method.method_version}"
                keys.append(key)
                entry = candidate_catalog.setdefault(key, {
                    "method_id": str(method.id),
                    "method_version": method.method_version,
                    "name": method.name or method.code.replace("_", " ").title(),
                    "code": method.code,
                    "quality": method.quality,
                    "training_role": method.role,
                    "selection_tags": method.selection_tags,
                    "allowed_applications": [],
                })
                application = {
                    "block_type": slot.definition.block_type,
                    "quality": slot.definition.quality,
                    "training_role": slot.definition.role,
                    "dose_bounds": slot.definition.dose,
                }
                if application not in entry["allowed_applications"]:
                    entry["allowed_applications"].append(application)
            reference_slots.append({
                "block_type": slot.definition.block_type,
                "quality": slot.definition.quality,
                "training_role": slot.definition.role,
                "dose_bounds": slot.definition.dose,
                "template_context": slot.definition.metadata,
                "candidate_method_keys": keys,
            })
        reference_sessions.append({
            "scheduled_for": session.scheduled_for.isoformat(),
            "session_type": session.definition.session_type,
            "purpose": session.definition.purpose,
            "load_class": session.definition.load_class,
            "duration_minutes": session.definition.estimated_minutes,
            "template_context": session.definition.metadata,
            "reference_slots": reference_slots,
        })
    return {
        "schema_version": RESPONSE_SCHEMA_VERSION,
        "input_hash": draft.input_hash,
        "athlete_profile": {
            "level_rank": state.level_rank,
            "goal_code": state.goal_code,
            "primary_sport": state.primary_sport,
            "event_code": state.event_code,
            "role_code": state.role_code,
            "discipline_code": state.discipline_code,
            "format_code": state.format_code,
            "weight_class_code": state.weight_class_code,
            "target_date": state.target_date.isoformat() if state.target_date else None,
            "session_duration_minutes": state.maximum_session_minutes,
            "equipment": sorted(state.equipment),
            "environments": sorted(state.environments),
            "additional_context": state.athlete_context,
        },
        "reference_templates_and_schedule": reference_sessions,
        "candidate_catalog": candidate_catalog,
        "output_requirements": {
            "weeks": 4,
            "sessions_per_week": len(draft.sessions) // 4,
        },
    }


SYSTEM_PROMPT = """You are Runlete's expert running and strength-and-conditioning coach. Design one complete, individualized four-week running block from the supplied runner profile, event goal, ranked running requirements, reference templates, schedule, and exercise catalog.

Use this decision priority: (1) health restrictions and interruption history, (2) recent running volume and longest run, (3) available surfaces and equipment, (4) experience and technical ability, (5) scheduled days and per-day time ceiling, (6) target event, date and time, (7) fatigue and recovery, (8) reference-template guidance, and (9) purposeful variety.

When previous_four_week_block is present, use its adherence, completion, effort and pain summary to adjust the next block. Progress only when completion and recovery support it; hold or reduce load when adherence was low, effort was excessive, or pain was reported.

Templates are reviewed programming references. Analyze their structure, progression, dose boundaries and recovery distribution. Adapt and combine them when useful. They are not prose to copy and do not prevent you from adding a necessary running session, block or exercise. Create exactly four weeks and exactly the requested sessions per week. Preserve the supplied scheduled_for values. The supplied duration is a ceiling: a session may be shorter when appropriate, but its blocks must add up to its estimated duration. Build an integrated calendar of easy runs, long runs, intervals, threshold work, hills, sprint work, drills, mobility, strength, plyometrics and recovery as appropriate for this runner. Include a purposeful warm-up and cooldown in demanding sessions; do not add meaningless filler.

Prefer suitable catalog exercises and reference them with the exact supplied method_id and method_version. Use a catalog exercise only for a block, quality, role and prescription represented in its allowed_applications; never repurpose it simply because it is available. Choose prescription values inside the corresponding dose_bounds. When no allowed application fits a necessary use, create a generated exercise instead. Never alter or invent a catalog identifier. The backend attaches catalog instructions, cues, mistakes, safety and media after selection.

You may create as many exercises as the program genuinely needs when the supplied catalog misses a relevant movement, progression, regression, equipment variation or sport-specific method. Do not create a cosmetic rename or duplicate of a suitable catalog exercise. Define each new exercise once in generated_exercises, give it a stable generated_exercise_id, and reuse that ID in occurrences. Every generated exercise must include complete app-facing description, step-by-step instructions, coaching cues, common mistakes with corrections, safety information, contraindications, regressions and progressions.

Provide a complete prescription for every occurrence: sets and reps, time or distance, intensity or effort, rest and tempo whenever applicable. Circuits must include rounds, order, work, transition and recovery timing. Do not place maximal, highly technical or high-impact work in fatigue circuits. Progress the plan coherently across four weeks and manage repeated movement patterns, high-impact exposure and recovery.

Do not diagnose, treat, prescribe rehabilitation or guarantee outcomes. Return only data matching the response schema. Do not provide chain-of-thought."""


class OpenAIWorkoutGenerationProvider(WorkoutGenerationProvider):
    async def generate(self, *, packet: dict[str, Any], repair_context: dict[str, Any] | None = None) -> GenerationProviderResult:
        settings = get_settings()
        started = perf_counter()
        task = "Create the complete four-week program."
        if repair_context:
            task = "Repair the identified issues while preserving all valid program content. Return the complete corrected program."
        response = await create_structured_response(
            model=settings.openai_workout_model,
            system=SYSTEM_PROMPT,
            user_content=(
                f"TASK:{task}\n"
                f"INPUT_PACKAGE:{json.dumps(packet, sort_keys=True, separators=(',', ':'))}\n"
                f"REPAIR_CONTEXT:{json.dumps(repair_context, sort_keys=True, separators=(',', ':')) if repair_context else 'null'}"
            ),
            schema_name="runlete_four_week_workout_program",
            schema=AIWorkoutProgram.model_json_schema(),
            strict=False,
            max_output_tokens=16_000,
            timeout_seconds=300.0,
        )
        output = AIWorkoutProgram.model_validate_json(response.text)
        return GenerationProviderResult(output, "openai", response.model, int((perf_counter() - started) * 1000), response.input_tokens, response.output_tokens)


def get_workout_generation_provider() -> WorkoutGenerationProvider:
    return OpenAIWorkoutGenerationProvider()

# Compatibility aliases for existing tests and imports during the architecture migration.
build_selection_packet = build_generation_packet
get_workout_selection_provider = get_workout_generation_provider

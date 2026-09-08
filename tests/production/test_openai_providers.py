from __future__ import annotations

import json
import asyncio
from uuid import uuid4

from backend.app.core.openai_responses import StructuredResponse
from backend.app.nutrition.provider import OpenAIFoodAnalysisProvider
from backend.app.training.ai_selector import OpenAIWorkoutGenerationProvider


def test_openai_workout_provider_parses_catalog_and_generated_exercises(monkeypatch) -> None:
    method_id = uuid4()

    async def fake_response(**kwargs):
        assert kwargs["model"]
        assert kwargs["schema_name"] == "runlete_four_week_workout_program"
        session = {
            "week_number": 1, "session_number": 1, "scheduled_for": "2026-09-14T07:00:00+00:00",
            "title": "Strength", "purpose": "Build strength", "load_class": "moderate", "estimated_minutes": 90,
            "blocks": [{"block_type": "warmup", "title": "Warm-up", "purpose": "Prepare", "estimated_minutes": 90,
                "exercises": [{"exercise": {"source": "catalog", "method_id": str(method_id), "method_version": 1},
                    "prescription": {"sets": 3, "reps": 5}, "estimated_minutes": 90, "coaching_note": ""}]}],
        }
        return StructuredResponse(
            text=json.dumps(
                {
                    "schema_version": "3.0", "program_title": "Test", "program_summary": "Test plan",
                    "generated_exercises": [],
                    "weeks": [{"week_number": week, "theme": "Build", "progression_rule": "Progress", "deload": False,
                               "sessions": [{**session, "week_number": week}]} for week in range(1, 5)],
                }
            ),
            model="gpt-4o",
            input_tokens=100,
            output_tokens=40,
        )

    monkeypatch.setattr("backend.app.training.ai_selector.create_structured_response", fake_response)
    result = asyncio.run(OpenAIWorkoutGenerationProvider().generate(packet={}))
    assert result.provider == "openai"
    assert result.output.weeks[0].sessions[0].blocks[0].block_type == "warmup"
    assert result.output.weeks[0].sessions[0].blocks[0].exercises[0].exercise.method_id == method_id
    assert result.input_tokens == 100


def test_openai_food_provider_uses_image_and_validates_ranges(monkeypatch) -> None:
    async def fake_response(**kwargs):
        image = kwargs["user_content"][1]
        assert image["type"] == "input_image"
        assert image["detail"] == "high"
        assert image["image_url"].startswith("data:image/jpeg;base64,")
        return StructuredResponse(
            text=json.dumps(
                {
                    "candidates": [
                        {
                            "name": "Oats",
                            "portion_description": "One medium bowl",
                            "confidence": 0.8,
                            "calories": {"minimum": 250, "likely": 320, "maximum": 420, "unit": "kcal"},
                            "protein": {"minimum": 8, "likely": 12, "maximum": 18, "unit": "g"},
                            "carbohydrate": {"minimum": 40, "likely": 55, "maximum": 72, "unit": "g"},
                            "fat": {"minimum": 5, "likely": 9, "maximum": 15, "unit": "g"},
                            "fibre": {"minimum": 5, "likely": 8, "maximum": 12, "unit": "g"},
                        }
                    ],
                    "overall_confidence": 0.8,
                    "needs_user_review": True,
                }
            ),
            model="gpt-4o",
            input_tokens=200,
            output_tokens=100,
        )

    monkeypatch.setattr("backend.app.nutrition.provider.create_structured_response", fake_response)
    result = asyncio.run(
        OpenAIFoodAnalysisProvider().analyze(
            image_bytes=b"jpeg",
            content_type="image/jpeg",
            content_hash="a" * 64,
        )
    )
    assert result.result.candidates[0].fibre.likely == 8
    assert result.result.needs_user_review is True

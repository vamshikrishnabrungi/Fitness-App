from __future__ import annotations

import json
import asyncio
from uuid import uuid4

from backend.app.core.openai_responses import StructuredResponse
from backend.app.nutrition.provider import OpenAIFoodAnalysisProvider
from backend.app.training.ai_selector import OpenAIWorkoutSelectionProvider


def test_openai_workout_provider_parses_only_structured_ids(monkeypatch) -> None:
    slot_id = uuid4()
    method_id = uuid4()

    async def fake_response(**kwargs):
        assert kwargs["model"]
        assert kwargs["schema_name"] == "runlete_workout_selection"
        return StructuredResponse(
            text=json.dumps(
                {
                    "schema_version": "1.0",
                    "selections": [
                        {
                            "occurrence_id": "w1-s1-a",
                            "slot_id": str(slot_id),
                            "method_id": str(method_id),
                            "prescription": {"sets": 3, "repetitions": 5},
                            "alternative_method_ids": [],
                            "rationale_code": "objective_fit",
                        }
                    ],
                }
            ),
            model="gpt-4o",
            input_tokens=100,
            output_tokens=40,
        )

    monkeypatch.setattr("backend.app.training.ai_selector.create_structured_response", fake_response)
    result = asyncio.run(OpenAIWorkoutSelectionProvider().select(packet={"sessions": []}))
    assert result.provider == "openai"
    assert result.output.selections[0].method_id == method_id
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

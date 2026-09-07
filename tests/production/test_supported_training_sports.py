from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.athletes.schemas import SportInput
from backend.app.knowledge.sports import SUPPORTED_TRAINING_SPORTS


EXPECTED_SPORTS = {
    "badminton",
    "basketball",
    "boxing",
    "cricket",
    "cycling",
    "football",
    "mma",
    "running",
    "swimming",
    "tennis",
    "volleyball",
}


def test_supported_sports_match_committed_training_dataset() -> None:
    assert SUPPORTED_TRAINING_SPORTS == EXPECTED_SPORTS


def test_sport_input_normalizes_supported_code() -> None:
    assert SportInput(sport_code=" Running ", event_code="5k").sport_code == "running"


def test_sport_input_rejects_unbacked_sport() -> None:
    with pytest.raises(ValidationError, match="not supported by the training dataset"):
        SportInput(sport_code="Hockey")

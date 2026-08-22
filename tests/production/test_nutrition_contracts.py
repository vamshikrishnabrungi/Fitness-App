from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.nutrition.models import Meal
from backend.app.nutrition.schemas import MealConfirm


def test_confirmed_meal_requires_a_closed_meal_type() -> None:
    command = MealConfirm(
        eaten_at=datetime(2026, 8, 9, 8, tzinfo=timezone.utc),
        meal_type="breakfast",
        name="Oats and fruit",
        calories_kcal=420,
        protein_g=18,
        carbohydrate_g=68,
        fat_g=9,
        fibre_g=11,
    )
    assert command.meal_type == "breakfast"


def test_confirmed_meal_rejects_unknown_meal_type() -> None:
    with pytest.raises(ValidationError):
        MealConfirm(
            eaten_at=datetime(2026, 8, 9, 8, tzinfo=timezone.utc),
            meal_type="post_training",
            name="Meal",
            calories_kcal=200,
            protein_g=10,
            carbohydrate_g=20,
            fat_g=5,
        )


def test_meal_type_is_part_of_the_relational_model() -> None:
    assert Meal.__table__.c.meal_type.nullable is False
    assert Meal.__table__.c.meal_type.type.length == 16

from backend.app.athletes.schemas import GoalInput
from backend.app.training.reference_service import _generation_goal_code, _reference_event_code


def test_product_goal_is_preserved_by_onboarding_contract() -> None:
    goal = GoalInput(goal_type="target_race", target_event="100m")

    assert goal.goal_type == "target_race"


def test_sprint_race_uses_speed_priority_family() -> None:
    assert _generation_goal_code("target_race", "100m") == "speed_movement"
    assert _generation_goal_code("target_race", "mile") == "speed_movement"


def test_road_race_and_distance_goal_use_conditioning_family() -> None:
    assert _generation_goal_code("target_race", "10k") == "conditioning"
    assert _generation_goal_code("build_endurance", "half_marathon") == "conditioning"


def test_consistency_keeps_general_intent_and_uses_reviewed_5k_reference() -> None:
    assert _reference_event_code("general_running") == "5k"
    assert _generation_goal_code("start_running", "general_running") == "conditioning"

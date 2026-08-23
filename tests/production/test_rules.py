import pytest

from backend.app.training.rules import RuleEvaluationError, validate_rule_definition


def test_closed_rule_dsl_requires_bounded_clamp() -> None:
    validate_rule_definition(
        {"all": [{"field": "athlete.level", "op": "eq", "value": "beginner"}]},
        [{"type": "clamp", "target": "dose.sets", "value": {"minimum": 2, "maximum": 3}}],
    )
    with pytest.raises(RuleEvaluationError):
        validate_rule_definition(
            {"field": "athlete.level", "op": "execute_python", "value": "beginner"},
            [{"type": "set", "target": "dose.sets", "value": 3}],
        )
    with pytest.raises(RuleEvaluationError):
        validate_rule_definition(
            {"field": "athlete.level", "op": "eq", "value": "beginner"},
            [{"type": "clamp", "target": "dose.sets", "value": {"minimum": 5, "maximum": 2}}],
        )

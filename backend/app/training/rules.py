from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ALLOWED_OPERATORS = {"eq", "ne", "lt", "lte", "gt", "gte", "in", "contains"}
ALLOWED_ACTIONS = {"set", "clamp", "multiply", "exclude", "require", "stop", "refer", "replace", "reschedule"}
ALLOWED_CONTEXT_ROOTS = {
    "athlete",
    "goal",
    "sport",
    "schedule",
    "equipment",
    "environment",
    "readiness",
    "pain",
    "program",
    "phase",
    "week",
    "session",
    "method",
    "competition",
    "external_load",
    "weather",
}
ALLOWED_ACTION_TARGET_ROOTS = {"program", "phase", "week", "session", "slot", "dose", "method", "generation"}


class RuleEvaluationError(ValueError):
    pass


def _resolve(context: dict[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def condition_matches(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    operator = condition.get("op")
    if operator not in ALLOWED_OPERATORS:
        raise RuleEvaluationError(f"unsupported operator: {operator}")
    actual, expected = _resolve(context, condition["field"]), condition.get("value")
    if operator == "eq": return actual == expected
    if operator == "ne": return actual != expected
    if operator == "lt": return actual is not None and actual < expected
    if operator == "lte": return actual is not None and actual <= expected
    if operator == "gt": return actual is not None and actual > expected
    if operator == "gte": return actual is not None and actual >= expected
    if operator == "in": return actual in expected
    if operator == "contains": return expected in (actual or [])
    return False


def _validate_path(path: Any, *, roots: set[str], label: str) -> None:
    if not isinstance(path, str) or not path or path.split(".", 1)[0] not in roots:
        raise RuleEvaluationError(f"{label} is not part of the registered rule context")


def rule_matches(expression: dict[str, Any], context: dict[str, Any]) -> bool:
    if "all" in expression:
        return all(rule_matches(item, context) for item in expression["all"])
    if "any" in expression:
        return any(rule_matches(item, context) for item in expression["any"])
    if "not" in expression:
        return not rule_matches(expression["not"], context)
    return condition_matches(expression, context)


def validate_actions(actions: list[dict[str, Any]]) -> None:
    for action in actions:
        if action.get("type") not in ALLOWED_ACTIONS:
            raise RuleEvaluationError(f"unsupported action: {action.get('type')}")
        if action["type"] in {"clamp", "multiply"} and not isinstance(action.get("value"), (int, float, dict)):
            raise RuleEvaluationError("numeric actions require bounded numeric values")


def validate_rule_definition(expression: dict[str, Any], actions: list[dict[str, Any]]) -> None:
    def visit(node: Any) -> None:
        if not isinstance(node, dict):
            raise RuleEvaluationError("rule conditions must be objects")
        boolean_keys = [key for key in ("all", "any", "not") if key in node]
        if boolean_keys:
            if len(boolean_keys) != 1:
                raise RuleEvaluationError("a condition node may contain only one boolean operator")
            key = boolean_keys[0]
            children = node[key] if key != "not" else [node[key]]
            if not isinstance(children, list) or not children:
                raise RuleEvaluationError(f"{key} requires at least one condition")
            for child in children:
                visit(child)
            return
        if node.get("op") not in ALLOWED_OPERATORS or not isinstance(node.get("field"), str):
            raise RuleEvaluationError("leaf conditions require a supported operator and field")
        _validate_path(node["field"], roots=ALLOWED_CONTEXT_ROOTS, label="condition field")
        if node["op"] == "in" and not isinstance(node.get("value"), (list, tuple, set)):
            raise RuleEvaluationError("the in operator requires a collection")

    visit(expression)
    if not actions:
        raise RuleEvaluationError("a rule requires at least one bounded action")
    validate_actions(actions)
    for action in actions:
        if action["type"] not in {"stop", "refer"}:
            _validate_path(action.get("target"), roots=ALLOWED_ACTION_TARGET_ROOTS, label="action target")
        if action["type"] == "clamp":
            value = action.get("value")
            if not isinstance(value, dict) or not isinstance(value.get("minimum"), (int, float)) or not isinstance(value.get("maximum"), (int, float)) or value["minimum"] > value["maximum"]:
                raise RuleEvaluationError("clamp actions require ordered minimum and maximum bounds")


@dataclass(frozen=True)
class RuleApplication:
    values: dict[str, Any]
    trace: tuple[dict[str, Any], ...]
    stopped: bool = False
    referral_required: bool = False


def apply_bounded_actions(
    values: dict[str, Any],
    rules: list[tuple[str, int, dict[str, Any], list[dict[str, Any]]]],
    context: dict[str, Any],
) -> RuleApplication:
    """Apply a closed subset of the rule DSL to a bounded value object.

    `values` is normally a slot dose schema.  Rules cannot introduce arbitrary
    executable behavior: they may stop/refer, or alter an existing bounded field.
    """
    result = dict(values)
    trace: list[dict[str, Any]] = []
    stopped = False
    referral = False
    for code, version, conditions, actions in sorted(rules, key=lambda item: (item[0], item[1])):
        validate_rule_definition(conditions, actions)
        if not rule_matches(conditions, context):
            continue
        for action in actions:
            action_type = action["type"]
            if action_type == "stop":
                stopped = True
            elif action_type == "refer":
                referral = True
            else:
                target = action.get("target", "")
                if not target.startswith("dose."):
                    # Other targets are consumed by their owning deterministic stage.
                    continue
                field = target.split(".", 1)[1]
                if field not in result:
                    raise RuleEvaluationError(f"rule {code} targets an unavailable dose field")
                current = result[field]
                if action_type == "set":
                    result[field] = action["value"]
                elif action_type == "clamp":
                    if not isinstance(current, dict):
                        raise RuleEvaluationError(f"rule {code} cannot clamp a non-range dose")
                    lower = max(current.get("minimum", current.get("min")), action["value"]["minimum"])
                    upper = min(current.get("maximum", current.get("max")), action["value"]["maximum"])
                    if lower > upper:
                        raise RuleEvaluationError(f"rule {code} produced an empty dose range")
                    result[field] = {**current, "minimum": lower, "maximum": upper}
                elif action_type == "multiply":
                    factor = action["value"]
                    if not isinstance(current, dict) or not isinstance(factor, (int, float)):
                        raise RuleEvaluationError(f"rule {code} cannot multiply this dose")
                    updated = dict(current)
                    for bound in ("minimum", "maximum", "min", "max"):
                        if bound in updated:
                            updated[bound] = updated[bound] * factor
                    result[field] = updated
        trace.append({"rule_code": code, "rule_version": version, "actions": [action["type"] for action in actions]})
    return RuleApplication(result, tuple(trace), stopped, referral)

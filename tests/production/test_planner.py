from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest

from backend.app.training.ai_selector import AIWorkoutProgram, build_generation_packet
from backend.app.training.models import SessionItem
from backend.app.training.planner import (
    CandidateMethod,
    MethodSelection,
    PlannerInput,
    SessionDefinition,
    SlotDefinition,
    PlanInvariantError,
    finalize_plan,
    prepare_plan,
)


def state(**changes):
    data = dict(
        athlete_id=uuid4(),
        level_rank=2,
        goal_code="5k",
        primary_sport="running",
        event_code="5k",
        role_code=None,
        target_date=None,
        available_slots=((0, 1080, 60), (2, 1080, 60), (5, 600, 90)),
        equipment=frozenset(),
        environments=frozenset({"road", "home"}),
        maximum_session_minutes=90,
        external_hard_days=frozenset(),
        pain_flag=False,
        content_release_id=uuid4(),
        starts_on=date(2026, 8, 10),
    )
    data.update(changes)
    return PlannerInput(**data)


def fixtures():
    slot = SlotDefinition(
        uuid4(),
        "easy_run",
        "aerobic_capacity",
        "primary",
        "main_work",
        {"duration_minutes": {"minimum": 25, "maximum": 35, "step": 5}},
    )
    recipe = SessionDefinition(uuid4(), "endurance", "Build aerobic capacity", "easy", 45, (slot,))
    method = CandidateMethod(
        uuid4(),
        "easy_continuous_run",
        "aerobic_capacity",
        "primary",
        frozenset(),
        frozenset({"road"}),
        1,
        1,
        1,
        2,
        frozenset({"duration_minutes"}),
    )
    return recipe, method


def valid_selections(draft, method):
    return [
        MethodSelection(
            occurrence_id=slot.occurrence_id,
            slot_id=slot.definition.id,
            method_id=method.id,
            prescription={"duration_minutes": 30},
            alternative_method_ids=(),
            rationale_code="objective_fit",
        )
        for session in draft.sessions
        for slot in session.slots
    ]


def test_candidate_packet_is_deterministic_and_contains_only_eligible_ids():
    recipe, method = fixtures()
    inputs = state(equipment=frozenset({"dumbbells", "bodyweight"}))
    one = prepare_plan(inputs, [recipe], [method], weeks=4)
    two = prepare_plan(inputs, [recipe], [method], weeks=4)
    first_packet = build_generation_packet(inputs, one)
    assert one.input_hash == two.input_hash
    assert first_packet == build_generation_packet(inputs, two)
    assert first_packet["athlete_profile"]["equipment"] == ["bodyweight", "dumbbells"]
    assert first_packet["athlete_profile"]["environments"] == ["home", "road"]
    assert all(slot.candidates == (method,) for session in one.sessions for slot in session.slots)


def test_valid_ai_selection_is_finalized_inside_released_bounds():
    recipe, method = fixtures()
    draft = prepare_plan(state(), [recipe], [method], weeks=1)
    result = finalize_plan(draft, valid_selections(draft, method))
    assert result.sessions[0].items[0].method_id == method.id
    assert result.sessions[0].items[0].prescription == {"duration_minutes": 30}


def test_ai_can_create_a_bounded_circuit_from_eligible_main_work():
    recipe, method = fixtures()
    second_method = replace(method, id=uuid4(), code="tempo_run")
    second_slot = replace(recipe.slots[0], id=uuid4(), code="tempo_run")
    recipe = replace(recipe, slots=(recipe.slots[0], second_slot))
    draft = prepare_plan(state(), [recipe], [method, second_method], weeks=1)
    selections = []
    for order, (slot, selected_method) in enumerate(zip(draft.sessions[0].slots, (method, second_method)), 1):
        selections.append(MethodSelection(
            occurrence_id=slot.occurrence_id,
            slot_id=slot.definition.id,
            method_id=selected_method.id,
            prescription={"duration_minutes": 30},
            alternative_method_ids=(),
            rationale_code="objective_fit",
            circuit={
                "circuit_id": "conditioning-a",
                "order": order,
                "rounds": 4,
                "work_seconds": 40,
                "rest_seconds": 20,
                "rest_between_rounds_seconds": 60,
            },
        ))
    result = finalize_plan(draft, selections)
    assert result.sessions[0].items[0].prescription["circuit"] == selections[0].circuit


def test_ai_schema_rejects_unknown_fields():
    with pytest.raises(Exception):
        AIWorkoutProgram.model_validate({"schema_version": "3.0", "program_title": "x", "program_summary": "x", "generated_exercises": [], "weeks": [], "invented_field": True})


def test_catalog_session_item_none_is_bound_as_sql_null():
    column_type = SessionItem.__table__.c.generated_exercise_json.type
    assert column_type.none_as_null is True


def test_out_of_range_ai_dose_fails_closed():
    recipe, method = fixtures()
    draft = prepare_plan(state(), [recipe], [method], weeks=1)
    selection = valid_selections(draft, method)[0]
    invalid = MethodSelection(**{**selection.__dict__, "prescription": {"duration_minutes": 60}})
    with pytest.raises(PlanInvariantError):
        finalize_plan(draft, [invalid])


def test_invented_method_id_fails_closed():
    recipe, method = fixtures()
    draft = prepare_plan(state(), [recipe], [method], weeks=1)
    selection = valid_selections(draft, method)[0]
    invalid = MethodSelection(**{**selection.__dict__, "method_id": uuid4()})
    with pytest.raises(PlanInvariantError):
        finalize_plan(draft, [invalid])


def test_pain_fails_before_ai_packet_is_built():
    recipe, method = fixtures()
    with pytest.raises(PlanInvariantError):
        prepare_plan(state(pain_flag=True), [recipe], [method], weeks=4)


def test_missing_equipment_has_no_ai_fallback_invention():
    recipe, method = fixtures()
    unavailable = CandidateMethod(**{**method.__dict__, "equipment": frozenset({"treadmill"})})
    with pytest.raises(PlanInvariantError):
        prepare_plan(state(), [recipe], [unavailable], weeks=1)

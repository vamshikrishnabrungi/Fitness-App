from datetime import date, datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from uuid import UUID

import pytest

from backend.app.training.reference_compiler import (
    AvailabilitySlot,
    CompilerContext,
    PhasePolicy,
    PriorityContext,
    RankedCategory,
    ReferenceCompilationError,
    ReferenceMethod,
    ReferenceTemplate,
    ReferenceWeek,
    compile_program,
)
from backend.app.training.reference_prescription import normalize_reference_prescription
from backend.app.training.reference_service import _external_hard_dates


def _method(code: str, *, equipment=frozenset({"bodyweight"}), units=None) -> ReferenceMethod:
    return ReferenceMethod(
        method_id=UUID("00000000-0000-0000-0000-000000000001" if code == "squat" else "00000000-0000-0000-0000-000000000002"),
        method_version=1,
        code=code,
        name=code.replace("_", " ").title(),
        sequence=1,
        applicable_modes=frozenset({"all"}),
        equipment=equipment,
        environments=frozenset({"home", "gym"}),
        minimum_level="beginner",
        technical_cost=1,
        impact_cost=1,
        fatigue_cost=1,
        accepted_dose_units=units or frozenset({"sets", "repetitions", "rir", "recovery_seconds"}),
        safety_boundaries=("stop on pain",),
    )


def _template(code: str, category: str, method: ReferenceMethod, *, frequency="2", work="8") -> ReferenceTemplate:
    if work.endswith("min"):
        amount = int(work.removesuffix("min"))
        weekly_work = (work, f"{amount + 2}min", f"{amount + 4}min", f"{max(1, amount // 2)}min")
    else:
        amount = int(work)
        weekly_work = (work, str(amount + 1), str(amount + 2), str(max(1, amount - 2)))
    return ReferenceTemplate(
        template_id=UUID("10000000-0000-0000-0000-000000000001" if category == "maximum_strength" else "10000000-0000-0000-0000-000000000002"),
        template_version=1,
        code=code,
        category_code=category,
        purpose=f"Develop {category}",
        source_hash=code.lower(),
        methods=(method,),
        weeks=tuple(
            ReferenceWeek(
                week_number=index,
                sessions_per_week=frequency,
                intent=f"week {index}",
                prescription=normalize_reference_prescription({
                    "sets_or_series": 2,
                    "repetitions_distance_or_duration": weekly_work[index - 1],
                    "intensity": "RIR 3",
                    "recovery": "60s",
                }),
                progression_condition="quality remains acceptable",
                regression_condition="repeat when quality fails",
            )
            for index in range(1, 5)
        ),
        week_4_policy="Consolidation/deload by default.",
    )


def _context(**changes) -> CompilerContext:
    environments = changes.get("environments", frozenset({"home"}))
    equipment = changes.get("equipment", frozenset({"bodyweight"}))
    phase_code = changes.get("phase_code", "general_preparation")
    phase_policy = {
        "general_preparation": PhasePolicy(
            "general_preparation", 1, "development", 4, 2,
            (1.0, 1.0, 1.0, 1.0), "bounded_by_method_cost", "general",
        ),
        "specific_preparation": PhasePolicy(
            "specific_preparation", 1, "development", 4, 2,
            (1.0, 1.0, 1.0, 1.0), "low_cost_only", "specific",
        ),
        "competition": PhasePolicy(
            "competition", 1, "competition_taper", 3, 1,
            (0.75, 0.75, 0.5, 0.25), "familiar_only", "competition",
        ),
        "transition": PhasePolicy(
            "transition", 1, "maintain_week_1", 2, 1,
            (1.0, 1.0, 1.0, 0.5), "low_cost_only", "transition",
        ),
    }[phase_code]
    values = {
        "starts_on": date(2026, 8, 31),
        "athlete_level": "beginner",
        "primary_mode": "running",
        "availability": (
            AvailabilitySlot(0, 420, 60, environments),
            AvailabilitySlot(2, 420, 60, environments),
            AvailabilitySlot(4, 420, 60, environments),
        ),
        "equipment": equipment,
        "environments": environments,
        "equipment_by_environment": tuple(
            (environment, equipment) for environment in sorted(environments)
        ),
        "external_hard_days": frozenset(),
        "maximum_session_minutes": 60,
        "phase_policy": phase_policy,
        "phase_code": phase_code,
        "pain_unresolved": False,
    }
    values.update(changes)
    if "availability" in changes:
        values["availability"] = changes["availability"]
    if "equipment_by_environment" not in changes:
        values["equipment_by_environment"] = tuple(
            (environment, values["equipment"]) for environment in sorted(values["environments"])
        )
    return CompilerContext(**values)


def _priority() -> PriorityContext:
    return PriorityContext(
        primary_category="maximum_strength",
        block_order=("maximum_strength", "mobility_range_capacity"),
        ranked_categories=(
            RankedCategory("maximum_strength", 1, 1.0),
            RankedCategory("mobility_range_capacity", 2, 0.5),
        ),
        source_hash="priority",
    )


def test_compiler_is_deterministic_and_preserves_four_week_doses():
    templates = {
        "maximum_strength": (_template("strength", "maximum_strength", _method("squat")),),
        "mobility_range_capacity": (_template("mobility", "mobility_range_capacity", _method("mobility"), frequency="1"),),
    }
    first = compile_program(_context(), _priority(), templates, "dataset")
    second = compile_program(_context(), _priority(), templates, "dataset")
    assert first == second
    assert len(first.weeks) == 4
    assert [len(week.sessions) for week in first.weeks] == [2, 2, 2, 2]
    assert first.weeks[0].sessions[0].items[0].category_code == "maximum_strength"
    assert first.weeks[3].deload is True
    assert all(week.planned_load > 0 for week in first.weeks)
    assert first.weeks[3].planned_load < max(week.planned_load for week in first.weeks[:3])
    assert first.weeks[0].sessions[0].items[0].prescription["reference_source"]["sets_or_series"] == 2


def test_compiler_fails_closed_for_pain_and_missing_primary_equipment():
    template = _template("strength", "maximum_strength", _method("squat", equipment=frozenset({"barbell"})))
    with pytest.raises(ReferenceCompilationError, match="pain"):
        compile_program(_context(pain_unresolved=True), _priority(), {"maximum_strength": (template,)}, "dataset")
    with pytest.raises(ReferenceCompilationError, match="compatible"):
        compile_program(_context(), _priority(), {"maximum_strength": (template,)}, "dataset")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"acute_illness": True}, "acute illness"),
        ({"readiness": 1}, "very low readiness"),
    ],
)
def test_compiler_stops_for_acute_health_gates(changes, message):
    template = _template("strength", "maximum_strength", _method("squat"))
    with pytest.raises(ReferenceCompilationError, match=message):
        compile_program(_context(**changes), _priority(), {"maximum_strength": (template,)}, "dataset")


def test_low_readiness_retains_primary_and_removes_optional_volume():
    templates = {
        "maximum_strength": (_template("strength", "maximum_strength", _method("squat")),),
        "mobility_range_capacity": (
            _template("mobility", "mobility_range_capacity", _method("mobility"), frequency="1"),
        ),
    }
    normal = compile_program(_context(), _priority(), templates, "dataset")
    reduced = compile_program(
        _context(readiness=2, scenario_codes=frozenset({"high_fatigue_or_low_readiness"})),
        _priority(),
        templates,
        "dataset",
    )
    assert normal.selected[0].template.category_code == "maximum_strength"
    assert reduced.selected[0].template.category_code == "maximum_strength"
    assert len(reduced.selected) <= 2
    assert reduced.trace[0]["scenario_codes"] == ["high_fatigue_or_low_readiness"]
    assert reduced.selected[0].bound_doses[0]["sets"] == 1
    assert reduced.selected[0].bound_doses[0]["context_adjustment"]["policies"] == [
        "low_readiness_reduced_volume"
    ]


def test_competition_phase_caps_frequency_and_reduces_volume_without_changing_intensity():
    template = _template("strength", "maximum_strength", _method("squat"), frequency="2")
    result = compile_program(
        _context(
            phase_code="competition",
            method_familiarity=(("squat", "familiar"),),
            competition_dates=(date(2026, 9, 7),),
            days_to_competition=7,
        ),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    assert [len(week.sessions) for week in result.weeks] == [1, 1, 1, 1]
    assert [result.selected[0].bound_doses[index]["sets"] for index in range(4)] == [2, 2, 1, 1]
    assert all(
        dose["reference_source"]["repetitions_distance_or_duration"] == "8"
        for dose in result.selected[0].bound_doses
    )
    assert result.selected[0].bound_doses[0]["rir"] == {"minimum": 3.0, "maximum": 3.0}
    assert result.selected[0].bound_doses[0]["context_adjustment"]["policies"] == [
        "competition_phase_volume_policy_v1"
    ]
    assert result.weeks[0].intent.startswith("competition phase:")


def test_incompatible_primary_uses_next_ranked_compatible_category():
    primary = _template(
        "strength",
        "maximum_strength",
        _method("barbell_squat", equipment=frozenset({"barbell"})),
    )
    next_ranked = _template(
        "mobility",
        "mobility_range_capacity",
        _method("mobility"),
        frequency="1",
    )
    result = compile_program(
        _context(goal_code="strength_power"),
        _priority(),
        {"maximum_strength": (primary,), "mobility_range_capacity": (next_ranked,)},
        "dataset",
    )
    assert result.selected[0].template.category_code == "mobility_range_capacity"
    assert result.trace[1]["primary_skipped"] is True
    assert result.trace[1]["selection_strategy"] == "first_ranked_compatible_category"


def test_unbindable_primary_method_is_not_guessed():
    duration_only = _method(
        "passive_rest",
        units=frozenset({"sets", "duration_seconds", "recovery_seconds"}),
    )
    template = _template("bad", "maximum_strength", duration_only)
    with pytest.raises(ReferenceCompilationError, match="compatible"):
        compile_program(_context(), _priority(), {"maximum_strength": (template,)}, "dataset")


def test_optional_low_priority_category_is_removed_when_session_is_too_long():
    primary = _template("strength", "maximum_strength", _method("squat"))
    optional = _template(
        "mobility",
        "mobility_range_capacity",
        _method("mobility", units=frozenset({"sets", "duration_seconds", "rir", "recovery_seconds"})),
        frequency="1",
        work="20min",
    )
    result = compile_program(
        _context(maximum_session_minutes=20),
        _priority(),
        {"maximum_strength": (primary,), "mobility_range_capacity": (optional,)},
        "dataset",
    )
    assert [item.template.category_code for item in result.selected] == ["maximum_strength"]


def test_hard_sessions_do_not_land_on_external_hard_days():
    hard_method = ReferenceMethod(
        **{
            **_method("squat").__dict__,
            "fatigue_cost": 5,
        }
    )
    result = compile_program(
        _context(external_hard_days=frozenset({0})),
        _priority(),
        {"maximum_strength": (_template("strength", "maximum_strength", hard_method),)},
        "dataset",
    )
    assert {session.weekday for session in result.weeks[0].sessions} == {2, 4}
    assert all(session.scheduling_demand == "high" for session in result.weeks[3].sessions)
    assert result.weeks[3].planned_load < result.weeks[2].planned_load


def test_hard_sessions_keep_a_clear_day_from_external_hard_load():
    hard_method = ReferenceMethod(**{**_method("squat").__dict__, "fatigue_cost": 5})
    result = compile_program(
        _context(
            availability=(
                AvailabilitySlot(1, 420, 60, frozenset({"home"})),
                AvailabilitySlot(2, 420, 60, frozenset({"home"})),
                AvailabilitySlot(4, 420, 60, frozenset({"home"})),
                AvailabilitySlot(6, 420, 60, frozenset({"home"})),
            ),
            external_hard_days=frozenset({0}),
        ),
        _priority(),
        {"maximum_strength": (_template("strength", "maximum_strength", hard_method),)},
        "dataset",
    )
    assert {session.weekday for session in result.weeks[0].sessions} == {2, 4}


def test_one_time_external_load_only_changes_the_affected_week():
    hard_method = ReferenceMethod(**{**_method("squat").__dict__, "fatigue_cost": 5})
    result = compile_program(
        _context(
            availability=(
                AvailabilitySlot(0, 420, 60, frozenset({"home"})),
                AvailabilitySlot(2, 420, 60, frozenset({"home"})),
                AvailabilitySlot(4, 420, 60, frozenset({"home"})),
                AvailabilitySlot(6, 420, 60, frozenset({"home"})),
            ),
            external_hard_dates=frozenset({date(2026, 9, 9)}),
        ),
        _priority(),
        {"maximum_strength": (_template("strength", "maximum_strength", hard_method),)},
        "dataset",
    )
    assert {session.weekday for session in result.weeks[0].sessions} == {0, 2}
    assert {session.weekday for session in result.weeks[1].sessions} == {0, 4}


def test_actual_power_categories_have_high_scheduling_demand():
    template = _template("power", "vertical_power", _method("squat"))
    priority = PriorityContext(
        primary_category="vertical_power",
        block_order=("vertical_power",),
        ranked_categories=(RankedCategory("vertical_power", 1, 1.0),),
        source_hash="priority",
    )
    result = compile_program(_context(), priority, {"vertical_power": (template,)}, "dataset")
    assert all(session.scheduling_demand == "high" for week in result.weeks for session in week.sessions)


def test_external_load_recurrence_is_explicit_and_bounded():
    rows = (
        SimpleNamespace(
            intensity="hard",
            starts_at=datetime(2026, 8, 3, 18, tzinfo=timezone.utc),
            recurrence_json={"frequency": "weekly", "until": "2026-09-21"},
        ),
        SimpleNamespace(
            intensity="hard",
            starts_at=datetime(2026, 9, 9, 18, tzinfo=timezone.utc),
            recurrence_json=None,
        ),
        SimpleNamespace(
            intensity="easy",
            starts_at=datetime(2026, 9, 10, 18, tzinfo=timezone.utc),
            recurrence_json=None,
        ),
    )
    dates = _external_hard_dates(rows, starts_on=date(2026, 9, 7), zone=ZoneInfo("UTC"))
    assert dates == frozenset({
        date(2026, 9, 7), date(2026, 9, 9), date(2026, 9, 14),
        date(2026, 9, 21),
    })


def test_unknown_external_load_recurrence_fails_closed():
    rows = (SimpleNamespace(
        intensity="hard",
        starts_at=datetime(2026, 9, 7, 18, tzinfo=timezone.utc),
        recurrence_json={"frequency": "daily"},
    ),)
    with pytest.raises(ReferenceCompilationError, match="frequency=weekly"):
        _external_hard_dates(rows, starts_on=date(2026, 9, 7), zone=ZoneInfo("UTC"))


def test_context_rules_choose_sprint_start_only_for_running_sprint_scope():
    standing = ReferenceMethod(**{
        **_method("standing_start").__dict__,
        "minimum_level": "intermediate",
        "sequence": 2,
    })
    three_point = ReferenceMethod(**{
        **_method("three_point_start").__dict__,
        "minimum_level": "advanced",
        "sequence": 1,
        "sport_codes": frozenset({"running"}),
        "scope_codes": frozenset({"100m", "200m", "400m"}),
    })
    template = ReferenceTemplate(
        **{
            **_template("acceleration", "maximum_strength", standing).__dict__,
            "methods": (three_point, standing),
        }
    )
    priority = _priority()
    running = compile_program(
        _context(athlete_level="advanced", sport_code="running", scope_code="100m"),
        priority,
        {"maximum_strength": (template,)},
        "dataset",
    )
    badminton = compile_program(
        _context(athlete_level="advanced", sport_code="badminton", scope_code="singles"),
        priority,
        {"maximum_strength": (template,)},
        "dataset",
    )
    assert running.selected[0].method.code == "three_point_start"
    assert badminton.selected[0].method.code == "standing_start"
    candidate_trace = next(row for row in badminton.trace if row["decision"] == "candidate_evaluation")
    rejected = next(
        method
        for category in candidate_trace["candidates"]
        for method in category.get("methods", [])
        if method["method_code"] == "three_point_start"
    )
    assert rejected["accepted"] is False
    assert rejected["reason_codes"] == ["sport_not_allowed", "scope_not_allowed"]


def test_reviewed_equipment_alternatives_do_not_require_every_option():
    goblet = ReferenceMethod(**{
        **_method("goblet_squat", equipment=frozenset({"dumbbells", "kettlebell"})).__dict__,
        "minimum_level": "intermediate",
    })
    template = _template("strength", "maximum_strength", goblet)
    result = compile_program(
        _context(
            athlete_level="intermediate",
            equipment=frozenset({"dumbbells"}),
        ),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    assert result.selected[0].method.code == "goblet_squat"


def test_full_gym_does_not_invent_a_partner_or_specialist_equipment():
    partner = _method("partner_drill", equipment=frozenset({"partner", "marked_area"}))
    template = _template("strength", "maximum_strength", partner)
    with pytest.raises(ReferenceCompilationError, match="compatible"):
        compile_program(
            _context(equipment=frozenset({"full_gym"}), environments=frozenset({"gym"})),
            _priority(),
            {"maximum_strength": (template,)},
            "dataset",
        )


def test_incompatible_venues_are_split_into_separate_sessions():
    gym_method = ReferenceMethod(**{
        **_method("squat").__dict__,
        "environments": frozenset({"gym"}),
    })
    pool_method = ReferenceMethod(**{
        **_method("pool_mobility").__dict__,
        "environments": frozenset({"pool"}),
    })
    context = _context(
        availability=(
            AvailabilitySlot(0, 420, 90, frozenset({"gym"})),
            AvailabilitySlot(1, 420, 90, frozenset({"pool"})),
            AvailabilitySlot(2, 420, 90, frozenset({"gym"})),
            AvailabilitySlot(3, 420, 90, frozenset({"pool"})),
        ),
        equipment=frozenset({"bodyweight"}),
        environments=frozenset({"gym", "pool"}),
        equipment_by_environment=(
            ("gym", frozenset({"bodyweight"})),
            ("pool", frozenset({"bodyweight"})),
        ),
    )
    result = compile_program(
        context,
        _priority(),
        {
            "maximum_strength": (_template("strength", "maximum_strength", gym_method, frequency="1"),),
            "mobility_range_capacity": (
                _template("pool", "mobility_range_capacity", pool_method, frequency="1"),
            ),
        },
        "dataset",
    )
    assert {session.venue_code for session in result.weeks[0].sessions} == {"gym", "pool"}


def test_competition_session_cap_removes_optional_mixed_venue_work():
    gym_method = ReferenceMethod(**{
        **_method("squat").__dict__,
        "environments": frozenset({"gym"}),
    })
    pool_method = ReferenceMethod(**{
        **_method("pool_mobility").__dict__,
        "environments": frozenset({"pool"}),
    })
    context = _context(
        phase_code="competition",
        days_to_competition=12,
        method_familiarity=(("squat", "familiar"), ("pool_mobility", "familiar")),
        availability=(
            AvailabilitySlot(0, 420, 90, frozenset({"gym"})),
            AvailabilitySlot(3, 420, 90, frozenset({"pool"})),
        ),
        equipment=frozenset({"bodyweight"}),
        environments=frozenset({"gym", "pool"}),
        equipment_by_environment=(
            ("gym", frozenset({"bodyweight"})),
            ("pool", frozenset({"bodyweight"})),
        ),
    )
    result = compile_program(
        context,
        _priority(),
        {
            "maximum_strength": (_template("strength", "maximum_strength", gym_method, frequency="1"),),
            "mobility_range_capacity": (_template("pool", "mobility_range_capacity", pool_method, frequency="1"),),
        },
        "dataset",
    )
    assert all(len(week.sessions) == 1 for week in result.weeks)
    assert {session.venue_code for week in result.weeks for session in week.sessions} == {"gym"}
    assert any(
        adjustment["category_code"] == "mobility_range_capacity"
        for trace in result.trace if trace["decision"] == "schedule_adjustments"
        for adjustment in trace["adjustments"]
    )
    assert all(
        all(session.venue_code in item.method.environments for item in result.selected if any(
            compiled.method_id == item.method.method_id for compiled in session.items
        ))
        for session in result.weeks[0].sessions
    )


def test_equipment_is_validated_at_the_scheduled_venue():
    method = ReferenceMethod(**{
        **_method("squat", equipment=frozenset({"barbell"})).__dict__,
        "environments": frozenset({"home", "gym"}),
    })
    context = _context(
        availability=(
            AvailabilitySlot(0, 420, 60, frozenset({"home"})),
            AvailabilitySlot(2, 420, 60, frozenset({"gym"})),
            AvailabilitySlot(4, 420, 60, frozenset({"gym"})),
        ),
        equipment=frozenset({"bodyweight", "barbell"}),
        environments=frozenset({"home", "gym"}),
        equipment_by_environment=(
            ("home", frozenset({"bodyweight"})),
            ("gym", frozenset({"bodyweight", "barbell"})),
        ),
    )
    result = compile_program(
        context,
        _priority(),
        {"maximum_strength": (_template("strength", "maximum_strength", method),)},
        "dataset",
    )
    assert all(session.venue_code == "gym" for week in result.weeks for session in week.sessions)


def test_unfamiliar_high_cost_method_is_rejected_near_competition():
    familiar = ReferenceMethod(**{
        **_method("squat").__dict__,
        "minimum_level": "intermediate",
        "sequence": 2,
    })
    unfamiliar = ReferenceMethod(**{
        **_method("advanced_jump").__dict__,
        "minimum_level": "advanced",
        "technical_cost": 5,
        "impact_cost": 5,
        "sequence": 1,
    })
    template = ReferenceTemplate(**{
        **_template("strength", "maximum_strength", familiar).__dict__,
        "methods": (unfamiliar, familiar),
    })
    result = compile_program(
        _context(
            athlete_level="advanced",
            days_to_competition=7,
            competition_dates=(date(2026, 9, 7),),
            method_familiarity=(("squat", "familiar"), ("advanced_jump", "unknown")),
        ),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    assert result.selected[0].method.code == "squat"
    candidate = result.trace[4]["candidates"][0]
    rejected = next(row for row in candidate["methods"] if row["method_code"] == "advanced_jump")
    assert "unfamiliar_high_cost_method_near_competition" in rejected["reason_codes"]


def test_transition_uses_entry_dose_and_lower_frequency_than_general_preparation():
    template = _template("strength", "maximum_strength", _method("squat"), frequency="2")
    general = compile_program(
        _context(phase_code="general_preparation"),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    transition = compile_program(
        _context(phase_code="transition"),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    assert [len(week.sessions) for week in general.weeks] == [2, 2, 2, 2]
    assert [len(week.sessions) for week in transition.weeks] == [1, 1, 1, 1]
    transition_repetitions = [
        transition.selected[0].bound_doses[index]["repetitions"]
        for index in range(4)
    ]
    assert len({str(value) for value in transition_repetitions[:3]}) == 1
    assert transition.selected[0].bound_doses[3]["sets"] < transition.selected[0].bound_doses[2]["sets"]
    assert transition.weeks[3].deload is True
    assert transition.weeks[3].planned_load < transition.weeks[2].planned_load


def test_cross_training_requires_consent_and_primary_mode_is_still_preferred():
    running = ReferenceMethod(**{
        **_method("run_intervals").__dict__,
        "applicable_modes": frozenset({"running"}),
        "sequence": 2,
    })
    cycling = ReferenceMethod(**{
        **_method("cycle_intervals").__dict__,
        "applicable_modes": frozenset({"cycling"}),
        "sequence": 1,
    })
    template = ReferenceTemplate(**{
        **_template("conditioning", "maximum_strength", running).__dict__,
        "methods": (cycling, running),
    })
    without_consent = compile_program(
        _context(primary_mode="running", cross_training_consent=False),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    with_consent = compile_program(
        _context(primary_mode="running", cross_training_consent=True),
        _priority(),
        {"maximum_strength": (template,)},
        "dataset",
    )
    assert without_consent.selected[0].method.code == "run_intervals"
    assert with_consent.selected[0].method.code == "run_intervals"
    cross_training_only = ReferenceTemplate(**{**template.__dict__, "methods": (cycling,)})
    with pytest.raises(ReferenceCompilationError, match="compatible"):
        compile_program(
            _context(primary_mode="running", cross_training_consent=False),
            _priority(),
            {"maximum_strength": (cross_training_only,)},
            "dataset",
        )
    opted_in = compile_program(
        _context(primary_mode="running", cross_training_consent=True),
        _priority(),
        {"maximum_strength": (cross_training_only,)},
        "dataset",
    )
    assert opted_in.selected[0].method.code == "cycle_intervals"

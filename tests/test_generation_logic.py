"""Tests for the workout-generation logic hardened in the validator/continuation/hybrid-macro work.

Pure-function coverage (no DB, no AI calls): tiered/strict/off validator behavior + auto-repair,
hybrid-macro phase-merge invariants, and the athlete-state / previous-block summarizers.
"""
from __future__ import annotations

import pytest

import backend.server as server
from backend.ai_workout_service import validate_program_quality, _extract_duration_text, _looks_time_based
from backend.knowledge_retrieval import _compact_protocol, _merge_dedup_interleave, _semantic_hard_filter
from backend.macro_plan_service import _merge_tuned_phases
from backend.seed_training_protocols import PROTOCOLS
from backend.models import (
    ProgramBlockPlan,
    ProgramExercisePrescription,
    ProgramGenerationOutput,
    ProgramWeekPlan,
    ProgramWorkoutPrescription,
)

PROFILE = {
    "sports": ["Cricket"],
    "training_days_per_week": 2,
    "session_duration_min": 60,
    "preferred_training_days": ["Monday", "Thursday"],
}


def _ex(name="Barbell Back Squat", purpose="Build maximal lower-body strength for sprint acceleration", sets=4, reps="5"):
    return ProgramExercisePrescription(name=name, purpose=purpose, sets=sets, reps=reps)


def _workout(title="Lower Strength", why="Develop acceleration and landing strength for cricket fielding today", day="Monday", dur=60, main=True):
    return ProgramWorkoutPrescription(
        day=day, title=title, category="Strength", duration_min=dur, intensity="hard",
        adaptation_targets=["strength"], sport_transfer=["acceleration", "landing"], why_this_session=why,
        warmup=[_ex("Leg Swings", "Prime hips for squatting and sprint mechanics", None, None)],
        main_work=[_ex()] if main else [],
        cooldown=[_ex("Couch Stretch", "Restore hip flexor length after the session", None, None)],
        injury_modifications=["Reduce depth if knee pain"],
    )


def _program(workouts):
    return ProgramGenerationOutput(
        title="Cricket Power Block", goal="Power", sports=["Cricket"], duration_weeks=1,
        athlete_analysis={"summary": "x"},
        blocks=[ProgramBlockPlan(name="Base", start_week=1, end_week=1, emphasis=["strength"])],
        weeks=[ProgramWeekPlan(week_number=1, theme="Base", progression_rule="add load", workouts=workouts)],
        recovery_focus=["sleep"], safety_notes=["warm up"],
    )


# --------------------------- validator: tiered ---------------------------

def test_tiered_accepts_weak_why_this_session(monkeypatch):
    """The exact failure that used to 503 onboarding now passes."""
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "tiered")
    p = _program([
        _workout(why="Develop base strength and general work capacity for the weeks ahead", day="Monday"),
        _workout(title="Upper", why="Develop pressing and pulling strength with controlled tempo and range", day="Thursday"),
    ])
    assert validate_program_quality(p, PROFILE) is p


def test_tiered_rejects_missing_main_work(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "tiered")
    p = _program([_workout(day="Monday"), _workout(title="Empty", day="Thursday", main=False)])
    with pytest.raises(ValueError):
        validate_program_quality(p, PROFILE)


def test_tiered_rejects_wrong_session_count(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "tiered")
    p = _program([_workout(day="Monday")])  # 1 workout vs requested 2
    with pytest.raises(ValueError):
        validate_program_quality(p, PROFILE)


def test_tiered_clamps_over_cap_duration(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "tiered")
    monkeypatch.setenv("WORKOUT_AI_MAX_SESSION_MIN", "150")
    p = _program([_workout(day="Monday", dur=240), _workout(title="Upper", day="Thursday", dur=120)])
    out = validate_program_quality(p, PROFILE)
    assert out.weeks[0].workouts[0].duration_min == 150  # clamped, not rejected
    assert out.weeks[0].workouts[1].duration_min == 120  # under cap untouched


def test_tiered_autorepairs_missing_defaults(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "tiered")
    w1 = _workout(day="Monday")
    w1.why_this_session = ""
    w1.injury_modifications = []
    w1.main_work[0].purpose = ""
    p = _program([w1, _workout(title="Upper", day="Thursday")])
    p.recovery_focus = []
    p.safety_notes = []
    prof = {**PROFILE, "pain_areas": ["knee"]}
    out = validate_program_quality(p, prof)
    assert out.recovery_focus and out.safety_notes
    assert out.weeks[0].workouts[0].why_this_session
    assert out.weeks[0].workouts[0].injury_modifications
    assert out.weeks[0].workouts[0].main_work[0].purpose


# --------------------------- validator: strict / off ---------------------------

def test_validator_repairs_time_based_exercise_duration(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "tiered")
    plank = ProgramExercisePrescription(name="RKC Plank", purpose="Build trunk stiffness for court contact", sets=3)
    assert not plank.reps and not plank.duration
    w1 = _workout(day="Monday")
    w1.main_work.append(plank)
    validate_program_quality(_program([w1, _workout(title="Upper", day="Thursday")]), PROFILE)
    assert plank.duration  # "3 x None" defect repaired with a hold time


def test_extract_duration_and_time_based_detection():
    ex = ProgramExercisePrescription(name="Plank", purpose="trunk stability", load_guidance="hold for 30-45 sec, brace hard")
    assert _extract_duration_text(ex) is not None
    assert _looks_time_based("RKC Plank", "Strength") is True
    assert _looks_time_based("Barbell Bench Press", "Strength") is False


def test_score_program_rubric():
    workouts = [{
        "adaptation": {"why_this_session": "assess pain and knee LSI baseline", "injury_modifications": ["pain-free range"]},
        "description": "monitor 24h knee response",
        "session_plan": {
            "warmup": [{"name": "Leg Swings", "duration": "30 sec"}],
            "main_work": [
                {"name": "Spanish Squat", "sets": 5, "duration": "45 sec",
                 "purpose": "isometric hold, slow tempo tendon loading", "knowledge_ref": {"exercise_id": "ex_spanish"}},
                {"name": "Box Squat", "sets": 3, "reps": "6", "rpe": "RPE 7", "knowledge_ref": {"exercise_id": "ex_box"}},
            ],
            "cooldown": [{"name": "Calf Stretch", "duration": "30 sec"}],
        },
    }]
    profile = {"pain_areas": ["knee"], "season_phase": "re_entry"}
    kc = {"training_protocols": [{"key_rules": ["Use isometric holds with slow tempo"],
                                  "recommended_exercises": ["Spanish Squat"]}]}
    r = server._score_program_rubric(workouts, profile, kc, {"grounding_rate": 1.0})
    assert 0 <= r["overall"] <= 100
    d = r["dimensions"]
    assert d["grounding"] == 100
    assert d["protocol_adherence"] == 100      # program followed the protocol's method (isometric/tempo)
    assert d["monitoring_testing"] == 100      # LSI / monitor referenced
    assert d["exercise_completeness"] == 100   # all have reps or duration
    assert d["load_anchoring"] == 100          # only Box Squat is rep-based; it has RPE


def test_strict_blocks_weak_why(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "strict")
    p = _program([
        _workout(why="Develop base strength and general work capacity for the weeks ahead", day="Monday"),
        _workout(title="Upper", why="Develop pressing and pulling strength with controlled tempo and range", day="Thursday"),
    ])
    with pytest.raises(ValueError):
        validate_program_quality(p, PROFILE)


def test_off_accepts_anything_with_weeks(monkeypatch):
    monkeypatch.setenv("WORKOUT_AI_VALIDATION_MODE", "off")
    p = _program([_workout(day="Monday", main=False)])  # would hard-reject in tiered
    assert validate_program_quality(p, PROFILE) is p


# --------------------------- hybrid macro: phase merge ---------------------------

ORIG_PHASES = [
    {"block": 1, "phase": "accumulation", "start_week": 1, "end_week": 4, "primary_goals": ["gpp"], "progression_logic": "add reps"},
    {"block": 2, "phase": "max_strength", "start_week": 5, "end_week": 8, "primary_goals": ["strength"], "progression_logic": "add load"},
]


def test_merge_valid_shifts_and_preserves_original_fields():
    tuned = [
        {"phase": "accumulation", "start_week": 1, "end_week": 5, "primary_goals": ["gpp2"], "emphasis": ["carries"], "tuning_reason": "beginner"},
        {"phase": "max_strength", "start_week": 6, "end_week": 8},
    ]
    merged = _merge_tuned_phases(ORIG_PHASES, tuned, 8)
    assert merged is not None
    assert merged[0]["end_week"] == 5 and merged[1]["start_week"] == 6
    assert merged[0]["emphasis"] == ["carries"]
    assert merged[0]["progression_logic"] == "add reps"  # original field preserved


def test_merge_rejects_wrong_count():
    assert _merge_tuned_phases(ORIG_PHASES, [{"phase": "accumulation", "start_week": 1, "end_week": 8}], 8) is None


def test_merge_rejects_renamed_phase():
    tuned = [{"phase": "accumulation", "start_week": 1, "end_week": 4}, {"phase": "POWER", "start_week": 5, "end_week": 8}]
    assert _merge_tuned_phases(ORIG_PHASES, tuned, 8) is None


def test_merge_rejects_noncontiguous():
    tuned = [{"phase": "accumulation", "start_week": 1, "end_week": 4}, {"phase": "max_strength", "start_week": 6, "end_week": 8}]
    assert _merge_tuned_phases(ORIG_PHASES, tuned, 8) is None


def test_merge_rejects_wrong_final_week():
    tuned = [{"phase": "accumulation", "start_week": 1, "end_week": 4}, {"phase": "max_strength", "start_week": 5, "end_week": 7}]
    assert _merge_tuned_phases(ORIG_PHASES, tuned, 8) is None


# --------------------------- athlete_state / continuation summarizers ---------------------------

def test_program_grounding_rate():
    workouts = [
        {"session_plan": {"main_work": [
            {"name": "A", "knowledge_ref": {"exercise_id": "pex_1"}},
            {"name": "B", "knowledge_ref": {"exercise_id": "pex_2"}},
            {"name": "C"},  # off-pool / ungrounded
        ]}},
        {"session_plan": {"main_work": [{"name": "D", "knowledge_ref": {"exercise_id": "pex_3"}}]}},
    ]
    g = server._program_grounding(workouts)
    assert g["total_main_exercises"] == 4
    assert g["grounded_main_exercises"] == 3
    assert g["grounding_rate"] == 0.75


def test_program_grounding_empty_is_none():
    assert server._program_grounding([])["grounding_rate"] is None


def test_estimate_1rm_epley():
    assert server._estimate_1rm(100, 1) == 100.0          # 1RM = the weight
    assert server._estimate_1rm(90, 5) == 105.0           # Epley: 90*(1+5/30)
    assert server._estimate_1rm(0, 5) is None
    assert server._estimate_1rm("x", 5) is None


def test_summarize_benchmarks_drops_empties():
    b = {"strength_1rm_kg": {"back squat": 100}, "cmj_cm": 45, "visa_p": None, "broad_jump_cm": None}
    s = server.summarize_benchmarks_for_ai(b)
    assert s["cmj_cm"] == 45 and s["strength_1rm_kg"] == {"back squat": 100}
    assert "visa_p" not in s and "broad_jump_cm" not in s
    assert server.summarize_benchmarks_for_ai(None) == {}


def test_rubric_load_anchoring_requires_percent_when_baseline_exists():
    base = {
        "adaptation": {"why_this_session": "strength work"},
        "session_plan": {
            "warmup": [{"name": "Prep", "duration": "5 min"}],
            "main_work": [{"name": "Back Squat", "sets": 4, "reps": "5", "load_guidance": "~78% of 1RM (78kg)",
                           "knowledge_ref": {"exercise_id": "ex_bs"}}],
            "cooldown": [{"name": "Stretch", "duration": "5 min"}],
        },
    }
    profile = {}
    # With a 1RM baseline, a %-referenced load scores full; a vague "moderate weight" would not.
    kc_with = {"benchmarks": {"strength_1rm_kg": {"back squat": 100}}}
    assert server._score_program_rubric([base], profile, kc_with, {"grounding_rate": 1.0})["dimensions"]["load_anchoring"] == 100
    vague = {**base, "session_plan": {**base["session_plan"],
             "main_work": [{"name": "Back Squat", "sets": 4, "reps": "5", "load_guidance": "moderate weight"}]}}
    assert server._score_program_rubric([vague], profile, kc_with, {"grounding_rate": 1.0})["dimensions"]["load_anchoring"] == 0


def test_summarize_athlete_state_none():
    assert server.summarize_athlete_state_for_ai(None) == {}


def test_summarize_athlete_state_shape_drops_extra():
    s = server.summarize_athlete_state_for_ai({
        "completion_rate_28d": 0.6, "average_rpe_14d": 8.3, "progression_signal": "hold_or_deload",
        "pain_trends": [{"area": "knee"}], "internal_only": "drop",
    })
    assert s["progression_signal"] == "hold_or_deload"
    assert s["average_rpe_14d"] == 8.3
    assert "internal_only" not in s


def test_strength_trends_load_progression():
    hist = [
        {"exercise_name": "Back Squat", "date": "2026-05-01", "load": "60 kg", "reps": "5", "sets": 3},
        {"exercise_name": "Back Squat", "date": "2026-06-01", "load": "80 kg", "reps": "5", "sets": 3},
        {"exercise_name": "Bench Press", "date": "2026-05-01", "load": "50 kg", "reps": "5", "sets": 3},
        {"exercise_name": "Bench Press", "date": "2026-06-01", "load": "50 kg", "reps": "5", "sets": 3},
    ]
    by_ex = {t["exercise"]: t for t in server._compute_strength_trends(hist)}
    assert by_ex["Back Squat"]["direction"] == "progressing"
    assert by_ex["Back Squat"]["metric"] == "load"
    assert by_ex["Bench Press"]["direction"] == "plateau"


def test_strength_trends_volume_fallback_for_bodyweight():
    hist = [
        {"exercise_name": "Push-Up", "date": "2026-05-01", "load": "bodyweight", "reps": "12", "sets": 3},
        {"exercise_name": "Push-Up", "date": "2026-06-01", "load": "bodyweight", "reps": "20", "sets": 3},
    ]
    t = server._compute_strength_trends(hist)[0]
    assert t["metric"] == "volume" and t["direction"] == "progressing"


def test_parse_load_value_ignores_non_numeric_loads():
    assert server._parse_load_value("60 kg") == 60.0
    assert server._parse_load_value("bodyweight") is None
    assert server._parse_load_value("RPE 7-8") is None
    assert server._parse_load_value("Use controlled reps in a pain-free range") is None


def test_merge_dedup_interleave_keeps_both_sources_first():
    keyword = [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]
    semantic = [{"id": "2", "name": "B"}, {"id": "3", "name": "C"}]  # 2 is a dup, 3 is a recall-rescue
    out = [d["id"] for d in _merge_dedup_interleave(keyword, semantic)]
    assert out == ["1", "2", "3"]           # interleaved + deduped, rescue (3) preserved near front


def test_semantic_hard_filter_gates_by_injury():
    injury = {"knee", "patellar"}
    assert not _semantic_hard_filter({"contraindications": ["knee pain"]}, injury, True)   # contraindicated
    assert not _semantic_hard_filter({"impact_level": "high"}, injury, True)               # impact + lower-limb injury
    assert _semantic_hard_filter({"name": "Goblet Squat", "impact_level": "low"}, injury, True)  # safe passes
    assert _semantic_hard_filter({"impact_level": "high"}, set(), False)                   # high impact ok when healthy


def test_protocol_seed_data_is_wellformed():
    ids = set()
    for p in PROTOCOLS:
        for field in ("id", "name", "category", "scope", "match", "stages"):
            assert p.get(field), f"protocol {p.get('id')} missing {field}"
        assert p["scope"] in ("condition", "general")
        assert isinstance(p["match"], dict)
        assert isinstance(p["stages"], list) and p["stages"]
        for stage in p["stages"]:
            assert stage.get("prescription"), f"{p['id']} stage missing prescription"
        assert p["id"] not in ids, "duplicate protocol id"
        ids.add(p["id"])


def test_compact_protocol_shape_and_truncation():
    doc = {
        "name": "Patellar Tendinopathy Loading Protocol", "category": "tendon_rehab",
        "summary": "x" * 500,
        "stages": [{"stage": "isometric", "when": "painful", "prescription": "hold 5x45s", "purpose": "analgesia"}] * 6,
        "key_rules": ["r1", "r2", "r3", "r4", "r5"],
        "recommended_exercises": ["Spanish Squat", "Box Squat"],
        "evidence_level": "high",
    }
    c = _compact_protocol(doc, ["injury", "goal"])
    assert c["name"] == "Patellar Tendinopathy Loading Protocol"
    assert c["applies_because"] == ["injury", "goal"]
    assert len(c["stages"]) <= 4          # truncated
    assert len(c["key_rules"]) <= 4       # truncated
    assert len(c["summary"]) < 500        # truncated
    assert c["evidence_level"] == "high"


def test_build_previous_block_summary_carries_feedback():
    program = {"title": "P", "goal": "Strength"}
    week = [{
        "title": "Lower", "category": "Strength", "duration": 60, "week_number": 1, "completed": True,
        "exercises": [{"name": "Squat"}, {"name": "RDL"}],
        "user_feedback": {"rpe": 8, "completion_percentage": 90, "pain_score": 2},
    }]
    s = server._build_previous_block_summary(program, week)
    assert s["completed_week_number"] == 1
    assert s["sessions"][0]["rpe"] == 8
    assert s["sessions"][0]["main_exercises"] == ["Squat", "RDL"]

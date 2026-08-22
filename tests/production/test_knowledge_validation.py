from uuid import uuid4
import pytest

from backend.app.knowledge.models import MethodEffect, MethodRelation, MethodVersion
from backend.app.knowledge.validation import KnowledgeValidationError, validate_method, validate_progression_dag


def method():
    return MethodVersion(method_id=uuid4(), content_version=1, canonical_name="Split Squat", method_type="exercise", movement_pattern="lunge", equipment_codes=[], environments=["home"], surfaces=[], accepted_dose_units=["repetitions"], force_directions=["vertical"], contractions=["concentric", "eccentric"], speed_intent="controlled", joint_positions={}, level_minimum="beginner", technical_cost=2, impact_cost=1, fatigue_cost=3, supervision_required=False, instructions=["Set a stable split stance."], cues=["Stay tall."], common_errors=["Front heel lifts."], safety_boundaries=["Stop for sharp pain."], wording_original=True, status="evidence_verified", generator_eligible=True)


def effect(primary=True, quality="unilateral_strength"):
    return MethodEffect(method_id=uuid4(), method_version=1, quality_code=quality, is_primary=primary, training_role="primary", magnitude=.8, confidence=.8, evidence_claim_id=uuid4(), evidence_claim_version=1)


def test_method_requires_one_primary_and_three_or_fewer_secondary_effects():
    validate_method(method(), [effect()])
    with pytest.raises(KnowledgeValidationError): validate_method(method(), [effect(False)])
    with pytest.raises(KnowledgeValidationError): validate_method(method(), [effect(), effect(False,"a"), effect(False,"b"), effect(False,"c"), effect(False,"d")])


def test_progression_graph_rejects_cycles():
    a, b, c = uuid4(), uuid4(), uuid4()
    rows = [MethodRelation(from_method_id=a, to_method_id=b, relation_type="progression", objective_code="squat", prerequisites_json={}, rationale="a"), MethodRelation(from_method_id=b, to_method_id=c, relation_type="progression", objective_code="squat", prerequisites_json={}, rationale="b"), MethodRelation(from_method_id=c, to_method_id=a, relation_type="progression", objective_code="squat", prerequisites_json={}, rationale="c")]
    with pytest.raises(KnowledgeValidationError): validate_progression_dag(rows)

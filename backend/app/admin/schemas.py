from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


Code = str
ContentStatus = Literal["draft", "evidence_verified", "released", "retired"]


class Page(BaseModel):
    items: list[dict[str, Any]]
    next_cursor: str | None = None


class MethodVersionDraft(BaseModel):
    canonical_name: str = Field(min_length=2, max_length=180)
    method_type: str = Field(min_length=2, max_length=30)
    movement_pattern: str = Field(min_length=2, max_length=50)
    equipment_codes: list[str] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    surfaces: list[str] = Field(default_factory=list)
    accepted_dose_units: list[str] = Field(min_length=1)
    force_directions: list[str] = Field(default_factory=list)
    contractions: list[str] = Field(default_factory=list)
    speed_intent: str = Field(min_length=2, max_length=24)
    joint_positions: dict[str, Any] = Field(default_factory=dict)
    level_minimum: str
    technical_cost: int = Field(ge=1, le=5)
    impact_cost: int = Field(ge=1, le=5)
    fatigue_cost: int = Field(ge=1, le=5)
    supervision_required: bool = False
    instructions: list[str] = Field(min_length=1)
    cues: list[str] = Field(min_length=1)
    common_errors: list[str] = Field(min_length=1)
    safety_boundaries: list[str] = Field(min_length=1)
    wording_original: bool = False


class MethodCreate(MethodVersionDraft):
    code: str = Field(pattern="^[a-z0-9_]+$", max_length=100)
    aliases: list[str] = Field(default_factory=list)


class MethodUpdate(MethodVersionDraft):
    expected_record_version: int = Field(ge=1)


class MethodAliasesUpdate(BaseModel):
    aliases: list[str] = Field(default_factory=list, max_length=30)
    expected_version: int = Field(ge=1)


class MethodArchiveCommand(BaseModel):
    archived: bool
    expected_version: int = Field(ge=1)


class AdminUserStatusUpdate(BaseModel):
    status: Literal["active", "suspended", "disabled"]
    expected_version: int = Field(ge=1)


class AdminClubStatusUpdate(BaseModel):
    status: Literal["active", "archived"]


class MethodIdentityView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    latest_version: int
    archived: bool
    version: int


class MethodView(MethodVersionDraft):
    id: UUID
    code: str
    content_version: int
    status: str
    generator_eligible: bool
    record_version: int
    identity_version: int
    archived: bool
    aliases: list[str] = Field(default_factory=list)


class EffectDraft(BaseModel):
    quality_code: str
    is_primary: bool = False
    training_role: Literal["preparation", "primary", "accessory", "capacity", "recovery"]
    magnitude: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_claim_id: UUID
    evidence_claim_version: int = Field(ge=1)


class ConstraintDraft(BaseModel):
    constraint_type: str
    code: str = Field(pattern="^[a-z0-9_]+$", max_length=80)
    condition_json: dict[str, Any] = Field(default_factory=dict)
    action: Literal["exclude", "modify", "stop", "refer", "require_supervision"]
    athlete_message: str = Field(min_length=5, max_length=1000)
    evidence_claim_id: UUID | None = None
    evidence_claim_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def evidence_pair(self):
        if (self.evidence_claim_id is None) != (self.evidence_claim_version is None):
            raise ValueError("evidence claim ID and version must be supplied together")
        return self


class RelationCreate(BaseModel):
    from_method_id: UUID
    to_method_id: UUID
    relation_type: Literal["progression", "substitution", "alternative"]
    objective_code: str
    prerequisites_json: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(min_length=5, max_length=3000)
    evidence_claim_id: UUID | None = None
    evidence_claim_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def evidence_pair(self):
        if (self.evidence_claim_id is None) != (self.evidence_claim_version is None):
            raise ValueError("evidence claim ID and version must be supplied together")
        return self


class RelationUpdate(RelationCreate):
    expected_version: int = Field(ge=1)


class MethodMediaDraft(BaseModel):
    media_type: Literal["image", "video", "animation"]
    bucket: str = Field(min_length=2, max_length=120)
    object_name: str = Field(min_length=2, max_length=500)
    content_hash: str = Field(pattern="^[0-9a-f]{64}$")
    ownership_status: Literal["owned", "licensed"]
    technical_review_status: Literal["pending", "approved", "rejected"] = "pending"


class EvidenceSourceDraft(BaseModel):
    title: str = Field(min_length=3, max_length=1000)
    canonical_locator: str = Field(min_length=3, max_length=2000)
    doi: str | None = Field(default=None, max_length=200)
    source_tier: int = Field(ge=1, le=5)
    publication_year: int | None = Field(default=None, ge=1800, le=2200)
    population: str | None = None
    context: str | None = None
    limitations: str | None = None


class EvidenceClaimDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=120)
    statement: str = Field(min_length=10, max_length=10000)
    claim_type: str = Field(min_length=2, max_length=40)
    implication_type: Literal["direct", "inferred", "practitioner_inference"]
    population: str | None = None
    context: str | None = None
    confidence: float = Field(ge=0, le=1)
    limitations: str | None = None
    source_ids: list[UUID] = Field(min_length=1)


class EvidenceClaimUpdate(EvidenceClaimDraft):
    expected_record_version: int = Field(ge=1)


class ReviewCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    entity_version: int = Field(ge=1)
    review_type: Literal["content", "evidence", "safety", "specialist"]
    decision: Literal["approved", "changes_required", "rejected"]
    rationale: str = Field(min_length=10, max_length=10000)
    scope: str = Field(min_length=3, max_length=2000)


class TermDraft(BaseModel):
    category: str = Field(pattern="^[a-z0-9_]+$", max_length=40)
    code: str = Field(pattern="^[a-z0-9_]+$", max_length=80)
    name: str = Field(min_length=2, max_length=140)
    description: str = Field(min_length=3, max_length=3000)


class TermUpdate(TermDraft):
    expected_version: int = Field(ge=1)


class PhysicalQualityDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_]+$", max_length=60)
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=3, max_length=3000)


class PhysicalQualityUpdate(PhysicalQualityDraft):
    expected_version: int = Field(ge=1)


class SportTaxonDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_]+$", max_length=80)
    name: str = Field(min_length=2, max_length=120)
    taxon_type: Literal["sport", "event", "role", "discipline", "format"]
    sport_code: str
    parent_id: UUID | None = None
    visible: bool = True


class SportTaxonUpdate(SportTaxonDraft):
    expected_version: int = Field(ge=1)


class DemandFactDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=120)
    sport_code: str
    event_code: str | None = None
    role_code: str | None = None
    discipline_code: str | None = None
    format_code: str | None = None
    weight_class_code: str | None = None
    competition_level: str | None = None
    phase_code: str | None = None
    dimension_code: str
    metric_code: str
    minimum_value: float | None = None
    maximum_value: float | None = None
    unit: str | None = None
    context: str = Field(min_length=5)
    implication_type: Literal["direct", "inferred", "practitioner_inference"]
    confidence: float = Field(ge=0, le=1)
    evidence_claim_id: UUID
    evidence_claim_version: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered_range(self):
        if self.minimum_value is not None and self.maximum_value is not None and self.minimum_value > self.maximum_value:
            raise ValueError("minimum_value cannot exceed maximum_value")
        return self


class DemandFactUpdate(DemandFactDraft):
    expected_record_version: int = Field(ge=1)


class QualityPriorityDraft(BaseModel):
    sport_code: str
    event_code: str | None = None
    role_code: str | None = None
    discipline_code: str | None = None
    format_code: str | None = None
    phase_code: str
    level_code: str | None = None
    quality_code: str
    priority_weight: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=5)
    evidence_claim_id: UUID
    evidence_claim_version: int = Field(ge=1)


class QualityPriorityUpdate(QualityPriorityDraft):
    expected_version: int = Field(ge=1)


class EvidenceReference(BaseModel):
    id: UUID
    version: int = Field(ge=1)


class RuleDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=100)
    scope: str = Field(min_length=2, max_length=40)
    sport_code: str | None = None
    priority: int = Field(default=100, ge=1, le=10000)
    conditions_json: dict[str, Any]
    actions_json: list[dict[str, Any]] = Field(min_length=1)
    units_json: dict[str, str] = Field(default_factory=dict)
    explanation: str = Field(min_length=5)
    evidence_claims: list[EvidenceReference] = Field(min_length=1)


class RuleUpdate(RuleDraft):
    expected_record_version: int = Field(ge=1)


class RecipeSlotDraft(BaseModel):
    slot_code: str = Field(pattern="^[a-z0-9_]+$", max_length=80)
    required_quality: str
    training_role: Literal["preparation", "primary", "accessory", "capacity", "recovery"]
    selection_constraints_json: dict[str, Any] = Field(default_factory=dict)
    dose_schema_json: dict[str, Any]
    required: bool = True


class RecipeBlockDraft(BaseModel):
    block_type: str = Field(min_length=2, max_length=30)
    purpose: str = Field(min_length=3, max_length=160)
    duration_minimum: int = Field(ge=1, le=300)
    duration_maximum: int = Field(ge=1, le=300)
    slots: list[RecipeSlotDraft] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_duration(self):
        if self.duration_minimum > self.duration_maximum:
            raise ValueError("duration_minimum cannot exceed duration_maximum")
        return self


class RecipeDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=100)
    name: str = Field(min_length=3, max_length=160)
    recipe_type: str = Field(min_length=2, max_length=30)
    sport_code: str | None = None
    event_codes: list[str] = Field(default_factory=list)
    role_codes: list[str] = Field(default_factory=list)
    discipline_codes: list[str] = Field(default_factory=list)
    format_codes: list[str] = Field(default_factory=list)
    phase_codes: list[str] = Field(default_factory=list)
    goal_codes: list[str] = Field(default_factory=list)
    level_codes: list[str] = Field(default_factory=list)
    load_class: Literal["easy", "moderate", "hard", "recovery"]
    purpose: str = Field(min_length=5)
    blocks: list[RecipeBlockDraft] = Field(min_length=1)


class RecipeUpdate(RecipeDraft):
    expected_record_version: int = Field(ge=1)


class RecipeRetireCommand(BaseModel):
    retired: bool
    expected_record_version: int = Field(ge=1)


class ProgramArchetypeDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=100)
    sport_code: str
    name: str = Field(min_length=3, max_length=160)
    event_codes: list[str] = Field(default_factory=list)
    role_codes: list[str] = Field(default_factory=list)
    discipline_codes: list[str] = Field(default_factory=list)
    format_codes: list[str] = Field(default_factory=list)
    goal_codes: list[str] = Field(default_factory=list)
    level_codes: list[str] = Field(default_factory=list)
    minimum_weeks: int = Field(ge=1, le=52)
    maximum_weeks: int = Field(ge=1, le=52)


class ProgramArchetypeUpdate(ProgramArchetypeDraft):
    expected_record_version: int = Field(ge=1)


class PhaseDraft(BaseModel):
    phase_code: str
    minimum_weeks: int = Field(ge=1, le=52)
    maximum_weeks: int = Field(ge=1, le=52)
    allocation_weight: float = Field(gt=0, le=1)
    entry_conditions_json: dict[str, Any] = Field(default_factory=dict)
    exit_conditions_json: dict[str, Any] = Field(default_factory=dict)


class WeekTemplateDraft(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=100)
    sport_code: str
    phase_code: str
    level_codes: list[str] = Field(default_factory=list)
    sessions_minimum: int = Field(ge=1, le=14)
    sessions_maximum: int = Field(ge=1, le=14)
    hard_session_maximum: int = Field(ge=0, le=7)
    spacing_rules_json: dict[str, Any]
    recipe_ids: list[UUID] = Field(min_length=1)


class WeekTemplateUpdate(WeekTemplateDraft):
    expected_version: int = Field(ge=1)


class ReleaseCreate(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=80)
    package_type: Literal["sport", "shared"]
    sport_code: str | None = None
    release_notes: str = Field(max_length=10000)

    @model_validator(mode="after")
    def package_scope(self):
        if self.package_type == "sport" and not self.sport_code:
            raise ValueError("sport_code is required for sport packages")
        if self.package_type == "shared" and self.sport_code is not None:
            raise ValueError("shared packages cannot have sport_code")
        return self


class ReleaseItemDraft(BaseModel):
    entity_type: str
    entity_id: UUID
    entity_version: int = Field(ge=1)


class ReleaseManifestReplace(BaseModel):
    expected_version: int = Field(ge=1)
    items: list[ReleaseItemDraft] = Field(min_length=1)


class PublishCommand(BaseModel):
    expected_version: int = Field(ge=1)


class ImportPreviewRequest(BaseModel):
    file_path: str = Field(min_length=1, max_length=2000)


class ImportCommitRequest(BaseModel):
    expected_version: int = Field(ge=1)


class SimulationRequest(BaseModel):
    release_id: UUID | None = None
    sport_code: str
    scenario_code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=100)
    athlete: dict[str, Any]


class OSMRegionCreate(BaseModel):
    code: str = Field(pattern="^[a-z0-9][a-z0-9_-]+$", max_length=80)
    name: str = Field(min_length=2, max_length=160)
    pbf_object: str = Field(min_length=1, max_length=500)
    boundary_geojson: dict[str, Any]


class OSMGraphCreate(BaseModel):
    region_id: UUID
    version_code: str = Field(pattern="^[a-zA-Z0-9_.-]+$", max_length=80)
    source_timestamp: datetime
    graph_object: str = Field(min_length=1, max_length=500)
    graph_hash: str = Field(pattern="^[0-9a-f]{64}$")


class OSMGraphStatusCommand(BaseModel):
    expected_version: int = Field(ge=1)
    status: Literal["validating"]


class RoleMutation(BaseModel):
    role: Literal["content_editor", "content_publisher", "moderator", "platform_admin"]


class FeatureFlagMutation(BaseModel):
    code: str = Field(pattern="^[a-z0-9_.-]+$", max_length=100)
    enabled: bool
    rules: dict[str, Any] = Field(default_factory=dict)
    expected_version: int | None = Field(default=None, ge=1)

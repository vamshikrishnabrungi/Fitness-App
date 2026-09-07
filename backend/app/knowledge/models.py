from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


CONTENT_STATES = ("draft", "catalogue_validated", "evidence_verified", "released", "retired")
RELEASE_STATES = ("draft", "validating", "released", "retired", "failed")


class EvidenceSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence_sources"
    __table_args__ = (
        UniqueConstraint("canonical_locator", name="uq_evidence_locator"),
        CheckConstraint("source_tier BETWEEN 1 AND 5", name="evidence_source_tier"),
        {"schema": "knowledge"},
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_locator: Mapped[str] = mapped_column(Text, nullable=False)
    doi: Mapped[str | None] = mapped_column(String(200))
    source_tier: Mapped[int] = mapped_column(Integer, nullable=False)
    publication_year: Mapped[int | None] = mapped_column(Integer)
    population: Mapped[str | None] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)


class EvidenceClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence_claims"
    __table_args__ = (UniqueConstraint("code", name="uq_evidence_claim_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class EvidenceClaimVersion(Base):
    __tablename__ = "evidence_claim_versions"
    __table_args__ = (
        PrimaryKeyConstraint("claim_id", "claim_version", name="pk_evidence_claim_versions"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="evidence_claim_confidence"),
        CheckConstraint("status IN ('draft','evidence_verified','released','retired')", name="evidence_claim_status"),
        {"schema": "knowledge"},
    )
    claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.evidence_claims.id", ondelete="CASCADE"), nullable=False)
    claim_version: Mapped[int] = mapped_column(Integer, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(40), nullable=False)
    implication_type: Mapped[str] = mapped_column(String(32), nullable=False)
    population: Mapped[str | None] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    limitations: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class EvidenceClaimSource(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evidence_claim_sources"
    __table_args__ = (
        ForeignKeyConstraint(["claim_id", "claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="CASCADE"),
        UniqueConstraint("claim_id", "claim_version", "source_id", name="uq_evidence_claim_source"),
        {"schema": "knowledge"},
    )
    claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    claim_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.evidence_sources.id", ondelete="RESTRICT"), nullable=False)
    support_type: Mapped[str] = mapped_column(String(24), default="supports", nullable=False)
    locator: Mapped[str | None] = mapped_column(String(300))


class SportKnowledgeSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reusable athlete-education source, separate from generator evidence claims."""

    __tablename__ = "sport_knowledge_sources"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_sport_knowledge_source_key"),
        UniqueConstraint("canonical_url", name="uq_sport_knowledge_source_url"),
        CheckConstraint("publication_year BETWEEN 1900 AND 2200", name="sport_knowledge_source_year"),
        {"schema": "knowledge"},
    )
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    publication_year: Mapped[int] = mapped_column(Integer, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    editorial_note: Mapped[str] = mapped_column(Text, nullable=False)


class SportKnowledgeArticle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sport_knowledge_articles"
    __table_args__ = (
        UniqueConstraint("sport_code", "slug", name="uq_sport_knowledge_article_slug"),
        {"schema": "knowledge"},
    )
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    published_version: Mapped[int | None] = mapped_column(Integer)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SportKnowledgeArticleVersion(Base):
    __tablename__ = "sport_knowledge_article_versions"
    __table_args__ = (
        PrimaryKeyConstraint("article_id", "content_version", name="pk_sport_knowledge_article_versions"),
        ForeignKeyConstraint(["article_id"], ["knowledge.sport_knowledge_articles.id"], ondelete="CASCADE"),
        CheckConstraint("status IN ('draft','in_review','published','retired')", name="sport_knowledge_article_version_status"),
        {"schema": "knowledge"},
    )
    article_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=False)
    audiences: Mapped[list[str]] = mapped_column(ARRAY(String(40)), nullable=False)
    events: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False)
    sections: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    medical_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class SportKnowledgeArticleSource(Base):
    __tablename__ = "sport_knowledge_article_sources"
    __table_args__ = (
        PrimaryKeyConstraint("article_id", "article_version", "source_id", name="pk_sport_knowledge_article_sources"),
        ForeignKeyConstraint(
            ["article_id", "article_version"],
            ["knowledge.sport_knowledge_article_versions.article_id", "knowledge.sport_knowledge_article_versions.content_version"],
            ondelete="CASCADE",
        ),
        {"schema": "knowledge"},
    )
    article_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    article_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.sport_knowledge_sources.id", ondelete="RESTRICT"), nullable=False)


class SportKnowledgeRelease(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sport_knowledge_releases"
    __table_args__ = (
        UniqueConstraint("sport_code", "release_version", name="uq_sport_knowledge_release_version"),
        CheckConstraint("status IN ('published','retired')", name="sport_knowledge_release_status"),
        {"schema": "knowledge"},
    )
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    release_version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    subtitle: Mapped[str] = mapped_column(Text, nullable=False)
    medical_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    article_manifest: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"))


class KnowledgeTerm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "terms"
    __table_args__ = (
        UniqueConstraint("category", "code", name="uq_knowledge_term_category_code"),
        {"schema": "knowledge"},
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)


class PhysicalQuality(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "physical_qualities"
    __table_args__ = (UniqueConstraint("code", name="uq_physical_quality_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)


class SportTaxon(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sport_taxa"
    __table_args__ = (
        UniqueConstraint("code", name="uq_sport_taxon_code"),
        {"schema": "knowledge"},
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    taxon_type: Mapped[str] = mapped_column(String(24), nullable=False)
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    parent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.sport_taxa.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Method(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stable logical identity. Athlete-facing fields live in immutable versions."""

    __tablename__ = "methods"
    __table_args__ = (UniqueConstraint("code", name="uq_method_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MethodVersion(Base):
    __tablename__ = "method_versions"
    __table_args__ = (
        PrimaryKeyConstraint("method_id", "content_version", name="pk_method_versions"),
        CheckConstraint("technical_cost BETWEEN 1 AND 5", name="method_version_technical_cost"),
        CheckConstraint("impact_cost BETWEEN 1 AND 5", name="method_version_impact_cost"),
        CheckConstraint("fatigue_cost BETWEEN 1 AND 5", name="method_version_fatigue_cost"),
        CheckConstraint("status IN ('draft','catalogue_validated','evidence_verified','released','retired')", name="method_version_status"),
        {"schema": "knowledge"},
    )
    method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.methods.id", ondelete="CASCADE"), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(180), nullable=False)
    method_type: Mapped[str] = mapped_column(String(30), nullable=False)
    movement_pattern: Mapped[str] = mapped_column(String(50), nullable=False)
    equipment_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    environments: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list, nullable=False)
    surfaces: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list, nullable=False)
    accepted_dose_units: Mapped[list[str]] = mapped_column(ARRAY(String(30)), nullable=False)
    force_directions: Mapped[list[str]] = mapped_column(ARRAY(String(24)), default=list, nullable=False)
    contractions: Mapped[list[str]] = mapped_column(ARRAY(String(24)), default=list, nullable=False)
    speed_intent: Mapped[str] = mapped_column(String(24), nullable=False)
    joint_positions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    level_minimum: Mapped[str] = mapped_column(String(20), nullable=False)
    technical_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    impact_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    fatigue_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    supervision_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    instructions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    cues: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    common_errors: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    safety_boundaries: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    source_hash: Mapped[str | None] = mapped_column(String(64))
    wording_original: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    generator_eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class MethodAlias(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "method_aliases"
    __table_args__ = (
        UniqueConstraint("normalized_alias", name="uq_method_normalized_alias"),
        {"schema": "knowledge"},
    )
    method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.methods.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(180), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(180), nullable=False)


class MethodEffect(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "method_effects"
    __table_args__ = (
        ForeignKeyConstraint(["method_id", "method_version"], ["knowledge.method_versions.method_id", "knowledge.method_versions.content_version"], ondelete="CASCADE"),
        ForeignKeyConstraint(["evidence_claim_id", "evidence_claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="RESTRICT"),
        UniqueConstraint("method_id", "method_version", "quality_code", name="uq_method_effect_version"),
        CheckConstraint("magnitude BETWEEN 0 AND 1", name="effect_magnitude_range"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="effect_confidence_range"),
        {"schema": "knowledge"},
    )
    method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    method_version: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_code: Mapped[str] = mapped_column(String(60), ForeignKey("knowledge.physical_qualities.code", ondelete="RESTRICT"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    training_role: Mapped[str] = mapped_column(String(20), nullable=False)
    magnitude: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    evidence_claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evidence_claim_version: Mapped[int] = mapped_column(Integer, nullable=False)


class MethodConstraint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "method_constraints"
    __table_args__ = (
        ForeignKeyConstraint(["method_id", "method_version"], ["knowledge.method_versions.method_id", "knowledge.method_versions.content_version"], ondelete="CASCADE"),
        ForeignKeyConstraint(["evidence_claim_id", "evidence_claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="RESTRICT"),
        UniqueConstraint("method_id", "method_version", "constraint_type", "code", name="uq_method_constraint_version"),
        CheckConstraint("(evidence_claim_id IS NULL) = (evidence_claim_version IS NULL)", name="method_constraint_evidence_pair"),
        {"schema": "knowledge"},
    )
    method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    method_version: Mapped[int] = mapped_column(Integer, nullable=False)
    constraint_type: Mapped[str] = mapped_column(String(30), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    condition_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    athlete_message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_claim_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    evidence_claim_version: Mapped[int | None] = mapped_column(Integer)


class MethodMedia(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "method_media"
    __table_args__ = (
        ForeignKeyConstraint(["method_id", "method_version"], ["knowledge.method_versions.method_id", "knowledge.method_versions.content_version"], ondelete="CASCADE"),
        UniqueConstraint("method_id", "method_version", "media_type", "object_name", name="uq_method_media_object"),
        {"schema": "knowledge"},
    )
    method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    method_version: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String(24), nullable=False)
    bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ownership_status: Mapped[str] = mapped_column(String(24), nullable=False)
    technical_review_status: Mapped[str] = mapped_column(String(24), nullable=False)


class MethodRelation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "method_relations"
    __table_args__ = (
        UniqueConstraint("from_method_id", "to_method_id", "relation_type", "objective_code", name="uq_method_relation"),
        CheckConstraint("relation_type IN ('progression','substitution','alternative')", name="method_relation_type"),
        CheckConstraint("(evidence_claim_id IS NULL) = (evidence_claim_version IS NULL)", name="method_relation_evidence_pair"),
        ForeignKeyConstraint(["evidence_claim_id", "evidence_claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="RESTRICT"),
        {"schema": "knowledge"},
    )
    from_method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.methods.id", ondelete="CASCADE"), nullable=False)
    to_method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.methods.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(24), nullable=False)
    objective_code: Mapped[str] = mapped_column(String(60), ForeignKey("knowledge.physical_qualities.code", ondelete="RESTRICT"), nullable=False)
    prerequisites_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_claim_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    evidence_claim_version: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)


class DemandFact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "demand_facts"
    __table_args__ = (UniqueConstraint("code", name="uq_demand_fact_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class DemandFactVersion(Base):
    __tablename__ = "demand_fact_versions"
    __table_args__ = (
        PrimaryKeyConstraint("demand_fact_id", "fact_version", name="pk_demand_fact_versions"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="demand_fact_confidence"),
        ForeignKeyConstraint(["evidence_claim_id", "evidence_claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="RESTRICT"),
        {"schema": "knowledge"},
    )
    demand_fact_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.demand_facts.id", ondelete="CASCADE"), nullable=False)
    fact_version: Mapped[int] = mapped_column(Integer, nullable=False)
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    event_code: Mapped[str | None] = mapped_column(String(60), index=True)
    role_code: Mapped[str | None] = mapped_column(String(60), index=True)
    discipline_code: Mapped[str | None] = mapped_column(String(60), index=True)
    format_code: Mapped[str | None] = mapped_column(String(60), index=True)
    weight_class_code: Mapped[str | None] = mapped_column(String(40))
    competition_level: Mapped[str | None] = mapped_column(String(24))
    phase_code: Mapped[str | None] = mapped_column(String(50))
    dimension_code: Mapped[str] = mapped_column(String(80), nullable=False)
    metric_code: Mapped[str] = mapped_column(String(80), nullable=False)
    minimum_value: Mapped[float | None] = mapped_column(Numeric(16, 5))
    maximum_value: Mapped[float | None] = mapped_column(Numeric(16, 5))
    unit: Mapped[str | None] = mapped_column(String(30))
    context: Mapped[str] = mapped_column(Text, nullable=False)
    implication_type: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    evidence_claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evidence_claim_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class SportQualityPriority(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sport_quality_priorities"
    __table_args__ = (
        UniqueConstraint("sport_code", "event_code", "role_code", "discipline_code", "format_code", "phase_code", "level_code", "quality_code", name="uq_sport_quality_priority_scope"),
        CheckConstraint("priority_weight BETWEEN 0 AND 1", name="sport_quality_priority_weight"),
        ForeignKeyConstraint(["evidence_claim_id", "evidence_claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="RESTRICT"),
        {"schema": "knowledge"},
    )
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    event_code: Mapped[str | None] = mapped_column(String(60))
    role_code: Mapped[str | None] = mapped_column(String(60))
    discipline_code: Mapped[str | None] = mapped_column(String(60))
    format_code: Mapped[str | None] = mapped_column(String(60))
    phase_code: Mapped[str] = mapped_column(String(50), nullable=False)
    level_code: Mapped[str | None] = mapped_column(String(24))
    quality_code: Mapped[str] = mapped_column(String(60), ForeignKey("knowledge.physical_qualities.code", ondelete="RESTRICT"), nullable=False)
    priority_weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evidence_claim_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)


class PrescriptionRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prescription_rules"
    __table_args__ = (UniqueConstraint("code", name="uq_prescription_rule_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class PrescriptionRuleVersion(Base):
    __tablename__ = "prescription_rule_versions"
    __table_args__ = (
        PrimaryKeyConstraint("rule_id", "rule_version", name="pk_prescription_rule_versions"),
        {"schema": "knowledge"},
    )
    rule_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.prescription_rules.id", ondelete="CASCADE"), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    scope: Mapped[str] = mapped_column(String(40), nullable=False)
    sport_code: Mapped[str | None] = mapped_column(String(40), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    conditions_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    actions_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    units_json: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class PrescriptionRuleEvidenceClaim(Base):
    __tablename__ = "prescription_rule_evidence_claims"
    __table_args__ = (
        PrimaryKeyConstraint("rule_id", "rule_version", "claim_id", "claim_version", name="pk_prescription_rule_evidence_claims"),
        ForeignKeyConstraint(["rule_id", "rule_version"], ["knowledge.prescription_rule_versions.rule_id", "knowledge.prescription_rule_versions.rule_version"], ondelete="CASCADE"),
        ForeignKeyConstraint(["claim_id", "claim_version"], ["knowledge.evidence_claim_versions.claim_id", "knowledge.evidence_claim_versions.claim_version"], ondelete="RESTRICT"),
        {"schema": "knowledge"},
    )
    rule_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    claim_version: Mapped[int] = mapped_column(Integer, nullable=False)


class ProgramArchetype(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "program_archetypes"
    __table_args__ = (UniqueConstraint("code", name="uq_program_archetype_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ProgramArchetypeVersion(Base):
    __tablename__ = "program_archetype_versions"
    __table_args__ = (
        PrimaryKeyConstraint("archetype_id", "content_version", name="pk_program_archetype_versions"),
        {"schema": "knowledge"},
    )
    archetype_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.program_archetypes.id", ondelete="CASCADE"), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    event_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    role_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    discipline_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    format_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    goal_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    level_codes: Mapped[list[str]] = mapped_column(ARRAY(String(24)), default=list, nullable=False)
    minimum_weeks: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    maximum_weeks: Mapped[int] = mapped_column(Integer, default=52, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class PhaseTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "phase_templates"
    __table_args__ = (
        UniqueConstraint("archetype_id", "archetype_version", "sequence", name="uq_phase_template_sequence"),
        ForeignKeyConstraint(["archetype_id", "archetype_version"], ["knowledge.program_archetype_versions.archetype_id", "knowledge.program_archetype_versions.content_version"], ondelete="CASCADE"),
        {"schema": "knowledge"},
    )
    archetype_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    archetype_version: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    phase_code: Mapped[str] = mapped_column(String(50), nullable=False)
    minimum_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    maximum_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    allocation_weight: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    entry_conditions_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    exit_conditions_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class WeekTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "week_templates"
    __table_args__ = (UniqueConstraint("code", name="uq_week_template_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    phase_code: Mapped[str] = mapped_column(String(50), nullable=False)
    level_codes: Mapped[list[str]] = mapped_column(ARRAY(String(24)), default=list, nullable=False)
    sessions_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_maximum: Mapped[int] = mapped_column(Integer, nullable=False)
    hard_session_maximum: Mapped[int] = mapped_column(Integer, nullable=False)
    spacing_rules_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)


class Recipe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipes"
    __table_args__ = (UniqueConstraint("code", name="uq_recipe_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    __table_args__ = (
        PrimaryKeyConstraint("recipe_id", "recipe_version", name="pk_recipe_versions"),
        {"schema": "knowledge"},
    )
    recipe_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.recipes.id", ondelete="CASCADE"), nullable=False)
    recipe_version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    recipe_type: Mapped[str] = mapped_column(String(30), nullable=False)
    sport_code: Mapped[str | None] = mapped_column(String(40), index=True)
    event_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    role_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    discipline_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    format_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    phase_codes: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, nullable=False)
    goal_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list, nullable=False)
    level_codes: Mapped[list[str]] = mapped_column(ARRAY(String(24)), default=list, nullable=False)
    load_class: Mapped[str] = mapped_column(String(16), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class RecipeBlock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe_blocks"
    __table_args__ = (
        ForeignKeyConstraint(["recipe_id", "recipe_version"], ["knowledge.recipe_versions.recipe_id", "knowledge.recipe_versions.recipe_version"], ondelete="CASCADE"),
        UniqueConstraint("recipe_id", "recipe_version", "sequence", name="uq_recipe_block_sequence"),
        {"schema": "knowledge"},
    )
    recipe_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    recipe_version: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    block_type: Mapped[str] = mapped_column(String(30), nullable=False)
    purpose: Mapped[str] = mapped_column(String(160), nullable=False)
    duration_minimum: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_maximum: Mapped[int] = mapped_column(Integer, nullable=False)


class RecipeSlot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe_slots"
    __table_args__ = (
        UniqueConstraint("block_id", "sequence", name="uq_recipe_slot_sequence"),
        {"schema": "knowledge"},
    )
    block_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.recipe_blocks.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_code: Mapped[str] = mapped_column(String(80), nullable=False)
    required_quality: Mapped[str] = mapped_column(String(60), ForeignKey("knowledge.physical_qualities.code", ondelete="RESTRICT"), nullable=False)
    training_role: Mapped[str] = mapped_column(String(20), nullable=False)
    selection_constraints_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    dose_schema_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WeekTemplateSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "week_template_sessions"
    __table_args__ = (
        UniqueConstraint("week_template_id", "sequence", name="uq_week_template_session_sequence"),
        {"schema": "knowledge"},
    )
    week_template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.week_templates.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    recipe_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.recipes.id", ondelete="RESTRICT"), nullable=False)
    preferred_weekday: Mapped[int | None] = mapped_column(Integer)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TrainingReferenceTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stable identity for a reviewed four-week category reference."""

    __tablename__ = "training_reference_templates"
    __table_args__ = (UniqueConstraint("code", name="uq_training_reference_template_code"), {"schema": "knowledge"})
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    latest_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class TrainingReferenceTemplateVersion(Base):
    __tablename__ = "training_reference_template_versions"
    __table_args__ = (
        PrimaryKeyConstraint("template_id", "content_version", name="pk_training_reference_template_versions"),
        CheckConstraint("duration_weeks BETWEEN 1 AND 52", name="training_reference_duration"),
        {"schema": "knowledge"},
    )
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.training_reference_templates.id", ondelete="CASCADE"), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False)
    research_phase: Mapped[int] = mapped_column(Integer, nullable=False)
    category_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    athlete_level: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    source_template_ids: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list, nullable=False)
    applicable_scenarios: Mapped[list[str]] = mapped_column(ARRAY(String(80)), default=list, nullable=False)
    selection_policy_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    selection_rules_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    exercise_progression_policy: Mapped[str] = mapped_column(Text, nullable=False)
    week_4_policy: Mapped[str] = mapped_column(Text, nullable=False)
    mandatory_stops: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    ai_use: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_reference_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="research_derived_candidate", nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class TrainingReferenceMethod(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "training_reference_methods"
    __table_args__ = (
        ForeignKeyConstraint(["template_id", "template_version"], ["knowledge.training_reference_template_versions.template_id", "knowledge.training_reference_template_versions.content_version"], ondelete="CASCADE"),
        ForeignKeyConstraint(["method_id", "method_version"], ["knowledge.method_versions.method_id", "knowledge.method_versions.content_version"], ondelete="RESTRICT"),
        UniqueConstraint("template_id", "template_version", "sequence", name="uq_training_reference_method_sequence"),
        UniqueConstraint("template_id", "template_version", "method_id", name="uq_training_reference_method"),
        {"schema": "knowledge"},
    )
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    method_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    method_version: Mapped[int] = mapped_column(Integer, nullable=False)
    block_role: Mapped[str] = mapped_column(String(32), nullable=False)
    applicable_modes: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list, nullable=False)
    sport_codes: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list, nullable=False)
    scope_codes: Mapped[list[str]] = mapped_column(ARRAY(String(80)), default=list, nullable=False)
    implementation_note: Mapped[str] = mapped_column(Text, default="", nullable=False)


class TrainingReferenceWeek(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "training_reference_weeks"
    __table_args__ = (
        ForeignKeyConstraint(["template_id", "template_version"], ["knowledge.training_reference_template_versions.template_id", "knowledge.training_reference_template_versions.content_version"], ondelete="CASCADE"),
        UniqueConstraint("template_id", "template_version", "week_number", name="uq_training_reference_week"),
        CheckConstraint("week_number BETWEEN 1 AND 52", name="training_reference_week_number"),
        {"schema": "knowledge"},
    )
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    intent: Mapped[str] = mapped_column(String(180), nullable=False)
    sessions_per_week: Mapped[str] = mapped_column(String(40), nullable=False)
    prescription_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    progression_condition: Mapped[str] = mapped_column(Text, nullable=False)
    regression_condition: Mapped[str] = mapped_column(Text, nullable=False)


class SportModePolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sport_mode_policies"
    __table_args__ = (UniqueConstraint("sport_code", name="uq_sport_mode_policy"), {"schema": "knowledge"})
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False)
    primary_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    cross_training_requires_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class PhaseDosePolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "phase_dose_policies"
    __table_args__ = (
        UniqueConstraint("phase_code", name="uq_phase_dose_policy"),
        CheckConstraint(
            "progression_mode IN ('development','maintain_week_1','competition_taper')",
            name="valid_phase_progression_mode",
        ),
        CheckConstraint("maximum_categories BETWEEN 1 AND 8", name="valid_phase_category_limit"),
        CheckConstraint("maximum_sessions_per_week BETWEEN 1 AND 7", name="valid_phase_session_limit"),
        {"schema": "knowledge"},
    )
    phase_code: Mapped[str] = mapped_column(String(60), nullable=False)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    progression_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    maximum_categories: Mapped[int] = mapped_column(Integer, nullable=False)
    maximum_sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    weekly_volume_multipliers: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    novelty_policy: Mapped[str] = mapped_column(String(40), nullable=False)
    policy_basis: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SportTemplatePriority(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sport_template_priorities"
    __table_args__ = (
        UniqueConstraint("sport_code", "scope_type", "scope_code", "phase_code", "goal_code", name="uq_sport_template_priority_scope"),
        {"schema": "knowledge"},
    )
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False)
    scope_code: Mapped[str] = mapped_column(String(80), nullable=False)
    phase_code: Mapped[str] = mapped_column(String(60), nullable=False)
    goal_code: Mapped[str] = mapped_column(String(80), nullable=False)
    primary_template_category: Mapped[str] = mapped_column(String(80), nullable=False)
    session_block_order: Mapped[list[str]] = mapped_column(ARRAY(String(80)), default=list, nullable=False)
    priority_basis: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SportTemplatePriorityItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sport_template_priority_items"
    __table_args__ = (
        UniqueConstraint("priority_id", "rank", name="uq_sport_template_priority_rank"),
        UniqueConstraint("priority_id", "category_code", name="uq_sport_template_priority_category"),
        CheckConstraint("rank BETWEEN 1 AND 8", name="sport_template_priority_rank"),
        CheckConstraint("weight BETWEEN 0 AND 1", name="sport_template_priority_weight"),
        {"schema": "knowledge"},
    )
    priority_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.sport_template_priorities.id", ondelete="CASCADE"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    category_code: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)


class ContentReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_reviews"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "entity_version", "review_type", "reviewer_user_id", name="uq_content_review_actor_scope"),
        {"schema": "knowledge"},
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    entity_version: Mapped[int] = mapped_column(Integer, nullable=False)
    review_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reviewer_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="RESTRICT"), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ContentRelease(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_releases"
    __table_args__ = (
        UniqueConstraint("code", name="uq_content_release_code"),
        CheckConstraint("state IN ('draft','validating','released','retired','failed')", name="content_release_state"),
        Index("uq_active_sport_release", "sport_code", unique=True, postgresql_where="state = 'released'"),
        {"schema": "knowledge"},
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    package_type: Mapped[str] = mapped_column(String(24), nullable=False)
    sport_code: Mapped[str | None] = mapped_column(String(40), index=True)
    state: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    release_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    validation_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="RESTRICT"))


class ReleaseItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "release_items"
    __table_args__ = (
        UniqueConstraint("release_id", "entity_type", "entity_id", name="uq_release_item"),
        {"schema": "knowledge"},
    )
    release_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.content_releases.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    entity_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SourceImport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_imports"
    __table_args__ = (UniqueConstraint("source_type", "content_hash", name="uq_source_import_hash"), {"schema": "knowledge"})
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_name: Mapped[str] = mapped_column(String(240), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="previewed", nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    committed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="RESTRICT"))


class SourceImportRow(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_import_rows"
    __table_args__ = (
        UniqueConstraint("source_import_id", "source_reference", name="uq_source_import_row_reference"),
        {"schema": "knowledge"},
    )
    source_import_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.source_imports.id", ondelete="CASCADE"), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(160), nullable=False)
    source_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    validation_errors: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    canonical_method_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.methods.id", ondelete="SET NULL"))


class SourceDisposition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_dispositions"
    __table_args__ = (UniqueConstraint("source_system", "source_reference", name="uq_source_disposition"), {"schema": "knowledge"})
    source_system: Mapped[str] = mapped_column(String(60), nullable=False)
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(Text)
    disposition: Mapped[str] = mapped_column(String(24), nullable=False)
    canonical_method_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.methods.id", ondelete="SET NULL"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class SimulationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "simulation_runs"
    __table_args__ = ({"schema": "knowledge"},)
    release_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.content_releases.id", ondelete="SET NULL"))
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    scenario_code: Mapped[str] = mapped_column(String(100), nullable=False)
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    planner_version: Mapped[str] = mapped_column(String(40), nullable=False)
    executed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"))

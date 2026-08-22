from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import model_dict
from backend.app.training.planner import canonical_hash

from .models import (
    ContentRelease,
    ContentReview,
    DemandFact,
    DemandFactVersion,
    EvidenceClaim,
    EvidenceClaimVersion,
    Method,
    MethodConstraint,
    MethodEffect,
    MethodRelation,
    MethodVersion,
    PhaseTemplate,
    PhysicalQuality,
    PrescriptionRule,
    PrescriptionRuleEvidenceClaim,
    PrescriptionRuleVersion,
    ProgramArchetype,
    ProgramArchetypeVersion,
    Recipe,
    RecipeBlock,
    RecipeSlot,
    RecipeVersion,
    ReleaseItem,
    SportQualityPriority,
    SportTaxon,
    WeekTemplate,
)
from .validation import (
    KnowledgeValidationError,
    validate_method,
    validate_prescription_rule,
    validate_progression_dag,
    validate_recipe,
)
from .sport_requirements import package_coverage_errors


LAUNCH_SPORTS = {
    "badminton",
    "basketball",
    "boxing",
    "cricket",
    "cycling",
    "football",
    "mma",
    "running",
    "swimming",
    "tennis",
    "volleyball",
    "hyrox",
}

VERSIONED_ENTITY_TYPES = {
    "method",
    "demand_fact",
    "prescription_rule",
    "program_archetype",
    "recipe",
    "evidence_claim",
}
SINGLE_VERSION_ENTITY_TYPES = {
    "method_relation",
    "physical_quality",
    "sport_taxon",
    "sport_quality_priority",
    "week_template",
}
ALLOWED_ENTITY_TYPES = VERSIONED_ENTITY_TYPES | SINGLE_VERSION_ENTITY_TYPES


class ReleaseValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedReleaseItem:
    item: ReleaseItem
    entity: object
    snapshot_hash: str


async def _resolve_item(session: AsyncSession, item: ReleaseItem) -> object:
    if item.entity_type == "method":
        row = await session.scalar(select(MethodVersion).where(MethodVersion.method_id == item.entity_id, MethodVersion.content_version == item.entity_version))
    elif item.entity_type == "demand_fact":
        row = await session.scalar(select(DemandFactVersion).where(DemandFactVersion.demand_fact_id == item.entity_id, DemandFactVersion.fact_version == item.entity_version))
    elif item.entity_type == "prescription_rule":
        row = await session.scalar(select(PrescriptionRuleVersion).where(PrescriptionRuleVersion.rule_id == item.entity_id, PrescriptionRuleVersion.rule_version == item.entity_version))
    elif item.entity_type == "program_archetype":
        row = await session.scalar(select(ProgramArchetypeVersion).where(ProgramArchetypeVersion.archetype_id == item.entity_id, ProgramArchetypeVersion.content_version == item.entity_version))
    elif item.entity_type == "recipe":
        row = await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id == item.entity_id, RecipeVersion.recipe_version == item.entity_version))
    elif item.entity_type == "evidence_claim":
        row = await session.scalar(select(EvidenceClaimVersion).where(EvidenceClaimVersion.claim_id == item.entity_id, EvidenceClaimVersion.claim_version == item.entity_version))
    else:
        model = {
            "method_relation": MethodRelation,
            "physical_quality": PhysicalQuality,
            "sport_taxon": SportTaxon,
            "sport_quality_priority": SportQualityPriority,
            "week_template": WeekTemplate,
        }.get(item.entity_type)
        row = await session.get(model, item.entity_id) if model else None
        if row is not None and item.entity_version != int(getattr(row, "version", 1)):
            row = None
    if row is None:
        raise ReleaseValidationError(f"unresolved release item: {item.entity_type}/{item.entity_id}/v{item.entity_version}")
    return row


async def snapshot_for_item(session: AsyncSession, item: ReleaseItem, entity: object) -> str:
    payload: dict[str, Any] = {"entity": model_dict(entity)}
    if item.entity_type == "method":
        payload["effects"] = [
            model_dict(row)
            for row in (await session.scalars(select(MethodEffect).where(MethodEffect.method_id == item.entity_id, MethodEffect.method_version == item.entity_version).order_by(MethodEffect.quality_code))).all()
        ]
        payload["constraints"] = [
            model_dict(row)
            for row in (await session.scalars(select(MethodConstraint).where(MethodConstraint.method_id == item.entity_id, MethodConstraint.method_version == item.entity_version).order_by(MethodConstraint.code))).all()
        ]
    elif item.entity_type == "recipe":
        blocks = (await session.scalars(select(RecipeBlock).where(RecipeBlock.recipe_id == item.entity_id, RecipeBlock.recipe_version == item.entity_version).order_by(RecipeBlock.sequence))).all()
        payload["blocks"] = [model_dict(row) for row in blocks]
        payload["slots"] = [
            model_dict(row)
            for row in (await session.scalars(select(RecipeSlot).where(RecipeSlot.block_id.in_([block.id for block in blocks])).order_by(RecipeSlot.block_id, RecipeSlot.sequence))).all()
        ] if blocks else []
    return canonical_hash(payload)


async def validate_release(session: AsyncSession, release: ContentRelease) -> list[ResolvedReleaseItem]:
    if release.state != "draft":
        raise ReleaseValidationError("only a draft release can be validated")
    if release.package_type not in {"sport", "shared"}:
        raise ReleaseValidationError("release package type must be sport or shared")
    if release.package_type == "sport" and release.sport_code not in LAUNCH_SPORTS:
        raise ReleaseValidationError("sport release uses an unsupported sport code")
    if release.package_type == "shared" and release.sport_code is not None:
        raise ReleaseValidationError("shared releases cannot have a sport code")

    items = (await session.scalars(select(ReleaseItem).where(ReleaseItem.release_id == release.id).order_by(ReleaseItem.entity_type, ReleaseItem.entity_id))).all()
    if not items:
        raise ReleaseValidationError("release manifest is empty")
    unknown = sorted({item.entity_type for item in items} - ALLOWED_ENTITY_TYPES)
    if unknown:
        raise ReleaseValidationError(f"unsupported release entity types: {', '.join(unknown)}")

    resolved: list[ResolvedReleaseItem] = []
    groups: dict[str, list[object]] = defaultdict(list)
    for item in items:
        entity = await _resolve_item(session, item)
        status = getattr(entity, "status", None)
        if status not in {"evidence_verified", "released"}:
            raise ReleaseValidationError(f"{item.entity_type}/{item.entity_id} is not evidence verified")
        snapshot_hash = await snapshot_for_item(session, item, entity)
        if item.snapshot_hash and item.snapshot_hash != snapshot_hash:
            raise ReleaseValidationError(f"release item changed after manifest selection: {item.entity_type}/{item.entity_id}")
        groups[item.entity_type].append(entity)
        resolved.append(ResolvedReleaseItem(item, entity, snapshot_hash))

    qualities = {row.code for row in groups["physical_quality"]}
    claims = {(row.claim_id, row.claim_version) for row in groups["evidence_claim"]}
    methods = {(row.method_id, row.content_version): row for row in groups["method"]}
    method_ids = {row.method_id for row in groups["method"]}

    effects_by_method: dict[tuple[UUID, int], list[MethodEffect]] = defaultdict(list)
    constraints_by_method: dict[tuple[UUID, int], list[MethodConstraint]] = defaultdict(list)
    if methods:
        conditions = [and_(MethodEffect.method_id == method_id, MethodEffect.method_version == version) for method_id, version in methods]
        for row in (await session.scalars(select(MethodEffect).where(or_(*conditions)))).all():
            effects_by_method[(row.method_id, row.method_version)].append(row)
        constraint_conditions = [and_(MethodConstraint.method_id == method_id, MethodConstraint.method_version == version) for method_id, version in methods]
        if constraint_conditions:
            for row in (await session.scalars(select(MethodConstraint).where(or_(*constraint_conditions)))).all():
                constraints_by_method[(row.method_id, row.method_version)].append(row)

    for key, method in methods.items():
        try:
            validate_method(method, effects_by_method[key], constraints_by_method[key])
        except KnowledgeValidationError as exc:
            raise ReleaseValidationError(f"method {method.method_id}/v{method.content_version}: {exc}") from exc
        for effect in effects_by_method[key]:
            if effect.quality_code not in qualities:
                raise ReleaseValidationError(f"method effect references an unmanifested quality: {effect.quality_code}")
            if (effect.evidence_claim_id, effect.evidence_claim_version) not in claims:
                raise ReleaseValidationError("method effect references an unmanifested evidence claim")

    relations = list(groups["method_relation"])
    if any(row.from_method_id not in method_ids or row.to_method_id not in method_ids for row in relations):
        raise ReleaseValidationError("method relation references a method outside the manifest")
    try:
        validate_progression_dag(relations)
    except KnowledgeValidationError as exc:
        raise ReleaseValidationError(str(exc)) from exc

    for fact in groups["demand_fact"]:
        if release.sport_code and fact.sport_code != release.sport_code:
            raise ReleaseValidationError("demand fact belongs to another sport")
        if (fact.evidence_claim_id, fact.evidence_claim_version) not in claims:
            raise ReleaseValidationError("demand fact references an unmanifested evidence claim")

    for priority in groups["sport_quality_priority"]:
        if release.sport_code and priority.sport_code != release.sport_code:
            raise ReleaseValidationError("quality priority belongs to another sport")
        if priority.quality_code not in qualities or (priority.evidence_claim_id, priority.evidence_claim_version) not in claims:
            raise ReleaseValidationError("quality priority has unresolved quality or evidence provenance")

    for rule in groups["prescription_rule"]:
        try:
            validate_prescription_rule(rule)
        except KnowledgeValidationError as exc:
            raise ReleaseValidationError(f"prescription rule {rule.rule_id}/v{rule.rule_version}: {exc}") from exc
        rule_claims = set((await session.execute(select(PrescriptionRuleEvidenceClaim.claim_id, PrescriptionRuleEvidenceClaim.claim_version).where(PrescriptionRuleEvidenceClaim.rule_id == rule.rule_id, PrescriptionRuleEvidenceClaim.rule_version == rule.rule_version))).all())
        if not rule_claims or not rule_claims.issubset(claims):
            raise ReleaseValidationError("prescription rule references an unmanifested evidence claim")

    effect_index = {(effect.quality_code, effect.training_role) for values in effects_by_method.values() for effect in values}
    for recipe in groups["recipe"]:
        if release.sport_code and recipe.sport_code not in {None, release.sport_code}:
            raise ReleaseValidationError("recipe belongs to another sport")
        blocks = (await session.scalars(select(RecipeBlock).where(RecipeBlock.recipe_id == recipe.recipe_id, RecipeBlock.recipe_version == recipe.recipe_version).order_by(RecipeBlock.sequence))).all()
        slots_by_block: dict = defaultdict(list)
        if blocks:
            for row in (await session.scalars(select(RecipeSlot).where(RecipeSlot.block_id.in_([block.id for block in blocks])).order_by(RecipeSlot.sequence))).all():
                slots_by_block[row.block_id].append(row)
        try:
            validate_recipe(recipe, blocks, slots_by_block)
        except KnowledgeValidationError as exc:
            raise ReleaseValidationError(f"recipe {recipe.recipe_id}/v{recipe.recipe_version}: {exc}") from exc
        for slots in slots_by_block.values():
            for slot in slots:
                if slot.required and (slot.required_quality, slot.training_role) not in effect_index:
                    raise ReleaseValidationError(f"required recipe slot cannot resolve: {slot.slot_code}")

    if release.package_type == "sport":
        required_groups = {"method", "physical_quality", "sport_taxon", "demand_fact", "sport_quality_priority", "prescription_rule", "program_archetype", "week_template", "recipe", "evidence_claim"}
        missing = sorted(name for name in required_groups if not groups[name])
        if missing:
            raise ReleaseValidationError(f"sport release is incomplete; missing: {', '.join(missing)}")
        sport_taxa = [row for row in groups["sport_taxon"] if row.sport_code == release.sport_code]
        if not any(row.taxon_type == "sport" for row in sport_taxa):
            raise ReleaseValidationError("sport release has no root sport taxonomy")
        if release.sport_code == "hyrox" and any(row.visible for row in sport_taxa):
            raise ReleaseValidationError("HYROX must remain hidden until its package is explicitly enabled")
        archetypes=list(groups["program_archetype"]); archetype_conditions=[and_(PhaseTemplate.archetype_id==row.archetype_id,PhaseTemplate.archetype_version==row.content_version) for row in archetypes]
        phases=(await session.scalars(select(PhaseTemplate).where(or_(*archetype_conditions)))).all() if archetype_conditions else []
        coverage_errors=package_coverage_errors(release.sport_code,demands=list(groups["demand_fact"]),priorities=list(groups["sport_quality_priority"]),recipes=list(groups["recipe"]),phases=phases,week_templates=list(groups["week_template"]))
        if coverage_errors: raise ReleaseValidationError("sport package coverage failed: " + "; ".join(coverage_errors))

    reviewed = (await session.scalars(select(ContentReview).where(ContentReview.entity_id.in_([item.entity_id for item in items]), ContentReview.decision == "approved"))).all()
    approved_keys = {(row.entity_type, row.entity_id, row.entity_version) for row in reviewed}
    review_required = {
        (item.entity_type, item.entity_id, item.entity_version)
        for item in items
        if item.entity_type in VERSIONED_ENTITY_TYPES
    }
    missing_reviews = review_required - approved_keys
    if missing_reviews:
        raise ReleaseValidationError(f"release contains {len(missing_reviews)} versioned items without an approved human review")

    return resolved

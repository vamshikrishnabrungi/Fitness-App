from __future__ import annotations

from collections import defaultdict
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, case, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session, model_dict
from backend.app.core.pagination import decode_cursor, encode_cursor
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_claims, current_user_id, require_roles
from backend.app.core.config import get_settings
from backend.app.core.ids import uuid7
from backend.app.core.storage import signed_gcs_url
from backend.app.knowledge.importer import WorkbookImportError, commit_import, preview_import
from backend.app.knowledge.dataset_importer import DATASET_KINDS, commit_dataset, preview_dataset
from backend.app.knowledge.models import (
    ContentRelease,
    ContentReview,
    DemandFact,
    DemandFactVersion,
    EvidenceClaim,
    EvidenceClaimVersion,
    EvidenceClaimSource,
    EvidenceSource,
    KnowledgeTerm,
    Method,
    MethodAlias,
    MethodConstraint,
    MethodEffect,
    MethodMedia,
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
    SimulationRun,
    SourceImport,
    SourceImportRow,
    SportQualityPriority,
    SportTaxon,
    WeekTemplate,
    WeekTemplateSession,
    TrainingReferenceTemplate,
    TrainingReferenceTemplateVersion,
    TrainingReferenceMethod,
    TrainingReferenceWeek,
    SportModePolicy,
    PhaseDosePolicy,
    SportTemplatePriority,
    SportTemplatePriorityItem,
)
from backend.app.knowledge.release import ReleaseValidationError, _resolve_item, snapshot_for_item, validate_release
from backend.app.knowledge.sport_requirements import package_coverage_errors
from backend.app.knowledge.validation import (
    KnowledgeValidationError,
    validate_method,
    validate_prescription_rule,
    validate_progression_dag,
    validate_recipe,
)
from backend.app.operations.models import AuditEvent
from backend.app.training.planner import PLANNER_VERSION, canonical_hash

from .schemas import (
    ConstraintDraft,
    DemandFactDraft,
    DemandFactUpdate,
    EffectDraft,
    EvidenceClaimDraft,
    EvidenceClaimUpdate,
    EvidenceSourceDraft,
    ImportCommitRequest,
    MethodAliasesUpdate,
    MethodArchiveCommand,
    MethodCreate,
    MethodMediaDraft,
    MethodUpdate,
    MethodView,
    PhaseDraft,
    PhysicalQualityDraft,
    PhysicalQualityUpdate,
    ProgramArchetypeDraft,
    ProgramArchetypeUpdate,
    PublishCommand,
    QualityPriorityDraft,
    QualityPriorityUpdate,
    RecipeDraft,
    RecipeRetireCommand,
    RecipeUpdate,
    RelationCreate,
    RelationUpdate,
    ReleaseCreate,
    ReleaseManifestReplace,
    ReviewCreate,
    RuleDraft,
    RuleUpdate,
    SimulationRequest,
    SportTaxonDraft,
    SportTaxonUpdate,
    TermDraft,
    TermUpdate,
    WeekTemplateDraft,
    WeekTemplateUpdate,
)


async def _knowledge_access_policy(request: Request, claims: dict = Depends(current_claims)) -> None:
    roles=set(claims.get("roles",[])); path=request.url.path
    if request.method in {"GET","HEAD","OPTIONS"}:
        allowed={"content_editor","content_publisher","platform_admin"}
    elif path.endswith(("/publish","/retire","/rollback")):
        allowed={"content_publisher","platform_admin"}
    else:
        allowed={"content_editor","platform_admin"}
    if not roles&allowed:
        raise ProblemError(403,"forbidden","Forbidden","Your administrative role cannot perform this knowledge operation.")


router = APIRouter(prefix="/knowledge", tags=["admin-knowledge"], dependencies=[Depends(_knowledge_access_policy)])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _problem(exc: Exception, *, code: str, title: str) -> ProblemError:
    return ProblemError(422, code, title, str(exc))


async def _audit(session: AsyncSession, actor: UUID, action: str, subject_type: str, subject_id: UUID | None, before=None, after=None) -> None:
    session.add(AuditEvent(
        actor_user_id=actor,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        before=jsonable_encoder(before) if before is not None else None,
        after=jsonable_encoder(after) if after is not None else None,
        created_at=_now(),
    ))


async def _require_claim_refs(session: AsyncSession, refs: set[tuple[UUID, int]]) -> None:
    if not refs:
        return
    found = set((await session.execute(select(EvidenceClaimVersion.claim_id, EvidenceClaimVersion.claim_version).where(or_(*[
        and_(EvidenceClaimVersion.claim_id == claim_id, EvidenceClaimVersion.claim_version == version)
        for claim_id, version in refs
    ])))).all())
    if found != refs:
        raise ProblemError(422, "evidence_claim_missing", "Evidence claim missing", "One or more evidence claim versions do not exist.")


async def _method_view(session: AsyncSession, method: Method, version: int | None = None) -> MethodView:
    content_version = version or method.latest_version
    row = await session.scalar(select(MethodVersion).where(MethodVersion.method_id == method.id, MethodVersion.content_version == content_version))
    if row is None:
        raise ProblemError(404, "method_version_not_found", "Method version not found", "The requested method version does not exist.")
    aliases = (await session.scalars(select(MethodAlias.alias).where(MethodAlias.method_id == method.id).order_by(MethodAlias.alias))).all()
    return MethodView(id=method.id, code=method.code, content_version=row.content_version, status=row.status, generator_eligible=row.generator_eligible, record_version=row.record_version, identity_version=method.version, archived=method.archived, aliases=list(aliases), **{key: value for key, value in model_dict(row).items() if key in MethodUpdate.model_fields and key != "expected_record_version"})


async def _method_version(session: AsyncSession, method_id: UUID, content_version: int, *, lock: bool = False) -> tuple[Method, MethodVersion]:
    statement = select(MethodVersion).where(MethodVersion.method_id == method_id, MethodVersion.content_version == content_version)
    if lock:
        statement = statement.with_for_update()
    method = await session.get(Method, method_id, with_for_update=lock)
    row = await session.scalar(statement)
    if method is None or row is None:
        raise ProblemError(404, "method_not_found", "Method not found", "The requested method or version does not exist.")
    return method, row


async def _validate_and_approve_method(session: AsyncSession, row: MethodVersion) -> None:
    """Keep owner-authored catalogue edits eligible when structurally valid."""
    effects = (await session.scalars(select(MethodEffect).where(
        MethodEffect.method_id == row.method_id,
        MethodEffect.method_version == row.content_version,
    ))).all()
    constraints = (await session.scalars(select(MethodConstraint).where(
        MethodConstraint.method_id == row.method_id,
        MethodConstraint.method_version == row.content_version,
    ))).all()
    validate_method(row, effects, constraints)
    row.status = "catalogue_validated"
    row.generator_eligible = True


@router.get("/methods")
async def list_methods(
    cursor: str | None = None,
    limit: int = Query(default=100, ge=1, le=250),
    query: str = Query(default="", max_length=160),
    status: str | None = None,
    archived: bool = False,
    session: AsyncSession = Depends(get_session),
) -> dict:
    filters = [Method.archived.is_(archived)]
    if query:
        filters.append(or_(Method.code.ilike(f"%{query}%"), Method.id.in_(select(MethodVersion.method_id).where(MethodVersion.canonical_name.ilike(f"%{query}%")))))
    if status:
        filters.append(Method.id.in_(select(MethodVersion.method_id).where(MethodVersion.status == status)))

    # Fetch identities, latest versions and full-collection totals in a single
    # Cloud SQL round trip. Aliases are detail-only and load when an exercise
    # is opened; they are unnecessary weight for the library table.
    statement = select(
        Method,
        MethodVersion,
        func.count(Method.id).over().label("collection_total"),
        func.sum(case((MethodVersion.generator_eligible.is_(True), 1), else_=0)).over().label("eligible_total"),
    ).join(
        MethodVersion,
        and_(MethodVersion.method_id == Method.id, MethodVersion.content_version == Method.latest_version),
    ).order_by(Method.created_at.desc(), Method.id.desc())
    if filters:
        statement = statement.where(*filters)
    if cursor:
        created_at, entity_id = decode_cursor(cursor)
        statement = statement.where(or_(Method.created_at < created_at, and_(Method.created_at == created_at, Method.id < entity_id)))
    fetched = (await session.execute(statement.limit(limit + 1))).all()
    rows = fetched[:limit]
    total = int(rows[0][2]) if rows else 0
    generator_eligible = int(rows[0][3] or 0) if rows else 0
    items = []
    for method, version, _, _ in rows:
        # The library grid needs only summary fields. Instructions, cues,
        # constraints and other large content load from the detail endpoint.
        items.append({
            "id": method.id,
            "code": method.code,
            "content_version": version.content_version,
            "canonical_name": version.canonical_name,
            "method_type": version.method_type,
            "movement_pattern": version.movement_pattern,
            "environments": version.environments,
            "technical_cost": version.technical_cost,
            "impact_cost": version.impact_cost,
            "fatigue_cost": version.fatigue_cost,
            "status": version.status,
            "generator_eligible": version.generator_eligible,
            "archived": method.archived,
            "identity_version": method.version,
        })
    return {
        "items": items,
        "next_cursor": encode_cursor(rows[-1][0].created_at, rows[-1][0].id) if len(fetched) > limit else None,
        "summary": {
            "total": total,
            "generator_eligible": generator_eligible,
            "needs_completion": total - generator_eligible,
        },
    }


@router.get("/methods/{method_id}")
async def get_method(method_id: UUID, content_version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    method = await session.get(Method, method_id)
    if method is None:
        raise ProblemError(404, "method_not_found", "Method not found", "The method does not exist.")
    view = await _method_view(session, method, content_version)
    effects = (await session.scalars(select(MethodEffect).where(MethodEffect.method_id == method_id, MethodEffect.method_version == view.content_version).order_by(MethodEffect.is_primary.desc(), MethodEffect.quality_code))).all()
    constraints = (await session.scalars(select(MethodConstraint).where(MethodConstraint.method_id == method_id, MethodConstraint.method_version == view.content_version).order_by(MethodConstraint.code))).all()
    relations = (await session.scalars(select(MethodRelation).where(or_(MethodRelation.from_method_id == method_id, MethodRelation.to_method_id == method_id)).order_by(MethodRelation.relation_type))).all()
    return {**view.model_dump(), "effects": [model_dict(row) for row in effects], "constraints": [model_dict(row) for row in constraints], "relations": [model_dict(row) for row in relations]}


@router.post("/methods", status_code=201)
async def create_method(body: MethodCreate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if await session.scalar(select(Method.id).where(Method.code == body.code)):
        raise ProblemError(409, "method_code_exists", "Method exists", "Choose a unique stable method code.")
    now = _now()
    method = Method(code=body.code, latest_version=1, archived=False)
    session.add(method)
    await session.flush()
    values = body.model_dump(exclude={"code", "aliases"})
    version = MethodVersion(method_id=method.id, content_version=1, status="draft", generator_eligible=False, created_at=now, updated_at=now, record_version=1, **values)
    session.add(version)
    session.add_all(MethodAlias(method_id=method.id, alias=alias, normalized_alias=alias.strip().casefold()) for alias in dict.fromkeys(body.aliases))
    await _audit(session, actor, "knowledge.method.created", "method", method.id, after={"code": method.code, "content_version": 1})
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409, "method_conflict", "Method conflict", "The code or an alias is already in use.") from exc
    return (await _method_view(session, method)).model_dump()


@router.put("/methods/{method_id}/versions/{content_version}")
async def update_method(method_id: UUID, content_version: int, body: MethodUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    method, row = await _method_version(session, method_id, content_version, lock=True)
    if row.status == "released":
        raise ProblemError(409, "released_content_immutable", "Released content is immutable", "Create a new content version.")
    if row.record_version != body.expected_record_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the method and try again.")
    before = model_dict(row)
    for key, value in body.model_dump(exclude={"expected_record_version"}).items():
        setattr(row, key, value)
    row.updated_at = _now()
    row.record_version += 1
    try:
        await _validate_and_approve_method(session, row)
    except KnowledgeValidationError as exc:
        await session.rollback()
        raise _problem(exc, code="method_validation_failed", title="Exercise is incomplete") from exc
    await _audit(session, actor, "knowledge.method.updated", "method", method.id, before=before, after=model_dict(row))
    await session.commit()
    return (await _method_view(session, method, content_version)).model_dump()


@router.put("/methods/{method_id}/aliases")
async def replace_method_aliases(method_id: UUID, body: MethodAliasesUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    method = await session.get(Method, method_id, with_for_update=True)
    if method is None:
        raise ProblemError(404, "method_not_found", "Exercise not found", "The exercise does not exist.")
    if method.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the exercise and try again.")
    cleaned = list(dict.fromkeys(alias.strip() for alias in body.aliases if alias.strip()))
    await session.execute(delete(MethodAlias).where(MethodAlias.method_id == method_id))
    session.add_all(MethodAlias(method_id=method_id, alias=alias, normalized_alias=alias.casefold()) for alias in cleaned)
    method.version += 1
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409, "method_alias_conflict", "Alias already used", "One of these alternative names belongs to another exercise.") from exc
    return {"items": cleaned, "version": method.version}


@router.put("/methods/{method_id}/archive")
async def archive_method(method_id: UUID, body: MethodArchiveCommand, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    method = await session.get(Method, method_id, with_for_update=True)
    if method is None:
        raise ProblemError(404, "method_not_found", "Exercise not found", "The exercise does not exist.")
    if method.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the exercise and try again.")
    method.archived = body.archived
    method.version += 1
    version = await session.scalar(select(MethodVersion).where(MethodVersion.method_id == method_id, MethodVersion.content_version == method.latest_version))
    if version is not None:
        version.generator_eligible = not body.archived
        version.status = "retired" if body.archived else "catalogue_validated"
        version.record_version += 1
        version.updated_at = _now()
    await _audit(session, actor, "knowledge.method.archived" if body.archived else "knowledge.method.restored", "method", method_id, after={"archived": body.archived})
    await session.commit()
    return {"id": method.id, "archived": method.archived, "version": method.version}


@router.post("/methods/{method_id}/versions", status_code=201)
async def create_method_version(method_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    method = await session.get(Method, method_id, with_for_update=True)
    if method is None:
        raise ProblemError(404, "method_not_found", "Method not found", "The method does not exist.")
    source = await session.scalar(select(MethodVersion).where(MethodVersion.method_id == method_id, MethodVersion.content_version == method.latest_version))
    if source is None or source.status not in {"released", "retired"}:
        raise ProblemError(409, "draft_version_exists", "Draft version exists", "Publish or retire the current version first.")
    new_version = method.latest_version + 1
    values = model_dict(source)
    for key in ("method_id", "content_version", "created_at", "updated_at", "record_version", "status", "generator_eligible"):
        values.pop(key, None)
    now = _now()
    row = MethodVersion(method_id=method.id, content_version=new_version, status="draft", generator_eligible=False, created_at=now, updated_at=now, record_version=1, **values)
    session.add(row)
    method.latest_version = new_version
    method.version += 1
    old_effects = (await session.scalars(select(MethodEffect).where(MethodEffect.method_id == method.id, MethodEffect.method_version == source.content_version))).all()
    session.add_all(MethodEffect(method_id=method.id, method_version=new_version, quality_code=item.quality_code, is_primary=item.is_primary, training_role=item.training_role, magnitude=item.magnitude, confidence=item.confidence, evidence_claim_id=item.evidence_claim_id, evidence_claim_version=item.evidence_claim_version) for item in old_effects)
    await _audit(session, actor, "knowledge.method.version_created", "method", method.id, after={"content_version": new_version})
    await session.commit()
    return (await _method_view(session, method, new_version)).model_dump()


@router.get("/methods/{method_id}/versions")
async def list_method_versions(method_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    method = await session.get(Method, method_id)
    if method is None:
        raise ProblemError(404, "method_not_found", "Exercise not found", "The exercise does not exist.")
    rows = (await session.scalars(select(MethodVersion).where(MethodVersion.method_id == method_id).order_by(MethodVersion.content_version.desc()))).all()
    return {"items": [{"content_version": row.content_version, "canonical_name": row.canonical_name, "status": row.status,
        "generator_eligible": row.generator_eligible, "created_at": row.created_at, "updated_at": row.updated_at,
        "record_version": row.record_version} for row in rows]}


@router.put("/methods/{method_id}/versions/{content_version}/effects")
async def replace_effects(method_id: UUID, content_version: int, body: list[EffectDraft], actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    _, method = await _method_version(session, method_id, content_version, lock=True)
    if method.status == "released":
        raise ProblemError(409, "released_content_immutable", "Released content is immutable", "Create a new content version.")
    await _require_claim_refs(session, {(item.evidence_claim_id, item.evidence_claim_version) for item in body})
    rows = [MethodEffect(method_id=method_id, method_version=content_version, **item.model_dump()) for item in body]
    constraints = (await session.scalars(select(MethodConstraint).where(MethodConstraint.method_id == method_id, MethodConstraint.method_version == content_version))).all()
    try:
        validate_method(method, rows, constraints)
    except KnowledgeValidationError as exc:
        raise _problem(exc, code="method_validation_failed", title="Method validation failed") from exc
    await session.execute(delete(MethodEffect).where(MethodEffect.method_id == method_id, MethodEffect.method_version == content_version))
    session.add_all(rows)
    method.status = "catalogue_validated"
    method.generator_eligible = True
    method.record_version += 1
    method.updated_at = _now()
    await _audit(session, actor, "knowledge.method.effects_replaced", "method", method_id, after={"content_version": content_version, "effect_count": len(rows)})
    await session.commit()
    return {"items": [item.model_dump() for item in body]}


@router.put("/methods/{method_id}/versions/{content_version}/constraints")
async def replace_constraints(method_id: UUID, content_version: int, body: list[ConstraintDraft], actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    _, method = await _method_version(session, method_id, content_version, lock=True)
    if method.status == "released":
        raise ProblemError(409, "released_content_immutable", "Released content is immutable", "Create a new content version.")
    await _require_claim_refs(session, {(item.evidence_claim_id, item.evidence_claim_version) for item in body if item.evidence_claim_id is not None and item.evidence_claim_version is not None})
    await session.execute(delete(MethodConstraint).where(MethodConstraint.method_id == method_id, MethodConstraint.method_version == content_version))
    rows = [MethodConstraint(method_id=method_id, method_version=content_version, **item.model_dump()) for item in body]
    session.add_all(rows)
    effects = (await session.scalars(select(MethodEffect).where(MethodEffect.method_id == method_id, MethodEffect.method_version == content_version))).all()
    try:
        validate_method(method, effects, rows)
    except KnowledgeValidationError as exc:
        await session.rollback()
        raise _problem(exc, code="method_validation_failed", title="Exercise is incomplete") from exc
    method.status = "catalogue_validated"
    method.generator_eligible = True
    method.record_version += 1
    method.updated_at = _now()
    await _audit(session, actor, "knowledge.method.constraints_replaced", "method", method_id, after={"content_version": content_version, "constraint_count": len(rows)})
    await session.commit()
    return {"items": [model_dict(row) for row in rows]}


@router.get("/methods/{method_id}/versions/{content_version}/media")
async def list_method_media(method_id: UUID, content_version: int, session: AsyncSession = Depends(get_session)) -> dict:
    await _method_version(session,method_id,content_version)
    rows=(await session.scalars(select(MethodMedia).where(MethodMedia.method_id==method_id,MethodMedia.method_version==content_version).order_by(MethodMedia.created_at))).all()
    return {"items":[model_dict(row) for row in rows]}


@router.post("/methods/{method_id}/versions/{content_version}/media/upload-url")
async def method_media_upload_url(method_id: UUID, content_version: int, body: dict, session: AsyncSession = Depends(get_session)) -> dict:
    await _method_version(session, method_id, content_version)
    content_type = str(body.get("content_type", ""))
    if not (content_type.startswith("image/") or content_type.startswith("video/")):
        raise ProblemError(422, "media_type_invalid", "Invalid media", "Choose an image or video file.")
    extension = str(body.get("file_name", "file")).rsplit(".", 1)[-1].lower()[:10]
    settings = get_settings()
    bucket = settings.exercise_media_bucket
    if not bucket:
        raise ProblemError(503, "storage_unavailable", "Storage unavailable", "Exercise media storage is not configured.")
    object_name = f"methods/{method_id}/v{content_version}/{uuid7()}.{extension}"
    try:
        upload_url = await signed_gcs_url(project_id=settings.gcp_project_id, bucket=bucket, object_name=object_name, method="PUT", content_type=content_type)
    except Exception as exc:
        raise ProblemError(503, "storage_signing_failed", "Upload unavailable", "Could not prepare the media upload.") from exc
    return {"upload_url": upload_url, "bucket": bucket, "object_name": object_name, "media_type": "image" if content_type.startswith("image/") else "video"}


@router.post("/methods/{method_id}/versions/{content_version}/media", status_code=201)
async def create_method_media(method_id: UUID, content_version: int, body: MethodMediaDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    _,method=await _method_version(session,method_id,content_version,lock=True)
    if method.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new method version.")
    row=MethodMedia(method_id=method_id,method_version=content_version,**body.model_dump()); session.add(row); method.record_version+=1; method.updated_at=_now(); await session.flush(); await _audit(session,actor,"knowledge.method_media.created","method_media",row.id,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.delete("/methods/{method_id}/versions/{content_version}/media/{media_id}", status_code=204)
async def delete_method_media(method_id: UUID, content_version: int, media_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> Response:
    _,method=await _method_version(session,method_id,content_version,lock=True)
    if method.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new method version.")
    row=await session.scalar(select(MethodMedia).where(MethodMedia.id==media_id,MethodMedia.method_id==method_id,MethodMedia.method_version==content_version).with_for_update())
    if row is None: return Response(status_code=204)
    before=model_dict(row); await session.delete(row); method.record_version+=1; method.updated_at=_now(); await _audit(session,actor,"knowledge.method_media.deleted","method_media",media_id,before=before); await session.commit()
    return Response(status_code=204)


@router.post("/relations", status_code=201)
async def create_relation(body: RelationCreate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if body.from_method_id == body.to_method_id:
        raise ProblemError(422, "relation_invalid", "Invalid relation", "A method cannot relate to itself.")
    if body.evidence_claim_id is not None and body.evidence_claim_version is not None:
        await _require_claim_refs(session, {(body.evidence_claim_id, body.evidence_claim_version)})
    row = MethodRelation(**body.model_dump(), status="draft")
    session.add(row)
    await session.flush()
    relations = (await session.scalars(select(MethodRelation).where(MethodRelation.status != "retired"))).all()
    try:
        validate_progression_dag(relations)
    except KnowledgeValidationError as exc:
        await session.rollback()
        raise _problem(exc, code="progression_cycle", title="Invalid progression graph") from exc
    await _audit(session, actor, "knowledge.method_relation.created", "method_relation", row.id, after=model_dict(row))
    await session.commit()
    return model_dict(row)


@router.put("/relations/{relation_id}")
async def update_relation(relation_id: UUID, body: RelationUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(MethodRelation,relation_id,with_for_update=True)
    if row is None: raise ProblemError(404,"relation_not_found","Relation not found","The method relation does not exist.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a replacement relation in a future release.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the relation and try again.")
    if body.from_method_id==body.to_method_id: raise ProblemError(422,"relation_invalid","Invalid relation","A method cannot relate to itself.")
    if body.evidence_claim_id and body.evidence_claim_version: await _require_claim_refs(session,{(body.evidence_claim_id,body.evidence_claim_version)})
    before=model_dict(row)
    for key,value in body.model_dump(exclude={"expected_version"}).items(): setattr(row,key,value)
    row.status="draft"; row.version+=1
    relations=(await session.scalars(select(MethodRelation).where(MethodRelation.status!="retired"))).all()
    try: validate_progression_dag(relations)
    except KnowledgeValidationError as exc: raise _problem(exc,code="progression_cycle",title="Invalid progression graph") from exc
    await _audit(session,actor,"knowledge.method_relation.updated","method_relation",relation_id,before=before,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.get("/evidence/sources")
async def list_evidence_sources(cursor: str | None = None, limit: int = Query(default=25, ge=1, le=100), session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(EvidenceSource).order_by(EvidenceSource.created_at.desc(), EvidenceSource.id.desc())
    if cursor:
        created_at, entity_id = decode_cursor(cursor)
        statement = statement.where(or_(EvidenceSource.created_at < created_at, and_(EvidenceSource.created_at == created_at, EvidenceSource.id < entity_id)))
    fetched = (await session.scalars(statement.limit(limit + 1))).all(); rows = fetched[:limit]
    return {"items": [model_dict(row) for row in rows], "next_cursor": encode_cursor(rows[-1].created_at, rows[-1].id) if len(fetched) > limit else None}


@router.post("/evidence/sources", status_code=201)
async def create_evidence_source(body: EvidenceSourceDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row = EvidenceSource(**body.model_dump()); session.add(row); await session.flush()
    await _audit(session, actor, "knowledge.evidence_source.created", "evidence_source", row.id, after=model_dict(row)); await session.commit(); return model_dict(row)


@router.get("/evidence/claims")
async def list_evidence_claims(cursor: str | None = None, limit: int = Query(default=25, ge=1, le=100), session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(EvidenceClaim, EvidenceClaimVersion).join(EvidenceClaimVersion, and_(EvidenceClaimVersion.claim_id == EvidenceClaim.id, EvidenceClaimVersion.claim_version == EvidenceClaim.latest_version)).order_by(EvidenceClaim.created_at.desc(), EvidenceClaim.id.desc())
    if cursor:
        created_at, entity_id = decode_cursor(cursor); statement = statement.where(or_(EvidenceClaim.created_at < created_at, and_(EvidenceClaim.created_at == created_at, EvidenceClaim.id < entity_id)))
    fetched = (await session.execute(statement.limit(limit + 1))).all(); rows = fetched[:limit]
    return {"items": [{"id": identity.id, "code": identity.code, **model_dict(version)} for identity, version in rows], "next_cursor": encode_cursor(rows[-1][0].created_at, rows[-1][0].id) if len(fetched) > limit else None}


@router.get("/evidence/claims/{claim_id}")
async def get_evidence_claim(claim_id: UUID, claim_version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(EvidenceClaim,claim_id)
    if identity is None: raise ProblemError(404,"evidence_claim_not_found","Evidence claim not found","The evidence claim does not exist.")
    version=claim_version or identity.latest_version; row=await session.scalar(select(EvidenceClaimVersion).where(EvidenceClaimVersion.claim_id==claim_id,EvidenceClaimVersion.claim_version==version))
    if row is None: raise ProblemError(404,"evidence_claim_version_not_found","Evidence claim version not found","The evidence claim version does not exist.")
    sources=(await session.scalars(select(EvidenceClaimSource).where(EvidenceClaimSource.claim_id==claim_id,EvidenceClaimSource.claim_version==version))).all()
    return {"id":claim_id,"code":identity.code,**model_dict(row),"source_ids":[item.source_id for item in sources]}


@router.post("/evidence/claims", status_code=201)
async def create_evidence_claim(body: EvidenceClaimDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if len(set(body.source_ids)) != len(body.source_ids):
        raise ProblemError(422, "duplicate_source", "Duplicate source", "Evidence source IDs must be unique.")
    found = set((await session.scalars(select(EvidenceSource.id).where(EvidenceSource.id.in_(body.source_ids)))).all())
    if found != set(body.source_ids):
        raise ProblemError(422, "evidence_source_missing", "Evidence source missing", "One or more evidence sources do not exist.")
    values = body.model_dump(exclude={"source_ids", "code"}); identity = EvidenceClaim(code=body.code, latest_version=1); session.add(identity); await session.flush(); now = _now()
    row = EvidenceClaimVersion(claim_id=identity.id, claim_version=1, status="draft", created_at=now, updated_at=now, record_version=1, **values); session.add(row); await session.flush()
    session.add_all(EvidenceClaimSource(claim_id=identity.id, claim_version=1, source_id=source_id, support_type="supports") for source_id in body.source_ids)
    await _audit(session, actor, "knowledge.evidence_claim.created", "evidence_claim", identity.id, after={"code": body.code, **model_dict(row)}); await session.commit(); return {"id": identity.id, "code": identity.code, **model_dict(row)}


@router.post("/evidence/claims/{claim_id}/versions", status_code=201)
async def create_evidence_claim_version(claim_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(EvidenceClaim,claim_id,with_for_update=True)
    if identity is None: raise ProblemError(404,"evidence_claim_not_found","Evidence claim not found","The evidence claim does not exist.")
    source=await session.scalar(select(EvidenceClaimVersion).where(EvidenceClaimVersion.claim_id==claim_id,EvidenceClaimVersion.claim_version==identity.latest_version))
    if source is None or source.status not in {"released","retired"}: raise ProblemError(409,"draft_version_exists","Draft version exists","Publish or retire the current version first.")
    version=identity.latest_version+1; values=model_dict(source)
    for key in ("claim_id","claim_version","status","created_at","updated_at","record_version"): values.pop(key,None)
    now=_now(); row=EvidenceClaimVersion(claim_id=claim_id,claim_version=version,status="draft",created_at=now,updated_at=now,record_version=1,**values); session.add(row)
    links=(await session.scalars(select(EvidenceClaimSource).where(EvidenceClaimSource.claim_id==claim_id,EvidenceClaimSource.claim_version==source.claim_version))).all()
    session.add_all(EvidenceClaimSource(claim_id=claim_id,claim_version=version,source_id=item.source_id,support_type=item.support_type) for item in links)
    identity.latest_version=version; identity.version+=1; await _audit(session,actor,"knowledge.evidence_claim.version_created","evidence_claim",claim_id,after={"claim_version":version}); await session.commit()
    return {"id":claim_id,"code":identity.code,**model_dict(row)}


@router.put("/evidence/claims/{claim_id}/versions/{claim_version}")
async def update_evidence_claim(claim_id: UUID, claim_version: int, body: EvidenceClaimUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(EvidenceClaim,claim_id); row=await session.scalar(select(EvidenceClaimVersion).where(EvidenceClaimVersion.claim_id==claim_id,EvidenceClaimVersion.claim_version==claim_version).with_for_update())
    if identity is None or row is None: raise ProblemError(404,"evidence_claim_not_found","Evidence claim not found","The evidence claim version does not exist.")
    if identity.code!=body.code: raise ProblemError(409,"stable_code_immutable","Stable code is immutable","Create a different claim for a different code.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new content version.")
    if row.record_version!=body.expected_record_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the claim and try again.")
    found=set((await session.scalars(select(EvidenceSource.id).where(EvidenceSource.id.in_(body.source_ids)))).all())
    if found!=set(body.source_ids): raise ProblemError(422,"evidence_source_missing","Evidence source missing","One or more evidence sources do not exist.")
    before=model_dict(row)
    for key,value in body.model_dump(exclude={"code","source_ids","expected_record_version"}).items(): setattr(row,key,value)
    row.status="draft"; row.record_version+=1; row.updated_at=_now()
    await session.execute(delete(EvidenceClaimSource).where(EvidenceClaimSource.claim_id==claim_id,EvidenceClaimSource.claim_version==claim_version))
    session.add_all(EvidenceClaimSource(claim_id=claim_id,claim_version=claim_version,source_id=value,support_type="supports") for value in dict.fromkeys(body.source_ids))
    await _audit(session,actor,"knowledge.evidence_claim.updated","evidence_claim",claim_id,before=before,after=model_dict(row)); await session.commit(); return {"id":claim_id,"code":identity.code,**model_dict(row)}


@router.post("/reviews", status_code=201)
async def create_review(body: ReviewCreate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row = ContentReview(**body.model_dump(), reviewer_user_id=actor, decided_at=_now()); session.add(row)
    if body.decision == "approved":
        if body.entity_type == "method":
            method = await session.scalar(select(MethodVersion).where(MethodVersion.method_id == body.entity_id, MethodVersion.content_version == body.entity_version).with_for_update())
            if method is None: raise ProblemError(404, "review_target_not_found", "Review target not found", "The method version does not exist.")
            effects = (await session.scalars(select(MethodEffect).where(MethodEffect.method_id == body.entity_id, MethodEffect.method_version == body.entity_version))).all()
            constraints = (await session.scalars(select(MethodConstraint).where(MethodConstraint.method_id == body.entity_id, MethodConstraint.method_version == body.entity_version))).all()
            try: validate_method(method, effects, constraints)
            except KnowledgeValidationError as exc: raise _problem(exc, code="review_gate_failed", title="Review gate failed") from exc
            method.status = "evidence_verified"; method.record_version += 1; method.updated_at = _now()
        elif body.entity_type == "evidence_claim":
            target = await session.scalar(select(EvidenceClaimVersion).where(EvidenceClaimVersion.claim_id == body.entity_id, EvidenceClaimVersion.claim_version == body.entity_version).with_for_update())
            if target is None: raise ProblemError(404, "review_target_not_found", "Review target not found", "The evidence claim version does not exist.")
            target.status = "evidence_verified"; target.record_version += 1; target.updated_at = _now()
        elif body.entity_type == "prescription_rule":
            target = await session.scalar(select(PrescriptionRuleVersion).where(PrescriptionRuleVersion.rule_id == body.entity_id, PrescriptionRuleVersion.rule_version == body.entity_version).with_for_update())
            if target is None: raise ProblemError(404, "review_target_not_found", "Review target not found", "The rule version does not exist.")
            try: validate_prescription_rule(target)
            except KnowledgeValidationError as exc: raise _problem(exc, code="review_gate_failed", title="Review gate failed") from exc
            if not await session.scalar(select(func.count()).select_from(PrescriptionRuleEvidenceClaim).where(PrescriptionRuleEvidenceClaim.rule_id == body.entity_id, PrescriptionRuleEvidenceClaim.rule_version == body.entity_version)): raise ProblemError(422,"review_gate_failed","Review gate failed","The rule has no version-pinned evidence claim.")
            target.status = "evidence_verified"; target.record_version += 1; target.updated_at = _now()
        elif body.entity_type == "recipe":
            target = await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id == body.entity_id, RecipeVersion.recipe_version == body.entity_version).with_for_update())
            if target is None: raise ProblemError(404, "review_target_not_found", "Review target not found", "The recipe version does not exist.")
            blocks = (await session.scalars(select(RecipeBlock).where(RecipeBlock.recipe_id == body.entity_id, RecipeBlock.recipe_version == body.entity_version))).all(); slots_by_block = defaultdict(list)
            if blocks:
                for item in (await session.scalars(select(RecipeSlot).where(RecipeSlot.block_id.in_([block.id for block in blocks])))).all(): slots_by_block[item.block_id].append(item)
            try: validate_recipe(target, blocks, slots_by_block)
            except KnowledgeValidationError as exc: raise _problem(exc, code="review_gate_failed", title="Review gate failed") from exc
            target.status = "evidence_verified"; target.record_version += 1; target.updated_at = _now()
        elif body.entity_type == "demand_fact":
            target = await session.scalar(select(DemandFactVersion).where(DemandFactVersion.demand_fact_id == body.entity_id, DemandFactVersion.fact_version == body.entity_version).with_for_update())
            if target is None: raise ProblemError(404, "review_target_not_found", "Review target not found", "The demand fact version does not exist.")
            target.status = "evidence_verified"; target.record_version += 1; target.updated_at = _now()
        elif body.entity_type == "program_archetype":
            target = await session.scalar(select(ProgramArchetypeVersion).where(ProgramArchetypeVersion.archetype_id == body.entity_id, ProgramArchetypeVersion.content_version == body.entity_version).with_for_update())
            if target is None: raise ProblemError(404, "review_target_not_found", "Review target not found", "The program archetype version does not exist.")
            target.status = "evidence_verified"; target.record_version += 1; target.updated_at = _now()
        elif body.entity_type in {"physical_quality", "sport_taxon", "sport_quality_priority", "week_template", "method_relation"}:
            model = {
                "physical_quality": PhysicalQuality,
                "sport_taxon": SportTaxon,
                "sport_quality_priority": SportQualityPriority,
                "week_template": WeekTemplate,
                "method_relation": MethodRelation,
            }[body.entity_type]
            target = await session.get(model, body.entity_id, with_for_update=True)
            if target is None or target.version != body.entity_version: raise ProblemError(404, "review_target_not_found", "Review target not found", "The content record or version does not exist.")
            target.status = "evidence_verified"; target.version += 1
        else:
            raise ProblemError(422, "unsupported_review_target", "Unsupported review target", "This content type cannot enter a release through the review workflow.")
    await _audit(session, actor, "knowledge.content_review.recorded", body.entity_type, body.entity_id, after=body.model_dump(mode="json")); await session.commit(); return model_dict(row)


@router.get("/reviews")
async def list_reviews(entity_type: str | None = None, decision: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement=select(ContentReview).order_by(ContentReview.decided_at.desc()).limit(250)
    if entity_type: statement=statement.where(ContentReview.entity_type==entity_type)
    if decision: statement=statement.where(ContentReview.decision==decision)
    return {"items":[model_dict(row) for row in (await session.scalars(statement)).all()]}


@router.get("/terms")
async def list_terms(category: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(KnowledgeTerm).order_by(KnowledgeTerm.category, KnowledgeTerm.code)
    if category: statement = statement.where(KnowledgeTerm.category == category)
    return {"items": [model_dict(row) for row in (await session.scalars(statement)).all()]}


@router.post("/terms", status_code=201)
async def create_term(body: TermDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row = KnowledgeTerm(**body.model_dump(), status="draft"); session.add(row); await session.flush(); await _audit(session, actor, "knowledge.term.created", "term", row.id, after=model_dict(row)); await session.commit(); return model_dict(row)


@router.put("/terms/{term_id}")
async def update_term(term_id: UUID, body: TermUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(KnowledgeTerm,term_id,with_for_update=True)
    if row is None: raise ProblemError(404,"term_not_found","Term not found","The controlled term does not exist.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a replacement through a future schema release.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the term and try again.")
    if (row.category,row.code)!=(body.category,body.code): raise ProblemError(409,"stable_identity_immutable","Stable identity is immutable","Category and code cannot be changed.")
    before=model_dict(row); row.name=body.name; row.description=body.description; row.status="draft"; row.version+=1; await _audit(session,actor,"knowledge.term.updated","term",row.id,before=before,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.post("/qualities", status_code=201)
async def create_quality(body: PhysicalQualityDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row = PhysicalQuality(**body.model_dump(), status="draft"); session.add(row); await session.flush(); await _audit(session, actor, "knowledge.quality.created", "physical_quality", row.id, after=model_dict(row)); await session.commit(); return model_dict(row)


@router.put("/qualities/{quality_id}")
async def update_quality(quality_id: UUID, body: PhysicalQualityUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(PhysicalQuality,quality_id,with_for_update=True)
    if row is None: raise ProblemError(404,"quality_not_found","Quality not found","The physical quality does not exist.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a replacement through a future schema release.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the quality and try again.")
    if row.code!=body.code: raise ProblemError(409,"stable_code_immutable","Stable code is immutable","The quality code cannot be changed.")
    before=model_dict(row); row.name=body.name; row.category=body.category; row.description=body.description; row.status="draft"; row.version+=1; await _audit(session,actor,"knowledge.quality.updated","physical_quality",row.id,before=before,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.get("/qualities")
async def list_qualities(session: AsyncSession = Depends(get_session)) -> dict:
    return {"items": [model_dict(row) for row in (await session.scalars(select(PhysicalQuality).order_by(PhysicalQuality.category, PhysicalQuality.code))).all()]}


@router.get("/sports")
async def list_sports(session: AsyncSession = Depends(get_session)) -> dict:
    return {"items": [model_dict(row) for row in (await session.scalars(select(SportTaxon).order_by(SportTaxon.sport_code, SportTaxon.taxon_type, SportTaxon.name))).all()]}


@router.post("/sports", status_code=201)
async def create_sport_taxon(body: SportTaxonDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row = SportTaxon(**body.model_dump(), status="draft"); session.add(row); await session.flush(); await _audit(session, actor, "knowledge.sport_taxon.created", "sport_taxon", row.id, after=model_dict(row)); await session.commit(); return model_dict(row)


@router.put("/sports/{taxon_id}")
async def update_sport_taxon(taxon_id: UUID, body: SportTaxonUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(SportTaxon,taxon_id,with_for_update=True)
    if row is None: raise ProblemError(404,"sport_taxon_not_found","Sport scope not found","The sport scope does not exist.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a replacement through a future taxonomy release.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the sport scope and try again.")
    if (row.code,row.taxon_type,row.sport_code)!=(body.code,body.taxon_type,body.sport_code): raise ProblemError(409,"stable_identity_immutable","Stable identity is immutable","Code, type and owning sport cannot be changed.")
    before=model_dict(row); row.name=body.name; row.parent_id=body.parent_id; row.visible=body.visible; row.status="draft"; row.version+=1; await _audit(session,actor,"knowledge.sport_taxon.updated","sport_taxon",row.id,before=before,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.post("/demands", status_code=201)
async def create_demand(body: DemandFactDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    await _require_claim_refs(session, {(body.evidence_claim_id, body.evidence_claim_version)})
    values = body.model_dump(exclude={"code"}); identity = DemandFact(code=body.code, latest_version=1); session.add(identity); await session.flush(); now = _now(); row = DemandFactVersion(demand_fact_id=identity.id, fact_version=1, status="draft", created_at=now, updated_at=now, record_version=1, **values); session.add(row); await _audit(session, actor, "knowledge.demand_fact.created", "demand_fact", identity.id, after={"code": body.code, **values}); await session.commit(); return {"id": identity.id, "fact_version": 1, **values, "status": "draft"}


@router.get("/demands")
async def list_demands(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(DemandFact, DemandFactVersion, EvidenceClaim.code).join(DemandFactVersion, and_(DemandFactVersion.demand_fact_id == DemandFact.id, DemandFactVersion.fact_version == DemandFact.latest_version)).join(EvidenceClaim, EvidenceClaim.id == DemandFactVersion.evidence_claim_id).order_by(DemandFact.code)
    if sport_code: statement = statement.where(DemandFactVersion.sport_code == sport_code)
    rows = (await session.execute(statement)).all()
    return {"items": [{"id": identity.id, "code": identity.code, "evidence_claim_code": claim_code, **model_dict(version)} for identity, version, claim_code in rows]}


@router.get("/demands/{demand_id}")
async def get_demand(demand_id: UUID, fact_version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(DemandFact,demand_id)
    if identity is None: raise ProblemError(404,"demand_not_found","Demand not found","The demand fact does not exist.")
    version=fact_version or identity.latest_version; row=await session.scalar(select(DemandFactVersion).where(DemandFactVersion.demand_fact_id==demand_id,DemandFactVersion.fact_version==version))
    if row is None: raise ProblemError(404,"demand_version_not_found","Demand version not found","The demand fact version does not exist.")
    return {"id":demand_id,"code":identity.code,**model_dict(row)}


@router.post("/demands/{demand_id}/versions", status_code=201)
async def create_demand_version(demand_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(DemandFact,demand_id,with_for_update=True)
    if identity is None: raise ProblemError(404,"demand_not_found","Demand not found","The demand fact does not exist.")
    source=await session.scalar(select(DemandFactVersion).where(DemandFactVersion.demand_fact_id==demand_id,DemandFactVersion.fact_version==identity.latest_version))
    if source is None or source.status not in {"released","retired"}: raise ProblemError(409,"draft_version_exists","Draft version exists","Publish or retire the current version first.")
    version=identity.latest_version+1; values=model_dict(source)
    for key in ("demand_fact_id","fact_version","status","created_at","updated_at","record_version"): values.pop(key,None)
    now=_now(); row=DemandFactVersion(demand_fact_id=demand_id,fact_version=version,status="draft",created_at=now,updated_at=now,record_version=1,**values); session.add(row); identity.latest_version=version; identity.version+=1
    await _audit(session,actor,"knowledge.demand_fact.version_created","demand_fact",demand_id,after={"fact_version":version}); await session.commit(); return {"id":demand_id,"code":identity.code,**model_dict(row)}


@router.put("/demands/{demand_id}/versions/{fact_version}")
async def update_demand(demand_id: UUID, fact_version: int, body: DemandFactUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(DemandFact,demand_id); row=await session.scalar(select(DemandFactVersion).where(DemandFactVersion.demand_fact_id==demand_id,DemandFactVersion.fact_version==fact_version).with_for_update())
    if identity is None or row is None: raise ProblemError(404,"demand_not_found","Demand not found","The demand fact version does not exist.")
    if identity.code!=body.code: raise ProblemError(409,"stable_code_immutable","Stable code is immutable","Create a different demand fact for a different code.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new content version.")
    if row.record_version!=body.expected_record_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the demand and try again.")
    await _require_claim_refs(session,{(body.evidence_claim_id,body.evidence_claim_version)}); before=model_dict(row)
    for key,value in body.model_dump(exclude={"code","expected_record_version"}).items(): setattr(row,key,value)
    row.status="draft"; row.record_version+=1; row.updated_at=_now(); await _audit(session,actor,"knowledge.demand_fact.updated","demand_fact",demand_id,before=before,after=model_dict(row)); await session.commit(); return {"id":demand_id,"code":identity.code,**model_dict(row)}


@router.post("/quality-priorities", status_code=201)
async def create_priority(body: QualityPriorityDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    await _require_claim_refs(session, {(body.evidence_claim_id, body.evidence_claim_version)})
    row = SportQualityPriority(**body.model_dump(), status="draft"); session.add(row); await session.flush(); await _audit(session, actor, "knowledge.quality_priority.created", "sport_quality_priority", row.id, after=model_dict(row)); await session.commit(); return model_dict(row)


@router.put("/quality-priorities/{priority_id}")
async def update_priority(priority_id: UUID, body: QualityPriorityUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(SportQualityPriority,priority_id,with_for_update=True)
    if row is None: raise ProblemError(404,"priority_not_found","Priority not found","The sport quality priority does not exist.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a replacement in a future release.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the priority and try again.")
    await _require_claim_refs(session,{(body.evidence_claim_id,body.evidence_claim_version)}); before=model_dict(row)
    for key,value in body.model_dump(exclude={"expected_version"}).items(): setattr(row,key,value)
    row.status="draft"; row.version+=1; await _audit(session,actor,"knowledge.quality_priority.updated","sport_quality_priority",row.id,before=before,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.get("/quality-priorities")
async def list_priorities(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(SportQualityPriority).order_by(SportQualityPriority.sport_code, SportQualityPriority.phase_code, SportQualityPriority.quality_code)
    if sport_code: statement = statement.where(SportQualityPriority.sport_code == sport_code)
    return {"items": [model_dict(row) for row in (await session.scalars(statement)).all()]}


@router.post("/rules", status_code=201)
async def create_rule(body: RuleDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    requested={(ref.id,ref.version) for ref in body.evidence_claims}; await _require_claim_refs(session, requested)
    values = body.model_dump(exclude={"code", "evidence_claims"}); identity = PrescriptionRule(code=body.code, latest_version=1); session.add(identity); await session.flush(); now = _now(); row = PrescriptionRuleVersion(rule_id=identity.id, rule_version=1, status="draft", created_at=now, updated_at=now, record_version=1, **values)
    try: validate_prescription_rule(row)
    except KnowledgeValidationError as exc: raise _problem(exc, code="rule_validation_failed", title="Rule validation failed") from exc
    session.add(row); await session.flush(); session.add_all(PrescriptionRuleEvidenceClaim(rule_id=identity.id, rule_version=1, claim_id=ref.id, claim_version=ref.version) for ref in body.evidence_claims); await _audit(session, actor, "knowledge.rule.created", "prescription_rule", identity.id, after={"code": body.code, **values}); await session.commit(); return {"id": identity.id, "rule_version": 1, **values, "evidence_claims": body.model_dump(mode="json")["evidence_claims"], "status": "draft"}


@router.get("/rules")
async def list_rules(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(PrescriptionRule, PrescriptionRuleVersion).join(PrescriptionRuleVersion, and_(PrescriptionRuleVersion.rule_id == PrescriptionRule.id, PrescriptionRuleVersion.rule_version == PrescriptionRule.latest_version)).order_by(PrescriptionRuleVersion.priority, PrescriptionRule.code)
    if sport_code: statement = statement.where(or_(PrescriptionRuleVersion.sport_code.is_(None), PrescriptionRuleVersion.sport_code == sport_code))
    rows = (await session.execute(statement)).all()
    return {"items": [{"id": identity.id, "code": identity.code, **model_dict(version)} for identity, version in rows]}


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: UUID, rule_version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(PrescriptionRule,rule_id)
    if identity is None: raise ProblemError(404,"rule_not_found","Rule not found","The prescription rule does not exist.")
    version=rule_version or identity.latest_version; row=await session.scalar(select(PrescriptionRuleVersion).where(PrescriptionRuleVersion.rule_id==rule_id,PrescriptionRuleVersion.rule_version==version))
    if row is None: raise ProblemError(404,"rule_version_not_found","Rule version not found","The prescription rule version does not exist.")
    refs=(await session.scalars(select(PrescriptionRuleEvidenceClaim).where(PrescriptionRuleEvidenceClaim.rule_id==rule_id,PrescriptionRuleEvidenceClaim.rule_version==version))).all()
    return {"id":rule_id,"code":identity.code,**model_dict(row),"evidence_claims":[{"id":item.claim_id,"version":item.claim_version} for item in refs]}


@router.post("/rules/{rule_id}/versions", status_code=201)
async def create_rule_version(rule_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(PrescriptionRule,rule_id,with_for_update=True)
    if identity is None: raise ProblemError(404,"rule_not_found","Rule not found","The rule does not exist.")
    source=await session.scalar(select(PrescriptionRuleVersion).where(PrescriptionRuleVersion.rule_id==rule_id,PrescriptionRuleVersion.rule_version==identity.latest_version))
    if source is None or source.status not in {"released","retired"}: raise ProblemError(409,"draft_version_exists","Draft version exists","Publish or retire the current version first.")
    version=identity.latest_version+1; values=model_dict(source)
    for key in ("rule_id","rule_version","status","created_at","updated_at","record_version"): values.pop(key,None)
    now=_now(); row=PrescriptionRuleVersion(rule_id=rule_id,rule_version=version,status="draft",created_at=now,updated_at=now,record_version=1,**values); session.add(row)
    refs=(await session.scalars(select(PrescriptionRuleEvidenceClaim).where(PrescriptionRuleEvidenceClaim.rule_id==rule_id,PrescriptionRuleEvidenceClaim.rule_version==source.rule_version))).all()
    session.add_all(PrescriptionRuleEvidenceClaim(rule_id=rule_id,rule_version=version,claim_id=item.claim_id,claim_version=item.claim_version) for item in refs)
    identity.latest_version=version; identity.version+=1; await _audit(session,actor,"knowledge.rule.version_created","prescription_rule",rule_id,after={"rule_version":version}); await session.commit(); return {"id":rule_id,"code":identity.code,**model_dict(row)}


@router.put("/rules/{rule_id}/versions/{rule_version}")
async def update_rule(rule_id: UUID, rule_version: int, body: RuleUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(PrescriptionRule,rule_id); row=await session.scalar(select(PrescriptionRuleVersion).where(PrescriptionRuleVersion.rule_id==rule_id,PrescriptionRuleVersion.rule_version==rule_version).with_for_update())
    if identity is None or row is None: raise ProblemError(404,"rule_not_found","Rule not found","The rule version does not exist.")
    if identity.code!=body.code: raise ProblemError(409,"stable_code_immutable","Stable code is immutable","Create a different rule for a different code.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new content version.")
    if row.record_version!=body.expected_record_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the rule and try again.")
    refs={(item.id,item.version) for item in body.evidence_claims}; await _require_claim_refs(session,refs); before=model_dict(row)
    for key,value in body.model_dump(exclude={"code","evidence_claims","expected_record_version"}).items(): setattr(row,key,value)
    try: validate_prescription_rule(row)
    except KnowledgeValidationError as exc: raise _problem(exc,code="rule_validation_failed",title="Rule validation failed") from exc
    row.status="draft"; row.record_version+=1; row.updated_at=_now(); await session.execute(delete(PrescriptionRuleEvidenceClaim).where(PrescriptionRuleEvidenceClaim.rule_id==rule_id,PrescriptionRuleEvidenceClaim.rule_version==rule_version)); session.add_all(PrescriptionRuleEvidenceClaim(rule_id=rule_id,rule_version=rule_version,claim_id=item.id,claim_version=item.version) for item in body.evidence_claims)
    await _audit(session,actor,"knowledge.rule.updated","prescription_rule",rule_id,before=before,after=model_dict(row)); await session.commit(); return {"id":rule_id,"code":identity.code,**model_dict(row)}


@router.post("/rules/validate")
async def validate_rule(body: RuleDraft) -> dict:
    now = _now(); row = PrescriptionRuleVersion(rule_id=UUID(int=0), rule_version=1, status="draft", created_at=now, updated_at=now, record_version=1, **body.model_dump(exclude={"code", "evidence_claims"}))
    try: validate_prescription_rule(row)
    except KnowledgeValidationError as exc: raise _problem(exc, code="rule_validation_failed", title="Rule validation failed") from exc
    return {"valid": True}


@router.post("/session-recipes", status_code=201)
async def create_recipe(body: RecipeDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if await session.scalar(select(Recipe.id).where(Recipe.code == body.code)):
        raise ProblemError(409,"recipe_code_exists","Template exists","Choose a unique template code or edit the existing template.")
    values = body.model_dump(exclude={"code", "blocks"}); identity = Recipe(code=body.code, latest_version=1); session.add(identity); await session.flush(); now = _now(); version = RecipeVersion(recipe_id=identity.id, recipe_version=1, status="draft", created_at=now, updated_at=now, record_version=1, **values); session.add(version); await session.flush(); blocks=[]; slots_by_block=defaultdict(list)
    for block_index, item in enumerate(body.blocks, 1):
        block = RecipeBlock(recipe_id=identity.id, recipe_version=1, sequence=block_index, **item.model_dump(exclude={"slots"})); session.add(block); await session.flush(); blocks.append(block)
        for slot_index, slot in enumerate(item.slots, 1):
            row = RecipeSlot(block_id=block.id, sequence=slot_index, **slot.model_dump()); session.add(row); slots_by_block[block.id].append(row)
    try: validate_recipe(version, blocks, slots_by_block)
    except KnowledgeValidationError as exc: raise _problem(exc, code="recipe_validation_failed", title="Recipe validation failed") from exc
    version.status="evidence_verified"
    await _audit(session, actor, "knowledge.recipe.created", "recipe", identity.id, after={"code": body.code, "recipe_version": 1}); await session.commit(); return {"id": identity.id, "recipe_version": 1, **values, "blocks": [item.model_dump() for item in body.blocks], "status": version.status}


@router.post("/session-recipes/import-csv", status_code=201)
async def import_recipe_csv(file: UploadFile = File(...), actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    content=await file.read(5*1024*1024+1)
    try: text=content.decode("utf-8-sig")
    except UnicodeDecodeError as exc: raise ProblemError(422,"template_csv_encoding","Invalid CSV","Workout-template CSV must be UTF-8.") from exc
    import csv, io
    rows=list(csv.DictReader(io.StringIO(text)))
    required={"template_code","template_name","template_type","load_class","purpose","block_order","block_type","block_purpose","duration_minimum","duration_maximum","slot_order","slot_code","required_quality","training_role","dose_schema_json"}
    if not rows or not required.issubset(rows[0]): raise ProblemError(422,"template_csv_columns","Invalid template CSV",f"Missing columns: {sorted(required-set(rows[0] if rows else []))}")
    codes={row["template_code"].strip() for row in rows}
    if len(codes)!=1: raise ProblemError(422,"template_csv_multiple","One template per file","A template CSV must contain exactly one template code.")
    split=lambda value:[item.strip() for item in (value or "").replace("|",";").split(";") if item.strip()]
    try:
        first=rows[0]; grouped=defaultdict(list)
        for row in rows: grouped[int(row["block_order"])].append(row)
        blocks=[]
        for _,items in sorted(grouped.items()):
            head=items[0]; slots=[]
            for row in sorted(items,key=lambda value:int(value["slot_order"])):
                slots.append({"slot_code":row["slot_code"].strip(),"required_quality":row["required_quality"].strip(),"training_role":row["training_role"].strip(),"selection_constraints_json":json.loads(row.get("selection_constraints_json") or "{}"),"dose_schema_json":json.loads(row["dose_schema_json"]),"required":str(row.get("required","yes")).lower() in {"yes","true","1"}})
            blocks.append({"block_type":head["block_type"].strip(),"purpose":head["block_purpose"].strip(),"duration_minimum":int(head["duration_minimum"]),"duration_maximum":int(head["duration_maximum"]),"slots":slots})
        body=RecipeDraft(code=first["template_code"].strip(),name=first["template_name"].strip(),recipe_type=first["template_type"].strip(),sport_code=first.get("sport_code") or None,event_codes=split(first.get("event_codes")),role_codes=split(first.get("role_codes")),discipline_codes=split(first.get("discipline_codes")),format_codes=split(first.get("format_codes")),phase_codes=split(first.get("phase_codes")),goal_codes=split(first.get("goal_codes")),level_codes=split(first.get("level_codes")),load_class=first["load_class"].strip(),purpose=first["purpose"].strip(),blocks=blocks)
    except (ValueError,KeyError,json.JSONDecodeError) as exc: raise ProblemError(422,"template_csv_invalid","Invalid template CSV",str(exc)) from exc
    return await create_recipe(body,actor,session)


@router.get("/session-recipes")
async def list_recipes(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(Recipe, RecipeVersion).join(RecipeVersion, and_(RecipeVersion.recipe_id == Recipe.id, RecipeVersion.recipe_version == Recipe.latest_version)).order_by(Recipe.code)
    if sport_code: statement = statement.where(or_(RecipeVersion.sport_code.is_(None), RecipeVersion.sport_code == sport_code))
    rows = (await session.execute(statement)).all()
    return {"items": [{"id": identity.id, "code": identity.code, **model_dict(version)} for identity, version in rows]}


@router.get("/session-recipes/{recipe_id}")
async def get_recipe(recipe_id: UUID, recipe_version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(Recipe,recipe_id)
    if identity is None: raise ProblemError(404,"recipe_not_found","Recipe not found","The recipe does not exist.")
    version_number=recipe_version or identity.latest_version; version=await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id==recipe_id,RecipeVersion.recipe_version==version_number))
    if version is None: raise ProblemError(404,"recipe_version_not_found","Recipe version not found","The recipe version does not exist.")
    blocks=(await session.scalars(select(RecipeBlock).where(RecipeBlock.recipe_id==recipe_id,RecipeBlock.recipe_version==version_number).order_by(RecipeBlock.sequence))).all(); output=[]
    slots_by_block=defaultdict(list)
    if blocks:
        for slot in (await session.scalars(select(RecipeSlot).where(RecipeSlot.block_id.in_([block.id for block in blocks])).order_by(RecipeSlot.block_id,RecipeSlot.sequence))).all(): slots_by_block[slot.block_id].append(slot)
    quality_codes={slot.required_quality for slots in slots_by_block.values() for slot in slots}
    eligible_by_quality=defaultdict(list)
    if quality_codes:
        matches=(await session.execute(select(Method,MethodVersion,MethodEffect).join(MethodVersion,and_(MethodVersion.method_id==Method.id,MethodVersion.content_version==Method.latest_version)).join(MethodEffect,and_(MethodEffect.method_id==Method.id,MethodEffect.method_version==MethodVersion.content_version)).where(Method.archived.is_(False),MethodVersion.generator_eligible.is_(True),MethodEffect.quality_code.in_(quality_codes)))).all()
        for method,method_version,effect in matches: eligible_by_quality[effect.quality_code].append({"id":method.id,"code":method.code,"name":method_version.canonical_name,"training_role":effect.training_role})
    for block in blocks:
        output.append({**model_dict(block),"slots":[{**model_dict(item),"eligible_methods":eligible_by_quality[item.required_quality]} for item in slots_by_block[block.id]]})
    return {"id":recipe_id,"code":identity.code,**model_dict(version),"blocks":output}


@router.get("/session-recipes/{recipe_id}/versions")
async def list_recipe_versions(recipe_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    if await session.get(Recipe, recipe_id) is None:
        raise ProblemError(404,"recipe_not_found","Template not found","The workout template does not exist.")
    rows=(await session.scalars(select(RecipeVersion).where(RecipeVersion.recipe_id==recipe_id).order_by(RecipeVersion.recipe_version.desc()))).all()
    return {"items":[{"recipe_version":row.recipe_version,"name":row.name,"status":row.status,"updated_at":row.updated_at,"record_version":row.record_version} for row in rows]}


@router.put("/session-recipes/{recipe_id}/retire")
async def retire_recipe(recipe_id: UUID, body: RecipeRetireCommand, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(Recipe,recipe_id)
    if identity is None: raise ProblemError(404,"recipe_not_found","Template not found","The workout template does not exist.")
    row=await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id==recipe_id,RecipeVersion.recipe_version==identity.latest_version).with_for_update())
    if row is None: raise ProblemError(404,"recipe_not_found","Template not found","The workout template does not exist.")
    if row.record_version!=body.expected_record_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the template and try again.")
    row.status="retired" if body.retired else "evidence_verified";row.record_version+=1;row.updated_at=_now()
    await _audit(session,actor,"knowledge.recipe.retired" if body.retired else "knowledge.recipe.restored","recipe",recipe_id,after={"status":row.status});await session.commit()
    return {"id":recipe_id,"status":row.status,"record_version":row.record_version}


@router.post("/session-recipes/{recipe_id}/versions", status_code=201)
async def create_recipe_version(recipe_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(Recipe,recipe_id,with_for_update=True)
    if identity is None: raise ProblemError(404,"recipe_not_found","Recipe not found","The recipe does not exist.")
    source=await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id==recipe_id,RecipeVersion.recipe_version==identity.latest_version))
    if source is None or source.status not in {"released","retired"}: raise ProblemError(409,"draft_version_exists","Draft version exists","Publish or retire the current version first.")
    version=identity.latest_version+1; values=model_dict(source)
    for key in ("recipe_id","recipe_version","status","created_at","updated_at","record_version"): values.pop(key,None)
    now=_now(); row=RecipeVersion(recipe_id=recipe_id,recipe_version=version,status="draft",created_at=now,updated_at=now,record_version=1,**values); session.add(row); await session.flush()
    blocks=(await session.scalars(select(RecipeBlock).where(RecipeBlock.recipe_id==recipe_id,RecipeBlock.recipe_version==source.recipe_version).order_by(RecipeBlock.sequence))).all()
    for block in blocks:
        block_values=model_dict(block)
        for key in ("id","recipe_id","recipe_version","created_at","updated_at","version"): block_values.pop(key,None)
        clone=RecipeBlock(recipe_id=recipe_id,recipe_version=version,**block_values); session.add(clone); await session.flush()
        slots=(await session.scalars(select(RecipeSlot).where(RecipeSlot.block_id==block.id).order_by(RecipeSlot.sequence))).all()
        for slot in slots:
            slot_values=model_dict(slot)
            for key in ("id","block_id","created_at","updated_at","version"): slot_values.pop(key,None)
            session.add(RecipeSlot(block_id=clone.id,**slot_values))
    identity.latest_version=version; identity.version+=1; await _audit(session,actor,"knowledge.recipe.version_created","recipe",recipe_id,after={"recipe_version":version}); await session.commit(); return {"id":recipe_id,"code":identity.code,**model_dict(row)}


@router.put("/session-recipes/{recipe_id}/versions/{recipe_version}")
async def update_recipe(recipe_id: UUID, recipe_version: int, body: RecipeUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(Recipe,recipe_id); row=await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id==recipe_id,RecipeVersion.recipe_version==recipe_version).with_for_update())
    if identity is None or row is None: raise ProblemError(404,"recipe_not_found","Recipe not found","The recipe version does not exist.")
    if identity.code!=body.code: raise ProblemError(409,"stable_code_immutable","Stable code is immutable","Create a different recipe for a different code.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new content version.")
    if row.record_version!=body.expected_record_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the recipe and try again.")
    before=model_dict(row)
    for key,value in body.model_dump(exclude={"code","blocks","expected_record_version"}).items(): setattr(row,key,value)
    await session.execute(delete(RecipeBlock).where(RecipeBlock.recipe_id==recipe_id,RecipeBlock.recipe_version==recipe_version)); await session.flush(); blocks=[]; slots_by_block=defaultdict(list)
    for block_index,item in enumerate(body.blocks,1):
        block=RecipeBlock(recipe_id=recipe_id,recipe_version=recipe_version,sequence=block_index,**item.model_dump(exclude={"slots"})); session.add(block); await session.flush(); blocks.append(block)
        for slot_index,slot in enumerate(item.slots,1):
            child=RecipeSlot(block_id=block.id,sequence=slot_index,**slot.model_dump()); session.add(child); slots_by_block[block.id].append(child)
    try: validate_recipe(row,blocks,slots_by_block)
    except KnowledgeValidationError as exc: raise _problem(exc,code="recipe_validation_failed",title="Recipe validation failed") from exc
    row.status="evidence_verified"; row.record_version+=1; row.updated_at=_now(); await _audit(session,actor,"knowledge.recipe.updated","recipe",recipe_id,before=before,after=model_dict(row)); await session.commit(); return {"id":recipe_id,"code":identity.code,**model_dict(row)}


@router.post("/program-archetypes", status_code=201)
async def create_archetype(body: ProgramArchetypeDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    values = body.model_dump(exclude={"code", "sport_code"}); identity = ProgramArchetype(code=body.code, sport_code=body.sport_code, latest_version=1); session.add(identity); await session.flush(); now=_now(); row=ProgramArchetypeVersion(archetype_id=identity.id, content_version=1, status="draft", created_at=now, updated_at=now, record_version=1, **values); session.add(row); await _audit(session, actor, "knowledge.program_archetype.created", "program_archetype", identity.id, after=body.model_dump()); await session.commit(); return {"id": identity.id, "content_version": 1, **body.model_dump(), "status": "draft"}


@router.get("/program-archetypes")
async def list_archetypes(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(ProgramArchetype, ProgramArchetypeVersion).join(ProgramArchetypeVersion, and_(ProgramArchetypeVersion.archetype_id == ProgramArchetype.id, ProgramArchetypeVersion.content_version == ProgramArchetype.latest_version)).order_by(ProgramArchetype.sport_code, ProgramArchetype.code)
    if sport_code: statement = statement.where(ProgramArchetype.sport_code == sport_code)
    rows = (await session.execute(statement)).all()
    return {"items": [{"id": identity.id, "code": identity.code, "sport_code": identity.sport_code, **model_dict(version)} for identity, version in rows]}


@router.get("/program-archetypes/{archetype_id}")
async def get_archetype(archetype_id: UUID, content_version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(ProgramArchetype,archetype_id)
    if identity is None: raise ProblemError(404,"archetype_not_found","Archetype not found","The program archetype does not exist.")
    version_number=content_version or identity.latest_version; row=await session.scalar(select(ProgramArchetypeVersion).where(ProgramArchetypeVersion.archetype_id==archetype_id,ProgramArchetypeVersion.content_version==version_number))
    if row is None: raise ProblemError(404,"archetype_version_not_found","Archetype version not found","The program archetype version does not exist.")
    phases=(await session.scalars(select(PhaseTemplate).where(PhaseTemplate.archetype_id==archetype_id,PhaseTemplate.archetype_version==version_number).order_by(PhaseTemplate.sequence))).all()
    return {"id":archetype_id,"code":identity.code,"sport_code":identity.sport_code,**model_dict(row),"phases":[model_dict(item) for item in phases]}


@router.post("/program-archetypes/{archetype_id}/versions", status_code=201)
async def create_archetype_version(archetype_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(ProgramArchetype,archetype_id,with_for_update=True)
    if identity is None: raise ProblemError(404,"archetype_not_found","Archetype not found","The program archetype does not exist.")
    source=await session.scalar(select(ProgramArchetypeVersion).where(ProgramArchetypeVersion.archetype_id==archetype_id,ProgramArchetypeVersion.content_version==identity.latest_version))
    if source is None or source.status not in {"released","retired"}: raise ProblemError(409,"draft_version_exists","Draft version exists","Publish or retire the current version first.")
    version=identity.latest_version+1; values=model_dict(source)
    for key in ("archetype_id","content_version","status","created_at","updated_at","record_version"): values.pop(key,None)
    now=_now(); row=ProgramArchetypeVersion(archetype_id=archetype_id,content_version=version,status="draft",created_at=now,updated_at=now,record_version=1,**values); session.add(row)
    phases=(await session.scalars(select(PhaseTemplate).where(PhaseTemplate.archetype_id==archetype_id,PhaseTemplate.archetype_version==source.content_version).order_by(PhaseTemplate.sequence))).all()
    for phase in phases:
        phase_values=model_dict(phase)
        for key in ("id","archetype_id","archetype_version","created_at","updated_at","version"): phase_values.pop(key,None)
        session.add(PhaseTemplate(archetype_id=archetype_id,archetype_version=version,**phase_values))
    identity.latest_version=version; identity.version+=1; await _audit(session,actor,"knowledge.program_archetype.version_created","program_archetype",archetype_id,after={"content_version":version}); await session.commit(); return {"id":archetype_id,"code":identity.code,"sport_code":identity.sport_code,**model_dict(row)}


@router.put("/program-archetypes/{archetype_id}/versions/{content_version}")
async def update_archetype(archetype_id: UUID, content_version: int, body: ProgramArchetypeUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    identity=await session.get(ProgramArchetype,archetype_id); row=await session.scalar(select(ProgramArchetypeVersion).where(ProgramArchetypeVersion.archetype_id==archetype_id,ProgramArchetypeVersion.content_version==content_version).with_for_update())
    if identity is None or row is None: raise ProblemError(404,"archetype_not_found","Archetype not found","The archetype version does not exist.")
    if identity.code!=body.code or identity.sport_code!=body.sport_code: raise ProblemError(409,"stable_identity_immutable","Stable identity is immutable","Create a different archetype for a different code or sport.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a new content version.")
    if row.record_version!=body.expected_record_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the archetype and try again.")
    if body.minimum_weeks>body.maximum_weeks: raise ProblemError(422,"archetype_bounds_invalid","Invalid archetype bounds","Minimum weeks cannot exceed maximum weeks.")
    before=model_dict(row)
    for key,value in body.model_dump(exclude={"code","sport_code","expected_record_version"}).items(): setattr(row,key,value)
    row.status="draft"; row.record_version+=1; row.updated_at=_now(); await _audit(session,actor,"knowledge.program_archetype.updated","program_archetype",archetype_id,before=before,after=model_dict(row)); await session.commit(); return {"id":archetype_id,"code":identity.code,"sport_code":identity.sport_code,**model_dict(row)}


@router.post("/program-archetypes/{archetype_id}/versions/{content_version}/phases", status_code=201)
async def replace_phases(archetype_id: UUID, content_version: int, body: list[PhaseDraft], actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    target = await session.scalar(select(ProgramArchetypeVersion).where(ProgramArchetypeVersion.archetype_id == archetype_id, ProgramArchetypeVersion.content_version == content_version).with_for_update())
    if target is None: raise ProblemError(404, "archetype_not_found", "Archetype not found", "The archetype version does not exist.")
    if target.status == "released": raise ProblemError(409, "released_content_immutable", "Released content is immutable", "Create a new content version.")
    if not body or abs(sum(item.allocation_weight for item in body) - 1) > 0.001: raise ProblemError(422, "phase_allocation_invalid", "Invalid phase allocation", "Phase allocation weights must sum to one.")
    from backend.app.knowledge.models import PhaseTemplate
    await session.execute(delete(PhaseTemplate).where(PhaseTemplate.archetype_id == archetype_id, PhaseTemplate.archetype_version == content_version)); rows=[PhaseTemplate(archetype_id=archetype_id, archetype_version=content_version, sequence=index, **item.model_dump()) for index,item in enumerate(body,1)]; session.add_all(rows); target.status="draft"; target.record_version+=1; target.updated_at=_now(); await _audit(session,actor,"knowledge.program_phases.replaced","program_archetype",archetype_id,after={"phase_count":len(rows)}); await session.commit(); return {"items":[model_dict(row) for row in rows]}


@router.post("/weeks", status_code=201)
async def create_week(body: WeekTemplateDraft, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if body.sessions_minimum > body.sessions_maximum or body.hard_session_maximum > body.sessions_maximum: raise ProblemError(422,"week_bounds_invalid","Invalid week bounds","Session and hard-session bounds are inconsistent.")
    found=set((await session.scalars(select(Recipe.id).where(Recipe.id.in_(body.recipe_ids)))).all())
    if found != set(body.recipe_ids): raise ProblemError(422,"recipe_missing","Recipe missing","One or more week recipes do not exist.")
    values=body.model_dump(exclude={"recipe_ids"}); row=WeekTemplate(**values,status="draft"); session.add(row); await session.flush(); session.add_all(WeekTemplateSession(week_template_id=row.id,sequence=index,recipe_id=recipe_id,required=True) for index,recipe_id in enumerate(body.recipe_ids,1)); await _audit(session,actor,"knowledge.week_template.created","week_template",row.id,after=body.model_dump(mode="json")); await session.commit(); return {**model_dict(row),"recipe_ids":body.recipe_ids}


@router.put("/weeks/{week_id}")
async def update_week(week_id: UUID, body: WeekTemplateUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(WeekTemplate,week_id,with_for_update=True)
    if row is None: raise ProblemError(404,"week_not_found","Week template not found","The weekly template does not exist.")
    if row.status=="released": raise ProblemError(409,"released_content_immutable","Released content is immutable","Create a replacement in a future release.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the week template and try again.")
    if (row.code,row.sport_code)!=(body.code,body.sport_code): raise ProblemError(409,"stable_identity_immutable","Stable identity is immutable","Code and sport cannot be changed.")
    if body.sessions_minimum>body.sessions_maximum or body.hard_session_maximum>body.sessions_maximum: raise ProblemError(422,"week_bounds_invalid","Invalid week bounds","Session and hard-session bounds are inconsistent.")
    found=set((await session.scalars(select(Recipe.id).where(Recipe.id.in_(body.recipe_ids)))).all())
    if found!=set(body.recipe_ids): raise ProblemError(422,"recipe_missing","Recipe missing","One or more week recipes do not exist.")
    before=model_dict(row)
    for key,value in body.model_dump(exclude={"recipe_ids","expected_version","code","sport_code"}).items(): setattr(row,key,value)
    await session.execute(delete(WeekTemplateSession).where(WeekTemplateSession.week_template_id==week_id)); session.add_all(WeekTemplateSession(week_template_id=week_id,sequence=index,recipe_id=recipe_id,required=True) for index,recipe_id in enumerate(body.recipe_ids,1)); row.status="draft"; row.version+=1; await _audit(session,actor,"knowledge.week_template.updated","week_template",row.id,before=before,after={**model_dict(row),"recipe_ids":body.model_dump(mode="json")["recipe_ids"]}); await session.commit(); return {**model_dict(row),"recipe_ids":body.recipe_ids}


@router.get("/weeks")
async def list_weeks(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(WeekTemplate).order_by(WeekTemplate.sport_code, WeekTemplate.phase_code, WeekTemplate.code)
    if sport_code: statement = statement.where(WeekTemplate.sport_code == sport_code)
    rows = (await session.scalars(statement)).all()
    return {"items": [{**model_dict(row), "recipe_ids": list((await session.scalars(select(WeekTemplateSession.recipe_id).where(WeekTemplateSession.week_template_id == row.id).order_by(WeekTemplateSession.sequence))).all())} for row in rows]}


@router.post("/imports", status_code=201)
async def preview_workbook(file: UploadFile = File(...), actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    content = await file.read(20 * 1024 * 1024 + 1)
    filename = file.filename or "exercise-import"
    if not filename.lower().endswith((".xlsx", ".csv", ".md", ".docx")):
        raise ProblemError(422, "exercise_import_type_invalid", "Unsupported file", "Choose an .csv, .md, .docx or .xlsx file.")
    try: row = await preview_import(session, filename=filename, content=content)
    except WorkbookImportError as exc: raise _problem(exc, code="workbook_import_invalid", title="Workbook import invalid") from exc
    await _audit(session,actor,"knowledge.source_import.previewed","source_import",row.id,after=row.summary_json); await session.commit(); return {"id":row.id,"source_name":row.source_name,"content_hash":row.content_hash,"status":row.status,"row_count":row.row_count,"summary":row.summary_json,"version":row.version}


@router.post("/dataset-imports/{dataset_kind}", status_code=201)
async def preview_structured_dataset(
    dataset_kind: str,
    files: list[UploadFile] = File(...),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if dataset_kind not in DATASET_KINDS:
        raise ProblemError(404, "dataset_kind_unknown", "Dataset type not found", "Choose training_templates, sport_priority_matrix or training_policies.")
    uploaded=[]
    for file in files:
        filename=file.filename or "dataset"
        allowed_suffixes=(".csv",) if dataset_kind=="sport_priority_matrix" else (".json",)
        if not filename.lower().endswith(allowed_suffixes):
            raise ProblemError(422,"dataset_file_type_invalid","Unsupported file",f"This dataset requires {', '.join(allowed_suffixes)} files.")
        uploaded.append((filename, await file.read(30 * 1024 * 1024 + 1)))
    try: row=await preview_dataset(session,dataset_kind=dataset_kind,files=uploaded)
    except WorkbookImportError as exc: raise _problem(exc,code="dataset_import_invalid",title="Dataset import invalid") from exc
    await _audit(session,actor,"knowledge.dataset_import.previewed","source_import",row.id,after=row.summary_json)
    await session.commit()
    return {"id":row.id,"source_name":row.source_name,"content_hash":row.content_hash,"status":row.status,"row_count":row.row_count,"summary":row.summary_json,"version":row.version}


@router.post("/dataset-imports/{source_import_id}/commit")
async def commit_structured_dataset(source_import_id: UUID, body: ImportCommitRequest, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(SourceImport,source_import_id,with_for_update=True)
    if row is None: raise ProblemError(404,"source_import_not_found","Import not found","The source import does not exist.")
    # A client may retry after the database commit succeeded but its response
    # was lost. Return the completed result before applying optimistic-version
    # checks so the mutation is genuinely idempotent.
    if row.status == "committed":
        return {"id": row.id, "status": "committed", "summary": dict(row.summary_json)}
    if row.version != body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the import and try again.")
    try: summary=await commit_dataset(session,row,actor)
    except WorkbookImportError as exc:
        await session.rollback(); raise _problem(exc,code="dataset_commit_failed",title="Dataset commit failed") from exc
    return {"id":row.id,"status":"committed","summary":summary}


@router.get("/dataset-status")
async def dataset_status(session: AsyncSession = Depends(get_session)) -> dict:
    models=(
        ("exercises", Method), ("training_templates", TrainingReferenceTemplate),
        ("training_template_versions", TrainingReferenceTemplateVersion), ("sport_priorities", SportTemplatePriority),
        ("sport_mode_policies", SportModePolicy),
        ("phase_dose_policies", PhaseDosePolicy),
    )
    values=(await session.execute(select(*(select(func.count()).select_from(model).scalar_subquery().label(key) for key,model in models)))).one()
    counts={key:int(value or 0) for (key,_),value in zip(models,values)}
    return {"counts":counts}


@router.get("/training-reference-templates")
async def list_training_reference_templates(
    category_code: str | None = None,
    athlete_level: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    method_count=select(func.count()).select_from(TrainingReferenceMethod).where(TrainingReferenceMethod.template_id==TrainingReferenceTemplate.id,TrainingReferenceMethod.template_version==TrainingReferenceTemplateVersion.content_version).correlate(TrainingReferenceTemplate,TrainingReferenceTemplateVersion).scalar_subquery()
    week_count=select(func.count()).select_from(TrainingReferenceWeek).where(TrainingReferenceWeek.template_id==TrainingReferenceTemplate.id,TrainingReferenceWeek.template_version==TrainingReferenceTemplateVersion.content_version).correlate(TrainingReferenceTemplate,TrainingReferenceTemplateVersion).scalar_subquery()
    statement = select(TrainingReferenceTemplate, TrainingReferenceTemplateVersion, method_count.label("method_count"), week_count.label("week_count")).join(
        TrainingReferenceTemplateVersion,
        and_(TrainingReferenceTemplateVersion.template_id == TrainingReferenceTemplate.id, TrainingReferenceTemplateVersion.content_version == TrainingReferenceTemplate.latest_version),
    ).order_by(TrainingReferenceTemplateVersion.category_code, TrainingReferenceTemplateVersion.athlete_level)
    if category_code: statement=statement.where(TrainingReferenceTemplateVersion.category_code==category_code)
    if athlete_level: statement=statement.where(TrainingReferenceTemplateVersion.athlete_level==athlete_level)
    rows=(await session.execute(statement)).all()
    priority_rows = (await session.scalars(select(SportTemplatePriority))).all()
    priority_sports = {row.id: row.sport_code for row in priority_rows}
    category_sports: dict[str, set[str]] = defaultdict(set)
    for row in priority_rows:
        category_sports[row.primary_template_category].add(row.sport_code)
    if priority_rows:
        for item in (await session.scalars(select(SportTemplatePriorityItem).where(SportTemplatePriorityItem.priority_id.in_(priority_sports)))).all():
            category_sports[item.category_code].add(priority_sports[item.priority_id])
    items=[]
    for identity, version, methods, weeks in rows:
        used_by_sports = sorted(category_sports[version.category_code])
        items.append({"id":identity.id,"code":identity.code,"content_version":version.content_version,"name":version.name,"category_code":version.category_code,"athlete_level":version.athlete_level,"duration_weeks":version.duration_weeks,"method_count":int(methods),"week_count":int(weeks),"status":version.status,"used_by_sports":used_by_sports,"usage_scope":"shared" if len(used_by_sports)>1 else "sport_specific"})
    return {"items":items,"total":len(items)}


@router.get("/sport-template-priorities")
async def list_sport_template_priorities(
    sport_code: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    statement = select(SportTemplatePriority).order_by(
        SportTemplatePriority.sport_code,
        SportTemplatePriority.scope_type,
        SportTemplatePriority.scope_code,
        SportTemplatePriority.phase_code,
        SportTemplatePriority.goal_code,
    )
    if sport_code:
        statement = statement.where(SportTemplatePriority.sport_code == sport_code)
    rows = (await session.scalars(statement)).all()
    ranked: dict[UUID, list[dict]] = defaultdict(list)
    if rows:
        item_rows = (await session.scalars(
            select(SportTemplatePriorityItem)
            .where(SportTemplatePriorityItem.priority_id.in_([row.id for row in rows]))
            .order_by(SportTemplatePriorityItem.priority_id, SportTemplatePriorityItem.rank)
        )).all()
        for item in item_rows:
            ranked[item.priority_id].append({
                "rank": item.rank,
                "category_code": item.category_code,
                "weight": float(item.weight),
            })
    return {
        "items": [
            {
                **model_dict(row),
                "priorities": ranked[row.id],
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.get("/training-policies")
async def list_training_policies(
    sport_code: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    mode_statement = select(SportModePolicy).order_by(SportModePolicy.sport_code)
    if sport_code:
        mode_statement = mode_statement.where(SportModePolicy.sport_code == sport_code)
    sport_modes = (await session.scalars(mode_statement)).all()
    phase_policies = (await session.scalars(
        select(PhaseDosePolicy).order_by(PhaseDosePolicy.phase_code)
    )).all()
    all_mode_count = await session.scalar(select(func.count()).select_from(SportModePolicy)) or 0
    return {
        "summary": {
            "total": int(all_mode_count) + len(phase_policies),
            "sport_modes": int(all_mode_count),
            "phase_dose_policies": len(phase_policies),
        },
        "sport_modes": [model_dict(row) for row in sport_modes],
        "phase_dose_policies": [model_dict(row) for row in phase_policies],
    }


@router.get("/imports")
async def list_imports(session: AsyncSession = Depends(get_session)) -> dict:
    return {"items": [model_dict(row) for row in (await session.scalars(select(SourceImport).order_by(SourceImport.created_at.desc()))).all()]}


@router.get("/imports/{source_import_id}")
async def get_import(source_import_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(SourceImport,source_import_id)
    if row is None: raise ProblemError(404,"source_import_not_found","Import not found","The source import does not exist.")
    rows=(await session.scalars(select(SourceImportRow).where(SourceImportRow.source_import_id==source_import_id).order_by(SourceImportRow.source_reference))).all(); return {**model_dict(row),"rows":[model_dict(item) for item in rows]}


@router.post("/imports/{source_import_id}/commit")
async def commit_workbook(source_import_id: UUID, body: ImportCommitRequest, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(SourceImport,source_import_id,with_for_update=True)
    if row is None: raise ProblemError(404,"source_import_not_found","Import not found","The source import does not exist.")
    if row.status == "committed":
        return {"id": row.id, "status": "committed", "summary": dict(row.summary_json)}
    if row.version != body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the import and try again.")
    try: summary=await commit_import(session,row,actor)
    except WorkbookImportError as exc:
        await session.rollback()
        raise _problem(exc,code="workbook_commit_failed",title="Exercise import failed") from exc
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409,"exercise_import_conflict","Exercise import conflict","The import conflicted with existing exercise data. Reload the library and preview the CSV again.") from exc
    return {"id":row.id,"status":"committed","summary":summary}


@router.post("/releases", status_code=201)
async def create_release(body: ReleaseCreate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=ContentRelease(**body.model_dump(),state="draft",validation_summary={}); session.add(row); await session.flush(); await _audit(session,actor,"knowledge.release.created","content_release",row.id,after=model_dict(row)); await session.commit(); return model_dict(row)


@router.get("/releases")
async def list_releases(sport_code: str | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    statement = select(ContentRelease).order_by(ContentRelease.created_at.desc())
    if sport_code: statement = statement.where(ContentRelease.sport_code == sport_code)
    return {"items": [model_dict(row) for row in (await session.scalars(statement)).all()]}


@router.get("/releases/{release_id}")
async def get_release(release_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    row = await session.get(ContentRelease, release_id)
    if row is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    items = (await session.scalars(select(ReleaseItem).where(ReleaseItem.release_id == release_id).order_by(ReleaseItem.entity_type, ReleaseItem.entity_id))).all()
    return {**model_dict(row), "items": [model_dict(item) for item in items]}


@router.get("/releases/{release_id}/candidates")
async def release_candidates(release_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    release = await session.get(ContentRelease, release_id)
    if release is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    candidates: list[dict] = []
    versioned = [
        ("method", Method, MethodVersion, MethodVersion.method_id, MethodVersion.content_version),
        ("evidence_claim", EvidenceClaim, EvidenceClaimVersion, EvidenceClaimVersion.claim_id, EvidenceClaimVersion.claim_version),
        ("demand_fact", DemandFact, DemandFactVersion, DemandFactVersion.demand_fact_id, DemandFactVersion.fact_version),
        ("prescription_rule", PrescriptionRule, PrescriptionRuleVersion, PrescriptionRuleVersion.rule_id, PrescriptionRuleVersion.rule_version),
        ("program_archetype", ProgramArchetype, ProgramArchetypeVersion, ProgramArchetypeVersion.archetype_id, ProgramArchetypeVersion.content_version),
        ("recipe", Recipe, RecipeVersion, RecipeVersion.recipe_id, RecipeVersion.recipe_version),
    ]
    for entity_type, identity_model, version_model, id_column, version_column in versioned:
        statement = select(identity_model, version_model).join(version_model, id_column == identity_model.id).where(version_model.status.in_(["evidence_verified", "released"]))
        if release.sport_code and hasattr(version_model, "sport_code"): statement = statement.where(or_(version_model.sport_code.is_(None), version_model.sport_code == release.sport_code))
        for identity, version in (await session.execute(statement)).all():
            candidates.append({"entity_type": entity_type, "entity_id": identity.id, "entity_version": getattr(version, version_column.key), "code": identity.code})
    for entity_type, model in [("physical_quality", PhysicalQuality),("sport_taxon", SportTaxon),("sport_quality_priority", SportQualityPriority),("week_template", WeekTemplate),("method_relation", MethodRelation)]:
        statement = select(model).where(model.status.in_(["evidence_verified", "released"]))
        if release.sport_code and hasattr(model, "sport_code"): statement = statement.where(model.sport_code == release.sport_code)
        for row in (await session.scalars(statement)).all(): candidates.append({"entity_type":entity_type,"entity_id":row.id,"entity_version":row.version,"code":getattr(row,"code",str(row.id))})
    return {"items": sorted(candidates, key=lambda item: (item["entity_type"], item["code"]))}


@router.put("/releases/{release_id}/manifest")
async def replace_manifest(release_id: UUID, body: ReleaseManifestReplace, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    release=await session.get(ContentRelease,release_id,with_for_update=True)
    if release is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    if release.state != "draft": raise ProblemError(409,"release_immutable","Release is immutable","Only a draft manifest can change.")
    if release.version != body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the release and try again.")
    if len({(item.entity_type,item.entity_id) for item in body.items}) != len(body.items): raise ProblemError(422,"manifest_duplicate","Duplicate manifest item","A release may select only one version of each entity.")
    await session.execute(delete(ReleaseItem).where(ReleaseItem.release_id==release_id)); rows=[]
    for item in body.items:
        probe=ReleaseItem(release_id=release_id,entity_type=item.entity_type,entity_id=item.entity_id,entity_version=item.entity_version,snapshot_hash="")
        try: entity=await _resolve_item(session,probe)
        except ReleaseValidationError as exc: raise _problem(exc,code="manifest_item_invalid",title="Manifest item invalid") from exc
        probe.snapshot_hash=await snapshot_for_item(session,probe,entity); rows.append(probe)
    session.add_all(rows); release.version+=1; release.validation_summary={}; await _audit(session,actor,"knowledge.release.manifest_replaced","content_release",release.id,after={"item_count":len(rows)}); await session.commit(); return {"id":release.id,"version":release.version,"item_count":len(rows)}


@router.post("/releases/{release_id}/validate")
async def validate_release_endpoint(release_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    release=await session.get(ContentRelease,release_id)
    if release is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    try: resolved=await validate_release(session,release)
    except ReleaseValidationError as exc: release.validation_summary={"passed":False,"error":str(exc),"validated_at":_now().isoformat()}; await session.commit(); raise _problem(exc,code="release_validation_failed",title="Release validation failed") from exc
    release.validation_summary={"passed":True,"item_count":len(resolved),"validated_at":_now().isoformat()}; release.version+=1; await session.commit(); return release.validation_summary


@router.get("/releases/{release_id}/diff")
async def release_diff(release_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    release=await session.get(ContentRelease,release_id)
    if release is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    previous=await session.scalar(select(ContentRelease).where(ContentRelease.sport_code==release.sport_code,ContentRelease.state.in_(["released","retired"]),ContentRelease.id!=release.id).order_by(ContentRelease.published_at.desc()))
    current={(row.entity_type,row.entity_id):row.entity_version for row in (await session.scalars(select(ReleaseItem).where(ReleaseItem.release_id==release.id))).all()}; old={(row.entity_type,row.entity_id):row.entity_version for row in (await session.scalars(select(ReleaseItem).where(ReleaseItem.release_id==previous.id))).all()} if previous else {}
    return {"previous_release_id":previous.id if previous else None,"added":[{"entity_type":key[0],"entity_id":key[1],"version":version} for key,version in current.items() if key not in old],"removed":[{"entity_type":key[0],"entity_id":key[1],"version":version} for key,version in old.items() if key not in current],"changed":[{"entity_type":key[0],"entity_id":key[1],"from_version":old[key],"to_version":version} for key,version in current.items() if key in old and old[key]!=version]}


@router.post("/releases/{release_id}/publish", dependencies=[Depends(require_roles("content_publisher","platform_admin"))])
async def publish_release(release_id: UUID, body: PublishCommand, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    release=await session.get(ContentRelease,release_id,with_for_update=True)
    if release is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    if release.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the release and try again.")
    try: resolved=await validate_release(session,release)
    except ReleaseValidationError as exc: raise _problem(exc,code="release_validation_failed",title="Release validation failed") from exc
    if release.sport_code:
        active=(await session.scalars(select(ContentRelease).where(ContentRelease.sport_code==release.sport_code,ContentRelease.state=="released",ContentRelease.id!=release.id).with_for_update())).all()
        for old in active: old.state="retired"; old.retired_at=_now(); old.version+=1
    hashes=[]
    for item in resolved:
        item.item.snapshot_hash=item.snapshot_hash; hashes.append(item.snapshot_hash)
        if hasattr(item.entity,"status"): setattr(item.entity,"status","released")
        if isinstance(item.entity,MethodVersion): item.entity.generator_eligible=True
        if release.sport_code=="hyrox" and isinstance(item.entity,SportTaxon): item.entity.visible=True
    release.content_hash=canonical_hash(sorted(hashes)); release.state="released"; release.published_at=_now(); release.published_by=actor; release.validation_summary={"passed":True,"item_count":len(resolved),"published_at":release.published_at.isoformat()}; release.version+=1; await _audit(session,actor,"knowledge.release.published","content_release",release.id,after={"content_hash":release.content_hash,"item_count":len(resolved)}); await session.commit(); return {"id":release.id,"state":release.state,"content_hash":release.content_hash,"item_count":len(resolved),"version":release.version}


@router.post("/releases/{release_id}/retire", dependencies=[Depends(require_roles("content_publisher","platform_admin"))])
async def retire_release(release_id: UUID, body: PublishCommand, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    row=await session.get(ContentRelease,release_id,with_for_update=True)
    if row is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    if row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the release and try again.")
    if row.state!="released": raise ProblemError(409,"release_not_active","Release not active","Only a released package can be retired.")
    row.state="retired"; row.retired_at=_now(); row.version+=1; await _audit(session,actor,"knowledge.release.retired","content_release",row.id); await session.commit(); return model_dict(row)


@router.post("/releases/{release_id}/rollback", dependencies=[Depends(require_roles("content_publisher","platform_admin"))])
async def rollback_release(release_id: UUID, body: PublishCommand, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    target=await session.get(ContentRelease,release_id,with_for_update=True)
    if target is None: raise ProblemError(404,"release_not_found","Release not found","The release does not exist.")
    if target.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the release and try again.")
    if target.state!="retired": raise ProblemError(409,"rollback_target_invalid","Invalid rollback target","Only a previously published retired release can be reactivated.")
    active=(await session.scalars(select(ContentRelease).where(ContentRelease.sport_code==target.sport_code,ContentRelease.state=="released").with_for_update())).all()
    for row in active: row.state="retired"; row.retired_at=_now(); row.version+=1
    target.state="released"; target.retired_at=None; target.version+=1
    await _audit(session,actor,"knowledge.release.rolled_back","content_release",target.id,after={"replaced_release_ids":[str(row.id) for row in active]}); await session.commit(); return model_dict(target)


@router.post("/simulations", status_code=201)
async def run_simulation(body: SimulationRequest, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    release=await session.get(ContentRelease,body.release_id) if body.release_id else await session.scalar(select(ContentRelease).where(ContentRelease.sport_code==body.sport_code,ContentRelease.state=="released"))
    errors=[]
    if release is None: errors.append("no matching release")
    elif release.state=="draft":
        try: await validate_release(session,release)
        except ReleaseValidationError as exc: errors.append(str(exc))
    athlete=body.athlete
    for field in ("level","available_days","maximum_session_minutes","equipment","environments"):
        if field not in athlete: errors.append(f"missing athlete field: {field}")
    slot_results=[]
    if release is not None and not errors:
        manifest=(await session.scalars(select(ReleaseItem).where(ReleaseItem.release_id==release.id))).all()
        method_versions={item.entity_id:item.entity_version for item in manifest if item.entity_type=="method"}; recipe_versions={item.entity_id:item.entity_version for item in manifest if item.entity_type=="recipe"}
        methods=[]; level_rank={"beginner":1,"recreational":1,"intermediate":2,"club":2,"advanced":3,"national":3,"international":4}; athlete_rank=level_rank.get(str(athlete["level"]),1); equipment=set(athlete["equipment"]); environments=set(athlete["environments"])
        for method_id,version in method_versions.items():
            method=await session.scalar(select(MethodVersion).where(MethodVersion.method_id==method_id,MethodVersion.content_version==version)); effects=(await session.scalars(select(MethodEffect).where(MethodEffect.method_id==method_id,MethodEffect.method_version==version))).all()
            if method is None: continue
            method_rank=level_rank.get(method.level_minimum,1); equipment_ok=not method.equipment_codes or set(method.equipment_codes).issubset(equipment|{"bodyweight","none"}); environment_ok=not method.environments or bool(set(method.environments)&environments)
            if method_rank<=athlete_rank and equipment_ok and environment_ok: methods.append((method,effects))
        for recipe_id,version in recipe_versions.items():
            recipe=await session.scalar(select(RecipeVersion).where(RecipeVersion.recipe_id==recipe_id,RecipeVersion.recipe_version==version))
            if recipe is None or recipe.sport_code not in {None,body.sport_code}: continue
            blocks=(await session.scalars(select(RecipeBlock).where(RecipeBlock.recipe_id==recipe_id,RecipeBlock.recipe_version==version))).all()
            slots=(await session.scalars(select(RecipeSlot).where(RecipeSlot.block_id.in_([block.id for block in blocks])))).all() if blocks else []
            for slot in slots:
                candidates=[]
                for method,effects in methods:
                    if any(effect.quality_code==slot.required_quality and effect.training_role==slot.training_role for effect in effects): candidates.append(str(method.method_id))
                resolved=bool(candidates) or not slot.required; slot_results.append({"recipe_id":str(recipe_id),"recipe_version":version,"slot_code":slot.slot_code,"quality":slot.required_quality,"role":slot.training_role,"required":slot.required,"resolved":resolved,"candidate_method_ids":candidates[:20]})
                if not resolved: errors.append(f"unresolved required slot {slot.slot_code} in recipe {recipe_id}")
        if not recipe_versions: errors.append("release manifest contains no session recipes")
    result={"passed":not errors,"errors":errors,"release_id":str(release.id) if release else None,"sport_code":body.sport_code,"resolved_slots":sum(item["resolved"] for item in slot_results),"total_slots":len(slot_results),"slot_results":slot_results}
    row=SimulationRun(release_id=release.id if release else None,sport_code=body.sport_code,scenario_code=body.scenario_code,input_json=athlete,result_json=result,passed=not errors,planner_version=PLANNER_VERSION,executed_by=actor); session.add(row); await session.commit(); return {"id":row.id,**result}


@router.get("/simulations")
async def list_simulations(session: AsyncSession = Depends(get_session)) -> dict:
    return {"items": [model_dict(row) for row in (await session.scalars(select(SimulationRun).order_by(SimulationRun.created_at.desc()).limit(100))).all()]}


@router.get("/reports/generator-eligibility")
async def generator_eligibility_report(session: AsyncSession = Depends(get_session)) -> dict:
    rows=(await session.execute(select(Method,MethodVersion).join(MethodVersion,and_(MethodVersion.method_id==Method.id,MethodVersion.content_version==Method.latest_version)).order_by(Method.code))).all(); items=[]
    for identity,version in rows:
        effects=(await session.scalars(select(MethodEffect).where(MethodEffect.method_id==identity.id,MethodEffect.method_version==version.content_version))).all(); reasons=[]
        try: validate_method(version,effects)
        except KnowledgeValidationError as exc: reasons.append(str(exc))
        if version.status not in {"evidence_verified","released"}: reasons.append("human review is incomplete")
        items.append({"id":identity.id,"code":identity.code,"content_version":version.content_version,"eligible":not reasons and version.generator_eligible,"reasons":reasons})
    return {"total":len(items),"eligible":sum(item["eligible"] for item in items),"items":items}


@router.get("/reports/sport-coverage")
async def sport_coverage_report(session: AsyncSession = Depends(get_session)) -> dict:
    sports=[row.sport_code for row in (await session.scalars(select(SportTaxon).where(SportTaxon.taxon_type=="sport").order_by(SportTaxon.sport_code))).all()]; items=[]
    for sport in sports:
        demands=(await session.scalars(select(DemandFactVersion).where(DemandFactVersion.sport_code==sport))).all()
        priorities=(await session.scalars(select(SportQualityPriority).where(SportQualityPriority.sport_code==sport))).all()
        recipes=(await session.scalars(select(RecipeVersion).where(RecipeVersion.sport_code==sport))).all()
        archetype_ids=(await session.scalars(select(ProgramArchetype.id).where(ProgramArchetype.sport_code==sport))).all()
        phases=(await session.scalars(select(PhaseTemplate).where(PhaseTemplate.archetype_id.in_(archetype_ids)))).all() if archetype_ids else []
        week_templates=(await session.scalars(select(WeekTemplate).where(WeekTemplate.sport_code==sport))).all()
        coverage_errors=package_coverage_errors(
            sport,
            demands=demands,
            priorities=priorities,
            recipes=recipes,
            phases=phases,
            week_templates=week_templates,
        )
        counts={
            "taxa":await session.scalar(select(func.count()).select_from(SportTaxon).where(SportTaxon.sport_code==sport)),
            "demands":len(demands),
            "priorities":len(priorities),
            "rules":await session.scalar(select(func.count()).select_from(PrescriptionRuleVersion).where(PrescriptionRuleVersion.sport_code==sport)),
            "recipes":len(recipes),
            "archetypes":len(archetype_ids),
            "weeks":len(week_templates),
        }
        active=await session.scalar(select(ContentRelease.id).where(ContentRelease.sport_code==sport,ContentRelease.state=="released"))
        items.append({
            "sport_code":sport,
            "counts":counts,
            "active_release_id":active,
            "coverage_ready":not coverage_errors,
            "released":bool(active),
            "complete":bool(active) and not coverage_errors,
            "missing":coverage_errors,
        })
    return {"items":items}


@router.get("/reports/conflicts")
async def conflict_report(session: AsyncSession = Depends(get_session)) -> dict:
    names=(await session.execute(select(func.lower(MethodVersion.canonical_name),func.count()).group_by(func.lower(MethodVersion.canonical_name)).having(func.count()>1))).all()
    orphan_slots=(await session.execute(select(RecipeSlot.id,RecipeSlot.required_quality,RecipeSlot.training_role).where(~select(MethodEffect.id).where(MethodEffect.quality_code==RecipeSlot.required_quality,MethodEffect.training_role==RecipeSlot.training_role).exists()))).all()
    relations=(await session.scalars(select(MethodRelation).where(MethodRelation.status!="retired"))).all(); progression_error=None
    try: validate_progression_dag(relations)
    except KnowledgeValidationError as exc: progression_error=str(exc)
    return {"duplicate_names":[{"name":name,"count":count} for name,count in names],"orphan_recipe_slots":[{"id":row.id,"quality":row.required_quality,"role":row.training_role} for row in orphan_slots],"progression_error":progression_error}

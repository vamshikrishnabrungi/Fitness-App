import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id, require_roles
from backend.app.maps.models import OSMGraphVersion, OSMRegion, StreetEdge
from backend.app.maps.osm_ingestion import activate_graph
from backend.app.activities.models import Activity, ImportJob
from backend.app.athletes.models import AthleteProfile
from backend.app.competition.models import Challenge, Club, ClubBan, ClubMembership, Race, TerritoryCurrentControl
from backend.app.identity.models import AccountDeletionRequest, ConsentRecord, EmailIdentity, RefreshSession, Subscription, User, UserRole
from backend.app.nutrition.models import FoodAnalysis
from backend.app.operations.models import AuditEvent, ConsumerReceipt, FeatureFlag, Job, OutboxEvent
from .knowledge_router import router as knowledge_router
from .schemas import AdminClubStatusUpdate, AdminUserStatusUpdate, FeatureFlagMutation, OSMGraphCreate, OSMGraphStatusCommand, OSMRegionCreate, RoleMutation

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("content_editor", "content_publisher", "platform_admin"))])

router.include_router(knowledge_router)


@router.get("/users")
async def admin_users(query: str = "", subscription: str = "all", offset: int = 0, limit: int = 50, session: AsyncSession = Depends(get_session)) -> dict:
    """User and entitlement view used by the deliberately small Admin Studio."""
    limit = max(1, min(limit, 250))
    statement = (
        select(User, EmailIdentity, Subscription)
        .join(EmailIdentity, (EmailIdentity.user_id == User.id) & EmailIdentity.primary.is_(True))
        .outerjoin(Subscription, Subscription.user_id == User.id)
        .where(User.display_name != "Local Admin Studio")
        .order_by(User.created_at.desc(), User.id.desc())
    )
    if query.strip():
        pattern = f"%{query.strip().lower()}%"
        statement = statement.where(or_(func.lower(User.display_name).like(pattern), EmailIdentity.normalized_email.like(pattern)))
    active_statuses = ("active", "trialing")
    if subscription == "subscribed":
        statement = statement.where(Subscription.status.in_(active_statuses))
    elif subscription == "not_subscribed":
        statement = statement.where(or_(Subscription.id.is_(None), Subscription.status.not_in(active_statuses)))
    offset = max(0, offset)
    rows = (await session.execute(statement.offset(offset).limit(limit + 1))).all()
    page = rows[:limit]
    total = int(await session.scalar(select(func.count()).select_from(User).where(User.display_name != "Local Admin Studio")) or 0)
    subscribed = int(await session.scalar(select(func.count()).select_from(Subscription).join(User, User.id == Subscription.user_id).where(User.display_name != "Local Admin Studio", Subscription.status.in_(active_statuses))) or 0)
    return {
        "summary": {"total": total, "subscribed": subscribed, "not_subscribed": total - subscribed},
        "items": [
            {
                "id": user.id,
                "display_name": user.display_name,
                "email": identity.email,
                "status": user.status,
                "signed_up_at": user.created_at,
                "subscription_status": entitlement.status if entitlement else "not_subscribed",
                "plan_code": entitlement.plan_code if entitlement else None,
                "subscription_ends_at": entitlement.current_period_ends_at if entitlement else None,
            }
            for user, identity, entitlement in page
        ],
        "offset": offset,
        "limit": limit,
        "has_more": len(rows) > limit,
    }


@router.get("/users/{user_id}")
async def admin_user_detail(user_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    user = await session.get(User, user_id)
    if user is None or user.display_name == "Local Admin Studio":
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    identity = await session.scalar(select(EmailIdentity).where(EmailIdentity.user_id == user_id, EmailIdentity.primary.is_(True)))
    subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user_id))
    sessions = (await session.scalars(select(RefreshSession).where(RefreshSession.user_id == user_id).order_by(RefreshSession.created_at.desc()))).all()
    consents = (await session.scalars(select(ConsentRecord).where(ConsentRecord.user_id == user_id).order_by(ConsentRecord.recorded_at.desc()))).all()
    deletion = await session.scalar(select(AccountDeletionRequest).where(AccountDeletionRequest.user_id == user_id).order_by(AccountDeletionRequest.created_at.desc()))
    return {
        "id": user.id, "display_name": user.display_name, "email": identity.email if identity else None,
        "status": user.status, "onboarding_completed": user.onboarding_completed, "signed_up_at": user.created_at,
        "last_seen_at": user.last_seen_at, "version": user.version,
        "subscription": ({"status": subscription.status, "plan_code": subscription.plan_code, "provider": subscription.provider,
            "current_period_starts_at": subscription.current_period_starts_at, "current_period_ends_at": subscription.current_period_ends_at,
            "canceled_at": subscription.canceled_at} if subscription else None),
        "sessions": [{"id": row.id, "device_name": row.device_name, "last_used_at": row.last_used_at,
            "expires_at": row.expires_at, "revoked_at": row.revoked_at} for row in sessions],
        "consents": [{"consent_type": row.consent_type, "policy_version": row.policy_version,
            "granted": row.granted, "recorded_at": row.recorded_at} for row in consents],
        "deletion_request": ({"id": deletion.id, "status": deletion.status, "requested_at": deletion.requested_at} if deletion else None),
    }


@router.put("/users/{user_id}/status")
async def admin_user_status(user_id: UUID, body: AdminUserStatusUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    user = await session.get(User, user_id, with_for_update=True)
    if user is None or user.display_name == "Local Admin Studio":
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    if user.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the user and try again.")
    before = user.status
    user.status = body.status
    user.version += 1
    if body.status != "active":
        await session.execute(update(RefreshSession).where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
    session.add(AuditEvent(actor_user_id=actor, action="identity.user.status_changed", subject_type="user", subject_id=user.id, before={"status": before}, after={"status": body.status}, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return {"id": user.id, "status": user.status, "version": user.version}


@router.post("/users/{user_id}/revoke-sessions")
async def admin_revoke_user_sessions(user_id: UUID, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if await session.get(User, user_id) is None:
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    result = await session.execute(update(RefreshSession).where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
    session.add(AuditEvent(actor_user_id=actor, action="identity.user.sessions_revoked", subject_type="user", subject_id=user_id, before=None, after={"count": result.rowcount}, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return {"revoked": result.rowcount}


@router.get("/clubs")
async def admin_clubs(query: str = "", status: str = "active", offset: int = 0, limit: int = 50, session: AsyncSession = Depends(get_session)) -> dict:
    """Operational club catalogue. This deliberately exposes no athlete-private activity data."""
    limit = max(1, min(limit, 250))
    offset = max(0, offset)
    statement = (
        select(Club, func.count(ClubMembership.id).filter(ClubMembership.status == "active").label("member_count"))
        .outerjoin(ClubMembership, ClubMembership.club_id == Club.id)
        .group_by(Club.id)
        .order_by(Club.created_at.desc(), Club.id.desc())
    )
    if query.strip():
        pattern = f"%{query.strip().lower()}%"
        statement = statement.where(or_(func.lower(Club.name).like(pattern), func.lower(Club.slug).like(pattern)))
    if status in {"active", "archived"}:
        statement = statement.where(Club.status == status)
    rows = (await session.execute(statement.offset(offset).limit(limit + 1))).all()
    page = rows[:limit]
    total = int(await session.scalar(select(func.count()).select_from(Club)) or 0)
    active = int(await session.scalar(select(func.count()).select_from(Club).where(Club.status == "active")) or 0)
    private = int(await session.scalar(select(func.count()).select_from(Club).where(Club.status == "active", Club.visibility == "private")) or 0)
    pending_requests = int(await session.scalar(select(func.count()).select_from(ClubMembership).where(ClubMembership.status == "pending")) or 0)
    return {
        "summary": {"total": total, "active": active, "archived": total - active, "private": private, "pending_requests": pending_requests},
        "items": [{"id": club.id, "name": club.name, "slug": club.slug, "visibility": club.visibility, "timezone": club.timezone, "status": club.status, "member_count": member_count, "created_at": club.created_at} for club, member_count in page],
        "offset": offset, "limit": limit, "has_more": len(rows) > limit,
    }


@router.get("/clubs/{club_id}")
async def admin_club_detail(club_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    club = await session.get(Club, club_id)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    memberships = (
        await session.execute(
            select(ClubMembership, User, EmailIdentity)
            .join(AthleteProfile, AthleteProfile.id == ClubMembership.athlete_id)
            .join(User, User.id == AthleteProfile.user_id)
            .outerjoin(EmailIdentity, (EmailIdentity.user_id == User.id) & EmailIdentity.primary.is_(True))
            .where(ClubMembership.club_id == club.id)
            .order_by(ClubMembership.role.desc(), ClubMembership.created_at)
            .limit(250)
        )
    ).all()
    challenge_count = int(await session.scalar(select(func.count()).select_from(Challenge).where(Challenge.club_id == club.id)) or 0)
    race_count = int(await session.scalar(select(func.count()).select_from(Race).where(Race.club_id == club.id)) or 0)
    territory_count = int(await session.scalar(select(func.count()).select_from(TerritoryCurrentControl).where(TerritoryCurrentControl.club_id == club.id, TerritoryCurrentControl.controller_type == "club")) or 0)
    ban_count = int(await session.scalar(select(func.count()).select_from(ClubBan).where(ClubBan.club_id == club.id)) or 0)
    return {
        "id": club.id, "name": club.name, "slug": club.slug, "description": club.description, "visibility": club.visibility,
        "timezone": club.timezone, "rules": club.rules, "status": club.status, "created_at": club.created_at,
        "member_count": sum(1 for membership, _, _ in memberships if membership.status == "active"),
        "pending_request_count": sum(1 for membership, _, _ in memberships if membership.status == "pending"),
        "challenge_count": challenge_count, "race_count": race_count, "territory_edge_count": territory_count, "ban_count": ban_count,
        "members": [{"id": membership.id, "athlete_id": membership.athlete_id, "display_name": user.display_name, "email": identity.email if identity else None, "role": membership.role, "status": membership.status, "requested_at": membership.requested_at, "joined_at": membership.joined_at} for membership, user, identity in memberships],
    }


@router.put("/clubs/{club_id}/status")
async def admin_club_status(club_id: UUID, body: AdminClubStatusUpdate, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    club = await session.get(Club, club_id, with_for_update=True)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    before = club.status
    club.status = body.status
    session.add(AuditEvent(actor_user_id=actor, action="competition.club.status_changed", subject_type="club", subject_id=club.id, before={"status": before}, after={"status": club.status}, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return {"id": club.id, "status": club.status}


@router.get("/osm/regions", dependencies=[Depends(require_roles("platform_admin"))])
async def osm_regions(session: AsyncSession = Depends(get_session)) -> dict:
    regions = (await session.scalars(select(OSMRegion).order_by(OSMRegion.code))).all()
    graphs = (await session.scalars(select(OSMGraphVersion).order_by(OSMGraphVersion.source_timestamp.desc()))).all()
    by_region: dict[UUID, list[dict]] = {}
    for graph in graphs:
        by_region.setdefault(graph.region_id, []).append({"id": graph.id, "version_code": graph.version_code, "source_timestamp": graph.source_timestamp, "status": graph.status, "activated_at": graph.activated_at, "version": graph.version})
    return {"items": [{"id": region.id, "code": region.code, "name": region.name, "pbf_object": region.pbf_object, "status": region.status, "version": region.version, "graphs": by_region.get(region.id, [])} for region in regions]}


@router.post("/osm/regions", status_code=201, dependencies=[Depends(require_roles("platform_admin"))])
async def create_osm_region(
    body: OSMRegionCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    geometry_type = body.boundary_geojson.get("type")
    if geometry_type not in {"Polygon", "MultiPolygon"} or not body.boundary_geojson.get("coordinates"):
        raise ProblemError(422, "osm_boundary_invalid", "Invalid region boundary", "Provide a Polygon or MultiPolygon GeoJSON boundary.")
    row = OSMRegion(
        code=body.code,
        name=body.name,
        pbf_object=body.pbf_object,
        status="pending",
        boundary=func.ST_Multi(func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(body.boundary_geojson)), 4326)),
    )
    session.add(row)
    await session.flush()
    session.add(AuditEvent(actor_user_id=actor, action="maps.osm_region.created", subject_type="osm_region", subject_id=row.id, before=None, after={"code": row.code, "pbf_object": row.pbf_object}, created_at=datetime.now(timezone.utc)))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409, "osm_region_exists", "OSM region exists", "Choose a unique region code.") from exc
    return {"id": row.id, "code": row.code, "status": row.status, "version": row.version}


@router.post("/osm/graphs", status_code=201, dependencies=[Depends(require_roles("platform_admin"))])
async def create_osm_graph(
    body: OSMGraphCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    region = await session.get(OSMRegion, body.region_id, with_for_update=True)
    if region is None:
        raise ProblemError(404, "osm_region_not_found", "OSM region not found", "Register the OSM region first.")
    row = OSMGraphVersion(**body.model_dump(), status="building")
    session.add(row)
    await session.flush()
    region.status = "building"
    region.version += 1
    session.add(AuditEvent(actor_user_id=actor, action="maps.osm_graph.registered", subject_type="osm_graph_version", subject_id=row.id, before=None, after={"region_id": str(region.id), "version_code": row.version_code}, created_at=datetime.now(timezone.utc)))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409, "osm_graph_exists", "OSM graph exists", "This graph version is already registered.") from exc
    return {"id": row.id, "region_id": row.region_id, "status": row.status, "version": row.version}


@router.post("/osm/graphs/{graph_id}/status", dependencies=[Depends(require_roles("platform_admin"))])
async def mark_osm_graph_validating(
    graph_id: UUID,
    body: OSMGraphStatusCommand,
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    graph = await session.get(OSMGraphVersion, graph_id, with_for_update=True)
    if graph is None:
        raise ProblemError(404, "osm_graph_not_found", "OSM graph not found", "The graph version does not exist.")
    if graph.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload graph status and try again.")
    if graph.status != "building":
        raise ProblemError(409, "osm_graph_not_building", "Graph state invalid", "Only a building graph can move to validation.")
    edge_count = int(await session.scalar(select(func.count()).select_from(StreetEdge).where(StreetEdge.graph_version_id == graph.id)) or 0)
    if edge_count < 1:
        raise ProblemError(409, "osm_edges_missing", "Claim edges missing", "Load and validate the region claim edges first.")
    graph.status = "validating"
    graph.version += 1
    session.add(AuditEvent(actor_user_id=actor, action="maps.osm_graph.validating", subject_type="osm_graph_version", subject_id=graph.id, before={"status": "building"}, after={"status": graph.status, "edge_count": edge_count}, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return {"id": graph.id, "status": graph.status, "edge_count": edge_count, "version": graph.version}


@router.post("/osm/graphs/{graph_id}/activate", dependencies=[Depends(require_roles("platform_admin"))])
async def activate_osm_graph(
    graph_id: UUID,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        result = await activate_graph(session, graph_id)
    except ValueError as exc:
        raise ProblemError(409, "osm_graph_not_activatable", "Graph cannot be activated", str(exc)) from exc
    session.add(AuditEvent(actor_user_id=actor, action="maps.osm_graph.activated", subject_type="osm_graph_version", subject_id=graph_id, before=None, after=result, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return result


@router.get("/operations/overview", dependencies=[Depends(require_roles("platform_admin"))])
async def operations_overview(session: AsyncSession = Depends(get_session)) -> dict:
    async def count(model, *conditions) -> int:
        return int(await session.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)

    return {
        "outbox_unpublished": await count(OutboxEvent, OutboxEvent.published_at.is_(None)),
        "consumer_retries": await count(ConsumerReceipt, ConsumerReceipt.status == "retry"),
        "jobs_queued": await count(Job, Job.status.in_(("queued", "processing"))),
        "jobs_failed": await count(Job, Job.status == "failed"),
        "imports_processing": await count(ImportJob, ImportJob.status.in_(("awaiting_upload", "queued", "processing"))),
        "imports_failed": await count(ImportJob, ImportJob.status == "failed"),
        "activities_processing": await count(Activity, Activity.status.in_(("uploaded", "processing", "provisional"))),
        "activities_rejected": await count(Activity, Activity.status == "rejected"),
        "food_processing": await count(FoodAnalysis, FoodAnalysis.status.in_(("queued", "processing"))),
        "food_failed": await count(FoodAnalysis, FoodAnalysis.status == "failed"),
    }


@router.get("/operations/events", dependencies=[Depends(require_roles("platform_admin"))])
async def operations_events(limit: int = 100, session: AsyncSession = Depends(get_session)) -> dict:
    limit = max(1, min(limit, 250))
    rows = (
        await session.execute(
            select(OutboxEvent, ConsumerReceipt)
            .outerjoin(ConsumerReceipt, ConsumerReceipt.event_id == OutboxEvent.id)
            .where(
                or_(
                    OutboxEvent.published_at.is_(None),
                    OutboxEvent.last_error.is_not(None),
                    ConsumerReceipt.status == "retry",
                )
            )
            .order_by(OutboxEvent.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": event.id,
                "topic": event.topic,
                "event_type": event.event_type,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
                "created_at": event.created_at,
                "published_at": event.published_at,
                "publish_attempts": event.attempts,
                "publish_error": event.last_error,
                "consumer": receipt.consumer_code if receipt else None,
                "consumer_status": receipt.status if receipt else None,
                "consumer_attempts": receipt.attempts if receipt else 0,
                "consumer_error": receipt.last_error if receipt else None,
            }
            for event, receipt in rows
        ]
    }


@router.post("/operations/events/{event_id}/replay", dependencies=[Depends(require_roles("platform_admin"))])
async def replay_event(
    event_id: UUID,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    event = await session.get(OutboxEvent, event_id, with_for_update=True)
    if event is None:
        raise ProblemError(404, "event_not_found", "Event not found", "The outbox event does not exist.")
    receipts = (
        await session.scalars(
            select(ConsumerReceipt).where(ConsumerReceipt.event_id == event.id).with_for_update()
        )
    ).all()
    for receipt in receipts:
        receipt.status = "retry"
        receipt.started_at = datetime.now(timezone.utc)
        receipt.completed_at = None
        receipt.attempts = 0
        receipt.last_error = None
    event.published_at = None
    event.last_error = None
    session.add(AuditEvent(actor_user_id=actor, action="operations.event.replay_requested", subject_type="outbox_event", subject_id=event.id, before=None, after={"event_type": event.event_type}, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return {"id": event.id, "status": "queued_for_replay"}


@router.get("/roles/users", dependencies=[Depends(require_roles("platform_admin"))])
async def role_users(query: str = "", limit: int = 50, session: AsyncSession = Depends(get_session)) -> dict:
    limit = max(1, min(limit, 100))
    statement = (
        select(User, EmailIdentity)
        .join(EmailIdentity, EmailIdentity.user_id == User.id)
        .where(EmailIdentity.primary.is_(True))
        .order_by(User.display_name, User.id)
        .limit(limit)
    )
    if query.strip():
        pattern = f"%{query.strip().lower()}%"
        statement = statement.where(
            or_(func.lower(User.display_name).like(pattern), EmailIdentity.normalized_email.like(pattern))
        )
    rows = (await session.execute(statement)).all()
    output = []
    for user, email in rows:
        roles = list(await session.scalars(select(UserRole.role).where(UserRole.user_id == user.id).order_by(UserRole.role)))
        output.append({"id": user.id, "display_name": user.display_name, "email": email.email, "status": user.status, "roles": roles, "version": user.version})
    return {"items": output}


@router.get("/operations/audit", dependencies=[Depends(require_roles("platform_admin"))])
async def audit_history(action: str = "", subject_type: str = "", limit: int = 100, session: AsyncSession = Depends(get_session)) -> dict:
    statement=select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(max(1,min(limit,250)))
    if action: statement=statement.where(AuditEvent.action.ilike(f"%{action.strip()}%"))
    if subject_type: statement=statement.where(AuditEvent.subject_type==subject_type)
    return {"items":[{column.name:getattr(row,column.name) for column in row.__table__.columns} for row in (await session.scalars(statement)).all()]}


@router.get("/operations/feature-flags", dependencies=[Depends(require_roles("platform_admin"))])
async def feature_flags(session: AsyncSession = Depends(get_session)) -> dict:
    return {"items":[{column.name:getattr(row,column.name) for column in row.__table__.columns} for row in (await session.scalars(select(FeatureFlag).order_by(FeatureFlag.code))).all()]}


@router.put("/operations/feature-flags/{code}", dependencies=[Depends(require_roles("platform_admin"))])
async def upsert_feature_flag(code: str, body: FeatureFlagMutation, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    if code!=body.code: raise ProblemError(422,"feature_flag_code_mismatch","Feature flag mismatch","The path and payload codes must match.")
    row=await session.scalar(select(FeatureFlag).where(FeatureFlag.code==code).with_for_update())
    before=None
    if row is None:
        if body.expected_version is not None: raise ProblemError(409,"version_conflict","Version conflict","The feature flag does not exist.")
        row=FeatureFlag(code=code,enabled=body.enabled,rules=body.rules); session.add(row); await session.flush()
    else:
        if body.expected_version is None or row.version!=body.expected_version: raise ProblemError(409,"version_conflict","Version conflict","Reload the feature flag and try again.")
        before={"enabled":row.enabled,"rules":row.rules,"version":row.version}; row.enabled=body.enabled; row.rules=body.rules; row.version+=1
    after={"code":row.code,"enabled":row.enabled,"rules":row.rules,"version":row.version}; session.add(AuditEvent(actor_user_id=actor,action="operations.feature_flag.updated",subject_type="feature_flag",subject_id=row.id,before=before,after=after,created_at=datetime.now(timezone.utc))); await session.commit(); return {"id":row.id,**after}


@router.post("/roles/users/{target_user_id}", status_code=201, dependencies=[Depends(require_roles("platform_admin"))])
async def grant_role(
    target_user_id: UUID,
    body: RoleMutation,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    target = await session.get(User, target_user_id)
    if target is None:
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    existing = await session.scalar(select(UserRole).where(UserRole.user_id == target.id, UserRole.role == body.role))
    if existing:
        return {"id": existing.id, "user_id": target.id, "role": existing.role}
    row = UserRole(user_id=target.id, role=body.role, granted_by=actor, granted_at=datetime.now(timezone.utc))
    session.add(row)
    session.add(AuditEvent(actor_user_id=actor, action="identity.role.granted", subject_type="user", subject_id=target.id, before=None, after={"role": body.role}, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return {"id": row.id, "user_id": target.id, "role": row.role}


@router.delete("/roles/users/{target_user_id}/{role}", status_code=204, dependencies=[Depends(require_roles("platform_admin"))])
async def revoke_role(
    target_user_id: UUID,
    role: str,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    actor: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    if role not in {"content_editor", "content_publisher", "moderator", "platform_admin"}:
        raise ProblemError(422, "role_invalid", "Invalid role", "Choose a supported administrative role.")
    if target_user_id == actor and role == "platform_admin":
        raise ProblemError(409, "self_admin_revoke_forbidden", "Role required", "You cannot remove your own platform administrator role.")
    row = await session.scalar(select(UserRole).where(UserRole.user_id == target_user_id, UserRole.role == role).with_for_update())
    if row is None:
        return
    if role == "platform_admin":
        admin_count = int(await session.scalar(select(func.count()).select_from(UserRole).where(UserRole.role == "platform_admin")) or 0)
        if admin_count <= 1:
            raise ProblemError(409, "last_admin_revoke_forbidden", "Role required", "At least one platform administrator must remain.")
    await session.delete(row)
    session.add(AuditEvent(actor_user_id=actor, action="identity.role.revoked", subject_type="user", subject_id=target_user_id, before={"role": role}, after=None, created_at=datetime.now(timezone.utc)))
    await session.commit()

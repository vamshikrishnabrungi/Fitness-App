from __future__ import annotations

import hashlib
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from backend.club_domain import (
    ClubChallengeCreate,
    ClubCreate,
    ClubInvitationCreate,
    ClubRaceCreate,
    ClubUpdate,
    CompetitionFlagCreate,
    MembershipDecision,
    ModerationAppealCreate,
    ModerationDecisionCreate,
    OwnershipTransfer,
    PrimaryClubUpdate,
    PushTokenCreate,
    RoleUpdate,
    TerritoryTileSessionCreate,
    invitation_token,
)
from backend.club_store import (
    ClubStore,
    DomainConflict,
    DomainForbidden,
    DomainNotFound,
    PlatformUnavailable,
)
from backend.platform_ids import new_id


def _problem(status: int, code: str, detail: str, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://runlete.app/problems/{code}",
            "title": code.replace("_", " ").title(),
            "status": status,
            "detail": detail,
            "instance": str(request.url.path),
            "code": code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


def _store() -> ClubStore:
    try:
        return ClubStore()
    except PlatformUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _optional_store() -> Optional[ClubStore]:
    try:
        return ClubStore()
    except PlatformUnavailable:
        return None


def _idempotency_key(value: Optional[str]) -> str:
    if not value or len(value.strip()) < 8 or len(value) > 200:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header must contain between 8 and 200 characters",
        )
    return value.strip()


async def _idempotent(
    store: ClubStore,
    *,
    user_id: str,
    scope: str,
    key: str,
    payload: Any,
    operation: Callable[[], Any],
) -> Any:
    request_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()
    async with store.idempotency_lock(user_id, scope, key):
        saved = await store.idempotency_result(user_id, scope, key, request_hash)
        if saved is not None:
            return saved
        result = await operation()
        await store.save_idempotency_result(
            user_id, scope, key, request_hash, result
        )
        return result


def _push_cipher() -> Fernet:
    configured = (os.environ.get("PUSH_TOKEN_ENCRYPTION_KEY") or "").strip()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail="Push token encryption is not configured",
        )
    try:
        return Fernet(configured.encode())
    except (ValueError, InvalidToken) as exc:
        raise HTTPException(status_code=503, detail="Push encryption configuration is invalid") from exc


def install_club_exception_handlers(app: Any) -> None:
    async def not_found(request: Request, exc: DomainNotFound):
        return _problem(404, "resource_not_found", str(exc), request)

    async def forbidden(request: Request, exc: DomainForbidden):
        return _problem(403, "forbidden", str(exc), request)

    async def conflict(request: Request, exc: DomainConflict):
        return _problem(409, "conflict", str(exc), request)

    app.add_exception_handler(DomainNotFound, not_found)
    app.add_exception_handler(DomainForbidden, forbidden)
    app.add_exception_handler(DomainConflict, conflict)


def build_club_router(
    *,
    get_current_user: Callable[..., Any],
    require_admin: Callable[..., Any],
    mongo_db: Any,
    tile_secret: str,
    legacy_challenge_join: Optional[Callable[..., Any]] = None,
    legacy_challenge_leaderboard: Optional[Callable[..., Any]] = None,
    legacy_race_join: Optional[Callable[..., Any]] = None,
    legacy_race_results: Optional[Callable[..., Any]] = None,
    legacy_territory_mine: Optional[Callable[..., Any]] = None,
) -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["run-clubs"])

    async def enrich_users(page: Dict[str, Any]) -> Dict[str, Any]:
        user_ids = list(
            {
                str(item["user_id"])
                for item in page.get("items", [])
                if item.get("user_id")
            }
        )
        users = (
            await mongo_db.users.find(
                {"id": {"$in": user_ids}},
                {"_id": 0, "id": 1, "name": 1, "profile.avatar_url": 1},
            ).to_list(len(user_ids))
            if user_ids
            else []
        )
        by_id = {user["id"]: user for user in users}
        for item in page.get("items", []):
            user = by_id.get(str(item.get("user_id")))
            if user:
                item["athlete"] = {
                    "id": user["id"],
                    "name": user.get("name") or "Runner",
                    "avatar_url": (user.get("profile") or {}).get("avatar_url"),
                }
        return page

    @router.post("/clubs", status_code=201)
    async def create_club(
        payload: ClubCreate,
        request: Request,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        body = payload.model_dump()
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope="club.create",
            key=key,
            payload=body,
            operation=lambda: store.create_club(
                body,
                current_user["id"],
                request_id=getattr(request.state, "request_id", key),
            ),
        )

    @router.get("/clubs")
    async def discover_clubs(
        q: Optional[str] = Query(default=None, max_length=120),
        region_id: Optional[str] = None,
        membership: Optional[str] = Query(default=None, pattern="^(mine)?$"),
        cursor: Optional[str] = None,
        limit: int = Query(default=20, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.list_clubs(
            current_user["id"],
            query=q,
            region_id=region_id,
            membership=membership,
            cursor=cursor,
            limit=limit,
        )

    @router.get("/clubs/mine")
    async def my_clubs(
        cursor: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.list_clubs(
            current_user["id"], membership="mine", cursor=cursor, limit=limit
        )

    @router.get("/clubs/{club_id}")
    async def club_detail(
        club_id: str,
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.get_club(club_id, current_user["id"])

    @router.patch("/clubs/{club_id}")
    async def update_club(
        club_id: str,
        payload: ClubUpdate,
        request: Request,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        body = payload.model_dump(exclude_unset=True)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"club.update:{club_id}",
            key=key,
            payload=body,
            operation=lambda: store.update_club(
                club_id,
                current_user["id"],
                body,
                request_id=getattr(request.state, "request_id", key),
            ),
        )

    @router.post("/clubs/{club_id}/archive")
    async def archive_club(
        club_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"club.archive:{club_id}",
            key=key,
            payload={"archived": True},
            operation=lambda: store.archive(club_id, current_user["id"], True),
        )

    @router.post("/clubs/{club_id}/restore")
    async def restore_club(
        club_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"club.restore:{club_id}",
            key=key,
            payload={"archived": False},
            operation=lambda: store.archive(club_id, current_user["id"], False),
        )

    @router.post("/clubs/{club_id}/join")
    async def join_club(
        club_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"club.join:{club_id}",
            key=key,
            payload={"club_id": club_id},
            operation=lambda: store.join(club_id, current_user["id"]),
        )

    @router.delete("/clubs/{club_id}/membership")
    async def leave_or_cancel_membership(
        club_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.leave:{club_id}",
            key=key,
            payload={"club_id": club_id},
            operation=lambda: store.end_membership(
                club_id, current_user["id"], current_user["id"]
            ),
        )

    @router.get("/clubs/{club_id}/members")
    async def club_members(
        club_id: str,
        status: str = Query(default="active", pattern="^(active|pending|rejected|removed|banned)$"),
        cursor: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        page = await store.members(
            club_id, current_user["id"], status=status, cursor=cursor, limit=limit
        )
        return await enrich_users(page)

    @router.post("/clubs/{club_id}/members/{user_id}/approve")
    async def approve_member(
        club_id: str,
        user_id: str,
        payload: MembershipDecision,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.approve:{club_id}:{user_id}",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.review_membership(
                club_id, user_id, current_user["id"], approve=True, reason=payload.reason
            ),
        )

    @router.post("/clubs/{club_id}/members/{user_id}/reject")
    async def reject_member(
        club_id: str,
        user_id: str,
        payload: MembershipDecision,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.reject:{club_id}:{user_id}",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.review_membership(
                club_id, user_id, current_user["id"], approve=False, reason=payload.reason
            ),
        )

    @router.delete("/clubs/{club_id}/members/{user_id}")
    async def remove_member(
        club_id: str,
        user_id: str,
        reason: Optional[str] = Query(default=None, max_length=1_000),
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.remove:{club_id}:{user_id}",
            key=key,
            payload={"reason": reason},
            operation=lambda: store.end_membership(
                club_id, user_id, current_user["id"], reason=reason
            ),
        )

    @router.post("/clubs/{club_id}/members/{user_id}/ban")
    async def ban_member(
        club_id: str,
        user_id: str,
        payload: MembershipDecision,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.ban:{club_id}:{user_id}",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.end_membership(
                club_id,
                user_id,
                current_user["id"],
                ban=True,
                reason=payload.reason,
            ),
        )

    @router.post("/clubs/{club_id}/members/{user_id}/unban")
    async def unban_member(
        club_id: str,
        user_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.unban:{club_id}:{user_id}",
            key=key,
            payload={"user_id": user_id},
            operation=lambda: store.revoke_ban(
                club_id, user_id, current_user["id"]
            ),
        )

    @router.patch("/clubs/{club_id}/members/{user_id}/role")
    async def change_role(
        club_id: str,
        user_id: str,
        payload: RoleUpdate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"membership.role:{club_id}:{user_id}",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.update_role(
                club_id, user_id, current_user["id"], payload.role, payload.version
            ),
        )

    @router.post("/clubs/{club_id}/transfer-ownership")
    async def transfer_ownership(
        club_id: str,
        payload: OwnershipTransfer,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"club.transfer:{club_id}",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.transfer_ownership(
                club_id,
                current_user["id"],
                payload.new_owner_user_id,
                payload.version,
            ),
        )

    @router.put("/clubs/primary")
    async def select_primary_club(
        payload: PrimaryClubUpdate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope="club.primary",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.set_primary_club(current_user["id"], payload.club_id),
        )

    @router.post("/clubs/{club_id}/invitations", status_code=201)
    async def create_invitation(
        club_id: str,
        payload: ClubInvitationCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        token, token_hash = invitation_token()
        async def create_with_token():
            created = await store.create_invitation(
                club_id, current_user["id"], payload.model_dump(), token_hash
            )
            created["accept_token"] = token
            return created
        invitation = await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"invitation.create:{club_id}",
            key=key,
            payload=payload.model_dump(),
            operation=create_with_token,
        )
        return invitation

    @router.get("/clubs/{club_id}/invitations")
    async def list_invitations(
        club_id: str,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return {
            "items": await store.invitations(
                club_id, current_user["id"], limit
            ),
            "next_cursor": None,
        }

    @router.delete(
        "/clubs/{club_id}/invitations/{invitation_id}", status_code=204
    )
    async def revoke_invitation(
        club_id: str,
        invitation_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"invitation.revoke:{club_id}:{invitation_id}",
            key=key,
            payload={"invitation_id": invitation_id},
            operation=lambda: store.revoke_invitation(
                club_id, invitation_id, current_user["id"]
            ),
        )
        return Response(status_code=204)

    @router.post("/club-invitations/{token}/accept")
    async def accept_invitation(
        token: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        email_hash = (
            hashlib.sha256(str(current_user.get("email")).strip().lower().encode()).hexdigest()
            if current_user.get("email")
            else None
        )
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope="invitation.accept",
            key=key,
            payload={"token_hash": token_hash},
            operation=lambda: store.accept_invitation(
                token_hash, current_user["id"], email_hash
            ),
        )

    @router.get("/clubs/{club_id}/activity")
    async def club_activity(
        club_id: str,
        cursor: Optional[str] = None,
        limit: int = Query(default=30, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.club_timeline(
            club_id, current_user["id"], cursor=cursor, limit=limit
        )

    @router.get("/clubs/{club_id}/leaderboards")
    async def club_leaderboard(
        club_id: str,
        period: str = Query(default="week", pattern="^(week|month|season|all)$"),
        metric: str = Query(
            default="distance",
            pattern="^(distance|moving_time|runs|consistency|territory_gain)$",
        ),
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        rows = await store.leaderboard(
            club_id,
            current_user["id"],
            period=period,
            metric=metric,
            limit=limit,
        )
        return await enrich_users({"items": rows, "next_cursor": None})

    @router.get("/seasons")
    async def seasons(
        limit: int = Query(default=12, ge=1, le=40),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return {"items": await store.seasons(limit), "next_cursor": None}

    @router.get("/leaderboards")
    async def public_leaderboard(
        scope: str = Query(default="global", pattern="^(global|city|country)$"),
        region_id: Optional[str] = None,
        subject: str = Query(default="athlete", pattern="^(athlete|club)$"),
        period: str = Query(default="week", pattern="^(week|month|season|all)$"),
        metric: str = Query(
            default="distance",
            pattern="^(distance|moving_time|runs|consistency|territory_gain)$",
        ),
        normalized: bool = False,
        limit: int = Query(default=100, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        rows = await store.public_leaderboard(
            current_user["id"],
            scope=scope,
            region_id=region_id,
            subject=subject,
            period=period,
            metric=metric,
            normalized=normalized,
            limit=limit,
        )
        page = {"items": rows, "next_cursor": None}
        return await enrich_users(page) if subject == "athlete" else page

    @router.get("/achievements")
    async def my_achievements(
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return {
            "items": await store.achievements(
                current_user["id"], club_id=None, limit=limit
            ),
            "next_cursor": None,
        }

    @router.get("/clubs/{club_id}/achievements")
    async def club_achievements(
        club_id: str,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        rows = await store.achievements(
            current_user["id"], club_id=club_id, limit=limit
        )
        return await enrich_users({"items": rows, "next_cursor": None})

    @router.post("/clubs/{club_id}/challenges", status_code=201)
    async def create_challenge(
        club_id: str,
        payload: ClubChallengeCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        body = payload.model_dump()
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"challenge.create:{club_id}",
            key=key,
            payload=body,
            operation=lambda: store.create_challenge(
                club_id, current_user["id"], body
            ),
        )

    @router.get("/challenges")
    async def my_open_challenges(
        cursor: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.athlete_challenges(current_user["id"], cursor, limit)

    @router.get("/clubs/{club_id}/challenges")
    async def list_challenges(
        club_id: str,
        cursor: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.list_challenges(
            club_id, current_user["id"], cursor, limit
        )

    @router.post("/challenges/{challenge_id}/join")
    async def join_challenge(
        challenge_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: Optional[ClubStore] = Depends(_optional_store),
    ):
        if store is None:
            if legacy_challenge_join:
                return await legacy_challenge_join(challenge_id, current_user)
            raise HTTPException(status_code=503, detail="Club competition is not configured")
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"challenge.join:{challenge_id}",
            key=key,
            payload={"challenge_id": challenge_id},
            operation=lambda: store.join_challenge(challenge_id, current_user["id"]),
        )

    @router.get("/challenges/{challenge_id}/leaderboard")
    async def challenge_leaderboard(
        challenge_id: str,
        limit: int = Query(default=100, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: Optional[ClubStore] = Depends(_optional_store),
    ):
        if store is None:
            if legacy_challenge_leaderboard:
                return await legacy_challenge_leaderboard(challenge_id, current_user)
            raise HTTPException(status_code=503, detail="Club competition is not configured")
        rows = await store.challenge_leaderboard(challenge_id, current_user["id"], limit)
        return await enrich_users({"items": rows, "next_cursor": None})

    @router.post("/clubs/{club_id}/races", status_code=201)
    async def create_race(
        club_id: str,
        payload: ClubRaceCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        body = payload.model_dump()
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"race.create:{club_id}",
            key=key,
            payload=body,
            operation=lambda: store.create_race(club_id, current_user["id"], body),
        )

    @router.get("/races")
    async def my_open_races(
        cursor: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.athlete_races(current_user["id"], cursor, limit)

    @router.get("/clubs/{club_id}/races")
    async def list_races(
        club_id: str,
        cursor: Optional[str] = None,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.list_races(club_id, current_user["id"], cursor, limit)

    @router.post("/races/{race_id}/join")
    async def join_race(
        race_id: str,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: Optional[ClubStore] = Depends(_optional_store),
    ):
        if store is None:
            if legacy_race_join:
                return await legacy_race_join(race_id, current_user)
            raise HTTPException(status_code=503, detail="Club competition is not configured")
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"race.join:{race_id}",
            key=key,
            payload={"race_id": race_id},
            operation=lambda: store.join_race(race_id, current_user["id"]),
        )

    @router.get("/races/{race_id}/results")
    async def race_results(
        race_id: str,
        limit: int = Query(default=100, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: Optional[ClubStore] = Depends(_optional_store),
    ):
        if store is None:
            if legacy_race_results:
                return await legacy_race_results(race_id, current_user)
            raise HTTPException(status_code=503, detail="Club competition is not configured")
        rows = await store.race_results(race_id, current_user["id"], limit)
        return await enrich_users({"items": rows, "next_cursor": None})

    @router.get("/territory/mine")
    async def my_territory(
        bbox: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
        store: Optional[ClubStore] = Depends(_optional_store),
    ):
        if store is None:
            if legacy_territory_mine:
                return await legacy_territory_mine(current_user)
            raise HTTPException(status_code=503, detail="Territory is not configured")
        parsed_bbox = [float(item) for item in bbox.split(",")] if bbox else None
        return await store.territory_geojson(
            current_user["id"],
            controller_type="athlete",
            controller_id=current_user["id"],
            bbox=parsed_bbox,
        )

    @router.get("/territory/club/{club_id}")
    async def club_territory(
        club_id: str,
        bbox: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        parsed_bbox = [float(item) for item in bbox.split(",")] if bbox else None
        return await store.territory_geojson(
            current_user["id"],
            controller_type="club",
            controller_id=club_id,
            bbox=parsed_bbox,
        )

    @router.get("/territory/edges/{street_edge_id}")
    async def territory_edge(
        street_edge_id: str,
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.territory_edge(current_user["id"], street_edge_id)

    @router.get("/territory/history")
    async def territory_history(
        street_edge_id: str,
        controller_type: str = Query(pattern="^(athlete|club)$"),
        controller_id: str = Query(min_length=1),
        cursor: Optional[str] = None,
        limit: int = Query(default=30, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.territory_history(
            current_user["id"],
            street_edge_id=street_edge_id,
            controller_type=controller_type,
            controller_id=controller_id,
            cursor=cursor,
            limit=limit,
        )

    @router.post("/territory/tile-session")
    async def territory_tile_session(
        payload: TerritoryTileSessionCreate,
        request: Request,
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        if payload.layer == "club" and payload.club_id:
            # Authorize now and again when each tile is read.
            await store.territory_geojson(
                current_user["id"],
                controller_type="club",
                controller_id=payload.club_id,
                bbox=None,
                limit=1,
            )
        public_tile_base = (
            os.environ.get("TERRITORY_PUBLIC_TILE_BASE_URL") or ""
        ).rstrip("/")
        if payload.layer == "competitors" and public_tile_base:
            expires = datetime.now(timezone.utc) + timedelta(hours=24)
            return {
                "tile_url": (
                    f"{public_tile_base}/api/v1/territory/public-tiles/"
                    "{z}/{x}/{y}.mvt"
                ),
                "expires_at": expires,
            }
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        token = jwt.encode(
            {
                "sub": current_user["id"],
                "scope": "territory:tiles",
                "layer": payload.layer,
                "club_id": payload.club_id,
                "exp": expires,
            },
            tile_secret,
            algorithm="HS256",
        )
        base = str(request.base_url).rstrip("/")
        template = (
            f"{base}/api/v1/territory/tiles/{{z}}/{{x}}/{{y}}.mvt"
            f"?layer={payload.layer}&token={token}"
        )
        if payload.club_id:
            template += f"&club_id={payload.club_id}"
        return {"tile_url": template, "expires_at": expires}

    @router.get("/territory/tiles/{z}/{x}/{y}.mvt")
    async def territory_tile(
        z: int,
        x: int,
        y: int,
        layer: str = Query(default="me", pattern="^(me|club|competitors)$"),
        club_id: Optional[str] = None,
        token: str = Query(min_length=20),
        store: ClubStore = Depends(_store),
    ):
        try:
            claims = jwt.decode(token, tile_secret, algorithms=["HS256"])
        except JWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired tile token") from exc
        if (
            claims.get("scope") != "territory:tiles"
            or claims.get("layer") != layer
            or claims.get("club_id") != club_id
            or not claims.get("sub")
        ):
            raise HTTPException(status_code=403, detail="Tile token scope mismatch")
        tile = await store.territory_tile(
            claims["sub"],
            z=z,
            x=x,
            y=y,
            layer=layer,
            club_id=club_id,
        )
        return Response(
            content=tile,
            media_type="application/vnd.mapbox-vector-tile",
            headers={"Cache-Control": "private, max-age=60"},
        )

    @router.get("/territory/public-tiles/{z}/{x}/{y}.mvt")
    async def public_competitor_territory_tile(
        z: int,
        x: int,
        y: int,
        store: ClubStore = Depends(_store),
    ):
        tile = await store.territory_tile(
            "00000000-0000-0000-0000-000000000000",
            z=z,
            x=x,
            y=y,
            layer="competitors",
            club_id=None,
        )
        return Response(
            content=tile,
            media_type="application/vnd.mapbox-vector-tile",
            headers={
                "Cache-Control": "public, max-age=60, s-maxage=60, stale-while-revalidate=300"
            },
        )

    @router.post("/moderation/flags", status_code=201)
    async def report_activity(
        payload: CompetitionFlagCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        body = payload.model_dump()
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"moderation.flag:{payload.activity_id}",
            key=key,
            payload=body,
            operation=lambda: store.create_flag(
                current_user["id"],
                payload.activity_id,
                payload.reason_code,
                payload.details,
            ),
        )

    @router.get("/moderation/flags")
    async def moderation_queue(
        status: str = Query(default="open", pattern="^(open|reviewing|upheld|dismissed|appealed)$"),
        limit: int = Query(default=100, ge=1, le=200),
        current_user: dict = Depends(require_admin),
        store: ClubStore = Depends(_store),
    ):
        return await store.moderation_queue(status, limit)

    @router.get("/moderation/my-flags")
    async def my_moderation_flags(
        limit: int = Query(default=50, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.athlete_flags(current_user["id"], limit)

    @router.post("/moderation/flags/{flag_id}/decision")
    async def moderation_decision(
        flag_id: str,
        payload: ModerationDecisionCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(require_admin),
        store: ClubStore = Depends(_store),
    ):
        _idempotency_key(idempotency_key)
        result = await store.decide_flag(
            flag_id, current_user["id"], payload.decision, payload.notes
        )
        if payload.decision in {"dismiss", "reopen"}:
            now = datetime.now(timezone.utc)
            await mongo_db.activity_outbox.update_one(
                {
                    "activity_id": result["activity_id"],
                    "event_type": "activity.completed",
                },
                {
                    "$set": {
                        "user_id": result["user_id"],
                        "status": "pending",
                        "attempts": 0,
                        "available_at": now,
                        "last_error": None,
                        "lease_expires_at": None,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "id": new_id(),
                        "created_at": now,
                    },
                },
                upsert=True,
            )
        return result

    @router.post("/moderation/flags/{flag_id}/appeal", status_code=201)
    async def moderation_appeal(
        flag_id: str,
        payload: ModerationAppealCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        key = _idempotency_key(idempotency_key)
        return await _idempotent(
            store,
            user_id=current_user["id"],
            scope=f"moderation.appeal:{flag_id}",
            key=key,
            payload=payload.model_dump(),
            operation=lambda: store.appeal_flag(
                flag_id, current_user["id"], payload.reason
            ),
        )

    @router.get("/notifications")
    async def notifications(
        cursor: Optional[str] = None,
        limit: int = Query(default=30, ge=1, le=100),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        return await store.notifications(current_user["id"], cursor, limit)

    @router.post("/notifications/{notification_id}/read", status_code=204)
    async def read_notification(
        notification_id: str,
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        await store.mark_notification_read(current_user["id"], notification_id)
        return Response(status_code=204)

    @router.post("/notifications/push-tokens", status_code=201)
    async def register_push(
        payload: PushTokenCreate,
        idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
        current_user: dict = Depends(get_current_user),
        store: ClubStore = Depends(_store),
    ):
        _idempotency_key(idempotency_key)
        token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
        encrypted = _push_cipher().encrypt(payload.token.encode()).decode()
        return await store.register_push_token(
            current_user["id"], token_hash, encrypted, payload.platform
        )

    return router

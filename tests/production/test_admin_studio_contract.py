from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from backend.app.admin.knowledge_router import _audit, _knowledge_access_policy
from backend.app.core.problems import ProblemError
from backend.app.main import app
from backend.app.core.ids import uuid7


class RecordingSession:
    def __init__(self) -> None:
        self.row = None

    def add(self, row) -> None:
        self.row = row


def test_admin_audit_snapshots_are_json_safe() -> None:
    session = RecordingSession()
    entity_id = uuid7()
    asyncio.run(
        _audit(
            session,  # type: ignore[arg-type]
            uuid7(),
            "knowledge.test",
            "method",
            entity_id,
            before={"id": entity_id, "confidence": Decimal("0.750")},
            after={"at": datetime(2026, 8, 11, tzinfo=timezone.utc)},
        )
    )
    assert session.row.before == {"id": str(entity_id), "confidence": 0.75}
    assert session.row.after == {"at": "2026-08-11T00:00:00+00:00"}


def test_admin_studio_authoring_contract_is_exposed() -> None:
    paths = app.openapi()["paths"]
    required = {
        "/api/v1/admin/knowledge/evidence/claims/{claim_id}": {"get"},
        "/api/v1/admin/knowledge/evidence/claims/{claim_id}/versions": {"post"},
        "/api/v1/admin/knowledge/terms/{term_id}": {"put"},
        "/api/v1/admin/knowledge/qualities/{quality_id}": {"put"},
        "/api/v1/admin/knowledge/sports/{taxon_id}": {"put"},
        "/api/v1/admin/knowledge/demands/{demand_id}/versions/{fact_version}": {"put"},
        "/api/v1/admin/knowledge/quality-priorities/{priority_id}": {"put"},
        "/api/v1/admin/knowledge/rules/{rule_id}/versions/{rule_version}": {"put"},
        "/api/v1/admin/knowledge/session-recipes/{recipe_id}": {"get"},
        "/api/v1/admin/knowledge/session-recipes/{recipe_id}/versions/{recipe_version}": {"put"},
        "/api/v1/admin/knowledge/session-recipes/{recipe_id}/versions": {"get", "post"},
        "/api/v1/admin/knowledge/session-recipes/{recipe_id}/retire": {"put"},
        "/api/v1/admin/knowledge/program-archetypes/{archetype_id}": {"get"},
        "/api/v1/admin/knowledge/weeks/{week_id}": {"put"},
        "/api/v1/admin/knowledge/methods/{method_id}/versions/{content_version}/media": {"get", "post"},
        "/api/v1/admin/knowledge/methods/{method_id}/versions": {"get", "post"},
        "/api/v1/admin/knowledge/methods/{method_id}/aliases": {"put"},
        "/api/v1/admin/knowledge/methods/{method_id}/archive": {"put"},
        "/api/v1/admin/users/{user_id}": {"get"},
        "/api/v1/admin/users/{user_id}/status": {"put"},
        "/api/v1/admin/users/{user_id}/revoke-sessions": {"post"},
        "/api/v1/admin/knowledge/reviews": {"get", "post"},
        "/api/v1/admin/knowledge/reports/sport-coverage": {"get"},
        "/api/v1/admin/knowledge/releases/{release_id}/diff": {"get"},
        "/api/v1/admin/operations/feature-flags": {"get"},
        "/api/v1/admin/operations/audit": {"get"},
    }
    for path, methods in required.items():
        assert path in paths
        assert methods.issubset(paths[path])


def _request(method: str, path: str):
    from starlette.requests import Request

    return Request({"type": "http", "method": method, "path": path, "headers": [], "query_string": b"", "server": ("test", 80), "scheme": "http"})


def test_editor_and_publisher_duties_are_separated() -> None:
    asyncio.run(_knowledge_access_policy(_request("POST", "/api/v1/admin/knowledge/methods"), {"roles": ["content_editor"]}))
    asyncio.run(_knowledge_access_policy(_request("POST", "/api/v1/admin/knowledge/releases/x/publish"), {"roles": ["content_publisher"]}))
    asyncio.run(_knowledge_access_policy(_request("GET", "/api/v1/admin/knowledge/methods"), {"roles": ["content_publisher"]}))
    try:
        asyncio.run(_knowledge_access_policy(_request("POST", "/api/v1/admin/knowledge/methods"), {"roles": ["content_publisher"]}))
    except ProblemError as exc:
        assert exc.status == 403
    else:
        raise AssertionError("content publishers must not author drafts")

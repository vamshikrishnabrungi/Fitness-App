import base64
from uuid import uuid4

from starlette.requests import Request

from backend.app.core.security import create_access_token
from backend.app.operations.idempotency import _actor_id, _replay
from backend.app.operations.models import IdempotencyRecord


def test_authenticated_actor_is_derived_from_verified_access_token():
    user_id, session_id = uuid4(), uuid4()
    token = create_access_token(user_id, session_id, ["athlete"])
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/test",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
        }
    )
    assert _actor_id(request) == user_id


def test_completed_record_replays_exact_body_and_marks_response():
    record = IdempotencyRecord(
        actor_id=uuid4(),
        operation="POST:/api/v1/test",
        key="retry-key",
        request_hash="a" * 64,
        status_code=201,
        response_body={
            "body_base64": base64.b64encode(b'{"id":"stable"}').decode(),
            "headers": {"content-type": "application/json"},
        },
    )
    response = _replay(record)
    assert response.status_code == 201
    assert response.body == b'{"id":"stable"}'
    assert response.headers["idempotency-replayed"] == "true"

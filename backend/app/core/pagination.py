from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from .problems import ProblemError

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


class CursorParams(BaseModel):
    cursor: str | None = None
    limit: int = Field(default=25, ge=1, le=100)


def encode_cursor(created_at: datetime, entity_id: UUID) -> str:
    payload = json.dumps([created_at.isoformat(), str(entity_id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(value: str) -> tuple[datetime, UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        created_at, entity_id = json.loads(base64.urlsafe_b64decode(padded).decode())
        return datetime.fromisoformat(created_at), UUID(entity_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ProblemError(400, "invalid_cursor", "Invalid cursor", "The pagination cursor is invalid.") from exc


def encode_numeric_cursor(value: float, entity_id: UUID) -> str:
    payload = json.dumps([value, str(entity_id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_numeric_cursor(value: str) -> tuple[float, UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        number, entity_id = json.loads(base64.urlsafe_b64decode(padded).decode())
        return float(number), UUID(entity_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ProblemError(400, "invalid_cursor", "Invalid cursor", "The pagination cursor is invalid.") from exc

from __future__ import annotations

import base64
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from geoalchemy2.elements import WKBElement
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import Base
import backend.app.models  # noqa: F401


OWNER_COLUMNS = ("user_id", "recipient_user_id", "owner_user_id")
ATHLETE_COLUMNS = ("athlete_id", "owner_athlete_id")
EXCLUDED_TABLES = {
    "identity.otp_challenges",
    "operations.audit_events",
    "operations.consumer_receipts",
    "operations.idempotency_records",
    "operations.outbox_events",
    "operations.feature_flags",
    "competition.territory_control_history",
}
SECRET_PARTS = ("token_hash", "code_hash", "wrapped_dek", "ciphertext", "encrypted_token")


def _value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return base64.b64encode(value).decode()
    if isinstance(value, WKBElement):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_value(item) for item in value]
    return value


def _safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _value(value)
        for key, value in row.items()
        if not any(part in key for part in SECRET_PARTS)
    }


async def build_user_export(session: AsyncSession, user_id: UUID) -> dict[str, Any]:
    athlete_id = await session.scalar(
        select(Base.metadata.tables["athlete.profiles"].c.id).where(
            Base.metadata.tables["athlete.profiles"].c.user_id == user_id
        )
    )
    rows_by_table: dict[str, dict[UUID, dict[str, Any]]] = {}

    for table_name, table in Base.metadata.tables.items():
        if table_name in EXCLUDED_TABLES or "id" not in table.c:
            continue
        conditions = []
        if table_name == "identity.users":
            conditions.append(table.c.id == user_id)
        for column_name in OWNER_COLUMNS:
            if column_name in table.c:
                conditions.append(table.c[column_name] == user_id)
        if athlete_id is not None:
            for column_name in ATHLETE_COLUMNS:
                if column_name in table.c:
                    conditions.append(table.c[column_name] == athlete_id)
        if not conditions:
            continue
        records = (await session.execute(select(table).where(or_(*conditions)))).mappings().all()
        if records:
            rows_by_table[table_name] = {record["id"]: dict(record) for record in records}

    # Traverse only from already-owned entities. Direct links back to identity or
    # athlete profiles are excluded above to avoid exporting records merely acted
    # upon by this athlete (for example, another member's approval record).
    changed = True
    while changed:
        changed = False
        selected_ids = {
            name: set(records)
            for name, records in rows_by_table.items()
            if records
        }
        for table_name, table in Base.metadata.tables.items():
            if table_name in EXCLUDED_TABLES or "id" not in table.c:
                continue
            conditions = []
            for foreign_key in table.foreign_keys:
                target = foreign_key.column.table.fullname
                if target in {"identity.users", "athlete.profiles"}:
                    continue
                target_ids = selected_ids.get(target)
                if target_ids:
                    conditions.append(foreign_key.parent.in_(target_ids))
            if not conditions:
                continue
            records = (await session.execute(select(table).where(or_(*conditions)))).mappings().all()
            destination = rows_by_table.setdefault(table_name, {})
            for record in records:
                if record["id"] not in destination:
                    destination[record["id"]] = dict(record)
                    changed = True

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user_id),
        "data": {
            table_name: [_safe_row(row) for _, row in sorted(records.items(), key=lambda item: str(item[0]))]
            for table_name, records in sorted(rows_by_table.items())
            if records
        },
    }

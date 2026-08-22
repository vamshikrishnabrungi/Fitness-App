import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.service import athlete_id
from backend.app.core.database import get_session
from backend.app.core.encryption import Envelope, decrypt_json, encrypt_json
from backend.app.core.security import current_user_id
from backend.app.operations.outbox import enqueue_event
from .models import DailyCheckIn, HealthMetricRecord, PainReport
from .schemas import CheckInCommand, PainCommand, conservative_action

router = APIRouter(prefix="/health", tags=["health"])


@router.put("/check-ins/daily", status_code=200)
async def check_in(body: CheckInCommand, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id)
    row = await session.scalar(select(DailyCheckIn).where(DailyCheckIn.athlete_id == athlete, DailyCheckIn.local_date == body.local_date).with_for_update())
    if row is None: row = DailyCheckIn(athlete_id=athlete, local_date=body.local_date); session.add(row)
    for key, value in body.model_dump(exclude_none=True).items(): setattr(row, key, value)
    await session.commit(); return {"id": row.id, "local_date": row.local_date, "readiness": row.readiness}


@router.post("/pain-reports", status_code=201)
async def pain(body: PainCommand, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); action = conservative_action(body)
    envelope = await encrypt_json({"description": body.description}, aad=f"pain:{athlete}".encode())
    row = PainReport(athlete_id=athlete, reported_at=datetime.now(timezone.utc), region_code=body.region_code, severity=body.severity, during_activity=body.during_activity, payload_ciphertext=envelope.ciphertext, wrapped_dek=envelope.wrapped_dek, kms_key_version=envelope.key_version, action=action)
    session.add(row); await session.flush(); await enqueue_event(session, topic="health", event_type="health.pain_reported", aggregate_type="pain_report", aggregate_id=row.id, payload={"pain_report_id": str(row.id), "action": action}); await session.commit()
    return {"id": row.id, "action": action, "message": "Stop if symptoms worsen and seek qualified professional assessment when indicated."}


@router.get("/summary")
async def summary(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); latest = await session.scalar(select(DailyCheckIn).where(DailyCheckIn.athlete_id == athlete).order_by(DailyCheckIn.local_date.desc()))
    open_pain = (await session.scalars(select(PainReport).where(PainReport.athlete_id == athlete, PainReport.status == "open"))).all()
    metric_rows = (
        await session.scalars(
            select(HealthMetricRecord)
            .where(
                HealthMetricRecord.athlete_id == athlete,
                HealthMetricRecord.metric_code.in_(("sleep_duration_min", "resting_hr_bpm", "hrv_rmssd_ms")),
            )
            .distinct(HealthMetricRecord.metric_code)
            .order_by(HealthMetricRecord.metric_code, HealthMetricRecord.ended_at.desc())
        )
    ).all()

    async def reveal(row: HealthMetricRecord) -> tuple[str, dict]:
        payload = await decrypt_json(
            Envelope(row.payload_ciphertext, row.wrapped_dek, row.kms_key_version),
            aad=f"health-metric:{athlete}:{row.provider}:{row.provider_record_hash}".encode(),
        )
        return row.metric_code, {"value": payload.get("value"), "unit": payload.get("unit"), "measured_at": row.ended_at, "provider": row.provider}

    connected_metrics = dict(await asyncio.gather(*(reveal(row) for row in metric_rows))) if metric_rows else {}
    sleep_minutes = latest.sleep_minutes if latest else None
    if sleep_minutes is None and "sleep_duration_min" in connected_metrics:
        sleep_minutes = int(float(connected_metrics["sleep_duration_min"]["value"]))
    return {"readiness": latest.readiness if latest else None, "sleep_minutes": sleep_minutes, "stress": latest.stress if latest else None, "open_pain_reports": len(open_pain), "connected_metrics": connected_metrics}


@router.get("/pain-reports")
async def pain_reports(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> list[dict]:
    athlete = await athlete_id(session, user_id); rows = (await session.scalars(select(PainReport).where(PainReport.athlete_id == athlete).order_by(PainReport.reported_at.desc()).limit(100))).all()
    return [{"id": row.id, "region_code": row.region_code, "severity": row.severity, "reported_at": row.reported_at, "status": row.status, "action": row.action, "version": row.version} for row in rows]


@router.put("/pain-reports/{report_id}/resolve", status_code=204)
async def resolve_pain(report_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    athlete = await athlete_id(session, user_id); row = await session.scalar(select(PainReport).where(PainReport.id == report_id, PainReport.athlete_id == athlete).with_for_update())
    if row: row.status = "resolved"; row.version += 1; await session.commit()

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.encryption import Envelope, decrypt_json
from backend.app.core.http_client import http_client

from .models import Notification, NotificationDelivery, PushToken


EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
EXPO_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"
TERMINAL_TOKEN_ERRORS = {"DeviceNotRegistered"}


async def deliver_notification(session: AsyncSession, notification_id: UUID) -> None:
    """Deliver one durable in-app notification to every active device token.

    Each notification/token pair is its own idempotent delivery. Successful
    tickets are never sent again when Pub/Sub retries the source event.
    """

    notification = await session.get(Notification, notification_id)
    if notification is None:
        return
    tokens = (
        await session.scalars(
            select(PushToken).where(
                PushToken.user_id == notification.recipient_user_id,
                PushToken.active.is_(True),
            )
        )
    ).all()
    transient_errors: list[str] = []
    settings = get_settings()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.expo_access_token:
        headers["Authorization"] = f"Bearer {settings.expo_access_token}"

    existing_deliveries = (
        await session.scalars(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.notification_id == notification.id,
                NotificationDelivery.push_token_id.in_([token.id for token in tokens]),
            )
            .with_for_update()
        )
    ).all() if tokens else []
    delivery_by_token = {delivery.push_token_id: delivery for delivery in existing_deliveries}
    client = http_client()
    for token in tokens:
        delivery = delivery_by_token.get(token.id)
        if delivery and delivery.status in {"accepted", "invalid_token"}:
            continue
        if delivery is None:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                push_token_id=token.id,
                provider="expo",
                status="processing",
                attempts=1,
            )
            session.add(delivery)
        else:
            delivery.status = "processing"
            delivery.attempts += 1
            delivery.last_error = None
        try:
            decrypted = await decrypt_json(
                Envelope(token.encrypted_token, token.wrapped_dek, token.kms_key_version),
                aad=f"push:{token.user_id}".encode(),
            )
            push_token = str(decrypted["token"])
            response = await client.post(
                EXPO_PUSH_URL,
                headers=headers,
                json={
                    "to": push_token,
                    "title": notification.title,
                    "body": notification.body,
                    "data": notification.payload_json,
                    "sound": "default",
                    "channelId": "club-competition",
                },
                timeout=15.0,
            )
            response.raise_for_status()
            ticket = response.json().get("data") or {}
            if isinstance(ticket, list):
                ticket = ticket[0] if ticket else {}
            if ticket.get("status") == "ok":
                delivery.status = "accepted"
                delivery.provider_message_id = ticket.get("id")
                delivery.accepted_at = datetime.now(timezone.utc)
            else:
                error_code = str((ticket.get("details") or {}).get("error") or "push_rejected")
                delivery.last_error = error_code[:500]
                if error_code in TERMINAL_TOKEN_ERRORS:
                    delivery.status = "invalid_token"
                    token.active = False
                else:
                    delivery.status = "retry"
                    transient_errors.append(error_code)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            delivery.status = "retry"
            delivery.last_error = type(exc).__name__[:500]
            transient_errors.append(type(exc).__name__)
    await session.commit()
    if transient_errors:
        raise RuntimeError(f"push delivery retry required: {','.join(sorted(set(transient_errors)))}")


async def check_delivery_receipts(session: AsyncSession) -> int:
    deliveries = (
        await session.scalars(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.status == "accepted",
                NotificationDelivery.provider_message_id.is_not(None),
            )
            .limit(500)
            .with_for_update(skip_locked=True)
        )
    ).all()
    if not deliveries:
        return 0
    settings = get_settings()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.expo_access_token:
        headers["Authorization"] = f"Bearer {settings.expo_access_token}"
    response = await http_client().post(
        EXPO_RECEIPTS_URL,
        headers=headers,
        json={"ids": [row.provider_message_id for row in deliveries]},
        timeout=15.0,
    )
    response.raise_for_status()
    receipts = response.json().get("data") or {}
    now = datetime.now(timezone.utc)
    checked = 0
    for delivery in deliveries:
        receipt = receipts.get(delivery.provider_message_id)
        if not receipt:
            continue
        checked += 1
        delivery.receipt_checked_at = now
        if receipt.get("status") == "ok":
            delivery.status = "delivered"
            delivery.delivered_at = now
            delivery.last_error = None
            continue
        error_code = str((receipt.get("details") or {}).get("error") or "delivery_failed")
        delivery.status = "failed"
        delivery.last_error = error_code[:500]
        if error_code == "DeviceNotRegistered":
            token = await session.get(PushToken, delivery.push_token_id, with_for_update=True)
            if token:
                token.active = False
    await session.commit()
    return checked

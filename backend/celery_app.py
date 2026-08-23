from __future__ import annotations

import asyncio
import os

from celery import Celery
from motor.motor_asyncio import AsyncIOMotorClient

from backend.activity_pipeline import process_pending_outbox
from backend.account_lifecycle import process_due_account_deletions
from backend.competition_workers import (
    ensure_quarterly_seasons,
    process_competition_outbox,
    rebuild_challenge_scores,
    schedule_competition_events,
    send_pending_push_notifications,
    snapshot_daily_leaderboards,
)
from backend.territory_engine import expire_territory_scores


REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'sftc_database')
OUTBOX_BATCH_SIZE = max(1, int(os.environ.get('ACTIVITY_OUTBOX_BATCH_SIZE', '25') or 25))

celery_app = Celery(
    'runlete',
    broker=REDIS_URL,
    backend=REDIS_URL,
)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_transport_options={'visibility_timeout': 3600},
    beat_schedule={
        'process-activity-outbox': {
            'task': 'runlete.process_activity_outbox',
            'schedule': 10.0,
        },
        'process-account-deletions': {
            'task': 'runlete.process_account_deletions',
            'schedule': 300.0,
        },
        'process-competition-outbox': {
            'task': 'runlete.process_competition_outbox',
            'schedule': 10.0,
        },
        'send-competition-push-notifications': {
            'task': 'runlete.send_competition_push_notifications',
            'schedule': 10.0,
        },
        'rebuild-challenge-scores': {
            'task': 'runlete.rebuild_challenge_scores',
            'schedule': 60.0,
        },
        'expire-territory-control': {
            'task': 'runlete.expire_territory_control',
            'schedule': 3600.0,
        },
        'ensure-quarterly-seasons': {
            'task': 'runlete.ensure_quarterly_seasons',
            'schedule': 86400.0,
        },
        'schedule-competition-events': {
            'task': 'runlete.schedule_competition_events',
            'schedule': 300.0,
        },
        'snapshot-daily-leaderboards': {
            'task': 'runlete.snapshot_daily_leaderboards',
            'schedule': 86400.0,
        },
    },
)


async def _run_activity_outbox() -> dict:
    client = AsyncIOMotorClient(MONGO_URL)
    try:
        return await process_pending_outbox(
            client[DB_NAME],
            limit=OUTBOX_BATCH_SIZE,
        )
    finally:
        client.close()


@celery_app.task(name='runlete.process_activity_outbox')
def process_activity_outbox() -> dict:
    return asyncio.run(_run_activity_outbox())


async def _run_account_deletions() -> dict:
    client = AsyncIOMotorClient(MONGO_URL)
    try:
        return await process_due_account_deletions(client[DB_NAME])
    finally:
        client.close()


@celery_app.task(name='runlete.process_account_deletions')
def process_account_deletions() -> dict:
    return asyncio.run(_run_account_deletions())


@celery_app.task(name='runlete.process_competition_outbox')
def process_relational_competition_outbox() -> dict:
    return asyncio.run(process_competition_outbox())


@celery_app.task(name='runlete.rebuild_challenge_scores')
def rebuild_active_challenge_scores() -> dict:
    return asyncio.run(rebuild_challenge_scores())


@celery_app.task(name='runlete.expire_territory_control')
def expire_territory_control() -> dict:
    return asyncio.run(expire_territory_scores())


@celery_app.task(name='runlete.send_competition_push_notifications')
def send_competition_push_notifications() -> dict:
    return asyncio.run(send_pending_push_notifications())


@celery_app.task(name='runlete.ensure_quarterly_seasons')
def ensure_competition_seasons() -> dict:
    return asyncio.run(ensure_quarterly_seasons())


@celery_app.task(name='runlete.schedule_competition_events')
def schedule_race_and_challenge_events() -> dict:
    return asyncio.run(schedule_competition_events())


@celery_app.task(name='runlete.snapshot_daily_leaderboards')
def snapshot_competition_leaderboards() -> dict:
    return asyncio.run(snapshot_daily_leaderboards())

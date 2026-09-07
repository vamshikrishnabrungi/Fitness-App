"""Pull development Pub/Sub messages into the loopback-only worker HTTP server.

Run from the repository root: .venv/bin/python -m backend.tools.local_worker
Start backend.app.worker_main on 127.0.0.1:8003 first.
"""
from __future__ import annotations

import base64
import logging
import signal
import threading
from functools import partial

import requests
from google.cloud import pubsub_v1

from backend.app.core.config import get_settings

TOPICS = ('activity', 'territory', 'training', 'nutrition', 'health', 'club', 'competition', 'notifications', 'maintenance')
WORKER_URL = 'http://127.0.0.1:8003'
logger = logging.getLogger('runlete.local_worker')


def deliver(topic, message):
    try:
        response = requests.post(
            f'{WORKER_URL}/internal/pubsub/{topic}',
            json={'message': {'data': base64.b64encode(message.data).decode(), 'messageId': message.message_id}},
            timeout=(5, 900),
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning('Delivery failed topic=%s message=%s error=%s; retry scheduled', topic, message.message_id, type(exc).__name__)
        message.nack()
    else:
        message.ack()
        logger.info('Processed topic=%s message=%s', topic, message.message_id)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    settings = get_settings()
    if settings.environment != 'development':
        raise SystemExit('This runner is only for ENVIRONMENT=development')
    requests.get(f'{WORKER_URL}/readyz', timeout=60).raise_for_status()
    stopped = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopped.set())
    futures = []
    with pubsub_v1.SubscriberClient() as subscriber:
        try:
            for topic in TOPICS:
                path = subscriber.subscription_path(settings.gcp_project_id, f'runlete-development-{topic}-local')
                futures.append(subscriber.subscribe(path, callback=partial(deliver, topic), flow_control=pubsub_v1.types.FlowControl(max_messages=1)))
                logger.info('Listening: %s', path)
            while not stopped.is_set():
                for future in futures:
                    if future.done():
                        future.result()
                        raise RuntimeError('Subscription unexpectedly stopped')
                try:
                    # Publish newly queued and previously failed outbox events.
                    requests.post(f'{WORKER_URL}/internal/maintenance/outbox', timeout=60).raise_for_status()
                except requests.RequestException as exc:
                    logger.warning('Outbox recovery failed: %s', type(exc).__name__)
                stopped.wait(60)
        finally:
            for future in futures:
                future.cancel()
            for future in futures:
                future.result(timeout=30)


if __name__ == '__main__':
    main()

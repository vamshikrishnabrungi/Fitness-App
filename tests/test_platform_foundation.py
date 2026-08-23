from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.activity_pipeline import outbox_retry_delay
from backend.migrate_legacy_runs import build_canonical_legacy_activity
from backend.platform_models import HealthActivityBatch, LiveLocationUpdate


def test_outbox_retry_delay_is_bounded_exponential():
    assert outbox_retry_delay(1) == 15
    assert outbox_retry_delay(2) == 30
    assert outbox_retry_delay(20) == 3600


def test_health_batch_rejects_duplicate_provider_ids():
    item = {
        'external_id': 'watch-activity-1',
        'activity': {
            'source': 'apple_health',
            'activity_type': 'treadmill',
            'distance_m': 5000,
            'moving_time_sec': 1800,
        },
    }
    with pytest.raises(ValidationError):
        HealthActivityBatch(
            provider='apple_health',
            activities=[item, item],
        )


def test_live_location_validation_rejects_invalid_coordinates():
    with pytest.raises(ValidationError):
        LiveLocationUpdate(
            latitude=100,
            longitude=78,
            timestamp=datetime.now(timezone.utc),
        )


def test_legacy_migration_recomputes_from_gps_and_is_deterministic():
    legacy = {
        'id': 'legacy-run-1',
        'user_id': 'user-1',
        'distance': 999,
        'gps_path': [
            {'latitude': 17.4, 'longitude': 78.4, 'timestamp': '2026-01-01T06:00:00Z'},
            {'latitude': 17.401, 'longitude': 78.4, 'timestamp': '2026-01-01T06:01:00Z'},
        ],
    }
    user = {'id': 'user-1', 'profile': {'weight_kg': 65}}
    first = build_canonical_legacy_activity('terra_runs', legacy, user)
    second = build_canonical_legacy_activity('terra_runs', legacy, user)
    assert first is not None
    assert first['id'] == second['id']
    assert first['distance_km'] < 1
    assert first['distance_km'] != legacy['distance']
    assert first['schema_version'] == 1

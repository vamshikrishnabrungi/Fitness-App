from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.app.activities.schemas import HealthBatchCommand


NOW = datetime(2026, 8, 9, 7, 0, tzinfo=timezone.utc)


def test_health_batch_accepts_closed_metric_and_provider_taxonomy() -> None:
    batch = HealthBatchCommand(
        provider="health_connect",
        records=[
            {
                "provider_record_id": "sleep-123",
                "metric_code": "sleep_duration_min",
                "started_at": NOW - timedelta(hours=8),
                "ended_at": NOW,
                "value": 462,
                "unit": "min",
                "source_name": "Pixel Watch",
            }
        ],
    )
    assert batch.records[0].value == 462


@pytest.mark.parametrize(
    "change",
    [
        {"provider": "unknown_vendor"},
        {"metric_code": "diagnosis"},
        {"value": -1},
    ],
)
def test_health_batch_rejects_unknown_or_unsafe_values(change: dict) -> None:
    change = dict(change)
    record = {
        "provider_record_id": "record-1",
        "metric_code": "resting_hr_bpm",
        "started_at": NOW,
        "ended_at": NOW,
        "value": 58,
        "unit": "bpm",
    }
    provider = change.pop("provider", "apple_health")
    record.update(change)
    with pytest.raises(ValidationError):
        HealthBatchCommand(provider=provider, records=[record])


def test_health_batch_is_bounded() -> None:
    record = {
        "provider_record_id": "record-1",
        "metric_code": "steps",
        "started_at": NOW,
        "ended_at": NOW,
        "value": 1,
        "unit": "count",
    }
    with pytest.raises(ValidationError):
        HealthBatchCommand(provider="apple_health", records=[record] * 501)

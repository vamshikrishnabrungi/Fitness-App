import pytest

from backend.app.operations.outbox import ALLOWED_TOPICS


def test_infrastructure_topic_contract_is_closed_and_complete():
    assert ALLOWED_TOPICS == {
        "activity",
        "territory",
        "training",
        "nutrition",
        "health",
        "club",
        "competition",
        "notifications",
        "maintenance",
    }


def test_unknown_topic_is_not_silently_persisted():
    # Topic validation occurs before the session is used, so a tiny sentinel is sufficient.
    from backend.app.operations.outbox import enqueue_event
    from uuid import uuid4

    class SessionSentinel:
        def add(self, value):
            raise AssertionError("invalid topics must fail before persistence")

    with pytest.raises(ValueError, match="Unsupported outbox topic"):
        import asyncio

        asyncio.run(
            enqueue_event(
                SessionSentinel(),
                topic="unknown",
                event_type="unknown.event",
                aggregate_type="test",
                aggregate_id=uuid4(),
                payload={},
            )
        )

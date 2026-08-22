from backend.app.core.ids import uuid7


def test_uuid7_is_canonical_and_time_ordered():
    values = [uuid7() for _ in range(100)]
    assert all(value.version == 7 for value in values)
    assert len(set(values)) == len(values)
    assert values == sorted(values)


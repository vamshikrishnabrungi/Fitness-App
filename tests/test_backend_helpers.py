from __future__ import annotations

from backend.helpers import (
    _parse_iso_datetime,
    _to_non_negative_float,
    _to_non_negative_int,
    clean_doc,
)


def test_clean_doc_removes_mongo_id():
    doc = {'_id': 'mongo-id', 'id': 'user-1', 'name': 'Athlete'}
    assert clean_doc(doc) == {'id': 'user-1', 'name': 'Athlete'}


def test_numeric_helpers_normalize_values():
    assert _to_non_negative_int('12.2') == 12
    assert _to_non_negative_int(-4) == 0
    assert _to_non_negative_float('3.67') == 3.7
    assert _to_non_negative_float(-2.2) == 0.0


def test_parse_iso_datetime_accepts_z_suffix():
    dt = _parse_iso_datetime('2026-03-30T10:00:00Z')
    assert dt is not None
    assert dt.tzinfo is not None

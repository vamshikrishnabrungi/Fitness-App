from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / 'backend' / 'server.py'

spec = importlib.util.spec_from_file_location('backend_server', SERVER_PATH)
assert spec and spec.loader
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def test_clean_doc_removes_mongo_id():
    doc = {'_id': 'mongo-id', 'id': 'user-1', 'name': 'Athlete'}
    assert server.clean_doc(doc) == {'id': 'user-1', 'name': 'Athlete'}


def test_numeric_helpers_normalize_values():
    assert server._to_non_negative_int('12.2') == 12
    assert server._to_non_negative_int(-4) == 0
    assert server._to_non_negative_float('3.67') == 3.7
    assert server._to_non_negative_float(-2.2) == 0.0


def test_parse_iso_datetime_accepts_z_suffix():
    dt = server._parse_iso_datetime('2026-03-30T10:00:00Z')
    assert dt is not None
    assert dt.tzinfo is not None

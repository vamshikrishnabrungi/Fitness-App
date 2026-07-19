"""Runnable check for the per-user AI-generation cost guard (_enforce_ai_generation_quota)."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('backend_server_quota', ROOT / 'backend' / 'server.py')
assert spec and spec.loader
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class _FakeLog:
    def __init__(self):
        self.docs = []

    async def count_documents(self, query):
        uid = query.get('user_id')
        since = (query.get('created_at') or {}).get('$gte')
        return sum(1 for d in self.docs if d['user_id'] == uid and (since is None or d['created_at'] >= since))

    async def insert_one(self, doc):
        self.docs.append(doc)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_quota_blocks_after_limit_and_is_per_user():
    old_db, old_quota = server.db, server.WORKOUT_AI_DAILY_QUOTA
    try:
        server.WORKOUT_AI_DAILY_QUOTA = 2
        server.db = SimpleNamespace(ai_generation_log=_FakeLog())

        _run(server._enforce_ai_generation_quota('u1'))   # 1st — ok
        _run(server._enforce_ai_generation_quota('u1'))   # 2nd — ok
        with pytest.raises(server.HTTPException) as exc:
            _run(server._enforce_ai_generation_quota('u1'))  # 3rd — blocked
        assert exc.value.status_code == 429

        _run(server._enforce_ai_generation_quota('u2'))   # other user unaffected
    finally:
        server.db, server.WORKOUT_AI_DAILY_QUOTA = old_db, old_quota


def test_day_streak():
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    d = lambda n: (today - timedelta(days=n)).strftime('%Y-%m-%d')
    assert server._current_day_streak(set()) == 0
    assert server._current_day_streak({d(0)}) == 1
    assert server._current_day_streak({d(0), d(1), d(2)}) == 3       # today + 2 back
    assert server._current_day_streak({d(1), d(2)}) == 2             # ends yesterday → still counts
    assert server._current_day_streak({d(3)}) == 0                   # older than yesterday → broken
    assert server._current_day_streak({d(0), d(2), d(3)}) == 1       # gap after today breaks it


def test_program_base_date():
    from datetime import datetime, timedelta
    now = datetime(2026, 7, 13, 10, 0, 0)  # a Monday
    # future start date is honored
    assert server._program_base_date('2026-07-20', now).date() == datetime(2026, 7, 20).date()
    # today is honored
    assert server._program_base_date('2026-07-13', now).date() == now.date()
    # past date falls back to today
    assert server._program_base_date('2026-07-01', now) == now
    # empty / garbage falls back to today
    assert server._program_base_date(None, now) == now
    assert server._program_base_date('not-a-date', now) == now


def test_quota_disabled_when_zero():
    old_db, old_quota = server.db, server.WORKOUT_AI_DAILY_QUOTA
    try:
        server.WORKOUT_AI_DAILY_QUOTA = 0
        server.db = SimpleNamespace(ai_generation_log=_FakeLog())
        for _ in range(50):
            _run(server._enforce_ai_generation_quota('u1'))  # never blocks
    finally:
        server.db, server.WORKOUT_AI_DAILY_QUOTA = old_db, old_quota

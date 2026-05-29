from __future__ import annotations

import copy
import importlib.util
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / 'backend' / 'server.py'

spec = importlib.util.spec_from_file_location('backend_server', SERVER_PATH)
assert spec and spec.loader
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def route_exists(method: str, path: str) -> bool:
    expected_path = f'/api{path}'
    method = method.upper()
    for route in server.app.routes:
        if getattr(route, 'path', None) == expected_path and method in getattr(route, 'methods', set()):
            return True
    return False


def require_routes(*routes: tuple[str, str]) -> None:
    missing = [f'{method} {path}' for method, path in routes if not route_exists(method, path)]
    if missing:
        pytest.skip('Sleep backend slice not implemented yet: ' + ', '.join(missing))


class InMemoryCursor:
    def __init__(self, docs: list[dict]):
        self.docs = docs

    def sort(self, key, direction=1):
        if isinstance(key, list):
            keys = key
        else:
            keys = [(key, direction)]

        docs = self.docs
        for field, dir_value in reversed(keys):
            docs = sorted(docs, key=lambda doc: doc.get(field), reverse=dir_value < 0)
        self.docs = docs
        return self

    async def to_list(self, length: int):
        return [copy.deepcopy(doc) for doc in self.docs[:length]]


class InMemoryCollection:
    def __init__(self, docs: list[dict] | None = None):
        self.docs = [copy.deepcopy(doc) for doc in (docs or [])]

    def _matches(self, doc: dict, query: dict | None) -> bool:
        if not query:
            return True

        for key, value in query.items():
            if key == '$or':
                if not any(self._matches(doc, clause) for clause in value):
                    return False
                continue

            current = doc.get(key)
            if isinstance(value, dict):
                if '$in' in value and current not in value['$in']:
                    return False
                if '$ne' in value and current == value['$ne']:
                    return False
                if '$gte' in value and current < value['$gte']:
                    return False
                if '$lte' in value and current > value['$lte']:
                    return False
                if '$regex' in value:
                    flags = re.IGNORECASE if value.get('$options') == 'i' else 0
                    if not re.search(value['$regex'], str(current or ''), flags=flags):
                        return False
            elif current != value:
                return False
        return True

    def _filter(self, query: dict | None = None) -> list[dict]:
        return [doc for doc in self.docs if self._matches(doc, query)]

    async def find_one(self, query: dict | None = None, sort=None):
        docs = self._filter(query)
        if sort:
            docs = InMemoryCursor(docs).sort(sort).docs
        return copy.deepcopy(docs[0]) if docs else None

    def find(self, query: dict | None = None, *args, **kwargs):
        return InMemoryCursor(self._filter(query))

    async def insert_one(self, doc: dict):
        self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_id=doc.get('id'))

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        for doc in self.docs:
            if self._matches(doc, query):
                if '$set' in update:
                    doc.update(copy.deepcopy(update['$set']))
                return SimpleNamespace(modified_count=1, upserted_id=None)

        if upsert:
            new_doc = {
                key: value
                for key, value in query.items()
                if not key.startswith('$') and not isinstance(value, dict)
            }
            if '$set' in update:
                new_doc.update(copy.deepcopy(update['$set']))
            self.docs.append(new_doc)
            return SimpleNamespace(modified_count=0, upserted_id=new_doc.get('id'))

        return SimpleNamespace(modified_count=0, upserted_id=None)


class FakeDB:
    def __init__(self, seed: dict[str, list[dict]] | None = None):
        self._collections: dict[str, InMemoryCollection] = {
            name: InMemoryCollection(docs) for name, docs in (seed or {}).items()
        }

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        return self._collections.setdefault(name, InMemoryCollection())

    def __getitem__(self, name: str):
        return self.__getattr__(name)


class FakeOpenAIClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, *args, **kwargs):
        message = SimpleNamespace(content='{}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_client(monkeypatch, seed: dict[str, list[dict]] | None = None):
    fake_db = FakeDB(seed)
    monkeypatch.setattr(server, 'db', fake_db)
    monkeypatch.setattr(server, 'openai_client', FakeOpenAIClient())
    server.app.dependency_overrides[server.get_current_user] = lambda: {
        'id': 'user-1',
        'email': 'athlete@example.com',
        'name': 'Athlete',
        'mode': 'user',
        'profile': {},
        'created_at': datetime(2026, 3, 30),
    }
    return TestClient(server.app), fake_db


def test_sleep_notes_sessions_and_stats_contract(monkeypatch):
    require_routes(
        ('POST', '/sleep/notes'),
        ('POST', '/sleep/sessions'),
        ('GET', '/sleep/sessions'),
        ('GET', '/sleep/stats'),
    )

    seed = {
        'quick_logs': [
            {
                'id': 'quick-1',
                'user_id': 'user-1',
                'date': '2026-03-29',
                'mood': 'good',
                'energy': 'high',
                'stress': 'calm',
                'sleep_quality': 4,
                'created_at': datetime(2026, 3, 29, 10, 0),
            },
            {
                'id': 'quick-2',
                'user_id': 'user-1',
                'date': '2026-03-30',
                'mood': 'okay',
                'energy': 'normal',
                'stress': 'moderate',
                'sleep_quality': 3,
                'created_at': datetime(2026, 3, 30, 10, 0),
            },
        ],
    }
    client, _ = make_client(monkeypatch, seed=seed)

    note_response = client.post(
        '/api/sleep/notes',
        json={
            'mood': 'relaxed',
            'activities': ['reading', 'stretching'],
            'note': 'Kept the room cool and went to bed early.',
        },
    )
    assert note_response.status_code == 200
    note = note_response.json()
    assert note['user_id'] == 'user-1'
    assert note['mood'] == 'relaxed'
    assert note['activities'] == ['reading', 'stretching']
    assert note['note'] == 'Kept the room cool and went to bed early.'

    session_one = client.post(
        '/api/sleep/sessions',
        json={
            'start_time': '2026-03-29T22:00:00Z',
            'end_time': '2026-03-30T06:30:00Z',
            'duration_hours': 8.5,
            'deep_sleep_hours': 2.5,
            'rem_sleep_hours': 1.5,
            'sleep_score': 86,
        },
    )
    assert session_one.status_code == 200
    session_one_payload = session_one.json()
    assert session_one_payload['user_id'] == 'user-1'

    session_two = client.post(
        '/api/sleep/sessions',
        json={
            'start_time': '2026-03-30T23:15:00Z',
            'end_time': '2026-03-31T06:15:00Z',
            'duration_hours': 7.0,
            'deep_sleep_hours': 2.0,
            'rem_sleep_hours': 1.0,
            'sleep_score': 72,
        },
    )
    assert session_two.status_code == 200
    session_two_payload = session_two.json()
    assert session_two_payload['user_id'] == 'user-1'

    list_response = client.get('/api/sleep/sessions')
    assert list_response.status_code == 200
    sessions = list_response.json()
    assert len(sessions) == 2
    assert sessions[0]['id'] == session_two_payload['id']
    assert sessions[1]['id'] == session_one_payload['id']

    stats_response = client.get('/api/sleep/stats')
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats['total_sessions'] == 2
    assert stats['avg_score'] == 74.5
    assert stats['avg_duration'] == 7.8
    assert stats['avg_deep_sleep'] == 2.2
    assert stats['avg_rem_sleep'] == 1.2
    assert stats['sleep_debt']['total_debt_hours'] == 1.0


def test_recovery_summary_reflects_sleep_quality_log(monkeypatch):
    require_routes(('GET', '/health/recovery'))

    seed = {
        'quick_logs': [
            {
                'id': 'quick-recovery',
                'user_id': 'user-1',
                'date': '2026-03-30',
                'mood': 'good',
                'energy': 'high',
                'stress': 'calm',
                'sleep_quality': 4,
                'created_at': datetime(2026, 3, 30, 10, 0),
            },
        ],
    }
    client, _ = make_client(monkeypatch, seed=seed)

    response = client.get('/api/health/recovery')
    assert response.status_code == 200
    recovery = response.json()
    assert recovery['score'] == 80
    assert recovery['status'] == 'high'
    assert recovery['sleep'] == {'value': None, 'quality': 'good'}


def test_recovery_summary_handles_missing_sleep_and_quick_logs(monkeypatch):
    require_routes(('GET', '/health/recovery'))

    client, _ = make_client(monkeypatch)

    response = client.get('/api/health/recovery')
    assert response.status_code == 200
    recovery = response.json()
    assert recovery['score'] is None
    assert recovery['status'] == 'moderate'
    assert recovery['sleep'] == {'value': None, 'quality': 'unknown'}

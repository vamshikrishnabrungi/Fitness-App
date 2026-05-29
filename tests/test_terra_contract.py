from __future__ import annotations

import copy
import importlib.util
import re
from datetime import datetime, timedelta
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
        pytest.skip('Terra backend slice not implemented yet: ' + ', '.join(missing))


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


def make_client(monkeypatch, seed: dict[str, list[dict]] | None = None):
    fake_db = FakeDB(seed)
    monkeypatch.setattr(server, 'db', fake_db)
    server.app.dependency_overrides[server.get_current_user] = lambda: {
        'id': 'user-1',
        'email': 'athlete@example.com',
        'name': 'Athlete',
        'mode': 'user',
        'profile': {},
        'created_at': datetime(2026, 3, 30),
    }
    return TestClient(server.app), fake_db


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    server.app.dependency_overrides.clear()


def test_run_stats_contract_aggregates_seeded_runs(monkeypatch):
    require_routes(('GET', '/runs/stats'))

    today = datetime.utcnow().date()
    seed = {
        'runs': [
            {
                'id': 'run-1',
                'user_id': 'user-1',
                'distance_km': 5.0,
                'duration_sec': 1800,
                'date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            },
            {
                'id': 'run-2',
                'user_id': 'user-1',
                'distance_km': 7.0,
                'duration_sec': 2520,
                'date': today.strftime('%Y-%m-%d'),
            },
            {
                'id': 'run-3',
                'user_id': 'other-user',
                'distance_km': 9.0,
                'duration_sec': 2700,
                'date': today.strftime('%Y-%m-%d'),
            },
        ],
    }
    client, _ = make_client(monkeypatch, seed=seed)

    response = client.get('/api/runs/stats')
    assert response.status_code == 200
    payload = response.json()
    assert payload['total_distance'] == 12.0
    assert payload['average_pace'] == "6'00"
    assert payload['fatigue'] == 'Moderate'
    assert payload['consistency'] == 28

    expected_history = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        expected_history.append({
            'day': day.strftime('%a'),
            'value': 7.0 if day == today else 5.0 if day == today - timedelta(days=1) else 0,
        })
    assert payload['history'] == expected_history


def test_terra_run_creation_and_reflection_contract(monkeypatch):
    require_routes(
        ('POST', '/terra/runs'),
        ('POST', '/terra/reflections'),
    )

    client, _ = make_client(monkeypatch)

    save_response = client.post(
        '/api/terra/runs',
        json={
            'gps_path': [
                {'latitude': 37.7749, 'longitude': -122.4194, 'timestamp': '2026-03-30T03:00:00.000Z'},
                {'latitude': 37.7752, 'longitude': -122.4189, 'timestamp': '2026-03-30T03:05:00.000Z'},
            ],
            'start_time': '2026-03-30T03:00:00.000Z',
            'end_time': '2026-03-30T03:05:00.000Z',
        },
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert isinstance(saved['id'], str)
    assert 'distance' in saved
    assert 'duration' in saved
    assert 'territory_captured' in saved
    assert 'xp_earned' in saved
    assert 'is_loop' in saved

    reflection_response = client.post(
        '/api/terra/reflections',
        json={
            'run_id': saved['id'],
            'feeling': 'good',
            'notes': 'Strong tempo effort and controlled finish.',
        },
    )
    assert reflection_response.status_code == 200


def test_terra_feed_and_leaderboard_contract(monkeypatch):
    require_routes(
        ('GET', '/terra/feed'),
        ('POST', '/terra/feed'),
        ('POST', '/terra/feed/{post_id}/like'),
        ('GET', '/terra/leaderboard/global'),
        ('GET', '/terra/leaderboard/friends'),
    )

    client, _ = make_client(monkeypatch)

    feed_response = client.get('/api/terra/feed')
    assert feed_response.status_code == 200
    feed = feed_response.json()
    assert isinstance(feed, list)

    post_response = client.post('/api/terra/feed', json={'content': 'Easy recovery loop today.'})
    assert post_response.status_code == 200
    post = post_response.json()
    assert isinstance(post['id'], str)
    assert post['content'] == 'Easy recovery loop today.'
    assert 'likes' in post
    assert 'comments' in post

    like_response = client.post(f"/api/terra/feed/{post['id']}/like")
    assert like_response.status_code == 200

    global_response = client.get('/api/terra/leaderboard/global')
    friends_response = client.get('/api/terra/leaderboard/friends')
    assert global_response.status_code == 200
    assert friends_response.status_code == 200
    assert isinstance(global_response.json(), list)
    assert isinstance(friends_response.json(), list)


def test_terra_plans_competition_and_vault_contract(monkeypatch):
    require_routes(
        ('GET', '/terra/stats'),
        ('GET', '/terra/training-plans'),
        ('POST', '/terra/training-plans'),
        ('GET', '/terra/competition/current'),
        ('GET', '/terra/vault'),
    )

    client, _ = make_client(monkeypatch)

    stats_response = client.get('/api/terra/stats')
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert 'total_runs' in stats
    assert 'total_distance' in stats
    assert 'total_territory' in stats
    assert 'xp' in stats
    assert 'level' in stats
    assert 'history' in stats

    plans_response = client.get('/api/terra/training-plans')
    assert plans_response.status_code == 200
    plans = plans_response.json()
    assert isinstance(plans, list)

    create_response = client.post(
        '/api/terra/training-plans',
        json={'goal': '5K', 'fitness_level': 'intermediate'},
    )
    assert create_response.status_code == 200
    created_plan = create_response.json()
    assert created_plan['goal'] == '5K'
    assert created_plan['fitness_level'] == 'intermediate'
    assert 'current_week' in created_plan
    assert 'total_weeks' in created_plan

    competition_response = client.get('/api/terra/competition/current')
    assert competition_response.status_code == 200
    competition = competition_response.json()
    assert 'name' in competition
    assert 'prize' in competition
    assert 'description' in competition
    assert 'days_remaining' in competition

    vault_response = client.get('/api/terra/vault')
    assert vault_response.status_code == 200
    vault = vault_response.json()
    assert isinstance(vault, list)
    if vault:
        assert 'id' in vault[0]
        assert 'type' in vault[0]
        assert 'name' in vault[0]
        assert 'value' in vault[0]
        assert 'unlock_level' in vault[0]
        assert 'unlocked' in vault[0]


def test_terra_merged_run_sources_deduplicate_by_id(monkeypatch):
    require_routes(('GET', '/terra/stats'), ('GET', '/terra/runs'))

    today = datetime(2026, 3, 30)
    seed = {
        'runs': [
            {
                'id': 'shared-run',
                'user_id': 'user-1',
                'distance_km': 3.0,
                'duration_sec': 900,
                'territory_km2': 0.015,
                'xp': 50,
                'date': '2026-03-29',
                'created_at': today,
            }
        ],
        'terra_runs': [
                {
                    'id': 'shared-run',
                    'user_id': 'user-1',
                    'distance': 9.0,
                    'duration': 1800,
                    'territory_captured': 0.4,
                    'xp_earned': 140,
                    'date': '2026-03-30',
                    'created_at': today,
                },
                {
                    'id': 'terra-only-run',
                    'user_id': 'user-1',
                    'distance': 5.0,
                    'duration': 1200,
                    'territory_captured': 0.2,
                    'xp_earned': 90,
                    'date': '2026-03-30',
                    'created_at': today,
                },
        ],
    }
    client, _ = make_client(monkeypatch, seed=seed)

    stats_response = client.get('/api/terra/stats')
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats['total_runs'] == 2
    assert stats['total_distance'] == 14.0
    assert stats['xp'] == 230
    assert stats['total_territory'] == 0.6

    runs_response = client.get('/api/terra/runs')
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert [run['id'] for run in runs] == ['shared-run', 'terra-only-run']

from __future__ import annotations

import copy
import importlib.util
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
        pytest.skip('Coach backend slice not implemented yet: ' + ', '.join(missing))


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
                    import re

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

    async def delete_many(self, query: dict | None = None):
        before = len(self.docs)
        self.docs = [doc for doc in self.docs if not self._matches(doc, query or {})]
        return SimpleNamespace(deleted_count=before - len(self.docs))

    async def insert_many(self, docs):
        docs = list(docs)
        for doc in docs:
            self.docs.append(copy.deepcopy(doc))
        return SimpleNamespace(inserted_ids=[doc.get('id') for doc in docs])

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


def make_db(monkeypatch, seed: dict[str, list[dict]] | None = None):
    fake_db = FakeDB(seed)
    monkeypatch.setattr(server, 'db', fake_db)
    return fake_db


def set_current_user(current_user: dict):
    server.app.dependency_overrides[server.get_current_user] = lambda: current_user


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    server.app.dependency_overrides.clear()


def test_coach_client_lifecycle_enforces_relationship_and_completion(monkeypatch):
    require_routes(
        ('GET', '/coach/clients'),
        ('GET', '/coach/search-users'),
        ('POST', '/coach/send-request'),
        ('POST', '/coach/workouts'),
        ('POST', '/coach/meals'),
        ('POST', '/coach/goals'),
        ('GET', '/client/pending-requests'),
        ('POST', '/client/respond-request/{request_id}'),
        ('GET', '/my-coach-workouts'),
        ('GET', '/my-coach-meals'),
        ('GET', '/my-coach-goals'),
        ('POST', '/coach/workouts/{workout_id}/complete'),
    )

    coach = {
        'id': 'coach-1',
        'email': 'coach@example.com',
        'name': 'Coach One',
        'mode': 'coach',
        'profile': {},
        'created_at': datetime(2026, 3, 30),
    }
    client_user = {
        'id': 'client-1',
        'email': 'client@example.com',
        'name': 'Client One',
        'mode': 'user',
        'profile': {},
        'created_at': datetime(2026, 3, 30),
    }
    seed = {
        'users': [coach, client_user, {
            'id': 'coach-2',
            'email': 'other-coach@example.com',
            'name': 'Coach Two',
            'mode': 'coach',
            'profile': {},
            'created_at': datetime(2026, 3, 30),
        }],
        'coach_requests': [],
        'workouts': [],
        'coach_meals': [],
        'coach_goals': [],
    }

    make_db(monkeypatch, seed=seed)
    client = TestClient(server.app)
    set_current_user(coach)

    search_response = client.get('/api/coach/search-users?query=client')
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert any(item['id'] == 'client-1' for item in search_results)
    assert all(item['id'] != 'coach-2' for item in search_results)

    send_request_response = client.post(
        '/api/coach/send-request',
        json={'client_id': 'client-1', 'message': 'Join my program'},
    )
    assert send_request_response.status_code == 200
    request_doc = send_request_response.json()
    assert request_doc['status'] == 'pending'
    request_id = request_doc['id']

    duplicate_request_response = client.post(
        '/api/coach/send-request',
        json={'client_id': 'client-1', 'message': 'Updated note'},
    )
    assert duplicate_request_response.status_code == 200
    assert duplicate_request_response.json()['id'] == request_id

    blocked_workout_response = client.post(
        '/api/coach/workouts',
        json={
            'client_id': 'client-1',
            'title': 'Strength Day',
            'description': 'Blocked until the client accepts the request.',
            'workout_type': 'strength',
            'difficulty': 'intermediate',
            'duration': 45,
            'exercises': [],
        },
    )
    assert blocked_workout_response.status_code == 403

    blocked_client_view_response = client.get('/api/client/pending-requests')
    assert blocked_client_view_response.status_code == 403

    set_current_user(client_user)
    client_view = client
    pending_response = client_view.get('/api/client/pending-requests')
    assert pending_response.status_code == 200
    pending_requests = pending_response.json()
    assert len(pending_requests) == 1
    assert pending_requests[0]['id'] == request_id

    accept_response = client_view.post(f'/api/client/respond-request/{request_id}?approve=true')
    assert accept_response.status_code == 200

    set_current_user(coach)
    coach_view = client
    clients_response = coach_view.get('/api/coach/clients')
    assert clients_response.status_code == 200
    clients = clients_response.json()
    assert len(clients) == 1
    assert clients[0]['id'] == 'client-1'
    assert clients[0]['total_workouts'] == 0

    workout_response = coach_view.post(
        '/api/coach/workouts',
        json={
            'client_id': 'client-1',
            'title': 'Strength Day',
            'description': 'Assigned after acceptance.',
            'workout_type': 'strength',
            'difficulty': 'intermediate',
            'duration': 45,
            'exercises': [{'name': 'Squat', 'sets': 4, 'reps': '8'}],
        },
    )
    assert workout_response.status_code == 200
    workout_doc = workout_response.json()
    assert workout_doc['source'] == 'coach'
    workout_id = workout_doc['id']

    meal_response = coach_view.post(
        '/api/coach/meals',
        json={
            'client_id': 'client-1',
            'title': 'Lunch plan',
            'description': 'High protein lunch',
            'meal_type': 'lunch',
            'total_calories': 550,
        },
    )
    assert meal_response.status_code == 200
    assert meal_response.json()['coach_id'] == 'coach-1'

    goal_response = coach_view.post(
        '/api/coach/goals',
        json={
            'client_id': 'client-1',
            'title': 'Weekly consistency',
            'description': 'Finish all assigned sessions.',
            'goal_type': 'general_fitness',
            'target_value': 4,
            'unit': 'sessions',
            'target_date': '2026-04-06',
        },
    )
    assert goal_response.status_code == 200
    assert goal_response.json()['client_id'] == 'client-1'

    set_current_user(client_user)
    client_view = client
    workouts_response = client_view.get('/api/my-coach-workouts')
    meals_response = client_view.get('/api/my-coach-meals')
    goals_response = client_view.get('/api/my-coach-goals')
    assert workouts_response.status_code == 200
    assert meals_response.status_code == 200
    assert goals_response.status_code == 200
    assert len(workouts_response.json()) == 1
    assert len(meals_response.json()) == 1
    assert len(goals_response.json()) == 1

    complete_response = client_view.post(f'/api/coach/workouts/{workout_id}/complete')
    assert complete_response.status_code == 200

    repeat_complete_response = client_view.post(f'/api/coach/workouts/{workout_id}/complete')
    assert repeat_complete_response.status_code == 200
    assert repeat_complete_response.json().get('already_completed') is True

    set_current_user(coach)
    coach_view = client
    updated_clients_response = coach_view.get('/api/coach/clients')
    assert updated_clients_response.status_code == 200
    updated_clients = updated_clients_response.json()
    assert updated_clients[0]['completed_workouts'] == 1
    assert updated_clients[0]['compliance_rate'] == 100.0

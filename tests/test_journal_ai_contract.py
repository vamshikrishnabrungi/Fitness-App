from __future__ import annotations

import copy
import importlib.util
import json
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
        pytest.skip('Journal + AI backend slice not implemented yet: ' + ', '.join(missing))


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

    async def delete_one(self, query: dict):
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)


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
    def __init__(self, responses: list[str]):
        self._responses = responses
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, *args, **kwargs):
        content = self._responses.pop(0) if self._responses else '{}'
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_client(monkeypatch, seed: dict[str, list[dict]] | None = None, ai_responses: list[str] | None = None):
    fake_db = FakeDB(seed)
    monkeypatch.setattr(server, 'db', fake_db)
    monkeypatch.setattr(server, 'openai_client', FakeOpenAIClient(ai_responses or []))
    server.app.dependency_overrides[server.get_current_user] = lambda: {
        'id': 'user-1',
        'email': 'athlete@example.com',
        'name': 'Athlete',
        'mode': 'user',
        'profile': {},
        'created_at': datetime(2026, 3, 30),
    }
    return TestClient(server.app), fake_db


def test_journal_deep_contract(monkeypatch):
    require_routes(
        ('POST', '/journal/deep'),
        ('GET', '/journal/deep'),
        ('GET', '/journal/deep/{entry_id}'),
        ('PUT', '/journal/deep/{entry_id}'),
        ('DELETE', '/journal/deep/{entry_id}'),
        ('GET', '/journal/on-this-day'),
    )

    seed = {
        'journal_entries': [
            {
                'id': 'entry-old',
                'title': 'Race nerves',
                'content': 'I felt anxious before the start but settled in.',
                'entry_type': 'deep',
                'date': '2025-03-30',
                'created_at': datetime(2025, 3, 30, 8, 0),
                'tags': ['race', 'mindset'],
                'is_pinned': False,
            },
            {
                'id': 'entry-recent',
                'title': 'Recovery note',
                'content': 'Sleep and stretching helped today.',
                'entry_type': 'deep',
                'date': '2026-03-29',
                'created_at': datetime(2026, 3, 29, 20, 0),
                'tags': ['recovery'],
                'is_pinned': True,
            },
        ]
    }
    client, _ = make_client(monkeypatch, seed=seed)

    create_response = client.post(
        '/api/journal/deep',
        json={
            'title': 'Morning reflection',
            'content': 'Training felt sharp and focused.',
            'tags': ['training', 'focus'],
            'is_pinned': True,
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created['title'] == 'Morning reflection'
    assert created['content'] == 'Training felt sharp and focused.'
    assert created['is_pinned'] is True
    assert isinstance(created['id'], str)

    list_response = client.get('/api/journal/deep?limit=20')
    assert list_response.status_code == 200
    entries = list_response.json()
    assert isinstance(entries, list)
    assert entries[0]['id'] in {'entry-recent', created['id']}

    detail_response = client.get(f"/api/journal/deep/{created['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail['id'] == created['id']

    update_response = client.put(
        f"/api/journal/deep/{created['id']}",
        json={
            'title': 'Morning reflection',
            'content': 'Training felt sharp, focused, and calm.',
            'tags': ['training', 'focus'],
            'is_pinned': False,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated['content'] == 'Training felt sharp, focused, and calm.'
    assert updated['is_pinned'] is False

    on_this_day_response = client.get('/api/journal/on-this-day')
    assert on_this_day_response.status_code == 200
    on_this_day = on_this_day_response.json()
    assert isinstance(on_this_day, list)

    delete_response = client.delete(f"/api/journal/deep/{created['id']}")
    assert delete_response.status_code == 200


def test_guided_templates_programs_and_calendar_contract_uses_builtin_definitions(monkeypatch):
    require_routes(
        ('GET', '/journal/templates'),
        ('GET', '/journal/programs'),
        ('POST', '/journal/guided'),
        ('POST', '/journal/programs/{program_id}/start'),
        ('GET', '/journal/calendar'),
    )

    client, _ = make_client(monkeypatch)

    templates_response = client.get('/api/journal/templates')
    assert templates_response.status_code == 200
    templates = templates_response.json()
    assert isinstance(templates, list)
    gratitude_template = next(template for template in templates if template['id'] == 'gratitude_daily')
    assert gratitude_template['name'] == 'Daily Gratitude'
    assert gratitude_template['prompts'][0]['key'] == 'wins'

    programs_response = client.get('/api/journal/programs')
    assert programs_response.status_code == 200
    programs = programs_response.json()
    assert 'programs' in programs
    assert 'active_enrollments' in programs
    consistency_program = next(program for program in programs['programs'] if program['id'] == 'consistency_7')
    assert consistency_program['name'] == '7-Day Consistency Challenge'
    assert programs['active_enrollments'] == []

    guided_response = client.post(
        '/api/journal/guided',
        json={
            'template_id': gratitude_template['id'],
            'template_name': gratitude_template['name'],
            'responses': {'win': 'Finished intervals', 'thanks': 'My coach'},
        },
    )
    assert guided_response.status_code == 200
    guided = guided_response.json()
    assert guided['template_id'] == gratitude_template['id']
    assert guided['template_name'] == gratitude_template['name']
    assert guided['entry_type'] == 'guided'
    assert 'Finished intervals' in guided['content']

    start_response = client.post('/api/journal/programs/consistency_7/start')
    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert start_payload['program_id'] == 'consistency_7'
    assert start_payload['current_day'] == 1
    assert start_payload['is_active'] is True

    calendar_response = client.get('/api/journal/calendar?year=2026&month=3')
    assert calendar_response.status_code == 200
    calendar = calendar_response.json()
    assert isinstance(calendar, dict)
    assert guided['date'] in calendar
    assert calendar[guided['date']]['guided'] >= 1


def test_ai_journal_search_and_insights_contract_uses_db_search_and_ai_insights(monkeypatch):
    require_routes(
        ('POST', '/ai/journal/search'),
        ('GET', '/ai/journal/insights'),
        ('POST', '/ai/coach/chat'),
    )

    seed = {
        'journal_entries': [
            {
                'id': 'entry-1',
                'user_id': 'user-1',
                'title': 'Pre-race anxiety',
                'content': 'I felt anxious before the start line but settled after the warmup.',
                'entry_type': 'deep',
                'date': '2026-03-28',
                'created_at': datetime(2026, 3, 28, 18, 0),
                'mood': 'bad',
            },
            {
                'id': 'entry-2',
                'user_id': 'user-1',
                'title': 'Recovery day',
                'content': 'Stretching and sleep made me feel better.',
                'entry_type': 'guided',
                'date': '2026-03-29',
                'created_at': datetime(2026, 3, 29, 20, 0),
                'mood': 'good',
            },
        ]
    }
    ai_responses = [
        json.dumps(
            {
                'summary': 'Your notes show a strong recovery pattern after stressful sessions.',
                'strength': 'You follow through on recovery habits.',
                'improvement': 'Capture more detail on sleep and energy.',
                'recommendation': 'Keep journaling after hard sessions.',
            }
        ),
    ]
    client, _ = make_client(monkeypatch, seed=seed, ai_responses=ai_responses)

    search_response = client.post(
        '/api/ai/journal/search',
        json={'query': 'anxious', 'limit': 10},
    )
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert 'results' in search_payload
    assert 'summary' in search_payload
    assert isinstance(search_payload['results'], list)
    assert any(result['id'] == 'entry-1' for result in search_payload['results'])
    assert search_payload['summary']

    insights_response = client.get('/api/ai/journal/insights?period=week')
    assert insights_response.status_code == 200
    insights_payload = insights_response.json()
    assert insights_payload['period'] == 'week'
    assert 'insights' in insights_payload
    if isinstance(insights_payload['insights'], dict):
        assert 'summary' in insights_payload['insights']

    coach_response = client.post(
        '/api/ai/coach/chat',
        json={'message': 'How should I approach recovery this week?'},
    )
    assert coach_response.status_code == 200
    coach_payload = coach_response.json()
    assert isinstance(coach_payload.get('response'), str)
    assert coach_payload['response']

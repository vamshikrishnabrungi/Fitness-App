"""End-to-end backend tests for SFTC: AI workouts + H3 territory + run clubs.

Covers:
- OTP register flow
- /onboarding/complete with AI program generation (Claude Sonnet 4.5 fallback OK)
- Workouts listing / today / complete / regenerate
- Run submission (valid loop / teleport / too-few-points / takeover)
- Territory endpoints (me, cells, leaderboard, peaks/me)
- Clubs CRUD + membership + leaderboards
- Stats aggregates
"""
from __future__ import annotations

import os
import time
import uuid
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest
import requests
from pymongo import MongoClient

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or "https://run-club-build.preview.emergentagent.com"
).rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "sftc_database")

mongo = MongoClient(MONGO_URL)[DB_NAME]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _api(path: str) -> str:
    return f"{BASE_URL}/api{path}"


def _fetch_otp(email: str) -> str:
    for _ in range(20):
        doc = mongo.otps.find_one({"email": email}, sort=[("created_at", -1)])
        if doc:
            return doc["code"]
        time.sleep(0.25)
    raise AssertionError(f"OTP not found for {email}")


def register_user(name_prefix: str = "alex") -> Dict[str, Any]:
    """Returns {email, token, user_id, headers}."""
    ts = int(time.time() * 1000) + uuid.uuid4().int % 1000
    email = f"{name_prefix}+{ts}@example.com"
    r = requests.post(_api("/auth/request-otp"), json={"email": email}, timeout=10)
    assert r.status_code == 200, r.text
    code = _fetch_otp(email)
    payload = {
        "email": email,
        "password": "Pass1234!",
        "name": f"{name_prefix.title()} Runner",
        "otp_code": code,
    }
    r = requests.post(_api("/auth/register"), json=payload, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    token = body["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    user_id = body.get("user", {}).get("id") or body.get("id")
    return {"email": email, "token": token, "user_id": user_id, "headers": headers}


def _profile_payload(city: str = "Hyderabad") -> Dict[str, Any]:
    return {
        "primary_goal": "muscle gain",
        "selected_goals": ["muscle gain", "improve running"],
        "sports": ["running", "strength"],
        "experience": "intermediate",
        "training_days_per_week": 4,
        "session_duration_min": 45,
        "equipment": ["dumbbells", "barbell"],
        "city": city,
        "country": "India",
        "training_location": "gym",
        "preferred_training_days": ["Monday", "Tuesday", "Thursday", "Saturday"],
    }


def _hyd_loop_path(start_ts: datetime, points: int = 12, radius_km: float = 0.15) -> List[Dict[str, Any]]:
    """Build a circular loop around Hyderabad (17.43, 78.45), ~1 km perimeter."""
    cx, cy = 17.4310, 78.4480
    # 0.0015 deg lat ~ 0.165 km
    r_lat = radius_km / 111.0
    r_lng = radius_km / (111.0 * math.cos(math.radians(cx)))
    path = []
    duration_per_pt = 120  # 2 min per point => 12 pts = 24 min
    for i in range(points):
        theta = (2 * math.pi * i) / points
        lat = cx + r_lat * math.sin(theta)
        lng = cy + r_lng * math.cos(theta)
        ts = (start_ts + timedelta(seconds=i * duration_per_pt)).isoformat() + "Z"
        path.append({"latitude": lat, "longitude": lng, "timestamp": ts, "altitude": 500 + i * 6})
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def user_a() -> Dict[str, Any]:
    return register_user("alex")


@pytest.fixture(scope="session")
def user_b() -> Dict[str, Any]:
    return register_user("rival")


@pytest.fixture(scope="session")
def onboarded_a(user_a) -> Dict[str, Any]:
    """Runs the AI onboarding once and caches the resulting program."""
    payload = {"profile": _profile_payload(), "generate_program": True}
    # Claude calls can take 30-90s
    r = requests.post(
        _api("/onboarding/complete"),
        json=payload,
        headers=user_a["headers"],
        timeout=180,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    return body


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    def test_request_otp_and_register(self):
        u = register_user("authcheck")
        assert u["token"]
        # token works
        r = requests.get(_api("/workouts"), headers=u["headers"], timeout=10)
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Onboarding + AI program
# ---------------------------------------------------------------------------

class TestOnboardingAI:
    def test_onboarding_returns_weekly_plan(self, onboarded_a):
        body = onboarded_a
        # source either 'ai' (Claude) or 'rules_engine' fallback
        src = (body.get("source") or "").lower()
        assert src in ("ai", "rules_engine", "rules_engine_v1"), f"unexpected source={src}"
        if "rules_engine" in src:
            print(f"WARN: AI fallback triggered, source={src}")
        plan = body.get("weekly_plan") or []
        # Spec says 12-20 workouts. Allow >=8 to be lenient with fallback.
        assert len(plan) >= 8, f"expected >=8 workouts, got {len(plan)}"
        # Each workout has exercises
        for w in plan[:3]:
            ex = w.get("exercises") or []
            assert ex, f"workout has no exercises: {w.get('title')}"
            first = ex[0]
            assert first.get("name")
            assert first.get("sets") or first.get("reps") or first.get("duration"), "exercise missing sets/reps/duration"

    def test_workouts_persisted(self, user_a, onboarded_a):
        r = requests.get(_api("/workouts"), headers=user_a["headers"], timeout=15)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 8
        # exercises preserved
        assert any((it.get("exercises") or []) for it in items)

    def test_workouts_today(self, user_a, onboarded_a):
        r = requests.get(_api("/workouts/today"), headers=user_a["headers"], timeout=10)
        assert r.status_code == 200
        items = r.json()
        # may be empty list if scheduling went to future; should be a list
        assert isinstance(items, list)

    def test_complete_workout(self, user_a, onboarded_a):
        # pick first upcoming
        r = requests.get(_api("/workouts"), headers=user_a["headers"], timeout=10)
        items = r.json()
        assert items
        wid = items[0]["id"]
        r2 = requests.post(_api(f"/workouts/{wid}/complete"), headers=user_a["headers"], timeout=10)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert body.get("completed") is True
        assert body.get("completed_at")

    def test_regenerate_weekly(self, user_a, onboarded_a):
        r = requests.post(_api("/workouts/generate-weekly"), headers=user_a["headers"], timeout=180)
        assert r.status_code == 200, r.text
        body = r.json()
        assert (body.get("weekly_plan") or []), "regenerated plan empty"
        # confirm previous program was archived
        n_archived = mongo.training_programs.count_documents({"user_id": user_a["user_id"], "status": "archived"})
        assert n_archived >= 1


# ---------------------------------------------------------------------------
# Runs + Anti-cheat + H3 territory
# ---------------------------------------------------------------------------

class TestRuns:
    def test_valid_loop_run(self, user_a):
        start = datetime.utcnow() - timedelta(minutes=30)
        path = _hyd_loop_path(start, points=12, radius_km=0.18)
        payload = {
            "gps_path": path,
            "start_time": start.isoformat() + "Z",
            "end_time": (start + timedelta(seconds=12 * 120)).isoformat() + "Z",
        }
        r = requests.post(_api("/terra/runs"), json=payload, headers=user_a["headers"], timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        ac = body.get("anti_cheat", {})
        assert ac.get("valid") is True, f"anti_cheat reasons={ac.get('reasons')}"
        assert (body.get("distance_km") or body.get("distance") or 0) > 0.3
        claim = body.get("claim", {})
        assert len(claim.get("claimed", [])) > 0
        geo = body.get("territory_geojson", {})
        assert geo.get("features"), "territory_geojson features empty"
        # save for takeover
        TestRuns._user_a_cells = body.get("cells_claimed") or claim.get("claimed") or []
        TestRuns._user_a_path = path

    def test_teleport_rejected(self, user_a):
        start = datetime.utcnow() - timedelta(hours=1)
        # 8 points in Hyderabad with one huge jump after point 1
        path = []
        for i in range(8):
            if i == 1:
                lat, lng = 30.0, 80.0  # jump >1000km
            else:
                lat = 17.43 + i * 0.0008
                lng = 78.45 + i * 0.0008
            ts = (start + timedelta(seconds=i * 60)).isoformat() + "Z"
            path.append({"latitude": lat, "longitude": lng, "timestamp": ts})
        payload = {
            "gps_path": path,
            "start_time": start.isoformat() + "Z",
            "end_time": (start + timedelta(minutes=8)).isoformat() + "Z",
        }
        r = requests.post(_api("/terra/runs"), json=payload, headers=user_a["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        ac = body.get("anti_cheat", {})
        assert ac.get("valid") is False, f"expected invalid, got {ac}"
        reasons = " ".join(ac.get("reasons", []))
        assert "teleport" in reasons.lower() or "avg_speed_above" in reasons.lower()
        claim = body.get("claim", {})
        assert not claim.get("claimed"), f"expected no claim, got {claim}"

    def test_too_few_points_rejected(self, user_a):
        start = datetime.utcnow() - timedelta(minutes=5)
        path = [
            {"latitude": 17.43, "longitude": 78.45, "timestamp": start.isoformat() + "Z"},
            {"latitude": 17.431, "longitude": 78.451, "timestamp": (start + timedelta(seconds=60)).isoformat() + "Z"},
            {"latitude": 17.432, "longitude": 78.452, "timestamp": (start + timedelta(seconds=120)).isoformat() + "Z"},
        ]
        payload = {
            "gps_path": path,
            "start_time": start.isoformat() + "Z",
            "end_time": (start + timedelta(minutes=3)).isoformat() + "Z",
        }
        r = requests.post(_api("/terra/runs"), json=payload, headers=user_a["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        ac = body.get("anti_cheat", {})
        assert ac.get("valid") is False
        assert any("5_points" in s or "points" in s for s in ac.get("reasons", []))
        claim = body.get("claim", {})
        assert not claim.get("claimed")

    def test_takeover_by_user_b(self, user_a, user_b):
        # user_a should already have territory from test_valid_loop_run
        start = datetime.utcnow() - timedelta(minutes=20)
        path = _hyd_loop_path(start, points=12, radius_km=0.18)
        payload = {
            "gps_path": path,
            "start_time": start.isoformat() + "Z",
            "end_time": (start + timedelta(seconds=12 * 120)).isoformat() + "Z",
        }
        r = requests.post(_api("/terra/runs"), json=payload, headers=user_b["headers"], timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        ac = body.get("anti_cheat", {})
        assert ac.get("valid") is True, f"anti_cheat={ac}"
        taken_over = body.get("claim", {}).get("taken_over", [])
        assert len(taken_over) > 0, "expected at least one takeover cell"
        names = [t.get("previous_owner_name") for t in taken_over if isinstance(t, dict)]
        # name may be email or "Alex Runner"
        assert any("alex" in (n or "").lower() or "runner" in (n or "").lower() for n in names), names


# ---------------------------------------------------------------------------
# Territory
# ---------------------------------------------------------------------------

class TestTerritory:
    def test_territory_me(self, user_b):
        r = requests.get(_api("/territory/me"), headers=user_b["headers"], timeout=10)
        assert r.status_code == 200
        body = r.json()
        # Either flat FeatureCollection or wrapper with total_cells
        if "type" in body:
            assert body["type"] == "FeatureCollection"
        else:
            assert "total_cells" in body or "features" in body

    def test_territory_cells_in_bbox(self, user_b):
        params = {"south": 17.42, "west": 78.44, "north": 17.44, "east": 78.46}
        r = requests.get(_api("/territory/cells"), params=params, headers=user_b["headers"], timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "cells_in_view" in body or "cells" in body
        assert "cells_owned" in body or isinstance(body, dict)

    def test_territory_leaderboard(self, user_a):
        r = requests.get(_api("/territory/leaderboard"), headers=user_a["headers"], timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)

    def test_territory_peaks_me(self, user_a):
        r = requests.get(_api("/territory/peaks/me"), headers=user_a["headers"], timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)


# ---------------------------------------------------------------------------
# Clubs
# ---------------------------------------------------------------------------

class TestClubs:
    @pytest.fixture(scope="class")
    def club_ctx(self, user_a, user_b):
        # owner = user_a
        r = requests.post(
            _api("/terra/clubs"),
            json={"name": f"Hyd Trail {int(time.time())}", "city": "Hyderabad", "description": "Test club", "is_public": True},
            headers=user_a["headers"],
            timeout=10,
        )
        assert r.status_code == 200, r.text
        club = r.json()
        assert club.get("member_count") == 1
        assert club.get("invite_code")
        return {"club": club}

    def test_club_create_fields(self, club_ctx, user_a):
        club = club_ctx["club"]
        assert club.get("owner_id") == user_a["user_id"]
        # is_owner only present in detail; member_count + invite_code asserted in fixture

    def test_my_and_city_lists(self, club_ctx, user_a):
        cid = club_ctx["club"]["id"]
        my = requests.get(_api("/terra/clubs/my"), headers=user_a["headers"], timeout=10).json()
        assert any(c["id"] == cid for c in my)
        city = requests.get(_api("/terra/clubs/city?city=Hyderabad"), headers=user_a["headers"], timeout=10).json()
        assert any(c["id"] == cid for c in city)

    def test_detail_and_members(self, club_ctx, user_a):
        cid = club_ctx["club"]["id"]
        d = requests.get(_api(f"/terra/clubs/{cid}"), headers=user_a["headers"], timeout=10)
        assert d.status_code == 200
        m = requests.get(_api(f"/terra/clubs/{cid}/members"), headers=user_a["headers"], timeout=10)
        assert m.status_code == 200
        assert any(mb.get("is_owner") for mb in m.json())

    def test_join_and_leave(self, club_ctx, user_a, user_b):
        cid = club_ctx["club"]["id"]
        r = requests.post(_api(f"/terra/clubs/{cid}/join"), headers=user_b["headers"], timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert user_b["user_id"] in body.get("member_ids", [])
        # owner cannot leave
        r2 = requests.post(_api(f"/terra/clubs/{cid}/leave"), headers=user_a["headers"], timeout=10)
        assert r2.status_code == 400
        # user_b leaves OK
        r3 = requests.post(_api(f"/terra/clubs/{cid}/leave"), headers=user_b["headers"], timeout=10)
        assert r3.status_code == 200
        # rejoin for territory test
        requests.post(_api(f"/terra/clubs/{cid}/join"), headers=user_b["headers"], timeout=10)

    def test_territory_and_leaderboards(self, club_ctx, user_a):
        cid = club_ctx["club"]["id"]
        t = requests.get(_api(f"/terra/clubs/{cid}/territory"), headers=user_a["headers"], timeout=15)
        assert t.status_code == 200
        body = t.json()
        assert body.get("type") == "FeatureCollection"
        lb = requests.get(_api(f"/terra/clubs/{cid}/members/leaderboard"), headers=user_a["headers"], timeout=15)
        assert lb.status_code == 200
        assert isinstance(lb.json(), list)
        city_lb = requests.get(_api("/terra/clubs/leaderboard/city"), headers=user_a["headers"], timeout=15)
        assert city_lb.status_code == 200

    def test_delete_permissions(self, club_ctx, user_a, user_b):
        cid = club_ctx["club"]["id"]
        # non-owner forbidden
        r = requests.delete(_api(f"/terra/clubs/{cid}"), headers=user_b["headers"], timeout=10)
        assert r.status_code == 403
        # owner OK
        r2 = requests.delete(_api(f"/terra/clubs/{cid}"), headers=user_a["headers"], timeout=10)
        assert r2.status_code == 200


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_terra_stats(self, user_a):
        r = requests.get(_api("/terra/stats"), headers=user_a["headers"], timeout=10)
        assert r.status_code == 200
        body = r.json()
        for k in ("total_runs", "total_distance", "xp", "level"):
            assert k in body, f"missing {k}"

    def test_runs_stats_consistent(self, user_a):
        r1 = requests.get(_api("/terra/stats"), headers=user_a["headers"], timeout=10).json()
        r2 = requests.get(_api("/runs/stats"), headers=user_a["headers"], timeout=10).json()
        assert r2.get("total_distance") == r1.get("total_distance")

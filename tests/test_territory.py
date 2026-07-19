"""Proves the territory capture engine: segmentation, GPS matching, decay, ownership flips, status."""
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("territory", ROOT / "backend" / "territory.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)

# A ~605 m corridor running east at lat 17.43 (Hyderabad-ish).
CORRIDOR = [(17.4300, 78.4700), (17.4300, 78.4757)]


def _trace(lng0, lng1, n=12, lat=17.4302):
    """Sample a GPS trace along the corridor (lat offset ~22 m to mimic GPS drift, within tol)."""
    return [(lat, lng0 + (lng1 - lng0) * i / (n - 1)) for i in range(n)]


def test_segmentation():
    length = t.polyline_length_m(CORRIDOR)
    segs = t.split_into_segments(CORRIDOR, seg_len_m=150)
    assert 590 < length < 620
    assert len(segs) == 4  # 605 m / 150 ≈ 4 units
    # each segment ~150 m (last a bit longer)
    for s in segs[:-1]:
        assert 140 < t.polyline_length_m(s) < 160


def test_matching_on_and_off_corridor():
    segs = t.split_into_segments(CORRIDOR, seg_len_m=150)
    on = t.match_trace_to_segments(_trace(78.4700, 78.4757), segs)
    assert sum(on.values()) > 500          # a full run covers the corridor
    assert len(on) >= 3                     # spread across multiple segments

    far = t.match_trace_to_segments(_trace(78.4700, 78.4757, lat=17.4500), segs)  # ~2 km north
    assert sum(far.values()) == 0           # nothing matches off-corridor


def test_freshness_decay():
    now = datetime(2026, 1, 31)
    assert t.freshness_weight(now, now) == 1.0
    assert abs(t.freshness_weight(now - timedelta(days=15), now) - 0.5) < 0.01
    assert t.freshness_weight(now - timedelta(days=31), now) == 0.0   # outside 30-day window


def test_ownership_and_steal():
    now = datetime(2026, 1, 31)
    contribs = [
        {"club_id": "orange", "meters": 300, "ts": now},
        {"club_id": "blue", "meters": 400, "ts": now},
    ]
    owner, _ = t.owner_of(contribs, now)
    assert owner == "blue"                          # more meters → owns it
    contribs.append({"club_id": "orange", "meters": 250, "ts": now})
    owner, _ = t.owner_of(contribs, now)
    assert owner == "orange"                         # orange runs more → steals it

    # decay hands it back: blue's lead is old, orange is fresh
    old = [
        {"club_id": "blue", "meters": 400, "ts": now - timedelta(days=25)},  # heavily decayed
        {"club_id": "orange", "meters": 200, "ts": now},                     # fresh
    ]
    owner, _ = t.owner_of(old, now)
    assert owner == "orange"


def test_status_labels():
    assert t.corridor_status(70, 30, you_own=True) == "strong"
    assert t.corridor_status(50, 50, you_own=True) == "under_attack"
    assert t.corridor_status(50, 50, you_own=False) == "easy_capture"
    assert t.corridor_status(35, 65, you_own=False) == "contested"
    assert t.corridor_status(10, 90, you_own=False) == "enemy_stronghold"
    assert t.corridor_status(0, 0, you_own=False) == "neutral"


def test_end_to_end_capture_flow():
    """Orange claims the corridor; Blue runs it twice and takes it; status reads correctly."""
    now = datetime(2026, 1, 31)
    segs = t.split_into_segments(CORRIDOR, seg_len_m=150)
    contributions = []
    # Orange runs the full corridor once
    for meters in t.match_trace_to_segments(_trace(78.4700, 78.4757), segs).values():
        contributions.append({"club_id": "orange", "meters": meters, "ts": now})
    owner, _ = t.owner_of(contributions, now)
    assert owner == "orange"

    # Blue runs it twice → more total influence
    for _ in range(2):
        for meters in t.match_trace_to_segments(_trace(78.4700, 78.4757), segs).values():
            contributions.append({"club_id": "blue", "meters": meters, "ts": now})
    inf = t.influence_by_club(contributions, now)
    owner = max(inf, key=inf.get)
    assert owner == "blue"

    # From Orange's view it's now contested (behind, but close-ish), not owned
    status = t.corridor_status(inf.get("orange", 0), inf.get("blue", 0), you_own=False)
    assert status in ("contested", "enemy_stronghold")

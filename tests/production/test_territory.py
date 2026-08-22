from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from backend.app.competition.territory import DailyTraversal, club_winner, daily_points, personal_winner, strongest_distinct_days


def row(athlete, club, age, confidence=.9, coverage=.9, speed=4):
    today=date(2026,8,6); moment=datetime(2026,8,6,tzinfo=timezone.utc)-timedelta(days=age)
    return DailyTraversal(athlete,club,today-timedelta(days=age),confidence,coverage,speed,moment)


def test_decay_and_rolling_window():
    athlete,club=uuid4(),uuid4(); today=date(2026,8,6)
    assert daily_points(row(athlete,club,14),today)==pytest.approx(daily_points(row(athlete,club,0),today)/2)
    assert strongest_distinct_days([row(athlete,club,x) for x in range(9)]+[row(athlete,club,28)],today).__len__()==7


def test_personal_and_club_winners_are_deterministic():
    today=date(2026,8,6); club_a,club_b=uuid4(),uuid4(); athletes=[uuid4() for _ in range(8)]
    rows=[row(a,club_a,0,.95,.95) for a in athletes[:6]]+[row(a,club_b,0,.9,.9) for a in athletes[6:]]
    assert personal_winner(rows,today)[0] in athletes[:6]
    assert club_winner(rows,today)[0]==club_a


def test_speed_then_earliest_aggregate_completion_breaks_equal_scores():
    today = date(2026, 8, 6)
    club_a, club_b = uuid4(), uuid4()
    athlete_a, athlete_b = uuid4(), uuid4()
    early = datetime(2026, 8, 6, 8, tzinfo=timezone.utc)
    late = datetime(2026, 8, 6, 9, tzinfo=timezone.utc)
    equal = [
        DailyTraversal(athlete_a, club_a, today, .9, .9, 4.0, late),
        DailyTraversal(athlete_b, club_b, today, .9, .9, 4.1, late),
    ]
    assert personal_winner(equal, today)[0] == athlete_b
    assert club_winner(equal, today)[0] == club_b

    equal_time_tie = [
        DailyTraversal(athlete_a, club_a, today, .9, .9, 4.0, early),
        DailyTraversal(athlete_b, club_b, today, .9, .9, 4.0, late),
    ]
    assert personal_winner(equal_time_tie, today)[0] == athlete_a
    assert club_winner(equal_time_tie, today)[0] == club_a


import pytest

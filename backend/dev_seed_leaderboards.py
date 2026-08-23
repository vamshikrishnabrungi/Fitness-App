"""Dev: seed geographic regions + leaderboard facts to exercise the new boards."""
import asyncio
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, func, select  # noqa: E402
from backend.app.core.database import SessionFactory  # noqa: E402
from backend.app.identity.models import EmailIdentity  # noqa: E402
from backend.app.athletes.models import AthleteProfile  # noqa: E402
from backend.app.competition.models import Club, LeaderboardFact  # noqa: E402
from backend.app.maps.models import GeographicRegion  # noqa: E402
from backend.app.competition.leaderboards import current_period_code  # noqa: E402


async def region(session, code, name, country):
    r = await session.scalar(select(GeographicRegion).where(GeographicRegion.code == code))
    if r:
        return r.id
    poly = func.ST_Multi(func.ST_SetSRID(func.ST_GeomFromText(
        "POLYGON((0 0,0.1 0,0.1 0.1,0 0.1,0 0))"), 4326))
    r = GeographicRegion(code=code, name=name, region_type="city", country_code=country, boundary=poly)
    session.add(r); await session.flush()
    return r.id


async def athlete(session, email):
    ident = await session.scalar(select(EmailIdentity).where(EmailIdentity.normalized_email == email))
    return await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == ident.user_id))


async def main():
    period = current_period_code("week")
    async with SessionFactory() as session:
        await session.execute(delete(LeaderboardFact).where(LeaderboardFact.source_type == "lb-seed"))
        monaco = await region(session, "city-monaco", "Monaco", "MC")
        nice = await region(session, "city-nice", "Nice", "FR")
        a = await athlete(session, "owner@test.dev")
        b = await athlete(session, "member@test.dev")
        club = await session.scalar(select(Club).where(Club.slug == "club-alpha"))
        club_id = club.id if club else None
        data = [
            (a, club_id, monaco, 42000.0),
            (b, club_id, monaco, 31000.0),
            (a, club_id, nice, 12000.0),
            (b, club_id, nice, 26000.0),
        ]
        for ath, cid, reg, val in data:
            session.add(LeaderboardFact(
                source_type="lb-seed", source_id=uuid4(), athlete_id=ath, club_id=cid,
                region_id=reg, metric_code="distance_m", period_code=period,
                value=val, eligible=True, visibility="public"))
        await session.commit()
        print(f"seeded facts for period {period}: Monaco(MC) + Nice(FR)")


asyncio.run(main())

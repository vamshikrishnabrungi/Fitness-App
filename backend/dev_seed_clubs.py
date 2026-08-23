"""Dev-only: seed two athletes and print JWT access tokens for club smoke tests."""
import asyncio
import os
import sys
from datetime import date, datetime, timezone
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402
from backend.app.core.database import SessionFactory  # noqa: E402
from backend.app.core.security import create_access_token  # noqa: E402
from backend.app.identity.models import EmailIdentity, PrivacySettings, User  # noqa: E402
from backend.app.athletes.models import AthleteProfile  # noqa: E402


async def ensure_athlete(session, email, name):
    ident = await session.scalar(select(EmailIdentity).where(EmailIdentity.normalized_email == email))
    if ident:
        user = await session.get(User, ident.user_id)
    else:
        user = User(id=uuid4(), display_name=name, birth_date=date(1995, 1, 1),
                    status="active", onboarding_completed=True)
        session.add(user)
        await session.flush()
        session.add(EmailIdentity(user_id=user.id, email=email, normalized_email=email,
                                  verified_at=datetime.now(timezone.utc), primary=True))
        session.add(PrivacySettings(user_id=user.id, public_leaderboards=True))
    profile = await session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user.id))
    if profile is None:
        profile = AthleteProfile(user_id=user.id, timezone="UTC", competition_level="recreational")
        session.add(profile)
    await session.commit()
    token = create_access_token(user.id, uuid4(), ["athlete"])
    return user.id, profile.id, token


async def main():
    async with SessionFactory() as session:
        for email, name in [("owner@test.dev", "Owner Runner"), ("member@test.dev", "Member Runner")]:
            uid, aid, token = await ensure_athlete(session, email, name)
            print(f"{email}\tuser={uid}\tathlete={aid}\nTOKEN={token}\n")


asyncio.run(main())

import asyncio
import uuid
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Connect to DB
client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client['sftc_dev']

async def seed():
    print("Clearing old data...")
    await db.users.delete_many({})
    await db.run_clubs.delete_many({})
    await db.run_club_memberships.delete_many({})
    await db.terra_runs.delete_many({})

    # 1. Create 3 Users
    users = []
    names = ["Alice (Admin)", "Bob (Member)", "Charlie (Runner)"]
    for name in names:
        user_id = str(uuid.uuid4())
        users.append(user_id)
        await db.users.insert_one({
            "id": user_id,
            "name": name,
            "email": f"{name.split()[0].lower()}@test.com",
            "created_at": datetime.utcnow()
        })
    print(f"Created {len(users)} users.")

    # 2. Create a Run Club
    club_id = str(uuid.uuid4())
    await db.run_clubs.insert_one({
        "id": club_id,
        "name": "Local Legends Club",
        "city": "Austin",
        "description": "A club for testing the new backend features!",
        "is_public": True,
        "owner_id": users[0],
        "member_ids": users,  # Legacy array for quick lookups
        "created_at": datetime.utcnow()
    })
    print("Created 1 Run Club.")

    # 3. Create Memberships
    roles = ["owner", "member", "member"]
    for i, user_id in enumerate(users):
        await db.run_club_memberships.insert_one({
            "club_id": club_id,
            "user_id": user_id,
            "role": roles[i],
            "status": "active",
            "joined_at": datetime.utcnow()
        })
    print("Created 3 active memberships.")

    # 4. Generate Random GPS Runs for the Leaderboard
    runs = 0
    now = datetime.utcnow()
    for user_id in users:
        # Each user did 2-5 runs in the last week
        num_runs = random.randint(2, 5)
        for _ in range(num_runs):
            distance = round(random.uniform(3.0, 15.0), 2)
            await db.terra_runs.insert_one({
                "run_id": str(uuid.uuid4()),
                "user_id": user_id,
                "distance_meters": distance * 1000,
                "start_time": (now - timedelta(days=random.randint(0, 6))).isoformat(),
                "territory_km2": round(distance * 0.1, 4)
            })
            runs += 1
    
    print(f"Created {runs} Terra Runs (GPS workouts) for the leaderboard.")
    print(f"\n--- SUCCESS ---")
    print(f"You can now test the leaderboard endpoint: GET /api/terra/clubs/{club_id}/members/leaderboard")

asyncio.run(seed())

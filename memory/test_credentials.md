# Test Credentials (dev environment)

The Runlete API uses passwordless (OTP/JWT) auth. For local backend testing, mint
JWTs directly instead of using passwords.

## Mint athlete tokens
```
cd /app && python backend/dev_seed_clubs.py
```
Seeds two athletes (idempotent) and prints 15-min access tokens:
- owner@test.dev  → display "Owner Runner"
- member@test.dev → display "Member Runner"

Use as `Authorization: Bearer <TOKEN>`. All mutations need an `Idempotency-Key` header.

## Admin Studio (open access in dev)
`ADMIN_STUDIO_OPEN_ACCESS=true` → `/api/v1/admin/*` and `/api/v1/moderation/admin*`
require NO token in dev (auto local admin `0198f000-0000-7000-8000-000000000001`).

## Services
- API:      http://localhost:8001  (supervisor: backend)
- Postgres: postgresql+asyncpg://runlete:runlete@localhost:5432/runlete (supervisor: postgresql)
- Redis:    redis://localhost:6379/0 (supervisor: redis)

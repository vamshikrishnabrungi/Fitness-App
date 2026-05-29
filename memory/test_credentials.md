# Test credentials

Backend e2e flow uses OTP-based registration. Codes are stored in the
`otps` collection (10 min TTL) and logged to backend stdout.

Workflow for creating a test user:
1. `POST /api/auth/request-otp { "email": "<email>" }`
2. Read the latest OTP from MongoDB: `db.otps.find({email:'<email>'}).sort({created_at:-1}).limit(1)`
   (or scrape it from `/var/log/supervisor/backend.out.log`).
3. `POST /api/auth/register { email, password, name, otp_code }` → returns `access_token`.

## Long-lived demo accounts (created during integration testing)

| Purpose | Email pattern | Password |
| --- | --- | --- |
| Primary onboarding subject | `alex+<ts>@example.com` | `Pass1234!` |
| Rival runner (territory takeover) | `rival+<ts>@example.com` | `Pass1234!` |

Both follow the OTP flow above. Replace `<ts>` with a fresh unix timestamp to
avoid hitting the unique-email constraint.

## API key

`EMERGENT_LLM_KEY=sk-emergent-41d0274F218D055Ad9` (in `/app/backend/.env`)
Powers Claude Sonnet 4.5 calls through `emergentintegrations`.

# Deploying the Runlete backend (Render + MongoDB Atlas)

The backend needs two cloud pieces: a **database** (MongoDB Atlas) and an **app
host** (Render). The app creates its own collections and indexes on first boot,
so there is **no seeding step** — a fresh database just works.

Total time: ~20 minutes, no credit card.

---

## 1. Database — MongoDB Atlas (free)

1. Sign up at <https://www.mongodb.com/atlas> and create a **free M0 cluster**
   (pick a region close to you, e.g. Mumbai).
2. **Database Access** → Add a database user (username + password). Save the
   password.
3. **Network Access** → Add IP `0.0.0.0/0` (allow from anywhere — Render's IPs
   aren't fixed on the free tier).
4. **Connect → Drivers** → copy the connection string. It looks like:
   ```
   mongodb+srv://USER:PASSWORD@cluster0.xxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Put your real password in place of `PASSWORD`. This is your **MONGO_URL**.

---

## 2. App host — Render (free)

1. Sign up at <https://render.com> with your GitHub account.
2. **New → Blueprint** → connect this repo → pick the branch to deploy
   (`main`, or `feat/adaptive-workout-engine` if you haven't merged yet).
   Render reads `render.yaml` and sets up the service automatically.
3. It will prompt for the values marked `sync: false`. Enter:

   | Key | Value |
   |-----|-------|
   | `MONGO_URL` | the Atlas string from step 1 |
   | `JWT_SECRET` | a long random string — run `openssl rand -hex 32` and paste it. **Keep it stable**; changing it logs everyone out. |
   | `INFO_EMAIL_USER` | `info@ydhya.in` |
   | `INFO_EMAIL_PASS` | your Hostinger mailbox password |
   | `ALLOWED_ORIGINS` | `https://runlete-api.onrender.com` (your Render URL, filled in after first deploy — the mobile app itself doesn't need CORS) |

4. Click **Apply**. Render installs deps and starts the app. First build takes
   ~5–10 min.

When it's live you'll get a URL like `https://runlete-api.onrender.com`.
Check it's up:
```
curl https://runlete-api.onrender.com/api/
# {"status":"ok"}
```

> **Free-tier note:** the instance sleeps after 15 min idle, so the first
> request after a break takes ~30s to wake. Normal for testing.

---

## 3. Point the app at the hosted backend

In `frontend/.env`:
```
EXPO_PUBLIC_BACKEND_URL=https://runlete-api.onrender.com
```
Then rebuild the app so the URL is baked in.

> In dev (`__DEV__`) the app auto-detects your Mac's Metro host and ignores this
> value — that's intentional. `EXPO_PUBLIC_BACKEND_URL` is used by **release
> builds**, which is what you'd install on a phone to run untethered.

---

## What is NOT needed

- **No seeding.** Collections + indexes are created on startup. Users, clubs,
  runs and territory all populate themselves as people use the app.
- **No workout/AI keys.** `WORKOUT_GENERATION_ENABLED=false` and
  `EXERCISE_EMBEDDINGS_ENABLED=false` keep those off. Add `ANTHROPIC_API_KEY` /
  `OPENROUTER_API_KEY` and flip the flags later if you re-enable workouts.

## Redeploying

Render auto-deploys on every push to the connected branch. To change a secret,
edit it under the service's **Environment** tab and redeploy.

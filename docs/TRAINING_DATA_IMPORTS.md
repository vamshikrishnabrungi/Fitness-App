# Training data imports

The Admin Studio **Data imports** page is the only supported way to stage and commit the four workout-generation datasets. Uploaded source files are retained as provenance rows; runtime planning reads PostgreSQL only.

## Before the first upload

Apply Alembic revision `20260815_05` to the target database:

```bash
alembic -c alembic.ini upgrade head
```

For GCP Cloud SQL, start the instance and Cloud SQL Auth Proxy first, then run the command with the production `DATABASE_URL`. Do not run it while the instance is intentionally stopped.

## Upload order

1. `Backend data files/exercises/curated_exercises.csv`
2. All nine `Backend data files/exercise templates/phase_*_exercise_templates.json` files in one selection
3. `Backend data files/sport models/sport_role_phase_goal_priority_matrix.csv`
4. These three files in one selection:
   - `category_level_availability.json`
   - `sport_mode_policy.json`
   - `scenario_overlays.json`

Each upload has two explicit operations:

- **Preview** parses and validates every record but does not update runtime tables.
- **Commit to PostgreSQL** runs one transaction and is disabled when preview errors exist.

## Update behavior

- Exercises retain their stable UUID and receive a new immutable content version when their stable code already exists.
- Four-week references retain their stable UUID and receive a new immutable content version.
- Sport-priority and policy records retain their stable UUID for matching canonical keys; records removed from an authoritative replacement file are removed during commit.
- A source type plus content hash is unique, so submitting the same input again is idempotent.
- Four-week templates pin the current immutable exercise version at commit time.

Importing data does not publish a knowledge release or enable workout generation. Release validation and the application feature flag remain separate gates.

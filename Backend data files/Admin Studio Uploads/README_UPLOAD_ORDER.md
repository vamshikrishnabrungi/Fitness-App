# Runlete Admin Studio upload bundle

Upload these files from **Admin Studio → Data imports** in this order.

## Step 1 — Exercise catalogue

Select:

- `01_exercise_catalogue.csv`

Preview it, confirm that validation passes, and commit it before Step 2.

## Step 2 — Four-week training templates

Select all nine files in the same file-picker operation:

- `02_phase_01_training_templates.json`
- `02_phase_02_training_templates.json`
- `02_phase_03_training_templates.json`
- `02_phase_04_training_templates.json`
- `02_phase_05_training_templates.json`
- `02_phase_06_training_templates.json`
- `02_phase_07_training_templates.json`
- `02_phase_08_training_templates.json`
- `02_phase_09_training_templates.json`

Do not upload the phase files individually. The backend requires all nine phases together.

## Step 3 — Sport priorities

Select:

- `03_sport_role_phase_goal_priorities.csv`

## Step 4 — Policies and fallbacks

Select all three files in the same file-picker operation:

- `04a_category_level_availability.json`
- `04b_sport_mode_and_fallback_policies.json`
- `04c_scenario_overlays.json`

## Important

- Always use **Preview** before **Commit to PostgreSQL**.
- A preview does not change runtime data.
- Do not proceed to the next step while the current step has validation errors.
- Importing these files does not publish a knowledge release or enable workout generation.
- These are upload-ready copies. Their source files remain in the original folders so generation scripts and automated tests continue to work.

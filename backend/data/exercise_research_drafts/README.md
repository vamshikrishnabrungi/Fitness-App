# Exercise Research Drafts

This folder is a staging area for parallel research outputs.

Draft files are not production database records. They must be reviewed, deduplicated, normalized, and imported through a controlled catalog builder before MongoDB ingestion.

## Current Draft Domains

- `lower_body_gym_draft.json`
- `upper_body_gym_draft.json`
- `core_carries_athletic_accessories_draft.json`

## Canonical Schema

Use:

`backend/data/exercise_schema/general_gym_exercise_taxonomy_v1.json`

## Merge Rules

- Keep source-backed, paraphrased coaching knowledge.
- Do not copy long source text.
- Do not write directly to Mongo from draft files.
- Normalize duplicate names before import.
- Separate primary exercises from variations.
- Preserve progressions, regressions, substitutions, and injury cautions.
- Every production exercise must have:
  - `id`
  - `name`
  - `base_exercise`
  - `tier`
  - `category`
  - `patterns`
  - `qualities`
  - `equipment`
  - `summary`
  - `coaching_cues`
  - `common_errors`
  - `use_when`
  - `avoid_when`
  - `source_refs`

## Production Target

After review, these drafts should become:

- `primary_exercise_library`
- `exercise_variation_library`
- `exercise_progression_graph`
- compact raw trace records in `exercise_library`


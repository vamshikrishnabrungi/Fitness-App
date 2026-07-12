# Exercise Thumbnail Plan

## Current State

- Current app-visible workout exercises covered: 45 / 45.
- Full local exercise/media requirement from Mongo: 636 unique thumbnail slugs.
- Current full coverage: 45 / 636, about 7%.
- Existing image assets live in `frontend/assets/images/exercise-thumbnails`.
- The frontend uses `ExerciseThumbnail` and the generated `exerciseThumbnailMap.ts`.

## Why Multiple Agents Help

Multiple agents help for:
- auditing database counts and slug collisions
- reviewing generated image batches
- checking thumbnails against exercise names
- preparing prompt batches

Multiple agents do not solve the image-generation bottleneck by themselves. The image tool still needs controlled batches and review because AI-generated exercise images can be technically wrong.

## Correct Pipeline

1. Query Mongo exercise collections.
2. Build canonical exercise thumbnail requirements.
3. Assign stable media keys.
4. Compare required keys to existing PNG files.
5. Generate priority batches of 6 thumbnails per contact sheet.
6. Crop contact sheets into individual PNG files.
7. Review questionable thumbnails.
8. Regenerate the frontend static `require(...)` map.
9. Run frontend typecheck/lint.

## Priority Order

1. Active workout exercises
   - Must always be 100% covered.
2. Primary exercise library
   - Main app workout generation pool.
3. Mobility drills
   - Needed for warmups, cooldowns, recovery, and injury-aware plans.
4. Specialist variations
   - Olympic lifts, advanced calisthenics, plyometrics, technical variations.
5. Raw/source exercise library leftovers
   - Keep only if they are truly usable app-facing movements.

## Key Rule

Do not generate all 600+ images blindly.

Each batch must be:
- generated from exact exercise names
- cropped into exact file names
- reviewed visually
- added to the generated TS map through `backend/exercise_thumbnail_pipeline.py`

## Long-Term Fix

Display-name lookup is acceptable only as a bridge.

Production should use:
- `exercise_id`
- `media_slug`
- alias mappings
- normalized display name fallback only as the last option

Workout generation should preserve `exercise_id` from the exercise catalog so thumbnails, coaching cues, instructions, and videos can all resolve from the same stable key.

## Files

- Pipeline script: `backend/exercise_thumbnail_pipeline.py`
- Coverage report: `backend/thumbnail_generation/coverage_report.md`
- Batch prompts: `backend/thumbnail_generation/priority_batch_prompts.md`
- Generated frontend map: `frontend/src/data/exerciseThumbnailMap.ts`
- UI component: `frontend/src/components/ExerciseThumbnail.tsx`
- Image assets: `frontend/assets/images/exercise-thumbnails`


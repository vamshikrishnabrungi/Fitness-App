# Runlete four-week exercise-reference templates

This package converts the Phase 01–09 research into exercise- and modality-based references for one-call, four-week AI workout generation.

## What these files are

Each category has references only for levels that the approved catalogue can support honestly. Most have beginner, intermediate and advanced references; five unsupported category/level combinations are recorded explicitly in `category_level_availability.json` rather than being filled with a harder or unrelated method. Every available reference contains:

- actual exercise, drill or conditioning-modality codes;
- four explicit weeks;
- weekly intent, frequency, dose, intensity and recovery;
- progression and regression gates;
- phase/schedule scenario overlays;
- source Phase template IDs; and
- safety stopping conditions.

The AI may adapt a relevant reference to the athlete's sport, position, goal, schedule, equipment and restrictions. It must use released method IDs and remain within validated dose and safety limits.

These artifacts are **research-derived candidates**, not a published production release. They must be reviewed and imported into canonical PostgreSQL knowledge tables before generator use.

## Files

- `manifest.json` — package identity, counts and file map.
- `exercise_template.schema.json` — formal JSON Schema for every template record.
- `category_coverage.json` — all covered categories and their source Phase templates.
- `category_level_availability.json` — supported and fail-closed category/level combinations with prerequisite references.
- `sport_mode_policy.json` — the sport-to-conditioning-mode contract and explicit missing-mode fallbacks.
- `retrieval_index.json` — direct category + level lookup without scanning all files.
- `source_template_reconciliation.json` — disposition for every original Phase 01–09 template family.
- `phase_01_exercise_templates.json` through `phase_09_exercise_templates.json` — 4-week references grouped by research phase.
- `scenario_overlays.json` — offseason/preseason/in-season/taper/congestion, re-entry, equipment, environment, minor, readiness, pain and missed-session changes.
- `required_catalogue_extensions.json` — drills and modalities required by the research but absent from the current 173-exercise CSV.
- `validation_report.json` — generated reconciliation results.
- `template_integrity_report.json` — level, eligibility, dose, duplicate and modality-integrity results.
- `build_exercise_templates.py` — reproducible compiler and validator input.
- `SCHEMA_AND_AI_USAGE.md` — field meanings and compact prompt assembly.

## Coverage

| Phase | Categories |
|---|---|
| 01 | Maximum strength, yielding isometrics, overcoming isometrics, eccentric capacity |
| 02 | Explosive, vertical, horizontal, lateral, rotational and upper-body power |
| 03 | Landing, extensive plyometrics, reactive/elastic strength, horizontal bounding and lateral elasticity |
| 04 | Acceleration, maximum velocity and speed endurance |
| 05 | Deceleration, planned COD and reactive agility |
| 06 | Aerobic capacity, threshold capacity and high-intensity aerobic power |
| 07 | Anaerobic power, anaerobic capacity, repeated-sprint ability and repeated-high-intensity ability |
| 08 | Local muscular endurance and calf–soleus, hamstring, adductor, shoulder, trunk, neck and grip capacity |
| 09 | Performance preparation, mobility/range capacity and recovery management |

## Catalogue status

The normalized curated CSV contains 238 canonical methods. It now includes the sprint, braking, COD, reactive-agility, running/cycling/swimming interval and recovery methods referenced by these templates. `required_catalogue_extensions.json` is retained as a lineage artifact and should be empty after a successful build. Catalogue approval does not publish a sport package; release-manifest and simulation gates still apply.

## Production gate

Do not send the entire package to the LLM. Runtime retrieval should select:

1. the athlete's relevant sport-demand summary and scoped priority-matrix row;
2. only the relevant category/level templates;
3. applicable scenario overlays;
4. eligible released methods; and
5. the athlete's normalized inputs.

For conditioning references, retrieval first filters method candidates to the sport's primary mode. Cross-training methods require an explicit athlete choice; the generator must never mix running, cycling and swimming merely because they share an energy-system label.

The model then generates one complete four-week program in one call. Backend validation rejects unknown IDs, incompatible equipment/level or mode, missing weeks, invalid dose units, exceeded bounds, schedule conflicts and safety violations.

Each record includes `prompt_reference_text`, a compact prose compilation of its four weeks. Runtime can send this paragraph instead of the complete storage object, reducing prompt tokens while preserving the actual exercise progression and dose.

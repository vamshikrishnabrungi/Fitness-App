# Schema and one-call AI usage

## Template meaning

A template is a four-week exercise-based reference for developing one physical quality. It is not a full sport program and is not copied verbatim for every athlete.

`method_options` contains the actual methods that demonstrate how the quality can be trained. It appears once per template rather than being repeated in all four weeks. `prescription_per_primary_method` provides the weekly development envelope. The generator may select a compatible released method, but it must preserve the objective, ordering and progression logic.

## Required fields

- `template_code`: stable candidate identifier.
- `phase` and `category_code`: research and quality lineage.
- `athlete_level`: beginner, intermediate or advanced.
- `source_template_ids`: exact Phase 01–09 template families used.
- `applicable_scenarios`: overlays the retrieval layer may attach.
- `method_options`: preparation, primary and supporting method candidates, including their applicable conditioning modes.
- `selection_policy`: whether selection is quality-based or requires exactly one sport-compatible modality.
- `weeks`: exactly four ordered weekly references.
- `prescription_per_primary_method`: bounded sets/series, work, intensity and recovery.
- `progression_condition` and `regression_condition`: response gates.
- `mandatory_stops`: fail-closed conditions.

## One-call generation packet

The prompt builder sends only compact relevant content:

```json
{
  "athlete": "normalized onboarding, schedule, equipment and restrictions",
  "sport_demands": "short relevant sport/position paragraph",
  "four_week_references": [
    "only categories prioritized for this athlete and their level"
  ],
  "scenario_overlays": [
    "only overlays matching phase, schedule and environment"
  ],
  "eligible_methods": [
    "released method IDs that fit equipment, level and safety"
  ],
  "request": "Generate the complete four-week program for the available days"
}
```

The full Phase reports and all 112 available references are never sent together.

The current package contains 112 available references across 39 categories, plus five explicit unavailable category/level records. Runtime
retrieval uses `sport_role_phase_goal_priority_matrix.csv` to select the small
set relevant to the athlete's sport scope, phase and goal before constructing
the one-call packet.

For a conditioning category, retrieval also applies `sport_mode_policy.json`.
Only candidates matching the selected mode are sent. Cross-training requires
explicit opt-in, and a missing mode/level combination uses its declared
prerequisite or fails closed.

## Validation after the AI response

The backend verifies:

- four weeks exist and fit the requested days;
- every exercise/drill/modality ID was supplied and released;
- equipment, environment and athlete-level requirements pass;
- dose fields use accepted units and stay inside bounds;
- speed, power and high-skill work is not placed after fatiguing work;
- external practices and competitions are counted;
- hard sessions are not inappropriately stacked;
- pain, illness, minor and environmental rules pass; and
- the program contains no invented rehabilitation or sport-technique instruction.

Failure returns structured errors. No invalid plan is saved or shown.

## Week progression

The reference convention is:

1. Week 1 — entry and baseline.
2. Week 2 — add successful exposure.
3. Week 3 — highest planned development exposure.
4. Week 4 — consolidate and reduce fatigue.

This is the default four-week shape, not a universal law. Competition/taper or re-entry overlays can reduce the progression. The model cannot turn Week 4 into another overload merely to make every week harder.

## Missing-method rule

Codes in `required_catalogue_extensions.json` are unresolved specifications,
not approved production exercises. The normalized CSV currently resolves every
template method, so this registry is expected to be empty. Any future nonempty
entry blocks publication until its canonical method and review record exist.

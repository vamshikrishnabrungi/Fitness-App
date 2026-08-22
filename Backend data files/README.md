# Runlete Backend Data Files

This folder is the canonical staging area for reviewed, structured knowledge
that can be validated and imported into PostgreSQL. The production backend does
not read these files on every request; imports create versioned database rows.

## Import order

1. `exercises/curated_exercises.csv`
2. `exercise templates/phase_*_exercise_templates.json`
3. `exercise templates/scenario_overlays.json`
4. `sport models/sport_role_phase_goal_priority_matrix.csv`

`exercise templates/manifest.json`, `retrieval_index.json`, schemas, validation
reports and reconciliation files support validation and lineage. The files in
`import templates/` are blank/operator-facing input formats, not released
content by themselves.

Only files listed by an immutable content-release manifest should become
generator-visible. Markdown files in this folder document a structured data
contract; they are not inserted as workout prose.


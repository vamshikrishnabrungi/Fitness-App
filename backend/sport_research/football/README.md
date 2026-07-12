# Football Research Workspace

This folder holds the football/soccer research pipeline for SFTC.

The research name is `football` for readability. The backend sport key should be `soccer`, because the current macro-plan service normalizes `football` to `soccer`.

## Workflow

1. Build the research map and agent briefs.
2. Create structured draft JSON files in `drafts/`.
3. Validate drafts with `validate_football_research_drafts.py`.
4. Generate `FOOTBALL_RESEARCH_DRAFT_SUMMARY.md`.
5. Convert validated drafts into app-facing records:
   - sport profile
   - roles and position profiles
   - teaching progressions
   - skill assessments
   - level transition rules
   - S&C, injury, macro-planning, and match-week rules
6. Ingest into MongoDB and test retrieval against sample profiles.

## Scope

Initial scope is association football / soccer:

- youth, school, club, amateur, college, semi-pro, and advanced competitive levels
- outfield players and goalkeepers
- beginner/intermediate/advanced teaching
- technical skill, tactical IQ, team systems, physical preparation, injury risk, and match-week planning

Later scope:

- futsal
- beach soccer
- elite opposition scouting packs
- goalkeeper-only specialist database

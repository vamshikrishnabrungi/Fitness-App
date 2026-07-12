# Cricket Sport Knowledge Research

Cricket is the first sport chosen for deep sport-IQ research.

## Files

- `CRICKET_RESEARCH_MASTER_PLAN.md`  
  Complete knowledge map: what we need to understand before creating cricket database records.

- `CRICKET_AGENT_RESEARCH_BRIEFS.md`  
  Future parallel-agent roles for batting, pace bowling, spin bowling, fielding/wicketkeeping, conditions/tactics, and S&C/injury/macro planning.

## Current Status

This is a research-planning stage, not database ingestion.

The current backend already has a small cricket planning profile, but it does not yet include the sport IQ required for a premium app:

- batting technique and tactics
- pace bowling technique and workload
- spin bowling technique and tactics
- fielding and throwing
- wicketkeeping
- pitch/weather/ball condition logic
- role-specific S&C
- match-week planning by role

## Recommended Next Step

Run the six cricket research agents from `CRICKET_AGENT_RESEARCH_BRIEFS.md` and save their drafts in:

`backend/sport_research/cricket/drafts/`

Then merge their outputs into cricket-specific backend collections.


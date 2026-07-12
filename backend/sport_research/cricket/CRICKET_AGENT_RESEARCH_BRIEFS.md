# Cricket Agent Research Briefs

## Purpose

These briefs are for future parallel research agents. Each agent should research one cricket domain deeply and output structured findings. Agents should not write final MongoDB records directly.

All agents must:

- use credible sources
- avoid influencer/clickbait content
- avoid copying long text
- paraphrase coaching and tactical knowledge
- include source URLs
- separate facts from coaching interpretation
- mark uncertainty when evidence is weak or debated

## Agent 1: Batting Skill And Tactical IQ

### Research Scope

- stance variants
- grip/backlift
- head position
- trigger movement
- front-foot and back-foot play
- shot families
- batting against pace
- batting against spin
- strike rotation
- powerplay/middle/death overs
- red-ball session batting
- left/right-hand matchups
- batting order roles
- game situation decisions

### Must Answer

1. What makes a technically stable batting setup?
2. How do batters adapt against swing, seam, bounce, pace, and spin?
3. What are common batting errors?
4. What physical qualities support batting?
5. How should a batter train differently from a bowler?
6. What tactical rules can the app store?

### Output File

`backend/sport_research/cricket/drafts/batting_skill_tactics_draft.json`

## Agent 2: Pace Bowling Skill, Workload, And Tactics

### Research Scope

- run-up rhythm
- gather/bound
- front-foot contact
- trunk mechanics
- arm path
- wrist/seam position
- release mechanics
- swing/seam/cutters/yorker/bouncer/slower ball
- new-ball and old-ball plans
- death bowling
- bowling workload
- youth/adult workload differences
- fast bowler injury risks

### Must Answer

1. What are the key phases of pace bowling?
2. What tactical tools does a pace bowler use?
3. How does pitch/weather/ball age change pace bowling strategy?
4. What physical qualities support fast bowling?
5. What workload rules should protect bowlers?
6. What gym stress should be avoided near high bowling load?

### Output File

`backend/sport_research/cricket/drafts/pace_bowling_skill_workload_draft.json`

## Agent 3: Spin Bowling Skill And Tactics

### Research Scope

- off spin
- leg spin
- left-arm orthodox
- wrist spin
- grip and release
- drift, dip, turn, bounce
- flight and pace variation
- use of crease
- stock ball and variations
- field placement logic
- bowling to left/right-hand batters
- pitch rough
- spinner physical needs

### Must Answer

1. What are the main spin bowling families?
2. What technical elements create spin, drift, dip, and control?
3. What tactical rules govern spin bowling?
4. How do pitch conditions change spin bowling?
5. What physical qualities and injury risks matter?
6. What should a spinner’s S&C support?

### Output File

`backend/sport_research/cricket/drafts/spin_bowling_skill_tactics_draft.json`

## Agent 4: Fielding, Throwing, And Wicketkeeping

### Research Scope

- catching positions
- ground fielding
- diving/sliding
- pickup and release
- overarm/sidearm/underarm throws
- throwing speed and accuracy
- throwing load
- wicketkeeping stance
- standing back/up
- footwork
- reaction and glove work
- role-specific physical demands

### Must Answer

1. What are the fielding skill families?
2. What does elite fielding require physically?
3. What makes throwing faster and safer?
4. What injury risks come from throwing volume?
5. What are wicketkeeping-specific physical demands?
6. What drills and gym qualities transfer to fielding/wicketkeeping?

### Output File

`backend/sport_research/cricket/drafts/fielding_throwing_wicketkeeping_draft.json`

## Agent 5: Pitch, Weather, Ball Condition, And Match IQ

### Research Scope

- pitch types
- ball age
- red ball vs white ball
- swing/seam/reverse swing
- spin and pitch wear
- dew
- humidity/overcast claims and uncertainty
- wind
- rain interruptions
- toss decisions
- batting first vs chasing
- match format strategy
- innings phase strategy

### Must Answer

1. How do pitch types affect batting and bowling?
2. How does weather affect ball behavior and player fatigue?
3. What does dew change?
4. How does ball age change tactics?
5. What match IQ rules should the backend store?
6. Which claims are strongly supported vs mostly coaching tradition?

### Output File

`backend/sport_research/cricket/drafts/conditions_match_iq_draft.json`

## Agent 6: Cricket S&C, Injury Risk, And Macro Planning

### Research Scope

- role-specific physical qualities
- fast bowler injury risk
- batter physical support
- spinner physical support
- wicketkeeper physical support
- fielding demands
- off-season/pre-season/in-season structure
- return-to-play
- youth vs adult progression
- tests and benchmarks
- workload monitoring
- match-week microcycles

### Must Answer

1. What physical qualities matter by role?
2. How should training change by season phase?
3. What should happen in match week?
4. What injuries must shape plans?
5. What tests and benchmarks are useful?
6. How should athlete_state update after cricket practice/matches?

### Output File

`backend/sport_research/cricket/drafts/cricket_snc_injury_macro_planning_draft.json`

## Required Draft Output Shape

Each agent should output:

```json
{
  "sport": "cricket",
  "domain": "",
  "executive_summary": "",
  "key_concepts": [],
  "technical_models": [],
  "tactical_rules": [],
  "physical_demands": [],
  "injury_or_load_risks": [],
  "training_implications": [],
  "backend_records_to_create": [],
  "open_questions": [],
  "source_refs": [
    {
      "title": "",
      "url": "",
      "source_type": "",
      "notes": ""
    }
  ]
}
```

## Merge Path

After drafts are complete:

1. Validate source quality.
2. Deduplicate repeated concepts.
3. Normalize terms.
4. Convert into cricket-specific app collections.
5. Add retrieval tests.
6. Add cricket profile generation tests.


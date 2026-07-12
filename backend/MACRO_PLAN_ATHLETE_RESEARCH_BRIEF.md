# Macro Plan Reference Research Brief

## Purpose

We need real-world references for building athletic macro plans.

The goal is not to copy any athlete's exact program. The goal is to study how high-quality training is planned across sports, then convert those patterns into backend planning rules for SFTC.

Research should answer:
- how athletes structure months of training
- how they build strength, power, speed, endurance, mobility, and skill
- how training changes around competition or match days
- how beginners progress into intermediate and advanced training
- how injuries, fatigue, travel, and season phase change the plan
- how coaches balance sport practice and gym work

The final output should become a reference document for macro-plan creation.

## Research Task

Research real athlete development cases, team training camps, strength-and-conditioning models, and sport preparation systems across multiple sports.

Use credible sources only:
- official team or federation articles
- coach interviews
- strength-and-conditioning conference notes
- published books
- research papers
- athlete interviews
- verified training camp reports
- reputable coaching education sources

Avoid:
- influencer workouts
- celebrity workout clickbait
- unsourced routines
- copied bodybuilding splits
- fake "secret workout" articles
- exact copyrighted program reproduction

We need principles, structures, and planning logic, not copied programs.

## Sports To Cover

Cover at least these categories:

1. Running and endurance sports
2. Football/soccer
3. Cricket
4. Volleyball
5. Basketball
6. Combat sports
7. Tennis or badminton
8. Olympic weightlifting
9. Track and field sprinting/jumping
10. General strength and athletic development

For each sport, include beginner, intermediate, and advanced considerations when available.

## Athlete Case Study Template

Each case study should use this structure:

```json
{
  "athlete_or_team": "",
  "sport": "",
  "level": "elite | professional | collegiate | academy | amateur | beginner-development",
  "source_refs": [
    {
      "title": "",
      "author_or_org": "",
      "url_or_book": "",
      "date": "",
      "source_type": ""
    }
  ],
  "training_context": {
    "season_phase": "off-season | pre-season | in-season | competition camp | return-to-play | general prep",
    "main_goal": "",
    "timeline": "",
    "constraints": []
  },
  "macro_structure": {
    "block_length": "",
    "block_theme": "",
    "weekly_training_frequency": "",
    "training_day_structure": "",
    "deload_or_taper_strategy": ""
  },
  "qualities_trained": [
    "strength",
    "power",
    "speed",
    "aerobic base",
    "repeat sprint ability",
    "mobility",
    "skill",
    "recovery"
  ],
  "gym_training_patterns": [],
  "field_or_court_training_patterns": [],
  "skill_training_patterns": [],
  "conditioning_patterns": [],
  "competition_week_adjustments": [],
  "progression_model": {
    "how_volume_progressed": "",
    "how_intensity_progressed": "",
    "how_exercise_complexity_progressed": "",
    "how_testing_or_benchmarks_were_used": ""
  },
  "recovery_model": {
    "sleep": "",
    "rest_days": "",
    "mobility": "",
    "soft_tissue_or_restoration": "",
    "fatigue_monitoring": ""
  },
  "injury_or_risk_management": [],
  "lessons_for_sftc": [],
  "macro_plan_rules_extracted": []
}
```

## Questions To Answer Per Sport

For every sport, answer these:

1. What physical qualities matter most?
2. How does training change across off-season, pre-season, and in-season?
3. How many gym sessions are realistic per week?
4. How many sport practice sessions are realistic per week?
5. What should happen close to match day or competition day?
6. Which qualities should not be trained hard together?
7. What common overuse or injury risks shape the plan?
8. How should beginners train differently from advanced athletes?
9. What tests or benchmarks are commonly used?
10. What progression rules can be converted into backend logic?

## Macro Plan Patterns To Extract

Extract reusable macro-plan patterns such as:

### Beginner Foundation

Used when:
- new user
- poor movement quality
- low training history
- pain or low readiness

Usually emphasizes:
- movement quality
- basic strength
- aerobic base
- mobility
- low-impact conditioning
- habit formation

### Strength Base

Used when:
- athlete needs general force production
- sport performance goal requires stronger lower body, trunk, or upper body

Usually emphasizes:
- squat/hinge/lunge/push/pull/carry patterns
- progressive overload
- controlled accessory work
- trunk stiffness
- tissue capacity

### Power Conversion

Used when:
- athlete already has enough strength base
- sport requires jumping, sprinting, throwing, striking, or explosive change of direction

Usually emphasizes:
- low-volume high-quality power work
- sprint or jump exposure
- medicine ball work
- Olympic lift derivatives when appropriate
- longer rest and lower fatigue

### Speed And Agility Block

Used when:
- field/court athlete needs acceleration, deceleration, or change of direction

Usually emphasizes:
- acceleration mechanics
- deceleration mechanics
- lateral movement
- reactive agility
- hamstring, adductor, calf capacity
- controlled exposure to high speed

### In-Season Maintenance

Used when:
- matches or competitions are frequent

Usually emphasizes:
- maintaining strength and power
- reducing soreness
- managing fatigue
- avoiding high-risk novelty
- placing heavier work far from match day

### Return To Training

Used when:
- pain, injury history, long break, or low readiness exists

Usually emphasizes:
- lower volume
- gradual impact
- regressions
- pain monitoring
- mobility and tissue capacity
- conservative progression

## Backend Rules To Derive

Research should produce rules that can later become database records.

Example rule format:

```json
{
  "id": "rule_match_day_minus_1",
  "category": "competition_week",
  "applies_to": ["field_sports", "court_sports", "cricket", "volleyball"],
  "condition": "User has match or competition within 24 hours",
  "rule": "Avoid high-volume lower-body strength, high-impact plyometrics, and exhausting conditioning.",
  "recommended_focus": ["mobility", "activation", "low-volume speed primer", "recovery"],
  "source_refs": []
}
```

## Final Research Document Format

The final document should include:

1. Executive summary
2. Sport-by-sport training demands
3. Athlete/team case studies
4. Common macro-plan patterns
5. Competition week planning rules
6. Beginner to intermediate progression references
7. Intermediate to advanced progression references
8. Injury and fatigue adjustment rules
9. SFTC backend planning rules extracted
10. Source bibliography

## Quality Bar

The document is good only if it helps us build a backend that can:
- create a logical 24-week macro plan
- generate a strong 4-week block
- adjust training based on user progress
- respect sport demands
- handle match days and competition weeks
- avoid random workouts
- avoid copying exact athlete programs
- convert real-world coaching principles into structured backend rules

## Important Instruction

Do not write a generic article about training.

Create a practical reference document for building an AI workout backend.

Every insight should connect to one of these backend needs:
- macro plan creation
- block planning
- sport-specific training
- exercise selection
- progression
- recovery
- readiness adjustment
- injury risk management
- competition week planning

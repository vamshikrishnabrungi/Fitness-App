# Cricket Research Master Plan

## Decision

Cricket is the first sport to research deeply.

Reason:

- It is highly relevant for the target user base.
- It has clear role differences: batter, fast bowler, spin bowler, all-rounder, wicketkeeper, fielder.
- It connects directly to the app's hybrid athletic concept: strength, power, speed, rotation, shoulder durability, lower-back protection, sprint ability, mobility, endurance, skill load, and tactical IQ.
- It has strong context variables: pitch, weather, ball age, dew, format, match day, bowling workload, batting order, field placement, and opposition style.

This phase is not database ingestion. This phase is knowledge mapping so that later data agents can research with precise roles and produce useful structured records.

## Current Database Gap

The current planning data has only a basic cricket profile:

- role variants
- broad weekly gym/practice frequencies
- injury risks
- broad load-management rules

Missing:

- batting technical model
- batting tactical model
- pace bowling technical model
- spin bowling technical model
- wicketkeeping demands
- fielding demands
- throwing mechanics and workload
- pitch/weather/ball-condition game IQ
- match format strategy
- role-specific S&C priorities
- age and development-stage progression
- practice planning
- competition week logic by role
- skill-to-gym transfer logic
- tests and benchmarks

## Mental Model For Cricket In SFTC

Cricket is not one sport profile. It is a role-based tactical and physical system.

The backend should understand:

```text
Cricket Plan = user role + match format + season phase + skill workload + physical goal + injury risk + pitch/weather context
```

Example:

- A fast bowler with back stiffness should not receive the same lower-body/spine workload as a batter.
- A wicketkeeper needs repeated squat positions, hip mobility, reaction speed, trunk endurance, and shoulder throwing durability.
- A top-order batter in red-ball cricket needs different tactical and physical emphasis from a T20 finisher.
- A spinner needs shoulder, trunk, hip, and finger/wrist/forearm capacity, but not the same sprint/run-up load as a fast bowler.

## Research Domains

### 1. Cricket Rules, Formats, And Match Structure

Research needs:

- Tests, ODIs, T20s, local league formats.
- Overs, innings, fielding restrictions, powerplays.
- Toss decision logic.
- Follow-on / declaration logic for long format.
- Substitution and fielding rules.
- Match interruption rules and dangerous/unreasonable conditions.
- How format changes physical and tactical demands.

Backend use:

- Format-specific macro plans.
- Match-week rules.
- Training load trimming before/after matches.
- Tactical context for batting/bowling plans.

Primary source direction:

- MCC Laws of Cricket.
- ICC playing conditions.

### 2. Batting Knowledge

Research needs:

- Stance: open, closed, side-on, balanced, trigger movements.
- Grip and backlift.
- Head position and eye line.
- Footwork: front-foot, back-foot, press, skip, shuffle.
- Shot categories:
  - defensive shots
  - drives
  - cuts
  - pulls/hooks
  - sweeps/reverse sweeps
  - lofted shots
  - rotation-of-strike shots
- Against pace:
  - new ball
  - swing
  - seam
  - short ball
  - yorker
  - slower ball
  - death overs
- Against spin:
  - reading hand/release
  - use of feet
  - sweep options
  - strike rotation
  - playing with/against spin
- Tactical batting:
  - risk management
  - scoring zones
  - game tempo
  - partnerships
  - powerplay/middle/death overs
  - red-ball session batting
- Physical transfer:
  - rotational power
  - hip-shoulder separation
  - trunk stiffness
  - bat speed
  - acceleration between wickets
  - hamstring/calf capacity

Backend use:

- Batter role profile.
- Batting-focused S&C priorities.
- Technical constraints for warm-ups and movement prep.
- Tactical IQ rules for match preparation.

### 3. Pace Bowling Knowledge

Research needs:

- Run-up rhythm and speed.
- Bound and gather.
- Back-foot contact.
- Front-foot contact.
- Trunk alignment and lateral flexion.
- Hip-shoulder separation.
- Bowling arm path.
- Wrist/seam position.
- Release mechanics.
- Follow-through.
- Ball types:
  - outswing
  - inswing
  - seam
  - scrambled seam
  - cutters
  - bouncer
  - yorker
  - slower ball
  - reverse swing
- Tactical pace bowling:
  - new ball plans
  - old ball plans
  - setting up batters
  - field placement support
  - lengths by pitch
  - death bowling
- Workload:
  - balls per session
  - overs per spell
  - weekly bowling days
  - spikes after layoff
  - youth back-stress risk
- Physical transfer:
  - lower-body strength
  - trunk stiffness
  - anti-rotation
  - hip mobility
  - hamstring/calf capacity
  - shoulder/scapular durability
  - aerobic support

Backend use:

- Fast bowler macro plan.
- Bowling load guardrails.
- Back-pain safety checks.
- Match-week gym stress rules.

### 4. Spin Bowling Knowledge

Research needs:

- Finger spin vs wrist spin.
- Off-spin, leg-spin, left-arm orthodox, left-arm wrist spin.
- Grip, wrist/finger mechanics.
- Revolutions, drift, dip, turn, bounce.
- Use of crease.
- Pace variation.
- Flight and trajectory.
- Stock ball and variations.
- Tactical spin bowling:
  - attacking vs containing spells
  - field placement
  - bowling to left/right-hand batters
  - matchups
  - pitch rough
  - defensive plans
- Physical transfer:
  - shoulder durability
  - trunk rotation and anti-rotation
  - hip mobility
  - forearm/wrist/finger capacity
  - repeatability under fatigue

Backend use:

- Spinner role profile.
- Shoulder/trunk/forearm support plans.
- Pitch-condition tactical rules.

### 5. Fielding And Throwing Knowledge

Research needs:

- Catching: high catch, flat catch, close catching, slips, boundary catching.
- Ground fielding: approach angle, long barrier, pickup, one-hand pickup.
- Throwing:
  - overarm throw
  - sidearm throw
  - relay throw
  - underarm flick
  - quick release
- Diving/sliding.
- Position-specific demands:
  - slips
  - infield
  - outfield
  - boundary riders
  - short-leg/silly point
- Physical transfer:
  - acceleration
  - deceleration
  - repeated sprint ability
  - lateral movement
  - shoulder and elbow durability
  - trunk rotation
  - grip and forearm capacity

Backend use:

- Universal cricket athletic layer.
- Fielding-focused accessories.
- Throwing load and shoulder prehab.

### 6. Wicketkeeping Knowledge

Research needs:

- Set-up stance.
- Standing back vs standing up.
- Lateral footwork.
- Glove path.
- Reaction training.
- Taking pace vs spin.
- Leg-side collection.
- Stumping mechanics.
- Dives and repeat squat positions.
- Physical transfer:
  - hip mobility
  - ankle mobility
  - trunk endurance
  - adductor capacity
  - quad endurance
  - reaction speed
  - shoulder/forearm durability

Backend use:

- Wicketkeeper role profile.
- Knee/hip/back fatigue management.
- Match-week lower-body volume adjustment.

### 7. Pitch, Weather, Ball, And Conditions IQ

Research needs:

- Pitch types:
  - green top
  - dry pitch
  - hard/bouncy pitch
  - slow/low pitch
  - turning pitch
  - cracked/worn pitch
  - damp pitch
- Ball behavior:
  - new ball swing/seam
  - old ball reverse swing
  - red ball vs white ball
  - seam deterioration
  - shine management within laws
  - wet ball/dew impact
- Weather:
  - humidity/overcast claims and what evidence supports
  - heat/dehydration/fatigue
  - wind
  - rain interruptions
  - dew in evening matches
- Tactical effects:
  - toss decision
  - bowling first vs batting first
  - spinners later in long format
  - death overs with dew
  - pace vs spin selection

Backend use:

- Match IQ layer.
- Pre-match readiness advice.
- Tactical workout/context notes.
- Future app features for match-day prep.

### 8. Cricket S&C And Injury Knowledge

Research needs:

- Fast bowler back stress injury risk.
- Hamstring injuries.
- Shoulder/throwing load.
- Side strain.
- Adductor/groin load.
- Knee/ankle demands.
- Wrist/finger load for spinners.
- Role-specific physical qualities.
- In-season vs off-season vs pre-season training.
- Youth vs adult progression.
- Workload spikes and return-to-bowling.
- Testing:
  - sprint times
  - repeated sprint ability
  - jump tests
  - throwing velocity
  - bowling workload
  - shoulder range/strength
  - trunk endurance
  - aerobic capacity

Backend use:

- Cricket macro plan.
- Athlete state.
- Role-specific injury guardrails.
- Training readiness rules.

## Future Database Collections Needed

The cricket research should eventually produce records for:

```text
sport_profiles
sport_roles
sport_skill_models
sport_technical_errors
sport_tactical_rules
sport_condition_rules
sport_training_rules
sport_workload_rules
sport_injury_rules
sport_tests_benchmarks
sport_practice_templates
sport_match_week_rules
```

## Minimum Cricket Data Model

### Role Record

```json
{
  "id": "cricket_role_fast_bowler",
  "sport": "cricket",
  "role": "fast_bowler",
  "sub_roles": ["new_ball", "death_bowler", "swing_bowler", "seam_bowler"],
  "primary_demands": [],
  "secondary_demands": [],
  "key_skills": [],
  "physical_priorities": [],
  "common_injuries": [],
  "training_conflicts": [],
  "match_week_notes": [],
  "source_refs": []
}
```

### Tactical Rule Record

```json
{
  "id": "cricket_rule_green_pitch_new_ball",
  "sport": "cricket",
  "category": "pitch_condition",
  "condition": "green or damp pitch with new ball",
  "applies_to": ["fast_bowler", "batter"],
  "rule": "",
  "batting_response": [],
  "bowling_response": [],
  "training_response": [],
  "source_refs": []
}
```

### Skill Model Record

```json
{
  "id": "cricket_skill_batting_front_foot_drive",
  "sport": "cricket",
  "skill_family": "batting",
  "skill": "front_foot_drive",
  "description": "",
  "key_positions": [],
  "coaching_cues": [],
  "common_errors": [],
  "physical_support": [],
  "progressions": [],
  "source_refs": []
}
```

### Workload Rule Record

```json
{
  "id": "cricket_workload_fast_bowler_weekly_spike",
  "sport": "cricket",
  "role": "fast_bowler",
  "category": "workload",
  "condition": "",
  "rule": "",
  "blocked_training": [],
  "recommended_adjustment": [],
  "source_refs": []
}
```

## Source Map

Use credible sources only. Priority sources:

- MCC Laws of Cricket: https://www.lords.org/mcc/about-the-laws-of-cricket
- ICC Playing Conditions: https://www.icc-cricket.com/about/cricket/rules-and-regulations/playing-conditions
- Cricket Australia Junior Pace Bowling Guidelines: https://play.cricket.com.au/community/resources/player-safety/junior-bowling-guidelines
- ECB Recreational Fast Bowling Guidance 2024: https://resources.ecb.co.uk/ecb/document/2024/06/14/292038a2-ac47-4655-bdf7-454c79d285eb/Recreational-Fast-Bowling-Guidance-2024.pdf
- NSCA Strength & Conditioning Journal, Injury Prevention Strategies in Cricket: https://journals.lww.com/nsca-scj/fulltext/2018/10000/injury_prevention_strategies_in_cricket.4.aspx
- Injuries in Cricket, PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC5958448/
- Strength and Conditioning for Cricket Fielding, Loughborough repository PDF: https://repository.lboro.ac.uk/articles/journal_contribution/Strength_and_conditioning_for_cricket_fielding_A_narrative_review/22182286/1/files/39414655.pdf
- Cricket biomechanics research profile, Stuart McErlain-Naylor: https://www.stuartmcnaylor.com/project/cricket-batting/
- ASCA review on throwing speed determinants in cricketers: https://strengthandconditioning.org/jasc-30-5/3637-a-review-of-scientific-literature-determinants-of-throwing-speed-in-elite-male-cricketers

## Quality Bar

The cricket knowledge base is useful only if it can answer:

- What type of cricket does the user play?
- What role does the user play?
- What skills does that role require?
- What physical qualities support those skills?
- What injury risks matter for that role?
- What should change before match day?
- How does bowling/throwing volume affect gym work?
- What does pitch/weather/ball condition change tactically?
- What should the athlete do differently in off-season, pre-season, in-season, and return-to-play?


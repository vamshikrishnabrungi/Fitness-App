# Kickboxing Understanding Brief

## Purpose

This brief defines kickboxing as a standalone SFTC sport knowledge domain. It should not be treated as "MMA striking" or "boxing with kicks." The backend must understand rule set, range, scoring incentives, contact level, style, technical level, and injury exposure before it can create good macro plans, skill progressions, or S&C recommendations.

The goal is not to copy a single coach's program. The goal is to build a reusable Olympic-coach-level knowledge base that lets SFTC plan for:

- beginner recreational kickboxing
- point fighting / tatami kickboxing
- full-contact kickboxing
- low-kick kickboxing
- K-1 / Glory-style kickboxing
- kickboxing used as cross-training for MMA
- fitness kickboxing users who do not spar
- athletes preparing for graded sparring, smokers, amateurs, or competition camps

## Source Orientation

Primary source families for later database records:

- WAKO rule systems and discipline structure: point fighting, light contact, kick light, full contact, low kick, K1 rules, forms.
- GLORY-style professional kickboxing rules: knockdowns, scoring, limited clinch/knee permissions, ring control, effective striking.
- Muay Thai/IFMA rules as an adjacent comparator: clinch, knees, elbows, sweeps, and traditional scoring differ enough that Muay Thai should be treated as related but not identical.
- Sport science and combat-sport injury literature: high-intensity intermittent demands, head-contact risk, hand/wrist injury, lower-limb impact, hip/adductor stress, fatigue management, and weight-making risk.

## What Kickboxing Is

Kickboxing is a striking sport built around punches and kicks, but the exact technical priorities depend on rule set.

### Rule-Set Families

#### Point Fighting

Point fighting is stop-start, distance-and-timing dominant. The athlete wins exchanges through clean scoring touches, speed, precision, entries, exits, and defensive reset. Training must emphasize:

- explosive first-step entry
- lead-leg kicking speed
- blitz-style punching entries
- distance control
- fast exits after scoring
- reaction and feint recognition
- low-contact technical sparring
- elastic lower-leg stiffness without excessive contact fatigue

Point fighting should not be trained like a 3-round K-1 fight. Long fatigue circuits, heavy low-kick conditioning, and pocket brawling are usually mismatched.

#### Light Contact

Light contact is continuous but controlled. Athletes must maintain technique, balance, volume, defense, and composure without full-power collision. Training priorities:

- continuous combination flow
- guard return after every strike
- safe contact control
- aerobic repeatability
- movement quality under moderate fatigue
- defense while striking

#### Kick Light

Kick light resembles light contact but permits low kicks in a controlled format. It adds:

- checking and low-kick defense
- leg targeting awareness
- stance discipline
- safe low-kick mechanics
- shin/foot/ankle load management

#### Full Contact

Full contact usually emphasizes above-waist kicks and punches with continuous fighting. Training priorities:

- punch-kick combinations
- body/head kick setups
- ringcraft
- scoring volume
- guard endurance
- trunk rotation and hip mobility
- conditioning for repeated high-output rounds

Because low kicks are not central, leg attrition strategies are less important than in low-kick/K-1 rule sets.

#### Low Kick

Low-kick kickboxing adds damaging legal attacks to the thigh/leg. This changes stance, defense, tactics, and physical preparation. Training priorities:

- low-kick setup and return defense
- checking mechanics
- stance width and weight distribution
- lead-leg vulnerability management
- calf/adductor/hip resilience
- shin contact tolerance progression
- avoiding excessive hard low-kick volume too early

Low-kick users with knee, shin, ankle, hip, or adductor pain need conservative exposure and technical checks before volume.

#### K-1 / Glory-Style Kickboxing

K-1-style rules blend punches, kicks, and knees, usually with limited clinching and no extended Muay Thai clinch battle. Training priorities:

- punch-to-kick and kick-to-punch combinations
- knees from brief clinch or entries
- anti-clinch posture and exits
- damage scoring and knockdown awareness
- countering kicks and punching exits
- rope/ring control
- round pacing and burst management

The athlete must learn to strike, exit, defend counters, and avoid staying square in the pocket after kicking.

#### Muay Thai Overlap

Muay Thai shares kicks and knees but differs in clinch depth, elbows, sweeps, scoring culture, stance, rhythm, and tactical incentives. SFTC can use Muay Thai as an adjacent reference for clinch/knee education, but should not label Muay Thai-specific clinch dominance as standard kickboxing unless the user selected Muay Thai or K-1 with knee/clinch rules.

## Fight Phases And Ranges

### Long Kick Range

Main actions:

- teep/front kick equivalents where legal and useful
- round kick to body/leg/head
- lead-leg probing kick
- long jab/feint to hide kick entry
- exit after kick before counter punch

Coaching priorities:

- kick without falling in
- return to stance
- eyes up after contact
- hands protect during kick
- build hip turn and pivot gradually

### Boxing Range

Main actions:

- jab, cross, hook, uppercut
- punch-to-kick combinations
- slips, rolls, parries, high guard
- exits on angle

Kickboxing difference from boxing:

- stance cannot become too bladed if low kicks are allowed
- head movement cannot drop blindly into knees/kicks
- punching entries must account for kick counters

### Pocket / Exchange Range

Main actions:

- short hooks/uppercuts
- low kicks after hand combinations
- knees in K-1 style where legal
- frame, turn, exit

Main risk:

- beginner athletes overstay in the pocket and absorb counters.

### Clinch / Tie-Up Range

Rule-dependent. In many kickboxing rules, clinch is limited or broken quickly. In K-1/Glory-style rules, short clinch knees may be allowed with restrictions. In Muay Thai, clinch is a major scoring and control domain.

Backend implication:

- the profile must know `rule_set`.
- default kickboxing should not over-prescribe long clinch systems unless rule-set or cross-training context supports it.

### Reset / Ringcraft

Good kickboxers manage:

- center vs ropes/corner
- lateral exits
- stance after attack
- opponent's power-side alignment
- round clock and score state
- recovery while looking active

## Technical Pillars

### Stance And Guard

Beginner priorities:

- balanced stance, not too square or too bladed
- hands return after every punch/kick
- chin protected
- rear heel available for rotation
- knees soft, feet under hips
- ability to move forward/back/laterally without crossing feet

Rule-set differences:

- low-kick/K-1: stance must allow checking and leg defense.
- point fighting: stance may be more bladed and bounce-oriented, but should still protect balance and exit quality.
- fitness kickboxing: stance can be simplified, but joint alignment and guard habits still matter.

### Footwork

Foundational patterns:

- step-slide forward/back
- lateral step and pivot
- angle exit after combination
- check step
- stance switch only after base movement quality
- cut-off steps for pressure fighters
- ring escape from ropes/corner

Common errors:

- crossing feet
- tall bouncing with no defensive readiness
- punching while feet are too narrow
- kicking then landing square
- retreating straight back repeatedly

### Punch Mechanics

Essential punches:

- jab
- cross
- lead hook
- rear hook
- lead uppercut
- rear uppercut
- body jab / body cross
- overhand as advanced or style-specific

Kickboxing-specific punch rules:

- never let punching posture destroy kick defense
- avoid excessive boxing head movement into kick/knee lines
- teach punch exits and angle changes early
- build shoulder endurance for guard without overloading painful shoulders

### Kick Mechanics

Core kicks:

- lead round kick
- rear round kick
- low kick where legal
- body kick
- head kick progression
- front kick / push kick style actions
- side kick primarily for point fighting or style-specific users
- spinning back kick and hook kick only after control, range, and mobility prerequisites

Key mechanics:

- pivot and hip rotation
- knee chamber where appropriate
- strike surface awareness
- hand position during kick
- recoil or safe follow-through
- return to stance
- balance after miss

### Kick Defense

Core defenses:

- check
- step-out
- pull/retract lead leg
- catch only if rule set/level supports it
- block high kick with structured guard
- counter after check or miss
- angle exit after defending body kick

Beginner must learn defense before hard sparring volume.

### Knees

Rule-dependent. For K-1-style users:

- straight knee
- switch knee
- knee from brief clinch
- knee entry after punch cover
- posture control and immediate exit

Do not prescribe extensive clinch-knee wrestling as default kickboxing unless rule-set demands it.

### Defense And Countering

Defensive layers:

- stance and distance
- guard
- parry
- slip with kickboxing-safe head position
- check
- step-back / angle
- block
- counter
- clinch/hold only if legal and appropriate

Common beginner trap: teaching counters before the athlete can keep balance and guard under basic attack.

### Combinations

Progressions:

1. single strike with stance recovery
2. two-strike hand combinations
3. hand-to-kick combinations
4. kick-to-hand combinations
5. defensive response after combination
6. exit or angle after combination
7. rule-set-specific scoring/damage combinations

Examples of logic:

- jab-cross-low kick trains hand cover into leg attack, but only for low-kick/K-1 users.
- jab-cross-lead hook-exit trains boxing range and angle exit for full-contact users.
- lead-leg side kick blitz trains point fighting distance and first score.

## Style Archetypes

### Point Fighter

Needs speed, timing, distance, explosive entry, lead-leg dexterity, feints, and fast exits. Avoid default heavy attritional low-kick programming.

### Outfighter

Uses jab, front/round kicks, lateral movement, and range control. Needs calf capacity, hip mobility, aerobic base, and ringcraft.

### Pressure Fighter

Cuts the ring, uses combinations, body attacks, low kicks, and volume. Needs trunk stiffness, neck/shoulder durability, repeat-power conditioning, and defense while entering.

### Counter Fighter

Uses defensive reads, checks, pulls, parries, and counters. Needs reaction work, timing drills, controlled sparring, and high-quality footwork.

### Kicker

Relies on round kicks, front kicks, side kicks, spinning attacks, or high kicks. Needs hip mobility, adductor capacity, hamstring control, balance, trunk rotation, and progressive contact management.

### Boxer-Kickboxer

Uses hands to set up kicks or overwhelms with boxing volume. Needs boxing mechanics, kick defense, shoulder endurance, and anti-counter exits.

### K-1 Fighter

Needs blended punch-kick-knee combinations, limited clinch awareness, damage scoring, ring control, and high-output round pacing.

## Level-Based Teaching

### Beginner

Primary objective: safe base, stance, guard, movement, single-strike mechanics, basic defense, and controlled contact.

Teach:

- stance and guard
- step-slide movement
- jab/cross
- lead/rear round kick mechanics
- basic check
- basic block
- 1-2 and 1-2-kick combinations
- return-to-stance habit
- bag/pad work with controlled intensity
- light technical sparring only when defensive habits exist

Avoid:

- hard sparring
- spinning attacks
- high-volume head kicks
- hard low-kick exchanges
- advanced clinch knees
- exhaustion-based circuits that ruin technique
- aggressive weight cutting

### Intermediate

Primary objective: link offense, defense, exits, conditioning, and rule-set tactics.

Teach:

- punch-to-kick and kick-to-punch combinations
- low-kick/check/counter chains where relevant
- angle exits
- ring control
- controlled sparring rounds
- style identification
- southpaw/orthodox basics
- rule-set-specific scoring
- conditioning rounds that preserve skill quality

### Advanced

Primary objective: opponent-specific tactics, camp planning, speed-power conversion, high-quality sparring, and competition readiness.

Teach:

- feint layers
- counter systems
- ring/corner traps
- advanced pacing
- clinch/knee entries if rule set supports
- southpaw/orthodox matchup strategy
- taper and fight-week management
- technical maintenance under fatigue
- opponent-specific game plan

## Physical Qualities

### General Demands

Kickboxing requires repeated explosive actions across intermittent rounds. Useful qualities include:

- aerobic base for recovery between exchanges and rounds
- alactic power for explosive entries/kicks
- glycolytic repeat-power tolerance for combinations
- trunk rotation and stiffness
- hip mobility and adductor capacity
- calf/ankle stiffness and footwork endurance
- shoulder/scapular endurance for guard and punching
- hand/wrist robustness
- neck awareness and contact risk management
- reactive ability and decision speed

### S&C Priorities By Rule Set

Point fighting:

- acceleration
- elastic reactivity
- lead-leg speed
- low fatigue, high speed
- reaction and agility

Full contact:

- repeat combination endurance
- trunk rotation
- shoulder endurance
- aerobic base
- ring movement conditioning

Low kick:

- adductor/hip capacity
- shin/ankle/calf exposure management
- checking mechanics
- unilateral lower-body strength
- knee-friendly loading

K-1:

- punch-kick-knee integration
- high-output rounds
- anti-clinch posture
- trunk and hip power
- repeat-power conditioning

## Injury And Load Management

### Head Contact

Any sparring or competition with head contact requires conservative progression, coaching oversight, recovery monitoring, and removal from contact with concussion symptoms. Backend should never prescribe hard sparring as default fitness work.

### Hand/Wrist

Risks:

- poor wrapping/glove fit
- punching hard before wrist alignment is stable
- high bag volume too soon

Backend rules:

- beginners use technique volume before power volume
- include wrist/forearm prep when heavy bag volume rises
- reduce bag power if wrist pain appears

### Shoulder

Risks:

- guard fatigue
- high punching volume
- overreaching hooks
- poor scapular control

Backend rules:

- shoulder pain limits hard bag/pad volume
- add scapular endurance, rotator cuff capacity, thoracic mobility
- avoid excessive overhead strength on high striking weeks

### Hip/Adductor

Risks:

- high kicks
- poor warm-up
- sudden kicking volume
- forced flexibility

Backend rules:

- progress kick height gradually
- include adductor capacity and hip mobility
- avoid high-volume head kicks for beginners

### Knee/Ankle/Shin/Foot

Risks:

- low-kick contact
- checking volume
- pivot errors
- jumping conditioning when fatigued

Backend rules:

- low-kick users need progressive contact exposure
- knee pain blocks high-volume jumping, hard low-kick sparring, and sloppy fatigue circuits
- ankle instability needs foot/ankle and calf work before high bounce volume

### Weight Cutting

For recreational users, aggressive weight cutting should not be supported. For competitive athletes, the app should flag this as coach/medical-supervised.

## Competition Week Planning

General logic:

- Heavy lower-body strength is placed far from fight day.
- Hard sparring stops early enough to recover.
- Technical sharpness stays; fatigue drops.
- Short speed/power primers can remain if the athlete tolerates them.
- Mobility, activation, pads, drilling, and tactical rehearsal dominate late week.
- Weight-making stress changes training load and recovery assumptions.

## Backend Data Domains Needed

The kickboxing database should include records across:

- `kickboxing_rules_scoring`
- `kickboxing_style_differences`
- `kickboxing_stance_guard`
- `kickboxing_footwork_ringcraft`
- `kickboxing_punch_mechanics`
- `kickboxing_kick_mechanics`
- `kickboxing_kick_defense_checks`
- `kickboxing_combinations_entries_exits`
- `kickboxing_defense_countering`
- `kickboxing_clinch_knees_rule_dependent`
- `kickboxing_sparring_contact`
- `kickboxing_strength_conditioning`
- `kickboxing_injury_load_management`
- `kickboxing_competition_week`
- `kickboxing_level_progression`

## Retrieval Implications

Profile fields that matter:

- sport = kickboxing
- rule_set: point_fighting | light_contact | kick_light | full_contact | low_kick | k1 | fitness_kickboxing | unknown
- style: point_fighter | outfighter | pressure_fighter | counter_fighter | kicker | boxer_kickboxer | k1_fighter
- stance: orthodox | southpaw | switch | unknown
- contact_level: no_sparring | technical_sparring | light_sparring | hard_sparring | competition
- competition_date
- weekly_skill_sessions
- bag/pad/sparring access
- injuries: head, hand/wrist, shoulder, hip/adductor, knee, ankle/shin/foot, low back

Default safe assumption:

- If rule set is unknown, use general kickboxing with no hard sparring, no extended clinch, no aggressive weight cut, and no high-volume low-kick contact.

## Agent Split For Deeper Research

1. Rules/style systems:
   - WAKO tatami/ring, K-1/Glory, Muay Thai overlap, scoring incentives, illegal actions, contact level.
2. Stance/footwork/ringcraft:
   - stance, guard, movement, entries/exits, ring control, ropes/corner, southpaw/orthodox.
3. Punch/kick mechanics/combinations/defense:
   - strike mechanics, kick defense/checks, punch-kick chains, countering, common errors.
4. Clinch/knees/rule-dependent tactics:
   - K-1 limited clinch, knees, anti-clinch posture, Muay Thai differences.
5. Strength-conditioning/injury/load/competition:
   - physical qualities, camp structure, sparring load, fight week, injury rules.
6. Level teaching/assessment:
   - beginner/intermediate/advanced progressions, readiness gates, skill assessments.

## Backend Rules To Extract

Example rules:

```json
{
  "id": "kickboxing_rule_unknown_ruleset_safe_default",
  "sport": "kickboxing",
  "domain": "kickboxing_rules_scoring",
  "condition": "User selects kickboxing but rule set is unknown",
  "rule": "Default to general kickboxing with stance, guard, footwork, punch-kick basics, controlled bag/pad work, and no hard sparring or extended clinch assumptions.",
  "recommended_action": ["teach stance_guard", "teach basic punch_kick", "use technical contact only"],
  "blocked_action": ["hard_sparring_default", "aggressive_weight_cut", "muay_thai_clinch_default"]
}
```

```json
{
  "id": "kickboxing_rule_knee_pain_low_kick_management",
  "sport": "kickboxing",
  "domain": "kickboxing_injury_load_management",
  "condition": "User has knee pain and selected low kick or K1 style",
  "rule": "Reduce low-kick contact volume, avoid fatigue-based jumping circuits, teach pivot/check mechanics carefully, and prioritize hip, calf, adductor, and knee-control capacity.",
  "recommended_action": ["technical_low_kick_drills", "adductor_capacity", "calf_soleus_capacity", "knee_friendly_conditioning"],
  "blocked_action": ["hard_low_kick_sparring", "high_volume_plyometrics", "sloppy_fatigue_circuits"]
}
```

## Source References For Research

- WAKO official rules and discipline structure: https://www.wako.sport/rules/
- WAKO official organization and kickboxing disciplines: https://www.wako.sport/
- GLORY official rules: https://glorykickboxing.com/rules
- IFMA official Muay Thai rules context: https://muaythai.sport/
- Combat sport injury and physiology literature should be added to source refs during database conversion where specific records use those claims.

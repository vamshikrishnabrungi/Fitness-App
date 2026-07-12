# MMA Understanding Brief

## Purpose

This brief defines MMA for the SFTC backend before deeper draft conversion. MMA should not be treated as boxing with takedowns added. It is a hybrid combat sport where success depends on connecting striking, wrestling, clinch/cage control, ground control, submissions, ground-and-pound, tactical decision-making, and contact/load management.

## Core Game Model

MMA has four main fight phases:

- **Open-space striking:** stance, guard, range, entries, exits, kicks, boxing combinations, feints, checks, counters, and cage positioning.
- **Clinch and cage wrestling:** underhooks, head position, hand fighting, body locks, trips, mat returns, wall walks, pummeling, knees, dirty boxing, and breakaways.
- **Ground control and submission grappling:** top control, guard, half guard, side control, mount, back control, submissions, submission defense, sweeps, escapes, and ground-and-pound safety.
- **Transitions:** strike-to-takedown, takedown-to-control, control-to-ground-and-pound, scramble-to-stand, submission-to-position, and cage-get-up sequences.

The app must train MMA as phase connection, not isolated martial arts. A user can be advanced in boxing but beginner in cage wrestling. Level should be domain-specific.

## Scoring And Tactical Meaning

Modern MMA scoring prioritizes effective striking/grappling first. Effective aggression and fighting area control are backup criteria only when effective striking/grappling is even. For coaching, that means SFTC should reward actions that create real effect: clean strikes, damaging or position-improving grappling, legitimate submission threats, established takedown attacks, dominant control that enables attack, and phase transitions that improve winning chances.

Backend implication:

- Do not overvalue passive top position or cage pressure without attack.
- Teach beginners to connect position to safe offense or escape, not to stall.
- Teach intermediates to win exchanges with meaningful exits and follow-up options.
- Teach advanced athletes to choose actions by opponent style, score state, round time, and fatigue.

## Training Priorities By Level

### Beginner

Prioritize:

- stance, guard, balance, safe falling, and basic movement
- jab/cross, low kick basics, checking, simple defense, and exiting
- wrestling stance, level change, penetration step, sprawl, wall-walk basics
- positional hierarchy: guard, half guard, side control, mount, back
- tap culture, partner safety, no ego sparring
- aerobic base, basic strength, trunk control, neck preparation, shoulder/hip mobility

Avoid:

- hard sparring
- uncontrolled takedowns
- heel hooks and high-risk submissions
- high-volume head contact
- fight-camp conditioning for unprepared users

### Intermediate

Prioritize:

- entries that combine strikes and takedowns
- cage wrestling, clinch pummeling, mat returns, and wall escapes
- controlled sparring with themes and constraints
- defense-to-counter, strike-to-shot, shot-to-control, control-to-strike
- positional sparring, scramble decision-making, and controlled ground-and-pound mechanics
- repeat-power conditioning by round demand

Avoid:

- stacking hard sparring with heavy lower-body or neck work
- adding advanced submissions before escape/control competence
- turning all conditioning into exhausted skill rounds

### Advanced

Prioritize:

- opponent-specific fight planning
- style matchup work: striker vs grappler, wrestler vs submission threat, pressure vs counter striker
- camp phase planning, contact taper, round simulation, score-state tactics
- high-quality power/speed work with fatigue control
- recovery monitoring, concussion symptom rules, weight-cut risk management

Avoid:

- novelty close to competition
- high contact during poor readiness or symptom periods
- unplanned volume spikes in wrestling, sparring, or hard grappling

## Physical Qualities

MMA needs:

- aerobic base for recovery between exchanges and rounds
- anaerobic repeat power for flurries, scrambles, shots, mat returns, and ground-and-pound
- maximal and relative strength for clinch, grappling, and positional control
- rotational power for striking and takedown entries
- trunk stiffness and anti-rotation for striking, clinch, and scrambling
- neck strength and control, but never fatigued before contact
- shoulder/scapular durability for punching, frames, posting, pummeling, and grappling
- grip and upper-back endurance for clinch, wrist control, and grappling
- hip mobility and adductor capacity for kicks, sprawls, guard, and shots
- calf/ankle/knee capacity for footwork and level changes

## Injury And Safety Risks

Main risks:

- head trauma, concussion symptoms, cuts, and facial injury
- hand/wrist injury from striking
- shoulder/elbow/wrist stress from grappling, posting, frames, and submissions
- neck stress from grappling and contact
- rib/trunk stress from body shots, clinch, and rotation
- knee/ankle/adductor strain from shots, sprawls, kicks, and scrambles
- overtraining from stacking skill sessions, sparring, grappling, and S&C
- dehydration/weight-cut stress for competitive users

Backend safety rule:

- Any headache, dizziness, visual symptoms, confusion, neurological symptoms, worsening head/neck symptoms, or suspected concussion blocks contact escalation.
- Hard sparring, hard wrestling, and heavy neck work should not be stacked.
- Skill quality should be protected before fatigue, especially for beginners.

## MMA Backend Domains

Use these retrieval domains:

- `mma_rules_scoring`
- `mma_fight_iq`
- `mma_range_management`
- `mma_stance_guard`
- `mma_striking_entries`
- `mma_kicking`
- `mma_striking_defense`
- `mma_clinch_cage`
- `mma_wrestling`
- `mma_takedown_entries`
- `mma_takedown_defense`
- `mma_ground_control`
- `mma_submissions`
- `mma_escapes_scrambles`
- `mma_ground_and_pound`
- `mma_strength_conditioning`
- `mma_sparring_contact`
- `mma_fight_camp`
- `mma_injury_load_management`
- `mma_level_progression`

## Agent Split

The deeper research should be divided into:

- Rules, scoring, fight phases, and tactical IQ.
- MMA striking and kickboxing/Muay Thai adaptation.
- Wrestling, cage wrestling, clinch, takedown offense/defense.
- Submission grappling, ground control, escapes, and ground-and-pound.
- Strength and conditioning, fight-camp periodization, return-to-contact, and injury management.
- Level progression and assessment rules across beginner, intermediate, and advanced users.

## Key Sources

- ABC Unified Rules and MMA judging criteria: https://www.abcboxing.com/wp-content/uploads/2024/07/unified-mma-rules-rev-july-2024.pdf
- UFC Unified Rules: https://www.ufc.com/unified-rules-mixed-martial-arts
- IMMAF amateur MMA rules: https://immaf.org/wp-content/uploads/2022/10/IMMAF-Rules-Document-as-of-Oct-2022.pdf
- USA Wrestling Core Curriculum: https://www.usawmembership.com/usa_wrestling_core_curriculum
- USA Wrestling Athlete Development Model: https://content.themat.com/CoachesCorner/LTADPoster.pdf
- IBJJF rules resources: https://ibjjf.com/books-videos
- ADCC rules: https://adcombat.com/adcc-rules-regulations/
- MMA physiological profile review: https://pmc.ncbi.nlm.nih.gov/articles/PMC6628448/
- MMA training load distribution: https://pmc.ncbi.nlm.nih.gov/articles/PMC8109772/
- MMA injury systematic review: https://pubmed.ncbi.nlm.nih.gov/29347856/

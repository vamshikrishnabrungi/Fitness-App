# Tennis Sport Understanding Brief

## Purpose

This is the pre-agent understanding pass for tennis. It defines what tennis knowledge the backend needs before creating focused research agents or app-facing records.

The goal is not to collect random tennis tips. The goal is to understand the game deeply enough to assign the right research roles and later build a database that can support:

- macro plan creation
- 4-week block generation
- technical skill teaching
- tactical sport IQ
- surface and match-context adjustments
- S&C and injury/load management
- beginner, intermediate, and advanced progression

## Source Base Used For This Pass

- ITF tennis rules and governance resources.
- ITF Tennis Play and Stay / Tennis10s model for beginner and youth progression.
- USTA Player Development and American Development Model material.
- USTA high-performance technique material.
- Peer-reviewed tennis injury epidemiology reviews.
- Peer-reviewed match-play intensity and physical-demand reviews.
- Peer-reviewed serve biomechanics and kinetic-chain research.
- Peer-reviewed court-surface match-analysis research.

## Core Game Model

Tennis is a racket sport played as singles or doubles. The point starts with the serve and immediately becomes a serve-return contest, then a rally contest. The game is not only stroke production; it is a repeating loop:

1. Serve or receive.
2. Read ball, opponent, court position, score, and surface.
3. Move to the ball.
4. Create or neutralize advantage through contact quality.
5. Recover to the next high-probability court position.
6. Repeat until forced error, winner, tactical error, or physical breakdown.

For the backend, tennis should be modeled as:

- first-strike sport: serve, return, and plus-one ball matter heavily
- open-skill sport: every shot depends on ball height, speed, spin, location, court position, and opponent location
- repeated acceleration/deceleration sport
- rotational power and shoulder/elbow/wrist-load sport
- surface-sensitive sport
- match-score-pressure sport
- tournament-density sport

## Main Skill Families

### Stroke Mechanics

The stroke database should separate:

- ready position and unit turn
- grip choice and grip changes
- forehand
- one-handed backhand
- two-handed backhand
- slice backhand
- serve
- return of serve
- volley
- overhead smash
- drop shot
- lob
- half-volley
- passing shot
- approach shot

Each stroke should store:

- tactical purpose
- preferred contact zone
- stance options
- kinetic-chain model
- common errors
- coaching cues
- beginner teaching progression
- intermediate pressure progression
- advanced tactical variation
- load-risk flags
- assessment signals

The serve must be treated separately because it has its own load profile and technical model: toss, rhythm, leg drive, trunk rotation, shoulder external/internal rotation, racket drop, contact, pronation, landing, and recovery.

### Footwork And Court Movement

Movement is not generic agility. Tennis requires:

- split-step timing
- first step
- crossover recovery
- lateral shuffle
- adjustment steps
- open stance, neutral stance, closed stance, and semi-open stance setup
- approach movement
- recovery after wide ball
- recovery after serve
- net transition
- doubles positioning movement
- surface-specific movement

Court coverage differs by:

- singles vs doubles
- baseline vs net
- defensive vs neutral vs attacking state
- clay vs hard vs grass
- right-handed vs left-handed opponent
- player style

### Tactics And Sport IQ

Tennis tactics should be stored by situation, not only by shot:

- serve plus-one pattern
- return plus-one pattern
- crosscourt rally tolerance
- change direction down the line
- attack short ball
- defend high/deep
- use height/depth/spin to reset
- approach and volley
- pass or lob against net player
- target backhand or weaker wing
- exploit movement weakness
- protect own weakness
- handle break point / game point / tiebreak pressure

Doubles needs separate tactical records:

- serve placement and poaching
- return direction
- first volley
- net player positioning
- I-formation
- Australian formation
- two-back defense
- lob over net player
- middle ball responsibility
- communication rules

### Surface Intelligence

Tennis plans should change by surface:

- Clay: higher bounce, more sliding, longer movement demands, more tolerance and point construction, but first-strike tennis still matters.
- Grass: lower/skidding bounce, shorter reaction time, serve/return and net skills become more important.
- Hard court: balanced but higher impact; deceleration, repeated change of direction, and tendon/joint load matter.

Surface should affect:

- conditioning type
- footwork teaching
- tactical emphasis
- injury/load risk
- match-week preparation

## Physical Demands

Tennis requires:

- repeated short accelerations
- braking and change of direction
- lateral movement and recovery
- rotational power
- trunk stiffness and rotation control
- shoulder/scapular durability
- forearm/elbow/wrist capacity
- calf/Achilles/ankle capacity
- hip/knee deceleration control
- aerobic base for between-point and between-match recovery
- anaerobic repeat-effort ability

Backend should not treat tennis conditioning as random HIIT. Conditioning must match rally/rest rhythm, movement direction, surface, and tournament density.

## Injury And Load Model

Tennis load should be tracked by channels:

- serve count
- high-intent serve count
- forehand volume
- backhand volume
- overhead/smash volume
- wide-ball deceleration count
- change-of-direction density
- sliding exposure
- match duration
- tournament match density
- hitting-session duration
- gym upper-body load
- gym lower-body load
- next-day shoulder/elbow/wrist/back/knee/ankle response

Common risk areas:

- shoulder
- elbow
- wrist
- lumbar spine
- hip/groin
- knee
- ankle
- calf/Achilles

Planning implication: a user with elbow pain should not receive high-volume serve, heavy topspin, or maximal forehand work without grip/forearm/shoulder/trunk support and load caps. A user with low-back pain needs trunk/hip control and serve/rotation volume management. A user with knee/ankle/Achilles pain needs deceleration, surface, and jump/landing exposure managed.

## Beginner, Intermediate, Advanced Model

### Beginner

Needs:

- rally success
- safe movement
- basic grips
- simple forehand/backhand contact
- beginner serve action
- cooperative rally patterns
- basic scoring
- no pain spikes

Avoid:

- extreme technical detail too early
- high-volume serving
- hard court movement fatigue before movement quality
- tactical complexity before ball control

### Intermediate

Needs:

- reliable serve and return
- tactical rally patterns
- crosscourt consistency
- controlled change of direction
- approach and net options
- surface adjustments
- S&C support for rotation, deceleration, shoulder, elbow, trunk, and lower limb

Avoid:

- overloading serve + forehand + heavy gym upper body in the same week
- random conditioning unrelated to court patterns
- adding advanced tactics without stable shot tolerance

### Advanced

Needs:

- opponent-specific planning
- serve-location plus-one patterns
- return pattern selection
- score-state plans
- surface-specific tactics
- tournament-week load control
- match-density recovery
- technical refinement under pressure

Avoid:

- new tactical experiments in competition week
- ignoring accumulated serve/shoulder/elbow load
- high novelty when match density is high

## What The Database Must Eventually Store

### Sport Profile

One app-facing tennis sport profile with:

- sport summary
- physical qualities
- tactical qualities
- common injury risks
- weekly training frequency by level
- surface-specific planning rules
- competition-week rules

### Role / Style Records

Tennis has no fixed positions like cricket or volleyball, but it does have player styles and match contexts:

- aggressive baseliner
- counterpuncher
- all-court player
- serve-and-volley player
- big server
- defensive retriever
- doubles net player
- doubles baseline player
- left-handed player
- one-handed backhand player
- two-handed backhand player

### Teaching Progressions

Progressions should exist for:

- forehand
- backhand
- serve
- return
- volley
- overhead
- slice
- footwork and recovery
- baseline tactics
- net transition
- doubles tactics
- surface adaptation

### Skill Assessments

Assessment records should cover:

- contact quality
- rally tolerance
- serve consistency
- return quality
- depth/height control
- directional control
- recovery footwork
- movement quality under fatigue
- score-state decision making
- doubles communication
- pain/load response

### Planning Rules

Planning rules should cover:

- serve volume gate
- elbow/shoulder/back pain gate
- hard-court impact gate
- clay movement/load gate
- grass low-bounce reaction gate
- match day minus one
- tournament-day between-match adjustment
- beginner ball-control-before-tactics rule
- intermediate first-strike development rule
- advanced opponent-specific block rule

## Correct Agent Split After This Understanding Pass

The initial four-agent split was too generic. Tennis needs a more precise split:

1. **Stroke Mechanics Agent**
   - forehand, backhand, serve, return, volley, overhead, slice, grips, contact, common errors, teaching progressions, stroke-load risks

2. **Movement And Surface Agent**
   - split-step, first step, recovery, stance movement, approach, net transition, baseline coverage, clay/hard/grass movement and load differences

3. **Tactics And Match IQ Agent**
   - singles patterns, serve plus-one, return plus-one, score pressure, tiebreak/break point logic, opponent scouting, doubles formations

4. **Injury/S&C/Load Agent**
   - serve count, elbow/shoulder/wrist/back/lower-limb risks, S&C qualities, readiness, return to tennis, tournament load

5. **Doubles-Specific Agent**
   - communication, court roles, serve/return formations, poaching, I-formation, Australian formation, middle-ball rules, two-back defense

6. **Beginner-To-Advanced Teaching Agent**
   - level-specific skill gates, red/orange/green/yellow ball progression, adult beginner progression, assessment criteria, promotion/hold rules

This means tennis should use six research agents, not four, because doubles and level-based teaching need their own depth.

## Immediate Next Step

Do not create tennis database records yet.

First create six deep research drafts from the agent split above, validate them, then convert them into app-facing records.

## Source Links

- ITF Coaching: https://www.itftennis.com/en/growing-the-game/coaching/
- ITF Tennis Play and Stay: https://www.itftennis.com/en/growing-the-game/itf-tennis-play-and-stay/
- ITF Rules and regulations portal: https://www.itftennis.com/en/about-us/governance/rules-and-regulations/
- USTA American Development Model: https://www.usta.com/en/home/play/american-development-model.html
- USTA player development: https://www.playerdevelopment.usta.com/About-USTA/Player-Development/understanding_and_influencing_the_road_to_success/
- USTA high-performance technique: https://www.playerdevelopment.usta.com/high_performance_technique/
- Tennis injury epidemiology review: https://pmc.ncbi.nlm.nih.gov/articles/PMC5825333/
- Tennis match-play intensity review: https://pmc.ncbi.nlm.nih.gov/articles/PMC2653872/
- Tennis serve kinetic-chain framework: https://pmc.ncbi.nlm.nih.gov/articles/PMC13095676/
- Women's tennis surface match analysis: https://www.mdpi.com/1660-4601/19/13/7955
- Junior tennis match/training demands review: https://e-space.mmu.ac.uk/630650/1/The%20demands%20of%20training%20and%20match-play%20on%20elite%20and%20highly%20trained%20junior%20tennis%20players%20-%20A%20systematic%20review.pdf

# Cycling Sport Understanding Brief

## Purpose

This is the pre-agent understanding pass for cycling. It defines what cycling knowledge the backend needs before creating focused research agents or app-facing records.

The goal is not to collect random cycling tips. The goal is to understand cycling deeply enough to assign the right research roles and later build a database that can support:

- macro plan creation
- 4-week block generation
- technical skill teaching
- discipline-specific training
- endurance and power-zone planning
- tactics and sport IQ
- bike-fit, safety, and injury/load management
- beginner, intermediate, and advanced progression

## Source Base Used For This Pass

- UCI discipline and competition resources.
- USA Cycling rules, coach education, and rider-development resources.
- British Cycling coaching and rider knowledge resources.
- Cycling training literature on endurance intensity distribution, power profiling, FTP/threshold, cadence, sprinting, climbing, and tapering.
- Peer-reviewed cycling injury and bike-fit literature covering knee, low-back, neck/shoulder, hand/wrist, saddle, Achilles/calf, and crash-risk issues.
- Triathlon and endurance-coaching literature where cycling is trained as one part of a multi-sport system.

## Core Game Model

Cycling is not just cardio on a bike. It is an equipment-mediated endurance, power, handling, and tactical sport. The backend should model cycling as a repeated loop:

1. Choose terrain, route, discipline, and ride goal.
2. Manage position, balance, cadence, gearing, and braking.
3. Produce power at the right intensity for the event or training session.
4. Respond to terrain, wind, group dynamics, surface, traffic, and fatigue.
5. Fuel and hydrate enough to sustain output.
6. Recover and progress without overuse injury or excessive fatigue.

For the backend, cycling should be modeled as:

- endurance sport with power-zone and heart-rate-zone logic
- skill sport requiring bike handling, braking, cornering, descending, and group riding
- equipment-fit sport where saddle, reach, cleats, handlebar position, and bike setup influence injury risk
- terrain-sensitive sport where flats, climbs, descents, wind, and surfaces change demands
- discipline-specific sport with road, criterium, time trial, track, MTB, gravel, cyclocross, BMX, and triathlon cycling needs
- fueling-sensitive sport where under-fueling often ruins session quality and recovery
- crash-risk sport where safety and progression matter

## Main Discipline Families

### Road Cycling

Road cycling requires aerobic base, tempo durability, threshold power, climbing ability, sprint/attack capacity, descending skill, pack positioning, drafting, paceline work, and race tactics.

Sub-contexts:

- recreational road riding
- endurance rides
- sportive/gran fondo
- road racing
- criterium racing
- time trial
- hill climb

Backend implication: a road cyclist's plan should not be only long rides. It should blend endurance, threshold, VO2max, sprint/neuromuscular work, handling, group-riding skills, and recovery.

### Mountain Bike

Mountain biking adds technical terrain demands: body position, braking control, line choice, traction, climbing on loose surfaces, descending, cornering, drop/obstacle management, repeated accelerations, and upper-body/trunk fatigue.

Sub-contexts:

- cross-country
- trail
- enduro
- downhill

Backend implication: MTB riders need technical skill blocks and strength work for trunk, grip, shoulders, hips, legs, repeated accelerations, and crash resilience.

### Gravel And Cyclocross

Gravel blends endurance with surface variability, pacing, nutrition, equipment choices, and long-duration fatigue. Cyclocross adds repeated dismounts/remounts, carrying, short explosive efforts, cornering, mud/sand handling, and race-pace surges.

Backend implication: surface handling, traction, run-ups, repeated anaerobic efforts, and equipment decisions matter more than generic endurance.

### Track Cycling

Track cycling is highly discipline-specific:

- sprint events need maximal power, acceleration, cadence, starts, tactical sprinting, and long rests.
- endurance track events need high-speed aerobic/anaerobic power, bunch tactics, positioning, and repeated surges.

Backend implication: track cycling should not be programmed like outdoor road endurance. It needs event-specific power and skill.

### BMX

BMX racing demands start-gate acceleration, pump/terrain rhythm, sprint power, cornering, jumping, landing, and crash-risk management.

Backend implication: BMX is closer to sprint-power and technical skill than long endurance.

### Triathlon Cycling

Triathlon cycling requires steady power, aerodynamic position tolerance, pacing discipline, fueling, and the ability to run after cycling. It must be integrated with swim and run stress.

Backend implication: the cycling block cannot be planned alone for triathletes. It must respect run-leg fatigue and total weekly endurance load.

## Key Skill Families

### Bike Handling

The database should separate:

- balance and relaxed upper body
- mounting/dismounting
- braking technique
- cornering
- descending
- climbing technique
- shifting/gearing
- cadence control
- looking ahead and scanning
- one-hand control and signaling
- obstacle avoidance
- riding in a straight line
- group riding
- drafting and paceline
- standing climbing and seated climbing
- wet-road and loose-surface handling

Each skill should store:

- tactical or safety purpose
- beginner teaching progression
- common errors
- coaching cues
- risk flags
- assessment signals
- when to progress
- when to regress

### Power And Endurance Training

Cycling training should use multiple intensity anchors:

- RPE
- heart rate
- power
- FTP/threshold
- cadence
- terrain
- duration
- recovery response

The backend should support:

- easy endurance rides
- long aerobic rides
- tempo intervals
- sweet-spot / sub-threshold work
- threshold intervals
- VO2max intervals
- anaerobic capacity intervals
- sprint / neuromuscular work
- climbing repeats
- cadence drills
- recovery rides
- race simulations
- taper sessions

The system should avoid throwing high-intensity intervals at beginners before they have bike handling, saddle tolerance, aerobic habit, and recovery capacity.

### Tactics And Sport IQ

Cycling tactics should be stored by discipline and situation:

- drafting and sheltering from wind
- paceline rotation
- positioning before corners/climbs/sprints
- when to attack
- when to follow
- bridging
- sprint lead-out basics
- climbing pacing
- descending risk management
- time-trial pacing
- criterium cornering and positioning
- MTB line choice and traction
- cyclocross dismount/remount timing
- triathlon pacing and fueling

Tactics depend heavily on rider level. Beginners need safety and predictable handling. Advanced riders need race craft, energy conservation, and terrain-specific decisions.

## Physical Demands

Cycling requires:

- aerobic base
- muscular endurance
- threshold power
- VO2max capacity
- sprint power
- cadence control
- hip/knee/ankle repetitive-force tolerance
- trunk endurance
- neck/shoulder/upper-back postural tolerance
- grip and hand comfort
- hip mobility and posterior-chain support
- off-bike strength for force production and injury resilience
- fueling and hydration skills

Backend should not treat cycling conditioning as random HIIT. Conditioning must match the user's discipline, terrain, training age, available bike/trainer, and injury context.

## Injury, Safety, And Load Model

Cycling load should be tracked by channels:

- weekly ride frequency
- weekly ride duration
- long ride duration
- time in zone
- high-intensity interval count
- sprint count
- climbing volume
- seated vs standing climbing exposure
- indoor trainer time
- cadence extremes
- bike-fit changes
- crash/fall events
- next-day knee, low-back, neck, shoulder, hand, saddle, calf, Achilles response
- fueling/hydration quality
- sleep and fatigue response

Common risk areas:

- anterior knee
- lateral knee / IT band region
- low back
- neck and shoulders
- hands/wrists numbness or pressure
- saddle/perineal discomfort
- Achilles/calf
- hip flexor irritation
- crash-related shoulder, wrist, collarbone, hip, and head injuries

Planning implications:

- Knee discomfort should trigger cadence, gearing, saddle/cleat/bike-fit review, reduced big-gear low-cadence climbing, and lower intensity until symptoms stabilize.
- Low-back discomfort should trigger bike-position review, trunk/hip endurance work, reduced aggressive aero posture, and progression of ride duration.
- Hand or neck symptoms should trigger reach/handlebar/contact-point review and upper-back/scapular endurance work.
- Beginners need traffic-safe routes, bike checks, braking skill, cornering skill, and group-riding safety before high-speed or pack-riding demands.

## Beginner, Intermediate, Advanced Model

### Beginner

Needs:

- safety habits
- helmet and bike check routine
- starting/stopping
- braking
- shifting/gearing
- cadence awareness
- easy aerobic ride habit
- saddle tolerance
- route selection
- simple fueling and hydration
- no pain spikes

Avoid:

- maximal sprints
- heavy interval density
- technical descents
- fast group rides
- big-gear grinding
- long rides that exceed saddle/neck/back tolerance

### Intermediate

Needs:

- structured endurance and intensity
- threshold/tempo work
- cadence drills
- climbing technique
- longer rides
- basic group riding
- discipline-specific skill
- off-bike S&C for trunk, hips, lower limb, neck/shoulder, and posture
- basic fueling targets

Avoid:

- stacking threshold, VO2, sprints, long rides, and heavy lower-body gym work without recovery
- race-like group rides before handling readiness
- ignoring bike-fit signals

### Advanced

Needs:

- event-specific power development
- periodized blocks
- disciplined intensity distribution
- high-quality interval targeting
- race-tactical sessions
- terrain-specific simulation
- tapering
- power-profile benchmarking
- detailed fueling, hydration, and recovery

Avoid:

- generic endurance volume with no event-specific transfer
- too much middle intensity
- excessive high-intensity density
- sudden bike-fit or equipment changes near competition

## Macro Plan Logic

Cycling macro plans should be built from:

- rider level
- discipline
- event distance and terrain
- available bike/trainer
- weekly ride days
- current endurance base
- power/HR/RPE data availability
- injury/pain signals
- route/traffic constraints
- weather/season constraints
- sport combination if multi-sport

Reusable block patterns:

### Learn To Ride / Confidence Foundation

Used for new riders or anxious riders.

Emphasis:

- safety
- braking
- turning
- shifting
- short easy rides
- flat traffic-free routes
- basic mobility and trunk support

### Aerobic Base

Used for most road, gravel, MTB, triathlon, and fitness cyclists.

Emphasis:

- easy endurance
- long-ride progression
- cadence comfort
- saddle tolerance
- fueling practice
- low soreness off-bike strength

### Threshold / FTP Build

Used once base and recovery are adequate.

Emphasis:

- tempo and threshold intervals
- sustainable power
- pacing
- controlled progression
- no excessive high-intensity density

### VO2 / Climbing Development

Used for hill, road racing, MTB XC, and riders needing repeated hard efforts.

Emphasis:

- VO2 intervals
- climbing repeats
- short surges
- trunk/hip support
- careful recovery

### Sprint / Neuromuscular Power

Used for track, criterium, BMX, sprint finish, and power goals.

Emphasis:

- low-volume high-quality sprints
- long rests
- cadence and gear choice
- gym power
- no fatigue-based sprint technique

### Race-Specific / Discipline Peak

Used near events.

Emphasis:

- event simulation
- terrain/tactic rehearsal
- fueling rehearsal
- taper
- reduced novelty
- maintaining freshness

### Return To Ride

Used after injury, illness, crash, or long break.

Emphasis:

- lower volume
- easy intensity
- pain monitoring
- fit review
- gradual ride duration
- conservative progression

## Agent Split For Deep Research

Cycling is broad enough that one agent would produce shallow data. Use these agents:

1. **Endurance And Power Programming Agent**
   - Training zones, FTP/threshold, HR/RPE, cadence, base/build/VO2/sprint blocks, long rides, tapering, indoor trainer use, and progression rules.

2. **Bike Handling And Safety Agent**
   - Braking, cornering, descending, climbing technique, shifting, cadence skill, road awareness, group riding, bike checks, wet/loose-surface skills, and beginner safety.

3. **Discipline And Tactics Agent**
   - Road, criterium, time trial, track, MTB, gravel, cyclocross, BMX, triathlon cycling, drafting, paceline, attacks, lead-outs, terrain, wind, route and race context.

4. **S&C, Injury, Bike Fit, And Load Agent**
   - Common cycling injuries, bike-fit links, strength training, mobility, trunk/hip/postural support, pain rules, return-to-ride logic, and load monitoring.

5. **Beginner, Fitness, And Commuter Cycling Agent**
   - Learn-to-ride, general fitness, weight loss, commuting safety, confidence, habit formation, indoor cycling, older adults, and low-equipment options.

6. **Level Assessment And Progression Agent**
   - Beginner/intermediate/advanced readiness, FTP/HR/RPE benchmarks, handling-skill assessment, group-ride readiness, race-readiness, level promotion, hold, and regression rules.

## Required App-Facing Output Later

The final cycling database should support these record families:

- `sport_profiles`
- `sport_roles` / `discipline_profiles`
- `sport_skill_models`
- `sport_teaching_progressions`
- `sport_tactical_rules`
- `sport_training_rules`
- `sport_injury_load_rules`
- `sport_skill_assessments`
- `sport_level_transition_rules`
- `macro_plan_templates`
- `planning_rules`

The records should be compact enough for retrieval but specific enough that the AI can generate cycling plans that are not generic cardio workouts.

## Backend Quality Bar

Cycling records are acceptable only if they help the backend answer:

- What kind of cyclist is this user?
- What terrain, discipline, and event context matter?
- What physical qualities should be trained now?
- What technical skills should be taught now?
- What bike-fit or safety risks should change the plan?
- How should weekly ride duration, intensity, and long rides progress?
- When should threshold, VO2, sprint, and climbing work be introduced?
- What should be avoided near competition?
- How does cycling training interact with gym work and other sports?
- What evidence should move the user from beginner to intermediate or advanced?


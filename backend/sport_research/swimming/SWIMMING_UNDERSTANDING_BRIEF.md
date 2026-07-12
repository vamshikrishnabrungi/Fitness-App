# Swimming Understanding Brief

## Purpose

This brief defines the swimming knowledge model before any deep-research agents create app-facing data.

Swimming is not only endurance training. For SFTC, it needs to be modeled as a technical water sport with event-specific energy systems, stroke mechanics, breathing skill, starts, turns, pacing, dryland support, shoulder and spine load management, and beginner safety rules.

The backend should not treat a swimmer the same way as a runner. Water changes impact, breathing, propulsion, drag, fatigue expression, and injury risk.

## Game And Event Model

Swimming performance is determined by:

- propulsion: how effectively the athlete creates force against water
- drag reduction: body position, streamline, balance, alignment, and rotation
- breathing control: timing, rhythm, exhalation, anxiety control, and stroke disruption
- stroke economy: distance per stroke, stroke rate, rhythm, and coordination
- starts, turns, and underwater phases: especially important in pool racing
- pacing: sprint, middle-distance, distance, and open-water demands differ heavily
- event specificity: 50 m sprint, 100/200 m, 400/800/1500 m, individual medley, relay, and open-water races need different plans
- water confidence and safety: beginners may need floating, breathing, and comfort before fitness work

## Main Skill Families

### Water Confidence And Safety

Beginner swimming must start with:

- comfort in water
- face immersion
- exhalation under water
- floating and recovery to stand
- basic kicking and gliding
- safe pool entry/exit
- lane etiquette and supervision

Do not give high-volume swim workouts to a user who cannot breathe, float, or recover safely.

### Freestyle

Key areas:

- horizontal body line
- relaxed exhalation
- head position
- rotation from trunk/hips
- catch and pull path
- recovery timing
- kick rhythm
- bilateral or controlled breathing
- stroke count and distance per stroke

Common problems:

- lifting the head to breathe
- crossing midline
- dropped elbow catch
- over-kicking for endurance users
- poor exhalation causing panic or breath holding
- excessive shoulder load from poor mechanics

### Backstroke

Key areas:

- body line and hip position
- head stillness
- rotation
- alternating arm rhythm
- catch depth and pull path
- kick consistency
- wall awareness

Risks:

- shoulder irritation from poor overhead mechanics
- low-back arching if hips sink
- collision risk in crowded lanes

### Breaststroke

Key areas:

- timing of pull, breath, kick, glide
- narrow efficient kick
- hip and knee control
- streamline recovery
- glide discipline

Risks:

- knee or groin irritation from kick mechanics
- low-back extension if timing is poor
- overuse from high breaststroke volume

### Butterfly

Key areas:

- body wave timing
- dolphin kick rhythm
- catch and press
- breathing timing
- relaxed recovery
- trunk and shoulder endurance

Risks:

- shoulder overload
- low-back irritation
- fatigue-based technique collapse

Butterfly should be gated carefully. Most beginners should not receive high-volume butterfly.

### Individual Medley

IM requires:

- all four strokes
- stroke transition skill
- turn specificity
- balanced shoulder/knee/back load
- technical endurance across fatigue

### Starts, Turns, Streamlines, And Underwaters

For racing swimmers, starts and turns are not optional extras. They are performance skills.

Important areas:

- dive/start setup
- reaction and entry
- streamline
- underwater dolphin kick
- breakout timing
- flip turns
- open turns
- push-off alignment

Safety gates:

- no diving prescriptions without safe pool rules, supervision, and demonstrated skill
- underwaters require breath-control caution and should avoid risky hypoxic work

## Event And Role Categories

The app should support:

- beginner swimmer
- fitness swimmer
- sprint freestyle swimmer
- middle-distance freestyle swimmer
- distance swimmer
- backstroke swimmer
- breaststroke swimmer
- butterfly swimmer
- individual medley swimmer
- open-water swimmer
- triathlon swimmer
- masters swimmer
- youth/development swimmer

These roles affect training emphasis. A triathlon swimmer needs open-water skills and endurance economy. A 50 m sprinter needs power, start/turn speed, and high-quality short repeats. A fitness beginner needs breathing, comfort, technique, and sustainable volume.

## Physical Demands

Swimming requires:

- shoulder and scapular endurance
- trunk stiffness and rotation control
- thoracic mobility
- hip extension and trunk coordination
- ankle mobility for kicking
- aerobic base
- lactate tolerance for middle-distance/sprint work
- power for starts and turns
- dryland strength for posture, shoulder health, and force transfer

Unlike field sports, swimming has low ground-impact load but high repetitive shoulder load.

## Common Injury And Load Risks

Important risks:

- swimmer's shoulder / shoulder impingement-like symptoms
- rotator cuff irritation
- scapular control deficits
- neck irritation from breathing mechanics
- low-back irritation, especially butterfly and poor body position
- breaststroke knee or groin symptoms
- overuse from rapid yardage increases
- fatigue technique collapse
- hypoxic/breath-control risk if misused

Programming should track:

- weekly swim volume
- high-intensity repeat volume
- stroke-specific volume
- paddles/pull buoy/fins use
- shoulder symptom trend
- knee/groin response for breaststroke
- back response for butterfly/underwaters
- dryland + pool total load

## Strength And Conditioning Model

Dryland should support swimming, not replace water skill.

Useful qualities:

- shoulder/scapular control
- rotator cuff capacity
- thoracic mobility
- trunk anti-extension and rotation control
- hip hinge and posterior-chain strength
- pull strength balanced with shoulder health
- power for starts and turns
- ankle mobility and plantar-flexion capacity for kicking

Avoid:

- excessive overhead fatigue for swimmers with shoulder pain
- hard upper-body lifting immediately before key swim sessions
- bodybuilding-only programs that add fatigue without stroke transfer
- high-volume dryland circuits that ruin water technique quality

## Macro Planning Logic

### Beginner Foundation

Used when:

- beginner or poor water confidence
- cannot breathe rhythmically
- cannot swim continuous lengths
- fear/panic in water
- returning after long break

Emphasis:

- comfort and safety
- breathing and floating
- short technique repeats
- rest-rich practice
- easy aerobic exposure
- dryland mobility and basic strength

### Technique And Base

Used when:

- user can swim basic lengths
- needs fitness or sport support
- technique limits efficiency

Emphasis:

- freestyle efficiency
- stroke count awareness
- aerobic base
- shoulder durability
- basic pacing
- gradual volume progression

### Speed / Power Block

Used when:

- swimmer has adequate technique and base
- sprint or race goal exists

Emphasis:

- short high-quality repeats
- starts/turns/streamlines
- power and full recovery
- race-pace work
- avoid junk fatigue

### Race-Specific / Competition Block

Used when:

- target event/date exists

Emphasis:

- event pace
- starts and turns
- taper
- quality over volume
- technical confidence

### Open-Water / Triathlon Block

Used when:

- open water, triathlon, or long-distance event goal exists

Emphasis:

- sighting
- bilateral breathing
- drafting awareness
- sustained rhythm
- anxiety control
- environmental safety
- wetsuit/context if relevant

### Return To Swim

Used when:

- shoulder, back, knee, or long break is present

Emphasis:

- low volume
- controlled intensity
- technique-only return
- avoid paddles and high-resistance tools early
- symptom-gated progression

## Teaching Levels

### Beginner

Can include:

- breathing drills
- floating
- glide/kick
- short freestyle fragments
- rest-rich intervals
- water confidence

Avoid:

- hypoxic sets
- long continuous swims without skill
- high-intensity repeats
- butterfly volume
- unsupervised diving/start instructions

### Intermediate

Can include:

- structured aerobic sets
- technique + endurance blend
- pacing intro
- pull/kick/drill sets
- basic starts/turns if pool context allows
- dryland support

Avoid:

- excessive yardage jumps
- paddles/fins as default
- speed work when technique collapses

### Advanced

Can include:

- race-pace sets
- lactate tolerance
- start/turn specialization
- stroke-specific training
- tapering
- high-quality speed
- event-specific dryland

Avoid:

- stacking hard pool days and heavy upper-body dryland without recovery
- ignoring shoulder/back/knee symptom trends

## Retrieval Needs

Swimming retrieval must send compact context by:

- level
- water confidence
- target event or goal
- stroke focus
- pool access
- available session duration
- shoulder/back/knee history
- open-water/triathlon context
- current swim ability: continuous distance, pace, comfort, stroke familiarity

Do not send all swimming records. Select:

- 4-8 relevant teaching progressions
- 2-4 skill assessments
- 2-4 planning rules
- 5-12 workout type/rule records
- 3-8 dryland support rules

## Correct Agent Split

Use six agents after this brief:

1. Stroke Mechanics Agent
   - freestyle, backstroke, breaststroke, butterfly, breathing, common errors, cues, drills, beginner/intermediate/advanced progressions

2. Starts / Turns / Underwater Agent
   - dive starts, push starts, flip turns, open turns, streamlines, underwater dolphin kick, breakouts, safety gates

3. Event Programming Agent
   - sprint, middle-distance, distance, IM, open-water, triathlon, pacing, training zones, tapering, periodization

4. S&C / Injury / Load Agent
   - swimmer shoulder, back, breaststroke knee, dryland, mobility, load monitoring, return-to-swim rules

5. Beginner Safety / Learn-To-Swim Agent
   - water confidence, breathing, floating, survival basics, fear/anxiety, progression from non-swimmer to fitness swimmer

6. Level Teaching / Assessment Agent
   - beginner/intermediate/advanced skill assessments, transition rules, readiness criteria, role/event-specific progression

## Source Direction For Agents

Agents should prefer:

- World Aquatics / FINA rules and education
- ITF equivalent is not relevant; use swimming governing bodies
- USA Swimming, Swim England, Swimming Australia, British Swimming, ASCA where available
- peer-reviewed sports medicine and sport science reviews
- Olympic or federation athlete-development material
- reputable coaching education sources

Avoid:

- unsourced swim workouts
- influencer-only technique claims
- unsafe breath-holding or hypoxic content
- copying exact copyrighted programs

## Useful Starting Sources

- World Aquatics rules and technical resources: https://www.worldaquatics.com/
- USA Swimming education and safe sport resources: https://www.usaswimming.org/
- Swim England teaching and coaching resources: https://www.swimming.org/
- Swimming Australia coaching resources: https://www.swimming.org.au/
- Sports medicine review on swimming injuries: https://pmc.ncbi.nlm.nih.gov/
- Physiological and biomechanical swimming research: https://pubmed.ncbi.nlm.nih.gov/

## Backend Goal

The final swimming database should help SFTC:

- generate safe beginner swim plans
- create fitness and athletic swim support plans
- build event-specific swim blocks
- integrate swimming into hybrid athletic programs
- adjust shoulder/back/knee load
- teach stroke technique by level
- select pool workouts without random volume
- protect users from unsafe breath-holding, diving, and load spikes


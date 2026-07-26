# Sport Content Research — what we're building and what "good" means

Research foundation for the Sport tab rebuild. No implementation here — this is
the understanding that the schema, the generation pipeline and the review
process must be built against.

---

## 1. What the app actually is

Runlete is an **athlete's companion**: a running-territory game plus training
for people who play sports. The Sport tab's job is not "an encyclopedia of
sports" — it is **"make me better at my sport."**

Two personas use it:
- **The practitioner** — plays badminton weekly, wants better footwork and
  smarter shot selection.
- **The newcomer** — a runner adding swimming for cross-training, needs
  "start here" content that doesn't assume anything.

Every content decision should be tested against one question: *would a coach
say this to an athlete?* If it reads like Wikipedia, it fails. If it reads like
coaching, it passes.

---

## 2. The four kinds of sport knowledge (they need different shapes)

The user's examples — "how to do butterfly", "pool sizes", "Olympic rules",
"passing IQ" — are actually **four different kinds of knowledge**. Sports
pedagogy treats them differently, and so must our content model.

### A. Reference (declarative)
Rules, scoring, formats, equipment, court/pool dimensions, divisions, weight
classes. Facts with authoritative sources (governing bodies).
- **Shape:** short reference cards. Precise numbers. No fluff.
- **Quality risk:** wrong numbers. Every figure must be checkable against the
  governing body (World Aquatics, FIBA, ITTF rulebooks…).
- **Easy to generate, easy to verify.**

### B. Technique (procedural)
How to execute a skill: freestyle stroke, jump shot, cover drive, jab.
This is where quality lives or dies. Motor-learning research says good
technique instruction has a known anatomy:
1. **Phase decomposition** — butterfly = body position → undulation → arm
   pull → recovery → breathing → timing. Never one blob of prose.
2. **Coaching cues** — short, preferably *external* cues ("push the water
   back", "reach for the far wall") which research shows outperform internal
   body-part cues for learning and retention.
3. **Common errors + fixes** — the most valuable part for a self-learner;
   every technique unit must have them.
4. **Level staging** — learners pass through cognitive → associative →
   autonomous stages; a beginner needs "what does the movement look like",
   an advanced player needs refinement details (stroke rate, spin variation).
   Content must be tagged by level and *say different things per level*.
- **Quality risk:** describing instead of coaching. "Extend the hips
  powerfully" is description; "jump as if pushing the ground away" is
  coaching.

### C. Tactics / game IQ (perceptual-cognitive)
Decision-making: when to pass, where to position, shot selection, pacing.
Coaching practice (Teaching Games for Understanding, tactical periodization)
teaches this through **principles + scenarios**, not essays:
- **Principles of play** — e.g. invasion sports share attack principles
  (penetration, support, width, depth) and defense principles (pressure,
  cover, balance, compactness).
- **Scenario framing** — "when X, do Y, because Z". A 2-v-1 fast break; a
  short-serve return in badminton; sitting in behind a rival's wheel in a
  cycling breakaway.
- Only competitive sports have tactics. Practice-based activities do not, and
  forcing a "tactics" section onto them produces filler.

### D. Progression (developmental)
What to learn, in what order, and how to know you're ready to advance —
the LTAD lens. This is what turns a pile of articles into a **curriculum**:
beginner → intermediate → advanced pathways with skill checkpoints.
- **Our existing knowledge base is exactly this type**: 804 teaching
  progressions + 177 skill assessments across 11 sports. It slots in here.

---

## 3. The quality bar (good vs. slop)

| Dimension | Slop | Our bar |
|---|---|---|
| Facts | "Pools are usually 25 or 50 meters" | "Olympic/World Champs: 50m × 25m, 10 lanes, ≥2m deep (World Aquatics). Short-course: 25m." |
| Technique | "Keep your body streamlined and kick powerfully" | Phases + cues + the 3 most common errors and their fixes, per level |
| Tactics | "Communication and teamwork are important" | "2-v-1 break: the ball-handler attacks the defender's inside shoulder to force commitment, then passes. If the defender sags, take the layup." |
| Structure | Same 4 headings forced on every sport | Each sport structured by its own logic (see §4) |
| Voice | Encyclopedia | Coach. Direct, second-person, actionable |
| Level | One-size | Explicitly staged beginner / intermediate / advanced |

Additional hard rules:
- Every reference number traceable to the governing body's current rules.
- Safety content is mandatory where relevant (combat sports sparring,
  horse riding, open-water swimming) and must be conservative.
- No medical claims. Injury topics say "see a professional".
- Technique is visual by nature. Text-first now, but the schema must carry a
  `media` slot; the long-term answer is our own original demo clips (same
  original-only philosophy as the exercise video pipeline).

---

## 4. The 17 sports — families and per-sport blueprints

One template does not fit all. The sports fall into **8 families**; the family
determines which sections a sport gets and what its "technique units" are.

### Family 1 — Cyclic endurance/technique (Running, Swimming, Cycling)
Technique = one repetitive movement refined forever + a training methodology.
Rules are minor; **technique + training are the core**. Sections: Technique ·
Training (zones, periodization, workouts) · Racing (events, pacing) · Rules &
Formats (small).
- **Running:** posture/lean, footstrike & cadence, arm carry; sprint vs
  distance mechanics (the "Olympic runner vs marathoner" contrast the user
  asked for is a real content unit: sprint = ball-of-foot, high knees, full
  extension; distance = midfoot, ~170–185 cadence, economy); hills; training
  zones; race distances 5K→marathon; pacing.
- **Swimming:** 4 strokes each with body/kick/pull/breathing/timing phases +
  starts & turns + breathing as its own beginner unit; training sets &
  drills; events, pool specs, stroke rules (what disqualifies a butterfly).
- **Cycling:** position/bike fit, pedaling, cornering/descending, group
  riding & drafting; power/HR training; road/TT/climbing tactics — cycling is
  the one endurance sport with real *team* tactics (breakaways, lead-outs).

### Family 2 — Racket/net individual (Tennis, Badminton, Table Tennis)
Discrete shot vocabulary + footwork + shot-selection tactics + scoring.
Sections: Fundamentals (grips, stances, footwork) · Shots (each a technique
unit) · Tactics (singles vs doubles are genuinely different games) · Rules &
Scoring.
- **Tennis:** serve, forehand, backhand (1H/2H), volley, slice, drop, lob;
  court positioning, patterns (serve+1), surfaces; scoring/tiebreaks.
- **Badminton:** clear/drop/smash/drive/net shots, the deceptive flick;
  footwork is *the* differentiator (6-corner movement, split step); singles
  (length, patience) vs doubles (rotation, attack formations); rally scoring.
- **Table tennis:** grips (shakehand/penhold), spin as the sport's core
  concept (topspin/backspin/sidespin, reading serves), loops/pushes/blocks;
  serve tactics; ITTF scoring (11-pt, 2-serve rotation).

### Family 3 — Invasion team sports (Basketball, Football, Hockey, Rugby)
Individual skills + shared principles of play + positions + set pieces.
Sections: The Game (explanation, positions, formats) · Skills · Principles &
Tactics (attack/defense principles, then sport-specific systems) · Game IQ
(scenario units) · Rules.
- **Basketball:** shooting form (BEEF/one-motion), layups/finishing,
  dribbling, passing (the user's "passing IQ": pass ahead of the receiver,
  fakes move defenders, weak-side awareness); pick-and-roll as the core
  2-man game; man vs zone; transition; 24s/8s/3s rules, fouls.
- **Football (soccer):** first touch, passing range, 1v1, finishing;
  formations as reference; principles (width, penetration, pressing vs
  block); offside explained properly (a notorious "explain it well" test).
- **Hockey (field):** dribble/push/hit/flick, reverse stick; D-entry and
  penalty-corner routines (unique set-piece craft); no-feet rule, shooting
  circle, quarters.
- **Rugby:** catch-pass (backwards passing shapes everything), tackle safety
  (mandatory safety-first unit), rucking, lineout/scrum basics; phase play,
  territory vs possession; union laws (knock-on, offside lines) — and note
  union vs league distinction once, then teach union.

### Family 4 — Bat-and-ball (Cricket)
Three separate crafts in one sport. Sections: The Game (formats matter
uniquely: Test/ODI/T20 change tactics entirely) · Batting (stance, the shot
map: drives/cuts/pulls/sweeps, playing pace vs spin) · Bowling (pace:
grip/run-up/seam/swing; spin: off/leg, flight) · Fielding & Keeping ·
Tactics per format · Laws (LBW is the "explain it well" test).

### Family 5 — Combat (Boxing, MMA)
Technique + defense + fight IQ + heavy safety/rules framing. Sections:
Fundamentals (stance, guard, footwork) · Offense · Defense · Fight IQ
(distance management, feints, ring/cage control) · Rules & Safety (weight
classes, scoring criteria, sparring safety as a mandatory unit).
- **Boxing:** jab/cross/hooks/uppercuts, combinations; slips/rolls/parries;
  10-point-must scoring explained.
- **MMA:** the three ranges (striking/clinch/ground) as the organizing idea;
  takedowns & defense, guard/mount/back basics, submissions conceptually;
  unified rules, fouls. MMA content links to boxing fundamentals rather than
  duplicating them.

### Family 6 — Precision individual (Golf)
Technique + its own unique IQ (course management). Sections: Fundamentals
(grip, setup, ball flight laws — the modern teaching foundation) · Full Swing ·
Short Game (50% of scoring: chipping, pitching, bunkers, putting) · Course
Management (club selection, risk, "aim for the fat of the green") · Rules &
Etiquette (stroke play vs match play, penalties, handicap system).

### Family 7 — Hybrid race format (Hyrox)
A fixed, fully-specified format — closest to "learnable by heart". Sections:
The Format (8 × [1km run + station], fixed station order: SkiErg 1000m → sled
push → sled pull → burpee broad jumps → rowing 1000m → farmers carry → sandbag
lunges → wall balls; divisions Open/Pro/Doubles/Relay, weights per division) ·
Station Technique (each station = a technique unit with standards, e.g. wall
ball depth/target rules) · Race Strategy (pacing the runs, compromised
running, transitions, roxzone) · Training (hybrid engine + strength balance).
Verify against the official HYROX rulebook each season (weights/standards
change).

### Family 8 — Equestrian (Horse Riding)
Unique: a partnership with an animal; safety- and care-heavy. Sections:
Foundations (safety, mounting, position/seat) · The Gaits (walk/trot/canter,
rising trot, aids) · Disciplines (dressage, show jumping, eventing — each
explained with its scoring) · Horse Care & Partnership (grooming, tack,
reading the horse) · Rules & Competition (FEI basics). Tone must be
safety-first throughout.

---

## 5. Sourcing map (verification targets, not content to copy)

| Sport | Rules authority | Technique verification frame |
|---|---|---|
| Running | World Athletics | sprint vs distance mechanics, cadence research |
| Swimming | World Aquatics | stroke-phase model used by federations' learn-to-swim levels |
| Cycling | UCI | bike fit & power-training conventions |
| Tennis | ITF | standard shot pedagogy |
| Badminton | BWF | footwork-first pedagogy |
| Table tennis | ITTF | spin-first pedagogy |
| Volleyball | FIVB | skill + rotation system |
| Basketball | FIBA (note NBA rule diffs) | standard shooting/PnR pedagogy |
| Football | IFAB/FIFA | principles-of-play model |
| Hockey | FIH | penalty-corner conventions |
| Rugby | World Rugby | tackle-safety programs (mandatory) |
| Cricket | ICC / MCC Laws | batting/bowling craft conventions |
| Boxing | World Boxing / unified pro rules | standard boxing pedagogy |
| MMA | Unified Rules of MMA | range-based model |
| Golf | R&A / USGA | ball-flight laws |
| Hyrox | Official HYROX rulebook (per season) | official station standards |
| Horse riding | FEI | national-federation safety guidance |

Existing knowledge base (local `test_database`) plugs into the **Progression**
layer for the 11 covered sports: 804 `sport_teaching_progressions`,
177 `sport_skill_assessments`, plus roles and training rules.

---

## 6. How content should be created (method, not code)

1. **Blueprint pass (per sport).** Generate the sport's *skill tree and
   section plan* per its family template — not prose. Human-review the
   blueprint: this is cheap to fix and determines everything downstream.
2. **Unit pass (per node).** Generate each content unit with a
   **type-specific template**:
   - Reference card: claim + number + source-anchor.
   - Technique unit: phases → cues (external-first) → common errors/fixes →
     per-level notes → drills (link KB where available).
   - Tactic unit: principle → scenario ("when X, do Y, because Z") →
     common mistake.
   - Progression: level checklist with "you're ready when…" criteria.
3. **Verification pass.** Every reference number cross-checked against the
   governing-body source; technique/tactics spot-checked against the family
   pedagogy. Fail → regenerate that unit only.
4. **Human gate.** Nothing ships unreviewed. Review the blueprint (cheap) and
   sample-audit units (spot checks), not every word.
5. **Depth tiers.** Don't build 17 sports to equal depth at once. Tier by
   user demand: full depth for the sports users actually select; launch-depth
   (blueprint + fundamentals + rules) for the rest, deepen on demand.

## 7. UI/UX — the interface follows the content types

The four knowledge types each get their own UI treatment; one generic
"article page" would flatten the quality the content model creates.

### Screen flow
Sport home → Section → Unit detail. Three levels, no deeper.

**Screen 1 — Sport home (the tab itself)**
- Sport switcher chips: the user's onboarding sports first, then "All".
  (Same chip pattern as the club switcher — reuse it.)
- "Continue learning" card — resumes the last unit (retention hook).
- Section cards driven by the sport's *family* (Swimming: Technique /
  Training / Racing / Rules; Basketball: The Game / Skills / Tactics /
  Game IQ / Rules), each with progress (e.g. "Technique · 4/12").

**Screen 2 — Section list**
- Units grouped by sub-topic (Strokes → freestyle, backstroke…), each row:
  title, level tag, read-time, done-check.

**Screen 3 — Unit detail, rendered by content type**
- **Technique unit:** media slot on top (placeholder now, original clips
  later) → numbered phases → coral "coach cue" callouts → common errors as
  error-styled fix cards → linked drills → "mark learned".
- **Reference:** scannable fact rows (label — value), grouped; no prose walls.
- **Tactic / game IQ:** scenario card — situation stated, **tap to reveal**
  the read and the why. Active recall beats passive reading; this also makes
  tactics feel like a game, on-brand for the app.
- **Progression:** checklist with "you're ready when…" criteria per level.

### Level staging in UX
User sets their level per sport once (defaulted from onboarding experience
answers); content defaults to that level with a Beginner / Intermediate /
Advanced toggle visible on every technique unit to peek up or down.

### Progress model
Per-unit completion → section progress → sport progress. Later, skill
assessments (existing KB) can gate level-ups — "pass these checkpoints to
unlock Advanced" — which connects the library to the app's game DNA without
gimmicks. Keep v1 to simple checkmarks + progress counts.

### Design language
Existing app system: white, coral accent (#FF4E2E), bold type, dark
feature-card moments (the tactic scenario card is a natural dark-card
moment). Reuse GlassCard, chip, and progress-bar components already in the
codebase. Reading typography: larger line-height for unit bodies than the
app's stat screens.

## 8. Open questions (decide before building)

- **Depth-first or breadth-first?** All 17 at launch-depth, or 3–4 sports at
  full depth first (e.g. Running + the user's own sports) to validate the
  format with real users?
- **Media**: text-only at launch is accepted; when do diagrams/clips enter?
  (Schema must reserve the slot now.)
- **Where generation runs**: needs API credits (Anthropic currently
  exhausted; OpenRouter key available).

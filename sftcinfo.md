# SFTC — The Complete AI-Powered Athletic Platform

> **Stronger. Faster. Tougher. Conditioned.**
> SFTC is an all-in-one AI-powered fitness and athletic performance platform that combines sport-specific training, intelligent nutrition tracking, health monitoring, sleep analysis, and real-time coaching — all driven by evidence-based science and personalized to your body, sport, and goals.

---

## What Is SFTC?

SFTC is a next-generation mobile fitness app built for **athletes of every level** — from beginners building their first habit to competitive athletes peaking for a season. Unlike generic workout apps, SFTC understands your sport, adapts to your body, and programs like a real strength & conditioning coach.

The app uses a **multi-stage AI engine** powered by Claude (Anthropic) to generate fully periodized, science-backed training programs. It doesn't just give you random workouts — it builds a structured plan with real coaching logic, then adapts it week by week based on how you respond.

---

## How It Works

### 1. Onboarding — Your Athletic Profile (8-Step Flow)

Every SFTC user starts with a deep onboarding that builds a complete athletic profile:

| Step | What We Learn |
|------|--------------|
| **Goals** | Primary goal (sport performance, muscle, fat loss, strength, endurance) plus secondary focuses (mobility, conditioning, jump higher, run faster, pain-free, return from injury) |
| **Experience** | Beginner, Intermediate, or Advanced — plus training location (gym, indoors, outdoors) |
| **Sports** | Select from 20+ sports: Basketball, Cricket, Football, MMA, Boxing, Swimming, Tennis, Running, Cycling, Badminton, Volleyball, Wrestling, Kickboxing, and more |
| **Profile** | Gender, age, height, weight, location, timezone |
| **Schedule** | Training days per week, preferred days, session duration, time of day |
| **Equipment** | Available gear (dumbbells, barbell, kettlebells, pull-up bar, resistance bands, bench, squat rack, machines) — or full gym access |
| **Health** | Pain areas, injury history, medical notes, sleep hours, stress level, diet preference (balanced, vegetarian, vegan, eggetarian, high-protein), and nutrition goal |
| **Assessment** | Baseline fitness tests — push-ups, pull-ups, squats, plank hold, and running pace (min/km) |

After onboarding, SFTC generates your first complete training program within minutes.

---

### 2. The AI Training Engine — How Programs Are Built

SFTC's workout engine is not a template library. It is a **multi-stage AI pipeline** that works like a real strength & conditioning coach:

#### Stage 1 — Macro Plan Selection & AI Tuning
- Rule-based logic selects a **periodized macro template** from a research-backed library based on your sport, goals, experience, schedule, and current training phase.
- The AI then **tunes** the macro plan — adjusting block emphasis, volume distribution, and session types based on your specific profile, injuries, and equipment.

#### Stage 2 — Knowledge Retrieval (Two-Stage)
Before writing a single exercise, the engine pulls from a massive **evidence-based knowledge base**:
- **Exercise Library** — 1000+ exercises with primary movers, variations, progressions, equipment tags, and sport-transfer notes
- **Sport-Specific Training Rules** — Unique programming rules for each sport (cricket acceleration patterns, basketball landing mechanics, swimming shoulder protocols, etc.)
- **Teaching Progressions** — Skill level progressions for each sport from beginner to advanced
- **Training Protocols** — Evidence-based condition-specific protocols (patellar tendinopathy loading, Achilles rehab, hamstring return-to-play, etc.)
- **Injury Modifications** — Automatic exercise swaps and load adjustments based on active injuries
- **Programming Rules** — Sets, reps, tempo, rest, RPE targets tuned to the training goal
- **Semantic Search** — FastEmbed-powered vector retrieval finds the most relevant exercises for your specific sport demands

#### Stage 3 — AI Program Generation
Claude writes a fully structured weekly plan that includes:
- **Session titles, categories, and duration**
- **Warmup, main work, and cooldown blocks** — each with named exercises, sets, reps, tempo, load guidance, RPE targets, and rest periods
- **Coaching notes** for form cues and injury awareness
- **Sport transfer tags** — explaining *why* each exercise matters for your sport
- **Substitutions** — alternative exercises if equipment isn't available
- **Progression rules** — how load, volume, or intensity should advance week to week

#### Stage 4 — Tiered Validation
Every generated plan passes through a **multi-tier validator** that checks:
- Exercise specificity (no generic fillers like "jumping jacks" in a sport program)
- Session structure integrity (warmup → main → cooldown)
- Load and volume within safe bounds
- Injury compliance (no contraindicated movements)
- Sport-transfer quality (exercises must reference the athlete's actual sport demands)
- The validator **repairs or rejects** plans that don't meet the quality bar

#### Stage 5 — Weekly Feedback Loop
After each week, the engine collects:
- **RPE ratings** — perceived effort for each session
- **Pain scores** — any new or worsening pain during exercises
- **Completion rate** — percentage of planned sessions completed
- **Strength trends** — tracked lifts and performance data
- **Mood and energy** — daily check-in data

This feedback drives the **next block of programming** — increasing load when you're ready, backing off when pain signals appear, and adjusting volume based on completion patterns.

---

## Core Features

### 🏋️ Train — Periodized Workout Programs

- **AI-generated periodized programs** — not random workouts, but structured mesocycles with progressive overload, deload weeks, and sport-specific blocks
- **Daily workout cards** with warmup, main work, and cooldown
- **Exercise detail view** with sets, reps, tempo, load guidance, RPE, rest, coaching notes, and substitutions
- **Workout completion tracking** with post-workout feedback (intensity, difficulty, energy, pain, RPE, notes)
- **Exercise history** — tracks every set, rep, and weight you've logged
- **Exercise thumbnails** — visual references for each movement
- **Week-by-week progression** with adaptation targets and sport transfer tags

### 🏃 Run — GPS Tracking & Territory System ("Terra Run")

SFTC includes a full **GPS running tracker** with a unique territory capture gamification system:

- **Live GPS tracking** with real-time distance, pace, duration, and elevation
- **Territory capture** — run loops to "claim" areas on the map, turning running into a game
- **Run history** with pace charts, distance totals, and consistency metrics
- **Post-run reflections** — log how you felt (Great, Good, Tired, Hard) with optional notes
- **Offline-first design** — runs save locally and sync when connectivity returns
- **Run statistics dashboard** — total distance, total territory, average pace, fatigue score, consistency percentage
- **Leaderboard** — compete with other runners on territory captured and distance
- **Social feed** — share runs, like, and comment on other athletes' activities

### 🏃‍♂️ Run Clubs

- **Join or create run clubs** — local running communities organized by city
- **Club leaderboards** — total distance, territory, and active members
- **Club discovery** — find and join public clubs in your area

### 🏟️ Run Training Plans

- **Structured running plans** — goal-based plans (5K, 10K, half marathon) with weekly sessions
- **Session tracking** — mark sessions complete as you progress through weeks

### 🍎 Nutrition — AI Meal Analysis

- **AI-powered food scanning** — take a photo of your meal and AI identifies foods and estimates macros (calories, protein, carbs, fat, fiber)
- **Manual meal logging** — add meals by type (breakfast, lunch, dinner, snack) with full macro entry
- **Daily macro tracking** — circular progress rings for protein, carbs, fats, and fiber against personalized goals
- **Calorie balance** — real-time tracking of consumed vs. target calories
- **Smart alerts** — notifications when you're low on protein or other macros
- **Nutritional insights** — BMR and TDEE calculations based on your profile
- **Goal-based targets** — macros auto-calculated for weight loss, muscle gain, or maintenance
- **Date navigation** — scroll through past days to review nutrition history
- **Full calendar view** — see all logged meals on any date
- **Meal type categorization** — breakfast, lunch, dinner, snack with status badges (Balanced, Low Protein, etc.)
- **Achievement system** — streaks, total meals logged, and badges

### 😴 Sleep Tracking & Analysis

- **Sleep session tracking** — set alarm time, log pre-sleep mood and activities
- **Pre-sleep mood capture** — Stress, Depressed, Tired, Hungry, Relaxed
- **Pre-sleep activity logging** — Coffee, Nicotine, Alcohol, Ate Late, Workout, Nap, Yoga, Meditation, Bath, Milk, Tea
- **Ambient sound player** — Beat Insomnia, Forest Dreams, Ocean Waves, Rainfall sounds for falling asleep
- **Sleep statistics** — average score, duration, deep sleep, REM sleep, total sessions
- **Sleep debt tracking** — monitors accumulated sleep deficit
- **Session history** — review past sleep sessions with detailed breakdowns
- **Wave animations** — calming visual design during sleep tracking mode

### ❤️ Health Hub — Comprehensive Health Monitoring

- **Vital metrics dashboard** — resting heart rate, HRV, sleep quality, weight trends
- **Biology deep-dive** — VO₂ Max, HRV baselines, RHR baselines, lean mass, body fat, weight trends with sparkline charts and gauge visualizations
- **Injury tracking** — log injuries by body region (26 body areas from head to foot), severity (low/medium/high), pain scale (1-10), restrictions, and readiness status (green/yellow/red)
- **Active injury management** — view and resolve active injuries; injury data feeds into the AI engine to modify workouts automatically
- **Data source integrations** — Apple Health, Garmin connectivity

### 📊 Strain Tracking (WHOOP-Style)

- **Daily strain score** — continuous measurement of cardio and muscular exertion
- **Strain status** — Low, Moderate, High indicators
- **Weekly average** — rolling 7-day strain trend
- **Strain history** — daily bar chart showing exertion over time
- **Education content** — explains how strain is calculated from cardio exertion, muscular exertion, and passive strain

### 🔄 Recovery Monitoring

- **Daily recovery score** — calculated each morning from sleep, HRV, and resting heart rate
- **Recovery status** — High (green), Moderate (yellow), Low (red) readiness indicators
- **Sleep metrics** — quality, duration, and composition feeding into recovery
- **HRV tracking** — heart rate variability as a recovery signal
- **RHR monitoring** — resting heart rate trends

### 💪 Strength Benchmarks

- **Key lift tracking** — Back Squat, Bench Press, Deadlift, Overhead Press
- **Estimated 1RM** — calculated using the Epley formula from weight × reps
- **Jump testing** — Countermovement Jump (CMJ), Broad Jump, Single-Leg Hop (left/right)
- **Tendon health questionnaires** — VISA-P (patellar tendon) and VISA-A (Achilles tendon) scores
- **Benchmark data feeds the AI** — load prescription is anchored to your tested maxes, not guesswork

### 📱 Morning Check-In

- **Daily mood capture** — 5-point scale from Very Low to Great
- **Sleep quality rating** — quick daily input
- **Quick wellness snapshot** — feeds into the daily coach analysis for training adjustments

### 📆 Calendar — Daily Activity Timeline

- **Full calendar view** — navigate through months to see any day's activity
- **Day detail view** — all meals, workouts, sleep sessions, moods, and water intake for the selected date
- **Cross-category overview** — see how training, nutrition, and recovery interact across days

### 🧠 AI Performance Coach (Chat)

- **Conversational AI coach** — chat interface for training questions, mental performance, injury recovery, and motivation
- **Quick prompts** — pre-built questions like "How should I structure my training week?", "How can I build mental toughness?", "Tips for better recovery sleep"
- **Context-aware responses** — the coach draws on your profile, training history, and current program

### 📖 Sport IQ — Sport-Specific Lessons

- **Structured lesson library** — sport-specific education organized by category (Fundamentals, Drills, Tactics, Recovery)
- **Multi-sport coverage** — lessons for each of the 20+ supported sports
- **Searchable and filterable** — find lessons by sport, category, difficulty, or keyword
- **Grouped by sport** — lessons organized under their respective sport headers

### 📈 Analytics Dashboard

- **Sleep analytics** — average score, duration, deep sleep, REM, session count, sleep debt
- **Workout analytics** — total workouts, total duration, average duration, calories burned, streak
- **Nutrition analytics** — average calories, protein, carbs, fat, fiber, days logged
- **Dropdown selector** — switch between Sleep, Workout, and Food analytics views

### 📚 Education Center

Interactive educational content teaching athletes the science behind performance:
- **Strain** — how cardio exertion, muscular exertion, and passive strain are measured
- **Recovery** — interpreting recovery scores (High, Moderate, Low) and how sleep, HRV, and RHR drive readiness
- **Sleep** — how sleep quality is calculated from time asleep, sleep stages, disturbances, consistency, and sleep need
- **Biology** — understanding VO₂ Max, HRV baselines, RHR baselines, weight trends, and body composition

### 🏋️‍♂️ Coach Mode (For Trainers)

SFTC supports a **dual-mode** system — users can toggle between **Athlete Mode** and **Coach Mode**:

#### Coach Dashboard
- **Client management** — view all clients with compliance rates and workout completion stats
- **Client search** — find and add new clients
- **Client detail view** — overview, progress trends (weight, run distance), and training history
- **Revenue analytics** — MRR, total revenue, active client count, growth trends

#### Coach Tools
- **Assign workouts** — create and assign custom workouts to specific clients
- **Assign meal plans** — set meal recommendations with type and calorie targets
- **Set goals** — create goals (weight loss, muscle gain, etc.) with target values, units, and deadlines
- **Track compliance** — see completion rates and progress for each client

#### Client View ("My Coach")
- **Pending requests** — accept or decline coach invitations
- **Coach workouts** — view and complete workouts assigned by your coach
- **Coach meals** — see meal plans from your coach
- **Coach goals** — track goals set by your coach with progress indicators

### 🎯 Goals & Trackers

- **Multi-goal tracking** — Weight, Workout frequency, Sleep, Water intake
- **Progress visualization** — current vs. target with unit tracking
- **Quick add** — tap to update progress on any goal

---

## Supported Sports (20+)

SFTC has deep, sport-specific programming logic with custom training rules, teaching progressions, skill assessments, and exercise selection for:

| Category | Sports |
|----------|--------|
| **Court & Field** | Basketball, Cricket, Football (Soccer), Volleyball, Badminton, Tennis, Table Tennis, Hockey, Rugby |
| **Combat** | Boxing, MMA, Kickboxing, Wrestling |
| **Endurance** | Running, Cycling, Swimming |
| **Lifestyle** | Yoga, Pilates, Climbing, Golf, Horse Riding, Hyrox |

Each sport has its own:
- **Training rules** — sport-specific volume, intensity, and periodization logic
- **Movement pattern priorities** — which physical qualities matter most (acceleration, deceleration, rotational power, landing mechanics, etc.)
- **Teaching progressions** — beginner to advanced skill development pathways
- **Skill assessments** — benchmarks for level transitions
- **Exercise selection bias** — the AI prioritizes exercises with direct transfer to your sport

---

## Evidence-Based Training Protocols

SFTC's knowledge base includes expert-level condition-specific protocols with concrete dosing (sets/reps/tempo/intensity/frequency + progression criteria):

| Protocol | Description |
|----------|-------------|
| **Patellar Tendinopathy** | Progressive tendon loading: isometric → heavy-slow-resistance → energy storage, with VISA-P monitoring |
| **Achilles Tendinopathy** | Graded calf/Achilles loading: isometric → slow calf raises → plyometric reintroduction, with VISA-A monitoring |
| **Hamstring Strain Recovery** | Nordics, hip-dominant loading, eccentric progression, running reintroduction criteria |
| **Load Prescription Anchors** | Percentage-based programming anchored to tested 1RM (Epley formula) |
| **Jump Training Progressions** | Bilateral → unilateral, low → high intensity, landing quality gates |
| **Return-to-Sport Protocols** | Strength LSI >90%, pain-free loading, graduated activity reintroduction |

---

## Technical Architecture

### Frontend
- **React Native (Expo)** — cross-platform mobile app for iOS and Android
- **Expo Router** — file-based routing with typed routes
- **Zustand** — lightweight state management for auth and onboarding
- **Glassmorphism design system** — premium glass-card UI with linear gradients
- **Expo Location** — GPS tracking for runs
- **Expo ImagePicker** — camera access for meal scanning

### Backend
- **FastAPI (Python)** — high-performance async API server
- **MongoDB (Motor)** — NoSQL database with 60+ collections for comprehensive data modeling
- **JWT Authentication** — secure token-based auth with OTP email verification
- **Claude AI (Anthropic)** — workout generation, program planning, and coaching chat
- **OpenRouter** — meal image analysis via GPT-4o-mini
- **FastEmbed** — semantic vector search for exercise retrieval
- **Rate Limiting (SlowAPI)** — API protection against abuse

### AI Stack
- **Claude Opus / Haiku** — primary models for training program generation
- **GPT-4o-mini** — meal analysis from food photos
- **FastEmbed** — local embedding model for semantic exercise search
- **Tiered validation** — multi-pass quality scoring for AI-generated programs

### Knowledge Base
- **1000+ exercises** — with detailed metadata, sport tags, and progression paths
- **60+ MongoDB collections** — exercises, sport profiles, training rules, protocols, assessments, and more
- **Research-backed protocols** — from peer-reviewed sources (Kongsgaard, Rio et al., etc.)
- **Multi-source ingestion** — data from textbooks, research papers, and structured web research across 15+ sport domains

---

## Level Progression System

SFTC uses an **objective, evidence-based level progression** system:

- **Beginner → Intermediate**: Requires 8+ completed workouts with 85%+ completion rate and no active pain risk
- **Intermediate → Advanced**: Requires 16+ completed workouts with 85%+ completion rate and no active pain risk
- **Hold/Regression triggers**: Completion rate below 65%, active injuries, or average intensity rating ≥ 9/10
- **120-day assessment window** — decisions based on recent training history, not lifetime data
- **Auto-with-review** — the system recommends level changes; the athlete/coach can approve

---

## Daily Coach Analysis

The AI generates a **daily coaching analysis** that includes:

| Signal | What It Does |
|--------|-------------|
| **Readiness Score** | 0-100 score based on sleep, mood, soreness, and training load |
| **Training Recommendation** | Prescribes intensity level for the day |
| **Workout Modifications** | Specific changes based on recovery and pain signals |
| **Nutrition Recommendation** | Dietary adjustments based on activity and goals |
| **Recovery Recommendation** | Sleep, mobility, and rest guidance |
| **Risk Flags** | Warnings about overtraining, injury risk, or inconsistency |
| **Trend Notes** | Multi-day patterns the coach should act on |
| **Should Regenerate Plan** | Triggers a new program if the current one needs major adjustment |

---

## Security & Authentication

- **OTP-based registration** — email verification required to create an account
- **Password-based login** — with OTP-based password reset flow
- **JWT tokens** — 30-day expiry with HS256 signing
- **Rate limiting** — API-level protection
- **CORS policy** — restricted to allowed origins

---

## Design Philosophy

SFTC is built on four design principles:

1. **Sport-First** — Training is designed around your sport, not generic fitness goals
2. **Evidence-Based** — Every protocol, progression, and programming decision is grounded in peer-reviewed research
3. **Adaptive** — The AI learns from your feedback and adjusts your program in real-time
4. **Premium Experience** — Nike-inspired clean design with glassmorphism, linear gradients, and micro-animations

---

## App Navigation

| Tab | Purpose |
|-----|---------|
| **Home** | Daily dashboard — today's workout, strain, activity, goals, nutrition snapshot, sport IQ |
| **Train** | Full training program — weekly schedule, workout detail, exercise library |
| **Run** | GPS run tracking, territory capture, run history, leaderboards, clubs, social feed, training plans |
| **Sport** | Sport IQ lesson library — fundamentals, drills, tactics, recovery by sport |
| **Profile** | User profile, stats, mode toggle (athlete/coach), settings, help, privacy, terms, logout |

---

## Who Is SFTC For?

- **Competitive athletes** who want sport-specific, periodized training that adapts to their season
- **Gym-goers** who want intelligent programming instead of random workouts
- **Runners** who want GPS tracking with a gamified territory system and social community
- **Combat sport athletes** who need fight-camp-aware periodization with weight management
- **Coaches and personal trainers** who want to manage clients, assign workouts, and track compliance
- **Anyone recovering from injury** who needs safe, evidence-based loading protocols
- **Beginners** who want to build a habit with simple, progressive programming

---

## What Makes SFTC Different?

| Feature | Generic Apps | SFTC |
|---------|-------------|------|
| **Workout Generation** | Template-based or random | Multi-stage AI with knowledge retrieval, periodization, and validation |
| **Sport Specificity** | Generic strength/cardio | Deep sport profiles with custom training rules for 20+ sports |
| **Injury Awareness** | None | Evidence-based protocols auto-modify workouts based on active injuries |
| **Progression** | Manual or none | Objective, data-driven level progression with safety gates |
| **Nutrition** | Manual macro counting | AI food photo analysis + smart goal-based macro targets |
| **Running** | Basic GPS tracking | Territory capture gamification + social leaderboards + run clubs |
| **Coaching** | One-size-fits-all | Dual-mode (athlete/coach) with client management and AI daily analysis |
| **Education** | None | In-app education center teaching the science of strain, recovery, sleep, and biology |
| **Feedback Loop** | None | Weekly RPE, pain, completion, and strength data drive the next program block |

---

*SFTC — Because your training should be as smart as you are.*

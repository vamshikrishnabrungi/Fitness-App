from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


def _coerce_string_list(value):
    if value in (None, ''):
        return []
    if isinstance(value, list):
        return value
    return [str(value)]


class UserProfile(BaseModel):
    onboarding_version: int = 1
    onboarding_completed_at: Optional[datetime] = None

    # Identity and location
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    timezone: Optional[str] = None

    # Goals and sport context
    goals: List[str] = []
    selected_goals: List[str] = []
    primary_goal: Optional[str] = None
    target_date: Optional[str] = None
    target_weight_kg: Optional[float] = None
    sports: List[str] = []
    sport_details: List[Dict[str, Any]] = []
    competition_level: Optional[str] = None
    season_phase: Optional[str] = None
    upcoming_events: List[Dict[str, Any]] = []

    # Training context
    experience: Optional[str] = None
    training_location: Optional[str] = None
    equipment: List[str] = []
    facilities: List[str] = []
    training_days_per_week: Optional[int] = None
    preferred_training_days: List[str] = []
    session_duration_min: Optional[int] = None
    preferred_training_time: Optional[str] = None
    schedule_constraints: Optional[str] = None
    fitness_assessment: Dict[str, Any] = {}

    # Health, recovery, and constraints
    current_injuries: List[Dict[str, Any]] = []
    injury_history: List[Dict[str, Any]] = []
    pain_areas: List[str] = []
    medical_notes: Optional[str] = None
    sleep_avg_hours: Optional[float] = None
    stress_level: Optional[str] = None
    recovery_score_baseline: Optional[float] = None

    # Nutrition preferences
    diet_preference: Optional[str] = None
    dietary_restrictions: List[str] = []
    allergies: List[str] = []
    nutrition_goal: Optional[str] = None

    marketing_opt_in: Optional[bool] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)
    name: str = Field(..., max_length=100)
    otp_code: str = Field(..., max_length=10)
    profile: Optional[UserProfile] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)


class OtpRequest(BaseModel):
    email: EmailStr


class OtpVerify(BaseModel):
    email: EmailStr
    code: str


class PasswordReset(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile: Optional[UserProfile] = None
    mode: Optional[str] = None


class AthleteProfileUpsert(BaseModel):
    profile: UserProfile
    generate_program: bool = False


class OnboardingComplete(BaseModel):
    profile: UserProfile
    generate_program: bool = True


class WorkoutExercise(BaseModel):
    name: str
    exercise_id: Optional[str] = None
    source_refs: List[Dict[str, Any]] = []
    purpose: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration: Optional[str] = None
    rest: Optional[str] = None
    notes: Optional[str] = None


class Workout(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    category: str
    duration: int
    difficulty: str
    equipment: List[str] = []
    exercises: List[WorkoutExercise] = []
    description: Optional[str] = None
    ai_generated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_date: Optional[str] = None
    completed: bool = False
    user_feedback: Optional[Dict[str, Any]] = None


class PerformedExercise(BaseModel):
    name: str
    exercise_id: Optional[str] = None
    weight_kg: Optional[float] = None      # actual working load lifted
    reps: Optional[int] = None             # actual reps completed


class WorkoutFeedback(BaseModel):
    workout_id: str
    intensity_rating: int
    completion_percentage: int
    difficulty_feedback: str
    energy_level: str
    pain_score: Optional[int] = None
    rpe: Optional[float] = None
    notes: Optional[str] = None
    performed_exercises: List[PerformedExercise] = Field(default_factory=list)


class ProgramExercisePrescription(BaseModel):
    name: str
    exercise_id: Optional[str] = None
    purpose: Optional[str] = None
    category: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration: Optional[str] = None
    load_guidance: Optional[str] = None
    rpe: Optional[str] = None
    rest: Optional[str] = None
    tempo: Optional[str] = None
    coaching_notes: List[str] = []
    substitutions: List[str] = []

    @field_validator('sets', mode='before')
    @classmethod
    def coerce_sets(cls, value):
        if value in (None, ''):
            return None
        return int(value)

    @field_validator('coaching_notes', 'substitutions', mode='before')
    @classmethod
    def coerce_exercise_lists(cls, value):
        return _coerce_string_list(value)


class ProgramWorkoutPrescription(BaseModel):
    day: str
    title: str
    category: str
    duration_min: int
    intensity: str
    adaptation_targets: List[str] = []
    sport_transfer: List[str] = []
    why_this_session: Optional[str] = None
    warmup: List[ProgramExercisePrescription] = []
    main_work: List[ProgramExercisePrescription] = []
    cooldown: List[ProgramExercisePrescription] = []
    injury_modifications: List[str] = []

    @field_validator('duration_min', mode='before')
    @classmethod
    def coerce_duration_min(cls, value):
        return int(value)

    @field_validator('adaptation_targets', 'sport_transfer', 'injury_modifications', mode='before')
    @classmethod
    def coerce_workout_lists(cls, value):
        return _coerce_string_list(value)


class ProgramWeekPlan(BaseModel):
    week_number: int
    theme: str
    workouts: List[ProgramWorkoutPrescription]
    progression_rule: str
    deload_note: Optional[str] = None

    @field_validator('week_number', mode='before')
    @classmethod
    def coerce_week_number(cls, value):
        return int(value)


class ProgramBlockPlan(BaseModel):
    name: str
    start_week: int
    end_week: int
    emphasis: List[str]

    @field_validator('start_week', 'end_week', mode='before')
    @classmethod
    def coerce_week_bounds(cls, value):
        return int(value)


class ProgramGenerationOutput(BaseModel):
    title: str
    goal: str
    sports: List[str] = []
    duration_weeks: int
    athlete_analysis: Dict[str, Any] = {}
    blocks: List[ProgramBlockPlan]
    weeks: List[ProgramWeekPlan]
    nutrition_focus: Optional[str] = None
    recovery_focus: List[str] = []
    safety_notes: List[str] = []
    assumptions: List[str] = []

    @field_validator('duration_weeks', mode='before')
    @classmethod
    def coerce_duration_weeks(cls, value):
        return int(value)

    @field_validator('sports', 'recovery_focus', 'safety_notes', 'assumptions', mode='before')
    @classmethod
    def coerce_program_lists(cls, value):
        return _coerce_string_list(value)

    @field_validator('athlete_analysis', mode='before')
    @classmethod
    def coerce_athlete_analysis(cls, value):
        if value in (None, ''):
            return {}
        if isinstance(value, dict):
            return value
        return {'summary': str(value)}


class DailySnapshotTotals(BaseModel):
    scheduled_workouts: int = 0
    completed_workouts: int = 0
    workout_sessions: int = 0
    exercise_results: int = 0
    run_count: int = 0
    run_distance_km: float = 0
    run_duration_sec: int = 0
    territory_km2: float = 0
    meals_logged: int = 0
    calories: int = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0
    sleep_hours: Optional[float] = None
    sleep_score: Optional[float] = None


class DailyActivitySnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    profile: Dict[str, Any] = {}
    active_program: Optional[Dict[str, Any]] = None
    scheduled_workouts: List[Dict[str, Any]] = []
    workout_sessions: List[Dict[str, Any]] = []
    exercise_results: List[Dict[str, Any]] = []
    runs: List[Dict[str, Any]] = []
    meals: List[Dict[str, Any]] = []
    sleep_sessions: List[Dict[str, Any]] = []
    quick_logs: List[Dict[str, Any]] = []
    moods: List[Dict[str, Any]] = []
    injuries: List[Dict[str, Any]] = []
    health_metrics: List[Dict[str, Any]] = []
    coach_assignments: List[Dict[str, Any]] = []
    totals: DailySnapshotTotals = Field(default_factory=DailySnapshotTotals)
    readiness_inputs: Dict[str, Any] = {}
    data_quality: Dict[str, Any] = {}


class DailyCoachAnalysis(BaseModel):
    date: str
    readiness_score: int
    readiness_label: str
    training_recommendation: str
    workout_modifications: List[str] = []
    nutrition_recommendation: str
    recovery_recommendation: str
    risk_flags: List[str] = []
    trend_notes: List[str] = []
    questions_for_user: List[str] = []
    should_regenerate_plan: bool = False


class Meal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str
    meal_type: str
    name: str
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: float = 0
    foods_identified: List[str] = []
    status: Optional[str] = None
    ai_analyzed: bool = False


class MealCreate(BaseModel):
    meal_type: str
    name: Optional[str] = None
    image_base64: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    foods_identified: List[str] = []
    status: Optional[str] = None
    ai_analyzed: bool = False


class QuickLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str
    mood: str
    energy: str
    stress: str
    sleep_quality: int
    soreness_regions: List[str] = []
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuickLogCreate(BaseModel):
    mood: str
    energy: Optional[str] = None
    stress: Optional[str] = None
    sleep_quality: int
    soreness_regions: List[str] = []
    note: Optional[str] = None


class SleepNoteCreate(BaseModel):
    mood: Optional[str] = None
    activities: List[str] = Field(default_factory=list)
    note: Optional[str] = None


class SleepSessionCreate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    alarm_time: Optional[str] = None
    pre_sleep_mood: Optional[str] = None
    pre_sleep_activities: List[str] = Field(default_factory=list)
    note: Optional[str] = None
    duration_hours: Optional[float] = None
    deep_sleep_hours: Optional[float] = None
    rem_sleep_hours: Optional[float] = None
    efficiency: Optional[float] = None
    sleep_quality: Optional[int] = None
    source: Optional[str] = None


class MoodCreate(BaseModel):
    mood_value: int
    mood_emoji: str
    note: Optional[str] = None
    activities: List[str] = []
    trigger: Optional[str] = None
    trigger_id: Optional[str] = None


class MoodEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood_value: int
    mood_emoji: str
    note: Optional[str] = None
    activities: List[str] = []
    trigger: Optional[str] = None
    trigger_id: Optional[str] = None
    date: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InjuryLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    body_area: str
    severity: str
    pain_scale: int
    restrictions: List[str] = []
    notes: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class InjuryLogCreate(BaseModel):
    body_area: str
    severity: str
    pain_scale: int
    restrictions: List[str] = []
    notes: Optional[str] = None


class StrainSummary(BaseModel):
    today: Optional[float] = None
    status: str = 'moderate'
    weeklyAvg: Optional[float] = None
    history: List[Dict[str, Any]] = []


class RecoverySummary(BaseModel):
    score: Optional[int] = None
    status: str = 'moderate'
    sleep: Dict[str, Any] = {}
    hrv: Dict[str, Any] = {}
    rhr: Dict[str, Any] = {}


class BiologySummary(BaseModel):
    leanMass: Dict[str, Any] = {}
    bodyFat: Dict[str, Any] = {}
    weight: Dict[str, Any] = {}
    status: str = 'needs_update'
    insight: Optional[str] = None


class ProgramSummary(BaseModel):
    title: str
    subtitle: Optional[str] = None
    next_session: Optional[str] = None
    week_label: str
    progress_completed: int
    progress_total: int


class Lesson(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sport: str
    title: str
    category: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[int] = None


class DeepJournalCreate(BaseModel):
    title: Optional[str] = None
    content: str
    tags: List[str] = Field(default_factory=list)
    is_pinned: bool = False


class GuidedJournalCreate(BaseModel):
    template_id: str
    template_name: Optional[str] = None
    responses: Dict[str, str] = Field(default_factory=dict)
    program_id: Optional[str] = None
    program_day: Optional[int] = None
    cbt_distortion: Optional[str] = None


class JournalSearchRequest(BaseModel):
    query: str
    limit: int = 10


class TerraGpsPoint(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[str] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None


class TerraRunCreate(BaseModel):
    gps_path: List[TerraGpsPoint] = Field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class TerraReflectionCreate(BaseModel):
    run_id: str
    feeling: str
    notes: Optional[str] = None


class TerraFeedCreate(BaseModel):
    content: str
    run_id: Optional[str] = None


class TerraTrainingPlanCreate(BaseModel):
    goal: str
    fitness_level: str
    total_weeks: Optional[int] = None
    current_week: Optional[int] = None
    completed_sessions: List[str] = Field(default_factory=list)


class RunClubCreate(BaseModel):
    name: str
    city: str
    description: Optional[str] = None
    is_public: bool = True


class JobStatus(BaseModel):
    job_id: str
    user_id: str
    status: str  # pending, processing, completed, failed
    result_program_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunClubMembership(BaseModel):
    club_id: str
    user_id: str
    role: str = "member"  # owner, admin, member
    status: str = "active"  # active, pending, removed
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class BenchmarkLift(BaseModel):
    exercise: str
    weight_kg: Optional[float] = None
    reps: Optional[int] = None


class BenchmarkCreate(BaseModel):
    date: Optional[str] = None
    lifts: List[BenchmarkLift] = Field(default_factory=list)
    cmj_cm: Optional[float] = None            # countermovement jump height
    broad_jump_cm: Optional[float] = None
    single_leg_hop_left_cm: Optional[float] = None
    single_leg_hop_right_cm: Optional[float] = None
    visa_p: Optional[int] = None              # patellar tendon questionnaire (0-100)
    visa_a: Optional[int] = None              # achilles tendon questionnaire (0-100)
    notes: Optional[str] = None


class CoachSubscription(BaseModel):
    id: str
    coach_id: str
    client_id: str
    status: str = "active"  # active, cancelled, past_due
    monthly_price: float = 0.0
    currency: str = "USD"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

import { create } from 'zustand';

interface FitnessAssessment {
  pushups: number;
  pullups: number;
  squats: number;
  plank: number;
  runPace: string;
}

interface SportDetail {
  sport: string;
  role?: string;
}

interface OnboardingData {
  onboarding_version: number;
  onboarding_completed_at: string;
  goals: string[];
  selected_goals: string[];
  primary_goal: string;
  experience: string;
  training_location: string;
  equipment: string[];
  fitness_assessment: FitnessAssessment;
  sports: string[];
  sport_details: SportDetail[];
  competition_level: string;
  season_phase: string;
  gender: string;
  date_of_birth: string;
  height_cm: number | null;
  weight_kg: number | null;
  target_weight_kg: number | null;
  country: string;
  city: string;
  training_days_per_week: number;
  preferred_training_days: string[];
  session_duration_min: number;
  preferred_training_time: string;
  schedule_constraints: string;
  current_injuries: { area: string; note: string }[];
  pain_areas: string[];
  medical_notes: string;
  sleep_avg_hours: number | null;
  stress_level: string;
  diet_preference: string;
  dietary_restrictions: string[];
  nutrition_goal: string;
}

interface OnboardingState {
  goals: string[];
  experience: string;
  location: string;
  equipment: string[];
  fitnessAssessment: FitnessAssessment;
  sports: string[];
  selectedGoals: string[];
  primaryGoal: string;
  gender: string;
  dateOfBirth: string;
  heightCm: string;
  weightKg: string;
  targetWeightKg: string;
  country: string;
  city: string;
  sportDetails: SportDetail[];
  competitionLevel: string;
  seasonPhase: string;
  trainingDaysPerWeek: number;
  preferredTrainingDays: string[];
  sessionDurationMin: number;
  preferredTrainingTime: string;
  scheduleConstraints: string;
  currentInjuries: { area: string; note: string }[];
  painAreas: string[];
  medicalNotes: string;
  sleepAvgHours: string;
  stressLevel: string;
  dietPreference: string;
  dietaryRestrictions: string[];
  nutritionGoal: string;
  
  setGoals: (goals: string[]) => void;
  setExperience: (experience: string) => void;
  setLocation: (location: string) => void;
  setEquipment: (equipment: string[]) => void;
  setFitnessAssessment: (assessment: FitnessAssessment) => void;
  setSports: (sports: string[]) => void;
  setSelectedGoals: (goals: string[]) => void;
  setPrimaryGoal: (goal: string) => void;
  setBodyProfile: (data: Partial<Pick<OnboardingState, 'gender' | 'dateOfBirth' | 'heightCm' | 'weightKg' | 'targetWeightKg' | 'country' | 'city'>>) => void;
  setSportContext: (data: Partial<Pick<OnboardingState, 'sportDetails' | 'competitionLevel' | 'seasonPhase'>>) => void;
  setSchedule: (data: Partial<Pick<OnboardingState, 'trainingDaysPerWeek' | 'preferredTrainingDays' | 'sessionDurationMin' | 'preferredTrainingTime' | 'scheduleConstraints'>>) => void;
  setHealthContext: (data: Partial<Pick<OnboardingState, 'currentInjuries' | 'painAreas' | 'medicalNotes' | 'sleepAvgHours' | 'stressLevel' | 'dietPreference' | 'dietaryRestrictions' | 'nutritionGoal'>>) => void;
  reset: () => void;
  getOnboardingData: () => OnboardingData;
}

const initialState: Pick<
  OnboardingState,
  'goals' | 'experience' | 'location' | 'equipment' | 'fitnessAssessment' | 'sports' | 'selectedGoals' |
  'primaryGoal' | 'gender' | 'dateOfBirth' | 'heightCm' | 'weightKg' | 'targetWeightKg' | 'country' | 'city' |
  'sportDetails' | 'competitionLevel' | 'seasonPhase' | 'trainingDaysPerWeek' | 'preferredTrainingDays' |
  'sessionDurationMin' | 'preferredTrainingTime' | 'scheduleConstraints' | 'currentInjuries' | 'painAreas' |
  'medicalNotes' | 'sleepAvgHours' | 'stressLevel' | 'dietPreference' | 'dietaryRestrictions' | 'nutritionGoal'
> = {
  goals: [],
  experience: '',
  location: '',
  equipment: [],
  fitnessAssessment: {
    pushups: 0,
    pullups: 0,
    squats: 0,
    plank: 0,
    runPace: '',
  },
  sports: [],
  selectedGoals: [],
  primaryGoal: '',
  gender: '',
  dateOfBirth: '',
  heightCm: '',
  weightKg: '',
  targetWeightKg: '',
  country: '',
  city: '',
  sportDetails: [],
  competitionLevel: 'recreational',
  seasonPhase: 'general',
  trainingDaysPerWeek: 4,
  preferredTrainingDays: [],
  sessionDurationMin: 45,
  preferredTrainingTime: 'evening',
  scheduleConstraints: '',
  currentInjuries: [],
  painAreas: [],
  medicalNotes: '',
  sleepAvgHours: '',
  stressLevel: 'moderate',
  dietPreference: '',
  dietaryRestrictions: [],
  nutritionGoal: '',
};

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  ...initialState,

  setGoals: (goals) => set({ goals }),
  setSelectedGoals: (selectedGoals) => set({ selectedGoals }),
  setPrimaryGoal: (primaryGoal) => set({ primaryGoal }),
  setExperience: (experience) => set({ experience }),
  setLocation: (location) => set({ location }),
  setEquipment: (equipment) => set({ equipment }),
  setFitnessAssessment: (fitnessAssessment) => set({ fitnessAssessment }),
  setSports: (sports) => set({ sports }),
  setBodyProfile: (data) => set(data),
  setSportContext: (data) => set(data),
  setSchedule: (data) => set(data),
  setHealthContext: (data) => set(data),
  reset: () => set(initialState),
  
  getOnboardingData: () => {
    const state = get();
    const toNumber = (value: string) => {
      const parsed = Number(value);
      return Number.isFinite(parsed) && value.trim() !== '' ? parsed : null;
    };
    const primaryGoal = state.primaryGoal || state.selectedGoals[0] || state.goals[0] || '';
    return {
      onboarding_version: 2,
      onboarding_completed_at: new Date().toISOString(),
      goals: state.goals,
      selected_goals: state.selectedGoals,
      primary_goal: primaryGoal,
      experience: state.experience,
      training_location: state.location,
      equipment: state.equipment,
      fitness_assessment: state.fitnessAssessment,
      sports: state.sports,
      sport_details: state.sportDetails,
      competition_level: state.competitionLevel,
      season_phase: state.seasonPhase,
      gender: state.gender,
      date_of_birth: state.dateOfBirth,
      height_cm: toNumber(state.heightCm),
      weight_kg: toNumber(state.weightKg),
      target_weight_kg: toNumber(state.targetWeightKg),
      country: state.country,
      city: state.city,
      training_days_per_week: state.trainingDaysPerWeek,
      preferred_training_days: state.preferredTrainingDays,
      session_duration_min: state.sessionDurationMin,
      preferred_training_time: state.preferredTrainingTime,
      schedule_constraints: state.scheduleConstraints,
      current_injuries: state.currentInjuries,
      pain_areas: state.painAreas,
      medical_notes: state.medicalNotes,
      sleep_avg_hours: toNumber(state.sleepAvgHours),
      stress_level: state.stressLevel,
      diet_preference: state.dietPreference,
      dietary_restrictions: state.dietaryRestrictions,
      nutrition_goal: state.nutritionGoal,
    };
  },
}));

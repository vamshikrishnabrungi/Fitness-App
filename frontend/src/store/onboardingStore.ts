import { create } from 'zustand';

export type RunnerLevel = 'beginner' | 'intermediate' | 'advanced';
export type DistanceUnit = 'km' | 'mi';
export type DayAvailability = { day: string; minutes: number; preferredTime: 'morning' | 'afternoon' | 'evening' };

export interface RunnerOnboardingData {
  onboarding_version: 3;
  goal_type: string;
  target_event: string | null;
  target_distance: number | null;
  target_date: string | null;
  target_time: string;
  distance_unit: DistanceUnit;
  experience_level: RunnerLevel;
  runs_per_week: number;
  weekly_distance: number;
  longest_recent_run: number;
  recent_race_event: string | null;
  recent_race_time: string;
  training_interruption: string;
  gender: string;
  date_of_birth: string;
  height_cm: number | null;
  weight_kg: number | null;
  target_weight_kg: number | null;
  country: string;
  city: string;
  availability: DayAvailability[];
  start_date: string;
  schedule_constraints: string;
  terrains: string[];
  strength_access: 'full_gym' | 'home_equipment' | 'bodyweight';
  equipment: string[];
  pain_areas: string[];
  medical_notes: string;
  stress_level: string;
  diet_preference: string;
  nutrition_goal: string;
}

interface OnboardingState extends Omit<RunnerOnboardingData, 'onboarding_version' | 'height_cm' | 'weight_kg' | 'target_weight_kg'> {
  height_cm: string;
  weight_kg: string;
  target_weight_kg: string;
  setGoal: (data: Partial<Pick<OnboardingState, 'goal_type' | 'target_event' | 'target_distance' | 'target_date' | 'target_time' | 'distance_unit'>>) => void;
  setBaseline: (data: Partial<Pick<OnboardingState, 'experience_level' | 'runs_per_week' | 'weekly_distance' | 'longest_recent_run' | 'recent_race_event' | 'recent_race_time' | 'training_interruption'>>) => void;
  setBodyProfile: (data: Partial<Pick<OnboardingState, 'gender' | 'date_of_birth' | 'height_cm' | 'weight_kg' | 'target_weight_kg' | 'country' | 'city'>>) => void;
  setSchedule: (data: Partial<Pick<OnboardingState, 'availability' | 'start_date' | 'schedule_constraints'>>) => void;
  setAccess: (data: Partial<Pick<OnboardingState, 'terrains' | 'strength_access' | 'equipment'>>) => void;
  setHealth: (data: Partial<Pick<OnboardingState, 'pain_areas' | 'medical_notes' | 'stress_level' | 'diet_preference' | 'nutrition_goal'>>) => void;
  reset: () => void;
  getOnboardingData: () => RunnerOnboardingData;
}

const initialState = {
  goal_type: '', target_event: null, target_distance: null, target_date: null, target_time: '', distance_unit: 'km' as DistanceUnit,
  experience_level: 'beginner' as RunnerLevel, runs_per_week: 0, weekly_distance: 0, longest_recent_run: 0,
  recent_race_event: null, recent_race_time: '', training_interruption: 'none',
  gender: '', date_of_birth: '', height_cm: '', weight_kg: '', target_weight_kg: '', country: '', city: '',
  availability: [] as DayAvailability[], start_date: '', schedule_constraints: '',
  terrains: ['road'], strength_access: 'bodyweight' as const, equipment: ['bodyweight'],
  pain_areas: [] as string[], medical_notes: '', stress_level: 'moderate', diet_preference: 'balanced', nutrition_goal: 'performance',
};

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  ...initialState,
  setGoal: data => set(data), setBaseline: data => set(data), setBodyProfile: data => set(data),
  setSchedule: data => set(data), setAccess: data => set(data), setHealth: data => set(data),
  reset: () => set(initialState),
  getOnboardingData: () => {
    const state = get();
    const numberOrNull = (value: string) => value.trim() && Number.isFinite(Number(value)) ? Number(value) : null;
    return {
      onboarding_version: 3, goal_type: state.goal_type, target_event: state.target_event,
      target_distance: state.target_distance, target_date: state.target_date, target_time: state.target_time,
      distance_unit: state.distance_unit, experience_level: state.experience_level, runs_per_week: state.runs_per_week,
      weekly_distance: state.weekly_distance, longest_recent_run: state.longest_recent_run,
      recent_race_event: state.recent_race_event, recent_race_time: state.recent_race_time,
      training_interruption: state.training_interruption, gender: state.gender, date_of_birth: state.date_of_birth,
      height_cm: numberOrNull(state.height_cm), weight_kg: numberOrNull(state.weight_kg), target_weight_kg: numberOrNull(state.target_weight_kg),
      country: state.country, city: state.city, availability: state.availability,
      start_date: state.start_date || new Date().toISOString().slice(0, 10), schedule_constraints: state.schedule_constraints,
      terrains: state.terrains, strength_access: state.strength_access, equipment: state.equipment,
      pain_areas: state.pain_areas, medical_notes: state.medical_notes, stress_level: state.stress_level,
      diet_preference: state.diet_preference, nutrition_goal: state.nutrition_goal,
    };
  },
}));

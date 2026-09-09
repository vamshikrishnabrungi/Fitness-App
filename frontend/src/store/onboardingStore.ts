import { create } from 'zustand';

export type RunnerLevel = 'beginner' | 'intermediate' | 'advanced';
export type DistanceUnit = 'km' | 'mi';
export type DayAvailability = { day: string; minutes: number; preferredTime: 'morning' | 'afternoon' | 'evening' };

export interface RunnerOnboardingData {
  onboarding_version: 4;
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
  training_interruption: string;
  height_cm: number | null;
  weight_kg: number | null;
  availability: DayAvailability[];
  schedule_constraints: string;
  terrains: string[];
  strength_access: 'full_gym' | 'home_equipment' | 'bodyweight';
  equipment: string[];
  pain_areas: string[];
  medical_notes: string;
  stress_level: string;
}

interface OnboardingState extends Omit<RunnerOnboardingData, 'onboarding_version' | 'height_cm' | 'weight_kg'> {
  height_cm: string;
  weight_kg: string;
  setGoal: (data: Partial<Pick<OnboardingState, 'goal_type' | 'target_event' | 'target_distance' | 'target_date' | 'target_time' | 'distance_unit'>>) => void;
  setBaseline: (data: Partial<Pick<OnboardingState, 'experience_level' | 'runs_per_week' | 'weekly_distance' | 'longest_recent_run' | 'training_interruption'>>) => void;
  setScheduleAndAccess: (data: Partial<Pick<OnboardingState, 'availability' | 'schedule_constraints' | 'terrains' | 'strength_access' | 'equipment'>>) => void;
  setHealth: (data: Partial<Pick<OnboardingState, 'height_cm' | 'weight_kg' | 'pain_areas' | 'medical_notes' | 'stress_level'>>) => void;
  reset: () => void;
  getOnboardingData: () => RunnerOnboardingData;
}

const initialState = {
  goal_type: '', target_event: null, target_distance: null, target_date: null, target_time: '', distance_unit: 'km' as DistanceUnit,
  experience_level: 'beginner' as RunnerLevel, runs_per_week: 0, weekly_distance: 0, longest_recent_run: 0,
  training_interruption: 'none', height_cm: '', weight_kg: '', availability: [] as DayAvailability[], schedule_constraints: '',
  terrains: ['road'], strength_access: 'bodyweight' as const, equipment: ['bodyweight'],
  pain_areas: [] as string[], medical_notes: '', stress_level: 'moderate',
};

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  ...initialState,
  setGoal: data => set(data), setBaseline: data => set(data), setScheduleAndAccess: data => set(data), setHealth: data => set(data),
  reset: () => set(initialState),
  getOnboardingData: () => {
    const state = get();
    const numberOrNull = (value: string) => value.trim() && Number.isFinite(Number(value)) ? Number(value) : null;
    return {
      onboarding_version: 4, goal_type: state.goal_type, target_event: state.target_event,
      target_distance: state.target_distance, target_date: state.target_date, target_time: state.target_time,
      distance_unit: state.distance_unit, experience_level: state.experience_level, runs_per_week: state.runs_per_week,
      weekly_distance: state.weekly_distance, longest_recent_run: state.longest_recent_run,
      training_interruption: state.training_interruption, height_cm: numberOrNull(state.height_cm), weight_kg: numberOrNull(state.weight_kg),
      availability: state.availability, schedule_constraints: state.schedule_constraints, terrains: state.terrains,
      strength_access: state.strength_access, equipment: state.equipment, pain_areas: state.pain_areas,
      medical_notes: state.medical_notes, stress_level: state.stress_level,
    };
  },
}));

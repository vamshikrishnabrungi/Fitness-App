import { create } from 'zustand';

export type RunnerLevel = 'beginner' | 'intermediate' | 'advanced';
export type DistanceUnit = 'km' | 'mi';
export type DayAvailability = { day: string; minutes: number };

export interface RunnerOnboardingData {
  onboarding_version: 4;
  goal_type: string;
  target_event: string | null;
  target_distance: number | null;
  target_date: string | null;
  target_time: string;
  current_time: string;
  distance_unit: DistanceUnit;
  experience_level: RunnerLevel;
  runs_per_week: number;
  weekly_distance: number;
  longest_recent_run: number;
  training_interruption: string;
  availability: DayAvailability[];
  schedule_constraints: string;
  terrains: string[];
  strength_access: 'full_gym' | 'home_equipment' | 'bodyweight';
  equipment: string[];
  pain_areas: string[];
}

interface OnboardingState extends Omit<RunnerOnboardingData, 'onboarding_version'> {
  setGoal: (data: Partial<Pick<OnboardingState, 'goal_type' | 'target_event' | 'target_distance' | 'target_date' | 'target_time' | 'current_time' | 'distance_unit'>>) => void;
  setBaseline: (data: Partial<Pick<OnboardingState, 'experience_level' | 'runs_per_week' | 'weekly_distance' | 'longest_recent_run' | 'training_interruption'>>) => void;
  setScheduleAndAccess: (data: Partial<Pick<OnboardingState, 'availability' | 'schedule_constraints' | 'terrains' | 'strength_access' | 'equipment'>>) => void;
  setHealth: (data: Partial<Pick<OnboardingState, 'pain_areas'>>) => void;
  reset: () => void;
  getOnboardingData: () => RunnerOnboardingData;
}

const initialState = {
  goal_type: '', target_event: null, target_distance: null, target_date: null, target_time: '', current_time: '', distance_unit: 'km' as DistanceUnit,
  experience_level: 'beginner' as RunnerLevel, runs_per_week: 0, weekly_distance: 0, longest_recent_run: 0,
  training_interruption: 'none', availability: [] as DayAvailability[], schedule_constraints: '',
  terrains: ['road'], strength_access: 'bodyweight' as const, equipment: ['bodyweight'],
  pain_areas: [] as string[],
};

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  ...initialState,
  setGoal: data => set(data), setBaseline: data => set(data), setScheduleAndAccess: data => set(data), setHealth: data => set(data),
  reset: () => set(initialState),
  getOnboardingData: () => {
    const state = get();
    return {
      onboarding_version: 4, goal_type: state.goal_type, target_event: state.target_event,
      target_distance: state.target_distance, target_date: state.target_date, target_time: state.target_time, current_time: state.current_time,
      distance_unit: state.distance_unit, experience_level: state.experience_level, runs_per_week: state.runs_per_week,
      weekly_distance: state.weekly_distance, longest_recent_run: state.longest_recent_run,
      training_interruption: state.training_interruption,
      availability: state.availability, schedule_constraints: state.schedule_constraints, terrains: state.terrains,
      strength_access: state.strength_access, equipment: state.equipment, pain_areas: state.pain_areas,
    };
  },
}));

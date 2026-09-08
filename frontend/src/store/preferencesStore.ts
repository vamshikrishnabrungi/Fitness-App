import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import { api } from '../utils/api';

export type DistanceUnit = 'km' | 'mi';
const KEY = 'distance_unit';

interface PreferencesState {
  distanceUnit: DistanceUnit;
  load: (authenticated: boolean) => Promise<void>;
  setDistanceUnit: (unit: DistanceUnit) => Promise<void>;
}

export const usePreferencesStore = create<PreferencesState>((set) => ({
  distanceUnit: 'km',
  load: async (authenticated) => {
    const cached = await AsyncStorage.getItem(KEY);
    if (cached === 'km' || cached === 'mi') set({ distanceUnit: cached });
    if (!authenticated) return;
    try {
      const profile = await api.get<{ distance_unit: DistanceUnit }>('/athletes/me');
      await AsyncStorage.setItem(KEY, profile.distance_unit);
      set({ distanceUnit: profile.distance_unit });
    } catch {
      // The cached preference remains usable while offline or before onboarding.
    }
  },
  setDistanceUnit: async (distanceUnit) => {
    await AsyncStorage.setItem(KEY, distanceUnit);
    set({ distanceUnit });
  },
}));

export const distanceFromKm = (kilometres: number, unit: DistanceUnit) =>
  unit === 'mi' ? kilometres / 1.609344 : kilometres;

export const distanceLabel = (kilometres: number, unit: DistanceUnit, digits = 2) =>
  `${distanceFromKm(kilometres, unit).toFixed(digits)} ${unit}`;

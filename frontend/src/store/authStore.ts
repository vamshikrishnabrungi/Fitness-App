import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../utils/api';

interface User {
  id: string;
  email: string;
  name: string;
  profile: {
    sport?: string;
    goals?: string[];
    equipment?: string[];
    fitness_level?: string;
    weight_kg?: number;
    height_cm?: number;
    weight?: number;
    height?: number;
    age?: number;
    city?: string;
    country?: string;
    weekly_goal_km?: number;
    date_of_birth?: string;
    marketing_opt_in?: boolean;
  };
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithOtp: (email: string, code: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    name: string,
    otpCode?: string,
    profile?: User['profile']
  ) => Promise<void>;
  logout: () => Promise<void>;
  loadAuth: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  clearOnboardingFlag: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await api.post<{ access_token: string; user: User }>('/auth/login', {
      email,
      password,
    });
    
    await AsyncStorage.setItem('auth_token', response.access_token);
    set({ user: response.user, token: response.access_token, isAuthenticated: true });
  },

  loginWithOtp: async (email: string, code: string) => {
    const response = await api.post<{ access_token: string; user: User }>('/auth/login-otp', {
      email,
      code,
    });
    
    await AsyncStorage.setItem('auth_token', response.access_token);
    set({ user: response.user, token: response.access_token, isAuthenticated: true });
  },

  register: async (email: string, password: string, name: string, otpCode?: string, profile?: User['profile']) => {
    const response = await api.post<{ access_token: string; user: User }>('/auth/register', {
      email,
      password,
      name,
      otp_code: otpCode,
      profile,
    });
    
    await AsyncStorage.setItem('auth_token', response.access_token);
    await AsyncStorage.setItem('needs_onboarding', 'true');
    set({ user: response.user, token: response.access_token, isAuthenticated: true });
  },

  logout: async () => {
    await AsyncStorage.removeItem('auth_token');
    set({ user: null, token: null, isAuthenticated: false });
  },

  loadAuth: async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        const user = await api.get<User>('/auth/me');
        set({ user, token, isAuthenticated: true, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      await AsyncStorage.removeItem('auth_token');
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearOnboardingFlag: async () => {
    await AsyncStorage.removeItem('needs_onboarding');
  },

  updateProfile: async (data: Partial<User>) => {
    const response = await api.put<User>('/auth/profile', data);
    set({ user: response });
  },
}));

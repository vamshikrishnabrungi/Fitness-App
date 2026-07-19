import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, ApiError } from '../utils/api';

// The user profile is cached next to the token so a launch that can't reach the
// API still renders the real account instead of an empty placeholder.
const CACHED_USER_KEY = 'auth_user';

const persistSession = async (token: string, user: unknown) => {
  await AsyncStorage.multiSet([
    ['auth_token', token],
    [CACHED_USER_KEY, JSON.stringify(user)],
  ]);
};

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
    
    await persistSession(response.access_token, response.user);
    set({ user: response.user, token: response.access_token, isAuthenticated: true });
  },

  loginWithOtp: async (email: string, code: string) => {
    const response = await api.post<{ access_token: string; user: User }>('/auth/login-otp', {
      email,
      code,
    });
    
    await persistSession(response.access_token, response.user);
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
    
    await persistSession(response.access_token, response.user);
    await AsyncStorage.setItem('needs_onboarding', 'true');
    set({ user: response.user, token: response.access_token, isAuthenticated: true });
  },

  logout: async () => {
    await AsyncStorage.multiRemove(['auth_token', CACHED_USER_KEY]);
    set({ user: null, token: null, isAuthenticated: false });
  },

  loadAuth: async () => {
    const token = await AsyncStorage.getItem('auth_token');
    if (!token) {
      set({ isLoading: false });
      return;
    }
    try {
      const user = await api.get<User>('/auth/me');
      await AsyncStorage.setItem(CACHED_USER_KEY, JSON.stringify(user));
      set({ user, token, isAuthenticated: true, isLoading: false });
    } catch (error) {
      // Only discard the session when the server actually rejected the token.
      // A network failure (backend down, no signal, changed IP) must NOT log the
      // user out — that previously wiped a perfectly valid session on every
      // launch that couldn't reach the API.
      if (error instanceof ApiError && !error.isAuthError) {
        const cached = await AsyncStorage.getItem(CACHED_USER_KEY);
        set({
          user: cached ? JSON.parse(cached) : null,
          token,
          isAuthenticated: true,
          isLoading: false,
        });
        return;
      }
      await AsyncStorage.removeItem('auth_token');
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearOnboardingFlag: async () => {
    await AsyncStorage.removeItem('needs_onboarding');
  },

  updateProfile: async (data: Partial<User>) => {
    const response = await api.put<User>('/auth/profile', data);
    await AsyncStorage.setItem(CACHED_USER_KEY, JSON.stringify(response));
    set({ user: response });
  },
}));

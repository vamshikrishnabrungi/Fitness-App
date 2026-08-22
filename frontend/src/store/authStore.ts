import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, ApiError } from '../utils/api';

// The user profile is cached next to the token so a launch that can't reach the
// API still renders the real account instead of an empty placeholder.
const CACHED_USER_KEY = 'auth_user';

const persistSession = async (token: string, refreshToken: string, user: unknown) => {
  await AsyncStorage.multiSet([
    ['auth_token', token],
    ['refresh_token', refreshToken],
    [CACHED_USER_KEY, JSON.stringify(user)],
  ]);
};

interface User {
  id: string;
  email: string;
  display_name: string;
  name: string;
  onboarding_completed: boolean;
  birth_date?: string;
  roles: string[];
  version: number;
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
  loginWithOtp: (challengeId: string, email: string, code: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    name: string,
    otpCode?: string,
    challengeId?: string,
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

  login: async () => {
    throw new ApiError('Runlete uses secure email codes; password sign-in is not enabled.', 400);
  },

  loginWithOtp: async (challengeId: string, email: string, code: string) => {
    const response = await api.post<{ access_token: string; refresh_token: string; user: User }>('/auth/otp/verify', {
      challenge_id: challengeId,
      email,
      code,
    });
    const user = { ...response.user, name: response.user.display_name };
    await persistSession(response.access_token, response.refresh_token, user);
    set({ user, token: response.access_token, isAuthenticated: true });
  },

  register: async (email: string, _password: string, name: string, otpCode?: string, challengeId?: string, profile?: User['profile']) => {
    if (!challengeId || !otpCode || !profile?.date_of_birth) throw new ApiError('Verification code and birth date are required.', 422);
    const response = await api.post<{ access_token: string; refresh_token: string; user: User }>('/auth/otp/verify', {
      challenge_id: challengeId,
      email,
      code: otpCode,
      display_name: name,
      birth_date: profile.date_of_birth,
    });
    const user = { ...response.user, name: response.user.display_name };
    await persistSession(response.access_token, response.refresh_token, user);
    await AsyncStorage.setItem('needs_onboarding', 'true');
    set({ user, token: response.access_token, isAuthenticated: true });
  },

  logout: async () => {
    await AsyncStorage.multiRemove(['auth_token', 'refresh_token', CACHED_USER_KEY]);
    set({ user: null, token: null, isAuthenticated: false });
  },

  loadAuth: async () => {
    const token = await AsyncStorage.getItem('auth_token');
    if (!token) {
      set({ isLoading: false });
      return;
    }
    try {
      const raw = await api.get<User>('/auth/me');
      const user = { ...raw, name: raw.display_name };
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
      await AsyncStorage.multiRemove(['auth_token', 'refresh_token']);
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearOnboardingFlag: async () => {
    await AsyncStorage.removeItem('needs_onboarding');
  },

  updateProfile: async (data: Partial<User>) => {
    const current = get().user;
    const response = await api.patch<User>('/auth/me', { display_name: data.display_name ?? data.name, expected_version: current?.version ?? 1 });
    const user = { ...response, name: response.display_name };
    await AsyncStorage.setItem(CACHED_USER_KEY, JSON.stringify(user));
    set({ user });
  },
}));

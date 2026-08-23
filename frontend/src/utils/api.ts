import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Use the backend URL from environment
const BACKEND_URL = (process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');

const getDevHost = () => {
  const hostUri =
    Constants.expoConfig?.hostUri ||
    Constants.expoConfig?.hostUri ||
    (Constants as any).manifest?.debuggerHost ||
    (Constants as any).manifest2?.extra?.expoClient?.hostUri;

  if (!hostUri) return null;
  const host = hostUri.split('://').pop()?.split('/')[0]?.split(':')[0];
  return host || null;
};

/** Thrown by ApiClient so callers can tell "server rejected me" from "server unreachable". */
export class ApiError extends Error {
  constructor(message: string, readonly status: number | null) {
    super(message);
    this.name = 'ApiError';
  }
  /** No HTTP response at all — DNS/offline/wrong host. The token is still probably fine. */
  get isNetworkError() { return this.status === null; }
  /** Server answered and refused the credentials. */
  get isAuthError() { return this.status === 401 || this.status === 403; }
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    // For local development on web, use the full backend URL
    // For production or mobile, use relative URLs (proxied by ingress)
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      this.baseUrl = 'http://localhost:8000/api/v1';
    } else if (Platform.OS !== 'web') {
      // Prefer the dev machine's *current* address, which Metro reports, over a
      // hardcoded EXPO_PUBLIC_BACKEND_URL — DHCP reassigns it and a stale value
      // means every request fails with "Network request failed". Falls back to
      // the env var (needed for real builds, where there is no Metro host).
      const devHost = __DEV__ ? getDevHost() : null;
      if (devHost) {
        this.baseUrl = `http://${devHost}:8000/api/v1`;
      } else if (BACKEND_URL) {
        this.baseUrl = `${BACKEND_URL}/api/v1`;
      } else {
        this.baseUrl = '/api/v1';
      }
    } else if (BACKEND_URL) {
      this.baseUrl = `${BACKEND_URL}/api/v1`;
    } else {
      this.baseUrl = '/api/v1';
    }
  }

  private async getToken(): Promise<string | null> {
    return await AsyncStorage.getItem('auth_token');
  }

  private mutationHeaders(headers?: HeadersInit): HeadersInit {
    const resolved = { ...(headers || {}) } as Record<string, string>;
    if (!resolved['Idempotency-Key']) {
      resolved['Idempotency-Key'] = `mobile-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    }
    return resolved;
  }

  absoluteUrl(endpoint: string): string {
    return `${this.baseUrl}${endpoint}`;
  }

  async request<T>(endpoint: string, options: RequestInit = {}, retryAuth = true): Promise<T> {
    const token = await this.getToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    } catch (e) {
      // fetch only rejects when the request never completed (offline, bad host).
      // status stays null so callers don't mistake this for a rejected token.
      throw new ApiError(e instanceof Error ? e.message : 'Network request failed', null);
    }

    if (response.status === 401 && retryAuth && !endpoint.startsWith('/auth/')) {
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const refreshed = await this.post<{ access_token: string; refresh_token: string }>('/auth/refresh', { refresh_token: refreshToken }, undefined, false);
          await AsyncStorage.multiSet([['auth_token', refreshed.access_token], ['refresh_token', refreshed.refresh_token]]);
          return this.request<T>(endpoint, options, false);
        } catch { /* fall through to the original authorization error */ }
      }
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new ApiError(error.detail || 'Request failed', response.status);
    }

    if (response.status === 204) return undefined as T;
    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, headers?: HeadersInit, retryAuth = true): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers: this.mutationHeaders(headers),
    }, retryAuth);
  }

  async put<T>(endpoint: string, data?: any, headers?: HeadersInit): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      headers: this.mutationHeaders(headers),
    });
  }

  async patch<T>(endpoint: string, data?: any, headers?: HeadersInit): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      headers: this.mutationHeaders(headers),
    });
  }

  async delete<T>(endpoint: string, headers?: HeadersInit): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE', headers: this.mutationHeaders(headers) });
  }
}

export const api = new ApiClient();

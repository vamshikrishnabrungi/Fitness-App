import { tokenStorage } from '../services/tokenStorage';

const BACKEND_URL = (process.env.EXPO_PUBLIC_BACKEND_URL || '').replace(/\/$/, '');
const API_TIMEOUT_MS = 20_000;

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

export const apiErrorMessage = (error: unknown, fallback = 'Something went wrong. Please try again.') =>
  error instanceof Error && error.message ? error.message : fallback;

class ApiClient {
  private baseUrl: string;
  private refreshPromise: Promise<boolean> | null = null;
  private pendingGets = new Map<string, Promise<unknown>>();

  constructor() {
    if (!BACKEND_URL) throw new Error('EXPO_PUBLIC_BACKEND_URL is required');
    this.baseUrl = `${BACKEND_URL}/api/v1`;
  }

  private async getToken(): Promise<string | null> {
    return tokenStorage.getAccessToken();
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

  private refreshSession(): Promise<boolean> {
    if (this.refreshPromise) return this.refreshPromise;
    this.refreshPromise = (async () => {
      const refreshToken = await tokenStorage.getRefreshToken();
      if (!refreshToken) return false;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
      try {
        const response = await fetch(`${this.baseUrl}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Idempotency-Key': `refresh-${Date.now()}-${Math.random().toString(36).slice(2)}` },
          body: JSON.stringify({ refresh_token: refreshToken }),
          signal: controller.signal,
        });
        if (!response.ok) return false;
        const refreshed = await response.json() as { access_token: string; refresh_token: string };
        await tokenStorage.setSession(refreshed.access_token, refreshed.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        clearTimeout(timeout);
        this.refreshPromise = null;
      }
    })();
    return this.refreshPromise;
  }

  async request<T>(endpoint: string, options: RequestInit = {}, retryAuth = true, timeoutMs = API_TIMEOUT_MS): Promise<T> {
    const token = await this.getToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    let response: Response;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    const upstreamSignal = options.signal;
    const abortFromUpstream = () => controller.abort();
    upstreamSignal?.addEventListener('abort', abortFromUpstream, { once: true });
    try {
      response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers, signal: controller.signal });
    } catch (e) {
      // fetch only rejects when the request never completed (offline, bad host).
      // status stays null so callers don't mistake this for a rejected token.
      throw new ApiError(
        controller.signal.aborted && !upstreamSignal?.aborted
          ? 'The server took too long to respond.'
          : e instanceof Error ? e.message : 'Network request failed',
        null,
      );
    } finally {
      clearTimeout(timeout);
      upstreamSignal?.removeEventListener('abort', abortFromUpstream);
    }

    if (response.status === 401 && retryAuth && !endpoint.startsWith('/auth/')) {
      if (await this.refreshSession()) return this.request<T>(endpoint, options, false, timeoutMs);
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' })) as {
        detail?: unknown;
        title?: unknown;
      };
      const detail = typeof error.detail === 'string'
        ? error.detail
        : typeof error.title === 'string'
          ? error.title
          : 'Request failed';
      throw new ApiError(detail, response.status);
    }

    if (response.status === 204) return undefined as T;
    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    const existing = this.pendingGets.get(endpoint) as Promise<T> | undefined;
    if (existing) return existing;
    const request = this.request<T>(endpoint, { method: 'GET' });
    this.pendingGets.set(endpoint, request);
    try {
      return await request;
    } finally {
      if (this.pendingGets.get(endpoint) === request) this.pendingGets.delete(endpoint);
    }
  }

  async post<T>(endpoint: string, data?: any, headers?: HeadersInit, retryAuth = true): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers: this.mutationHeaders(headers),
    }, retryAuth);
  }

  async postLongRunning<T>(endpoint: string, data?: any, timeoutMs = 300_000): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers: this.mutationHeaders(),
    }, true, timeoutMs);
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

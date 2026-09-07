import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import * as Crypto from 'expo-crypto';
import { Platform } from 'react-native';
import { api } from '../utils/api';
import {
  acceptAndSmoothPoint,
  GPS_SAMPLE_INTERVAL_MS,
} from './activityMetrics';

export const RUN_LOCATION_TASK = 'runlete-active-run-location-v1';
export const ACTIVE_RUN_KEY = 'runlete_active_run_v2';
export const PENDING_RUNS_KEY = 'runlete_pending_runs_v2';
export const LIVE_LOCATION_KEY = 'runlete_live_location_v1';

const AUTO_PAUSE_AFTER_MS = 10_000;
const AUTO_RESUME_SPEED_MPS = 0.8;
const AUTO_PAUSE_SPEED_MPS = 0.5;
const MAX_STORED_POINTS = 50_000;
const UPLOAD_CHUNK_SIZE = 250;
const UPLOAD_CHUNK_THRESHOLD = 50;

export type RunSessionState = 'recording' | 'paused' | 'finishing';

export interface RecordedPoint {
  latitude: number;
  longitude: number;
  timestamp: string;
  altitude?: number;
  speed?: number;
  accuracy?: number;
  heart_rate?: number;
  cadence?: number;
  smoothed_latitude?: number;
  smoothed_longitude?: number;
  metric_accepted?: boolean;
}

export interface PersistedRunSession {
  id: string;
  idempotencyKey: string;
  state: RunSessionState;
  startedAt: string;
  updatedAt: string;
  pausedDurationSec: number;
  manualPausedAt?: string;
  autoPausedAt?: string;
  slowSince?: string;
  autoPauseEnabled: boolean;
  visibility: 'public' | 'club' | 'private';
  surface?: 'road' | 'trail' | 'park' | 'track';
  points: RecordedPoint[];
  uploadSessionId?: string;
  uploadedPointCount?: number;
  nextChunkSequence?: number;
  uploadVersion?: number;
}

export interface PendingRunUpload {
  session: PersistedRunSession;
  endedAt: string;
  queuedAt: string;
}

let writeQueue: Promise<void> = Promise.resolve();

interface LiveLocationSession {
  sessionId: string;
  expiresAt: string;
  lastPublishedAt?: string;
}

const makeSessionId = () =>
  `run-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const locationToPoint = (location: Location.LocationObject): RecordedPoint => ({
  latitude: location.coords.latitude,
  longitude: location.coords.longitude,
  timestamp: new Date(location.timestamp).toISOString(),
  altitude: location.coords.altitude ?? undefined,
  speed: location.coords.speed ?? undefined,
  accuracy: location.coords.accuracy ?? undefined,
});

const parseSession = (raw: string | null): PersistedRunSession | null => {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw);
    if (
      !value ||
      typeof value !== 'object' ||
      typeof value.id !== 'string' ||
      !Array.isArray(value.points)
    ) {
      return null;
    }
    return value as PersistedRunSession;
  } catch {
    return null;
  }
};

export const loadActiveRun = async (): Promise<PersistedRunSession | null> =>
  parseSession(await AsyncStorage.getItem(ACTIVE_RUN_KEY));

export const setLiveLocationSession = async (sessionId: string, expiresAt: string) => {
  const session: LiveLocationSession = { sessionId, expiresAt };
  await AsyncStorage.setItem(LIVE_LOCATION_KEY, JSON.stringify(session));
};

const loadLiveLocationSession = async (): Promise<LiveLocationSession | null> => {
  try {
    const raw = await AsyncStorage.getItem(LIVE_LOCATION_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw);
    return value?.sessionId && value?.expiresAt ? value : null;
  } catch {
    return null;
  }
};

const publishLiveLocation = async (point: RecordedPoint) => {
  const share = await loadLiveLocationSession();
  if (!share) return;
  const now = new Date(point.timestamp);
  if (new Date(share.expiresAt) <= now) {
    await AsyncStorage.removeItem(LIVE_LOCATION_KEY);
    return;
  }
  if (share.lastPublishedAt && now.getTime() - new Date(share.lastPublishedAt).getTime() < 10_000) {
    return;
  }
  try {
    await api.put(`/safety/live-location/${share.sessionId}`, {
      latitude: point.latitude,
      longitude: point.longitude,
      timestamp: point.timestamp,
      accuracy_m: point.accuracy,
    });
    share.lastPublishedAt = point.timestamp;
    await AsyncStorage.setItem(LIVE_LOCATION_KEY, JSON.stringify(share));
  } catch {
    // Recording must continue offline. A later point retries the live update.
  }
};

export const stopLiveLocationSession = async () => {
  const share = await loadLiveLocationSession();
  await AsyncStorage.removeItem(LIVE_LOCATION_KEY);
  if (!share) return;
  try {
    await api.delete(`/safety/live-location/${share.sessionId}`);
  } catch {
    // The server-side session expires even if the final stop cannot be delivered.
  }
};

const saveActiveRun = async (session: PersistedRunSession) => {
  await AsyncStorage.setItem(ACTIVE_RUN_KEY, JSON.stringify(session));
};

const syncRunChunks = async (
  session: PersistedRunSession,
  force = false,
): Promise<PersistedRunSession> => {
  let uploaded = session.uploadedPointCount ?? 0;
  if (uploaded >= session.points.length) return session;
  if (!force && session.points.length - uploaded < UPLOAD_CHUNK_THRESHOLD) return session;

  if (!session.uploadSessionId) {
    const upload = await api.post<{ id: string; version: number }>(
      '/activities',
      {
        started_at: session.startedAt,
        visibility: session.visibility ?? 'private',
        surface: session.surface ?? 'road',
      },
      { 'Idempotency-Key': session.idempotencyKey },
    );
    session.uploadSessionId = upload.id;
    session.uploadVersion = upload.version;
    session.nextChunkSequence = 0;
    await saveActiveRun(session);
  }

  while (uploaded < session.points.length) {
    const remaining = session.points.length - uploaded;
    if (!force && remaining < UPLOAD_CHUNK_THRESHOLD) break;
    const pointCount = Math.min(UPLOAD_CHUNK_SIZE, remaining);
    const sequence = session.nextChunkSequence ?? 0;
    const content = JSON.stringify({schema_version:1,sequence,points:session.points.slice(uploaded, uploaded + pointCount)});
    const contentHash = await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA256, content);
    const signed = await api.post<{upload_url:string}>(`/activities/${session.uploadSessionId}/chunks/upload-url`, {chunk_number:sequence,content_hash:contentHash,sample_count:pointCount,content_type:'application/json'});
    const uploadedResponse = await fetch(signed.upload_url, {method:'PUT',headers:{'Content-Type':'application/json'},body:content});
    if (!uploadedResponse.ok) throw new Error('GPS chunk upload failed');
    uploaded += pointCount;
    session.uploadedPointCount = uploaded;
    session.nextChunkSequence = sequence + 1;
    await saveActiveRun(session);
  }
  return session;
};

export const completeResumableRunUpload = async (
  session: PersistedRunSession,
  endedAt: string,
  deviceDistanceM?: number,
) => {
  const synced = await syncRunChunks(session, true);
  if (!synced.uploadSessionId || (synced.uploadedPointCount ?? 0) !== synced.points.length) {
    throw new Error('Run chunks are not fully uploaded');
  }
  const finished = await api.post<any>(`/activities/${synced.uploadSessionId}/finish`, {expected_version:synced.uploadVersion ?? 1,ended_at:endedAt,device_distance_m:deviceDistanceM});
  const uploaded = await api.post<any>(`/activities/${synced.uploadSessionId}/uploaded`, {expected_version:finished.version,ended_at:endedAt});
  return uploaded;
};

export const appendLocations = async (locations: Location.LocationObject[]) => {
  let latestPoint: RecordedPoint | null = null;
  writeQueue = writeQueue.then(async () => {
    const session = await loadActiveRun();
    if (!session || session.state !== 'recording') return;

    for (const location of locations) {
      const point = locationToPoint(location);
      if (!Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) continue;
      let lastPoint: RecordedPoint | undefined;
      for (let index = session.points.length - 1; index >= 0; index -= 1) {
        if (session.points[index].metric_accepted !== false) {
          lastPoint = session.points[index];
          break;
        }
      }
      const acceptedPoint = acceptAndSmoothPoint(lastPoint, point);
      if (!acceptedPoint) {
        // Preserve the raw fix as evidence. It remains excluded from live
        // metrics and the backend independently applies the same rejection.
        session.points.push({ ...point, metric_accepted: false });
        continue;
      }
      acceptedPoint.metric_accepted = true;

      const nowMs = new Date(acceptedPoint.timestamp).getTime();
      const speed = Math.max(0, acceptedPoint.speed ?? 0);
      if (session.autoPauseEnabled) {
        if (session.autoPausedAt) {
          if (speed >= AUTO_RESUME_SPEED_MPS) {
            session.pausedDurationSec += Math.max(
              0,
              Math.round((nowMs - new Date(session.autoPausedAt).getTime()) / 1000),
            );
            session.autoPausedAt = undefined;
            session.slowSince = undefined;
          }
        } else if (speed < AUTO_PAUSE_SPEED_MPS) {
          if (!session.slowSince) session.slowSince = acceptedPoint.timestamp;
          if (nowMs - new Date(session.slowSince).getTime() >= AUTO_PAUSE_AFTER_MS) {
            session.autoPausedAt = session.slowSince;
          }
        } else {
          session.slowSince = undefined;
        }
      }

      session.points.push(acceptedPoint);
      latestPoint = acceptedPoint;
      if (session.points.length > MAX_STORED_POINTS) {
        const overflow = session.points.length - MAX_STORED_POINTS;
        const uploaded = session.uploadedPointCount ?? 0;
        if (uploaded >= overflow) {
          session.points = session.points.slice(overflow);
          session.uploadedPointCount = uploaded - overflow;
        }
      }
      session.updatedAt = acceptedPoint.timestamp;
    }
    await saveActiveRun(session);
    try {
      await syncRunChunks(session);
    } catch {
      // The raw session remains on-device and the next batch retries.
    }
  });
  await writeQueue;
  if (latestPoint) await publishLiveLocation(latestPoint);
};

if (!TaskManager.isTaskDefined(RUN_LOCATION_TASK)) {
  TaskManager.defineTask<{ locations: Location.LocationObject[] }>(
    RUN_LOCATION_TASK,
    async ({ data, error }) => {
      if (error || !data?.locations?.length) return;
      await appendLocations(data.locations);
    },
  );
}

export const requestRunPermissions = async () => {
  const foreground = await Location.requestForegroundPermissionsAsync();
  if (foreground.status !== 'granted') {
    return { foreground: false, background: false };
  }
  if (Platform.OS === 'web') {
    return { foreground: true, background: false };
  }
  const background = await Location.requestBackgroundPermissionsAsync();
  return {
    foreground: true,
    background: background.status === 'granted',
  };
};

export const startLocationTask = async (): Promise<boolean> => {
  if (Platform.OS === 'web') return false;
  try {
    const available = await TaskManager.isAvailableAsync();
    if (!available) return false;
    const registered = await TaskManager.isTaskRegisteredAsync(RUN_LOCATION_TASK);
    if (!registered) {
      await Location.startLocationUpdatesAsync(RUN_LOCATION_TASK, {
        accuracy: Location.Accuracy.BestForNavigation,
        timeInterval: GPS_SAMPLE_INTERVAL_MS,
        distanceInterval: 0,
        deferredUpdatesDistance: 0,
        deferredUpdatesInterval: 5_000,
        pausesUpdatesAutomatically: false,
        activityType: Location.ActivityType.Fitness,
        showsBackgroundLocationIndicator: true,
        foregroundService: {
          notificationTitle: 'Runlete is tracking your run',
          notificationBody: 'Distance and time are being recorded.',
          killServiceOnDestroy: false,
        },
      });
    }
    return true;
  } catch {
    return false;
  }
};

export const stopLocationTask = async () => {
  if (Platform.OS === 'web') return;
  try {
    if (await TaskManager.isTaskRegisteredAsync(RUN_LOCATION_TASK)) {
      await Location.stopLocationUpdatesAsync(RUN_LOCATION_TASK);
    }
  } catch {
    // The OS may already have removed the task.
  }
};

export const createRunSession = async (
  autoPauseEnabled = true,
  visibility: 'public' | 'club' | 'private' = 'private',
  surface: 'road' | 'trail' | 'park' | 'track' = 'road',
): Promise<PersistedRunSession> => {
  const now = new Date().toISOString();
  const id = makeSessionId();
  const session: PersistedRunSession = {
    id,
    idempotencyKey: id,
    state: 'recording',
    startedAt: now,
    updatedAt: now,
    pausedDurationSec: 0,
    autoPauseEnabled,
    visibility,
    surface,
    points: [],
  };
  await saveActiveRun(session);
  return session;
};

export const pauseRunSession = async (): Promise<PersistedRunSession | null> => {
  const session = await loadActiveRun();
  if (!session || session.state !== 'recording') return session;
  session.state = 'paused';
  session.manualPausedAt = new Date().toISOString();
  session.updatedAt = session.manualPausedAt;
  await saveActiveRun(session);
  await stopLocationTask();
  return session;
};

export const resumeRunSession = async (): Promise<PersistedRunSession | null> => {
  const session = await loadActiveRun();
  if (!session || (session.state !== 'paused' && session.state !== 'finishing')) return session;
  const now = new Date();
  if (session.manualPausedAt) {
    session.pausedDurationSec += Math.max(
      0,
      Math.round((now.getTime() - new Date(session.manualPausedAt).getTime()) / 1000),
    );
  }
  session.manualPausedAt = undefined;
  session.state = 'recording';
  session.updatedAt = now.toISOString();
  await saveActiveRun(session);
  await startLocationTask();
  return session;
};

export const finishRunSession = async (): Promise<PersistedRunSession | null> => {
  const session = await loadActiveRun();
  if (!session) return null;
  const now = new Date();
  if (session.manualPausedAt) {
    session.pausedDurationSec += Math.max(
      0,
      Math.round((now.getTime() - new Date(session.manualPausedAt).getTime()) / 1000),
    );
  }
  if (session.autoPausedAt) {
    session.pausedDurationSec += Math.max(
      0,
      Math.round((now.getTime() - new Date(session.autoPausedAt).getTime()) / 1000),
    );
  }
  session.manualPausedAt = undefined;
  session.autoPausedAt = undefined;
  session.state = 'finishing';
  session.updatedAt = now.toISOString();
  await saveActiveRun(session);
  await stopLocationTask();
  return session;
};

export const clearActiveRun = async () => {
  await stopLocationTask();
  await stopLiveLocationSession();
  await AsyncStorage.removeItem(ACTIVE_RUN_KEY);
};

export const queuePendingRun = async (session: PersistedRunSession, endedAt: string) => {
  const pending = await loadPendingRuns();
  const item: PendingRunUpload = {
    session,
    endedAt,
    queuedAt: new Date().toISOString(),
  };
  await AsyncStorage.setItem(
    PENDING_RUNS_KEY,
    JSON.stringify([item, ...pending.filter((entry) => entry.session.id !== session.id)].slice(0, 20)),
  );
};

export const loadPendingRuns = async (): Promise<PendingRunUpload[]> => {
  const raw = await AsyncStorage.getItem(PENDING_RUNS_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const removePendingRun = async (sessionId: string) => {
  const pending = await loadPendingRuns();
  await AsyncStorage.setItem(
    PENDING_RUNS_KEY,
    JSON.stringify(pending.filter((entry) => entry.session.id !== sessionId)),
  );
};

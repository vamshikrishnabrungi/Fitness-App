import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import MapView, { Polyline } from 'react-native-maps';
import { Button } from '../../src/components/Button';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

const RUN_HISTORY_KEY = 'terra_run_history_v1';
const TERRITORY_MIN_KM = 2.5; // a run claims its roads once it reaches this distance
const DEFAULT_REGION = { latitude: 17.42, longitude: 78.47, latitudeDelta: 0.01, longitudeDelta: 0.01 };
type LatLng = { latitude: number; longitude: number };

interface GPSPoint {
  latitude: number;
  longitude: number;
  timestamp: Date;
  altitude?: number;
  speed?: number;
}

interface CompletedRun {
  id: string;
  distance_km: number;
  duration_sec: number;
  territory_captured: number;
  is_loop: boolean;
  pace: string;
  calories: number;
  started_at: string;
  ended_at: string;
  path_points: number;
  feeling?: string;
  notes?: string;
  sync_status?: 'synced' | 'local_only';
}

const loadRunHistory = async (): Promise<CompletedRun[]> => {
  const raw = await AsyncStorage.getItem(RUN_HISTORY_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item): item is CompletedRun => item && typeof item === 'object' && typeof item.id === 'string')
      .sort((a, b) => new Date(b.ended_at).getTime() - new Date(a.ended_at).getTime());
  } catch {
    return [];
  }
};

const persistRunHistory = async (runs: CompletedRun[]) => {
  await AsyncStorage.setItem(RUN_HISTORY_KEY, JSON.stringify(runs.slice(0, 50)));
};

const appendRunHistory = async (run: CompletedRun) => {
  const runs = await loadRunHistory();
  await persistRunHistory([run, ...runs.filter((r) => r.id !== run.id)]);
};

const updateRunHistory = async (id: string, patch: Partial<CompletedRun>) => {
  const runs = await loadRunHistory();
  await persistRunHistory(runs.map((r) => (r.id === id ? { ...r, ...patch } : r)));
};

const haversineKm = (a: GPSPoint, b: GPSPoint) => {
  const R = 6371;
  const dLat = (b.latitude - a.latitude) * (Math.PI / 180);
  const dLon = (b.longitude - a.longitude) * (Math.PI / 180);
  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(a.latitude * (Math.PI / 180)) *
      Math.cos(b.latitude * (Math.PI / 180)) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
};

const formatTime = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
};

const formatPace = (distKm: number, durationSec: number) => {
  if (distKm <= 0) return "--'--\"";
  const paceSeconds = durationSec / distKm;
  const m = Math.floor(paceSeconds / 60);
  const s = Math.floor(paceSeconds % 60);
  return `${m}'${s.toString().padStart(2, '0')}"`;
};

type ScreenState = 'permission' | 'ready' | 'running' | 'paused';

const FEELINGS = [
  { key: 'great', emoji: '✓', label: 'Great' },
  { key: 'good', emoji: 'OK', label: 'Good' },
  { key: 'tired', emoji: '...', label: 'Tired' },
  { key: 'struggling', emoji: '!', label: 'Hard' },
];

export default function TrackRunScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [screen, setScreen] = useState<ScreenState>('ready');
  const [gpsReady, setGpsReady] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);

  const [duration, setDuration] = useState(0);
  const [distance, setDistance] = useState(0);
  const [calories, setCalories] = useState(0);
  const [territory, setTerritory] = useState(0);
  const [isLoop, setIsLoop] = useState(false);
  const [currentSpeed, setCurrentSpeed] = useState(0);
  const [routeCoords, setRouteCoords] = useState<LatLng[]>([]); // live polyline, drives the map
  const [region, setRegion] = useState(DEFAULT_REGION);

  const gpsPath = useRef<GPSPoint[]>([]);
  const startTime = useRef<Date | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const locationSub = useRef<Location.LocationSubscription | null>(null);

  const [showSummary, setShowSummary] = useState(false);
  const [runSummary, setRunSummary] = useState<CompletedRun | null>(null);
  const [captured, setCaptured] = useState<{ claimed: boolean; road_km: number; threshold_km: number } | null>(null);
  const [showReflection, setShowReflection] = useState(false);
  const [feeling, setFeeling] = useState('good');
  const [reflectionNotes, setReflectionNotes] = useState('');

  useEffect(() => {
    requestPermission();
    return () => stopTracking();
  }, []);

  const requestPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      setPermissionDenied(true);
      return;
    }
    // Pre-warm GPS lock and centre the map on the current position.
    try {
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setRegion({ latitude: loc.coords.latitude, longitude: loc.coords.longitude, latitudeDelta: 0.006, longitudeDelta: 0.006 });
      setGpsReady(true);
    } catch {
      setGpsReady(true); // proceed anyway
    }
  };

  const stopTracking = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (locationSub.current) locationSub.current.remove();
    timerRef.current = null;
    locationSub.current = null;
  };

  const startRun = async () => {
    startTime.current = new Date();
    gpsPath.current = [];
    setDuration(0);
    setDistance(0);
    setCalories(0);
    setTerritory(0);
    setIsLoop(false);
    setRouteCoords([]);
    setScreen('running');

    // Start timer
    timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000);

    // Start GPS watch
    locationSub.current = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.BestForNavigation,
        timeInterval: 2000,
        distanceInterval: 5,
      },
      (loc) => {
        const point: GPSPoint = {
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
          timestamp: new Date(loc.timestamp),
          altitude: loc.coords.altitude ?? undefined,
          speed: loc.coords.speed ?? undefined,
        };

        if (loc.coords.speed != null && loc.coords.speed > 0) {
          setCurrentSpeed(loc.coords.speed * 3.6); // m/s → km/h
        }

        const coord = { latitude: point.latitude, longitude: point.longitude };
        const path = gpsPath.current;
        if (path.length > 0) {
          const d = haversineKm(path[path.length - 1], point);
          if (d > 0.002) { // filter GPS jitter < 2m
            gpsPath.current = [...path, point];
            setRouteCoords((prev) => [...prev, coord]); // extend the live map line
            setDistance((prev) => {
              const next = prev + d;
              setCalories(next * 60);
              // Loop detection
              if (gpsPath.current.length >= 8) {
                const loopDist = haversineKm(gpsPath.current[0], point);
                setIsLoop(loopDist < 0.1 && next > 0.5);
              }
              // Territory = claimed road km once the run passes the threshold (matches the server).
              setTerritory(next >= TERRITORY_MIN_KM ? next : 0);
              return next;
            });
          }
        } else {
          gpsPath.current = [point];
          setRouteCoords([coord]);
        }
      }
    );
  };

  const pauseRun = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (locationSub.current) locationSub.current.remove();
    timerRef.current = null;
    locationSub.current = null;
    setScreen('paused');
  };

  const resumeRun = async () => {
    setScreen('running');
    timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000);
    locationSub.current = await Location.watchPositionAsync(
      { accuracy: Location.Accuracy.BestForNavigation, timeInterval: 2000, distanceInterval: 5 },
      (loc) => {
        const point: GPSPoint = {
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
          timestamp: new Date(loc.timestamp),
          altitude: loc.coords.altitude ?? undefined,
          speed: loc.coords.speed ?? undefined,
        };
        const path = gpsPath.current;
        if (path.length > 0) {
          const d = haversineKm(path[path.length - 1], point);
          if (d > 0.002) {
            gpsPath.current = [...path, point];
            setDistance((prev) => {
              const next = prev + d;
              setCalories(next * 60);
              return next;
            });
          }
        } else {
          gpsPath.current = [point];
        }
      }
    );
  };

  const handleFinish = () => {
    pauseRun();
    Alert.alert('Finish Run?', 'Save your run and capture territory?', [
      { text: 'Keep Going', onPress: resumeRun, style: 'cancel' },
      { text: 'End & Save', style: 'destructive', onPress: saveRun },
    ]);
  };

  const saveRun = async () => {
    const endTime = new Date();
    const path = gpsPath.current;

    // Don't save a run that never moved — no fabricated path, no phantom distance.
    if (path.length < 2 || distance < 0.05) {
      Alert.alert(
        'No route recorded',
        "You haven't moved enough to save a run yet. Start moving to trace a route.",
        [
          { text: 'Keep Going', onPress: resumeRun, style: 'cancel' },
          { text: 'Discard', style: 'destructive', onPress: () => router.back() },
        ]
      );
      return;
    }

    const pathToSend = path.map((p) => ({
      latitude: p.latitude,
      longitude: p.longitude,
      timestamp: p.timestamp instanceof Date ? p.timestamp.toISOString() : p.timestamp,
      altitude: p.altitude,
      speed: p.speed,
    }));

    try {
      const response = await api.post<any>('/terra/runs', {
        gps_path: pathToSend,
        start_time: startTime.current?.toISOString(),
        end_time: endTime.toISOString(),
      });

      const completed: CompletedRun = {
        id: String(response.id),
        distance_km: Number(response.distance ?? distance),
        duration_sec: Number(response.duration ?? duration),
        territory_captured: Number(response.territory_captured ?? territory),
        is_loop: Boolean(response.is_loop),
        pace: formatPace(Number(response.distance ?? distance), Number(response.duration ?? duration)),
        calories: Math.round(calories),
        started_at: String(response.start_time ?? startTime.current?.toISOString()),
        ended_at: String(response.end_time ?? endTime.toISOString()),
        path_points: pathToSend.length,
        sync_status: 'synced',
      };
      setCaptured(response.territory ?? null);
      setRunSummary(completed);
      setShowSummary(true);
    } catch {
      const completed: CompletedRun = {
        id: `run-${Date.now()}`,
        distance_km: distance,
        duration_sec: duration,
        territory_captured: territory,
        is_loop: isLoop,
        pace: formatPace(distance, duration),
        calories: Math.round(calories),
        started_at: startTime.current?.toISOString() ?? new Date().toISOString(),
        ended_at: endTime.toISOString(),
        path_points: path.length,
        sync_status: 'local_only',
      };
      await appendRunHistory(completed);
      setRunSummary(completed);
      setShowSummary(true);
    }
  };

  const handleReflection = async () => {
    if (runSummary?.id) {
      try {
        if (runSummary.sync_status === 'synced') {
          await api.post('/terra/reflections', { run_id: runSummary.id, feeling, notes: reflectionNotes });
        } else {
          await updateRunHistory(runSummary.id, { feeling, notes: reflectionNotes });
        }
      } catch {
        // best effort
      }
    }
    setShowReflection(false);
    router.back();
  };

  // ─── Permission denied screen ────────────────────────────────────────────
  if (permissionDenied) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Ionicons name="location-outline" size={64} color={colors.textTertiary} />
        <Text style={styles.permTitle}>Location Access Required</Text>
        <Text style={styles.permSubtitle}>
          Terra Run needs your location to track distance, territory, and pace.
        </Text>
        <TouchableOpacity style={styles.permButton} onPress={() => router.back()}>
          <Text style={styles.permButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ─── Ready screen ─────────────────────────────────────────────────────────
  if (screen === 'ready') {
    return (
      <View style={styles.container}>
        <LinearGradient colors={['#1a1a2e', '#16213e', '#0f3460']} style={StyleSheet.absoluteFill} />
        <View style={[styles.readyHeader, { paddingTop: insets.top + spacing.sm }]}>
          <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
            <Ionicons name="close" size={28} color="white" />
          </TouchableOpacity>
        </View>
        <View style={styles.readyContent}>
          <View style={styles.gpsIndicator}>
            <Ionicons name="navigate-circle-outline" size={80} color={gpsReady ? colors.statusSuccess : colors.textPrimary} />
          </View>
          <Text style={styles.readyTitle}>Ready to Run</Text>
          <Text style={styles.readySubtitle}>
            {gpsReady ? 'GPS locked. Hit Start when ready.' : 'Acquiring GPS signal…'}
          </Text>
          <View style={styles.readyTips}>
            {[
              { icon: 'map-outline', text: 'Run 2.5 km+ to claim the roads you cover' },
              { icon: 'people-outline', text: 'Your kilometers count for your club' },
              { icon: 'ribbon-outline', text: 'Claimed roads become your territory' },
            ].map((tip) => (
              <View key={tip.text} style={styles.tipRow}>
                <Ionicons name={tip.icon as any} size={18} color={colors.textPrimary} />
                <Text style={styles.tipText}>{tip.text}</Text>
              </View>
            ))}
          </View>
        </View>
        <View style={[styles.readyFooter, { paddingBottom: insets.bottom + 40 }]}>
          <TouchableOpacity style={styles.bigStartButton} onPress={startRun}>
            <Ionicons name="play" size={32} color={colors.background} />
            <Text style={styles.bigStartText}>START RUN</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ─── Active / Paused run screen ───────────────────────────────────────────
  return (
    <View style={styles.container}>
      {/* Live GPS map — follows you and traces the path as you run */}
      <MapView
        style={StyleSheet.absoluteFill}
        initialRegion={region}
        showsUserLocation
        followsUserLocation={screen === 'running'}
        showsMyLocationButton={false}
        showsCompass={false}
        showsPointsOfInterest={false}
        toolbarEnabled={false}
      >
        {routeCoords.length > 1 && (
          <Polyline coordinates={routeCoords} strokeColor={colors.brand} strokeWidth={6} lineCap="round" lineJoin="round" />
        )}
      </MapView>

      {/* Loop badge */}
      {isLoop && (
        <View style={[styles.loopBadge, { top: insets.top + 66 }]}>
          <Ionicons name="git-compare" size={14} color={colors.textPrimary} />
          <Text style={styles.loopText}>LOOP DETECTED</Text>
        </View>
      )}

      {/* Top header overlay */}
      <View style={[styles.runHeaderOverlay, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => { pauseRun(); router.back(); }} style={styles.mapIconBtn}>
          <Ionicons name="close" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.statusBadgeLight}>
          <View style={[styles.statusDot, { backgroundColor: screen === 'running' ? colors.statusSuccess : '#E0A21F' }]} />
          <Text style={styles.statusTextDark}>{screen === 'running' ? 'TRACKING' : 'PAUSED'}</Text>
        </View>
        <View style={{ width: 44 }} />
      </View>

      {/* Bottom sheet — stats + controls over the map */}
      <View style={[styles.bottomSheet, { paddingBottom: insets.bottom + 20 }]}>
        <View style={styles.distRow}>
          <View>
            <Text style={styles.metaLabel}>DISTANCE</Text>
            <Text style={styles.distanceValue}>{distance.toFixed(2)}<Text style={styles.distanceUnit}> km</Text></Text>
          </View>
          <View style={styles.claimBadge}>
            <Text style={styles.claimBadgeLbl}>{territory > 0 ? 'CLAIMED' : `${TERRITORY_MIN_KM - distance > 0 ? (TERRITORY_MIN_KM - distance).toFixed(1) : 0} km TO CLAIM`}</Text>
            <Text style={styles.claimBadgeVal}>{territory > 0 ? `${territory.toFixed(1)} km road` : 'no road yet'}</Text>
          </View>
        </View>
        <View style={styles.secondaryStats}>
          <View style={styles.statBlock}>
            <Text style={styles.metaLabel}>TIME</Text>
            <Text style={styles.statValue}>{formatTime(duration)}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBlock}>
            <Text style={styles.metaLabel}>PACE</Text>
            <Text style={styles.statValue}>{formatPace(distance, duration)}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBlock}>
            <Text style={styles.metaLabel}>km/h</Text>
            <Text style={[styles.statValue, { color: colors.accentTeal }]}>{currentSpeed.toFixed(1)}</Text>
          </View>
        </View>
        <View style={styles.controlsRow}>
        {screen === 'running' ? (
          <TouchableOpacity style={styles.pauseButton} onPress={pauseRun}>
            <Ionicons name="pause" size={36} color="white" />
          </TouchableOpacity>
        ) : (
          <View style={styles.pausedControls}>
            <TouchableOpacity style={styles.resumeButton} onPress={resumeRun}>
              <Ionicons name="play" size={36} color={colors.background} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.finishButton} onPress={handleFinish}>
              <Ionicons name="flag" size={20} color="white" />
              <Text style={styles.finishText}>FINISH</Text>
            </TouchableOpacity>
          </View>
        )}
        </View>
      </View>

      {/* Summary Modal */}
      <Modal visible={showSummary} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <LinearGradient colors={[colors.textPrimary, '#2B2B2B']} style={styles.summaryCard}>
            <Ionicons name="checkmark-circle" size={56} color="white" />
            <Text style={styles.summaryTitle}>Run Complete!</Text>
            <Text style={styles.summarySync}>
              {runSummary?.sync_status === 'synced' ? '✓ Saved to Terra' : '⚡ Saved locally'}
            </Text>
            <View style={styles.summaryRow}>
              <View style={styles.summaryStat}>
                <Text style={styles.summaryStatVal}>{runSummary?.distance_km.toFixed(2)}</Text>
                <Text style={styles.summaryStatLbl}>km</Text>
              </View>
              <View style={styles.summaryStat}>
                <Text style={styles.summaryStatVal}>{formatTime(runSummary?.duration_sec ?? 0)}</Text>
                <Text style={styles.summaryStatLbl}>time</Text>
              </View>
              <View style={styles.summaryStat}>
                <Text style={styles.summaryStatVal}>{runSummary?.pace}</Text>
                <Text style={styles.summaryStatLbl}>pace</Text>
              </View>
            </View>
            {captured?.claimed ? (
              <View style={styles.captureBanner}>
                <Text style={styles.captureEmoji}>🎉</Text>
                <Text style={styles.captureTitle}>ROAD CLAIMED!</Text>
                <Text style={styles.captureNames}>This route is now your territory</Text>
                <View style={styles.captureRewards}>
                  <View style={styles.crw}><Text style={styles.crwV}>{captured.road_km.toFixed(2)}</Text><Text style={styles.crwL}>km of road</Text></View>
                </View>
              </View>
            ) : (
              <View style={styles.xpEarned}>
                <Text style={styles.xpEarnedLabel}>NO TERRITORY YET</Text>
                <Text style={styles.xpEarnedValue}>{(runSummary?.distance_km ?? 0).toFixed(2)} km</Text>
                <Text style={styles.loopBonus}>Run {captured?.threshold_km ?? TERRITORY_MIN_KM} km+ to claim the road</Text>
              </View>
            )}
            <View style={styles.summaryMetaRow}>
              <Ionicons name="map-outline" size={16} color="rgba(255,255,255,0.7)" />
              <Text style={styles.summaryMetaText}>
                {(runSummary?.territory_captured ?? 0).toFixed(2)} km of roads · {runSummary?.calories} cal
              </Text>
            </View>
            <Button
              title="How Did You Feel?"
              onPress={() => { setShowSummary(false); setShowReflection(true); }}
              fullWidth
              style={{ backgroundColor: 'white', marginTop: spacing.lg }}
            />
            <TouchableOpacity style={styles.skipBtn} onPress={() => { setShowSummary(false); router.back(); }}>
              <Text style={styles.skipText}>Skip</Text>
            </TouchableOpacity>
          </LinearGradient>
        </View>
      </Modal>

      {/* Reflection Modal */}
      <Modal visible={showReflection} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.reflectionCard}>
            <Text style={styles.reflectionTitle}>How did you feel?</Text>
            <View style={styles.feelingsRow}>
              {FEELINGS.map((f) => (
                <TouchableOpacity
                  key={f.key}
                  style={[styles.feelingBtn, feeling === f.key && styles.feelingBtnActive]}
                  onPress={() => setFeeling(f.key)}
                >
                  <Text style={styles.feelingEmoji}>{f.emoji}</Text>
                  <Text style={[styles.feelingLabel, feeling === f.key && { color: 'white', fontWeight: '600' }]}>
                    {f.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.notesLabel}>Any notes?</Text>
            <TextInput
              style={styles.notesInput}
              placeholder="How was the run?"
              placeholderTextColor={colors.textTertiary}
              value={reflectionNotes}
              onChangeText={setReflectionNotes}
              multiline
            />
            <Button title="Save Reflection" onPress={handleReflection} fullWidth />
            <TouchableOpacity style={styles.skipBtn} onPress={() => { setShowReflection(false); router.back(); }}>
              <Text style={[styles.skipText, { color: colors.textTertiary }]}>Skip</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  centered: { justifyContent: 'center', alignItems: 'center', padding: spacing.xl },
  // Permission
  permTitle: { ...typography.h3, color: colors.textPrimary, marginTop: spacing.lg, textAlign: 'center' },
  permSubtitle: { ...typography.body, color: colors.textSecondary, textAlign: 'center', marginTop: spacing.sm, marginBottom: spacing.xl },
  permButton: { backgroundColor: colors.textPrimary, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, borderRadius: borderRadius.full },
  permButtonText: { color: 'white', fontWeight: '700' },
  // Ready screen
  readyHeader: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  readyContent: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: spacing.xl },
  gpsIndicator: { marginBottom: spacing.lg },
  readyTitle: { ...typography.h2, color: 'white', marginBottom: spacing.sm },
  readySubtitle: { ...typography.body, color: 'rgba(255,255,255,0.6)', marginBottom: spacing.xl, textAlign: 'center' },
  readyTips: { width: '100%', gap: spacing.md },
  tipRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: 'rgba(255,255,255,0.07)', padding: spacing.md, borderRadius: borderRadius.md },
  tipText: { ...typography.body, color: 'rgba(255,255,255,0.8)' },
  readyFooter: { alignItems: 'center' },
  bigStartButton: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.textPrimary, paddingHorizontal: spacing.xxxl, paddingVertical: spacing.lg, borderRadius: borderRadius.full },
  bigStartText: { color: colors.background, fontSize: 18, fontWeight: '800', letterSpacing: 2 },
  // Grid / path
  // Pulse
  loopBadge: { position: 'absolute', top: 110, alignSelf: 'center', flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.7)', paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full, gap: spacing.xs },
  loopText: { color: colors.textPrimary, fontSize: 11, fontWeight: '700', letterSpacing: 1 },
  closeButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: 'rgba(255,255,255,0.1)', justifyContent: 'center', alignItems: 'center' },
  // Run header
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  // Main stats
  metaLabel: { color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: '700', letterSpacing: 2, marginBottom: 4 },
  distanceValue: { color: 'white', fontSize: 48, fontWeight: '800', letterSpacing: -1.5 },
  distanceUnit: { fontSize: 20, color: colors.textPrimary, fontWeight: '600' },
  secondaryStats: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.md, backgroundColor: 'rgba(255,255,255,0.08)', paddingVertical: spacing.md, paddingHorizontal: spacing.lg, borderRadius: borderRadius.xl, gap: spacing.lg, justifyContent: 'center' },
  statBlock: { alignItems: 'center', minWidth: 52 },
  statValue: { color: 'white', fontSize: 18, fontWeight: '700' },
  statDivider: { width: 1, height: 28, backgroundColor: 'rgba(255,255,255,0.15)' },
  // Controls
  pauseButton: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.15)', borderWidth: 3, borderColor: 'white', justifyContent: 'center', alignItems: 'center' },
  pausedControls: { flexDirection: 'row', alignItems: 'center', gap: spacing.xl },
  resumeButton: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.textPrimary, justifyContent: 'center', alignItems: 'center' },
  finishButton: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#ff3b30', paddingHorizontal: spacing.xl, paddingVertical: spacing.md, borderRadius: borderRadius.full, gap: spacing.sm },
  finishText: { color: 'white', fontWeight: '700', letterSpacing: 1 },
  // Map overlays
  runHeaderOverlay: { position: 'absolute', top: 0, left: 0, right: 0, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  mapIconBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#fff', justifyContent: 'center', alignItems: 'center', shadowColor: '#000', shadowOpacity: 0.18, shadowRadius: 6, shadowOffset: { width: 0, height: 2 }, elevation: 4 },
  statusBadgeLight: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#fff', paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: borderRadius.full, shadowColor: '#000', shadowOpacity: 0.12, shadowRadius: 5, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  statusTextDark: { color: colors.textPrimary, fontSize: 11, fontWeight: '800', letterSpacing: 1 },
  bottomSheet: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: 'rgba(18,18,28,0.94)', borderTopLeftRadius: 26, borderTopRightRadius: 26, paddingTop: spacing.lg, paddingHorizontal: spacing.lg },
  distRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' },
  claimBadge: { alignItems: 'flex-end', backgroundColor: 'rgba(255,90,40,0.22)', paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: borderRadius.md },
  claimBadgeLbl: { color: colors.brand2, fontSize: 9.5, fontWeight: '800', letterSpacing: 0.8 },
  claimBadgeVal: { color: '#fff', fontSize: 14, fontWeight: '800', marginTop: 2 },
  controlsRow: { alignItems: 'center', justifyContent: 'center', paddingTop: spacing.lg },
  // Modals
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'center', alignItems: 'center', padding: spacing.lg },
  summaryCard: { width: '100%', borderRadius: borderRadius.xl, padding: spacing.xl, alignItems: 'center' },
  summaryTitle: { ...typography.h2, color: 'white', marginTop: spacing.md },
  summarySync: { ...typography.caption, color: 'rgba(255,255,255,0.7)', marginTop: 4, marginBottom: spacing.lg },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-around', width: '100%', marginBottom: spacing.lg },
  summaryStat: { alignItems: 'center' },
  summaryStatVal: { fontSize: 28, fontWeight: '800', color: 'white' },
  summaryStatLbl: { ...typography.caption, color: 'rgba(255,255,255,0.7)' },
  xpEarned: { alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.2)', paddingVertical: spacing.lg, paddingHorizontal: spacing.xxl, borderRadius: borderRadius.lg, marginBottom: spacing.lg, width: '100%' },
  xpEarnedLabel: { ...typography.caption, color: 'rgba(255,255,255,0.6)', letterSpacing: 2 },
  xpEarnedValue: { fontSize: 48, fontWeight: '900', color: 'white' },
  loopBonus: { ...typography.caption, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  captureBanner: { alignItems: 'center', width: '100%', backgroundColor: 'rgba(255,90,40,0.14)', borderWidth: 1, borderColor: 'rgba(255,122,24,0.4)', borderRadius: borderRadius.lg, paddingVertical: spacing.lg, paddingHorizontal: spacing.lg, marginBottom: spacing.lg },
  captureEmoji: { fontSize: 34 },
  captureTitle: { fontSize: 18, fontWeight: '900', letterSpacing: 0.5, color: '#FF7A18', marginTop: 6 },
  captureNames: { ...typography.bodySemibold, color: '#FFFFFF', textAlign: 'center', marginTop: 4 },
  captureRewards: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg, marginTop: spacing.md },
  crw: { alignItems: 'center' },
  crwV: { fontSize: 22, fontWeight: '900', color: '#FFFFFF' },
  crwL: { ...typography.caption, color: 'rgba(255,255,255,0.6)', marginTop: 1 },
  summaryMetaRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.md },
  summaryMetaText: { ...typography.caption, color: 'rgba(255,255,255,0.7)' },
  skipBtn: { marginTop: spacing.md, padding: spacing.sm },
  skipText: { ...typography.body, color: 'rgba(255,255,255,0.6)' },
  // Reflection
  reflectionCard: { width: '100%', backgroundColor: colors.background, borderRadius: borderRadius.xl, padding: spacing.xl },
  reflectionTitle: { ...typography.h3, color: colors.textPrimary, textAlign: 'center', marginBottom: spacing.lg },
  feelingsRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.xl },
  feelingBtn: { alignItems: 'center', padding: spacing.md, borderRadius: borderRadius.md, backgroundColor: colors.surface, minWidth: 68 },
  feelingBtnActive: { backgroundColor: colors.textPrimary },
  feelingEmoji: { fontSize: 28, marginBottom: 4 },
  feelingLabel: { ...typography.caption, color: colors.textSecondary },
  notesLabel: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.sm },
  notesInput: { backgroundColor: colors.surface, borderRadius: borderRadius.md, padding: spacing.md, ...typography.body, color: colors.textPrimary, minHeight: 80, textAlignVertical: 'top', marginBottom: spacing.lg },
});

import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GlassCard } from '../../src/components/GlassCard';
import { ApiError, api } from '../../src/utils/api';
import { setLiveLocationSession } from '../../src/services/runRecorder';
import { borderRadius, colors, spacing, typography } from '../../src/utils/theme';

type RouteSummary = { id: string; name: string; distance_km: number; surface: string };
type SegmentSummary = { id: string; name: string; distance_km: number; elevation_gain_m: number };
type GoalSummary = { id: string; name: string; target: number; current: number; progress_percent: number };
type ChallengeSummary = { id: string; name: string; challenge_type: string; ends_at: string; joined: boolean };
type RaceSummary = { id: string; name: string; starts_at: string; joined: boolean };
type FitnessSummary = { current: { fitness: number; fatigue: number; form: number } };
type PrivacySettings = { live_location_enabled: boolean; version: number };
type Page<T> = { items: T[]; next_cursor?: string | null };

const messageFor = (error: unknown) =>
  error instanceof ApiError ? error.message : 'Something went wrong. Please try again.';

export default function RunExploreScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [routes, setRoutes] = useState<RouteSummary[]>([]);
  const [segments, setSegments] = useState<SegmentSummary[]>([]);
  const [goals, setGoals] = useState<GoalSummary[]>([]);
  const [challenges, setChallenges] = useState<ChallengeSummary[]>([]);
  const [races, setRaces] = useState<RaceSummary[]>([]);
  const [fitness, setFitness] = useState<FitnessSummary['current'] | null>(null);
  const [privacy, setPrivacy] = useState<PrivacySettings | null>(null);
  const [joined, setJoined] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    const [routeData, segmentData, goalData, challengeData, raceData, fitnessData, privacyData] =
      await Promise.all([
        api.get<Page<RouteSummary>>('/routes?limit=100').catch(() => ({ items: [] })),
        api.get<Page<SegmentSummary>>('/segments?limit=100').catch(() => ({ items: [] })),
        api.get<GoalSummary[]>('/goals').catch(() => []),
        api.get<Page<ChallengeSummary>>('/challenges?limit=100').catch(() => ({ items: [] })),
        api.get<Page<RaceSummary>>('/races?limit=100').catch(() => ({ items: [] })),
        api.get<FitnessSummary>('/training/fitness').catch(() => null),
        api.get<PrivacySettings>('/privacy').catch(() => null),
      ]);
    setRoutes(routeData.items);
    setSegments(segmentData.items);
    setGoals(goalData);
    setChallenges(challengeData.items);
    setJoined(new Set(challengeData.items.filter((challenge) => challenge.joined).map((challenge) => challenge.id)));
    setRaces(raceData.items);
    setFitness(fitnessData?.current ?? null);
    setPrivacy(privacyData);
  }, []);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const createGoal = async () => {
    setBusy('goal');
    try {
      const start = new Date();
      start.setHours(0, 0, 0, 0);
      start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
      const end = new Date(start);
      end.setDate(end.getDate() + 7);
      await api.post('/goals', {
        name: '20 km this week',
        metric: 'distance_km',
        target: 20,
        period_start: start.toISOString(),
        period_end: end.toISOString(),
      });
      await load();
    } catch (error) {
      Alert.alert('Goal not created', messageFor(error));
    } finally {
      setBusy(null);
    }
  };

  const generateRoute = async () => {
    setBusy('route');
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== 'granted') {
        Alert.alert('Location needed', 'Allow location to generate a loop from where you are.');
        return;
      }
      const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const generated = await api.post<{
        path: { latitude: number; longitude: number }[];
        distance_km: number;
      }>('/routes/generate', {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        target_distance_km: 5,
        surface: 'any',
        avoid_hills: false,
      });
      await api.post('/routes', {
        name: `5K loop · ${new Date().toLocaleDateString()}`,
        path: generated.path,
        visibility: 'private',
        surface: 'any',
      });
      await load();
      Alert.alert('Route saved', `Your ${generated.distance_km.toFixed(1)} km loop is ready.`);
    } catch (error) {
      Alert.alert('Route not generated', messageFor(error));
    } finally {
      setBusy(null);
    }
  };

  const joinChallenge = async (id: string) => {
    setBusy(id);
    try {
      await api.post(
        `/challenges/${id}/join`,
        {},
        { 'Idempotency-Key': `challenge-join-${id}-${Date.now()}` },
      );
      setJoined((current) => new Set(current).add(id));
    } catch (error) {
      Alert.alert('Could not join', messageFor(error));
    } finally {
      setBusy(null);
    }
  };

  const joinRace = async (id: string) => {
    setBusy(id);
    try {
      await api.post(
        `/races/${id}/join`,
        {},
        { 'Idempotency-Key': `race-join-${id}-${Date.now()}` },
      );
      setRaces((current) => current.map((race) => race.id === id ? { ...race, joined: true } : race));
    } catch (error) {
      Alert.alert('Could not join race', messageFor(error));
    } finally {
      setBusy(null);
    }
  };

  const startSafetyShare = async () => {
    setBusy('safety');
    try {
      if (!privacy?.live_location_enabled) {
        setPrivacy(await api.patch<PrivacySettings>('/privacy', { live_location_enabled: true, expected_version: privacy?.version ?? 1 }));
      }
      const session = await api.post<{ id: string; share_url: string; expires_at: string }>(
        '/safety/live-location',
        { duration_minutes: 180 },
      );
      await setLiveLocationSession(session.id, session.expires_at);
      await Share.share({
        message: `Follow my Runlete live location until ${new Date(session.expires_at).toLocaleTimeString()}: ${session.share_url}`,
      });
    } catch (error) {
      Alert.alert('Live sharing unavailable', messageFor(error));
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return <View style={styles.loading}><ActivityIndicator size="large" color={colors.brand} /></View>;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <View>
          <Text style={styles.title}>Run Lab</Text>
          <Text style={styles.subtitle}>Routes, progress and safety</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 32 }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
      >
        <GlassCard style={styles.darkCard}>
          <Text style={styles.eyebrow}>TRAINING STATUS</Text>
          <View style={styles.fitnessRow}>
            {[
              ['Fitness', fitness?.fitness ?? 0],
              ['Fatigue', fitness?.fatigue ?? 0],
              ['Form', fitness?.form ?? 0],
            ].map(([label, value]) => (
              <View key={String(label)} style={styles.fitnessMetric}>
                <Text style={styles.fitnessValue}>{Number(value).toFixed(0)}</Text>
                <Text style={styles.fitnessLabel}>{label}</Text>
              </View>
            ))}
          </View>
          <Text style={styles.darkHint}>Calculated from verified running load, never generated text.</Text>
        </GlassCard>

        <SectionHeader title="Goals" action="20 km week" busy={busy === 'goal'} onPress={createGoal} />
        {goals.length === 0
          ? <EmptyCard text="Create a goal and every verified run will update it." />
          : goals.map((goal) => (
            <GlassCard key={goal.id} style={styles.card}>
              <View style={styles.rowBetween}>
                <Text style={styles.cardTitle}>{goal.name}</Text>
                <Text style={styles.progressText}>{Math.round(goal.progress_percent)}%</Text>
              </View>
              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: `${Math.min(100, goal.progress_percent)}%` }]} />
              </View>
              <Text style={styles.meta}>{goal.current.toFixed(1)} of {goal.target.toFixed(1)} km</Text>
            </GlassCard>
          ))}

        <SectionHeader title="Saved routes" action="Generate 5K" busy={busy === 'route'} onPress={generateRoute} />
        {routes.length === 0
          ? <EmptyCard text="Generate a private loop from your current location." />
          : routes.slice(0, 5).map((route) => (
            <MetricCard key={route.id} icon="map-outline" title={route.name} meta={`${route.distance_km.toFixed(2)} km · ${route.surface}`} />
          ))}

        <Text style={styles.sectionTitle}>Challenges</Text>
        {challenges.length === 0
          ? <EmptyCard text="Club and city challenges will appear here." />
          : challenges.slice(0, 8).map((challenge) => (
            <GlassCard key={challenge.id} style={styles.card}>
              <View style={styles.rowBetween}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>{challenge.name}</Text>
                  <Text style={styles.meta}>
                    {challenge.challenge_type.replaceAll('_', ' ')} · ends {new Date(challenge.ends_at).toLocaleDateString()}
                  </Text>
                </View>
                <TouchableOpacity
                  style={[styles.joinButton, joined.has(challenge.id) && styles.joinedButton]}
                  disabled={busy === challenge.id || joined.has(challenge.id)}
                  onPress={() => joinChallenge(challenge.id)}
                >
                  {busy === challenge.id
                    ? <ActivityIndicator size="small" color="#fff" />
                    : <Text style={styles.joinText}>{joined.has(challenge.id) ? 'Joined' : 'Join'}</Text>}
                </TouchableOpacity>
              </View>
            </GlassCard>
          ))}

        <Text style={styles.sectionTitle}>Segments</Text>
        {segments.length === 0
          ? <EmptyCard text="Curated running segments appear after street data is imported." />
          : segments.slice(0, 8).map((segment) => (
            <MetricCard
              key={segment.id}
              icon="flag-outline"
              title={segment.name}
              meta={`${segment.distance_km.toFixed(2)} km · ${segment.elevation_gain_m.toFixed(0)} m gain`}
            />
          ))}

        <Text style={styles.sectionTitle}>Scheduled races</Text>
        {races.length === 0
          ? <EmptyCard text="Route-verified club races will appear here." />
          : races.slice(0, 8).map((race) => (
            <GlassCard key={race.id} style={styles.card}>
              <View style={styles.rowBetween}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>{race.name}</Text>
                  <Text style={styles.meta}>Starts {new Date(race.starts_at).toLocaleString()}</Text>
                </View>
                <TouchableOpacity
                  style={[styles.joinButton, race.joined && styles.joinedButton]}
                  disabled={race.joined || busy === race.id}
                  onPress={() => joinRace(race.id)}
                >
                  {busy === race.id
                    ? <ActivityIndicator size="small" color="#fff" />
                    : <Text style={styles.joinText}>{race.joined ? 'Joined' : 'Join'}</Text>}
                </TouchableOpacity>
              </View>
            </GlassCard>
          ))}

        <Text style={styles.sectionTitle}>Safety</Text>
        <GlassCard style={styles.card}>
          <MetricCardContent
            icon="shield-checkmark-outline"
            title="Trusted-contact link"
            meta="Creates an expiring 3-hour link. You choose who receives it."
          />
          <TouchableOpacity style={styles.safetyButton} onPress={startSafetyShare} disabled={busy === 'safety'}>
            {busy === 'safety'
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.safetyText}>Create and share link</Text>}
          </TouchableOpacity>
        </GlassCard>
      </ScrollView>
    </View>
  );
}

function SectionHeader({ title, action, busy, onPress }: { title: string; action: string; busy: boolean; onPress: () => void }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <TouchableOpacity style={styles.actionButton} onPress={onPress} disabled={busy}>
        {busy ? <ActivityIndicator size="small" color={colors.textPrimary} /> : <Ionicons name="add" size={15} color={colors.textPrimary} />}
        <Text style={styles.actionText}>{action}</Text>
      </TouchableOpacity>
    </View>
  );
}

function EmptyCard({ text }: { text: string }) {
  return <GlassCard style={styles.emptyCard}><Text style={styles.emptyText}>{text}</Text></GlassCard>;
}

function MetricCard({ icon, title, meta }: { icon: keyof typeof Ionicons.glyphMap; title: string; meta: string }) {
  return <GlassCard style={styles.card}><MetricCardContent icon={icon} title={title} meta={meta} /></GlassCard>;
}

function MetricCardContent({ icon, title, meta }: { icon: keyof typeof Ionicons.glyphMap; title: string; meta: string }) {
  return (
    <View style={styles.iconRow}>
      <View style={styles.iconBox}><Ionicons name={icon} size={20} color={colors.accentBlue} /></View>
      <View style={{ flex: 1 }}><Text style={styles.cardTitle}>{title}</Text><Text style={styles.meta}>{meta}</Text></View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background },
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingHorizontal: spacing.lg, paddingVertical: spacing.md, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.separator },
  back: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surfaceSecondary },
  title: { ...typography.h2, color: colors.textPrimary },
  subtitle: { ...typography.caption, color: colors.textSecondary },
  content: { padding: spacing.lg, gap: spacing.md },
  darkCard: { backgroundColor: colors.featureCard, padding: spacing.xl, borderWidth: 0 },
  eyebrow: { fontSize: 11, fontWeight: '700', letterSpacing: 1.4, color: '#A9A9AF', marginBottom: spacing.lg },
  fitnessRow: { flexDirection: 'row' },
  fitnessMetric: { flex: 1, borderRightWidth: StyleSheet.hairlineWidth, borderRightColor: '#35353A', paddingHorizontal: spacing.sm },
  fitnessValue: { fontSize: 32, fontWeight: '700', color: '#FFFFFF' },
  fitnessLabel: { ...typography.caption, color: '#B9B9BF' },
  darkHint: { ...typography.caption, color: '#8F8F96', marginTop: spacing.lg },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.md },
  sectionTitle: { ...typography.h3, color: colors.textPrimary, marginTop: spacing.md },
  actionButton: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 12, paddingVertical: 8, borderRadius: borderRadius.full, backgroundColor: colors.surfaceSecondary },
  actionText: { fontSize: 13, fontWeight: '600', color: colors.textPrimary },
  card: { padding: spacing.lg },
  emptyCard: { padding: spacing.xl, backgroundColor: colors.surfaceSecondary },
  emptyText: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },
  rowBetween: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.md },
  iconRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  iconBox: { width: 42, height: 42, borderRadius: borderRadius.md, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.accentBlueLight },
  cardTitle: { ...typography.bodySemibold, color: colors.textPrimary },
  meta: { ...typography.caption, color: colors.textSecondary, marginTop: 3 },
  progressText: { fontSize: 14, fontWeight: '700', color: colors.brand },
  progressTrack: { height: 7, borderRadius: 4, backgroundColor: colors.surfaceSecondary, marginTop: spacing.md, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 4, backgroundColor: colors.brand },
  joinButton: { minWidth: 64, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', paddingHorizontal: spacing.md, backgroundColor: colors.featureCard },
  joinedButton: { backgroundColor: colors.accentGreen },
  joinText: { fontSize: 13, fontWeight: '700', color: '#FFFFFF' },
  safetyButton: { marginTop: spacing.lg, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: borderRadius.full, backgroundColor: colors.accentGreen },
  safetyText: { ...typography.bodySemibold, color: '#FFFFFF' },
});

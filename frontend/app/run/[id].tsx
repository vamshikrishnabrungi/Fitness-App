import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { GlassCard } from '../../src/components/GlassCard';
import { RunRouteMap } from '../../src/components/RunRouteMap';
import { api } from '../../src/utils/api';
import { borderRadius, colors, spacing, typography } from '../../src/utils/theme';

interface RunDetail {
  id: string;
  source: string;
  status: string;
  visibility: string;
  title?: string | null;
  distance_m?: number | null;
  moving_seconds?: number | null;
  elapsed_seconds?: number | null;
  paused_seconds?: number | null;
  average_pace_s_per_km?: number | null;
  elevation_gain_m?: number | null;
  calories_kcal?: number | null;
  average_hr?: number | null;
  average_cadence?: number | null;
  roads_verified_m: number;
  attributed_club_id?: string | null;
  processing_message?: string | null;
  rejection_code?: string | null;
  started_at: string;
  ended_at?: string | null;
  route: { latitude: number; longitude: number }[];
  splits?: {
    sequence: number;
    distance_m: number;
    elapsed_seconds: number;
    pace_s_per_km?: number | null;
  }[];
  best_efforts?: {
    distance_code: string;
    distance_m: number;
    elapsed_seconds: number;
    is_personal_record: boolean;
  }[];
  quality?: {
    gps_score: number;
    competition_eligible: boolean;
    territory_eligible: boolean;
    reasons: string[];
  } | null;
}

interface Reflection {
  feeling?: string;
  notes?: string;
}

interface ActivityInsight {
  summary: string;
  recommendation: string;
  effort: number;
  generated_by: string;
}

const feelingEmoji: Record<string, string> = {
  great: '✓', good: 'OK', tired: 'Tired', struggling: 'Hard',
};

const fmtDuration = (sec: number) => {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s}s`;
};

const fmtPace = (dist: number, dur: number) => {
  if (!dist) return '--';
  const s = dur / dist;
  return `${Math.floor(s / 60)}'${Math.floor(s % 60).toString().padStart(2, '0')}" /km`;
};

const fmtDateTime = (v?: string | null) => {
  if (!v) return '--';
  const d = new Date(v);
  if (isNaN(d.getTime())) return '--';
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

const fmtDate = (v?: string | null) => {
  if (!v) return '--';
  const d = new Date(v);
  if (isNaN(d.getTime())) return '--';
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
};

export default function RunDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const [run, setRun] = useState<RunDetail | null>(null);
  const [reflection, setReflection] = useState<Reflection | null>(null);
  const [insight, setInsight] = useState<ActivityInsight | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const load = async () => {
      try {
        const [activityRes, reflectionRes, insightRes] = await Promise.all([
          api.get<RunDetail>(`/activities/${id}`).catch(() => null),
          Promise.resolve(null),
          Promise.resolve(null),
        ]);
        if (cancelled) return;
        setRun(activityRes);
        setReflection(reflectionRes);
        setInsight(insightRes);
        if (
          activityRes &&
          ['uploaded', 'processing', 'provisional'].includes(activityRes.status)
        ) {
          timer = setTimeout(load, 5000);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [id]);

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color={colors.textPrimary} />
      </View>
    );
  }

  if (!run) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <Ionicons name="alert-circle-outline" size={56} color={colors.textTertiary} />
        <Text style={styles.notFoundText}>Run not found</Text>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Text style={styles.backBtnText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const distanceKm = Number(run.distance_m ?? 0) / 1000;
  const movingTime = Number(run.moving_seconds ?? 0);
  const elapsedTime = Number(run.elapsed_seconds ?? 0);
  const calories = Number(run.calories_kcal ?? 0);
  const route = run.route ?? [];
  const startedAt = run.started_at;
  const endedAt = run.ended_at ?? run.started_at;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerBack} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{fmtDate(endedAt)}</Text>
        <View style={{ width: 44 }} />
      </View>

      <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]} showsVerticalScrollIndicator={false}>
        {/* Hero */}
        <LinearGradient
          colors={[colors.accentBlue, '#5B8DEF']}
          style={styles.hero}
        >
          <View style={styles.heroIcon}>
            <Ionicons name="trending-up-outline" size={28} color="white" />
          </View>
          <Text style={styles.heroDistance}>{distanceKm.toFixed(2)}<Text style={styles.heroUnit}> km</Text></Text>
          <Text style={styles.heroTime}>{fmtDateTime(startedAt)}</Text>
        </LinearGradient>

        {/* Route map — static Strava-style trace of where you actually ran */}
        {route.length > 1 ? (
          <View style={styles.mapCard}>
            <RunRouteMap points={route} />
          </View>
        ) : (
          <GlassCard style={styles.noRouteCard}>
            <Ionicons name="map-outline" size={22} color={colors.textTertiary} />
            <Text style={styles.noRouteText}>No route recorded for this run</Text>
          </GlassCard>
        )}

        {/* Key metrics */}
        <View style={styles.metricsGrid}>
          {[
            { icon: 'time-outline', label: 'Moving Time', value: fmtDuration(movingTime), color: colors.accentBlue },
            { icon: 'hourglass-outline', label: 'Elapsed Time', value: fmtDuration(elapsedTime), color: '#7C3AED' },
            { icon: 'speedometer-outline', label: 'Avg Pace', value: fmtPace(distanceKm, movingTime), color: colors.accentTeal },
            {
              icon: 'analytics-outline',
              label: 'Heart rate',
              value: run.average_hr ? `${run.average_hr} bpm` : '--',
              color: colors.accentGreen,
            },
            { icon: 'flame-outline', label: 'Calories', value: `${calories} cal`, color: '#E74C3C' },
            { icon: 'trending-up-outline', label: 'Elevation', value: `${Number(run.elevation_gain_m ?? 0).toFixed(0)} m`, color: '#D97706' },
            { icon: 'map-outline', label: 'Roads verified', value: `${(run.roads_verified_m / 1000).toFixed(2)} km`, color: colors.statusSuccess },
          ].map((m) => (
            <GlassCard key={m.label} style={styles.metricCard}>
              <Ionicons name={m.icon as any} size={22} color={m.color} />
              <Text style={styles.metricValue}>{m.value}</Text>
              <Text style={styles.metricLabel}>{m.label}</Text>
            </GlassCard>
          ))}
        </View>

        {/* Club contribution */}
        <GlassCard style={styles.xpCard}>
          <View style={styles.xpRow}>
            <View>
              <Text style={styles.xpLabel}>CLUB CONTRIBUTION</Text>
              <Text style={styles.xpValue}>{distanceKm.toFixed(2)} km</Text>
            </View>
            <View style={styles.xpBreakdown}>
              <Text style={styles.xpBreakdownText}>
                {run.roads_verified_m > 0
                  ? `Matched ${(run.roads_verified_m / 1000).toFixed(2)} km to verified OSM roads`
                  : ['uploaded', 'processing', 'provisional'].includes(run.status)
                    ? 'Road verification is processing'
                    : run.quality?.reasons.includes('map_matching_unavailable_or_failed')
                      ? 'Territory maps are unavailable or GPS matching failed'
                      : 'No qualifying road traversal'}
              </Text>
              {!!run.attributed_club_id && (
                <Text style={styles.xpBreakdownText}>Credited once to your primary club</Text>
              )}
            </View>
          </View>
        </GlassCard>

        {run.splits && run.splits.length > 0 ? (
          <GlassCard style={styles.routeCard}>
            <Text style={styles.routeHeading}>Kilometre Splits</Text>
            {run.splits.map((split) => (
              <View key={split.sequence} style={styles.analysisRow}>
                <Text style={styles.analysisLabel}>KM {split.sequence}</Text>
                <Text style={styles.analysisValue}>
                  {fmtDuration(split.elapsed_seconds)} · {split.pace_s_per_km ? fmtPace(1, split.pace_s_per_km) : '--'}
                </Text>
              </View>
            ))}
          </GlassCard>
        ) : null}

        {run.best_efforts && run.best_efforts.length > 0 ? (
          <GlassCard style={styles.routeCard}>
            <Text style={styles.routeHeading}>Best Efforts</Text>
            {run.best_efforts.map((effort) => (
              <View key={effort.distance_code} style={styles.analysisRow}>
                <Text style={styles.analysisLabel}>{effort.distance_code.replace('_', ' ').toUpperCase()}{effort.is_personal_record ? ' · PR' : ''}</Text>
                <Text style={styles.analysisValue}>{fmtDuration(effort.elapsed_seconds)}</Text>
              </View>
            ))}
          </GlassCard>
        ) : null}

        {insight ? (
          <GlassCard style={styles.insightCard}>
            <View style={styles.insightHeader}>
              <Ionicons name="sparkles-outline" size={20} color={colors.accentBlue} />
              <Text style={styles.routeHeading}>Runlete Insight</Text>
            </View>
            <Text style={styles.insightText}>{insight.summary}</Text>
            <Text style={styles.insightRecommendation}>{insight.recommendation}</Text>
            <Text style={styles.insightMeta}>
              Effort {insight.effort.toFixed(0)} · private to you
            </Text>
          </GlassCard>
        ) : null}

        {/* Reflection */}
        {reflection?.feeling ? (
          <GlassCard style={styles.reflectionCard}>
            <Text style={styles.reflectionHeading}>Post-Run Reflection</Text>
            <View style={styles.reflectionFeelingRow}>
              <Text style={styles.reflectionEmoji}>{feelingEmoji[reflection.feeling] ?? '🏃'}</Text>
              <Text style={styles.reflectionFeeling}>Felt {reflection.feeling}</Text>
            </View>
            {reflection.notes ? (
              <Text style={styles.reflectionNotes}>{reflection.notes}</Text>
            ) : null}
          </GlassCard>
        ) : null}

        {/* Route info */}
        <GlassCard style={styles.routeCard}>
          <Text style={styles.routeHeading}>Route Info</Text>
          <View style={styles.routeRow}>
            <Ionicons name="location-outline" size={16} color={colors.textSecondary} />
            <Text style={styles.routeText}>
              {route.length > 0
                ? `${route.length} accepted GPS points`
                : 'No GPS data available'}
            </Text>
          </View>
          <View style={styles.routeRow}>
            <Ionicons name="time-outline" size={16} color={colors.textSecondary} />
            <Text style={styles.routeText}>
              {startedAt ? `Started: ${new Date(startedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Start time unknown'}
            </Text>
          </View>
          <View style={styles.routeRow}>
            <Ionicons name="flag-outline" size={16} color={colors.textSecondary} />
            <Text style={styles.routeText}>
              {endedAt ? `Finished: ${new Date(endedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'End time unknown'}
            </Text>
          </View>
          {run.quality ? (
            <View style={styles.routeRow}>
              <Ionicons name="shield-checkmark-outline" size={16} color={colors.textSecondary} />
              <Text style={styles.routeText}>
                GPS quality: {Math.round(run.quality.gps_score * 100)}% · {run.quality.competition_eligible ? 'competition eligible' : 'not competitive'}
              </Text>
            </View>
          ) : null}
        </GlassCard>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  centered: { justifyContent: 'center', alignItems: 'center', gap: spacing.md },

  // Header
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  headerBack: { width: 44, height: 44, justifyContent: 'center' },
  headerTitle: { ...typography.h4, color: colors.textPrimary },

  content: { padding: spacing.lg, gap: spacing.md },

  // Not found
  notFoundText: { ...typography.h4, color: colors.textSecondary },
  backBtn: { backgroundColor: colors.textPrimary, paddingHorizontal: spacing.xl, paddingVertical: spacing.sm, borderRadius: borderRadius.full },
  backBtnText: { color: colors.background, fontWeight: '700' },

  // Hero
  hero: { borderRadius: borderRadius.xl, padding: spacing.xl, alignItems: 'center', gap: spacing.sm },
  heroIcon: { width: 56, height: 56, borderRadius: 28, backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center', marginBottom: spacing.xs },
  heroDistance: { fontSize: 56, fontWeight: '800', color: 'white', letterSpacing: -1 },
  heroUnit: { fontSize: 22, fontWeight: '600', color: 'rgba(255,255,255,0.8)' },
  heroTime: { ...typography.caption, color: 'rgba(255,255,255,0.7)' },
  loopBadge: { backgroundColor: 'rgba(0,0,0,0.2)', paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full, marginTop: spacing.xs },
  loopBadgeText: { ...typography.caption, color: 'white', fontWeight: '600' },

  // Metrics
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  metricCard: { width: '47%', alignItems: 'center', padding: spacing.md, gap: spacing.xs },
  metricValue: { ...typography.h4, color: colors.textPrimary, textAlign: 'center' },
  metricLabel: { ...typography.caption, color: colors.textSecondary },

  // XP
  xpCard: { padding: spacing.lg },
  xpRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  xpLabel: { ...typography.caption, color: colors.textTertiary, letterSpacing: 1, fontWeight: '600' },
  xpValue: { fontSize: 40, fontWeight: '900', color: colors.textPrimary },
  xpBreakdown: { alignItems: 'flex-end', gap: 4 },
  xpBreakdownText: { ...typography.caption, color: colors.textSecondary },

  // Reflection
  reflectionCard: { padding: spacing.lg, gap: spacing.sm },
  reflectionHeading: { ...typography.h4, color: colors.textPrimary },
  reflectionFeelingRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  reflectionEmoji: { fontSize: 32 },
  reflectionFeeling: { ...typography.body, color: colors.textPrimary, fontWeight: '600', textTransform: 'capitalize' },
  reflectionNotes: { ...typography.body, color: colors.textSecondary, lineHeight: 22 },

  // Route
  routeCard: { padding: spacing.lg, gap: spacing.md },
  routeHeading: { ...typography.h4, color: colors.textPrimary },
  routeRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  routeText: { ...typography.body, color: colors.textSecondary },
  analysisRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: spacing.xs, borderBottomWidth: 1, borderBottomColor: colors.separator },
  analysisLabel: { ...typography.caption, color: colors.textSecondary, fontWeight: '700' },
  analysisValue: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  insightCard: { padding: spacing.lg, gap: spacing.sm, borderWidth: 1, borderColor: 'rgba(59,130,246,0.25)' },
  insightHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  insightText: { ...typography.body, color: colors.textPrimary, lineHeight: 22 },
  insightRecommendation: { ...typography.body, color: colors.textSecondary, lineHeight: 22 },
  insightMeta: { ...typography.caption, color: colors.textTertiary },

  // Route map
  mapCard: { borderRadius: borderRadius.xl, overflow: 'hidden', borderWidth: 1, borderColor: colors.separator },
  map: { width: '100%', height: 240 },
  pin: { width: 14, height: 14, borderRadius: 7, borderWidth: 2.5, borderColor: '#fff' },
  pinStart: { backgroundColor: '#16A34A' },
  pinEnd: { backgroundColor: colors.brand },
  noRouteCard: { padding: spacing.lg, alignItems: 'center', gap: spacing.sm },
  noRouteText: { ...typography.caption, color: colors.textTertiary },
});

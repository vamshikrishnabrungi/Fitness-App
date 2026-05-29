import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { GlassCard } from '../../src/components/GlassCard';
import { api } from '../../src/utils/api';
import { borderRadius, colors, spacing, typography } from '../../src/utils/theme';

interface RunDetail {
  id: string;
  distance: number;
  duration: number;
  territory_captured: number;
  is_loop: boolean;
  start_time?: string | null;
  end_time?: string | null;
  created_at?: string;
  gps_path?: { latitude: number; longitude: number }[];
}

interface Reflection {
  feeling?: string;
  notes?: string;
}

const feelingEmoji: Record<string, string> = {
  great: '🔥', good: '👍', tired: '😮‍💨', struggling: '😤',
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
  const [loading, setLoading] = useState(true);
  const [sharing, setSharing] = useState(false);
  const [shareText, setShareText] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [runsRes, reflectionRes] = await Promise.all([
          api.get<RunDetail[]>('/terra/runs').catch(() => []),
          api.get<Reflection>(`/terra/reflections/${id}`).catch(() => null),
        ]);
        const found = (runsRes ?? []).find((r) => String(r.id) === String(id));
        setRun(found ?? null);
        setReflection(reflectionRes);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleShareToFeed = async () => {
    if (!shareText.trim() || !run) return;
    setSharing(true);
    try {
      await api.post('/terra/feed', { content: shareText.trim(), run_id: id });
      setSharing(false);
      router.back();
    } catch {
      setSharing(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color={colors.accentOrange} />
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

  const calories = Math.round(run.distance * 60);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerBack} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{fmtDate(run.end_time ?? run.created_at)}</Text>
        <View style={{ width: 44 }} />
      </View>

      <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]} showsVerticalScrollIndicator={false}>
        {/* Hero */}
        <LinearGradient
          colors={run.is_loop ? [colors.accentOrange, '#FF8E53'] : [colors.accentBlue, '#5B8DEF']}
          style={styles.hero}
        >
          <View style={styles.heroIcon}>
            <Ionicons name={run.is_loop ? 'git-compare-outline' : 'trending-up-outline'} size={28} color="white" />
          </View>
          <Text style={styles.heroDistance}>{run.distance.toFixed(2)}<Text style={styles.heroUnit}> km</Text></Text>
          <Text style={styles.heroTime}>{fmtDateTime(run.start_time ?? run.created_at)}</Text>
          {run.is_loop && (
            <View style={styles.loopBadge}>
              <Text style={styles.loopBadgeText}>🔄 Loop Run · Territory Boost</Text>
            </View>
          )}
        </LinearGradient>

        {/* Key metrics */}
        <View style={styles.metricsGrid}>
          {[
            { icon: 'time-outline', label: 'Duration', value: fmtDuration(run.duration), color: colors.accentBlue },
            { icon: 'speedometer-outline', label: 'Avg Pace', value: fmtPace(run.distance, run.duration), color: colors.accentTeal },
            { icon: 'flame-outline', label: 'Calories', value: `${calories} cal`, color: '#E74C3C' },
            { icon: 'map-outline', label: 'Territory', value: `${run.territory_captured.toFixed(4)} km²`, color: colors.statusSuccess },
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
              <Text style={styles.xpValue}>{run.distance.toFixed(2)} km</Text>
            </View>
            <View style={styles.xpBreakdown}>
              <Text style={styles.xpBreakdownText}>Territory: {run.territory_captured.toFixed(4)} km²</Text>
              {run.is_loop && <Text style={[styles.xpBreakdownText, { color: colors.accentOrange }]}>Loop territory boost</Text>}
            </View>
          </View>
        </GlassCard>

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
              {run.gps_path && run.gps_path.length > 0
                ? `${run.gps_path.length} GPS points recorded`
                : 'No GPS data available'}
            </Text>
          </View>
          <View style={styles.routeRow}>
            <Ionicons name="time-outline" size={16} color={colors.textSecondary} />
            <Text style={styles.routeText}>
              {run.start_time ? `Started: ${new Date(run.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Start time unknown'}
            </Text>
          </View>
          <View style={styles.routeRow}>
            <Ionicons name="flag-outline" size={16} color={colors.textSecondary} />
            <Text style={styles.routeText}>
              {run.end_time ? `Finished: ${new Date(run.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'End time unknown'}
            </Text>
          </View>
        </GlassCard>

        {/* Share to feed */}
        <GlassCard style={styles.shareCard}>
          <Text style={styles.shareHeading}>Share to Feed</Text>
          <TextInput
            style={styles.shareInputRow}
            placeholder="Write something about this run…"
            placeholderTextColor={colors.textTertiary}
            value={shareText}
            onChangeText={setShareText}
            multiline
          />
          <View style={styles.shareBtnRow}>
            {['Just crushed it! 💪', `${run.distance.toFixed(1)}km done! 🏃`, 'New territory captured 🗺️'].map((t) => (
              <TouchableOpacity key={t} style={styles.shareChip} onPress={() => setShareText(t)}>
                <Text style={styles.shareChipText}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <TouchableOpacity
            style={[styles.sharePostBtn, (!shareText.trim() || sharing) && { opacity: 0.4 }]}
            onPress={handleShareToFeed}
            disabled={!shareText.trim() || sharing}
          >
            {sharing
              ? <ActivityIndicator size="small" color="#000" />
              : <><Ionicons name="send" size={16} color="#000" /><Text style={styles.sharePostBtnText}>Post to Feed</Text></>}
          </TouchableOpacity>
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
  backBtn: { backgroundColor: colors.accentOrange, paddingHorizontal: spacing.xl, paddingVertical: spacing.sm, borderRadius: borderRadius.full },
  backBtnText: { color: '#000', fontWeight: '700' },

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
  xpValue: { fontSize: 40, fontWeight: '900', color: colors.accentOrange },
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

  // Share
  shareCard: { padding: spacing.lg, gap: spacing.md },
  shareHeading: { ...typography.h4, color: colors.textPrimary },
  shareInputRow: { backgroundColor: colors.surface, borderRadius: borderRadius.md, padding: spacing.md, minHeight: 60, ...typography.body, color: colors.textPrimary },
  shareBtnRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  shareChip: { backgroundColor: colors.surface, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full, borderWidth: 1, borderColor: colors.border },
  shareChipText: { ...typography.caption, color: colors.textSecondary },
  sharePostBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, backgroundColor: colors.accentOrange, paddingVertical: spacing.md, borderRadius: borderRadius.full },
  sharePostBtnText: { color: '#000', fontWeight: '700', fontSize: 14 },
});

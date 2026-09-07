import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GlassCard } from '../../src/components/GlassCard';
import { TerritoryMap } from '../../src/components/TerritoryMap';
import { api, ApiError } from '../../src/utils/api';
import { colors, spacing, typography } from '../../src/utils/theme';

type Tab = 'territory' | 'activities';

interface Activity {
  id: string;
  title?: string;
  distance_m?: number | null;
  moving_seconds?: number | null;
  started_at?: string;
  status: string;
  competition_eligible?: boolean | null;
  processing_message?: string | null;
}

interface ActivityPage {
  items: Activity[];
}

interface OfflineRun {
  id: string;
  distance_km: number;
  duration_sec: number;
  ended_at: string;
}

const RUN_HISTORY_KEY = 'runlete_run_history_v2';
const LEGACY_RUN_HISTORY_KEY = 'terra_run_history_v1';

const durationLabel = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = Math.floor(seconds % 60);
  return hours
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
    : `${minutes}:${String(remainder).padStart(2, '0')}`;
};

const activityDate = (value?: string) => {
  if (!value) return 'Recent run';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? 'Recent run'
    : date.toLocaleDateString(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
};

const loadOfflineRuns = async (): Promise<OfflineRun[]> => {
  try {
    let raw = await AsyncStorage.getItem(RUN_HISTORY_KEY);
    if (!raw) {
      raw = await AsyncStorage.getItem(LEGACY_RUN_HISTORY_KEY);
      if (raw) {
        await AsyncStorage.setItem(RUN_HISTORY_KEY, raw);
        await AsyncStorage.removeItem(LEGACY_RUN_HISTORY_KEY);
      }
    }
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed)
      ? parsed.filter((item) =>
          item &&
          typeof item.id === 'string' &&
          Number.isFinite(item.distance_km) &&
          Number.isFinite(item.duration_sec),
        ).slice(0, 20)
      : [];
  } catch {
    return [];
  }
};

export default function RunScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [tab, setTab] = useState<Tab>('territory');
  const [activities, setActivities] = useState<Activity[]>([]);
  const [offline, setOffline] = useState<OfflineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [page, pending] = await Promise.all([
        api.get<ActivityPage | Activity[]>('/activities?limit=50'),
        loadOfflineRuns(),
      ]);
      setActivities(Array.isArray(page) ? page : page.items || []);
      setOffline(pending);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Activities could not be loaded.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <View style={styles.headerCopy}>
          <Text style={styles.title}>Run</Text>
          <Text style={styles.subtitle}>Verified activities and road control</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity
            accessibilityLabel="Activity reviews"
            style={styles.iconButton}
            onPress={() => router.push('/run/moderation' as any)}
          >
            <Ionicons name="shield-checkmark-outline" size={19} color={colors.textPrimary} />
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityLabel="Leaderboards"
            style={styles.iconButton}
            onPress={() => router.push('/run/leaderboards' as any)}
            testID="open-leaderboards"
          >
            <Ionicons name="trophy-outline" size={19} color={colors.textPrimary} />
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityLabel="Notifications"
            style={styles.iconButton}
            onPress={() => router.push('/run/notifications' as any)}
          >
            <Ionicons name="notifications-outline" size={19} color={colors.textPrimary} />
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Run clubs"
            style={styles.clubsButton}
            onPress={() => router.push('/run/clubs')}
          >
            <Ionicons name="people-outline" size={17} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.tabs}>
        {([
          ['territory', 'Territory', 'map-outline'],
          ['activities', 'Activities', 'footsteps-outline'],
        ] as [Tab, string, keyof typeof Ionicons.glyphMap][]).map(([key, label, icon]) => (
          <TouchableOpacity
            key={key}
            accessibilityRole="button"
            accessibilityState={{ selected: tab === key }}
            style={[styles.tab, tab === key && styles.tabActive]}
            onPress={() => setTab(key)}
          >
            <Ionicons
              name={icon}
              size={16}
              color={tab === key ? '#FFFFFF' : colors.textSecondary}
            />
            <Text style={[styles.tabText, tab === key && styles.tabTextActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 110 }]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              void load();
            }}
          />
        }
      >
        {tab === 'territory' && <TerritoryMap />}

        {tab === 'activities' && (
          <>
            <View style={styles.activityActions}>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="Start a GPS run"
                style={styles.startButton}
                onPress={() => router.push('/run/track')}
              >
                <Ionicons name="play" size={18} color="#FFFFFF" />
                <Text style={styles.startText}>Start run</Text>
              </TouchableOpacity>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="Open Run Lab"
                style={styles.labButton}
                onPress={() => router.push('/run/explore')}
              >
                <Ionicons name="compass-outline" size={18} color={colors.textPrimary} />
                <Text style={styles.labText}>Run Lab</Text>
              </TouchableOpacity>
              <TouchableOpacity
                accessibilityLabel="Import an activity file"
                style={styles.labButton}
                onPress={() => router.push('/run/import' as any)}
              >
                <Ionicons name="cloud-upload-outline" size={18} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            {loading ? (
              <ActivityIndicator color={colors.brand} style={{ marginTop: 60 }} />
            ) : error ? (
              <GlassCard style={styles.emptyCard}>
                <Ionicons name="cloud-offline-outline" size={30} color={colors.textTertiary} />
                <Text style={styles.emptyTitle}>Activities unavailable</Text>
                <Text style={styles.emptyBody}>{error}</Text>
                <TouchableOpacity
                  accessibilityRole="button"
                  style={styles.retryButton}
                  onPress={() => {
                    setLoading(true);
                    void load();
                  }}
                >
                  <Text style={styles.retryText}>Try again</Text>
                </TouchableOpacity>
              </GlassCard>
            ) : !activities.length && !offline.length ? (
              <GlassCard style={styles.emptyCard}>
                <Ionicons name="footsteps-outline" size={32} color={colors.textTertiary} />
                <Text style={styles.emptyTitle}>No runs yet</Text>
                <Text style={styles.emptyBody}>
                  Start your first run. Territory appears only after server verification.
                </Text>
              </GlassCard>
            ) : (
              <>
                {activities.map((activity) => {
                  const distance = Number(activity.distance_m ?? 0) / 1000;
                  const duration = Number(activity.moving_seconds ?? 0);
                  const territoryStatus = activity.status === 'complete'
                    ? activity.competition_eligible ? 'competition eligible' : 'processed'
                    : activity.status;
                  return (
                    <TouchableOpacity
                      key={activity.id}
                      onPress={() =>
                        router.push({
                          pathname: '/run/[id]' as any,
                          params: { id: activity.id },
                        })
                      }
                    >
                      <GlassCard style={styles.activityCard}>
                        <View style={styles.activityIcon}>
                          <Ionicons name="footsteps" size={19} color={colors.brand} />
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.activityTitle}>
                            {activity.title || activityDate(activity.started_at)}
                          </Text>
                          <Text style={styles.activityMeta}>
                            {distance.toFixed(2)} km · {durationLabel(duration)}
                          </Text>
                          <Text style={styles.territoryStatus}>
                            Roads: {territoryStatus.replaceAll('_', ' ')}
                          </Text>
                        </View>
                        <Ionicons name="chevron-forward" size={19} color={colors.textTertiary} />
                      </GlassCard>
                    </TouchableOpacity>
                  );
                })}
                {offline.map((run) => (
                  <GlassCard key={run.id} style={styles.activityCard}>
                    <View style={styles.offlineIcon}>
                      <Ionicons name="cloud-offline-outline" size={19} color={colors.textSecondary} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.activityTitle}>{activityDate(run.ended_at)}</Text>
                      <Text style={styles.activityMeta}>
                        {run.distance_km.toFixed(2)} km · {durationLabel(run.duration_sec)}
                      </Text>
                      <Text style={styles.offlineStatus}>Waiting to upload · no verified roads yet</Text>
                    </View>
                  </GlassCard>
                ))}
              </>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.page,
    paddingVertical: spacing.md,
  },
  headerCopy: { flex: 1, minWidth: 0, paddingRight: 8 },
  title: { ...typography.h2, color: colors.textPrimary },
  subtitle: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: 14,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clubsButton: {
    width: 36,
    height: 36,
    borderRadius: 14,
    backgroundColor: colors.textPrimary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabs: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: spacing.page,
    paddingBottom: spacing.md,
  },
  tab: {
    flex: 1,
    height: 43,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.separator,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  tabActive: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  tabText: { color: colors.textSecondary, fontSize: 11.5, fontWeight: '900' },
  tabTextActive: { color: '#FFFFFF' },
  content: { paddingHorizontal: spacing.page },
  activityActions: { flexDirection: 'row', gap: 9, marginBottom: spacing.md },
  startButton: {
    flex: 1,
    height: 48,
    borderRadius: 15,
    backgroundColor: colors.brand,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  startText: { color: '#FFFFFF', fontWeight: '900', fontSize: 12.5 },
  labButton: {
    flex: 1,
    height: 48,
    borderRadius: 15,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
    borderWidth: 1,
    borderColor: colors.separator,
  },
  labText: { color: colors.textPrimary, fontWeight: '900', fontSize: 12.5 },
  activityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    marginBottom: 9,
  },
  activityIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: '#FFF0EA',
    alignItems: 'center',
    justifyContent: 'center',
  },
  offlineIcon: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 13 },
  activityMeta: { color: colors.textSecondary, fontSize: 10.5, marginTop: 3 },
  territoryStatus: {
    color: '#168C75',
    fontSize: 9.5,
    fontWeight: '800',
    marginTop: 4,
    textTransform: 'capitalize',
  },
  offlineStatus: { color: colors.textTertiary, fontSize: 9.5, marginTop: 4 },
  emptyCard: { alignItems: 'center', paddingVertical: 42 },
  emptyTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 16, marginTop: 10 },
  emptyBody: {
    color: colors.textSecondary,
    textAlign: 'center',
    fontSize: 11.5,
    lineHeight: 17,
    marginTop: 5,
  },
  retryButton: {
    marginTop: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.textPrimary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  retryText: { color: colors.background, fontWeight: '800', fontSize: 12 },
});

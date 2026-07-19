import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  Modal,
  Platform,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GlassCard } from '../../src/components/GlassCard';
import { useAuthStore } from '../../src/store/authStore';
import { TerritoryMap } from '../../src/components/TerritoryMap';
import { api } from '../../src/utils/api';
import { borderRadius, colors, spacing, typography } from '../../src/utils/theme';

const { width } = Dimensions.get('window');
const RUN_HISTORY_KEY = 'terra_run_history_v1';
const MEDALS: Record<number, [string, string]> = { 1: colors.medalGold, 2: colors.medalSilver, 3: colors.medalBronze };
const GOAL_PRESETS = [20, 30, 40, 50, 60, 80];
const localISO = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

type TabType = 'map' | 'runs' | 'clubs' | 'social';
type StatPeriod = 'week' | 'lastweek' | 'all' | 'custom';

const fmtShortDate = (d: Date) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

interface TerraStats {
  total_runs: number;
  total_distance: number;
  total_territory: number;
  friends_count: number;
  consistency?: number;
  history: { day: string; value: number }[];
}

interface TerraRun {
  id: string;
  distance: number;
  duration: number;
  territory_captured: number;
  is_loop: boolean;
  created_at?: string;
  start_time?: string | null;
  end_time?: string | null;
}

interface LeaderboardEntry {
  rank: number;
  username: string;
  total_territory: number;
  total_distance?: number;
  total_runs?: number;
  is_me?: boolean;
  is_placeholder?: boolean;
}

interface RunClub {
  id: string;
  name: string;
  city: string;
  country?: string | null;
  emoji?: string | null;
  description?: string | null;
  member_count: number;
  active_members: number;
  total_distance: number;
  total_territory: number;
  total_runs: number;
  average_distance_per_member: number;
  is_member?: boolean;
  rank?: number;
}

interface CityOption {
  city: string;
  country: string | null;
  club_count: number;
}

// A row in the city-vs-city or country-vs-country leaderboard.
interface GeoRow {
  rank: number;
  city?: string;
  country?: string;
  total_distance: number;
  clubs: number;
  members: number;
  active_members: number;
  total_runs: number;
}

type ClubScope = 'city' | 'cities' | 'countries';
type LbPeriod = 'week' | 'month' | 'all';

interface ActivityEvent {
  id: string;
  type: 'run_completed' | 'member_joined' | 'club_created' | string;
  actor_name: string;
  is_me: boolean;
  club_name?: string | null;
  club_emoji?: string | null;
  target?: string | null;
  distance_km: number;
  territory_km2: number;
  created_at?: string | null;
}

interface Competition {
  name: string;
  prize: string;
  days_remaining: number;
}

interface TrainingPlan {
  id: string;
  goal: string;
  fitness_level: string;
  total_weeks: number;
  current_week: number;
  completed_sessions: string[];
}

interface OfflineRun {
  id: string;
  distance_km: number;
  duration_sec: number;
  territory_captured: number;
  is_loop: boolean;
  pace?: string;
  ended_at: string;
  feeling?: string;
  notes?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const loadOfflineRuns = async (): Promise<OfflineRun[]> => {
  try {
    const raw = await AsyncStorage.getItem(RUN_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((r): r is OfflineRun => Boolean(r?.id))
      .sort((a, b) => new Date(b.ended_at).getTime() - new Date(a.ended_at).getTime());
  } catch { return []; }
};

const fmtDuration = (sec: number) => {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const fmtPace = (dist: number, dur: number) => {
  if (!dist) return '--';
  const s = dur / dist;
  return `${Math.floor(s / 60)}'${Math.floor(s % 60).toString().padStart(2, '0')}"`;
};

const fmtDate = (v?: string | null) => {
  if (!v) return 'Today';
  const d = new Date(v);
  if (isNaN(d.getTime())) return 'Today';
  const today = new Date();
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const fmtRelative = (v?: string | null) => {
  if (!v) return 'Just now';
  const diff = Date.now() - new Date(v).getTime();
  const h = Math.floor(diff / 3.6e6);
  if (h < 1) return 'Just now';
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
};

const feelingEmoji: Record<string, string> = { great: '✓', good: 'OK', tired: 'Tired', struggling: 'Hard' };

export default function TerraRunScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('map');

  const [stats, setStats] = useState<TerraStats | null>(null);
  const [runs, setRuns] = useState<TerraRun[]>([]);
  const [offlineRuns, setOfflineRuns] = useState<OfflineRun[]>([]);
  const [myClubs, setMyClubs] = useState<RunClub[]>([]);
  const [cityClubs, setCityClubs] = useState<RunClub[]>([]);
  const [selectedClub, setSelectedClub] = useState<RunClub | null>(null);
  const [clubMembers, setClubMembers] = useState<LeaderboardEntry[]>([]);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [plans, setPlans] = useState<TrainingPlan[]>([]);

  // Run clubs
  const [showCreateClub, setShowCreateClub] = useState(false);
  const [clubName, setClubName] = useState('');
  const [clubCity, setClubCity] = useState('');
  const [clubCountry, setClubCountry] = useState('');
  const [clubEmoji, setClubEmoji] = useState('🏃');
  const [clubDescription, setClubDescription] = useState('');
  const [creatingClub, setCreatingClub] = useState(false);
  const [joiningClub, setJoiningClub] = useState<string | null>(null);

  // Leaderboard scope, period and city selection.
  const user = useAuthStore((s) => s.user);
  const updateProfile = useAuthStore((s) => s.updateProfile);
  const profileCity = user?.profile?.city ?? '';
  const [clubScope, setClubScope] = useState<ClubScope>('city');
  const [period, setPeriod] = useState<LbPeriod>('all');
  const [cities, setCities] = useState<CityOption[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [cityLeaderboard, setCityLeaderboard] = useState<GeoRow[]>([]);
  const [countryLeaderboard, setCountryLeaderboard] = useState<GeoRow[]>([]);
  const [showCityPicker, setShowCityPicker] = useState(false);
  const [lbLoading, setLbLoading] = useState(false);

  // Create plan modal
  const [showCreatePlan, setShowCreatePlan] = useState(false);
  const [planGoal, setPlanGoal] = useState('5K');
  const [planLevel, setPlanLevel] = useState('intermediate');
  const [creatingPlan, setCreatingPlan] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, runsRes, myClubsRes, citiesRes, activityRes, compRes, plansRes, offline] =
        await Promise.all([
          api.get<TerraStats>('/terra/stats').catch(() => null),
          api.get<TerraRun[]>('/terra/runs').catch(() => []),
          api.get<RunClub[]>('/terra/clubs/my').catch(() => []),
          api.get<CityOption[]>('/terra/clubs/cities').catch(() => []),
          api.get<ActivityEvent[]>('/terra/activity').catch(() => []),
          api.get<Competition>('/terra/competition/current').catch(() => null),
          api.get<TrainingPlan[]>('/terra/training-plans').catch(() => []),
          loadOfflineRuns(),
        ]);
      setStats(statsRes);
      setRuns(runsRes ?? []);
      setMyClubs(myClubsRes ?? []);
      const cityList = citiesRes ?? [];
      setCities(cityList);
      // Default the selected city to the user's own city if it has clubs, else the busiest city.
      setSelectedCity((prev) => {
        if (prev && cityList.some((c) => c.city.toLowerCase() === prev.toLowerCase())) return prev;
        const own = cityList.find((c) => c.city.toLowerCase() === profileCity.toLowerCase());
        return own?.city ?? cityList[0]?.city ?? profileCity;
      });
      const nextSelected = selectedClub
        ? (myClubsRes ?? []).find((club) => club.id === selectedClub.id) || null
        : (myClubsRes?.[0] ?? null);
      setSelectedClub(nextSelected);
      if (nextSelected) {
        const members = await api.get<LeaderboardEntry[]>(`/terra/clubs/${nextSelected.id}/members/leaderboard`).catch(() => []);
        setClubMembers(members ?? []);
      } else {
        setClubMembers([]);
      }
      setActivity(activityRes ?? []);
      setCompetition(compRes);
      setPlans(plansRes ?? []);
      setOfflineRuns(offline);
    } catch (e) {
      console.error('Terra fetch error', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedClub, profileCity]);

  // Run the latest fetchData once per focus. Depending on fetchData directly caused an
  // infinite refetch loop: fetchData sets a new selectedClub object → new fetchData identity
  // → effect re-runs → fetch again. The ref keeps it current without re-subscribing.
  const fetchRef = useRef(fetchData);
  fetchRef.current = fetchData;
  useFocusEffect(useCallback(() => { fetchRef.current(); }, []));

  const onRefresh = useCallback(() => { setRefreshing(true); fetchData(); }, [fetchData]);

  // Load the active leaderboard whenever scope, city, or period changes.
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      setLbLoading(true);
      try {
        if (clubScope === 'city') {
          if (!selectedCity) { if (!cancelled) setCityClubs([]); return; }
          const res = await api.get<RunClub[]>(`/terra/clubs/leaderboard/city?city=${encodeURIComponent(selectedCity)}&period=${period}`).catch(() => []);
          if (!cancelled) setCityClubs(res ?? []);
        } else if (clubScope === 'cities') {
          const res = await api.get<GeoRow[]>(`/terra/leaderboard/cities?period=${period}`).catch(() => []);
          if (!cancelled) setCityLeaderboard(res ?? []);
        } else {
          const res = await api.get<GeoRow[]>(`/terra/leaderboard/countries?period=${period}`).catch(() => []);
          if (!cancelled) setCountryLeaderboard(res ?? []);
        }
      } finally {
        if (!cancelled) setLbLoading(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [clubScope, selectedCity, period]);

  const openCreateClub = useCallback(() => {
    setClubCity((prev) => prev || selectedCity || profileCity);
    setClubCountry((prev) => prev || 'India');
    setShowCreateClub(true);
  }, [selectedCity, profileCity]);

  const createClub = useCallback(async () => {
    if (!clubName.trim() || !clubCity.trim()) return;
    setCreatingClub(true);
    try {
      const club = await api.post<RunClub>('/terra/clubs', {
        name: clubName.trim(),
        city: clubCity.trim(),
        country: clubCountry.trim() || undefined,
        emoji: clubEmoji,
        description: clubDescription.trim() || undefined,
        is_public: true,
      });
      setClubName('');
      setClubDescription('');
      setShowCreateClub(false);
      setSelectedClub(club);
      await fetchData();
    } catch {
      Alert.alert('Error', 'Could not create run club.');
    } finally {
      setCreatingClub(false);
    }
  }, [clubName, clubCity, clubCountry, clubDescription, fetchData]);

  const joinClub = useCallback(async (club: RunClub) => {
    setJoiningClub(club.id);
    try {
      const joined = await api.post<RunClub>(`/terra/clubs/${club.id}/join`);
      setSelectedClub(joined);
      await fetchData();
    } catch {
      Alert.alert('Error', 'Could not join this club.');
    } finally {
      setJoiningClub(null);
    }
  }, [fetchData]);

  const openClub = useCallback(async (club: RunClub) => {
    setSelectedClub(club);
    const members = await api.get<LeaderboardEntry[]>(`/terra/clubs/${club.id}/members/leaderboard`).catch(() => []);
    setClubMembers(members ?? []);
  }, []);

  const createPlan = useCallback(async () => {
    setCreatingPlan(true);
    try {
      await api.post('/terra/training-plans', { goal: planGoal, fitness_level: planLevel });
      setShowCreatePlan(false);
      await fetchData();
    } catch {
      Alert.alert('Error', 'Could not create plan.');
    } finally { setCreatingPlan(false); }
  }, [planGoal, planLevel, fetchData]);

  const maxHistory = Math.max(1, ...(stats?.history.map((h) => h.value) ?? [1]));
  // Relative heat-bar scaling for each leaderboard.
  const maxCityClubKm = Math.max(1, ...cityClubs.map((c) => c.total_distance));
  const maxCityKm = Math.max(1, ...cityLeaderboard.map((r) => r.total_distance));
  const maxCountryKm = Math.max(1, ...countryLeaderboard.map((r) => r.total_distance));
  const heatPct = (v: number, max: number) => `${Math.max(6, Math.round((v / max) * 100))}%` as const;

  // "This Week" progress: weekly distance vs goal + tangible territory.
  const weeklyGoal = user?.profile?.weekly_goal_km ?? 40;
  // Personal stats period filter. Every range is computed client-side from `runs`,
  // which /terra/runs returns in full (no pagination), so the numbers are exact.
  const [statPeriod, setStatPeriod] = useState<StatPeriod>('week');
  const [customFrom, setCustomFrom] = useState(() => { const d = new Date(); d.setDate(d.getDate() - 30); return d; });
  const [customTo, setCustomTo] = useState(() => new Date());

  const periodRange = useMemo(() => {
    const now = new Date();
    const dow = (now.getDay() + 6) % 7; // Monday = 0
    const weekStart = new Date(now); weekStart.setHours(0, 0, 0, 0); weekStart.setDate(now.getDate() - dow);
    if (statPeriod === 'week') return { from: weekStart, to: null as Date | null, label: 'This week' };
    if (statPeriod === 'lastweek') {
      const lastStart = new Date(weekStart); lastStart.setDate(weekStart.getDate() - 7);
      return { from: lastStart, to: weekStart, label: 'Last week' };
    }
    if (statPeriod === 'custom') {
      const f = new Date(customFrom); f.setHours(0, 0, 0, 0);
      const t = new Date(customTo); t.setHours(0, 0, 0, 0); t.setDate(t.getDate() + 1); // exclusive upper bound
      return { from: f, to: t, label: `${fmtShortDate(customFrom)} – ${fmtShortDate(customTo)}` };
    }
    return { from: null as Date | null, to: null as Date | null, label: 'All time' };
  }, [statPeriod, customFrom, customTo]);

  const periodStats = useMemo(() => {
    let km = 0, terr = 0, count = 0;
    for (const r of runs) {
      const d = new Date(r.end_time || r.created_at || 0);
      if (isNaN(d.getTime())) continue;
      if (periodRange.from && d < periodRange.from) continue;
      if (periodRange.to && d >= periodRange.to) continue;
      km += r.distance || 0; terr += r.territory_captured || 0; count += 1;
    }
    return { km, terr, count };
  }, [runs, periodRange]);

  const { weekKm, weekTerritory, todayTerritory } = useMemo(() => {
    const now = new Date();
    const dow = (now.getDay() + 6) % 7; // Monday = 0
    const weekStart = new Date(now); weekStart.setHours(0, 0, 0, 0); weekStart.setDate(now.getDate() - dow);
    const todayISO = localISO(now);
    let wk = 0, wt = 0, tt = 0;
    for (const r of runs) {
      const d = new Date(r.end_time || r.created_at || 0);
      if (isNaN(d.getTime())) continue;
      if (d >= weekStart) { wk += r.distance || 0; wt += r.territory_captured || 0; }
      if (localISO(d) === todayISO) tt += r.territory_captured || 0;
    }
    return { weekKm: wk, weekTerritory: wt, todayTerritory: tt };
  }, [runs]);
  const weekPct = Math.min(100, Math.round((weekKm / Math.max(1, weeklyGoal)) * 100));
  const totalTerritory = stats?.total_territory ?? 0;
  const terrMilestone = Math.max(1, Math.ceil(totalTerritory + 0.0001));
  const terrPct = Math.min(100, Math.round((totalTerritory / terrMilestone) * 100));
  const cycleGoal = useCallback(() => {
    const cur = user?.profile?.weekly_goal_km ?? 40;
    const next = GOAL_PRESETS[(GOAL_PRESETS.indexOf(cur) + 1) % GOAL_PRESETS.length];
    updateProfile({ profile: { ...(user?.profile ?? {}), weekly_goal_km: next } }).catch(() => {});
  }, [user, updateProfile]);

  const renderRank = (rank: number) => {
    const grad = MEDALS[rank];
    if (grad) {
      return (
        <LinearGradient colors={grad} start={{ x: 0.3, y: 0 }} end={{ x: 1, y: 1 }} style={styles.medal}>
          <Text style={styles.medalText}>{rank}</Text>
        </LinearGradient>
      );
    }
    return <View style={styles.medalPlain}><Text style={styles.medalPlainText}>{rank}</Text></View>;
  };
  const TABS: { key: TabType; label: string; icon: string }[] = [
    { key: 'map', label: 'Map', icon: 'map-outline' },
    { key: 'clubs', label: 'Club', icon: 'people-outline' },
    { key: 'runs', label: 'Runs', icon: 'footsteps-outline' },
    { key: 'social', label: 'Activity', icon: 'pulse-outline' },
  ];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* ── Header ── */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Run Club</Text>
          <Text style={styles.headerSub}>Runs · clubs · leaderboards</Text>
        </View>
        <View style={styles.headerRight}>
          <View style={styles.levelBadge}>
            <Text style={styles.levelText}>{myClubs.length} {myClubs.length === 1 ? 'club' : 'clubs'}</Text>
          </View>
        </View>
      </View>

      {/* ── Tabs ── */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsScroll} contentContainerStyle={styles.tabsContent}>
        {TABS.map((t) => (
          <TouchableOpacity key={t.key} style={[styles.tab, activeTab === t.key && styles.tabActive]} onPress={() => setActiveTab(t.key)}>
            <Ionicons name={t.icon as any} size={16} color={activeTab === t.key ? colors.background : colors.textTertiary} />
            <Text style={[styles.tabText, activeTab === t.key && styles.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* ── Content ── */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 100 }]}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.textPrimary} />}
      >
        {loading ? (
          <ActivityIndicator size="large" color={colors.textPrimary} style={{ marginTop: 80 }} />
        ) : (
          <>
            {/* ─────────── MAP (territory) ─────────── */}
            {activeTab === 'map' && <TerritoryMap />}

            {/* ─────────── RUNS ─────────── */}
            {activeTab === 'runs' && (
              <View>
                {runs.length === 0 && offlineRuns.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="compass-outline" size={56} color={colors.textTertiary} />
                    <Text style={styles.emptyTitle}>No runs yet</Text>
                    <Text style={styles.emptySub}>Start your first run to map your frontier.</Text>
                    <TouchableOpacity style={styles.emptyBtn} onPress={() => router.push('/run/track')}>
                      <Text style={styles.emptyBtnText}>Start a Run</Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  <>
                    {runs.length > 0 && (
                      <>
                        <Text style={styles.sectionTitle}>Saved Runs</Text>
                        {runs.map((run) => (
                          <TouchableOpacity key={run.id} onPress={() => router.push({ pathname: '/run/[id]' as any, params: { id: run.id } })}>
                            <GlassCard style={styles.runCard}>
                              <View style={styles.runCardLeft}>
                                <View style={[styles.runIcon, { backgroundColor: run.is_loop ? colors.surfaceSecondary : colors.accentBlue + '20' }]}>
                                  <Ionicons
                                    name={run.is_loop ? 'git-compare-outline' : 'trending-up-outline'}
                                    size={20}
                                    color={run.is_loop ? colors.textPrimary : colors.accentBlue}
                                  />
                                </View>
                                <View>
                                  <Text style={styles.runDate}>{fmtDate(run.end_time ?? run.created_at)}</Text>
                                  <Text style={styles.runPace}>{fmtPace(run.distance, run.duration)} /km</Text>
                                </View>
                              </View>
                              <View style={styles.runMetrics}>
                                <View style={styles.runMetric}>
                                  <Text style={styles.runMetricVal}>{run.distance.toFixed(2)}</Text>
                                  <Text style={styles.runMetricLbl}>km</Text>
                                </View>
                                <View style={styles.runMetric}>
                                  <Text style={styles.runMetricVal}>{fmtDuration(run.duration)}</Text>
                                  <Text style={styles.runMetricLbl}>time</Text>
                                </View>
                                <View style={styles.runMetric}>
                                  <Text style={[styles.runMetricVal, { color: colors.textPrimary }]}>{run.territory_captured.toFixed(3)}</Text>
                                  <Text style={styles.runMetricLbl}>km²</Text>
                                </View>
                              </View>
                            </GlassCard>
                          </TouchableOpacity>
                        ))}
                      </>
                    )}
                    {offlineRuns.length > 0 && (
                      <>
                        <View style={[styles.sectionRow, { marginTop: spacing.lg }]}>
                          <Text style={styles.sectionTitle}>Offline Runs</Text>
                          <View style={styles.offlineBadge}><Text style={styles.offlineBadgeText}>Not synced</Text></View>
                        </View>
                        {offlineRuns.map((run) => (
                          <GlassCard key={run.id} style={StyleSheet.flatten([styles.runCard, styles.runCardOffline])}>
                            <View style={styles.runCardLeft}>
                              <View style={[styles.runIcon, { backgroundColor: colors.textTertiary + '20' }]}>
                                <Ionicons name="cloud-offline-outline" size={20} color={colors.textTertiary} />
                              </View>
                              <View>
                                <Text style={styles.runDate}>{fmtDate(run.ended_at)}</Text>
                                <Text style={styles.runPace}>{run.feeling ? feelingEmoji[run.feeling] + ' ' : ''}{run.pace ?? fmtPace(run.distance_km, run.duration_sec)}</Text>
                              </View>
                            </View>
                            <View style={styles.runMetrics}>
                              <View style={styles.runMetric}>
                                <Text style={styles.runMetricVal}>{run.distance_km.toFixed(2)}</Text>
                                <Text style={styles.runMetricLbl}>km</Text>
                              </View>
                              <View style={styles.runMetric}>
                                <Text style={styles.runMetricVal}>{fmtDuration(run.duration_sec)}</Text>
                                <Text style={styles.runMetricLbl}>time</Text>
                              </View>
                            </View>
                          </GlassCard>
                        ))}
                      </>
                    )}
                  </>
                )}
              </View>
            )}

            {/* ─────────── CLUBS ─────────── */}
            {activeTab === 'clubs' && (
              <View>
                {/* Your stats — one card, filtered by period */}
                <GlassCard style={styles.contribCard}>
                  <LinearGradient colors={[colors.brand, colors.brand2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.heroAccentBar} />

                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.periodRow}>
                    {(([['week', 'This week'], ['lastweek', 'Last week'], ['all', 'All time'], ['custom', 'Dates']]) as [StatPeriod, string][]).map(([k, l]) => (
                      <TouchableOpacity
                        key={k}
                        style={StyleSheet.flatten([styles.periodChip, statPeriod === k ? styles.periodChipOn : undefined])}
                        onPress={() => setStatPeriod(k)}
                      >
                        <Text style={StyleSheet.flatten([styles.periodChipTxt, statPeriod === k ? styles.periodChipTxtOn : undefined])}>{l}</Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>

                  {/* ponytail: iOS `compact` pickers open their own calendar popover, so no modal state.
                      Android needs the imperative show/hide pattern — wire that up when Android ships. */}
                  {statPeriod === 'custom' && (
                    <View style={styles.dateRow}>
                      <View style={styles.dateBtn}>
                        <Text style={styles.dateBtnLbl}>From</Text>
                        <DateTimePicker
                          value={customFrom}
                          mode="date"
                          display={Platform.OS === 'ios' ? 'compact' : 'default'}
                          maximumDate={customTo}
                          onChange={(_e, d) => d && setCustomFrom(d)}
                        />
                      </View>
                      <View style={styles.dateBtn}>
                        <Text style={styles.dateBtnLbl}>To</Text>
                        <DateTimePicker
                          value={customTo}
                          mode="date"
                          display={Platform.OS === 'ios' ? 'compact' : 'default'}
                          minimumDate={customFrom}
                          maximumDate={new Date()}
                          onChange={(_e, d) => d && setCustomTo(d)}
                        />
                      </View>
                    </View>
                  )}

                  <Text style={styles.heroLbl}>{periodRange.label.toUpperCase()}</Text>
                  <Text style={styles.heroNum}>
                    {periodStats.km.toFixed(1)}<Text style={styles.heroNumUnit}> km</Text>
                  </Text>
                  <View style={styles.heroChips}>
                    <View style={styles.hChip}>
                      <Text style={styles.hChipVal}>{periodStats.count}</Text>
                      <Text style={styles.hChipLbl}>{periodStats.count === 1 ? 'run' : 'runs'}</Text>
                    </View>
                    <View style={StyleSheet.flatten([styles.hChip, styles.hChipTeal])}>
                      <Text style={StyleSheet.flatten([styles.hChipVal, styles.hChipValTeal])}>{periodStats.terr.toFixed(2)}</Text>
                      <Text style={styles.hChipLbl}>km² captured</Text>
                    </View>
                  </View>

                  {/* Weekly goal only makes sense against this week */}
                  {statPeriod === 'week' && (
                    <View style={styles.goalBlock}>
                      <View style={styles.weekTop}>
                        <Text style={styles.weekTitle}>Weekly goal</Text>
                        <TouchableOpacity onPress={cycleGoal} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                          <Text style={styles.weekGoalEdit}>{weeklyGoal} km ✎</Text>
                        </TouchableOpacity>
                      </View>
                      <View style={styles.weekBigRow}>
                        <Text style={styles.weekBig}>{weekKm.toFixed(1)}<Text style={styles.weekBigUnit}> / {weeklyGoal} km</Text></Text>
                        <Text style={styles.weekPct}>{weekPct}%</Text>
                      </View>
                      <View style={styles.weekTrack}><View style={[styles.weekFill, { width: `${Math.max(3, weekPct)}%` }]} /></View>
                      {todayTerritory > 0 && <Text style={styles.terrNext}>+{todayTerritory.toFixed(2)} km² captured today</Text>}
                    </View>
                  )}

                  {/* All-time milestone */}
                  {statPeriod === 'all' && (
                    <View style={styles.goalBlock}>
                      <View style={styles.terrTrack}><View style={[styles.terrFill, { width: `${Math.max(3, terrPct)}%` }]} /></View>
                      <Text style={styles.terrNext}>{(terrMilestone - totalTerritory).toFixed(2)} km² to your next {terrMilestone} km²</Text>
                    </View>
                  )}
                </GlassCard>

                {/* 7-day distance (folded from Stats) */}
                <GlassCard style={styles.chartCard}>
                  <Text style={styles.sectionTitle}>7-Day Distance</Text>
                  <View style={styles.chart}>
                    {(stats?.history ?? []).map((h) => (
                      <View key={h.day} style={styles.chartCol}>
                        <View style={styles.chartBarTrack}>
                          <View style={[styles.chartBarFill, { height: `${Math.max(4, (h.value / maxHistory) * 100)}%` }]} />
                        </View>
                        <Text style={styles.chartDay}>{h.day}</Text>
                        <Text style={styles.chartVal}>{h.value > 0 ? h.value.toFixed(1) : ''}</Text>
                      </View>
                    ))}
                  </View>
                </GlassCard>

                {competition && (
                  <GlassCard style={styles.compCard}>
                    <View style={styles.compRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.compName}>{competition.name}</Text>
                        <Text style={styles.compPrize}>{competition.prize}</Text>
                      </View>
                      <View style={styles.compDays}>
                        <Text style={styles.compDaysNum}>{competition.days_remaining}</Text>
                        <Text style={styles.compDaysLbl}>days left</Text>
                      </View>
                    </View>
                  </GlassCard>
                )}

                <View style={styles.sectionRow}>
                  <Text style={styles.sectionTitle}>Your Clubs</Text>
                  <TouchableOpacity style={styles.addPlanBtn} onPress={openCreateClub}>
                    <Ionicons name="add" size={18} color={colors.textPrimary} />
                    <Text style={styles.addPlanText}>Create</Text>
                  </TouchableOpacity>
                </View>

                {myClubs.length === 0 ? (
                  <GlassCard style={styles.clubEmptyCard}>
                    <Text style={styles.emptyTitle}>You're not in a club yet</Text>
                    <Text style={styles.emptySub}>Join one from the leaderboard below, or create your own.</Text>
                  </GlassCard>
                ) : (
                  // Name-only switcher — the club's stats live in the feature card below.
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.clubScroll}>
                    {myClubs.map((club) => {
                      const active = selectedClub?.id === club.id;
                      return (
                        <TouchableOpacity
                          key={club.id}
                          onPress={() => openClub(club)}
                          activeOpacity={0.85}
                          style={StyleSheet.flatten([styles.clubChip, active ? styles.clubChipActive : undefined])}
                        >
                          <Text
                            style={StyleSheet.flatten([styles.clubChipText, active ? styles.clubChipTextActive : undefined])}
                            numberOfLines={1}
                          >
                            {club.emoji ? club.emoji + '  ' : ''}{club.name}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </ScrollView>
                )}

                {selectedClub && (
                  <View style={styles.featureCardWrap}>
                  <View style={styles.featureCard}>
                    <View style={styles.featureHalo} />
                    <Text style={styles.fcCity}>{selectedClub.emoji ? selectedClub.emoji + '  ' : '● '}{selectedClub.city.toUpperCase()}</Text>
                    <View style={styles.fcHeader}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.fcName}>{selectedClub.name}</Text>
                        <Text style={styles.fcMeta}>{selectedClub.member_count} members · {selectedClub.active_members} active</Text>
                      </View>
                      {selectedClub.is_member ? (
                        <View style={styles.fcJoined}><Text style={styles.fcJoinedText}>Joined</Text></View>
                      ) : (
                        <TouchableOpacity style={styles.fcJoinBtn} onPress={() => joinClub(selectedClub)} disabled={joiningClub === selectedClub.id}>
                          {joiningClub === selectedClub.id
                            ? <ActivityIndicator size="small" color="#fff" />
                            : <Text style={styles.fcJoinText}>Join</Text>}
                        </TouchableOpacity>
                      )}
                    </View>
                    <Text style={styles.fcKm}>{selectedClub.total_distance.toFixed(1)}<Text style={styles.fcKmUnit}> km this week</Text></Text>
                    <View style={styles.fcStatsRow}>
                      <Text style={styles.fcStat}>{selectedClub.average_distance_per_member.toFixed(1)} km/member</Text>
                      <Text style={styles.fcDot}>·</Text>
                      <Text style={styles.fcStat}>{selectedClub.total_territory.toFixed(2)} km² held</Text>
                    </View>
                    {clubMembers.length > 0 && (
                      <View style={styles.fcMembers}>
                        {clubMembers.slice(0, 5).map((entry, idx) => (
                          <View key={`${selectedClub.id}-${entry.rank}`} style={styles.fcMemberRow}>
                            {renderRank(entry.rank ?? idx + 1)}
                            <Text style={styles.fcMemberName} numberOfLines={1}>{entry.username}</Text>
                            <Text style={styles.fcMemberDist}>{(entry.total_distance ?? 0).toFixed(1)} km</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                  </View>
                )}

                {/* ── Leaderboards ── */}
                <View style={styles.lbSectionHeader}>
                  <Text style={styles.lbSectionTitle}>Leaderboards</Text>
                </View>

                <Text style={styles.controlLabel}>SCOPE</Text>
                <View style={styles.segment}>
                  {(([['city', 'My City'], ['cities', 'Cities'], ['countries', 'Countries']]) as [ClubScope, string][]).map(([key, label]) => (
                    <TouchableOpacity key={key} style={StyleSheet.flatten([styles.segmentBtn, clubScope === key ? styles.segmentBtnActive : undefined])} onPress={() => setClubScope(key)}>
                      <Text style={StyleSheet.flatten([styles.segmentText, clubScope === key ? styles.segmentTextActive : undefined])}>{label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <View style={styles.filterRow}>
                  {clubScope === 'city' ? (
                    <TouchableOpacity style={styles.cityChip} onPress={() => setShowCityPicker(true)}>
                      <Ionicons name="location-outline" size={14} color={colors.textPrimary} />
                      <Text style={styles.cityChipText}>{selectedCity || 'Pick a city'}</Text>
                      <Ionicons name="chevron-down" size={14} color={colors.textSecondary} />
                    </TouchableOpacity>
                  ) : <View />}
                  <View style={styles.timeGroup}>
                    <Text style={styles.controlLabelInline}>TIME</Text>
                    <View style={styles.periodPills}>
                      {(([['week', 'Week'], ['month', 'Month'], ['all', 'All']]) as [LbPeriod, string][]).map(([key, label]) => (
                        <TouchableOpacity key={key} style={StyleSheet.flatten([styles.periodPill, period === key ? styles.periodPillActive : undefined])} onPress={() => setPeriod(key)}>
                          <Text style={StyleSheet.flatten([styles.periodPillText, period === key ? styles.periodPillTextActive : undefined])}>{label}</Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>
                </View>

                {lbLoading ? (
                  <ActivityIndicator color={colors.textPrimary} style={{ marginTop: 28 }} />
                ) : clubScope === 'city' ? (
                  cityClubs.length === 0 ? (
                    <View style={styles.emptyState}>
                      <Ionicons name="people-outline" size={44} color={colors.textTertiary} />
                      <Text style={styles.emptyTitle}>No clubs in {selectedCity || 'this city'}</Text>
                      <Text style={styles.emptySub}>Be the first — create one.</Text>
                    </View>
                  ) : (
                    cityClubs.map((club, idx) => (
                      <GlassCard key={club.id} style={styles.lbCard}>
                        {renderRank(club.rank ?? idx + 1)}
                        <TouchableOpacity style={{ flex: 1 }} onPress={() => openClub(club)}>
                          <Text style={styles.lbName}>{club.emoji ? club.emoji + '  ' : ''}{club.name}</Text>
                          <Text style={styles.lbMeta}>{club.member_count} members · {club.active_members} active</Text>
                          <View style={styles.heatTrack}><View style={[styles.heatFill, { width: heatPct(club.total_distance, maxCityClubKm) }]} /></View>
                        </TouchableOpacity>
                        <View style={styles.lbRight}>
                          <Text style={styles.lbDistance}>{club.total_distance.toFixed(1)}<Text style={styles.lbUnit}> km</Text></Text>
                          {club.is_member ? (
                            <Text style={styles.lbJoined}>Joined</Text>
                          ) : (
                            <TouchableOpacity style={styles.joinChip} onPress={() => joinClub(club)} disabled={joiningClub === club.id}>
                              {joiningClub === club.id ? <ActivityIndicator size="small" color={colors.background} /> : <Text style={styles.joinChipText}>Join</Text>}
                            </TouchableOpacity>
                          )}
                        </View>
                      </GlassCard>
                    ))
                  )
                ) : clubScope === 'cities' ? (
                  cityLeaderboard.length === 0 ? (
                    <View style={styles.emptyState}><Text style={styles.emptySub}>No city activity yet.</Text></View>
                  ) : (
                    cityLeaderboard.map((row) => (
                      <GlassCard key={row.city} style={styles.lbCard}>
                        {renderRank(row.rank)}
                        <View style={{ flex: 1 }}>
                          <Text style={styles.lbName}>{row.city}</Text>
                          <Text style={styles.lbMeta}>{row.clubs} {row.clubs === 1 ? 'club' : 'clubs'} · {row.active_members}/{row.members} active</Text>
                          <View style={styles.heatTrack}><View style={[styles.heatFill, { width: heatPct(row.total_distance, maxCityKm) }]} /></View>
                        </View>
                        <Text style={styles.lbDistance}>{row.total_distance.toFixed(1)}<Text style={styles.lbUnit}> km</Text></Text>
                      </GlassCard>
                    ))
                  )
                ) : (
                  countryLeaderboard.length === 0 ? (
                    <View style={styles.emptyState}><Text style={styles.emptySub}>No country activity yet.</Text></View>
                  ) : (
                    countryLeaderboard.map((row) => (
                      <GlassCard key={row.country} style={styles.lbCard}>
                        {renderRank(row.rank)}
                        <View style={{ flex: 1 }}>
                          <Text style={styles.lbName}>{row.country}</Text>
                          <Text style={styles.lbMeta}>{row.clubs} {row.clubs === 1 ? 'club' : 'clubs'} · {row.members} runners</Text>
                          <View style={styles.heatTrack}><View style={[styles.heatFill, { width: heatPct(row.total_distance, maxCountryKm) }]} /></View>
                        </View>
                        <Text style={styles.lbDistance}>{row.total_distance.toFixed(1)}<Text style={styles.lbUnit}> km</Text></Text>
                      </GlassCard>
                    ))
                  )
                )}

                {/* Training plans (folded from Plans tab) */}
                <View style={[styles.sectionRow, { marginTop: spacing.lg }]}>
                  <Text style={styles.sectionTitle}>Training Plans</Text>
                  <TouchableOpacity style={styles.addPlanBtn} onPress={() => setShowCreatePlan(true)}>
                    <Ionicons name="add" size={18} color={colors.textPrimary} />
                    <Text style={styles.addPlanText}>New Plan</Text>
                  </TouchableOpacity>
                </View>
                {plans.length === 0 ? (
                  <GlassCard style={styles.clubEmptyCard}>
                    <Text style={styles.emptySub}>No training plan yet. Create a goal-specific plan and track your progress.</Text>
                  </GlassCard>
                ) : (
                  plans.map((plan) => {
                    const pct = Math.min(100, Math.round((plan.current_week / Math.max(1, plan.total_weeks)) * 100));
                    return (
                      <GlassCard key={plan.id} style={styles.planCard}>
                        <View style={styles.planHeader}>
                          <View style={styles.planGoalBadge}>
                            <Text style={styles.planGoalText}>{plan.goal}</Text>
                          </View>
                          <Text style={styles.planLevel}>{plan.fitness_level}</Text>
                        </View>
                        <View style={styles.planProgress}>
                          <Text style={styles.planWeek}>Week {plan.current_week} of {plan.total_weeks}</Text>
                          <Text style={styles.planPct}>{pct}%</Text>
                        </View>
                        <View style={styles.planTrack}>
                          <View style={[styles.planFill, { width: `${pct}%` }]} />
                        </View>
                        <Text style={styles.planSessions}>{plan.completed_sessions.length} sessions completed</Text>
                      </GlassCard>
                    );
                  })
                )}
              </View>
            )}

            {/* ─────────── SOCIAL ─────────── */}
            {activeTab === 'social' && (
              <View>
                {activity.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="pulse-outline" size={48} color={colors.textTertiary} />
                    <Text style={styles.emptyTitle}>No activity yet</Text>
                    <Text style={styles.emptySub}>Runs, joins and new clubs from your clubs show up here.</Text>
                  </View>
                ) : (
                  activity.map((e) => {
                    const who = e.is_me ? 'You' : e.actor_name;
                    let icon: any = 'pulse-outline';
                    let tint = colors.textSecondary;
                    let text = `${who} posted an update`;
                    if (e.type === 'territory_captured') {
                      icon = 'location';
                      tint = colors.brand;
                      text = `${who} captured ${e.target ?? 'territory'}`;
                    } else if (e.type === 'run_completed') {
                      icon = 'footsteps';
                      tint = colors.brand;
                      text = `${who} ran ${e.distance_km.toFixed(1)} km` + (e.territory_km2 > 0 ? ` · captured ${e.territory_km2.toFixed(2)} km²` : '');
                    } else if (e.type === 'member_joined') {
                      icon = 'person-add';
                      tint = colors.accentTeal;
                      text = `${who} joined ${e.club_emoji ? e.club_emoji + ' ' : ''}${e.club_name ?? 'a club'}`;
                    } else if (e.type === 'club_created') {
                      icon = 'flag';
                      tint = colors.accentBlue;
                      text = `${who} created ${e.club_emoji ? e.club_emoji + ' ' : ''}${e.club_name ?? 'a club'}`;
                    }
                    return (
                      <View key={e.id} style={styles.actRow}>
                        <View style={StyleSheet.flatten([styles.actIcon, { backgroundColor: tint + '18' }])}>
                          <Ionicons name={icon} size={18} color={tint} />
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.actText}>{text}</Text>
                          <Text style={styles.actTime}>{fmtRelative(e.created_at)}</Text>
                        </View>
                      </View>
                    );
                  })
                )}
              </View>
            )}

          </>
        )}
      </ScrollView>

      {/* ── Floating Start Run — the core action, present on every Run Club screen (Strava/NRC style) ── */}
      <TouchableOpacity
        style={[styles.fab, { bottom: insets.bottom + 20 }]}
        onPress={() => router.push('/run/track')}
        activeOpacity={0.9}
      >
        <LinearGradient colors={[colors.brand, colors.brand2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.fabGrad}>
          <Ionicons name="play" size={20} color="#FFFFFF" />
          <Text style={styles.fabText}>Start Run</Text>
        </LinearGradient>
      </TouchableOpacity>

      {/* ── Create Club Modal ── */}
      <Modal visible={showCreateClub} transparent animationType="slide" onRequestClose={() => setShowCreateClub(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create Run Club</Text>
              <TouchableOpacity onPress={() => setShowCreateClub(false)}>
                <Ionicons name="close" size={24} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalLabel}>Badge</Text>
            <View style={styles.emojiRow}>
              {['🏃', '⚡', '🔥', '🏔️', '🌊', '🏋️', '🚀', '🐺'].map((e) => (
                <TouchableOpacity
                  key={e}
                  style={StyleSheet.flatten([styles.emojiOption, clubEmoji === e ? styles.emojiOptionActive : undefined])}
                  onPress={() => setClubEmoji(e)}
                >
                  <Text style={styles.emojiText}>{e}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.modalLabel}>Club Name</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Hyderabad Runners"
              placeholderTextColor={colors.textTertiary}
              value={clubName}
              onChangeText={setClubName}
            />

            <Text style={styles.modalLabel}>City</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Hyderabad"
              placeholderTextColor={colors.textTertiary}
              value={clubCity}
              onChangeText={setClubCity}
            />

            <Text style={styles.modalLabel}>Country</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="India"
              placeholderTextColor={colors.textTertiary}
              value={clubCountry}
              onChangeText={setClubCountry}
            />

            <Text style={styles.modalLabel}>Description</Text>
            <TextInput
              style={[styles.modalInput, styles.modalTextArea]}
              placeholder="What is this club about?"
              placeholderTextColor={colors.textTertiary}
              value={clubDescription}
              onChangeText={setClubDescription}
              multiline
            />

            <TouchableOpacity
              style={[styles.createPlanBtn, (!clubName.trim() || !clubCity.trim() || creatingClub) && { opacity: 0.6 }]}
              onPress={createClub}
              disabled={!clubName.trim() || !clubCity.trim() || creatingClub}
            >
              {creatingClub
                ? <ActivityIndicator size="small" color={colors.background} />
                : <Text style={styles.createPlanBtnText}>Create Club</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* ── City Picker Modal ── */}
      <Modal visible={showCityPicker} transparent animationType="slide" onRequestClose={() => setShowCityPicker(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Choose a city</Text>
              <TouchableOpacity onPress={() => setShowCityPicker(false)}>
                <Ionicons name="close" size={24} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>
            {cities.length === 0 ? (
              <Text style={styles.emptySub}>No cities with clubs yet.</Text>
            ) : (
              <ScrollView style={{ maxHeight: 360 }}>
                {cities.map((c) => (
                  <TouchableOpacity
                    key={c.city}
                    style={StyleSheet.flatten([styles.cityRow, selectedCity === c.city ? styles.cityRowActive : undefined])}
                    onPress={() => { setSelectedCity(c.city); setShowCityPicker(false); }}
                  >
                    <View style={{ flex: 1 }}>
                      <Text style={styles.cityRowName}>{c.city}</Text>
                      {!!c.country && <Text style={styles.cityRowCountry}>{c.country}</Text>}
                    </View>
                    <Text style={styles.cityRowCount}>{c.club_count} {c.club_count === 1 ? 'club' : 'clubs'}</Text>
                    {selectedCity === c.city && <Ionicons name="checkmark" size={18} color={colors.textPrimary} style={{ marginLeft: 8 }} />}
                  </TouchableOpacity>
                ))}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* ── Create Plan Modal ── */}
      <Modal visible={showCreatePlan} transparent animationType="slide" onRequestClose={() => setShowCreatePlan(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>New Training Plan</Text>
              <TouchableOpacity onPress={() => setShowCreatePlan(false)}>
                <Ionicons name="close" size={24} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalLabel}>Goal</Text>
            <View style={styles.chipRow}>
              {['5K', '10K', 'Half Marathon', 'Marathon'].map((g) => (
                <TouchableOpacity key={g} style={[styles.chip, planGoal === g && styles.chipActive]} onPress={() => setPlanGoal(g)}>
                  <Text style={[styles.chipText, planGoal === g && styles.chipTextActive]}>{g}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.modalLabel}>Fitness Level</Text>
            <View style={styles.chipRow}>
              {['beginner', 'intermediate', 'advanced'].map((l) => (
                <TouchableOpacity key={l} style={[styles.chip, planLevel === l && styles.chipActive]} onPress={() => setPlanLevel(l)}>
                  <Text style={[styles.chipText, planLevel === l && styles.chipTextActive]}>{l}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity
              style={[styles.createPlanBtn, creatingPlan && { opacity: 0.6 }]}
              onPress={createPlan}
              disabled={creatingPlan}
            >
              {creatingPlan
                ? <ActivityIndicator size="small" color={colors.background} />
                : <Text style={styles.createPlanBtnText}>Create Plan</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },

  // Header
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  headerTitle: { ...typography.h2, color: colors.textPrimary },
  headerSub: { ...typography.caption, color: colors.textTertiary, marginTop: 2 },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  levelBadge: { backgroundColor: colors.surface, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full },
  levelText: { ...typography.caption, color: colors.textSecondary, fontWeight: '700' },
  // Tabs
  tabsScroll: { maxHeight: 48 },
  tabsContent: { paddingHorizontal: spacing.lg, gap: spacing.sm, alignItems: 'center' },
  tab: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: borderRadius.full, backgroundColor: colors.surface },
  tabActive: { backgroundColor: colors.textPrimary },
  tabText: { ...typography.caption, color: colors.textTertiary, fontWeight: '600' },
  tabTextActive: { color: colors.background },

  // Scroll
  scroll: { flex: 1 },
  scrollContent: { padding: spacing.lg, gap: spacing.md },

  // Section helpers
  sectionTitle: { ...typography.h4, color: colors.textPrimary, marginBottom: spacing.sm },
  sectionRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.sm },

  // Chart
  chartCard: { padding: spacing.lg },
  chart: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', height: 80, marginTop: spacing.md },
  chartCol: { flex: 1, alignItems: 'center', gap: 4 },
  chartBarTrack: { width: 20, height: 60, backgroundColor: colors.surface, borderRadius: 4, overflow: 'hidden', justifyContent: 'flex-end' },
  chartBarFill: { backgroundColor: colors.textPrimary, width: '100%', borderRadius: 4 },
  chartDay: { ...typography.caption, color: colors.textTertiary, fontSize: 10 },
  chartVal: { fontSize: 9, color: colors.textSecondary },

  // Competition
  compCard: { padding: spacing.lg },
  compRow: { flexDirection: 'row', alignItems: 'center' },
  compName: { ...typography.h4, color: colors.textPrimary },
  compPrize: { ...typography.caption, color: colors.textSecondary, marginTop: 4 },
  compDays: { alignItems: 'center', backgroundColor: colors.surfaceSecondary, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: borderRadius.md },
  compDaysNum: { ...typography.h3, color: colors.textPrimary },
  compDaysLbl: { ...typography.caption, color: colors.textSecondary, fontSize: 10 },

  // Vault

  // Runs
  runCard: { padding: spacing.md, marginBottom: spacing.sm },
  runCardOffline: { borderColor: colors.textTertiary + '30', borderWidth: 1 },
  runCardLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  runIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  runDate: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  runPace: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  runMetrics: { flexDirection: 'row', gap: spacing.xl },
  runMetric: { alignItems: 'center' },
  runMetricVal: { ...typography.h4, color: colors.textPrimary },
  runMetricLbl: { ...typography.caption, color: colors.textTertiary, fontSize: 10 },
  offlineBadge: { backgroundColor: colors.surfaceSecondary, paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: borderRadius.full },
  offlineBadgeText: { ...typography.caption, color: colors.textSecondary, fontSize: 10 },

  // Empty states
  emptyState: { alignItems: 'center', paddingVertical: spacing.xxxl, gap: spacing.md },
  emptyTitle: { ...typography.h4, color: colors.textSecondary },
  emptySub: { ...typography.caption, color: colors.textTertiary, textAlign: 'center' },
  emptyBtn: { backgroundColor: colors.textPrimary, paddingHorizontal: spacing.xl, paddingVertical: spacing.sm, borderRadius: borderRadius.full, marginTop: spacing.sm },
  emptyBtnText: { color: colors.background, fontWeight: '700' },

  // Leaderboard
  lbCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md, marginBottom: spacing.sm },
  lbName: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  lbMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  lbDistance: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },

  // Clubs
  clubEmptyCard: { padding: spacing.lg, marginBottom: spacing.md, gap: spacing.xs, borderColor: colors.separatorDark },
  clubScroll: { gap: spacing.sm, paddingBottom: spacing.md },
  clubChip: { backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.full, paddingHorizontal: spacing.md, paddingVertical: 9, borderWidth: 1, borderColor: colors.separator },
  clubChipActive: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  clubChipText: { fontSize: 13.5, fontWeight: '800', color: colors.textSecondary },
  clubChipTextActive: { color: '#fff' },

  // Social

  // Plans
  addPlanBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, borderWidth: 1.5, borderColor: colors.brand, borderRadius: borderRadius.full, paddingHorizontal: spacing.md, paddingVertical: 6 },
  addPlanText: { ...typography.caption, color: colors.brand, fontWeight: '800' },
  planCard: { padding: spacing.lg, marginBottom: spacing.sm },
  planHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  planGoalBadge: { backgroundColor: colors.textPrimary, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full },
  planGoalText: { color: colors.background, fontWeight: '700', fontSize: 13 },
  planLevel: { ...typography.caption, color: colors.textSecondary, textTransform: 'capitalize' },
  planProgress: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  planWeek: { ...typography.caption, color: colors.textSecondary },
  planPct: { ...typography.caption, color: colors.textPrimary, fontWeight: '600' },
  planTrack: { height: 6, backgroundColor: colors.surface, borderRadius: 3, overflow: 'hidden', marginBottom: spacing.sm },
  planFill: { height: '100%', backgroundColor: colors.textPrimary, borderRadius: 3 },
  planSessions: { ...typography.caption, color: colors.textTertiary },

  // FAB
  fab: { position: 'absolute', right: spacing.lg, borderRadius: borderRadius.full, overflow: 'hidden', elevation: 8, shadowColor: '#000000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.18, shadowRadius: 8 },
  fabGrad: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingHorizontal: spacing.xl, paddingVertical: spacing.md },
  fabText: { color: colors.background, fontWeight: '800', fontSize: 15 },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.background, borderTopLeftRadius: borderRadius.xl, borderTopRightRadius: borderRadius.xl, padding: spacing.xl, gap: spacing.md },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  modalTitle: { ...typography.h3, color: colors.textPrimary },
  modalLabel: { ...typography.body, color: colors.textSecondary, fontWeight: '600' },
  modalInput: { backgroundColor: colors.surface, borderRadius: borderRadius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, ...typography.body, color: colors.textPrimary },
  modalTextArea: { minHeight: 80, textAlignVertical: 'top' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: borderRadius.full, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  chipActive: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  chipText: { ...typography.caption, color: colors.textSecondary, fontWeight: '600' },
  chipTextActive: { color: colors.background },
  createPlanBtn: { backgroundColor: colors.textPrimary, paddingVertical: spacing.md, borderRadius: borderRadius.full, alignItems: 'center', marginTop: spacing.sm },
  createPlanBtnText: { color: colors.background, fontWeight: '800', fontSize: 15 },

  // ── Premium clubs tab ──
  // Hero "your distance"
  contribCard: { padding: spacing.lg, paddingTop: spacing.lg, marginBottom: spacing.lg },
  heroAccentBar: { width: 44, height: 4, borderRadius: 2, marginBottom: spacing.md },
  periodRow: { gap: 6, paddingBottom: spacing.md },
  periodChip: { backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.full, paddingHorizontal: spacing.md, paddingVertical: 7, borderWidth: 1, borderColor: colors.separator },
  periodChipOn: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  periodChipTxt: { fontSize: 12.5, fontWeight: '800', color: colors.textSecondary },
  periodChipTxtOn: { color: '#fff' },
  dateRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  dateBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.xs, backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.md, paddingHorizontal: spacing.md, paddingVertical: 8 },
  dateBtnLbl: { fontSize: 11.5, fontWeight: '800', color: colors.textTertiary, textTransform: 'uppercase', letterSpacing: 0.5 },
  goalBlock: { marginTop: spacing.lg, gap: spacing.xs },
  heroLbl: { fontSize: 11, fontWeight: '800', letterSpacing: 1.3, color: colors.brand },
  heroNum: { fontSize: 52, fontWeight: '800', letterSpacing: -2, color: colors.textPrimary, marginTop: 6 },
  heroNumUnit: { fontSize: 20, fontWeight: '700', color: colors.textSecondary, letterSpacing: -0.5 },
  heroChips: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg },
  hChip: { flex: 1, backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.lg, paddingVertical: spacing.sm, paddingHorizontal: spacing.md },
  hChipTeal: { backgroundColor: colors.accentTealLight },
  hChipVal: { fontSize: 18, fontWeight: '800', letterSpacing: -0.4, color: colors.textPrimary },
  hChipValTeal: { color: colors.accentTeal },
  hChipLbl: { fontSize: 12, fontWeight: '600', color: colors.textSecondary, marginTop: 2 },

  // This Week progress card
  weekTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  weekTitle: { fontSize: 15, fontWeight: '800', letterSpacing: -0.2, color: colors.textPrimary },
  weekGoalEdit: { fontSize: 12, fontWeight: '700', color: colors.brand },
  weekBigRow: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: spacing.md },
  weekBig: { fontSize: 30, fontWeight: '800', letterSpacing: -1, color: colors.textPrimary },
  weekBigUnit: { fontSize: 15, fontWeight: '600', color: colors.textSecondary, letterSpacing: 0 },
  weekPct: { fontSize: 15, fontWeight: '800', color: colors.brand },
  weekTrack: { height: 8, borderRadius: 4, backgroundColor: colors.surfaceSecondary, overflow: 'hidden', marginTop: spacing.sm },
  weekFill: { height: '100%', borderRadius: 4, backgroundColor: colors.brand },
  terrTrack: { height: 6, borderRadius: 3, backgroundColor: colors.accentTealLight, overflow: 'hidden', marginTop: spacing.sm },
  terrFill: { height: '100%', borderRadius: 3, backgroundColor: colors.accentTeal },
  terrNext: { fontSize: 11, color: colors.textTertiary, marginTop: 6 },

  emojiRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xs },
  emojiOption: { width: 44, height: 44, borderRadius: borderRadius.md, backgroundColor: colors.surfaceSecondary, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: 'transparent' },
  emojiOptionActive: { borderColor: colors.brand, backgroundColor: colors.brandSoft },
  emojiText: { fontSize: 22 },

  // Activity feed
  actRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.separator },
  actIcon: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  actText: { ...typography.captionMedium, color: colors.textPrimary, lineHeight: 20 },
  actTime: { fontSize: 11, color: colors.textTertiary, marginTop: 2 },

  // Dark feature card (selected club) — shadow on wrapper, clip on inner (iOS clips shadows under overflow:hidden)
  featureCardWrap: { borderRadius: borderRadius.xxl, marginBottom: spacing.xl,
    shadowColor: '#000', shadowOffset: { width: 0, height: 16 }, shadowOpacity: 0.28, shadowRadius: 28, elevation: 6 },
  featureCard: { position: 'relative', overflow: 'hidden', backgroundColor: colors.featureCard, borderRadius: borderRadius.xxl, padding: spacing.lg },
  featureHalo: { position: 'absolute', width: 200, height: 200, right: -70, top: -70, borderRadius: 100, backgroundColor: 'rgba(255,90,40,0.22)' },
  fcCity: { fontSize: 10.5, fontWeight: '800', letterSpacing: 1.4, color: colors.brand2 },
  fcHeader: { flexDirection: 'row', alignItems: 'flex-start', marginTop: 5 },
  fcName: { fontSize: 19, fontWeight: '800', letterSpacing: -0.3, color: '#FFFFFF' },
  fcMeta: { ...typography.caption, color: 'rgba(255,255,255,0.6)', marginTop: 2 },
  fcJoined: { backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: borderRadius.full, paddingHorizontal: spacing.md, paddingVertical: 6 },
  fcJoinedText: { ...typography.caption, color: '#FFFFFF', fontWeight: '700' },
  fcJoinBtn: { backgroundColor: colors.brand, borderRadius: borderRadius.full, paddingHorizontal: spacing.lg, paddingVertical: 7 },
  fcJoinText: { ...typography.caption, color: '#FFFFFF', fontWeight: '800' },
  fcKm: { fontSize: 30, fontWeight: '800', letterSpacing: -1, color: '#FFFFFF', marginTop: spacing.md },
  fcKmUnit: { fontSize: 14, fontWeight: '600', color: 'rgba(255,255,255,0.6)', letterSpacing: 0 },
  fcStatsRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: 4 },
  fcStat: { ...typography.caption, color: 'rgba(255,255,255,0.6)' },
  fcDot: { color: 'rgba(255,255,255,0.4)' },
  fcMembers: { marginTop: spacing.lg, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: 'rgba(255,255,255,0.12)', paddingTop: spacing.md, gap: spacing.sm },
  fcMemberRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  fcMemberName: { ...typography.captionMedium, color: '#FFFFFF', flex: 1 },
  fcMemberDist: { ...typography.captionMedium, color: 'rgba(255,255,255,0.7)' },

  // Metallic medals
  medal: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.2, shadowRadius: 6, elevation: 3 },
  medalText: { fontSize: 15, fontWeight: '800', color: '#3A2A08' },
  medalPlain: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surfaceSecondary },
  medalPlainText: { fontSize: 15, fontWeight: '800', color: colors.textSecondary },

  // Heat bars
  heatTrack: { height: 5, borderRadius: 3, marginTop: 8, backgroundColor: colors.surfaceSecondary, overflow: 'hidden' },
  heatFill: { height: '100%', borderRadius: 3, backgroundColor: colors.brand },

  lbSectionHeader: { marginTop: spacing.sm, marginBottom: spacing.md },
  lbSectionTitle: { ...typography.h3, color: colors.textPrimary },
  controlLabel: { fontSize: 11, fontWeight: '800', letterSpacing: 1, color: colors.textTertiary, marginBottom: 8 },
  controlLabelInline: { fontSize: 10, fontWeight: '800', letterSpacing: 1, color: colors.textTertiary },
  timeGroup: { flexDirection: 'row', alignItems: 'center', gap: 8 },

  segment: { flexDirection: 'row', backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.full, padding: 3, marginBottom: spacing.md },
  segmentBtn: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: borderRadius.full },
  segmentBtnActive: { backgroundColor: colors.brand },
  segmentText: { ...typography.captionMedium, color: colors.textSecondary },
  segmentTextActive: { color: '#FFFFFF' },

  filterRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
  cityChip: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: colors.surfaceSecondary, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full },
  cityChipText: { ...typography.captionMedium, color: colors.textPrimary },
  periodPills: { flexDirection: 'row', backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.full, padding: 2 },
  periodPill: { paddingHorizontal: spacing.md, paddingVertical: 6, borderRadius: borderRadius.full },
  periodPillActive: { backgroundColor: colors.textPrimary },
  periodPillText: { ...typography.caption, color: colors.textSecondary, fontWeight: '700' },
  periodPillTextActive: { color: colors.background },

  lbRight: { alignItems: 'flex-end', gap: 4 },
  lbUnit: { ...typography.caption, color: colors.textTertiary, fontWeight: '600' },
  lbJoined: { fontSize: 11, fontWeight: '800', color: colors.brand, backgroundColor: colors.brandSoft, borderRadius: borderRadius.full, paddingHorizontal: 10, paddingVertical: 4, overflow: 'hidden' },
  joinChip: { backgroundColor: colors.brand, paddingHorizontal: spacing.md, paddingVertical: 5, borderRadius: borderRadius.full },
  joinChipText: { ...typography.caption, color: '#FFFFFF', fontWeight: '800' },

  cityRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md, paddingHorizontal: spacing.sm, borderRadius: borderRadius.md },
  cityRowActive: { backgroundColor: colors.surfaceSecondary },
  cityRowName: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  cityRowCountry: { ...typography.caption, color: colors.textTertiary, marginTop: 1 },
  cityRowCount: { ...typography.caption, color: colors.textSecondary },
});

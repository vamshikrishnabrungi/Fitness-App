import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  Modal,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GlassCard } from '../../src/components/GlassCard';
import { api } from '../../src/utils/api';
import { borderRadius, colors, spacing, typography } from '../../src/utils/theme';

const { width } = Dimensions.get('window');
const RUN_HISTORY_KEY = 'terra_run_history_v1';

type TabType = 'overview' | 'runs' | 'clubs' | 'social' | 'plans';

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

interface SocialPost {
  id: string;
  username: string;
  content: string;
  likes: string[];
  comments: { id?: string; username?: string; content?: string }[];
  run?: { distance: number; duration: number; territory_captured: number } | null;
  created_at?: string;
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
  const [activeTab, setActiveTab] = useState<TabType>('clubs');

  const [stats, setStats] = useState<TerraStats | null>(null);
  const [runs, setRuns] = useState<TerraRun[]>([]);
  const [offlineRuns, setOfflineRuns] = useState<OfflineRun[]>([]);
  const [myClubs, setMyClubs] = useState<RunClub[]>([]);
  const [cityClubs, setCityClubs] = useState<RunClub[]>([]);
  const [selectedClub, setSelectedClub] = useState<RunClub | null>(null);
  const [clubMembers, setClubMembers] = useState<LeaderboardEntry[]>([]);
  const [feed, setFeed] = useState<SocialPost[]>([]);
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [plans, setPlans] = useState<TrainingPlan[]>([]);

  // Social
  const [postText, setPostText] = useState('');
  const [posting, setPosting] = useState(false);
  const [expandedPost, setExpandedPost] = useState<string | null>(null);
  const [commentTexts, setCommentTexts] = useState<Record<string, string>>({});
  const [submittingComment, setSubmittingComment] = useState<string | null>(null);

  // Run clubs
  const [showCreateClub, setShowCreateClub] = useState(false);
  const [clubName, setClubName] = useState('');
  const [clubCity, setClubCity] = useState('Your City');
  const [clubDescription, setClubDescription] = useState('');
  const [creatingClub, setCreatingClub] = useState(false);
  const [joiningClub, setJoiningClub] = useState<string | null>(null);

  // Create plan modal
  const [showCreatePlan, setShowCreatePlan] = useState(false);
  const [planGoal, setPlanGoal] = useState('5K');
  const [planLevel, setPlanLevel] = useState('intermediate');
  const [creatingPlan, setCreatingPlan] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, runsRes, myClubsRes, cityClubsRes, feedRes, compRes, plansRes, offline] =
        await Promise.all([
          api.get<TerraStats>('/terra/stats').catch(() => null),
          api.get<TerraRun[]>('/terra/runs').catch(() => []),
          api.get<RunClub[]>('/terra/clubs/my').catch(() => []),
          api.get<RunClub[]>('/terra/clubs/leaderboard/city').catch(() => []),
          api.get<SocialPost[]>('/terra/feed').catch(() => []),
          api.get<Competition>('/terra/competition/current').catch(() => null),
          api.get<TrainingPlan[]>('/terra/training-plans').catch(() => []),
          loadOfflineRuns(),
        ]);
      setStats(statsRes);
      setRuns(runsRes ?? []);
      setMyClubs(myClubsRes ?? []);
      setCityClubs(cityClubsRes ?? []);
      const nextSelected = selectedClub
        ? (myClubsRes ?? []).find((club) => club.id === selectedClub.id) || (cityClubsRes ?? []).find((club) => club.id === selectedClub.id) || null
        : (myClubsRes?.[0] ?? cityClubsRes?.[0] ?? null);
      setSelectedClub(nextSelected);
      if (nextSelected) {
        const members = await api.get<LeaderboardEntry[]>(`/terra/clubs/${nextSelected.id}/members/leaderboard`).catch(() => []);
        setClubMembers(members ?? []);
      } else {
        setClubMembers([]);
      }
      setFeed(feedRes ?? []);
      setCompetition(compRes);
      setPlans(plansRes ?? []);
      setOfflineRuns(offline);
    } catch (e) {
      console.error('Terra fetch error', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedClub]);

  useFocusEffect(useCallback(() => { fetchData(); }, [fetchData]));

  const onRefresh = useCallback(() => { setRefreshing(true); fetchData(); }, [fetchData]);

  const submitPost = useCallback(async () => {
    if (!postText.trim()) return;
    setPosting(true);
    try {
      await api.post('/terra/feed', { content: postText.trim() });
      setPostText('');
      await fetchData();
    } catch {
      Alert.alert('Error', 'Could not post. Try again.');
    } finally { setPosting(false); }
  }, [postText, fetchData]);

  const toggleLike = useCallback(async (id: string) => {
    try {
      await api.post(`/terra/feed/${id}/like`);
      setFeed((prev) => prev.map((p) =>
        p.id === id
          ? { ...p, likes: p.likes.includes('me') ? p.likes.filter((l) => l !== 'me') : [...p.likes, 'me'] }
          : p
      ));
    } catch { /* optimistic already applied */ }
  }, []);

  const submitComment = useCallback(async (postId: string) => {
    const text = (commentTexts[postId] ?? '').trim();
    if (!text) return;
    setSubmittingComment(postId);
    try {
      await api.post(`/terra/feed/${postId}/comments`, { content: text });
      setCommentTexts((prev) => ({ ...prev, [postId]: '' }));
      await fetchData();
    } catch {
      Alert.alert('Error', 'Could not post comment.');
    } finally {
      setSubmittingComment(null);
    }
  }, [commentTexts, fetchData]);

  const createClub = useCallback(async () => {
    if (!clubName.trim() || !clubCity.trim()) return;
    setCreatingClub(true);
    try {
      const club = await api.post<RunClub>('/terra/clubs', {
        name: clubName.trim(),
        city: clubCity.trim(),
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
  }, [clubName, clubCity, clubDescription, fetchData]);

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
  const selectedClubMember = clubMembers.find((entry) => entry.is_me);

  const TABS: { key: TabType; label: string; icon: string }[] = [
    { key: 'clubs', label: 'Clubs', icon: 'people-outline' },
    { key: 'overview', label: 'Stats', icon: 'stats-chart-outline' },
    { key: 'runs', label: 'Runs', icon: 'footsteps-outline' },
    { key: 'plans', label: 'Plans', icon: 'calendar-outline' },
  ];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* ── Header ── */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Run Club</Text>
          <Text style={styles.headerSub}>City teams ranked by distance.</Text>
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
            {/* ─────────── OVERVIEW ─────────── */}
            {activeTab === 'overview' && (
              <View>
                {/* Distance Hero */}
                <GlassCard style={styles.xpCard}>
                  <View style={styles.xpTopRow}>
                    <View>
                      <Text style={styles.xpLevelLabel}>RUN CLUB</Text>
                      <Text style={styles.xpNumbers}>{stats?.total_distance?.toFixed(1) ?? '0.0'} km</Text>
                    </View>
                    <View style={styles.xpBadge}>
                      <Text style={styles.xpBadgeText}>🏃</Text>
                    </View>
                  </View>
                  <Text style={styles.xpHint}>
                    {stats?.total_territory?.toFixed(3) ?? '0.000'} km² territory captured solo
                  </Text>
                </GlassCard>

                {/* Stats grid */}
                <View style={styles.statsGrid}>
                  {[
                    { icon: 'footsteps-outline', color: colors.textPrimary, val: String(stats?.total_runs ?? 0), lbl: 'Total Runs' },
                    { icon: 'speedometer-outline', color: colors.accentBlue, val: `${stats?.total_distance?.toFixed(1) ?? '0'}`, lbl: 'km Distance' },
                    { icon: 'map-outline', color: colors.statusSuccess, val: `${stats?.total_territory?.toFixed(2) ?? '0'}`, lbl: 'sq km Territory' },
                    { icon: 'flash-outline', color: colors.textPrimary, val: `${stats?.consistency ?? 0}%`, lbl: 'Consistency' },
                  ].map((s) => (
                    <GlassCard key={s.lbl} style={styles.statCard}>
                      <Ionicons name={s.icon as any} size={22} color={s.color} />
                      <Text style={styles.statVal}>{s.val}</Text>
                      <Text style={styles.statLbl}>{s.lbl}</Text>
                    </GlassCard>
                  ))}
                </View>

                {/* 7-day chart */}
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

                {/* Competition */}
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

                {/* Run Clubs Entry */}
                <TouchableOpacity onPress={() => router.push('/run/clubs' as any)}>
                  <GlassCard style={{ ...(styles.compCard as object), marginTop: 16 }}>
                    <View style={styles.compRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.compName}>Run Clubs</Text>
                        <Text style={styles.compPrize}>Discover and join local groups</Text>
                      </View>
                      <View style={styles.compDays}>
                         <Ionicons name="people-outline" size={32} color={colors.textPrimary} />
                      </View>
                    </View>
                  </GlassCard>
                </TouchableOpacity>
              </View>
            )}

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
                <View style={styles.clubHeroCard}>
                  <View style={styles.clubHeroTop}>
                    <View style={styles.clubHeroIcon}>
                      <Ionicons name="people" size={22} color={colors.textPrimary} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.clubHeroEyebrow}>CITY TEAMS</Text>
                      <Text style={styles.clubHeroTitle}>Run Club</Text>
                      <Text style={styles.clubHeroSub}>Your kilometers lift your club. Your loops capture territory for you.</Text>
                    </View>
                  </View>
                  <View style={styles.clubHeroStats}>
                    <View style={styles.clubHeroMetric}>
                      <Text style={styles.clubHeroMetricVal}>{stats?.total_distance?.toFixed(1) ?? '0.0'}</Text>
                      <Text style={styles.clubHeroMetricLabel}>your km</Text>
                    </View>
                    <View style={styles.clubHeroDivider} />
                    <View style={styles.clubHeroMetric}>
                      <Text style={styles.clubHeroMetricVal}>{myClubs.length}</Text>
                      <Text style={styles.clubHeroMetricLabel}>clubs</Text>
                    </View>
                    <View style={styles.clubHeroDivider} />
                    <View style={styles.clubHeroMetric}>
                      <Text style={styles.clubHeroMetricVal}>{stats?.total_territory?.toFixed(2) ?? '0.00'}</Text>
                      <Text style={styles.clubHeroMetricLabel}>km²</Text>
                    </View>
                  </View>
                </View>

                <View style={styles.sectionRow}>
                  <Text style={styles.sectionTitle}>Your Clubs</Text>
                  <TouchableOpacity style={styles.addPlanBtn} onPress={() => setShowCreateClub(true)}>
                    <Ionicons name="add" size={18} color={colors.textPrimary} />
                    <Text style={styles.addPlanText}>Create</Text>
                  </TouchableOpacity>
                </View>

                {myClubs.length === 0 ? (
                  <GlassCard style={styles.clubEmptyCard}>
                    <Text style={styles.emptyTitle}>No club yet</Text>
                    <Text style={styles.emptySub}>Create a club or join one in your city to start contributing kilometers.</Text>
                  </GlassCard>
                ) : (
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.clubScroll}>
                    {myClubs.map((club) => (
                      <TouchableOpacity key={club.id} onPress={() => openClub(club)} activeOpacity={0.85}>
                        <GlassCard style={StyleSheet.flatten([styles.clubCard, selectedClub?.id === club.id ? styles.clubCardActive : undefined])}>
                          <View style={styles.clubCardTop}>
                            {selectedClub?.id === club.id && <View style={styles.activeDot} />}
                            <Text style={styles.clubCity}>{club.city}</Text>
                          </View>
                          <Text style={styles.clubName} numberOfLines={2}>{club.name}</Text>
                          <Text style={styles.clubDistance}>{club.total_distance.toFixed(1)} km</Text>
                          <View style={styles.clubCardMetaRow}>
                            <Text style={styles.clubMeta}>{club.member_count} members</Text>
                            <Text style={styles.clubMeta}>{club.total_territory.toFixed(2)} km²</Text>
                          </View>
                        </GlassCard>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                )}

                {selectedClub && (
                  <GlassCard style={styles.selectedClubCard}>
                    <View style={styles.selectedClubHeader}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.selectedClubName}>{selectedClub.name}</Text>
                        <Text style={styles.selectedClubMeta}>{selectedClub.city} · {selectedClub.member_count} members</Text>
                      </View>
                      {selectedClub.is_member ? (
                        <View style={styles.memberBadge}>
                          <Text style={styles.memberBadgeText}>Joined</Text>
                        </View>
                      ) : (
                        <TouchableOpacity style={styles.joinBtn} onPress={() => joinClub(selectedClub)} disabled={joiningClub === selectedClub.id}>
                          {joiningClub === selectedClub.id
                            ? <ActivityIndicator size="small" color={colors.background} />
                            : <Text style={styles.joinBtnText}>Join</Text>}
                        </TouchableOpacity>
                      )}
                    </View>
                    {!!selectedClub.description && (
                      <Text style={styles.selectedClubDescription}>{selectedClub.description}</Text>
                    )}
                    <View style={styles.selectedMetrics}>
                      <View style={styles.selectedMetric}>
                        <Text style={styles.selectedMetricVal}>{selectedClub.total_distance.toFixed(1)}</Text>
                        <Text style={styles.selectedMetricLabel}>club km</Text>
                      </View>
                      <View style={styles.selectedMetric}>
                        <Text style={styles.selectedMetricVal}>{selectedClub.average_distance_per_member.toFixed(1)}</Text>
                        <Text style={styles.selectedMetricLabel}>km/member</Text>
                      </View>
                      <View style={styles.selectedMetric}>
                        <Text style={styles.selectedMetricVal}>{selectedClub.total_territory.toFixed(2)}</Text>
                        <Text style={styles.selectedMetricLabel}>km²</Text>
                      </View>
                    </View>
                    <View style={styles.activeMembersStrip}>
                      <Ionicons name="pulse-outline" size={16} color={colors.textSecondary} />
                      <Text style={styles.activeMembersText}>{selectedClub.active_members} active runners · {selectedClub.total_runs} total runs</Text>
                    </View>
                    {selectedClubMember && (
                      <View style={styles.contributionRow}>
                        <Text style={styles.contributionLabel}>Your contribution</Text>
                        <Text style={styles.contributionValue}>{(selectedClubMember.total_distance ?? 0).toFixed(1)} km · #{selectedClubMember.rank}</Text>
                      </View>
                    )}
                  </GlassCard>
                )}

                <View style={styles.sectionRow}>
                  <Text style={styles.sectionTitle}>City Club Leaderboard</Text>
                  <Text style={styles.sectionMeta}>All time</Text>
                </View>
                {cityClubs.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="people-outline" size={48} color={colors.textTertiary} />
                    <Text style={styles.emptyTitle}>No clubs in your city</Text>
                    <Text style={styles.emptySub}>Create the first one.</Text>
                  </View>
                ) : (
                  cityClubs.map((club, idx) => (
                    <GlassCard key={club.id} style={styles.lbCard}>
                      <View style={StyleSheet.flatten([styles.rankBadge, idx === 0 ? styles.rankGold : idx === 1 ? styles.rankSilver : idx === 2 ? styles.rankBronze : undefined])}>
                        <Text style={styles.rankText}>#{club.rank ?? idx + 1}</Text>
                      </View>
                      <TouchableOpacity style={{ flex: 1 }} onPress={() => openClub(club)}>
                        <Text style={styles.lbName}>{club.name}</Text>
                        <Text style={styles.lbMeta}>{club.city} · {club.member_count} members · {club.active_members} active</Text>
                      </TouchableOpacity>
                      <View style={styles.lbStats}>
                        <Text style={styles.lbDistance}>{club.total_distance.toFixed(1)} km</Text>
                        <Text style={styles.lbTerritory}>{club.average_distance_per_member.toFixed(1)} km/member</Text>
                      </View>
                      {!club.is_member && (
                        <TouchableOpacity style={styles.joinBtn} onPress={() => joinClub(club)} disabled={joiningClub === club.id}>
                          {joiningClub === club.id
                            ? <ActivityIndicator size="small" color={colors.background} />
                            : <Text style={styles.joinBtnText}>Join</Text>}
                        </TouchableOpacity>
                      )}
                    </GlassCard>
                  ))
                )}

                {selectedClub && (
                  <>
                    <View style={[styles.sectionRow, { marginTop: spacing.lg }]}>
                      <Text style={styles.sectionTitle}>{selectedClub.name} Members</Text>
                      <Text style={styles.sectionMeta}>Top distance</Text>
                    </View>
                    {clubMembers.length === 0 ? (
                      <Text style={styles.emptySub}>No member runs yet.</Text>
                    ) : (
                      clubMembers.map((entry, idx) => (
                        <GlassCard key={`${selectedClub.id}-${entry.rank}`} style={styles.lbCard}>
                          <View style={styles.rankBadge}>
                            <Text style={styles.rankText}>#{entry.rank ?? idx + 1}</Text>
                          </View>
                          <View style={{ flex: 1 }}>
                            <Text style={styles.lbName}>{entry.username}</Text>
                            <Text style={styles.lbMeta}>{entry.total_runs ?? 0} runs · {entry.total_territory.toFixed(3)} km² territory</Text>
                          </View>
                          <View style={styles.lbStats}>
                            <Text style={styles.lbDistance}>{(entry.total_distance ?? 0).toFixed(1)} km</Text>
                          </View>
                        </GlassCard>
                      ))
                    )}
                  </>
                )}
              </View>
            )}

            {/* ─────────── SOCIAL ─────────── */}
            {activeTab === 'social' && (
              <View>
                {/* Composer */}
                <GlassCard style={styles.composerCard}>
                  <TextInput
                    style={styles.composerInput}
                    placeholder="Share your run with the community…"
                    placeholderTextColor={colors.textTertiary}
                    value={postText}
                    onChangeText={setPostText}
                    multiline
                  />
                  <TouchableOpacity
                    style={[styles.postBtn, (!postText.trim() || posting) && styles.postBtnDisabled]}
                    onPress={submitPost}
                    disabled={!postText.trim() || posting}
                  >
                    {posting
                      ? <ActivityIndicator size="small" color={colors.background} />
                      : <><Ionicons name="send" size={16} color={colors.background} /><Text style={styles.postBtnText}>Post</Text></>}
                  </TouchableOpacity>
                </GlassCard>

                {feed.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="chatbubble-ellipses-outline" size={48} color={colors.textTertiary} />
                    <Text style={styles.emptyTitle}>No posts yet</Text>
                    <Text style={styles.emptySub}>Be the first to share a run!</Text>
                  </View>
                ) : (
                  feed.map((post) => {
                    const expanded = expandedPost === post.id;
                    return (
                      <GlassCard key={post.id} style={styles.postCard}>
                        {/* Post header */}
                        <View style={styles.postHeader}>
                          <View style={styles.postAvatar}>
                            <Text style={styles.postAvatarText}>{post.username[0]?.toUpperCase()}</Text>
                          </View>
                          <View style={{ flex: 1 }}>
                            <Text style={styles.postAuthor}>{post.username}</Text>
                            <Text style={styles.postTime}>{fmtRelative(post.created_at)}</Text>
                          </View>
                        </View>

                        {/* Content */}
                        <Text style={styles.postContent}>{post.content}</Text>

                        {/* Attached run */}
                        {post.run && (
                          <View style={styles.postRunStrip}>
                            <Ionicons name="footsteps-outline" size={14} color={colors.textPrimary} />
                            <Text style={styles.postRunText}>
                              {post.run.distance.toFixed(1)} km · {fmtDuration(post.run.duration)} · {post.run.territory_captured.toFixed(3)} km²
                            </Text>
                          </View>
                        )}

                        {/* Actions */}
                        <View style={styles.postActions}>
                          <TouchableOpacity style={styles.postAction} onPress={() => toggleLike(post.id)}>
                            <Ionicons name="heart-outline" size={18} color={colors.textPrimary} />
                            <Text style={styles.postActionText}>{post.likes.length}</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={styles.postAction}
                            onPress={() => setExpandedPost(expanded ? null : post.id)}
                          >
                            <Ionicons name="chatbubble-outline" size={17} color={colors.textSecondary} />
                            <Text style={styles.postActionText}>{post.comments.length}</Text>
                          </TouchableOpacity>
                        </View>

                        {/* Comments */}
                        {expanded && (
                          <View style={styles.commentsSection}>
                            {post.comments.length > 0 ? (
                              post.comments.map((c, i) => (
                                <View key={c.id ?? i} style={styles.commentRow}>
                                  <Text style={styles.commentAuthor}>{c.username ?? 'User'}</Text>
                                  <Text style={styles.commentContent}>{c.content}</Text>
                                </View>
                              ))
                            ) : (
                              <Text style={styles.noComments}>No comments yet.</Text>
                            )}
                            <View style={styles.commentInputRow}>
                              <TextInput
                                style={styles.commentInput}
                                placeholder="Add a comment…"
                                placeholderTextColor={colors.textTertiary}
                                value={commentTexts[post.id] ?? ''}
                                onChangeText={(t) => setCommentTexts((prev) => ({ ...prev, [post.id]: t }))}
                                returnKeyType="send"
                                onSubmitEditing={() => submitComment(post.id)}
                              />
                              <TouchableOpacity
                                style={[styles.commentSendBtn, submittingComment === post.id && { opacity: 0.4 }]}
                                onPress={() => submitComment(post.id)}
                                disabled={submittingComment === post.id}
                              >
                                {submittingComment === post.id
                                  ? <ActivityIndicator size="small" color={colors.textPrimary} />
                                  : <Ionicons name="send" size={16} color={colors.textPrimary} />}
                              </TouchableOpacity>
                            </View>
                          </View>
                        )}
                      </GlassCard>
                    );
                  })
                )}
              </View>
            )}

            {/* ─────────── PLANS ─────────── */}
            {activeTab === 'plans' && (
              <View>
                <View style={styles.sectionRow}>
                  <Text style={styles.sectionTitle}>Training Plans</Text>
                  <TouchableOpacity style={styles.addPlanBtn} onPress={() => setShowCreatePlan(true)}>
                    <Ionicons name="add" size={18} color={colors.textPrimary} />
                    <Text style={styles.addPlanText}>New Plan</Text>
                  </TouchableOpacity>
                </View>

                {plans.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Ionicons name="calendar-outline" size={56} color={colors.textTertiary} />
                    <Text style={styles.emptyTitle}>No training plan</Text>
                    <Text style={styles.emptySub}>Create a goal-specific plan and track your progress.</Text>
                    <TouchableOpacity style={styles.emptyBtn} onPress={() => setShowCreatePlan(true)}>
                      <Text style={styles.emptyBtnText}>Create Plan</Text>
                    </TouchableOpacity>
                  </View>
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
          </>
        )}
      </ScrollView>

      {/* ── Floating Start Run Button ── */}
      <TouchableOpacity
        style={[styles.fab, { bottom: insets.bottom + 20 }]}
        onPress={() => router.push('/run/track')}
        activeOpacity={0.85}
      >
        <LinearGradient colors={[colors.textPrimary, '#2B2B2B']} style={styles.fabGrad}>
          <Ionicons name="play" size={20} color={colors.background} />
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

            <Text style={styles.modalLabel}>Club Name</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Runlete Hyderabad Runners"
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
  sectionMeta: { ...typography.caption, color: colors.textTertiary },

  // XP Card
  xpCard: { padding: spacing.lg },
  xpTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md },
  xpLevelLabel: { ...typography.caption, color: colors.textSecondary, fontWeight: '700', letterSpacing: 1 },
  xpNumbers: { ...typography.h3, color: colors.textPrimary, marginTop: 2 },
  xpBadge: { width: 48, height: 48, borderRadius: 24, backgroundColor: colors.surfaceSecondary, alignItems: 'center', justifyContent: 'center' },
  xpBadgeText: { fontSize: 22 },
  xpTrack: { height: 8, backgroundColor: colors.surface, borderRadius: 4, overflow: 'hidden', marginBottom: spacing.xs },
  xpFill: { height: '100%', backgroundColor: colors.textPrimary, borderRadius: 4 },
  xpHint: { ...typography.caption, color: colors.textTertiary },

  // Stats grid
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  statCard: { width: (width - spacing.lg * 2 - spacing.sm) / 2 - 1, padding: spacing.md, alignItems: 'center', gap: spacing.xs },
  statVal: { ...typography.h3, color: colors.textPrimary },
  statLbl: { ...typography.caption, color: colors.textSecondary, textAlign: 'center' },

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
  vaultScroll: { gap: spacing.sm, paddingVertical: spacing.sm },
  vaultItem: { width: 90, alignItems: 'center', backgroundColor: colors.surface, borderRadius: borderRadius.md, padding: spacing.md, gap: 4 },
  vaultLocked: { opacity: 0.4 },
  vaultEmoji: { fontSize: 28 },
  vaultName: { ...typography.caption, color: colors.textPrimary, textAlign: 'center', fontSize: 11 },
  vaultStatus: { fontSize: 10, color: colors.textTertiary },
  vaultUnlocked: { color: colors.statusSuccess },

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
  lbToggle: { flexDirection: 'row', backgroundColor: colors.surface, borderRadius: borderRadius.full, padding: 3, marginBottom: spacing.md },
  lbToggleBtn: { flex: 1, paddingVertical: spacing.sm, borderRadius: borderRadius.full, alignItems: 'center' },
  lbToggleBtnActive: { backgroundColor: colors.textPrimary },
  lbToggleText: { ...typography.caption, color: colors.textSecondary, fontWeight: '600' },
  lbToggleTextActive: { color: colors.background },
  lbCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md, marginBottom: spacing.sm },
  lbCardMe: { borderWidth: 1, borderColor: colors.textPrimary },
  lbCardPlaceholder: { opacity: 0.5 },
  rankBadge: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  rankGold: { backgroundColor: '#FFD70020' },
  rankSilver: { backgroundColor: '#C0C0C020' },
  rankBronze: { backgroundColor: '#CD7F3220' },
  rankText: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  lbNameRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  lbName: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  lbNameMe: { color: colors.textPrimary },
  lbMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  lbStats: { alignItems: 'flex-end' },
  lbDistance: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  lbTerritory: { ...typography.caption, color: colors.textTertiary },
  meBadge: { backgroundColor: colors.textPrimary, paddingHorizontal: spacing.xs, paddingVertical: 1, borderRadius: 4 },
  meBadgeText: { fontSize: 10, color: colors.background, fontWeight: '700' },
  ghostBadge: { backgroundColor: colors.textTertiary + '30', paddingHorizontal: spacing.xs, paddingVertical: 1, borderRadius: 4 },
  ghostText: { fontSize: 10, color: colors.textTertiary },

  // Clubs
  clubHeroCard: {
    padding: spacing.lg,
    marginBottom: spacing.xl,
    gap: spacing.lg,
    backgroundColor: '#F6F4EF',
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: '#EEECE8',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.08,
    shadowRadius: 20,
    elevation: 4,
  },
  clubHeroTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  clubHeroIcon: { width: 46, height: 46, borderRadius: 23, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' },
  clubHeroEyebrow: { fontSize: 11, lineHeight: 15, fontWeight: '800', letterSpacing: 0.8, color: '#8D8880', marginBottom: 2 },
  clubHeroTitle: { fontSize: 26, lineHeight: 32, fontWeight: '800', color: colors.textPrimary },
  clubHeroSub: { fontSize: 13, lineHeight: 19, color: '#756F67', marginTop: 4 },
  clubHeroStats: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#FFFFFF', borderRadius: borderRadius.lg, padding: spacing.md },
  clubHeroMetric: { flex: 1, alignItems: 'center' },
  clubHeroMetricVal: { ...typography.h4, color: colors.textPrimary },
  clubHeroMetricLabel: { ...typography.caption, color: colors.textTertiary, fontSize: 11 },
  clubHeroDivider: { width: 1, height: 34, backgroundColor: colors.separatorDark },
  clubEmptyCard: { padding: spacing.lg, marginBottom: spacing.md, gap: spacing.xs, borderColor: colors.separatorDark },
  clubScroll: { gap: spacing.md, paddingBottom: spacing.md },
  clubCard: { width: 204, padding: spacing.md, gap: spacing.xs, borderColor: colors.separatorDark },
  clubCardActive: { borderWidth: 1.5, borderColor: colors.textPrimary, backgroundColor: '#FAFAFA' },
  clubCardTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  clubName: { fontSize: 17, lineHeight: 22, color: colors.textPrimary, fontWeight: '800', marginTop: spacing.xs, minHeight: 44 },
  clubCity: { fontSize: 12, lineHeight: 16, color: colors.textTertiary, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.4 },
  clubDistance: { fontSize: 28, lineHeight: 34, color: colors.textPrimary, fontWeight: '800', marginTop: spacing.sm },
  clubMeta: { fontSize: 12, lineHeight: 17, color: colors.textSecondary, fontWeight: '600' },
  clubCardMetaRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.xs },
  activeDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.textPrimary },
  selectedClubCard: { padding: spacing.lg, marginBottom: spacing.xl, gap: spacing.md, borderColor: colors.separatorDark },
  selectedClubHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  selectedClubName: { ...typography.h3, color: colors.textPrimary },
  selectedClubMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 3 },
  selectedClubDescription: { ...typography.caption, color: colors.textSecondary, lineHeight: 20 },
  selectedMetrics: { flexDirection: 'row', gap: spacing.sm },
  selectedMetric: { flex: 1, backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.md, padding: spacing.md, alignItems: 'center' },
  selectedMetricVal: { fontSize: 18, lineHeight: 24, fontWeight: '800', color: colors.textPrimary },
  selectedMetricLabel: { ...typography.caption, color: colors.textTertiary, fontSize: 11, textAlign: 'center' },
  activeMembersStrip: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  activeMembersText: { ...typography.caption, color: colors.textSecondary, fontWeight: '600' },
  memberBadge: { backgroundColor: '#111111', paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full },
  memberBadgeText: { ...typography.caption, color: '#FFFFFF', fontWeight: '700' },
  contributionRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderTopWidth: 1, borderTopColor: colors.separator, paddingTop: spacing.md },
  contributionLabel: { ...typography.caption, color: colors.textSecondary },
  contributionValue: { ...typography.caption, color: colors.textPrimary, fontWeight: '700' },
  joinBtn: { backgroundColor: colors.textPrimary, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: borderRadius.full, minWidth: 58, alignItems: 'center' },
  joinBtnText: { color: '#FFFFFF', fontWeight: '700', fontSize: 12 },

  // Social
  composerCard: { padding: spacing.md, marginBottom: spacing.md },
  composerInput: { ...typography.body, color: colors.textPrimary, minHeight: 60, textAlignVertical: 'top', marginBottom: spacing.md },
  postBtn: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, backgroundColor: colors.textPrimary, paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, borderRadius: borderRadius.full, alignSelf: 'flex-end' },
  postBtnDisabled: { opacity: 0.4 },
  postBtnText: { color: colors.background, fontWeight: '700', fontSize: 13 },
  postCard: { padding: spacing.md, marginBottom: spacing.md },
  postHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm },
  postAvatar: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.surfaceSecondary, alignItems: 'center', justifyContent: 'center' },
  postAvatarText: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  postAuthor: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  postTime: { ...typography.caption, color: colors.textTertiary },
  postContent: { ...typography.body, color: colors.textPrimary, lineHeight: 22, marginBottom: spacing.sm },
  postRunStrip: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, backgroundColor: colors.surfaceSecondary, padding: spacing.sm, borderRadius: borderRadius.sm, marginBottom: spacing.sm },
  postRunText: { ...typography.caption, color: colors.textPrimary },
  postActions: { flexDirection: 'row', gap: spacing.lg, borderTopWidth: 1, borderTopColor: colors.separator, paddingTop: spacing.sm },
  postAction: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  postActionText: { ...typography.caption, color: colors.textSecondary },
  commentsSection: { marginTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.separator, paddingTop: spacing.md, gap: spacing.sm },
  commentRow: { gap: 2 },
  commentAuthor: { ...typography.caption, color: colors.textPrimary, fontWeight: '600' },
  commentContent: { ...typography.caption, color: colors.textSecondary },
  noComments: { ...typography.caption, color: colors.textTertiary, textAlign: 'center', paddingVertical: spacing.sm },
  commentInputRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.xs },
  commentInput: { flex: 1, backgroundColor: colors.surface, borderRadius: borderRadius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, ...typography.caption, color: colors.textPrimary },
  commentSendBtn: { padding: spacing.sm },

  // Plans
  addPlanBtn: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  addPlanText: { ...typography.caption, color: colors.textPrimary, fontWeight: '600' },
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
});

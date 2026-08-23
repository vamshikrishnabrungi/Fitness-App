import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api, ApiError } from '../../../src/utils/api';
import { ClubTerritoryMap } from '../../../src/components/ClubTerritoryMap';
import { colors, spacing } from '../../../src/utils/theme';

type Tab =
  | 'overview'
  | 'leaderboard'
  | 'territory'
  | 'challenges'
  | 'races'
  | 'activity'
  | 'members';

interface Club {
  id: string;
  name: string;
  description?: string | null;
  rules?: string | null;
  primary_color: string;
  visibility: 'public' | 'private';
  status: string;
  member_count: number;
  membership_role?: 'owner' | 'admin' | 'member' | null;
  membership_status?: string | null;
  is_primary: boolean;
  competitive_profile_version: number;
  version: number;
}

interface Athlete {
  id: string;
  name: string;
  avatar_url?: string | null;
}

interface LeaderboardRow {
  rank: number;
  athlete_id: string;
  display_name: string;
  value: number;
  is_me: boolean;
}

interface Challenge {
  id: string;
  name: string;
  description?: string;
  metric: string;
  target?: number;
  starts_at: string;
  ends_at: string;
  status: string;
  participant_count: number;
  is_joined: boolean;
}

interface Race {
  id: string;
  name: string;
  description?: string;
  starts_at: string;
  route_distance_m: number;
  participant_count: number;
  participant_capacity?: number;
  status: string;
  is_joined: boolean;
}

interface ClubEvent {
  id: string;
  event_type: string;
  actor_user_id?: string;
  payload: Record<string, any>;
  occurred_at: string;
}

interface ClubMember {
  id: string;
  user_id: string;
  role: string;
  athlete?: Athlete;
}

interface Achievement {
  id: string;
  title: string;
  awarded_at: string;
  athlete?: Athlete;
}

const key = (scope: string) =>
  `${scope}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const metricLabel = (metric: string) =>
  ({
    distance: 'Distance',
    duration: 'Moving time',
    run_count: 'Runs',
    consistency: 'Consistency',
    territory_gain: 'Territory gain',
    fastest_segment: 'Fastest segment',
  })[metric] || metric;

const dateLabel = (value: string) =>
  new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

export default function ClubDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [club, setClub] = useState<Club | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [races, setRaces] = useState<Race[]>([]);
  const [events, setEvents] = useState<ClubEvent[]>([]);
  const [members, setMembers] = useState<ClubMember[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [tab, setTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setError(null);
    try {
      const detail = await api.get<Club>(`/clubs/${id}`);
      setClub(detail);
      if (detail.membership_status === 'active') {
        const [
          board,
          clubChallenges,
          clubRaces,
          activity,
          clubMembers,
          clubAchievements,
        ] = await Promise.all([
          api.get<{ items: LeaderboardRow[] }>(
            `/clubs/${id}/leaderboards?period=week&metric=distance`,
          ),
          api.get<{ items: Challenge[] }>(`/clubs/${id}/challenges`),
          api.get<{ items: Race[] }>(`/clubs/${id}/races`),
          api.get<{ items: ClubEvent[] }>(`/clubs/${id}/activity?limit=50`),
          api.get<{ items: ClubMember[] }>(
            `/clubs/${id}/members?status=active&limit=100`,
          ),
          api.get<{ items: Achievement[] }>(
            `/clubs/${id}/achievements?limit=20`,
          ),
        ]);
        setLeaderboard(board.items);
        setChallenges(clubChallenges.items);
        setRaces(clubRaces.items);
        setEvents(activity.items);
        setMembers(clubMembers.items);
        setAchievements(clubAchievements.items);
      }
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Club could not be loaded.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const isAdmin = club?.membership_role === 'owner' || club?.membership_role === 'admin';
  const isMember = club?.membership_status === 'active';

  const join = async () => {
    if (!club) return;
    setWorking('join');
    try {
      await api.post(
        `/clubs/${club.id}/join`,
        undefined,
        { 'Idempotency-Key': key('join-club') },
      );
      await load();
    } catch (reason) {
      Alert.alert('Could not join', reason instanceof Error ? reason.message : 'Please try again.');
    } finally {
      setWorking(null);
    }
  };

  const setPrimary = async () => {
    if (!club) return;
    setWorking('primary');
    try {
      await api.put(
        '/clubs/primary',
        { club_id: club.id, expected_version: club.competitive_profile_version },
        { 'Idempotency-Key': key('primary-club') },
      );
      await load();
    } catch (reason) {
      Alert.alert(
        'Primary club not changed',
        reason instanceof Error ? reason.message : 'Please try again.',
      );
    } finally {
      setWorking(null);
    }
  };

  const joinCompetition = async (kind: 'challenge' | 'race', itemId: string) => {
    setWorking(itemId);
    try {
      await api.post(
        `/${kind === 'challenge' ? 'challenges' : 'races'}/${itemId}/join`,
        undefined,
        { 'Idempotency-Key': key(`join-${kind}`) },
      );
      await load();
    } catch (reason) {
      Alert.alert('Could not join', reason instanceof Error ? reason.message : 'Please try again.');
    } finally {
      setWorking(null);
    }
  };

  const controlCopy = useMemo(() => {
    if (!club) return '';
    if (club.is_primary) return 'Your verified future runs contribute to this club.';
    return 'You can belong here without double-counting runs. Select it as primary to contribute.';
  }, [club]);

  if (loading) {
    return (
      <SafeAreaView style={styles.loading}>
        <ActivityIndicator color={colors.brand} />
      </SafeAreaView>
    );
  }

  if (!club || error) {
    return (
      <SafeAreaView style={styles.loading}>
        <Ionicons name="alert-circle-outline" size={34} color={colors.textTertiary} />
        <Text style={styles.errorTitle}>Club unavailable</Text>
        <Text style={styles.errorBody}>{error}</Text>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backText}>Go back</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {club.name}
        </Text>
        {isAdmin ? (
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => router.push(`/run/clubs/${club.id}/admin` as any)}
          >
            <Ionicons name="settings-outline" size={21} color={colors.textPrimary} />
          </TouchableOpacity>
        ) : (
          <View style={{ width: 40 }} />
        )}
      </View>

      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              load();
            }}
          />
        }
        contentContainerStyle={styles.content}
      >
        <View style={[styles.hero, { backgroundColor: club.primary_color || '#FF4F2E' }]}>
          <View style={styles.heroTop}>
            <Text style={styles.heroEmoji}>{club.name.slice(0, 1).toUpperCase()}</Text>
            <View style={styles.visibilityBadge}>
              <Ionicons
                name={club.visibility === 'private' ? 'lock-closed' : 'globe-outline'}
                size={11}
                color="#FFFFFF"
              />
              <Text style={styles.visibilityText}>
                {club.visibility === 'private' ? 'PRIVATE' : 'PUBLIC'}
              </Text>
            </View>
          </View>
          <Text style={styles.heroName}>{club.name}</Text>
          <Text style={styles.heroMembers}>
            {club.member_count} member{club.member_count === 1 ? '' : 's'}
          </Text>
          {!!club.description && <Text style={styles.heroDescription}>{club.description}</Text>}
        </View>

        {!isMember ? (
          <View style={styles.joinCard}>
            <Text style={styles.joinTitle}>
              {club.membership_status === 'requested'
                ? 'Membership pending'
                : 'Join this run club'}
            </Text>
            <Text style={styles.joinBody}>
              {club.membership_status === 'requested'
                ? 'An owner or admin will review your request.'
                : club.visibility === 'private'
                  ? 'Your request must be approved before club activity becomes visible.'
                  : 'Membership is immediate. Your runs count only if you later make this your primary club.'}
            </Text>
            {club.membership_status !== 'requested' && (
              <TouchableOpacity style={styles.primaryAction} onPress={join} disabled={working === 'join'}>
                {working === 'join' ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.primaryActionText}>Join club</Text>
                )}
              </TouchableOpacity>
            )}
          </View>
        ) : (
          <View style={styles.attributionCard}>
            <View style={styles.attributionIcon}>
              <Ionicons
                name={club.is_primary ? 'shield-checkmark' : 'swap-horizontal-outline'}
                size={20}
                color={club.is_primary ? '#138772' : colors.brand}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.attributionTitle}>
                {club.is_primary ? 'Primary competitive club' : 'Secondary membership'}
              </Text>
              <Text style={styles.attributionBody}>{controlCopy}</Text>
            </View>
            {!club.is_primary && (
              <TouchableOpacity onPress={setPrimary} disabled={working === 'primary'}>
                <Text style={styles.makePrimary}>Make primary</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {isMember && (
          <>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.tabs}
            >
              {(
                [
                  ['overview', 'Overview'],
                  ['leaderboard', 'Leaderboard'],
                  ['territory', 'Territory'],
                  ['challenges', 'Challenges'],
                  ['races', 'Races'],
                  ['activity', 'Activity'],
                  ['members', 'Members'],
                ] as [Tab, string][]
              ).map(([keyName, label]) => (
                <TouchableOpacity
                  key={keyName}
                  style={[styles.tab, tab === keyName && styles.tabActive]}
                  onPress={() => setTab(keyName)}
                >
                  <Text style={[styles.tabText, tab === keyName && styles.tabTextActive]}>
                    {label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {tab === 'overview' && (
              <>
                <View style={styles.statGrid}>
                  <View style={styles.statCard}>
                    <Ionicons name="people-outline" size={20} color="#4F84E8" />
                    <Text style={styles.statValue}>{club.member_count}</Text>
                    <Text style={styles.statLabel}>Members</Text>
                  </View>
                  <View style={styles.statCard}>
                    <Ionicons name="footsteps-outline" size={20} color={colors.brand} />
                    <Text style={styles.statValue}>
                      {((leaderboard.reduce((sum, row) => sum + row.value, 0) || 0) / 1000).toFixed(0)}
                    </Text>
                    <Text style={styles.statLabel}>km this week</Text>
                  </View>
                </View>
                <TouchableOpacity
                  style={styles.territoryCard}
                  onPress={() => setTab('territory')}
                >
                  <View style={styles.territoryIcon}>
                    <Ionicons name="map" size={22} color="#62E6D1" />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.territoryTitle}>Club road control</Text>
                    <Text style={styles.territoryBody}>
                      View verified road edges, control points, and expiry windows on the map.
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color="#FFFFFF" />
                </TouchableOpacity>
                {!!club.rules && (
                  <View style={styles.rulesCard}>
                    <Text style={styles.cardTitle}>Club rules</Text>
                    <Text style={styles.rulesBody}>{club.rules}</Text>
                  </View>
                )}
                {!!achievements.length && (
                  <View style={styles.rulesCard}>
                    <Text style={styles.cardTitle}>Recent achievements</Text>
                    {achievements.slice(0, 4).map((achievement) => (
                      <View key={achievement.id} style={styles.achievementRow}>
                        <Ionicons name="ribbon-outline" size={18} color="#D79822" />
                        <View style={{ flex: 1 }}>
                          <Text style={styles.runnerName}>{achievement.title}</Text>
                          <Text style={styles.runnerMeta}>
                            {achievement.athlete?.name || 'Runner'} ·{' '}
                            {dateLabel(achievement.awarded_at)}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                )}
              </>
            )}

            {tab === 'leaderboard' && (
              <View style={styles.listSection}>
                <Text style={styles.cardTitle}>Weekly distance</Text>
                {leaderboard.length ? (
                  leaderboard.map((row) => (
                    <View key={row.athlete_id} style={[styles.rankRow, row.is_me && styles.myRank]}>
                      <Text style={styles.rankNumber}>{row.rank}</Text>
                      <View style={styles.avatar}>
                        <Text style={styles.avatarText}>
                          {(row.display_name || 'R').slice(0, 1).toUpperCase()}
                        </Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.runnerName}>
                          {row.display_name || 'Runner'}
                          {row.is_me ? ' · You' : ''}
                        </Text>
                        <Text style={styles.runnerMeta}>Verified weekly distance</Text>
                      </View>
                      <Text style={styles.runnerScore}>{(row.value / 1000).toFixed(1)} km</Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.emptyText}>No verified club runs in this period.</Text>
                )}
              </View>
            )}

            {tab === 'territory' && <ClubTerritoryMap clubId={club.id} />}

            {tab === 'challenges' && (
              <>
                <View style={styles.sectionHeader}>
                  <Text style={styles.cardTitle}>Challenges</Text>
                  {isAdmin && (
                    <TouchableOpacity
                      onPress={() => router.push(`/run/clubs/${club.id}/challenge-create` as any)}
                    >
                      <Text style={styles.addText}>Create</Text>
                    </TouchableOpacity>
                  )}
                </View>
                {challenges.map((challenge) => (
                  <View key={challenge.id} style={styles.competitionCard}>
                    <View style={styles.competitionTop}>
                      <View style={styles.challengeIcon}>
                        <Ionicons name="flag" size={18} color="#7A55D6" />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.competitionName}>{challenge.name}</Text>
                        <Text style={styles.competitionMeta}>
                          {metricLabel(challenge.metric)} · ends {dateLabel(challenge.ends_at)}
                        </Text>
                      </View>
                    </View>
                    <View style={styles.competitionFooter}>
                      <Text style={styles.participants}>
                        {challenge.participant_count} joined
                      </Text>
                      <TouchableOpacity
                        style={[styles.smallAction, challenge.is_joined && styles.joinedAction]}
                        disabled={challenge.is_joined || working === challenge.id}
                        onPress={() => joinCompetition('challenge', challenge.id)}
                      >
                        <Text style={styles.smallActionText}>
                          {challenge.is_joined ? 'Joined' : 'Join challenge'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ))}
                {!challenges.length && <Text style={styles.emptyText}>No active challenges.</Text>}

              </>
            )}

            {tab === 'races' && (
              <>
                <View style={styles.sectionHeader}>
                  <Text style={styles.cardTitle}>Scheduled races</Text>
                  {isAdmin && (
                    <TouchableOpacity
                      onPress={() => router.push(`/run/clubs/${club.id}/race-create` as any)}
                    >
                      <Text style={styles.addText}>Schedule</Text>
                    </TouchableOpacity>
                  )}
                </View>
                {races.map((race) => (
                  <View key={race.id} style={styles.competitionCard}>
                    <View style={styles.competitionTop}>
                      <View style={styles.raceIcon}>
                        <Ionicons name="stopwatch" size={18} color="#E77532" />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.competitionName}>{race.name}</Text>
                        <Text style={styles.competitionMeta}>
                          {(race.route_distance_m / 1000).toFixed(1)} km · {dateLabel(race.starts_at)}
                        </Text>
                      </View>
                    </View>
                    <View style={styles.competitionFooter}>
                      <Text style={styles.participants}>
                        {race.participant_count}
                        {race.participant_capacity ? ` / ${race.participant_capacity}` : ''} joined
                      </Text>
                      <TouchableOpacity
                        style={[styles.smallAction, race.is_joined && styles.joinedAction]}
                        disabled={race.is_joined || working === race.id}
                        onPress={() => joinCompetition('race', race.id)}
                      >
                        <Text style={styles.smallActionText}>
                          {race.is_joined ? 'Entered' : 'Enter race'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                ))}
                {!races.length && <Text style={styles.emptyText}>No scheduled races.</Text>}
              </>
            )}

            {tab === 'activity' && (
              <View style={styles.listSection}>
                <Text style={styles.cardTitle}>Club activity</Text>
                <Text style={styles.timelineNotice}>
                  Automatically generated. Members cannot post, comment, react, or message.
                </Text>
                {events.map((event) => (
                  <View key={event.id} style={styles.eventRow}>
                    <View style={styles.eventDot} />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.eventTitle}>
                        {event.event_type.startsWith('territory_')
                          ? `Territory update${typeof event.payload?.claimed === 'number' ? ` · +${event.payload.claimed} claimed, ${event.payload.defended ?? 0} defended` : ''}`
                          : event.event_type.replaceAll('_', ' ')}
                      </Text>
                      <Text style={styles.eventTime}>
                        {new Date(event.occurred_at).toLocaleString()}
                      </Text>
                    </View>
                  </View>
                ))}
                {!events.length && <Text style={styles.emptyText}>No club events yet.</Text>}
              </View>
            )}

            {tab === 'members' && (
              <View style={styles.listSection}>
                <Text style={styles.cardTitle}>Members</Text>
                {members.map((member) => (
                  <View key={member.id} style={styles.rankRow}>
                    <View style={styles.avatar}>
                      <Text style={styles.avatarText}>
                        {(member.athlete?.name || 'R').slice(0, 1).toUpperCase()}
                      </Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.runnerName}>
                        {member.athlete?.name || 'Runner'}
                      </Text>
                      <Text style={styles.runnerMeta}>{member.role}</Text>
                    </View>
                  </View>
                ))}
              </View>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loading: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 30,
  },
  errorTitle: { color: colors.textPrimary, fontSize: 18, fontWeight: '900' },
  errorBody: { color: colors.textSecondary, textAlign: 'center' },
  backText: { color: colors.brand, fontWeight: '900', marginTop: 10 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.page,
    paddingVertical: 10,
  },
  headerTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 15, maxWidth: '60%' },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: { padding: spacing.page, paddingBottom: 60 },
  hero: { borderRadius: 25, padding: 20, minHeight: 210, justifyContent: 'flex-end' },
  heroTop: {
    position: 'absolute',
    left: 20,
    right: 20,
    top: 18,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  heroEmoji: { fontSize: 34 },
  visibilityBadge: {
    height: 28,
    paddingHorizontal: 9,
    borderRadius: 10,
    backgroundColor: 'rgba(0,0,0,0.2)',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  visibilityText: { color: '#FFFFFF', fontWeight: '900', fontSize: 8, letterSpacing: 0.8 },
  heroName: { color: '#FFFFFF', fontSize: 28, fontWeight: '900' },
  heroMembers: { color: 'rgba(255,255,255,0.82)', fontSize: 12, marginTop: 3 },
  heroDescription: { color: 'rgba(255,255,255,0.9)', fontSize: 12, lineHeight: 17, marginTop: 8 },
  joinCard: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 17,
    marginTop: 12,
  },
  joinTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 15 },
  joinBody: { color: colors.textSecondary, fontSize: 11.5, lineHeight: 17, marginTop: 5 },
  primaryAction: {
    minHeight: 44,
    borderRadius: 14,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 14,
  },
  primaryActionText: { color: '#FFFFFF', fontWeight: '900', fontSize: 13 },
  attributionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderRadius: 18,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 14,
    marginTop: 12,
  },
  attributionIcon: {
    width: 40,
    height: 40,
    borderRadius: 13,
    backgroundColor: '#EAF8F5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  attributionTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 12.5 },
  attributionBody: { color: colors.textSecondary, fontSize: 10.5, lineHeight: 14, marginTop: 2 },
  makePrimary: { color: colors.brand, fontWeight: '900', fontSize: 10.5 },
  tabs: { gap: 7, paddingVertical: 18 },
  tab: {
    borderRadius: 13,
    borderWidth: 1,
    borderColor: colors.separator,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  tabActive: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  tabText: { color: colors.textSecondary, fontWeight: '800', fontSize: 11 },
  tabTextActive: { color: '#FFFFFF' },
  statGrid: { flexDirection: 'row', gap: 10 },
  statCard: {
    flex: 1,
    minHeight: 120,
    borderRadius: 19,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 15,
  },
  statValue: { color: colors.textPrimary, fontSize: 28, fontWeight: '900', marginTop: 13 },
  statLabel: { color: colors.textSecondary, fontSize: 10.5, marginTop: 2 },
  territoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#151923',
    borderRadius: 20,
    padding: 16,
    marginTop: 10,
  },
  territoryIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#283039',
    alignItems: 'center',
    justifyContent: 'center',
  },
  territoryTitle: { color: '#FFFFFF', fontWeight: '900', fontSize: 14 },
  territoryBody: { color: '#AAB1C0', fontSize: 10.5, lineHeight: 15, marginTop: 3 },
  rulesCard: {
    backgroundColor: colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 16,
    marginTop: 10,
  },
  cardTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 15 },
  rulesBody: { color: colors.textSecondary, fontSize: 12, lineHeight: 18, marginTop: 8 },
  listSection: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 15,
  },
  rankRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 11,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.separator,
  },
  myRank: { backgroundColor: '#FFF5EF', marginHorizontal: -8, paddingHorizontal: 8, borderRadius: 12 },
  rankNumber: { width: 20, color: colors.textTertiary, fontWeight: '900', textAlign: 'center' },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: colors.textPrimary, fontWeight: '900' },
  runnerName: { color: colors.textPrimary, fontWeight: '900', fontSize: 12.5 },
  runnerMeta: { color: colors.textSecondary, fontSize: 9.5, marginTop: 2 },
  runnerScore: { color: colors.textPrimary, fontWeight: '900', fontSize: 12 },
  emptyText: { color: colors.textSecondary, textAlign: 'center', paddingVertical: 24, fontSize: 12 },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 9,
  },
  addText: { color: colors.brand, fontWeight: '900', fontSize: 11 },
  competitionCard: {
    backgroundColor: colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 14,
    marginBottom: 9,
  },
  competitionTop: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  challengeIcon: {
    width: 39,
    height: 39,
    borderRadius: 13,
    backgroundColor: '#EEE7FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  raceIcon: {
    width: 39,
    height: 39,
    borderRadius: 13,
    backgroundColor: '#FFF0E6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  competitionName: { color: colors.textPrimary, fontWeight: '900', fontSize: 13 },
  competitionMeta: { color: colors.textSecondary, fontSize: 10.5, marginTop: 3 },
  competitionFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  participants: { color: colors.textTertiary, fontSize: 10.5 },
  smallAction: {
    backgroundColor: colors.textPrimary,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  joinedAction: { backgroundColor: '#DDF8F2' },
  smallActionText: { color: colors.background, fontWeight: '900', fontSize: 9.5 },
  timelineNotice: {
    color: colors.textSecondary,
    fontSize: 10.5,
    lineHeight: 15,
    marginTop: 4,
    marginBottom: 10,
  },
  eventRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.separator,
  },
  eventDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: colors.brand },
  eventTitle: { color: colors.textPrimary, fontWeight: '800', fontSize: 12, textTransform: 'capitalize' },
  eventTime: { color: colors.textTertiary, fontSize: 9.5, marginTop: 2 },
  achievementRow: {
    flexDirection: 'row',
    gap: 9,
    alignItems: 'center',
    paddingTop: 12,
  },
});

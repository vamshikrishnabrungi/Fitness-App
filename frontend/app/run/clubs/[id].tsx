import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../../src/components/GlassCard';
import { api } from '../../../src/utils/api';
import { colors, typography, spacing } from '../../../src/utils/theme';

interface RunFeedItem {
  run_id: string;
  user_name: string;
  distance_meters: number;
  active_duration_seconds: number;
  start_time: string;
}

interface LeaderboardEntry {
  user_id: string;
  username: string;
  total_distance: number;
  total_runs: number;
  rank: number;
}

export default function RunClubDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  
  const [activeTab, setActiveTab] = useState<'feed' | 'leaderboard'>('feed');
  const [feed, setFeed] = useState<RunFeedItem[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClubData();
  }, [id]);

  const fetchClubData = async () => {
    try {
      setLoading(true);
      const [feedData, leaderboardData] = await Promise.all([
        api.get<RunFeedItem[]>(`/terra/clubs/${id}/feed`).catch(() => []),
        api.get<LeaderboardEntry[]>(`/terra/clubs/${id}/members/leaderboard`).catch(() => [])
      ]);
      setFeed(feedData || []);
      setLeaderboard(leaderboardData || []);
    } catch (error) {
      console.error('Failed to load club details:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Club Details</Text>
        <View style={styles.headerRight} />
      </View>

      <View style={styles.tabsRow}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'feed' && styles.tabActive]}
          onPress={() => setActiveTab('feed')}
        >
          <Text style={[styles.tabText, activeTab === 'feed' && styles.tabTextActive]}>Activity Feed</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'leaderboard' && styles.tabActive]}
          onPress={() => setActiveTab('leaderboard')}
        >
          <Text style={[styles.tabText, activeTab === 'leaderboard' && styles.tabTextActive]}>Leaderboard</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 40 }]}>
        {loading ? (
          <ActivityIndicator size="large" color={colors.textPrimary} style={{ marginTop: 60 }} />
        ) : (
          <>
            {activeTab === 'feed' && (
              <View>
                {feed.length > 0 ? (
                  feed.map((run) => (
                    <GlassCard key={run.run_id} style={styles.feedCard}>
                      <View style={styles.feedHeader}>
                        <View style={styles.feedAvatar}>
                          <Text style={styles.avatarText}>{run.user_name?.charAt(0) || 'U'}</Text>
                        </View>
                        <View>
                          <Text style={styles.feedName}>{run.user_name}</Text>
                          <Text style={styles.feedTime}>{run.start_time?.substring(0, 10)}</Text>
                        </View>
                      </View>
                      <View style={styles.feedStats}>
                        <View style={styles.statBox}>
                          <Text style={styles.statValue}>{(run.distance_meters / 1000).toFixed(2)}</Text>
                          <Text style={styles.statLabel}>km</Text>
                        </View>
                        <View style={styles.statBox}>
                          <Text style={styles.statValue}>{Math.floor(run.active_duration_seconds / 60)}</Text>
                          <Text style={styles.statLabel}>min</Text>
                        </View>
                      </View>
                    </GlassCard>
                  ))
                ) : (
                  <Text style={styles.emptyText}>No recent runs from members.</Text>
                )}
              </View>
            )}

            {activeTab === 'leaderboard' && (
              <View>
                <GlassCard style={styles.leaderboardCard}>
                  {leaderboard.map((m) => (
                    <View key={m.user_id} style={styles.memberRow}>
                      <Text style={styles.memberRank}>{m.rank}</Text>
                      <View style={styles.memberInfo}>
                        <Text style={styles.memberName}>{m.username}</Text>
                        <Text style={styles.memberRole}>{m.total_runs} runs this week</Text>
                      </View>
                      <Text style={styles.memberStatus}>{m.total_distance.toFixed(1)} km</Text>
                    </View>
                  ))}
                  {leaderboard.length === 0 && <Text style={styles.emptyText}>No runs logged yet this week.</Text>}
                </GlassCard>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.separator,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  headerRight: {
    width: 40,
  },
  tabsRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: colors.separator,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: colors.textPrimary,
  },
  tabText: {
    ...typography.label,
    color: colors.textSecondary,
  },
  tabTextActive: {
    color: colors.textPrimary,
  },
  scrollContent: {
    padding: spacing.lg,
  },
  feedCard: {
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  feedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  feedAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  avatarText: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  feedName: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  feedTime: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  feedStats: {
    flexDirection: 'row',
    gap: spacing.xl,
    paddingLeft: 48,
  },
  statBox: {
    alignItems: 'baseline',
    flexDirection: 'row',
    gap: 4,
  },
  statValue: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  leaderboardCard: {
    padding: spacing.md,
  },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  memberRank: {
    ...typography.h4,
    color: colors.textSecondary,
    width: 30,
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  memberRole: {
    ...typography.caption,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  memberStatus: {
    ...typography.captionMedium,
    color: colors.textPrimary,
    textTransform: 'capitalize',
  },
  emptyText: {
    ...typography.body,
    color: colors.textTertiary,
    textAlign: 'center',
    marginTop: spacing.xl,
  },
});

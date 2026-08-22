import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api, ApiError } from '../../../src/utils/api';
import { colors, spacing } from '../../../src/utils/theme';

interface Club {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  emoji: string;
  primary_color: string;
  visibility: 'public' | 'private';
  member_count: number;
  membership_role?: 'owner' | 'admin' | 'member' | null;
  membership_status?: string | null;
  is_primary: boolean;
}

interface ClubPage {
  items: Club[];
  next_cursor?: string | null;
}

const idempotencyKey = (scope: string) =>
  `${scope}-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;

export default function ClubsScreen() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [clubs, setClubs] = useState<Club[]>([]);
  const [mine, setMine] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [joining, setJoining] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [discovery, memberships] = await Promise.all([
        api.get<ClubPage>(
          `/clubs?limit=50${query.trim() ? `&q=${encodeURIComponent(query.trim())}` : ''}`,
        ),
        api.get<ClubPage>('/clubs/mine?limit=100'),
      ]);
      setClubs(discovery.items);
      setMine(memberships.items);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Clubs could not be loaded.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [query]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const primary = useMemo(() => mine.find((club) => club.is_primary), [mine]);

  const join = async (club: Club) => {
    setJoining(club.id);
    try {
      await api.post(
        `/clubs/${club.id}/join`,
        undefined,
        { 'Idempotency-Key': idempotencyKey(`join-${club.id}`) },
      );
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not join this club.');
    } finally {
      setJoining(null);
    }
  };

  const renderClub = (club: Club) => {
    const active = club.membership_status === 'active';
    const pending = club.membership_status === 'requested';
    return (
      <TouchableOpacity
        key={club.id}
        style={styles.clubCard}
        activeOpacity={0.82}
        onPress={() => router.push(`/run/clubs/${club.id}` as any)}
      >
        <View style={[styles.clubMark, { backgroundColor: `${club.primary_color || '#FF4F2E'}20` }]}>
          <Text style={styles.clubEmoji}>{club.emoji || '🏃'}</Text>
        </View>
        <View style={styles.clubBody}>
          <View style={styles.nameRow}>
            <Text style={styles.clubName} numberOfLines={1}>
              {club.name}
            </Text>
            {club.is_primary && (
              <View style={styles.primaryBadge}>
                <Text style={styles.primaryBadgeText}>PRIMARY</Text>
              </View>
            )}
          </View>
          <Text style={styles.clubMeta}>
            {club.member_count} member{club.member_count === 1 ? '' : 's'} ·{' '}
            {club.visibility === 'private' ? 'Approval required' : 'Open club'}
          </Text>
          {!!club.description && (
            <Text style={styles.clubDescription} numberOfLines={2}>
              {club.description}
            </Text>
          )}
        </View>
        {active ? (
          <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
        ) : pending ? (
          <View style={styles.pendingBadge}>
            <Text style={styles.pendingText}>Pending</Text>
          </View>
        ) : (
          <TouchableOpacity
            style={styles.joinButton}
            disabled={joining === club.id}
            onPress={(event) => {
              event.stopPropagation();
              join(club);
            }}
          >
            {joining === club.id ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.joinText}>Join</Text>
            )}
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Run clubs</Text>
          <Text style={styles.subtitle}>One primary club receives each verified run</Text>
        </View>
        <TouchableOpacity style={styles.createButton} onPress={() => router.push('/run/clubs/create')}>
          <Ionicons name="add" size={18} color="#FFFFFF" />
          <Text style={styles.createText}>Create</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.search}>
        <Ionicons name="search" size={18} color={colors.textTertiary} />
        <TextInput
          accessibilityLabel="Search run clubs"
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={load}
          placeholder="Search clubs"
          placeholderTextColor={colors.textTertiary}
          style={styles.searchInput}
          returnKeyType="search"
        />
        {!!query && (
          <TouchableOpacity onPress={() => setQuery('')}>
            <Ionicons name="close-circle" size={18} color={colors.textTertiary} />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              load();
            }}
          />
        }
      >
        {primary && (
          <TouchableOpacity
            style={styles.primaryCard}
            onPress={() => router.push(`/run/clubs/${primary.id}` as any)}
          >
            <View style={styles.primaryTop}>
              <Text style={styles.primaryEyebrow}>PRIMARY COMPETITIVE CLUB</Text>
              <Ionicons name="shield-checkmark" size={18} color="#62E6D1" />
            </View>
            <Text style={styles.primaryName}>
              {primary.emoji} {primary.name}
            </Text>
            <Text style={styles.primaryCopy}>
              Future verified runs are attributed here. Changing clubs starts a seven-day cooldown.
            </Text>
          </TouchableOpacity>
        )}

        {!!mine.length && (
          <>
            <Text style={styles.sectionTitle}>Your clubs</Text>
            {mine.map(renderClub)}
          </>
        )}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Discover</Text>
          <Text style={styles.resultCount}>{clubs.length} results</Text>
        </View>

        {loading ? (
          <ActivityIndicator style={{ marginTop: 60 }} color={colors.brand} />
        ) : error ? (
          <View style={styles.empty}>
            <Ionicons name="cloud-offline-outline" size={34} color={colors.textTertiary} />
            <Text style={styles.emptyTitle}>Clubs unavailable</Text>
            <Text style={styles.emptyBody}>{error}</Text>
            <TouchableOpacity style={styles.retry} onPress={load}>
              <Text style={styles.retryText}>Try again</Text>
            </TouchableOpacity>
          </View>
        ) : clubs.length ? (
          clubs.map(renderClub)
        ) : (
          <View style={styles.empty}>
            <Ionicons name="people-outline" size={34} color={colors.textTertiary} />
            <Text style={styles.emptyTitle}>No clubs found</Text>
            <Text style={styles.emptyBody}>Try a different name or create the first club here.</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: spacing.page,
    paddingVertical: 12,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { color: colors.textPrimary, fontSize: 22, fontWeight: '900' },
  subtitle: { color: colors.textSecondary, fontSize: 11.5, marginTop: 2 },
  createButton: {
    backgroundColor: colors.textPrimary,
    borderRadius: 15,
    paddingHorizontal: 13,
    height: 40,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  createText: { color: '#FFFFFF', fontWeight: '900', fontSize: 12 },
  search: {
    marginHorizontal: spacing.page,
    backgroundColor: colors.surface,
    borderRadius: 16,
    height: 48,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    borderWidth: 1,
    borderColor: colors.separator,
  },
  searchInput: { flex: 1, color: colors.textPrimary, fontSize: 14, height: '100%' },
  content: { padding: spacing.page, paddingBottom: 60 },
  primaryCard: {
    backgroundColor: '#151923',
    borderRadius: 22,
    padding: 18,
    marginBottom: 24,
  },
  primaryTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  primaryEyebrow: { color: '#62E6D1', fontSize: 9.5, fontWeight: '900', letterSpacing: 1.3 },
  primaryName: { color: '#FFFFFF', fontSize: 23, fontWeight: '900', marginTop: 12 },
  primaryCopy: { color: '#A5ADBD', fontSize: 12, lineHeight: 17, marginTop: 5 },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 14,
  },
  sectionTitle: { color: colors.textPrimary, fontSize: 16, fontWeight: '900', marginBottom: 10 },
  resultCount: { color: colors.textTertiary, fontSize: 11, marginBottom: 10 },
  clubCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 13,
    marginBottom: 9,
    gap: 11,
  },
  clubMark: {
    width: 48,
    height: 48,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clubEmoji: { fontSize: 23 },
  clubBody: { flex: 1 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  clubName: { color: colors.textPrimary, fontWeight: '900', fontSize: 14, flexShrink: 1 },
  primaryBadge: {
    backgroundColor: '#DDF8F2',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 6,
  },
  primaryBadgeText: { color: '#178571', fontWeight: '900', fontSize: 7.5, letterSpacing: 0.6 },
  clubMeta: { color: colors.textSecondary, fontSize: 11, marginTop: 3 },
  clubDescription: { color: colors.textTertiary, fontSize: 10.5, lineHeight: 14, marginTop: 4 },
  joinButton: {
    minWidth: 55,
    height: 34,
    borderRadius: 11,
    backgroundColor: colors.brand,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },
  joinText: { color: '#FFFFFF', fontSize: 11, fontWeight: '900' },
  pendingBadge: { backgroundColor: '#FFF1D6', borderRadius: 9, padding: 8 },
  pendingText: { color: '#9A6500', fontWeight: '800', fontSize: 9.5 },
  empty: { alignItems: 'center', paddingVertical: 52, gap: 7 },
  emptyTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 16 },
  emptyBody: { color: colors.textSecondary, fontSize: 12, textAlign: 'center', maxWidth: 270 },
  retry: { marginTop: 5, paddingHorizontal: 16, paddingVertical: 10 },
  retryText: { color: colors.brand, fontWeight: '900' },
});

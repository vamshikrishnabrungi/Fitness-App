import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';
import { api } from '../../src/utils/api';
import { useAuthStore } from '../../src/store/authStore';
import { ExerciseThumbnail } from '../../src/components/ExerciseThumbnail';

// Workout type
interface Workout {
  id: string;
  title: string;
  category: string;
  duration: number;
  difficulty: string;
  exercises: any[];
  completed?: boolean;
  scheduled_date?: string;
  ai_generated?: boolean;
  description?: string;
  equipment?: string[];
  source?: string;
  week_number?: number;
  session_number?: number;
  intensity?: string;
  adaptation?: {
    goal?: string;
    sports?: string[];
    targets?: string[];
    sport_transfer?: string[];
    why_this_session?: string;
    week_theme?: string;
    progression_rule?: string;
  };
  session_plan?: {
    why_this_session?: string;
    adaptation_targets?: string[];
    sport_transfer?: string[];
    warmup?: { name?: string }[];
    main_work?: { name?: string }[];
    cooldown?: { name?: string }[];
  };
}

const todayKey = new Date().toISOString().slice(0, 10);

const formatDateLabel = (date?: string) => {
  if (!date) return 'Plan';
  const parsed = new Date(`${date}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
};

const humanizeLabel = (value?: string | null) => {
  if (!value) return '';
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const getWorkoutPurpose = (workout: Workout) => {
  return (
    workout.adaptation?.why_this_session ||
    workout.session_plan?.why_this_session ||
    workout.description ||
    'AI-built session from your current program.'
  );
};

const getWorkoutTargets = (workout: Workout) => {
  const targets = workout.adaptation?.targets || workout.session_plan?.adaptation_targets || [];
  const transfer = workout.adaptation?.sport_transfer || workout.session_plan?.sport_transfer || [];
  return [...targets, ...transfer].filter(Boolean).map((item) => humanizeLabel(item)).slice(0, 3);
};

const getPrimaryExerciseName = (workout: Workout) => {
  const plan = workout.session_plan;
  return (
    plan?.main_work?.find((exercise) => exercise.name)?.name ||
    plan?.warmup?.find((exercise) => exercise.name)?.name ||
    plan?.cooldown?.find((exercise) => exercise.name)?.name ||
    workout.exercises?.find((exercise) => exercise?.name)?.name ||
    workout.title
  );
};

const sortBySchedule = (items: Workout[]) => {
  return [...items].sort((a, b) => {
    const dateA = a.scheduled_date || '';
    const dateB = b.scheduled_date || '';
    if (dateA !== dateB) return dateA.localeCompare(dateB);
    return (a.session_number || 0) - (b.session_number || 0);
  });
};

export default function TrainScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuthStore();
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [query, setQuery] = useState('');
  const [generationPaused, setGenerationPaused] = useState(false);
  const initials = useMemo(() => {
    const source = user?.name?.trim() || user?.email?.split('@')[0] || 'Athlete';
    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return source.slice(0, 2).toUpperCase();
  }, [user?.email, user?.name]);

  useEffect(() => {
    fetchWorkouts();
  }, []);

  const fetchWorkouts = async () => {
    try {
      setLoading(true);
      const [res, status] = await Promise.all([
        api.get<Workout[]>('/workouts'),
        api.get<{ paused: boolean }>('/workouts/generation-status').catch(() => ({ paused: false })),
      ]);
      setWorkouts(res || []);
      setGenerationPaused(!!status?.paused);
    } catch (error) {
      console.error('Error fetching workouts:', error);
      setWorkouts([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchWorkouts();
    setRefreshing(false);
  };

  const filteredWorkouts = useMemo(() => {
    const term = query.trim().toLowerCase();
    const sorted = sortBySchedule(workouts);
    if (!term) return sorted;
    return sorted.filter((w) =>
      [
        w.title,
        w.category,
        w.difficulty,
        w.description,
        w.adaptation?.goal,
        ...(w.adaptation?.sports || []),
        ...(w.adaptation?.targets || []),
        ...(w.adaptation?.sport_transfer || []),
      ]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(term))
    );
  }, [query, workouts]);

  const todayWorkout = useMemo(() => {
    return filteredWorkouts.find((workout) => workout.scheduled_date === todayKey) || filteredWorkouts[0];
  }, [filteredWorkouts]);

  const weekWorkouts = useMemo(() => {
    return filteredWorkouts.filter((workout) => workout.id !== todayWorkout?.id);
  }, [filteredWorkouts, todayWorkout?.id]);

  const programMeta = useMemo(() => {
    const first = workouts[0];
    const sports = first?.adaptation?.sports || [];
    const goal = first?.adaptation?.goal;
    const weekTheme = first?.adaptation?.week_theme;
    return {
      title: sports.length ? `${sports.slice(0, 2).map((sport) => humanizeLabel(sport)).join(' + ')} Plan` : 'AI Training Plan',
      detail: [
        first?.week_number ? `Week ${first.week_number}` : 'Week 1',
        `${workouts.length} sessions`,
        humanizeLabel(goal),
      ].filter(Boolean).join(' · '),
      theme: weekTheme || 'Built from your onboarding profile.',
    };
  }, [workouts]);

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color={colors.textPrimary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>{initials}</Text>
            </View>
            <Text style={styles.headerTitle}>Workouts</Text>
          </View>
          <TouchableOpacity style={styles.headerButton}>
            <Ionicons name="bookmark-outline" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
        </View>

        {/* Search */}
        <View style={styles.searchContainer}>
          <Ionicons name="search-outline" size={18} color="#9CA3AF" />
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search"
            placeholderTextColor="#9CA3AF"
            style={styles.searchInput}
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        {generationPaused && (
          <View style={styles.pausedBanner}>
            <Ionicons name="pause-circle" size={22} color={colors.brand} />
            <View style={{ flex: 1 }}>
              <Text style={styles.pausedTitle}>Workout creation is paused</Text>
              <Text style={styles.pausedSub}>AI plan generation is turned off for now. Your existing workouts still show here.</Text>
            </View>
          </View>
        )}

        {filteredWorkouts.length > 0 && (
          <View style={styles.planHeader}>
            <Text style={styles.planEyebrow}>Your Plan</Text>
            <Text style={styles.planTitle}>{programMeta.title}</Text>
            <Text style={styles.planMeta}>{programMeta.detail}</Text>
            <Text style={styles.planTheme} numberOfLines={2}>{programMeta.theme}</Text>
          </View>
        )}

        {filteredWorkouts.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No workouts yet</Text>
            <Text style={styles.emptySubtitle}>{generationPaused ? 'Workout creation is paused right now.' : 'Generate a plan to see workouts here.'}</Text>
          </View>
        ) : (
          <>
            {todayWorkout && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>{todayWorkout.scheduled_date === todayKey ? 'Today' : 'Next Session'}</Text>
                <FeaturedWorkoutCard
                  workout={todayWorkout}
                  onPress={() => router.push(`/workout/${todayWorkout.id}`)}
                />
              </View>
            )}

            {weekWorkouts.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>This Week</Text>
                {weekWorkouts.map((workout) => (
                <WorkoutRow
                  key={workout.id}
                  workout={workout}
                  onPress={() => router.push(`/workout/${workout.id}`)}
                />
                ))}
              </View>
            )}
          </>
        )}

        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

function WorkoutRow({
  workout,
  onPress,
}: {
  workout: Workout;
  onPress: () => void;
}) {
  const showNew = !workout.completed;
  const purpose = getWorkoutPurpose(workout);
  const targets = getWorkoutTargets(workout);

  return (
    <TouchableOpacity
      style={styles.workoutRow}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.thumb}>
        <ExerciseThumbnail name={getPrimaryExerciseName(workout)} size={64} />
        {showNew && (
          <View style={styles.newPill}>
            <Text style={styles.newPillText}>New</Text>
          </View>
        )}
      </View>
      <View style={styles.rowContent}>
        <Text style={styles.rowTitle} numberOfLines={2}>{workout.title}</Text>
        <Text style={styles.rowMeta} numberOfLines={1}>
          {formatDateLabel(workout.scheduled_date)} · {humanizeLabel(workout.category)} · {workout.duration} min
        </Text>
        <Text style={styles.rowPurpose} numberOfLines={2}>{purpose}</Text>
        {targets.length > 0 && (
          <View style={styles.chipRow}>
            {targets.map((target) => (
              <View key={`${workout.id}-${target}`} style={styles.targetChip}>
                <Text style={styles.targetChipText} numberOfLines={1}>{target}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
      <TouchableOpacity style={styles.bookmarkButton} onPress={onPress}>
        <Ionicons name="bookmark-outline" size={18} color="#9CA3AF" />
      </TouchableOpacity>
    </TouchableOpacity>
  );
}

function FeaturedWorkoutCard({
  workout,
  onPress,
}: {
  workout: Workout;
  onPress: () => void;
}) {
  const purpose = getWorkoutPurpose(workout);
  const targets = getWorkoutTargets(workout);

  return (
    <TouchableOpacity style={styles.featuredCard} onPress={onPress} activeOpacity={0.75}>
      <View style={styles.featuredTop}>
        <ExerciseThumbnail name={getPrimaryExerciseName(workout)} size={52} style={styles.featuredIcon} />
        <View style={styles.featuredMeta}>
          <Text style={styles.featuredDate}>{formatDateLabel(workout.scheduled_date)}</Text>
          <Text style={styles.featuredInfo}>{humanizeLabel(workout.category)} · {workout.duration} min · {humanizeLabel(workout.intensity || workout.difficulty)}</Text>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#A1A1AA" />
      </View>
      <Text style={styles.featuredTitle} numberOfLines={2}>{workout.title}</Text>
      <Text style={styles.featuredPurpose} numberOfLines={3}>{purpose}</Text>
      {targets.length > 0 && (
        <View style={styles.chipRow}>
          {targets.map((target) => (
            <View key={`${workout.id}-featured-${target}`} style={styles.targetChip}>
              <Text style={styles.targetChipText} numberOfLines={1}>{target}</Text>
            </View>
          ))}
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.lg,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#E5E7EB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  headerButton: {
    padding: spacing.xs,
  },
  content: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: spacing.xl,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: colors.textPrimary,
  },
  planHeader: {
    backgroundColor: '#F7F6F2',
    borderRadius: 24,
    padding: 18,
    marginBottom: 28,
  },
  planEyebrow: {
    fontSize: 11,
    fontWeight: '800',
    color: '#8A8178',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  planTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  planMeta: {
    fontSize: 13,
    fontWeight: '600',
    color: '#59544D',
    marginBottom: 8,
  },
  planTheme: {
    fontSize: 14,
    color: '#7A746D',
    lineHeight: 20,
  },
  // Sections
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 14,
  },
  workoutRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 18,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.05)',
  },
  thumb: {
    width: 64,
    height: 64,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    overflow: 'hidden',
  },
  newPill: {
    position: 'absolute',
    left: 8,
    bottom: 8,
    backgroundColor: 'rgba(255,255,255,0.82)',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  newPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  rowContent: {
    flex: 1,
  },
  rowTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 5,
  },
  rowMeta: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 6,
  },
  rowPurpose: {
    fontSize: 13,
    color: '#6F6A63',
    lineHeight: 18,
    marginBottom: 9,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  targetChip: {
    backgroundColor: '#F2F1EE',
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 5,
    maxWidth: 180,
  },
  targetChipText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#625D56',
  },
  bookmarkButton: {
    padding: 6,
  },
  featuredCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#ECEAE5',
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
  },
  featuredTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  featuredIcon: {
    marginRight: 12,
  },
  featuredMeta: {
    flex: 1,
  },
  featuredDate: {
    fontSize: 12,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: 3,
  },
  featuredInfo: {
    fontSize: 12,
    color: '#7A746D',
  },
  featuredTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  featuredPurpose: {
    fontSize: 14,
    color: '#625D56',
    lineHeight: 20,
    marginBottom: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#6B7280',
  },
  pausedBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.brandSoft,
    borderRadius: 16,
    padding: spacing.lg,
    marginHorizontal: spacing.page,
    marginBottom: spacing.lg,
  },
  pausedTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: -0.2,
  },
  pausedSub: {
    fontSize: 12.5,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 18,
  },
});

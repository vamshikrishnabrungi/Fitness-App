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
}

const SECTION_COPY: Record<string, { title: string; description: string }> = {
  Strength: {
    title: 'Lock in and Lift',
    description: 'These sessions focus on heavy lifts with minimal reps for intentional strength building.',
  },
  Cardio: {
    title: 'Engine Room',
    description: 'Build stamina and conditioning with focused cardio sessions.',
  },
  Recovery: {
    title: 'Recover and Reset',
    description: 'Lower intensity work to restore, mobilize, and keep you moving.',
  },
  Flexibility: {
    title: 'Move Better',
    description: 'Mobility and flexibility sessions to improve range and control.',
  },
  Sport: {
    title: 'Sport Focus',
    description: 'Sport-specific sessions to sharpen skills and athleticism.',
  },
  Workouts: {
    title: 'Workouts',
    description: 'Curated sessions based on your plan.',
  },
};

// Category config
const CATEGORY_CONFIG: Record<string, { color: string; icon: string }> = {
  Strength: { color: '#F97316', icon: 'barbell' },
  Cardio: { color: '#EF4444', icon: 'heart' },
  Recovery: { color: '#16A34A', icon: 'leaf' },
  Flexibility: { color: '#8B5CF6', icon: 'body' },
  Sport: { color: '#3B82F6', icon: 'football' },
};

export default function TrainScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [query, setQuery] = useState('');

  useEffect(() => {
    fetchWorkouts();
  }, []);

  const fetchWorkouts = async () => {
    try {
      setLoading(true);
      const res = await api.get<Workout[]>('/workouts');
      setWorkouts(res || []);
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
    if (!term) return workouts;
    return workouts.filter((w) =>
      [w.title, w.category, w.difficulty, w.description]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(term))
    );
  }, [query, workouts]);

  const groupedWorkouts = useMemo(() => {
    return filteredWorkouts.reduce((acc, workout) => {
      const key = workout.category || 'Workouts';
      if (!acc[key]) acc[key] = [];
      acc[key].push(workout);
      return acc;
    }, {} as Record<string, Workout[]>);
  }, [filteredWorkouts]);

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
              <Text style={styles.avatarText}>VK</Text>
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

        {/* Sections */}
        {Object.keys(groupedWorkouts).length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No workouts yet</Text>
            <Text style={styles.emptySubtitle}>Generate a plan to see workouts here.</Text>
          </View>
        ) : (
          Object.entries(groupedWorkouts).map(([category, list]) => (
            <View key={category} style={styles.section}>
              <Text style={styles.sectionTitle}>{SECTION_COPY[category]?.title || category}</Text>
              <Text style={styles.sectionDescription}>
                {SECTION_COPY[category]?.description || 'Recommended sessions for you.'}
              </Text>
              {list.map((workout) => (
                <WorkoutRow
                  key={workout.id}
                  workout={workout}
                  onPress={() => router.push(`/workout/${workout.id}`)}
                />
              ))}
            </View>
          ))
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
  const category = CATEGORY_CONFIG[workout.category] || CATEGORY_CONFIG.Strength;
  const equipmentLabel = workout.equipment?.length ? workout.equipment.join(', ') : 'Bodyweight';
  const showNew = !workout.completed;

  return (
    <TouchableOpacity
      style={styles.workoutRow}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.thumb, { backgroundColor: category.color + '22' }]}>
        <Ionicons name={category.icon as any} size={22} color={category.color} />
        {showNew && (
          <View style={styles.newPill}>
            <Text style={styles.newPillText}>New</Text>
          </View>
        )}
      </View>
      <View style={styles.rowContent}>
        <Text style={styles.rowTitle} numberOfLines={2}>{workout.title}</Text>
        <Text style={styles.rowMeta} numberOfLines={1}>
          {workout.difficulty} · {workout.category} · {equipmentLabel}
        </Text>
        <Text style={styles.rowDuration}>{workout.duration} min</Text>
      </View>
      <TouchableOpacity style={styles.bookmarkButton} onPress={onPress}>
        <Ionicons name="bookmark-outline" size={18} color="#9CA3AF" />
      </TouchableOpacity>
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
  // Sections
  section: {
    marginBottom: spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 6,
  },
  sectionDescription: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: spacing.lg,
    lineHeight: 19,
  },
  workoutRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.05)',
  },
  thumb: {
    width: 78,
    height: 78,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    overflow: 'hidden',
  },
  newPill: {
    position: 'absolute',
    left: 8,
    bottom: 8,
    backgroundColor: '#FEE2E2',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  newPillText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#DC2626',
  },
  rowContent: {
    flex: 1,
  },
  rowTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  rowMeta: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  rowDuration: {
    fontSize: 12,
    color: '#6B7280',
  },
  bookmarkButton: {
    padding: 6,
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
});

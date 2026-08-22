/* eslint-disable react/no-unescaped-entities */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useFocusEffect } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { GlassCard } from '../../src/components/GlassCard';
import { Badge } from '../../src/components/Badge';
import { CircularProgress } from '../../src/components/CircularProgress';
import { StrainCard } from '../../src/components/StrainCard';
import { useAuthStore } from '../../src/store/authStore';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

interface Workout {
  id: string;
  title: string;
  category: string;
  duration: number;
  difficulty: string;
  equipment: string[];
  exercises: any[];
}

interface TrainingLoadData {
  today: {
    load_au: number;
    intensity: string;
    recovery_status: string;
    notes: string;
  };
  yesterday_au: number;
}

interface NutritionData {
  calories_kcal: number;
  protein_g: number;
  carbohydrate_g: number;
  fat_g: number;
  fibre_g: number;
  meals: { id: string; name: string; meal_type: string; eaten_at: string; calories_kcal: number; analysis_id?: string | null }[];
}

interface StrainData {
  today: number | null;
  status: 'low' | 'moderate' | 'high';
  weeklyAvg: number | null;
  history?: { day: string; value: number }[];
}

interface Lesson {
  id: string;
  sport: string;
  title: string;
  category: string;
  description?: string | null;
  difficulty?: string | null;
  duration?: number | null;
}

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuthStore();

  const [refreshing, setRefreshing] = useState(false);
  const [workout, setWorkout] = useState<Workout | null>(null);
  const [, setTrainingLoad] = useState<TrainingLoadData | null>(null);
  const [nutrition, setNutrition] = useState<NutritionData | null>(null);
  const [runStats, setRunStats] = useState<any>(null);
  const [goals, setGoals] = useState<any[]>([]);
  const [strain, setStrain] = useState<StrainData | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);

  const fetchData = async () => {
    try {
      const [workoutRes, loadRes, nutritionRes, statsRes, goalsRes, strainRes, lessonsRes] = await Promise.all([
        api.get<Workout>('/training/sessions/today').catch(() => null),
        api.get<TrainingLoadData>('/training-load').catch(() => null),
        api.get<NutritionData>('/nutrition/daily-summary').catch(() => null),
        api.get<any>('/activities/stats').catch(() => null),
        api.get<any[]>('/goals').catch(() => []),
        Promise.resolve(null as StrainData | null),
        Promise.resolve([] as Lesson[]),
      ]);

      if (workoutRes) setWorkout(workoutRes);
      if (loadRes) setTrainingLoad(loadRes);
      if (nutritionRes) setNutrition(nutritionRes);
      if (statsRes) setRunStats(statsRes);
      if (goalsRes) setGoals(goalsRes);
      setStrain(strainRes);
      setLessons(lessonsRes || []);
    } catch (error) {
      console.error('Error fetching home data:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Auto-refresh when screen gains focus (e.g., returning from Nutrition screen)
  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  // Calculate macro percentages - use real data only, no hardcoded fallbacks
  const proteinPercent = 0;
  const carbsPercent = 0;
  const fatPercent = 0;
  const fibrePercent = 0;
  const hasRunStats = Boolean(
    runStats &&
    (
      Number(runStats.distance_km) > 0 || Number(runStats.activities) > 0
    )
  );

  const goalsToDisplay = goals.slice(0, 4);

  const goalConfig: Record<string, { icon: string; bg: string; color: string; label: string }> = {
    weight: { icon: 'bar-chart-outline', bg: colors.goalWeight, color: colors.accentOrange, label: 'Weight' },
    workout: { icon: 'flame-outline', bg: colors.goalWorkout, color: colors.statusWarning, label: 'Workout' },
    water: { icon: 'water-outline', bg: colors.goalWater, color: colors.accentTeal, label: 'Water' },
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerText}>
            <Text style={styles.greeting}>Hello,</Text>
            <Text style={styles.userName}>{user?.name?.split(' ')[0] || 'Athlete'}</Text>
            <Text style={styles.subtitle}>Your personalized daily plan</Text>
          </View>
          <TouchableOpacity
            style={styles.profileButton}
            onPress={() => router.push('/(tabs)/profile')}
          >
            <View style={styles.avatarCircle}>
              <Ionicons name="person" size={20} color={colors.textTertiary} />
            </View>
          </TouchableOpacity>
        </View>

        {/* ═══════════ 1. TODAY'S WORKOUT ═══════════ */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today's Workout</Text>
          {workout ? (
            <TouchableOpacity activeOpacity={0.9} onPress={() => router.push(`/workout/${workout.id}`)}>
              <GlassCard variant="hero" style={styles.heroCard}>
                <LinearGradient
                  colors={['rgba(240,240,245,0.8)', 'rgba(230,230,235,0.6)']}
                  style={styles.heroGradient}
                >
                  <Badge
                    label={workout.category}
                    variant="filled"
                    size="sm"
                    icon={<Ionicons name="barbell" size={12} color={colors.badgeFilledText} />}
                  />
                  <Text style={styles.heroTitle}>
                    {workout.title}
                  </Text>
                  <Text style={styles.heroMeta}>
                    {workout.duration} min • {workout.difficulty} • {workout.equipment?.join(', ') || 'Bodyweight'}
                  </Text>
                </LinearGradient>
              </GlassCard>
            </TouchableOpacity>
          ) : (
            <GlassCard variant="hero" style={styles.heroCard}>
              <LinearGradient
                colors={['rgba(240,240,245,0.8)', 'rgba(230,230,235,0.6)']}
                style={styles.heroGradient}
              >
                <Text style={styles.heroTitle}>No workout scheduled</Text>
                <Text style={styles.heroMeta}>Check back later or generate a plan.</Text>
              </LinearGradient>
            </GlassCard>
          )}
        </View>

        {/* ═══════════ 2. STRAIN ═══════════ */}
        <View style={styles.section}>
          <StrainCard
            data={strain}
          />
        </View>

        {/* ═══════════ 5. ACTIVITY ═══════════ */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Activity</Text>
          <GlassCard>
            <TouchableOpacity
              style={styles.activityRow}
              onPress={() => router.push('/(tabs)/run')}
            >
              {hasRunStats ? (
                <>
                  <View style={styles.activityHeader}>
                    <View style={styles.activityTitle}>
                      <Ionicons name="walk-outline" size={20} color={colors.textPrimary} />
                      <Text style={styles.activityName}>Run</Text>
                    </View>
                    <Badge label={`${runStats.activities} activities`} variant="outline" size="sm" />
                  </View>
                  <View style={styles.statsRow}>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>{Number(runStats?.distance_km || 0).toFixed(1)}</Text>
                      <Text style={styles.statLabel}>km</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>{Math.round(Number(runStats?.moving_minutes || 0))}</Text>
                      <Text style={styles.statLabel}>Minutes</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>{runStats?.activities ?? 0}</Text>
                      <Text style={styles.statLabel}>Runs</Text>
                    </View>
                  </View>
                </>
              ) : (
                <View style={styles.emptyActivity}>
                  <View style={styles.emptyActivityIcon}>
                    <Ionicons name="walk-outline" size={20} color={colors.textTertiary} />
                  </View>
                  <View style={styles.emptyActivityContent}>
                    <Text style={styles.activityName}>No activities recorded</Text>
                    <Text style={styles.activityNote}>Start a run or complete a workout to see activity here.</Text>
                  </View>
                </View>
              )}
              <Ionicons
                name="chevron-forward"
                size={20}
                color={colors.textTertiary}
                style={styles.chevron}
              />
            </TouchableOpacity>
          </GlassCard>
        </View>

        {/* ═══════════ 6. GOALS & TRACKERS ═══════════ */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Goals & Trackers</Text>
          <GlassCard style={styles.goalsCard}>
            {goalsToDisplay.map((goal, index) => {
              const config = goalConfig[goal.goal_type] || goalConfig.weight;
              return (
                <View
                  key={goal.id || index}
                  style={[
                    styles.goalRow,
                    index < goalsToDisplay.length - 1 && styles.goalSeparator,
                  ]}
                >
                  <View style={[styles.goalIcon, { backgroundColor: config.bg }]}>
                    <Ionicons
                      name={config.icon as any}
                      size={18}
                      color={config.color}
                    />
                  </View>
                  <View style={styles.goalContent}>
                    <Text style={styles.goalTitle}>
                      {goal.name || config.label}
                    </Text>
                    <Text style={styles.goalValue}>
                      {`Target: ${goal.target}${goal.unit ? ` ${goal.unit}` : ''}`}
                    </Text>
                  </View>
                  <Ionicons name="add-circle-outline" size={24} color={colors.textTertiary} />
                </View>
              );
            })}
            {!goalsToDisplay.length && (
              <Text style={styles.activityNote}>No goals configured yet.</Text>
            )}
          </GlassCard>
        </View>

        {/* ═══════════ 8. NUTRITION ═══════════ */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Nutrition</Text>
            <TouchableOpacity onPress={() => router.push('/nutrition')}>
              <Text style={styles.openLink}>View All</Text>
            </TouchableOpacity>
          </View>
          <GlassCard>
            {/* Track Food Header */}
            <View style={styles.trackFoodHeader}>
              <View style={styles.trackFoodIcon}>
                <Ionicons name="restaurant-outline" size={20} color={colors.accentOrange} />
              </View>
              <View style={styles.trackFoodContent}>
                <Text style={styles.trackFoodTitle}>Track Food</Text>
                <Text style={styles.trackFoodSubtitle}>{nutrition ? `${Math.round(nutrition.calories_kcal)} kcal logged today` : 'No meals logged today'}</Text>
              </View>
              <TouchableOpacity
                style={styles.cameraButton}
                onPress={() => router.push('/nutrition?action=scan')}
              >
                <Ionicons name="camera-outline" size={20} color={colors.textSecondary} />
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => router.push('/nutrition')}
              >
                <Ionicons name="add-circle-outline" size={24} color={colors.accentGreen} />
              </TouchableOpacity>
            </View>

            {/* Macro Rings Grid */}
            <View style={styles.macroRingsGrid}>
              <CircularProgress
                progress={proteinPercent}
                size={70}
                strokeWidth={6}
                color={colors.accentOrange}
                showPercentage
                label="Protein"
              />
              <CircularProgress
                progress={fatPercent}
                size={70}
                strokeWidth={6}
                color={colors.accentOrange}
                showPercentage
                label="Fats"
              />
              <CircularProgress
                progress={carbsPercent}
                size={70}
                strokeWidth={6}
                color={colors.accentOrange}
                showPercentage
                label="Carbs"
              />
              <CircularProgress
                progress={fibrePercent}
                size={70}
                strokeWidth={6}
                color={colors.accentOrange}
                showPercentage
                label="Fibre"
              />
            </View>

            {/* Calorie Balance */}
            <View style={styles.calorieBalance}>
              <Text style={styles.calorieLabel}>Calorie Balance</Text>
              <Text style={styles.calorieValue}>
                {Math.round(nutrition?.calories_kcal || 0)} kcal logged
              </Text>
            </View>

            {/* Low Protein Alert - only show if we have nutrition data */}
          </GlassCard>
        </View>

        {/* ═══════════ 9. TODAY'S NUTRITION LOGS ═══════════ */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today's Nutrition Logs</Text>
          {(nutrition?.meals || []).slice(0, 2).map((meal: any, index: number) => (
            <GlassCard key={index} style={styles.mealLogCard}>
              <View style={styles.mealLogRow}>
                <Text style={styles.mealLogTime}>
                  {new Date(meal.eaten_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Text>
                <View style={styles.mealLogContent}>
                  <View style={styles.mealLogHeader}>
                    <Ionicons name="restaurant-outline" size={16} color={colors.accentOrange} />
                    <Text style={styles.mealLogType}>
                      {meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1)}
                    </Text>
                    {meal.analysis_id && <Badge label="AI estimate confirmed" variant="outline" size="sm" />}
                  </View>
                  <Text style={styles.mealLogCalories}>
                    <Text style={styles.mealLogCaloriesValue}>{Math.round(meal.calories_kcal)}</Text> kcal
                  </Text>
                  <Text style={styles.mealLogFoods}>
                    {meal.name}
                  </Text>
                </View>
              </View>
            </GlassCard>
          ))}
          {(nutrition?.meals?.length || 0) === 0 && (
            <GlassCard style={styles.mealLogCard}>
              <View style={styles.mealLogRow}>
                <Text style={styles.mealLogTime}>--:-- PM</Text>
                <View style={styles.mealLogContent}>
                  <Text style={styles.mealLogEmpty}>No meals logged today. Tap to add.</Text>
                </View>
              </View>
            </GlassCard>
          )}
        </View>

        {/* ═══════════ 11. SPORT IQ ═══════════ */}
        {lessons.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Sport IQ</Text>
              <TouchableOpacity onPress={() => router.push('/(tabs)/sport')}>
                <Text style={styles.openLink}>Open</Text>
              </TouchableOpacity>
            </View>
            <GlassCard>
              <Text style={styles.sportIqTitle}>Sport IQ</Text>
              <Text style={styles.sportIqSubtitle}>Recommended lessons</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.lessonsScroll}
              >
                {lessons.slice(0, 3).map((lesson, i) => (
                  <TouchableOpacity key={lesson.id || i} style={styles.lessonChip}>
                    <View style={styles.lessonChipIcon}>
                      <Ionicons name="fitness-outline" size={16} color={colors.accentOrange} />
                    </View>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </GlassCard>
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.page, // Nike-style 24px padding
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingTop: spacing.xl,
    paddingBottom: spacing.section, // Nike-style 40px bottom
  },
  headerText: {
    flex: 1,
  },
  greeting: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  userName: {
    ...typography.h1,
    color: colors.textPrimary,
    marginTop: spacing.xs,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  profileButton: {
    padding: spacing.xs,
  },
  avatarCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
  },
  section: {
    marginBottom: spacing.section, // Nike-style 40px sections
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    ...typography.h4,  // Larger, sentence-case titles
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },
  openLink: {
    ...typography.captionMedium,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  heroCard: {
    padding: 0,
    overflow: 'hidden',
  },
  heroGradient: {
    padding: spacing.lg,
    minHeight: 160,
    justifyContent: 'flex-end',
  },
  heroTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
    fontWeight: '700',
  },
  heroMeta: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  loadHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  loadLabel: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  loadValue: {
    ...typography.h2,
    color: colors.textPrimary,
    marginTop: spacing.xs,
  },
  loadSubtext: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  loadBadges: {
    alignItems: 'flex-end',
    gap: spacing.sm,
  },
  loadProgress: {
    marginVertical: spacing.md,
  },
  loadHistory: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  loadNote: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.sm,
  },
  whiteCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.08)',
  },
  sourceChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: spacing.md,
  },
  sourceText: {
    fontSize: 11,
    color: colors.textTertiary,
  },
  cardCta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.05)',
  },
  ctaText: {
    fontSize: 13,
    color: colors.textTertiary,
  },
  activityRow: {
    position: 'relative',
    paddingRight: spacing.xl,
  },
  emptyActivity: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  emptyActivityIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surfaceSecondary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyActivityContent: {
    flex: 1,
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  activityTitle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  activityName: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  miniChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: 40,
    paddingRight: spacing.xxl,
    marginBottom: spacing.sm,
  },
  chartBar: {
    width: 24,
    borderRadius: 4,
  },
  activityNote: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  chevron: {
    position: 'absolute',
    right: 0,
    top: '50%',
    marginTop: -10,
  },
  trackFoodHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  trackFoodIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.accentOrangeLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  trackFoodContent: {
    flex: 1,
  },
  trackFoodTitle: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  trackFoodSubtitle: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  cameraButton: {
    padding: spacing.sm,
    marginRight: spacing.xs,
  },
  addButton: {
    padding: spacing.xs,
  },
  macroRingsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  calorieBalance: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
  },
  calorieLabel: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  calorieValue: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  nutritionAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
  },
  alertText: {
    ...typography.caption,
    color: colors.accentOrange,
    flex: 1,
  },
  goalsCard: {
    padding: 0,
  },
  goalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.xl, // Nike-style generous padding
    minHeight: 72, // Taller touch targets
  },
  goalSeparator: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.separator,
  },
  goalIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  goalContent: {
    flex: 1,
  },
  goalTitle: {
    ...typography.body,
    color: colors.textPrimary,
  },
  goalValue: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  mealLogCard: {
    marginBottom: spacing.md,
  },
  mealLogRow: {
    flexDirection: 'row',
  },
  mealLogTime: {
    ...typography.caption,
    color: colors.textTertiary,
    width: 60,
    marginRight: spacing.md,
  },
  mealLogContent: {
    flex: 1,
  },
  mealLogHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.xs,
  },
  mealLogType: {
    ...typography.captionMedium,
    color: colors.accentOrange,
    flex: 1,
  },
  mealLogCalories: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  mealLogCaloriesValue: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  mealLogFoods: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  mealLogEmpty: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  programTitle: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  programSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  programNext: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.xs,
  },
  programProgress: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginTop: spacing.lg,
  },
  programWeek: {
    ...typography.caption,
    color: colors.textTertiary,
    minWidth: 70,
  },
  programNote: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  programNoteText: {
    ...typography.caption,
    color: colors.accentTeal,
  },
  viewPlanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.separator,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.full,
    alignSelf: 'flex-start',
    marginTop: spacing.lg,
  },
  viewPlanText: {
    ...typography.captionMedium,
    color: colors.textPrimary,
    marginRight: spacing.xs,
  },
  sportIqTitle: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  sportIqSubtitle: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.xs,
    marginBottom: spacing.md,
  },
  lessonsScroll: {
    gap: spacing.sm,
  },
  lessonChip: {
    backgroundColor: colors.accentOrangeLight,
    width: 80,
    height: 60,
    borderRadius: borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  lessonChipIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

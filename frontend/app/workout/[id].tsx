import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Button } from '../../src/components/Button';
import { ExerciseThumbnail } from '../../src/components/ExerciseThumbnail';
import { WorkoutFeedbackModal } from '../../src/components/WorkoutFeedbackModal';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius, shadows } from '../../src/utils/theme';

type WorkoutSectionName = 'warmup' | 'main_work' | 'cooldown';

interface Exercise {
  name: string;
  exercise_id?: string | null;
  purpose?: string | null;
  sets?: number | null;
  reps?: string | null;
  duration?: string | null;
  rest?: string | null;
  load_guidance?: string | null;
  rpe?: string | null;
  tempo?: string | null;
  notes?: string | null;
  coaching_notes?: string[];
  instructions?: string[];
  common_errors?: string[];
  safety_boundaries?: string[];
  substitutions?: string[];
  library_enrichment?: {
    summary?: string | null;
    coaching_cues?: string[];
    common_errors?: string[];
  };
}

interface SessionPlan {
  day?: string;
  title?: string;
  category?: string;
  duration_min?: number;
  intensity?: string;
  adaptation_targets?: string[];
  sport_transfer?: string[];
  why_this_session?: string;
  warmup?: Exercise[];
  main_work?: Exercise[];
  cooldown?: Exercise[];
  injury_modifications?: string[];
}

interface Workout {
  id: string;
  title: string;
  category: string;
  duration: number;
  difficulty: string;
  equipment?: string[];
  exercises?: Exercise[];
  description?: string;
  ai_generated?: boolean;
  completed?: boolean;
  scheduled_date?: string;
  intensity?: string;
  week_number?: number;
  session_number?: number;
  user_feedback?: Record<string, unknown> | null;
  adaptation?: {
    goal?: string;
    sports?: string[];
    targets?: string[];
    sport_transfer?: string[];
    why_this_session?: string;
    injury_modifications?: string[];
    progression_rule?: string;
    week_theme?: string;
  };
  session_plan?: SessionPlan;
  version?: number;
}

interface SectionBlock {
  key: WorkoutSectionName;
  title: string;
  subtitle: string;
  icon: keyof typeof Ionicons.glyphMap;
  exercises: Exercise[];
}

const sectionCopy: Record<WorkoutSectionName, Omit<SectionBlock, 'key' | 'exercises'>> = {
  warmup: {
    title: 'Prepare',
    subtitle: 'Raise temperature, open the right ranges, and rehearse the pattern.',
    icon: 'pulse-outline',
  },
  main_work: {
    title: 'Main Work',
    subtitle: 'The focused training that drives today’s adaptation.',
    icon: 'barbell-outline',
  },
  cooldown: {
    title: 'Reset',
    subtitle: 'Downshift the system and leave the session clean.',
    icon: 'leaf-outline',
  },
};

const formatDateLabel = (date?: string) => {
  if (!date) return 'Planned session';
  const parsed = new Date(`${date}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
};

const compact = (items?: (string | null | undefined)[], limit = 4) =>
  (items || []).filter((item): item is string => Boolean(item && item.trim())).slice(0, limit);

const displayWorkoutTitle = (purpose?: string, category?: string) => {
  if (!purpose || /^give the deterministic workout compiler/i.test(purpose) || /^this is a bounded main/i.test(purpose)) {
    return `${(category || 'Training').replace(/[_-]+/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())} Session`;
  }
  return purpose;
};

const displayRepetitions = (value: unknown) => {
  if (typeof value === 'number' || typeof value === 'string') return String(value);
  if (!value || typeof value !== 'object') return undefined;
  const dose = value as { minimum?: number; maximum?: number; per_side?: boolean };
  const range = dose.minimum != null && dose.maximum != null && dose.minimum !== dose.maximum
    ? `${dose.minimum}-${dose.maximum}`
    : dose.maximum ?? dose.minimum;
  return range == null ? undefined : `${range}${dose.per_side ? ' / side' : ''}`;
};

const displayRange = (value: unknown, unit: string) => {
  if (typeof value === 'number' || typeof value === 'string') return `${value}${unit}`;
  if (!value || typeof value !== 'object') return undefined;
  const range = value as { minimum?: number; maximum?: number };
  if (range.minimum == null && range.maximum == null) return undefined;
  const low = range.minimum ?? range.maximum;
  const high = range.maximum ?? range.minimum;
  return low === high ? `${low}${unit}` : `${low}-${high}${unit}`;
};

const prescriptionFor = (exercise: Exercise) => {
  const parts: string[] = [];
  if (exercise.sets) parts.push(`${exercise.sets} sets`);
  if (exercise.reps) parts.push(`${exercise.reps} reps`);
  if (exercise.duration) parts.push(exercise.duration);
  if (exercise.load_guidance) parts.push(exercise.load_guidance);
  return parts.join(' · ') || 'Quality reps';
};

export default function WorkoutDetailScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();

  const [workout, setWorkout] = useState<Workout | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [checkedExercises, setCheckedExercises] = useState<Set<string>>(new Set());

  const fetchWorkout = useCallback(async () => {
    try {
      setLoading(true);
      const session = await api.get<any>(`/training/sessions/${id}`);
      const exercises: Exercise[] = (session.items || []).map((item: any) => ({
        name: item.method_name,
        exercise_id: item.method_id,
        sets: item.prescription?.sets,
        reps: displayRepetitions(item.prescription?.repetitions),
        duration: displayRange(item.prescription?.duration_minutes, ' min')
          || displayRange(item.prescription?.duration_seconds, 's'),
        rest: displayRange(item.prescription?.recovery_seconds, 's')
          || displayRange(item.prescription?.recovery_between_sets_seconds, 's'),
        load_guidance: displayRange(item.prescription?.load_kg, ' kg')
          || displayRange(item.prescription?.percentage_1rm, '% 1RM'),
        rpe: displayRange(item.prescription?.effort_rpe, ' RPE')
          || displayRange(item.prescription?.rir, ' RIR'),
        tempo: displayRange(item.prescription?.tempo_seconds, 's tempo'),
        substitutions: item.alternatives || [],
        coaching_notes: item.coaching_cues || [],
        instructions: item.instructions || [],
        common_errors: item.common_errors || [],
        safety_boundaries: item.safety_boundaries || [],
      }));
      const sectionFor = (blockType: string) => {
        if (blockType === 'warmup' || blockType === 'preparation') return 'warmup';
        if (blockType === 'cooldown' || blockType === 'recovery') return 'cooldown';
        return 'main_work';
      };
      const warmup = (session.items || [])
        .filter((item: any) => sectionFor(item.block_type) === 'warmup')
        .map((item: any, index: number) => ({ ...exercises[(session.items || []).indexOf(item)], key: `warmup-${index}` }));
      const mainWork = (session.items || [])
        .filter((item: any) => sectionFor(item.block_type) === 'main_work')
        .map((item: any, index: number) => ({ ...exercises[(session.items || []).indexOf(item)], key: `main-${index}` }));
      const cooldown = (session.items || [])
        .filter((item: any) => sectionFor(item.block_type) === 'cooldown')
        .map((item: any, index: number) => ({ ...exercises[(session.items || []).indexOf(item)], key: `cooldown-${index}` }));
      const title = displayWorkoutTitle(session.purpose, session.session_type);
      setWorkout({
        id: session.id,
        title,
        category: session.session_type,
        duration: session.estimated_minutes,
        difficulty: session.status,
        completed: session.status === 'completed',
        scheduled_date: session.scheduled_for?.slice(0, 10),
        description: session.explanation,
        ai_generated: session.session_type === 'ai_training',
        exercises,
        version: session.version,
        session_plan: {
          title,
          category: session.session_type,
          duration_min: session.estimated_minutes,
          why_this_session: session.explanation,
          warmup,
          main_work: mainWork,
          cooldown,
        },
      });
    } catch (error) {
      console.error('Error fetching workout:', error);
      setWorkout(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchWorkout();
  }, [fetchWorkout]);

  const sections = useMemo<SectionBlock[]>(() => {
    if (!workout) return [];
    const plan = workout.session_plan;
    const fromPlan: SectionBlock[] = (['warmup', 'main_work', 'cooldown'] as WorkoutSectionName[])
      .map((key) => ({
        key,
        ...sectionCopy[key],
        exercises: plan?.[key] || [],
      }))
      .filter((section) => section.exercises.length > 0);

    if (fromPlan.length > 0) return fromPlan;

    return [{
      key: 'main_work',
      ...sectionCopy.main_work,
      exercises: workout.exercises || [],
    }];
  }, [workout]);

  const totalExercises = useMemo(
    () => sections.reduce((sum, section) => sum + section.exercises.length, 0),
    [sections],
  );

  const completionPercent = totalExercises > 0
    ? Math.round((checkedExercises.size / totalExercises) * 100)
    : 0;

  const workoutPurpose = workout?.session_plan?.why_this_session
    || workout?.adaptation?.why_this_session
    || workout?.description
    || 'AI-built session from your current program.';

  const sportTransfer = compact(workout?.session_plan?.sport_transfer || workout?.adaptation?.sport_transfer, 5);
  const targets = compact(workout?.session_plan?.adaptation_targets || workout?.adaptation?.targets, 5);
  const injuryNotes = compact(workout?.session_plan?.injury_modifications || workout?.adaptation?.injury_modifications, 4);

  const toggleExercise = (key: string) => {
    setCheckedExercises((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleFeedbackSubmitted = async () => {
    setShowFeedbackModal(false);
    await fetchWorkout();
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color={colors.textPrimary} />
      </View>
    );
  }

  if (!workout) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <Ionicons name="barbell-outline" size={56} color={colors.textTertiary} />
        <Text style={styles.errorText}>Workout not found</Text>
        <Button title="Go Back" onPress={() => router.back()} style={{ marginTop: spacing.lg }} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.iconButton}>
          <Ionicons name="chevron-back" size={26} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerRight}>
          {workout.ai_generated && (
            <View style={styles.aiTag}>
              <Ionicons name="sparkles" size={13} color={colors.textSecondary} />
              <Text style={styles.aiTagText}>AI plan</Text>
            </View>
          )}
          <TouchableOpacity style={styles.iconButton}>
            <Ionicons name="bookmark-outline" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 132 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.hero}>
          <Text style={styles.eyebrow}>{formatDateLabel(workout.scheduled_date)}</Text>
          <Text style={styles.workoutTitle}>{workout.title}</Text>
          <View style={styles.metaRow}>
            <MetaChip icon="time-outline" label={`${workout.duration} min`} />
            <MetaChip icon="speedometer-outline" label={workout.intensity || workout.difficulty} />
            <MetaChip icon="layers-outline" label={`${totalExercises} movements`} />
          </View>
          <Text style={styles.purpose}>{workoutPurpose}</Text>
        </View>

        {(workout.adaptation?.week_theme || workout.adaptation?.progression_rule) && (
          <View style={styles.coachCard}>
            <Text style={styles.coachLabel}>Coach Plan</Text>
            {workout.adaptation?.week_theme && (
              <Text style={styles.coachText}>{workout.adaptation.week_theme}</Text>
            )}
            {workout.adaptation?.progression_rule && (
              <Text style={styles.coachSubtext}>{workout.adaptation.progression_rule}</Text>
            )}
          </View>
        )}

        {(targets.length > 0 || sportTransfer.length > 0 || injuryNotes.length > 0) && (
          <View style={styles.contextGrid}>
            {targets.length > 0 && <InfoBlock title="Targets" items={targets} />}
            {sportTransfer.length > 0 && <InfoBlock title="Sport Transfer" items={sportTransfer} />}
            {injuryNotes.length > 0 && <InfoBlock title="Safety" items={injuryNotes} />}
          </View>
        )}

        <View style={styles.progressCard}>
          <View style={styles.progressHeader}>
            <View>
              <Text style={styles.progressTitle}>Session Progress</Text>
              <Text style={styles.progressText}>{checkedExercises.size} of {totalExercises} movements checked</Text>
            </View>
            <Text style={styles.progressValue}>{completionPercent}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${completionPercent}%` }]} />
          </View>
        </View>

        {sections.map((section) => (
          <View key={section.key} style={styles.section}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIcon}>
                <Ionicons name={section.icon} size={18} color={colors.textPrimary} />
              </View>
              <View style={styles.sectionCopy}>
                <Text style={styles.sectionTitle}>{section.title}</Text>
                <Text style={styles.sectionSubtitle}>{section.subtitle}</Text>
              </View>
            </View>
            {section.exercises.map((exercise, index) => {
              const exerciseKey = `${section.key}-${index}`;
              const checked = checkedExercises.has(exerciseKey);
              return (
                <ExerciseCard
                  key={exerciseKey}
                  exercise={exercise}
                  checked={checked}
                  index={index + 1}
                  onPress={() => toggleExercise(exerciseKey)}
                />
              );
            })}
          </View>
        ))}

        {workout.equipment && workout.equipment.length > 0 && (
          <View style={styles.equipmentSection}>
            <Text style={styles.smallSectionTitle}>Equipment</Text>
            <View style={styles.equipmentRow}>
              {workout.equipment.map((item) => (
                <View key={item} style={styles.equipmentChip}>
                  <Text style={styles.equipmentText}>{item}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      <View style={[styles.bottomBar, { paddingBottom: insets.bottom + spacing.md }]}>
        {workout.completed ? (
          <View style={styles.completedBanner}>
            <Ionicons name="checkmark-circle" size={24} color={colors.statusSuccess} />
            <Text style={styles.completedText}>Workout completed</Text>
          </View>
        ) : (
          <Button
            title={completionPercent >= 100 ? 'Finish & Log Feedback' : 'Log Progress'}
            onPress={() => setShowFeedbackModal(true)}
            fullWidth
            size="lg"
          />
        )}
      </View>

      <WorkoutFeedbackModal
        visible={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmitted={handleFeedbackSubmitted}
        workoutId={workout.id}
        workoutTitle={workout.title}
        initialCompletionPercentage={completionPercent}
        expectedVersion={workout.version}
        estimatedMinutes={workout.duration}
        mainExercises={(((workout as any)?.session_plan?.main_work as any[]) || [])
          .map((ex) => ({ name: ex?.name as string, exercise_id: (ex?.exercise_id ?? ex?.knowledge_ref?.exercise_id ?? null) as string | null }))
          .filter((ex) => !!ex.name)}
      />
    </View>
  );
}

function MetaChip({ icon, label }: { icon: keyof typeof Ionicons.glyphMap; label: string }) {
  return (
    <View style={styles.metaChip}>
      <Ionicons name={icon} size={15} color={colors.textSecondary} />
      <Text style={styles.metaText}>{label}</Text>
    </View>
  );
}

function InfoBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <View style={styles.infoBlock}>
      <Text style={styles.infoTitle}>{title}</Text>
      {items.map((item) => (
        <Text key={`${title}-${item}`} style={styles.infoText}>• {item}</Text>
      ))}
    </View>
  );
}

function ExerciseCard({
  exercise,
  checked,
  index,
  onPress,
}: {
  exercise: Exercise;
  checked: boolean;
  index: number;
  onPress: () => void;
}) {
  const cues = compact(exercise.coaching_notes || exercise.library_enrichment?.coaching_cues, 2);
  const substitutions = compact(exercise.substitutions, 2);

  return (
    <TouchableOpacity
      style={[styles.exerciseCard, checked && styles.exerciseCardChecked]}
      activeOpacity={0.82}
      onPress={onPress}
    >
      <View style={[styles.checkbox, checked && styles.checkboxChecked]}>
        {checked ? (
          <Ionicons name="checkmark" size={16} color={colors.background} />
        ) : (
          <Text style={styles.checkboxNumber}>{index}</Text>
        )}
      </View>
      <ExerciseThumbnail name={exercise.name} size={54} style={styles.exercisePreview} />
      <View style={styles.exerciseBody}>
        <Text style={[styles.exerciseName, checked && styles.exerciseNameChecked]}>{exercise.name}</Text>
        <View style={styles.prescriptionRow}>
          <Prescription label={prescriptionFor(exercise)} />
          {exercise.rest && <Prescription label={`Rest ${exercise.rest}`} />}
          {exercise.rpe && <Prescription label={exercise.rpe} />}
          {exercise.tempo && <Prescription label={`Tempo ${exercise.tempo}`} />}
        </View>
        {exercise.purpose && <Text style={styles.exercisePurpose}>{exercise.purpose}</Text>}
        {exercise.load_guidance && <Text style={styles.exerciseGuidance}>{exercise.load_guidance}</Text>}
        {exercise.instructions && exercise.instructions.length > 0 && (
          <View style={styles.noteBlock}>
            <Text style={styles.noteLabel}>How to perform</Text>
            {exercise.instructions.slice(0, 4).map((instruction) => <Text key={instruction} style={styles.noteText}>{instruction}</Text>)}
          </View>
        )}
        {exercise.common_errors && exercise.common_errors.length > 0 && (
          <View style={styles.noteBlock}>
            <Text style={styles.noteLabel}>Avoid</Text>
            {exercise.common_errors.slice(0, 3).map((error) => <Text key={error} style={styles.noteText}>{error}</Text>)}
          </View>
        )}
        {exercise.safety_boundaries && exercise.safety_boundaries.length > 0 && (
          <View style={styles.noteBlock}>
            <Text style={styles.noteLabel}>Safety</Text>
            {exercise.safety_boundaries.slice(0, 3).map((boundary) => <Text key={boundary} style={styles.noteText}>{boundary}</Text>)}
          </View>
        )}
        {cues.length > 0 && (
          <View style={styles.noteBlock}>
            <Text style={styles.noteLabel}>Cues</Text>
            {cues.map((cue) => <Text key={cue} style={styles.noteText}>{cue}</Text>)}
          </View>
        )}
        {substitutions.length > 0 && (
          <Text style={styles.substitutionText}>Swap: {substitutions.join(' · ')}</Text>
        )}
      </View>
    </TouchableOpacity>
  );
}

function Prescription({ label }: { label: string }) {
  return (
    <View style={styles.prescriptionChip}>
      <Text style={styles.prescriptionText}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.xl,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  iconButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  aiTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.separator,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  aiTagText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
  },
  errorText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.lg,
  },
  hero: {
    paddingTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  eyebrow: {
    ...typography.captionMedium,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  workoutTitle: {
    ...typography.h1,
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  metaChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.separator,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  metaText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  purpose: {
    ...typography.body,
    color: colors.textSecondary,
  },
  coachCard: {
    backgroundColor: colors.surfaceSecondary,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
  },
  coachLabel: {
    ...typography.labelSmall,
    color: colors.textTertiary,
    marginBottom: spacing.sm,
  },
  coachText: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  coachSubtext: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  contextGrid: {
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  infoBlock: {
    borderWidth: 1,
    borderColor: colors.separatorDark,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
  },
  infoTitle: {
    ...typography.label,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  infoText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  progressCard: {
    backgroundColor: colors.textPrimary,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    marginBottom: spacing.xxl,
    ...shadows.sm,
  },
  progressHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  progressTitle: {
    ...typography.bodySemibold,
    color: colors.background,
  },
  progressText: {
    ...typography.caption,
    color: 'rgba(255,255,255,0.72)',
    marginTop: spacing.xs,
  },
  progressValue: {
    ...typography.h2,
    color: colors.background,
  },
  progressBar: {
    height: 7,
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.background,
    borderRadius: borderRadius.full,
  },
  section: {
    marginBottom: spacing.xxl,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  sectionIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sectionCopy: {
    flex: 1,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  sectionSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  exerciseCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    paddingVertical: spacing.lg,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separatorDark,
  },
  exerciseCardChecked: {
    opacity: 0.62,
  },
  checkbox: {
    width: 30,
    height: 30,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: colors.separatorDark,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 1,
  },
  checkboxChecked: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary,
  },
  checkboxNumber: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  exercisePreview: {
    marginTop: 0,
  },
  exerciseBody: {
    flex: 1,
  },
  exerciseName: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  exerciseNameChecked: {
    textDecorationLine: 'line-through',
    color: colors.textTertiary,
  },
  prescriptionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  prescriptionChip: {
    backgroundColor: colors.separator,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  prescriptionText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  exercisePurpose: {
    ...typography.caption,
    color: colors.textPrimary,
    marginTop: spacing.xs,
  },
  exerciseGuidance: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  noteBlock: {
    marginTop: spacing.md,
    paddingLeft: spacing.md,
    borderLeftWidth: 2,
    borderLeftColor: colors.separatorDark,
  },
  noteLabel: {
    ...typography.labelSmall,
    color: colors.textTertiary,
    marginBottom: spacing.xs,
  },
  noteText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  substitutionText: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.sm,
  },
  equipmentSection: {
    marginBottom: spacing.xxl,
  },
  smallSectionTitle: {
    ...typography.label,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  equipmentRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  equipmentChip: {
    backgroundColor: colors.separator,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  equipmentText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
  },
  completedBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.md,
  },
  completedText: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
});

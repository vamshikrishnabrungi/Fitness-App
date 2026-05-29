import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../src/components/GlassCard';
import { Badge } from '../../src/components/Badge';
import { Button } from '../../src/components/Button';
import { WorkoutFeedbackModal } from '../../src/components/WorkoutFeedbackModal';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

interface Exercise {
  name: string;
  sets?: number;
  reps?: string;
  duration?: string;
  rest?: string;
  notes?: string;
}

interface Workout {
  id: string;
  title: string;
  category: string;
  duration: number;
  difficulty: string;
  equipment: string[];
  exercises: Exercise[];
  description?: string;
  ai_generated: boolean;
  completed: boolean;
}

export default function WorkoutDetailScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  
  const [workout, setWorkout] = useState<Workout | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [checkedExercises, setCheckedExercises] = useState<Set<number>>(new Set());

  const fetchWorkout = useCallback(async () => {
    try {
      // Try to get today's workout or specific workout
      const workouts = await api.get<Workout[]>('/workouts');
      const foundWorkout = workouts.find(w => w.id === id);
      if (foundWorkout) {
        setWorkout(foundWorkout);
      } else {
        // Try today's workout
        const todayWorkout = await api.get<Workout>('/workouts/today');
        setWorkout(todayWorkout);
      }
    } catch (error) {
      console.error('Error fetching workout:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchWorkout();
  }, [fetchWorkout]);

  const toggleExercise = (index: number) => {
    const newChecked = new Set(checkedExercises);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedExercises(newChecked);
  };

  const handleStartWorkout = () => {
    Alert.alert(
      'Start Workout',
      `Ready to begin ${workout?.title}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: "Let's Go!", onPress: () => {} },
      ]
    );
  };

  const handleCompleteWorkout = () => {
    if (workout?.completed) {
      Alert.alert('Already Completed', 'You\'ve already completed this workout!');
      return;
    }
    setShowFeedbackModal(true);
  };

  const handleFeedbackClose = () => {
    setShowFeedbackModal(false);
    // Refresh workout to show completed status
    fetchWorkout();
    Alert.alert(
      'Workout Complete!',
      'Your feedback has been submitted. SFTC AI will use this to optimize your future workouts.',
      [{ text: 'Awesome', onPress: () => router.back() }]
    );
  };

  const progress = workout?.exercises.length 
    ? (checkedExercises.size / workout.exercises.length) * 100 
    : 0;

  const exerciseCardStyle = (completed: boolean) =>
    StyleSheet.flatten([styles.exerciseCard, completed && styles.exerciseCardCompleted]);

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
        <Ionicons name="barbell-outline" size={64} color={colors.textTertiary} />
        <Text style={styles.errorText}>Workout not found</Text>
        <Button title="Go Back" onPress={() => router.back()} style={{ marginTop: spacing.lg }} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerRight}>
          {workout.ai_generated && (
            <View style={styles.aiTag}>
              <Ionicons name="sparkles" size={14} color={colors.textSecondary} />
              <Text style={styles.aiTagText}>AI</Text>
            </View>
          )}
          <TouchableOpacity style={styles.menuButton}>
            <Ionicons name="ellipsis-horizontal" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 100 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Workout Info */}
        <View style={styles.workoutHeader}>
          <Badge label={workout.category} variant="filled" size="sm" />
          <Text style={styles.workoutTitle}>{workout.title}</Text>
          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Ionicons name="time-outline" size={16} color={colors.textSecondary} />
              <Text style={styles.metaText}>{workout.duration} min</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="flame-outline" size={16} color={colors.textSecondary} />
              <Text style={styles.metaText}>{workout.difficulty}</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="barbell-outline" size={16} color={colors.textSecondary} />
              <Text style={styles.metaText}>{workout.exercises.length} exercises</Text>
            </View>
          </View>
          {workout.description && (
            <Text style={styles.description}>{workout.description}</Text>
          )}
        </View>

        {/* Progress Bar */}
        <GlassCard style={styles.progressCard}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressLabel}>Progress</Text>
            <Text style={styles.progressValue}>{Math.round(progress)}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
          <Text style={styles.progressSubtext}>
            {checkedExercises.size} of {workout.exercises.length} exercises completed
          </Text>
        </GlassCard>

        {/* Exercises List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>EXERCISES</Text>
          {workout.exercises.map((exercise, index) => (
            <TouchableOpacity
              key={index}
              activeOpacity={0.8}
              onPress={() => toggleExercise(index)}
            >
              <GlassCard style={exerciseCardStyle(checkedExercises.has(index))}>
                <View style={styles.exerciseRow}>
                  <View style={[
                    styles.checkbox,
                    checkedExercises.has(index) && styles.checkboxChecked
                  ]}>
                    {checkedExercises.has(index) && (
                      <Ionicons name="checkmark" size={16} color={colors.background} />
                    )}
                  </View>
                  <View style={styles.exerciseContent}>
                    <Text style={[
                      styles.exerciseName,
                      checkedExercises.has(index) && styles.exerciseNameCompleted
                    ]}>
                      {exercise.name}
                    </Text>
                    <View style={styles.exerciseDetails}>
                      {exercise.sets && (
                        <Text style={styles.exerciseDetail}>{exercise.sets} sets</Text>
                      )}
                      {exercise.reps && (
                        <Text style={styles.exerciseDetail}>{exercise.reps} reps</Text>
                      )}
                      {exercise.duration && (
                        <Text style={styles.exerciseDetail}>{exercise.duration}</Text>
                      )}
                      {exercise.rest && (
                        <Text style={styles.exerciseDetail}>Rest: {exercise.rest}</Text>
                      )}
                    </View>
                    {exercise.notes && (
                      <Text style={styles.exerciseNotes}>{exercise.notes}</Text>
                    )}
                  </View>
                  <View style={styles.exerciseNumber}>
                    <Text style={styles.exerciseNumberText}>{index + 1}</Text>
                  </View>
                </View>
              </GlassCard>
            </TouchableOpacity>
          ))}
        </View>

        {/* Equipment */}
        {workout.equipment && workout.equipment.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>EQUIPMENT NEEDED</Text>
            <View style={styles.equipmentRow}>
              {workout.equipment.map((item, index) => (
                <View key={index} style={styles.equipmentChip}>
                  <Text style={styles.equipmentText}>{item}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      {/* Bottom Action Bar */}
      <View style={[styles.bottomBar, { paddingBottom: insets.bottom + spacing.md }]}>
        {workout.completed ? (
          <View style={styles.completedBanner}>
            <Ionicons name="checkmark-circle" size={24} color={colors.textPrimary} />
            <Text style={styles.completedText}>Workout Completed</Text>
          </View>
        ) : progress === 100 ? (
          <Button
            title="Complete Workout & Give Feedback"
            onPress={handleCompleteWorkout}
            fullWidth
            size="lg"
          />
        ) : (
          <View style={styles.bottomButtons}>
            <Button
              title="Start Workout"
              onPress={handleStartWorkout}
              style={{ flex: 1 }}
              size="lg"
            />
            <TouchableOpacity
              style={styles.completeButton}
              onPress={handleCompleteWorkout}
            >
              <Ionicons name="checkmark-done" size={24} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Feedback Modal */}
      <WorkoutFeedbackModal
        visible={showFeedbackModal}
        onClose={handleFeedbackClose}
        workoutId={workout.id}
        workoutTitle={workout.title}
      />
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
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
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
  menuButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },
  errorText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.lg,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
  },
  workoutHeader: {
    marginBottom: spacing.xl,
  },
  workoutTitle: {
    ...typography.h2,
    color: colors.textPrimary,
    marginTop: spacing.md,
    marginBottom: spacing.md,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.lg,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  metaText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  description: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  progressCard: {
    marginBottom: spacing.xl,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  progressLabel: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  progressValue: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  progressBar: {
    height: 8,
    backgroundColor: colors.progressTrack,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.textPrimary,
    borderRadius: 4,
  },
  progressSubtext: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.sm,
  },
  section: {
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  exerciseCard: {
    marginBottom: spacing.sm,
  },
  exerciseCardCompleted: {
    opacity: 0.6,
  },
  exerciseRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: colors.textTertiary,
    marginRight: spacing.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary,
  },
  exerciseContent: {
    flex: 1,
  },
  exerciseName: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  exerciseNameCompleted: {
    textDecorationLine: 'line-through',
    color: colors.textTertiary,
  },
  exerciseDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  exerciseDetail: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  exerciseNotes: {
    ...typography.caption,
    color: colors.textTertiary,
    fontStyle: 'italic',
    marginTop: spacing.sm,
  },
  exerciseNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
  },
  exerciseNumberText: {
    ...typography.captionMedium,
    color: colors.textTertiary,
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
    borderRadius: borderRadius.md,
  },
  equipmentText: {
    ...typography.caption,
    color: colors.textPrimary,
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
  bottomButtons: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  completeButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
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

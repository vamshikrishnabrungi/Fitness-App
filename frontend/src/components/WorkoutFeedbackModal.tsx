import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Button } from './Button';
import { api } from '../utils/api';
import { colors, typography, spacing, borderRadius } from '../utils/theme';

interface WorkoutFeedbackModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmitted?: () => void;
  workoutId: string;
  workoutTitle: string;
  initialCompletionPercentage?: number;
  expectedVersion?: number;
  estimatedMinutes?: number;
  mainExercises?: { name: string; exercise_id?: string | null }[];
}

export const WorkoutFeedbackModal: React.FC<WorkoutFeedbackModalProps> = ({
  visible,
  onClose,
  onSubmitted,
  workoutId,
  workoutTitle,
  initialCompletionPercentage = 100,
  expectedVersion = 1,
  estimatedMinutes = 60,
  mainExercises = [],
}) => {
  const insets = useSafeAreaInsets();
  const [intensity, setIntensity] = useState(5);
  const [completion, setCompletion] = useState(initialCompletionPercentage);
  const [difficulty, setDifficulty] = useState<'too_easy' | 'just_right' | 'too_hard'>('just_right');
  const [energy, setEnergy] = useState<'low' | 'moderate' | 'high'>('moderate');
  const [painScore, setPainScore] = useState(0);
  const [notes, setNotes] = useState('');
  const [loads, setLoads] = useState<Record<string, { weight: string; reps: string }>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!visible) return;
    setCompletion(initialCompletionPercentage);
    setIntensity(5);
    setDifficulty('just_right');
    setEnergy('moderate');
    setPainScore(0);
    setNotes('');
    setLoads({});
  }, [initialCompletionPercentage, visible]);

  const setLoad = (name: string, patch: Partial<{ weight: string; reps: string }>) =>
    setLoads((prev) => ({ ...prev, [name]: { ...(prev[name] || { weight: '', reps: '' }), ...patch } }));

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const performed = (mainExercises || [])
        .map((ex) => {
          const entry = loads[ex.name] || { weight: '', reps: '' };
          const weight_kg = parseFloat(entry.weight);
          const reps = parseInt(entry.reps, 10);
          return {
            name: ex.name,
            exercise_id: ex.exercise_id ?? null,
            weight_kg: Number.isFinite(weight_kg) ? weight_kg : null,
            reps: Number.isFinite(reps) ? reps : null,
          };
        })
        .filter((p) => p.weight_kg !== null || p.reps !== null);
      await api.post(`/training/sessions/${workoutId}/complete`, {
        duration_minutes: estimatedMinutes,
        session_rpe: intensity,
        completion_ratio: completion / 100,
        pain_flag: painScore > 0,
        expected_version: expectedVersion,
        difficulty_feedback: difficulty,
        energy_level: energy,
        notes: notes || null,
        performed_exercises: performed,
      });
      onSubmitted?.();
      if (!onSubmitted) onClose();
    } catch (error) {
      console.error('Error submitting feedback:', error);
      Alert.alert('Could not save workout', 'Please check your connection and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const difficultyOptions = [
    { value: 'too_easy', label: 'Too Easy', icon: 'happy-outline' },
    { value: 'just_right', label: 'Just Right', icon: 'thumbs-up-outline' },
    { value: 'too_hard', label: 'Too Hard', icon: 'fitness-outline' },
  ];

  const energyOptions = [
    { value: 'low', label: 'Low', icon: 'battery-dead-outline' },
    { value: 'moderate', label: 'Moderate', icon: 'battery-half-outline' },
    { value: 'high', label: 'High', icon: 'battery-full-outline' },
  ];

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={[styles.container, { paddingBottom: insets.bottom + spacing.lg }]}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={colors.textPrimary} />
            </TouchableOpacity>
            <Text style={styles.title}>Workout Complete</Text>
            <View style={{ width: 44 }} />
          </View>

          <ScrollView
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.celebration}>
              <Text style={styles.celebrationTitle}>Log your session.</Text>
              <Text style={styles.celebrationSubtitle}>{workoutTitle}</Text>
            </View>

            {mainExercises.length > 0 ? (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Working sets (optional)</Text>
                <Text style={styles.logHint}>Enter the top set you actually lifted — this powers your strength trends.</Text>
                {mainExercises.map((ex) => (
                  <View key={ex.name} style={styles.logRow}>
                    <Text style={styles.logName} numberOfLines={1}>{ex.name}</Text>
                    <TextInput
                      style={styles.logInput}
                      value={loads[ex.name]?.weight || ''}
                      onChangeText={(t) => setLoad(ex.name, { weight: t })}
                      keyboardType="numeric"
                      placeholder="kg"
                      placeholderTextColor={colors.textTertiary}
                    />
                    <Text style={styles.logMul}>×</Text>
                    <TextInput
                      style={styles.logInput}
                      value={loads[ex.name]?.reps || ''}
                      onChangeText={(t) => setLoad(ex.name, { reps: t })}
                      keyboardType="numeric"
                      placeholder="reps"
                      placeholderTextColor={colors.textTertiary}
                    />
                  </View>
                ))}
              </View>
            ) : null}

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Session RPE</Text>
              <View style={styles.sliderContainer}>
                <Text style={styles.sliderLabel}>1</Text>
                <View style={styles.intensityDots}>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                    <TouchableOpacity
                      key={num}
                      style={[
                        styles.intensityDot,
                        intensity >= num && styles.intensityDotActive,
                      ]}
                      onPress={() => setIntensity(num)}
                    />
                  ))}
                </View>
                <Text style={styles.sliderLabel}>10</Text>
              </View>
              <Text style={styles.fieldHint}>{intensity}/10 · how hard the full session felt</Text>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Completed</Text>
              <View style={styles.completionOptions}>
                {[0, 25, 50, 75, 100].map((pct) => (
                  <TouchableOpacity
                    key={pct}
                    style={[
                      styles.completionOption,
                      completion === pct && styles.completionOptionActive,
                    ]}
                    onPress={() => setCompletion(pct)}
                  >
                    <Text style={[
                      styles.completionText,
                      completion === pct && styles.completionTextActive,
                    ]}>
                      {pct}%
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Difficulty</Text>
              <View style={styles.optionRow}>
                {difficultyOptions.map((opt) => (
                  <TouchableOpacity
                    key={opt.value}
                    style={[
                      styles.optionCard,
                      difficulty === opt.value && styles.optionCardActive,
                    ]}
                    onPress={() => setDifficulty(opt.value as any)}
                  >
                    <Ionicons
                      name={opt.icon as any}
                      size={24}
                      color={difficulty === opt.value ? colors.background : colors.textPrimary}
                    />
                    <Text style={[
                      styles.optionLabel,
                      difficulty === opt.value && styles.optionLabelActive,
                    ]}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Energy after</Text>
              <View style={styles.optionRow}>
                {energyOptions.map((opt) => (
                  <TouchableOpacity
                    key={opt.value}
                    style={[
                      styles.optionCard,
                      energy === opt.value && styles.optionCardActive,
                    ]}
                    onPress={() => setEnergy(opt.value as any)}
                  >
                    <Ionicons
                      name={opt.icon as any}
                      size={24}
                      color={energy === opt.value ? colors.background : colors.textPrimary}
                    />
                    <Text style={[
                      styles.optionLabel,
                      energy === opt.value && styles.optionLabelActive,
                    ]}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Pain or discomfort</Text>
              <View style={styles.painRow}>
                {[0, 1, 2, 3, 4, 5].map((score) => (
                  <TouchableOpacity
                    key={score}
                    style={[
                      styles.painOption,
                      painScore === score && styles.painOptionActive,
                    ]}
                    onPress={() => setPainScore(score)}
                  >
                    <Text style={[
                      styles.painText,
                      painScore === score && styles.painTextActive,
                    ]}>
                      {score}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              <Text style={styles.fieldHint}>0 is none. Use notes for location or movement.</Text>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Notes</Text>
              <TextInput
                style={styles.notesInput}
                placeholder="What felt strong, painful, skipped, or too easy?"
                placeholderTextColor={colors.textTertiary}
                value={notes}
                onChangeText={setNotes}
                multiline
                numberOfLines={3}
              />
            </View>

            <View style={styles.aiNote}>
              <Ionicons name="sparkles" size={16} color={colors.textTertiary} />
              <Text style={styles.aiNoteText}>
                This updates your training history, level assessment, and future blocks.
              </Text>
            </View>
          </ScrollView>

          {/* Submit Button */}
          <View style={styles.footer}>
            <Button
              title="Save Session"
              onPress={handleSubmit}
              loading={submitting}
              fullWidth
              size="lg"
            />
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius.xxl,
    borderTopRightRadius: borderRadius.xxl,
    maxHeight: '90%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.separator,
  },
  closeButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  celebration: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  celebrationTitle: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  celebrationSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    textAlign: 'center',
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  logHint: {
    fontSize: 12,
    color: colors.textTertiary,
    marginTop: -spacing.sm,
    marginBottom: spacing.sm,
  },
  logRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  logName: {
    flex: 1,
    fontSize: 14,
    color: colors.textPrimary,
  },
  logInput: {
    width: 60,
    textAlign: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.separatorDark,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.sm,
    fontSize: 15,
    color: colors.textPrimary,
    backgroundColor: colors.surfaceSecondary,
  },
  logMul: {
    fontSize: 14,
    color: colors.textTertiary,
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  sliderLabel: {
    ...typography.caption,
    color: colors.textTertiary,
    width: 20,
    textAlign: 'center',
  },
  intensityDots: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  intensityDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.separator,
  },
  intensityDotActive: {
    backgroundColor: colors.textPrimary,
  },
  fieldHint: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.md,
  },
  completionOptions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  completionOption: {
    flex: 1,
    backgroundColor: colors.separator,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  completionOptionActive: {
    backgroundColor: colors.textPrimary,
  },
  completionText: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  completionTextActive: {
    color: colors.background,
  },
  optionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  optionCard: {
    flex: 1,
    backgroundColor: colors.separator,
    paddingVertical: spacing.lg,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    gap: spacing.sm,
  },
  optionCardActive: {
    backgroundColor: colors.textPrimary,
  },
  optionLabel: {
    ...typography.caption,
    color: colors.textPrimary,
  },
  optionLabelActive: {
    color: colors.background,
  },
  painRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  painOption: {
    flex: 1,
    height: 44,
    borderRadius: borderRadius.full,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
  },
  painOptionActive: {
    backgroundColor: colors.textPrimary,
  },
  painText: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
  },
  painTextActive: {
    color: colors.background,
  },
  notesInput: {
    backgroundColor: colors.separator,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...typography.body,
    color: colors.textPrimary,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  aiNote: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  aiNoteText: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  footer: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
  },
});

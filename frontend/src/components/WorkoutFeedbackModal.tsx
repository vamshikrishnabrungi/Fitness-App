import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GlassCard } from './GlassCard';
import { Button } from './Button';
import { api } from '../utils/api';
import { colors, typography, spacing, borderRadius } from '../utils/theme';

interface WorkoutFeedbackModalProps {
  visible: boolean;
  onClose: () => void;
  workoutId: string;
  workoutTitle: string;
}

export const WorkoutFeedbackModal: React.FC<WorkoutFeedbackModalProps> = ({
  visible,
  onClose,
  workoutId,
  workoutTitle,
}) => {
  const insets = useSafeAreaInsets();
  const [intensity, setIntensity] = useState(5);
  const [completion, setCompletion] = useState(100);
  const [difficulty, setDifficulty] = useState<'too_easy' | 'just_right' | 'too_hard'>('just_right');
  const [energy, setEnergy] = useState<'low' | 'moderate' | 'high'>('moderate');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await api.post(`/workouts/${workoutId}/feedback`, {
        workout_id: workoutId,
        intensity_rating: intensity,
        completion_percentage: completion,
        difficulty_feedback: difficulty,
        energy_level: energy,
        notes: notes || null,
      });
      onClose();
    } catch (error) {
      console.error('Error submitting feedback:', error);
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
            {/* Celebration */}
            <View style={styles.celebration}>
              <View style={styles.celebrationIcon}>
                <Ionicons name="trophy" size={48} color={colors.textPrimary} />
              </View>
              <Text style={styles.celebrationTitle}>Great Work!</Text>
              <Text style={styles.celebrationSubtitle}>{workoutTitle}</Text>
            </View>

            {/* Intensity Rating */}
            <GlassCard style={styles.section}>
              <Text style={styles.sectionTitle}>How intense was the workout?</Text>
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
              <Text style={styles.intensityValue}>{intensity}/10</Text>
            </GlassCard>

            {/* Completion */}
            <GlassCard style={styles.section}>
              <Text style={styles.sectionTitle}>How much did you complete?</Text>
              <View style={styles.completionOptions}>
                {[25, 50, 75, 100].map((pct) => (
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
            </GlassCard>

            {/* Difficulty */}
            <GlassCard style={styles.section}>
              <Text style={styles.sectionTitle}>How was the difficulty?</Text>
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
            </GlassCard>

            {/* Energy Level */}
            <GlassCard style={styles.section}>
              <Text style={styles.sectionTitle}>Energy level after workout?</Text>
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
            </GlassCard>

            {/* Notes */}
            <GlassCard style={styles.section}>
              <Text style={styles.sectionTitle}>Any notes? (Optional)</Text>
              <TextInput
                style={styles.notesInput}
                placeholder="How did you feel? Any exercises to adjust?"
                placeholderTextColor={colors.textTertiary}
                value={notes}
                onChangeText={setNotes}
                multiline
                numberOfLines={3}
              />
            </GlassCard>

            {/* AI Learning Note */}
            <View style={styles.aiNote}>
              <Ionicons name="sparkles" size={16} color={colors.textTertiary} />
              <Text style={styles.aiNoteText}>
                Your feedback helps SFTC AI personalize future workouts
              </Text>
            </View>
          </ScrollView>

          {/* Submit Button */}
          <View style={styles.footer}>
            <Button
              title="Submit Feedback"
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
    marginBottom: spacing.xxl,
  },
  celebrationIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
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
  intensityValue: {
    ...typography.h4,
    color: colors.textPrimary,
    textAlign: 'center',
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

import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import {
  CoachBottom,
  CoachCard,
  CoachNote,
  CoachProgress,
  CoachSection,
  coachColors,
  coachLayout,
} from '../../src/components/onboarding/CoachOnboarding';
import { colors, spacing } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const TESTS = [
  { key: 'pushups', label: 'Push-ups', unit: 'reps', icon: 'fitness-outline' as const, placeholder: '0', description: 'One clean set.' },
  { key: 'pullups', label: 'Pull-ups', unit: 'reps', icon: 'arrow-up-outline' as const, placeholder: '0', description: 'Chin-ups count too.' },
  { key: 'squats', label: 'Squats', unit: 'reps', icon: 'body-outline' as const, placeholder: '0', description: 'Continuous reps.' },
  { key: 'plank', label: 'Plank', unit: 'sec', icon: 'timer-outline' as const, placeholder: '0', description: 'Best clean hold.' },
];

const parseRunPaceSeconds = (value: string): number | null => {
  const clean = value.toLowerCase().replace('/km', '').replace('min/km', '').trim();
  if (!clean) return null;
  if (clean.includes(':')) {
    const [minutes, seconds] = clean.split(':');
    const total = Number(minutes) * 60 + Number(seconds);
    return Number.isFinite(total) ? Math.round(total) : null;
  }
  const minutes = Number(clean);
  return Number.isFinite(minutes) ? Math.round(minutes * 60) : null;
};

export default function AssessmentScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { experience, setFitnessAssessment, fitnessAssessment } = useOnboardingStore();
  const [pushups, setPushups] = useState(fitnessAssessment.pushups?.toString() || '');
  const [pullups, setPullups] = useState(fitnessAssessment.pullups?.toString() || '');
  const [squats, setSquats] = useState(fitnessAssessment.squats?.toString() || '');
  const [plank, setPlank] = useState(fitnessAssessment.plank_seconds?.toString() || '');
  const [runPace, setRunPace] = useState(
    fitnessAssessment.run_pace_seconds_per_km
      ? `${Math.floor(fitnessAssessment.run_pace_seconds_per_km / 60)}:${String(fitnessAssessment.run_pace_seconds_per_km % 60).padStart(2, '0')}`
      : ''
  );
  const isBeginner = experience === 'beginner';
  const values = { pushups, pullups, squats, plank };
  const setters = { setPushups, setPullups, setSquats, setPlank };

  const handleNext = () => {
    setFitnessAssessment({
      pushups: parseInt(pushups, 10) || 0,
      pullups: parseInt(pullups, 10) || 0,
      squats: parseInt(squats, 10) || 0,
      plank_seconds: parseInt(plank, 10) || 0,
      run_pace_seconds_per_km: parseRunPaceSeconds(runPace),
    });
    router.push('/onboarding/generating');
  };

  const skipButton = isBeginner ? (
    <TouchableOpacity onPress={() => router.push('/onboarding/generating')} style={styles.skipButton}>
      <Text style={styles.skipText}>Skip for now</Text>
    </TouchableOpacity>
  ) : null;

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={8} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard
          icon="analytics"
          eyebrow="BASELINE CHECK"
          title="Calibrate your start point."
          subtitle={isBeginner ? 'These tests are optional. They help us start easier and progress with control.' : 'Use honest numbers. The plan adapts better when the baseline is real.'}
        >
          <CoachSection title="Quick tests" meta="Optional" />
          <View style={styles.testGrid}>
            {TESTS.map(test => {
              const setterName = `set${test.key.charAt(0).toUpperCase()}${test.key.slice(1)}` as keyof typeof setters;
              return (
                <View key={test.key} style={styles.testCard}>
                  <View style={styles.testHeader}>
                    <Ionicons name={test.icon} size={18} color={colors.textPrimary} />
                    <Text style={styles.testTitle}>{test.label}</Text>
                  </View>
                  <Text style={styles.testDescription}>{test.description}</Text>
                  <View style={styles.inputRow}>
                    <TextInput
                      style={styles.numberInput}
                      value={values[test.key as keyof typeof values]}
                      onChangeText={setters[setterName]}
                      placeholder={test.placeholder}
                      placeholderTextColor={colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={3}
                    />
                    <Text style={styles.unit}>{test.unit}</Text>
                  </View>
                </View>
              );
            })}
          </View>

          <CoachSection title="Running pace" meta="Optional" />
          <TextInput
            style={styles.paceInput}
            value={runPace}
            onChangeText={setRunPace}
            placeholder="6:30/km or 10:00/mile"
            placeholderTextColor={colors.textTertiary}
          />

          <CoachNote text="These numbers are only a starting signal. Daily feedback and activity will keep adjusting your plan." />
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext}>
        {skipButton}
      </CoachBottom>
    </View>
  );
}

const styles = StyleSheet.create({
  testGrid: {
    gap: 10,
  },
  testCard: {
    borderRadius: 18,
    backgroundColor: coachColors.control,
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  testHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    marginBottom: 6,
  },
  testTitle: {
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  testDescription: {
    fontSize: 12,
    lineHeight: 17,
    color: coachColors.muted,
    marginBottom: 11,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  numberInput: {
    width: 86,
    height: 48,
    borderRadius: 14,
    backgroundColor: colors.background,
    color: colors.textPrimary,
    fontSize: 17,
    fontWeight: '600',
    textAlign: 'center',
  },
  unit: {
    fontSize: 14,
    lineHeight: 19,
    fontWeight: '600',
    color: coachColors.muted,
  },
  paceInput: {
    minHeight: 52,
    borderRadius: 16,
    backgroundColor: coachColors.control,
    paddingHorizontal: 14,
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: '500',
  },
  skipButton: {
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  skipText: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '600',
    color: coachColors.muted,
  },
});

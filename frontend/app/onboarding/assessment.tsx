import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { CoachBottom, CoachCard, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { colors, spacing } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const LEVELS = [
  ['beginner', 'Beginner', 'New to structured training or returning after a long break.'],
  ['intermediate', 'Intermediate', 'You train consistently and can handle planned progression.'],
  ['advanced', 'Advanced', 'You have substantial training experience and tolerate higher complexity.'],
] as const;

export default function AssessmentScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { fitnessAssessment, setFitnessAssessment } = useOnboardingStore();
  const [level, setLevel] = useState(fitnessAssessment.level || 'intermediate');
  const handleNext = () => { setFitnessAssessment({ level }); router.push('/onboarding/generating'); };
  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={8} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard icon="analytics" eyebrow="TRAINING LEVEL" title="Where should we start?" subtitle="Choose the level that best describes your current strength and training experience.">
          <CoachSection title="Training level" />
          <View style={styles.list}>
            {LEVELS.map(([id, label, description]) => (
              <TouchableOpacity key={id} onPress={() => setLevel(id)} style={[styles.option, level === id && styles.selected]} activeOpacity={0.8}>
                <Ionicons name={level === id ? 'checkmark-circle' : 'ellipse-outline'} size={24} color={level === id ? colors.textPrimary : colors.textTertiary} />
                <View style={styles.copy}><Text style={styles.label}>{label}</Text><Text style={styles.description}>{description}</Text></View>
              </TouchableOpacity>
            ))}
          </View>
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.md },
  option: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md, padding: spacing.lg, borderWidth: 1, borderColor: colors.separatorDark, borderRadius: 18 },
  selected: { borderColor: colors.textPrimary, backgroundColor: colors.separator },
  copy: { flex: 1 },
  label: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
  description: { marginTop: spacing.xs, fontSize: 14, lineHeight: 20, color: colors.textSecondary },
});

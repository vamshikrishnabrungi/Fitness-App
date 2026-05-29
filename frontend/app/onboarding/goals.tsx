import React, { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';

type PrimaryGoal = {
  id: string;
  label: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
};

type SecondaryGoal = {
  id: string;
  label: string;
};

const PRIMARY_GOALS: PrimaryGoal[] = [
  {
    id: 'athletic',
    label: 'Perform better in sport',
    description: 'Strength, speed, power, and conditioning for your game.',
    icon: 'trophy-outline',
  },
  {
    id: 'muscle',
    label: 'Build muscle',
    description: 'Add lean size with progressive strength and hypertrophy work.',
    icon: 'fitness-outline',
  },
  {
    id: 'lose_weight',
    label: 'Lose fat',
    description: 'Improve body composition while keeping training performance high.',
    icon: 'flame-outline',
  },
  {
    id: 'strength',
    label: 'Get stronger',
    description: 'Build full-body strength and confidence under load.',
    icon: 'barbell-outline',
  },
  {
    id: 'endurance',
    label: 'Improve endurance',
    description: 'Run longer, recover faster, and handle more work.',
    icon: 'heart-outline',
  },
];

const SECONDARY_GOALS: SecondaryGoal[] = [
  { id: 'mobility', label: 'Mobility' },
  { id: 'conditioning', label: 'Conditioning' },
  { id: 'run_faster', label: 'Run faster' },
  { id: 'jump_higher', label: 'Jump higher' },
  { id: 'pain_free', label: 'Pain-free' },
  { id: 'athletic_physique', label: 'Athletic physique' },
  { id: 'return_from_injury', label: 'Return from injury' },
  { id: 'general', label: 'General fitness' },
];

const allGoalIds = new Set([
  ...PRIMARY_GOALS.map(goal => goal.id),
  ...SECONDARY_GOALS.map(goal => goal.id),
]);

export default function GoalsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setGoals, setSelectedGoals, setPrimaryGoal, goals, selectedGoals, primaryGoal } = useOnboardingStore();
  const initialGoals = selectedGoals.length > 0 ? selectedGoals : goals;
  const initialPrimary = primaryGoal || initialGoals.find(goal => PRIMARY_GOALS.some(item => item.id === goal)) || '';
  const [primary, setPrimary] = useState(initialPrimary);
  const [secondary, setSecondary] = useState<string[]>(
    initialGoals.filter(goal => goal !== initialPrimary && allGoalIds.has(goal))
  );

  const primaryDetails = useMemo(
    () => PRIMARY_GOALS.find(goal => goal.id === primary),
    [primary]
  );

  const toggleSecondary = (id: string) => {
    setSecondary(current =>
      current.includes(id) ? current.filter(goal => goal !== id) : [...current, id]
    );
  };

  const handleNext = () => {
    if (!primary) return;
    const nextGoals = [primary, ...secondary.filter(goal => goal !== primary)];
    setGoals(nextGoals);
    setSelectedGoals(nextGoals);
    setPrimaryGoal(primary);
    router.push('/onboarding/experience');
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.progressWrap}>
        <View style={styles.progressTrack}>
          <View style={styles.progressFill} />
        </View>
        <Text style={styles.progressText}>1 of 8</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.card}>
          <View style={styles.coachRow}>
            <View style={styles.coachMark}>
              <Ionicons name="flash" size={17} color={colors.background} />
            </View>
            <Text style={styles.eyebrow}>TRAINING PROFILE</Text>
          </View>

          <Text style={styles.title}>What are you training for first?</Text>
          <Text style={styles.subtitle}>
            Choose the outcome your first plan should prioritize. You can add supporting goals next.
          </Text>

          <View style={styles.primaryList}>
            {PRIMARY_GOALS.map(goal => (
              <PrimaryGoalRow
                key={goal.id}
                goal={goal}
                selected={primary === goal.id}
                onPress={() => setPrimary(goal.id)}
              />
            ))}
          </View>

          <View style={styles.divider} />

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Add secondary focus</Text>
            <Text style={styles.sectionMeta}>Optional</Text>
          </View>
          <View style={styles.secondaryGrid}>
            {SECONDARY_GOALS.map(goal => (
              <SecondaryGoalChip
                key={goal.id}
                goal={goal}
                selected={secondary.includes(goal.id)}
                onPress={() => toggleSecondary(goal.id)}
              />
            ))}
          </View>

          {primaryDetails ? (
            <View style={styles.insight}>
              <Text style={styles.insightLabel}>Coach note</Text>
              <Text style={styles.insightText}>
                Your plan will start with {primaryDetails.label.toLowerCase()} as the main signal.
              </Text>
            </View>
          ) : null}
        </View>
      </ScrollView>

      <View style={[styles.bottom, { paddingBottom: insets.bottom + spacing.lg }]}>
        <TouchableOpacity
          activeOpacity={0.82}
          disabled={!primary}
          style={[styles.continueButton, !primary && styles.continueButtonDisabled]}
          onPress={handleNext}
        >
          <Text style={[styles.continueText, !primary && styles.continueTextDisabled]}>
            Continue
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function PrimaryGoalRow({
  goal,
  selected,
  onPress,
}: {
  goal: PrimaryGoal;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.86}
      onPress={onPress}
      style={[styles.primaryRow, selected && styles.primaryRowSelected]}
    >
      <View style={[styles.primaryIcon, selected && styles.primaryIconSelected]}>
        <Ionicons name={goal.icon} size={20} color={selected ? colors.background : colors.textPrimary} />
      </View>
      <View style={styles.primaryCopy}>
        <Text style={[styles.primaryTitle, selected && styles.primaryTitleSelected]}>
          {goal.label}
        </Text>
        <Text style={[styles.primaryDescription, selected && styles.primaryDescriptionSelected]}>
          {goal.description}
        </Text>
      </View>
      <View style={[styles.radio, selected && styles.radioSelected]}>
        {selected ? <View style={styles.radioDot} /> : null}
      </View>
    </TouchableOpacity>
  );
}

function SecondaryGoalChip({
  goal,
  selected,
  onPress,
}: {
  goal: SecondaryGoal;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.84}
      onPress={onPress}
      style={[styles.secondaryChip, selected && styles.secondaryChipSelected]}
    >
      <Text style={[styles.secondaryChipText, selected && styles.secondaryChipTextSelected]}>
        {goal.label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F4EF',
  },
  progressWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 18,
    paddingHorizontal: 26,
    paddingTop: 24,
    paddingBottom: 20,
  },
  progressTrack: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(17,17,17,0.08)',
  },
  progressFill: {
    width: '12.5%',
    height: '100%',
    borderRadius: 2,
    backgroundColor: colors.textPrimary,
  },
  progressText: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '700',
    color: '#8D8880',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 116,
  },
  card: {
    backgroundColor: colors.background,
    borderRadius: 24,
    paddingHorizontal: 22,
    paddingTop: 24,
    paddingBottom: 22,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.08,
    shadowRadius: 28,
    elevation: 4,
  },
  coachRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 18,
  },
  coachMark: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  eyebrow: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '800',
    letterSpacing: 0.8,
    color: '#8D8880',
  },
  title: {
    fontSize: 29,
    lineHeight: 35,
    fontWeight: '700',
    color: colors.textPrimary,
    letterSpacing: -0.2,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: '#756F67',
    marginBottom: 22,
  },
  primaryList: {
    gap: 10,
  },
  primaryRow: {
    minHeight: 82,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: 'transparent',
    backgroundColor: '#F3F2EF',
    paddingHorizontal: 14,
    paddingVertical: 13,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  primaryRowSelected: {
    backgroundColor: '#FBF7EF',
    borderWidth: 1.5,
    borderColor: colors.textPrimary,
  },
  primaryIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryIconSelected: {
    backgroundColor: colors.textPrimary,
  },
  primaryCopy: {
    flex: 1,
  },
  primaryTitle: {
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  primaryTitleSelected: {
    color: colors.textPrimary,
  },
  primaryDescription: {
    fontSize: 13,
    lineHeight: 19,
    color: '#756F67',
    marginTop: 3,
  },
  primaryDescriptionSelected: {
    color: '#625C54',
  },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: 'rgba(17,17,17,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: {
    borderColor: colors.textPrimary,
    backgroundColor: colors.textPrimary,
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.background,
  },
  divider: {
    height: 1,
    backgroundColor: '#EEECE8',
    marginVertical: 22,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  sectionMeta: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
    color: '#9A948B',
  },
  secondaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 9,
  },
  secondaryChip: {
    minHeight: 38,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: '#F3F2EF',
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryChipSelected: {
    backgroundColor: '#FBF7EF',
    borderColor: colors.textPrimary,
  },
  secondaryChipText: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  secondaryChipTextSelected: {
    color: colors.textPrimary,
  },
  insight: {
    borderRadius: 16,
    backgroundColor: '#F8F6F2',
    padding: 14,
    marginTop: 22,
  },
  insightLabel: {
    fontSize: 11,
    lineHeight: 15,
    fontWeight: '800',
    letterSpacing: 0.6,
    color: '#9A948B',
    textTransform: 'uppercase',
    marginBottom: 5,
  },
  insightText: {
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '600',
    color: '#5F5A52',
  },
  bottom: {
    paddingHorizontal: 26,
    paddingTop: 18,
    backgroundColor: '#F6F4EF',
  },
  continueButton: {
    height: 62,
    borderRadius: 999,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.12,
    shadowRadius: 18,
    elevation: 3,
  },
  continueButtonDisabled: {
    backgroundColor: '#A7A29A',
    shadowOpacity: 0,
    elevation: 0,
  },
  continueText: {
    fontSize: 18,
    lineHeight: 23,
    fontWeight: '800',
    color: colors.background,
  },
  continueTextDisabled: {
    color: 'rgba(255,255,255,0.72)',
  },
});

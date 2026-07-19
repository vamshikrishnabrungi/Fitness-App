import React, { useState, useEffect } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CoachBottom,
  CoachCard,
  CoachChip,
  CoachField,
  CoachProgress,
  CoachSection,
  coachLayout,
} from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { useAuthStore } from '../../src/store/authStore';

const GENDERS = [
  { id: 'female', label: 'Female' },
  { id: 'male', label: 'Male' },
  { id: 'non_binary', label: 'Non-binary' },
  { id: 'prefer_not_to_say', label: 'Prefer not to say' },
];

const LEVELS = ['recreational', 'school', 'college', 'club', 'state', 'pro'];
const PHASES = ['off_season', 'pre_season', 'in_season', 'general'];
const label = (value: string) => value.replaceAll('_', ' ');

export default function ProfileScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const { user } = useAuthStore();
  const [gender, setGender] = useState(store.gender);
  const [heightCm, setHeightCm] = useState(store.heightCm);
  const [weightKg, setWeightKg] = useState(store.weightKg);
  const [targetWeightKg, setTargetWeightKg] = useState(store.targetWeightKg);
  const [competitionLevel, setCompetitionLevel] = useState(store.competitionLevel);
  const [seasonPhase, setSeasonPhase] = useState(store.seasonPhase);

  // Date of birth is collected at registration; carry it through so onboarding doesn't overwrite it with an empty value.
  useEffect(() => {
    if (!store.dateOfBirth && user?.profile?.date_of_birth) {
      store.setBodyProfile({ dateOfBirth: user.profile.date_of_birth });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleNext = () => {
    store.setBodyProfile({ gender, heightCm, weightKg, targetWeightKg });
    store.setSportContext({
      competitionLevel,
      seasonPhase,
      sportDetails: store.sports.map(sport => ({ sport })),
    });
    router.push('/onboarding/schedule' as any);
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={4} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard
          icon="person"
          eyebrow="BODY CONTEXT"
          title="Tell us the basics."
          subtitle="These details help set realistic loading and nutrition targets."
        >
          <CoachSection title="Body profile" />
          <View style={coachLayout.chipGrid}>
            {GENDERS.map(item => (
              <CoachChip
                key={item.id}
                label={item.label}
                selected={gender === item.id}
                onPress={() => setGender(item.id)}
              />
            ))}
          </View>

          <View style={coachLayout.divider} />

          <CoachSection title="Stats" />
          <View style={coachLayout.fieldGrid}>
            <CoachField style={coachLayout.halfField} label="Height" value={heightCm} onChangeText={setHeightCm} placeholder="cm" keyboardType="decimal-pad" />
            <CoachField style={coachLayout.halfField} label="Weight" value={weightKg} onChangeText={setWeightKg} placeholder="kg" keyboardType="decimal-pad" />
            <CoachField style={coachLayout.halfField} label="Target" value={targetWeightKg} onChangeText={setTargetWeightKg} placeholder="kg" keyboardType="decimal-pad" />
          </View>

          <View style={coachLayout.divider} />

          <CoachSection title="Competition level" />
          <View style={coachLayout.chipGrid}>
            {LEVELS.map(level => (
              <CoachChip key={level} label={label(level)} selected={competitionLevel === level} onPress={() => setCompetitionLevel(level)} />
            ))}
          </View>

          <CoachSection title="Season phase" />
          <View style={coachLayout.chipGrid}>
            {PHASES.map(phase => (
              <CoachChip key={phase} label={label(phase)} selected={seasonPhase === phase} onPress={() => setSeasonPhase(phase)} />
            ))}
          </View>
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

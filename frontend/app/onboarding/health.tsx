import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const PAIN_AREAS = ['foot', 'achilles', 'ankle', 'shin', 'calf', 'knee', 'hamstring', 'hip', 'back'];
export default function HealthScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [painAreas, setPainAreas] = useState<string[]>(store.pain_areas);

  const togglePainArea = (area: string) => setPainAreas(current =>
    current.includes(area) ? current.filter(item => item !== area) : [...current, area]);
  const handleNext = () => {
    store.setHealth({ pain_areas: painAreas });
    router.push('/onboarding/generating');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={store.goal_type !== 'start_running' ? 5 : 4} total={store.goal_type !== 'start_running' ? 5 : 4} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard icon="shield-checkmark" eyebrow="RUNNING HEALTH" title="Are you training with any pain?" subtitle="Select any areas that currently affect your running. Leave this empty if you have no pain.">
          <CoachSection title="Current pain areas" meta="Optional" />
          <View style={coachLayout.chipGrid}>
            <CoachChip label="No current pain" selected={painAreas.length === 0} onPress={() => setPainAreas([])} />
            {PAIN_AREAS.map(area => <CoachChip key={area} label={area} selected={painAreas.includes(area)} onPress={() => togglePainArea(area)} />)}
          </View>
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

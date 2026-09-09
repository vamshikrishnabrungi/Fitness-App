import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachOption, CoachProgress, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { RUNNER_GOALS } from '../../src/data/running';
import { useOnboardingStore } from '../../src/store/onboardingStore';

export default function GoalsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [goal, setGoal] = useState(store.goal_type);

  const handleNext = () => {
    if (!goal) return;
    if (goal !== 'start_running') {
      store.setGoal({ goal_type: goal, target_event: null, target_distance: null, target_date: null, target_time: '', current_time: '' });
      router.push('/onboarding/race-details');
      return;
    }
    store.setGoal({ goal_type: goal, target_event: 'general_running', target_distance: null, target_date: null, target_time: '', current_time: '' });
    router.push('/onboarding/experience');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={1} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard icon="flag" eyebrow="YOUR GOAL" title="What are you running toward?" subtitle="Choose one focus for your first four-week block.">
          {RUNNER_GOALS.map(item => <CoachOption key={item.code} title={item.label} description={item.description} icon={item.icon} selected={goal === item.code} onPress={() => setGoal(item.code)} />)}
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} disabled={!goal} onPress={handleNext} />
    </View>
  );
}

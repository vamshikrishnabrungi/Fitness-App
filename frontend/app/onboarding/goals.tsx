import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachOption, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { RUNNER_GOALS } from '../../src/data/running';

export default function GoalsScreen() {
  const router = useRouter(); const insets = useSafeAreaInsets(); const store = useOnboardingStore();
  const [goal, setGoal] = useState(store.goal_type);
  const next = () => { if (!goal) return; store.setGoal({ goal_type: goal, target_event: goal === 'target_race' ? store.target_event : null }); router.push('/onboarding/sports'); };
  return <View style={[coachLayout.container,{paddingTop:insets.top}]}><CoachProgress step={1}/><ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content}>
    <CoachCard icon="flag" eyebrow="YOUR RUNNING GOAL" title="What are you running toward?" subtitle="We will shape your running, strength, mobility, and recovery around this goal.">
      <CoachSection title="Primary goal"/>{RUNNER_GOALS.map(item=><CoachOption key={item.code} title={item.label} description={item.description} icon="footsteps-outline" selected={goal===item.code} onPress={()=>setGoal(item.code)}/>) }
    </CoachCard></ScrollView><CoachBottom bottomInset={insets.bottom} disabled={!goal} onPress={next}/></View>;
}

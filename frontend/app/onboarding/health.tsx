import React, { useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachNote, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const PAIN_AREAS = ['foot', 'achilles', 'ankle', 'shin', 'calf', 'knee', 'hamstring', 'hip', 'back'];
const STRESS_LEVELS = ['low', 'moderate', 'high'];

export default function HealthScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [height, setHeight] = useState(store.height_cm);
  const [weight, setWeight] = useState(store.weight_kg);
  const [painAreas, setPainAreas] = useState<string[]>(store.pain_areas);
  const [medicalNotes, setMedicalNotes] = useState(store.medical_notes);
  const [stressLevel, setStressLevel] = useState(store.stress_level);

  const togglePainArea = (area: string) => setPainAreas(current =>
    current.includes(area) ? current.filter(item => item !== area) : [...current, area]);
  const handleNext = () => {
    store.setHealth({ height_cm: height, weight_kg: weight, pain_areas: painAreas, medical_notes: medicalNotes, stress_level: stressLevel });
    router.push('/onboarding/generating');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={store.goal_type === 'target_race' ? 5 : 4} total={store.goal_type === 'target_race' ? 5 : 4} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard icon="shield-checkmark" eyebrow="HEALTH AND RECOVERY" title="Anything we should account for?" subtitle="Optional body measurements and current health context help the coach choose safer training loads.">
          <CoachSection title="Body measurements" meta="Optional" />
          <View style={coachLayout.fieldGrid}>
            <CoachField style={coachLayout.halfField} label="Height (cm)" value={height} onChangeText={setHeight} placeholder="175" keyboardType="decimal-pad" />
            <CoachField style={coachLayout.halfField} label="Weight (kg)" value={weight} onChangeText={setWeight} placeholder="70" keyboardType="decimal-pad" />
          </View>
          <CoachSection title="Pain or injury areas" meta="Optional" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>{PAIN_AREAS.map(area => <CoachChip key={area} label={area} selected={painAreas.includes(area)} onPress={() => togglePainArea(area)} />)}</View>
          <CoachSection title="Restrictions or medical notes" meta="Optional" style={styles.sectionGap} />
          <CoachField value={medicalNotes} onChangeText={setMedicalNotes} placeholder="Old injuries, current restrictions, clinician advice..." multiline />
          <CoachSection title="Current stress" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>{STRESS_LEVELS.map(level => <CoachChip key={level} label={level} selected={stressLevel === level} onPress={() => setStressLevel(level)} />)}</View>
          <CoachNote text="This information helps adjust training. It does not replace advice from a qualified healthcare professional." />
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

const styles = StyleSheet.create({ sectionGap: { marginTop: 28 } });

import React, { useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CoachBottom,
  CoachCard,
  CoachChip,
  CoachField,
  CoachNote,
  CoachProgress,
  CoachSection,
  coachLayout,
} from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const PAIN_AREAS = ['foot', 'achilles', 'ankle', 'shin', 'calf', 'knee', 'hamstring', 'hip', 'back'];
const STRESS_LEVELS = ['low', 'moderate', 'high'];
const DIETS = ['balanced', 'vegetarian', 'vegan', 'eggetarian', 'high_protein'];
const NUTRITION_GOALS = ['performance', 'fat_loss', 'muscle_gain', 'maintenance'];

const label = (value: string) => value.replaceAll('_', ' ');

export default function HealthScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [painAreas, setPainAreas] = useState<string[]>(store.pain_areas);
  const [medicalNotes, setMedicalNotes] = useState(store.medical_notes);
  const [stressLevel, setStressLevel] = useState(store.stress_level);
  const [dietPreference, setDietPreference] = useState(store.diet_preference || 'balanced');
  const [nutritionGoal, setNutritionGoal] = useState(store.nutrition_goal || 'performance');

  const togglePainArea = (area: string) => {
    setPainAreas(current =>
      current.includes(area) ? current.filter(item => item !== area) : [...current, area]
    );
  };

  const handleNext = () => {
    store.setHealth({
      pain_areas: painAreas,
      medical_notes: medicalNotes,
      stress_level: stressLevel,
      diet_preference: dietPreference,
      nutrition_goal: nutritionGoal,
    });
    router.push('/onboarding/generating');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={7} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard
          icon="shield-checkmark"
          eyebrow="RECOVERY LIMITS"
          title="Anything we should protect?"
          subtitle="Recovery, pain, sleep, and nutrition help the coach scale training without unnecessary risk."
        >
          <CoachSection title="Pain or injury areas" meta="Optional" />
          <View style={coachLayout.chipGrid}>
            {PAIN_AREAS.map(area => (
              <CoachChip key={area} label={area} selected={painAreas.includes(area)} onPress={() => togglePainArea(area)} />
            ))}
          </View>

          <CoachSection title="Notes" meta="Optional" style={styles.sectionGap} />
          <CoachField
            value={medicalNotes}
            onChangeText={setMedicalNotes}
            placeholder="Restrictions, old injuries, doctor's advice..."
            multiline
          />

          <CoachNote text="This is not medical advice. It helps the app avoid risky progressions and adjust daily recommendations." />
        </CoachCard>

        <View style={styles.cardGap} />

        <CoachCard
          icon="battery-charging"
          eyebrow="DAILY READINESS"
          title="How are you recovering?"
          subtitle="Sleep, stress, and nutrition help scale daily intensity and recovery recommendations."
        >
          <CoachSection title="Stress level" />
          <View style={coachLayout.chipGrid}>
            {STRESS_LEVELS.map(level => (
              <CoachChip key={level} label={level} selected={stressLevel === level} onPress={() => setStressLevel(level)} />
            ))}
          </View>

          <View style={coachLayout.divider} />

          <CoachSection title="Diet" />
          <View style={coachLayout.chipGrid}>
            {DIETS.map(diet => (
              <CoachChip key={diet} label={label(diet)} selected={dietPreference === diet} onPress={() => setDietPreference(diet)} />
            ))}
          </View>

          <CoachSection title="Nutrition focus" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>
            {NUTRITION_GOALS.map(goal => (
              <CoachChip key={goal} label={label(goal)} selected={nutritionGoal === goal} onPress={() => setNutritionGoal(goal)} />
            ))}
          </View>
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

const styles = StyleSheet.create({
  cardGap: {
    height: 18,
  },
  sectionGap: {
    marginTop: 28,
  },
});

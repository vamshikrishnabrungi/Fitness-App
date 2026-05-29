import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
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

const GENDERS = [
  { id: 'female', label: 'Female' },
  { id: 'male', label: 'Male' },
  { id: 'non_binary', label: 'Non-binary' },
  { id: 'prefer_not_to_say', label: 'Prefer not to say' },
];

export default function ProfileScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [gender, setGender] = useState(store.gender);
  const [dateOfBirth, setDateOfBirth] = useState(store.dateOfBirth);
  const [heightCm, setHeightCm] = useState(store.heightCm);
  const [weightKg, setWeightKg] = useState(store.weightKg);
  const [targetWeightKg, setTargetWeightKg] = useState(store.targetWeightKg);
  const [country, setCountry] = useState(store.country);
  const [city, setCity] = useState(store.city);

  const handleNext = () => {
    store.setBodyProfile({ gender, dateOfBirth, heightCm, weightKg, targetWeightKg, country, city });
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
          subtitle="These details help set realistic loading, nutrition targets, and local run features."
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
            <CoachField style={coachLayout.halfField} label="Birth year" value={dateOfBirth} onChangeText={setDateOfBirth} placeholder="2001" keyboardType="number-pad" />
            <CoachField style={coachLayout.halfField} label="Height" value={heightCm} onChangeText={setHeightCm} placeholder="cm" keyboardType="decimal-pad" />
            <CoachField style={coachLayout.halfField} label="Weight" value={weightKg} onChangeText={setWeightKg} placeholder="kg" keyboardType="decimal-pad" />
            <CoachField style={coachLayout.halfField} label="Target" value={targetWeightKg} onChangeText={setTargetWeightKg} placeholder="kg" keyboardType="decimal-pad" />
          </View>

          <CoachSection title="Location" />
          <CoachField label="Country" value={country} onChangeText={setCountry} placeholder="India" />
          <CoachField label="City" value={city} onChangeText={setCity} placeholder="Hyderabad" />

          <CoachNote text="Location supports city leaderboards, route context, and weather-aware run coaching later." />
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

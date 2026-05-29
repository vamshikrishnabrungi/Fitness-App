import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CoachBottom,
  CoachCard,
  CoachChip,
  CoachNote,
  CoachOption,
  CoachProgress,
  CoachSection,
  coachLayout,
} from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const EQUIPMENT = [
  'Dumbbells', 'Barbell', 'Kettlebells', 'Pull-up Bar',
  'Resistance Bands', 'Bench', 'Squat Rack', 'Treadmill',
  'Bike', 'Rower', 'Jump Rope', 'None',
];

export default function EquipmentScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setEquipment, location, equipment } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(equipment.filter(item => item !== 'full_gym'));
  const isGym = location === 'gym';

  const toggleEquipment = (item: string) => {
    if (item === 'None') {
      setSelected(current => current.includes(item) ? [] : ['None']);
      return;
    }
    setSelected(current => {
      const withoutNone = current.filter(value => value !== 'None');
      return withoutNone.includes(item)
        ? withoutNone.filter(value => value !== item)
        : [...withoutNone, item];
    });
  };

  const handleNext = () => {
    setEquipment(isGym ? ['full_gym'] : selected);
    router.push('/onboarding/health' as any);
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={6} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard
          icon="barbell"
          eyebrow="TRAINING ACCESS"
          title={isGym ? 'Your gym is covered.' : 'What can you train with?'}
          subtitle={isGym ? 'We will build with full gym access and adjust exercise choices from there.' : 'Choose what you can use consistently. Practical access beats perfect equipment.'}
        >
          {isGym ? (
            <>
              <CoachSection title="Confirmed access" />
              <CoachOption
                title="Full gym access"
                description="Racks, benches, machines, cables, free weights, and cardio equipment."
                icon="barbell-outline"
                selected
                onPress={() => undefined}
              />
              <CoachNote text="Your plan can include full strength progressions, machines, and conditioning options." />
            </>
          ) : (
            <>
              <CoachSection title="Available equipment" meta={`${selected.length} selected`} />
              <View style={coachLayout.chipGrid}>
                {EQUIPMENT.map(item => (
                  <CoachChip
                    key={item}
                    label={item}
                    selected={selected.includes(item)}
                    onPress={() => toggleEquipment(item)}
                  />
                ))}
              </View>
              <CoachNote text="We will only prescribe exercises that match your available equipment and space." />
            </>
          )}
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} disabled={!isGym && selected.length === 0} onPress={handleNext} />
    </View>
  );
}

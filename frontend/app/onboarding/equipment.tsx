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
  { label: 'Dumbbells', code: 'dumbbells' },
  { label: 'Barbell', code: 'barbell' },
  { label: 'Kettlebells', code: 'kettlebell' },
  { label: 'Pull-up Bar', code: 'pull_up_bar' },
  { label: 'Resistance Bands', code: 'resistance_band' },
  { label: 'Bench', code: 'bench' },
  { label: 'Squat Rack', code: 'squat_rack' },
  { label: 'Treadmill', code: 'treadmill' },
  { label: 'Bike', code: 'cycle_ergometer' },
  { label: 'Rower', code: 'rowing_ergometer' },
  { label: 'Jump Rope', code: 'jump_rope' },
  { label: 'None / bodyweight', code: 'bodyweight' },
] as const;

const EQUIPMENT_CODES = new Map(EQUIPMENT.flatMap(item => [
  [item.code.toLowerCase(), item.code],
  [item.label.toLowerCase(), item.code],
]));

export default function EquipmentScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setEquipment, location, equipment } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(
    equipment
      .filter(item => item !== 'full_gym')
      .map(item => EQUIPMENT_CODES.get(item.toLowerCase()) ?? item),
  );
  const isGym = location === 'gym';

  const toggleEquipment = (code: string) => {
    if (code === 'bodyweight') {
      setSelected(current => current.includes(code) ? [] : ['bodyweight']);
      return;
    }
    setSelected(current => {
      const withoutBodyweightOnly = current.filter(value => value !== 'bodyweight');
      return withoutBodyweightOnly.includes(code)
        ? withoutBodyweightOnly.filter(value => value !== code)
        : [...withoutBodyweightOnly, code];
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
                    key={item.code}
                    label={item.label}
                    selected={selected.includes(item.code)}
                    onPress={() => toggleEquipment(item.code)}
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

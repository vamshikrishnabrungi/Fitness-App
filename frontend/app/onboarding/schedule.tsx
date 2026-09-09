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
  CoachOption,
  CoachProgress,
  CoachSection,
  coachLayout,
} from '../../src/components/onboarding/CoachOnboarding';
import { DayAvailability, useOnboardingStore } from '../../src/store/onboardingStore';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const TIMES = [90, 120, 150];
const TERRAINS = [['road', 'Road'], ['track', 'Track'], ['trail', 'Trail'], ['treadmill', 'Treadmill']];
const ACCESS = [
  ['full_gym', 'Full gym', 'Free weights, machines, and cardio equipment.'],
  ['home_equipment', 'Basic equipment', 'Choose the equipment you can use consistently.'],
  ['bodyweight', 'Bodyweight only', 'No resistance equipment required.'],
] as const;
const EQUIPMENT = [
  ['dumbbells', 'Dumbbells'], ['barbell', 'Barbell'], ['kettlebell', 'Kettlebells'],
  ['resistance_band', 'Bands'], ['bench', 'Bench'], ['squat_rack', 'Squat rack'],
  ['pull_up_bar', 'Pull-up bar'], ['jump_rope', 'Jump rope'],
];

export default function ScheduleScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [slots, setSlots] = useState<DayAvailability[]>(store.availability);
  const [notes, setNotes] = useState(store.schedule_constraints);
  const [terrains, setTerrains] = useState(store.terrains);
  const [access, setAccess] = useState(store.strength_access);
  const [equipment, setEquipment] = useState(store.equipment.filter(item => item !== 'bodyweight' && item !== 'full_gym'));

  const toggleDay = (day: string) => setSlots(current => current.some(slot => slot.day === day)
    ? current.filter(slot => slot.day !== day)
    : [...current, { day, minutes: 90, preferredTime: 'morning' }]);
  const updateDay = (day: string, change: Partial<DayAvailability>) => setSlots(current =>
    current.map(slot => slot.day === day ? { ...slot, ...change } : slot));
  const toggleValue = (value: string, setter: React.Dispatch<React.SetStateAction<string[]>>) =>
    setter(current => current.includes(value) ? current.filter(item => item !== value) : [...current, value]);

  const handleNext = () => {
    store.setScheduleAndAccess({
      availability: slots,
      schedule_constraints: notes,
      terrains,
      strength_access: access,
      equipment: access === 'full_gym' ? ['full_gym'] : access === 'bodyweight' ? ['bodyweight'] : equipment,
    });
    router.push('/onboarding/health');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={store.goal_type === 'target_race' ? 4 : 3} total={store.goal_type === 'target_race' ? 5 : 4} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard icon="calendar" eyebrow="YOUR TRAINING WEEK" title="When and where can you train?" subtitle="Choose your available days, session limits, running surfaces, and strength access.">
          <CoachSection title="Available days" meta={`${slots.length} selected`} />
          <View style={coachLayout.chipGrid}>{DAYS.map(day => <CoachChip key={day} label={day} selected={slots.some(slot => slot.day === day)} onPress={() => toggleDay(day)} />)}</View>
          {DAYS.filter(day => slots.some(slot => slot.day === day)).map(day => {
            const slot = slots.find(item => item.day === day)!;
            return <View key={day} style={styles.dayBlock}>
              <CoachSection title={day} meta={`${slot.minutes} min · ${slot.preferredTime}`} />
              <View style={coachLayout.chipGrid}>{TIMES.map(minutes => <CoachChip key={minutes} label={`${minutes} min`} selected={slot.minutes === minutes} onPress={() => updateDay(day, { minutes })} />)}</View>
              <View style={coachLayout.chipGrid}>{(['morning', 'afternoon', 'evening'] as const).map(time => <CoachChip key={time} label={time} selected={slot.preferredTime === time} onPress={() => updateDay(day, { preferredTime: time })} />)}</View>
            </View>;
          })}

          <CoachSection title="Running surfaces" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>{TERRAINS.map(([id, title]) => <CoachChip key={id} label={title} selected={terrains.includes(id)} onPress={() => toggleValue(id, setTerrains)} />)}</View>

          <CoachSection title="Strength access" style={styles.sectionGap} />
          {ACCESS.map(([id, title, description]) => <CoachOption key={id} title={title} description={description} icon="barbell-outline" selected={access === id} onPress={() => setAccess(id)} />)}
          {access === 'home_equipment' ? <>
            <CoachSection title="Available equipment" />
            <View style={coachLayout.chipGrid}>{EQUIPMENT.map(([id, title]) => <CoachChip key={id} label={title} selected={equipment.includes(id)} onPress={() => toggleValue(id, setEquipment)} />)}</View>
          </> : null}

          <CoachSection title="Schedule notes" meta="Optional" style={styles.sectionGap} />
          <CoachField value={notes} onChangeText={setNotes} placeholder="Work shifts, travel, unavailable dates..." multiline />
          <CoachNote text="The coach will fit running, recovery, and supporting strength within these limits." />
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} disabled={slots.length < 2 || !terrains.length || (access === 'home_equipment' && !equipment.length)} onPress={handleNext} />
    </View>
  );
}

const styles = StyleSheet.create({
  dayBlock: { marginTop: 8 },
  sectionGap: { marginTop: 28 },
});

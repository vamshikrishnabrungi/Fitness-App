import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachNote, CoachOption, CoachProgress, CoachSection, coachColors, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { DayAvailability, useOnboardingStore } from '../../src/store/onboardingStore';
import { colors } from '../../src/utils/theme';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const TIMES = [90, 120, 150];
const DEFAULT_DAYS = DAYS.slice(0, 5).map(day => ({ day, minutes: 90 }));
const TERRAINS = [['road', 'Road'], ['track', 'Track'], ['trail', 'Trail'], ['treadmill', 'Treadmill']];
const ACCESS = [
  ['full_gym', 'Full gym', 'Free weights, machines, and cardio equipment.'],
  ['home_equipment', 'Basic equipment', 'Choose the equipment you can use consistently.'],
  ['bodyweight', 'Bodyweight only', 'No resistance equipment required.'],
] as const;
const EQUIPMENT = [
  ['dumbbells', 'Dumbbells'], ['barbell', 'Barbell'], ['kettlebell', 'Kettlebells'], ['resistance_band', 'Bands'],
  ['bench', 'Bench'], ['squat_rack', 'Squat rack'], ['pull_up_bar', 'Pull-up bar'], ['jump_rope', 'Jump rope'],
];

export default function ScheduleScreen() {
  const router = useRouter(); const insets = useSafeAreaInsets(); const store = useOnboardingStore();
  const initialSlots = store.availability.length ? store.availability : DEFAULT_DAYS;
  const [slots, setSlots] = useState<DayAvailability[]>(initialSlots);
  const [sessionMinutes, setSessionMinutes] = useState(initialSlots[0]?.minutes || 90);
  const [notes, setNotes] = useState(store.schedule_constraints); const [terrains, setTerrains] = useState(store.terrains);
  const [access, setAccess] = useState(store.strength_access);
  const [equipment, setEquipment] = useState(store.equipment.filter(item => item !== 'bodyweight' && item !== 'full_gym'));

  const toggleDay = (day: string) => setSlots(current => current.some(slot => slot.day === day) ? current.filter(slot => slot.day !== day) : [...current, { day, minutes: sessionMinutes }]);
  const selectDuration = (minutes: number) => { setSessionMinutes(minutes); setSlots(current => current.map(slot => ({ ...slot, minutes }))); };
  const toggleValue = (value: string, setter: React.Dispatch<React.SetStateAction<string[]>>) => setter(current => current.includes(value) ? current.filter(item => item !== value) : [...current, value]);
  const handleNext = () => {
    store.setScheduleAndAccess({ availability: slots, schedule_constraints: notes, terrains, strength_access: access,
      equipment: access === 'full_gym' ? ['full_gym'] : access === 'bodyweight' ? ['bodyweight'] : equipment });
    router.push('/onboarding/health');
  };
  const missingDays = Math.max(0, 5 - slots.length);

  return <View style={[coachLayout.container, { paddingTop: insets.top }]}>
    <CoachProgress step={store.goal_type !== 'start_running' ? 4 : 3} total={store.goal_type !== 'start_running' ? 5 : 4} />
    <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
      <CoachCard icon="calendar" eyebrow="YOUR TRAINING WEEK" title="Build your weekly schedule." subtitle="Choose a minimum of 5 days and one maximum session length for the week.">
        <CoachSection title="Training days" meta={`${slots.length} of 7 selected`} />
        <View style={coachLayout.chipGrid}>{DAYS.map(day => <CoachChip key={day} label={day} selected={slots.some(slot => slot.day === day)} onPress={() => toggleDay(day)} />)}</View>
        <View style={[styles.selectionStatus, missingDays === 0 && styles.selectionComplete]}><Text style={[styles.selectionText, missingDays === 0 && styles.selectionCompleteText]}>{missingDays ? `Choose ${missingDays} more ${missingDays === 1 ? 'day' : 'days'} (minimum 5)` : 'Minimum 5 days selected'}</Text></View>

        <CoachSection title="Maximum time per session" meta="Applies to every day" style={styles.sectionGap} />
        <View style={styles.durationRow}>{TIMES.map(minutes => <CoachChip key={minutes} label={`${minutes} min`} selected={sessionMinutes === minutes} onPress={() => selectDuration(minutes)} style={styles.durationChip} />)}</View>
        <CoachNote label="Plan flexibility" text="Recovery runs may be shorter. This is the maximum time the coach can use for a session." />

        <CoachSection title="Running surfaces" style={styles.sectionGap} />
        <View style={coachLayout.chipGrid}>{TERRAINS.map(([id, title]) => <CoachChip key={id} label={title} selected={terrains.includes(id)} onPress={() => toggleValue(id, setTerrains)} />)}</View>

        <CoachSection title="Strength access" style={styles.sectionGap} />
        <View style={coachLayout.optionStack}>{ACCESS.map(([id, title, description]) => <CoachOption key={id} title={title} description={description} icon="barbell-outline" selected={access === id} onPress={() => setAccess(id)} />)}</View>
        {access === 'home_equipment' ? <View style={styles.sectionGap}><CoachSection title="Available equipment" /><View style={coachLayout.chipGrid}>{EQUIPMENT.map(([id, title]) => <CoachChip key={id} label={title} selected={equipment.includes(id)} onPress={() => toggleValue(id, setEquipment)} />)}</View></View> : null}

        <CoachSection title="Schedule notes" meta="Optional" style={styles.sectionGap} />
        <CoachField value={notes} onChangeText={setNotes} placeholder="Work shifts, travel, or unavailable dates..." multiline />
      </CoachCard>
    </ScrollView>
    <CoachBottom bottomInset={insets.bottom} disabled={slots.length < 5 || !terrains.length || (access === 'home_equipment' && !equipment.length)} onPress={handleNext} />
  </View>;
}

const styles = StyleSheet.create({
  sectionGap: { marginTop: 30 }, selectionStatus: { marginTop: 14, borderRadius: 12, backgroundColor: coachColors.control, paddingHorizontal: 14, paddingVertical: 10 },
  selectionComplete: { backgroundColor: colors.accentGreenLight }, selectionText: { color: colors.textSecondary, fontSize: 13, fontWeight: '600' }, selectionCompleteText: { color: colors.accentGreen },
  durationRow: { flexDirection: 'row', gap: 10 }, durationChip: { flex: 1 },
});

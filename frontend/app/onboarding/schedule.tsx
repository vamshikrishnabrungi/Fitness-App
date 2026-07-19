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

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DURATIONS = [30, 45, 60, 75];

// Local-date ISO (avoids UTC off-by-one near midnight).
const toISO = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const START_OPTIONS = Array.from({ length: 7 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() + i);
  const label = i === 0 ? 'Today' : i === 1 ? 'Tomorrow' : d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  return { iso: toISO(d), label };
});

export default function ScheduleScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [trainingDaysPerWeek, setTrainingDaysPerWeek] = useState(store.trainingDaysPerWeek);
  const [preferredTrainingDays, setPreferredTrainingDays] = useState<string[]>(store.preferredTrainingDays);
  const [sessionDurationMin, setSessionDurationMin] = useState(store.sessionDurationMin);
  const [scheduleConstraints, setScheduleConstraints] = useState(store.scheduleConstraints);
  const [startDate, setStartDate] = useState(store.startDate || START_OPTIONS[0].iso);

  const toggleDay = (day: string) => {
    setPreferredTrainingDays(current =>
      current.includes(day) ? current.filter(item => item !== day) : [...current, day]
    );
  };

  const handleNext = () => {
    store.setSchedule({
      trainingDaysPerWeek,
      preferredTrainingDays,
      sessionDurationMin,
      scheduleConstraints,
      startDate,
    });
    router.push('/onboarding/equipment');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={5} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard
          icon="calendar"
          eyebrow="TRAINING WEEK"
          title="Build your week."
          subtitle="Your program should fit the week you actually have, not a perfect week."
        >
          <CoachSection title="Days per week" />
          <View style={coachLayout.chipGrid}>
            {[3, 4, 5, 6].map(count => (
              <CoachChip key={count} label={`${count} days`} selected={trainingDaysPerWeek === count} onPress={() => setTrainingDaysPerWeek(count)} />
            ))}
          </View>

          <CoachSection title="Preferred days" meta="Optional" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>
            {DAYS.map(day => (
              <CoachChip key={day} label={day} selected={preferredTrainingDays.includes(day)} onPress={() => toggleDay(day)} />
            ))}
          </View>

          <View style={coachLayout.divider} />

          <CoachSection title="Session length" />
          <View style={coachLayout.chipGrid}>
            {DURATIONS.map(duration => (
              <CoachChip key={duration} label={`${duration} min`} selected={sessionDurationMin === duration} onPress={() => setSessionDurationMin(duration)} />
            ))}
          </View>

          <CoachSection title="Start date" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>
            {START_OPTIONS.map(option => (
              <CoachChip key={option.iso} label={option.label} selected={startDate === option.iso} onPress={() => setStartDate(option.iso)} />
            ))}
          </View>

          <CoachSection title="Constraints" meta="Optional" style={styles.sectionGap} />
          <CoachField
            value={scheduleConstraints}
            onChangeText={setScheduleConstraints}
            placeholder="Travel, school hours, match days, work shifts..."
            multiline
          />

          <CoachNote text="This helps the coach avoid impossible weeks and place harder sessions where they make sense." />
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} onPress={handleNext} />
    </View>
  );
}

const styles = StyleSheet.create({
  sectionGap: {
    marginTop: 28,
  },
});

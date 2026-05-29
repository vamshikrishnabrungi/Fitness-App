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
const TIMES = ['morning', 'afternoon', 'evening', 'flexible'];
const LEVELS = ['recreational', 'school', 'college', 'club', 'state', 'pro'];
const PHASES = ['off_season', 'pre_season', 'in_season', 'general'];

const label = (value: string) => value.replaceAll('_', ' ');

export default function ScheduleScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [trainingDaysPerWeek, setTrainingDaysPerWeek] = useState(store.trainingDaysPerWeek);
  const [preferredTrainingDays, setPreferredTrainingDays] = useState<string[]>(store.preferredTrainingDays);
  const [sessionDurationMin, setSessionDurationMin] = useState(store.sessionDurationMin);
  const [preferredTrainingTime, setPreferredTrainingTime] = useState(store.preferredTrainingTime);
  const [scheduleConstraints, setScheduleConstraints] = useState(store.scheduleConstraints);
  const [competitionLevel, setCompetitionLevel] = useState(store.competitionLevel);
  const [seasonPhase, setSeasonPhase] = useState(store.seasonPhase);

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
      preferredTrainingTime,
      scheduleConstraints,
    });
    store.setSportContext({
      competitionLevel,
      seasonPhase,
      sportDetails: store.sports.map(sport => ({ sport })),
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

          <CoachSection title="Training time" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>
            {TIMES.map(time => (
              <CoachChip key={time} label={label(time)} selected={preferredTrainingTime === time} onPress={() => setPreferredTrainingTime(time)} />
            ))}
          </View>

          <CoachNote text="This helps the coach avoid impossible weeks and place harder sessions where they make sense." />
        </CoachCard>

        <View style={styles.cardGap} />

        <CoachCard
          icon="trophy"
          eyebrow="SPORT SEASON"
          title="Where are you in your season?"
          subtitle="This helps balance performance work, recovery, and match or competition demands."
        >
          <CoachSection title="Sport context" />
          <View style={coachLayout.chipGrid}>
            {LEVELS.map(level => (
              <CoachChip key={level} label={label(level)} selected={competitionLevel === level} onPress={() => setCompetitionLevel(level)} />
            ))}
          </View>

          <CoachSection title="Season phase" style={styles.sectionGap} />
          <View style={coachLayout.chipGrid}>
            {PHASES.map(phase => (
              <CoachChip key={phase} label={label(phase)} selected={seasonPhase === phase} onPress={() => setSeasonPhase(phase)} />
            ))}
          </View>

          <CoachSection title="Constraints" meta="Optional" style={styles.sectionGap} />
          <CoachField
            value={scheduleConstraints}
            onChangeText={setScheduleConstraints}
            placeholder="Travel, school hours, match days, work shifts..."
            multiline
          />
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

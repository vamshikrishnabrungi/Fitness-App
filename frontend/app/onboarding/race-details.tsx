import React, { useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachProgress, CoachSection, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { DistanceUnit, useOnboardingStore } from '../../src/store/onboardingStore';

type RaceType = 'road' | 'track' | 'trail' | 'ultra';
const RACE_TYPES = [['road', 'Road'], ['track', 'Track'], ['trail', 'Trail'], ['ultra', 'Ultra']] as const;
const DISTANCES = {
  road: [['5k', '5K'], ['10k', '10K'], ['half_marathon', 'Half marathon'], ['marathon', 'Marathon']],
  track: [['100m', '100 m'], ['200m', '200 m'], ['400m', '400 m'], ['800m', '800 m'], ['1500m', '1500 m'], ['mile', 'Mile']],
} as const;
const typeForEvent = (event: string | null): RaceType | null => {
  if (event === 'trail' || event === 'ultra') return event;
  if (DISTANCES.track.some(([code]) => code === event)) return 'track';
  if (DISTANCES.road.some(([code]) => code === event)) return 'road';
  return null;
};

export default function RaceDetailsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [raceType, setRaceType] = useState<RaceType | null>(typeForEvent(store.target_event));
  const [event, setEvent] = useState(store.target_event || '');
  const [distance, setDistance] = useState(store.target_distance?.toString() || '');
  const [date, setDate] = useState(store.target_date || '');
  const [time, setTime] = useState(store.target_time);
  const [unit, setUnit] = useState<DistanceUnit>(store.distance_unit);
  const customDistance = raceType === 'trail' || raceType === 'ultra';
  const options = useMemo(() => raceType === 'road' || raceType === 'track' ? DISTANCES[raceType] : [], [raceType]);
  const canContinue = Boolean(raceType && event && (!customDistance || Number(distance) > 0));

  const chooseRaceType = (value: RaceType) => {
    setRaceType(value);
    setEvent(value === 'trail' || value === 'ultra' ? value : '');
    setDistance('');
  };
  const handleNext = () => {
    if (!canContinue) return;
    store.setGoal({
      goal_type: 'target_race', target_event: event, target_distance: customDistance ? Number(distance) : null,
      target_date: date || null, target_time: time, distance_unit: unit,
    });
    router.push('/onboarding/experience');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={2} total={5} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
        <CoachCard icon="trophy-outline" eyebrow="YOUR RACE" title="What are you training for?" subtitle="Your event and target help the coach balance speed, endurance, strength, and recovery.">
          <CoachSection title="Race type" />
          <View style={coachLayout.chipGrid}>{RACE_TYPES.map(([code, label]) => <CoachChip key={code} label={label} selected={raceType === code} onPress={() => chooseRaceType(code)} />)}</View>
          {options.length ? <><CoachSection title="Distance" /><View style={coachLayout.chipGrid}>{options.map(([code, label]) => <CoachChip key={code} label={label} selected={event === code} onPress={() => setEvent(code)} />)}</View></> : null}
          {customDistance ? <><CoachSection title="Race distance" /><CoachField value={distance} onChangeText={setDistance} placeholder={`Distance (${unit})`} keyboardType="decimal-pad" /><View style={coachLayout.chipGrid}><CoachChip label="km" selected={unit === 'km'} onPress={() => setUnit('km')} /><CoachChip label="mi" selected={unit === 'mi'} onPress={() => setUnit('mi')} /></View></> : null}
          {event ? <><CoachSection title="Race date" meta="Optional" /><CoachField value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" /><CoachSection title="Target time" meta="Optional" /><CoachField value={time} onChangeText={setTime} placeholder="HH:MM:SS" /></> : null}
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} disabled={!canContinue} onPress={handleNext} />
    </View>
  );
}

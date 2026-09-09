import React, { useMemo, useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CoachBottom,
  CoachCard,
  CoachChip,
  CoachField,
  CoachOption,
  CoachProgress,
  CoachSection,
  coachLayout,
} from '../../src/components/onboarding/CoachOnboarding';
import { useOnboardingStore } from '../../src/store/onboardingStore';

type RaceType = 'road' | 'track' | 'trail' | 'ultra';

const RACE_TYPES = [
  { code: 'road', title: 'Road race', description: '5K through marathon', icon: 'map-outline' },
  { code: 'track', title: 'Track race', description: 'Sprints and middle distance', icon: 'stopwatch-outline' },
  { code: 'trail', title: 'Trail race', description: 'Off-road distance and elevation', icon: 'trail-sign-outline' },
  { code: 'ultra', title: 'Ultra', description: 'Beyond marathon distance', icon: 'compass-outline' },
] as const;

const DISTANCES: Record<'road' | 'track', { code: string; label: string }[]> = {
  road: [
    { code: '5k', label: '5K' },
    { code: '10k', label: '10K' },
    { code: 'half_marathon', label: 'Half marathon' },
    { code: 'marathon', label: 'Marathon' },
  ],
  track: [
    { code: '100m', label: '100 m' },
    { code: '200m', label: '200 m' },
    { code: '400m', label: '400 m' },
    { code: '800m', label: '800 m' },
    { code: '1500m', label: '1500 m' },
    { code: 'mile', label: 'Mile' },
  ],
};

const raceTypeForEvent = (event: string | null): RaceType | null => {
  if (!event) return null;
  if (event === 'trail') return 'trail';
  if (event === 'ultra') return 'ultra';
  if (DISTANCES.track.some(item => item.code === event)) return 'track';
  if (DISTANCES.road.some(item => item.code === event)) return 'road';
  return null;
};

export default function RaceTargetScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [raceType, setRaceType] = useState<RaceType | null>(raceTypeForEvent(store.target_event));
  const [event, setEvent] = useState(store.target_event || '');
  const [distance, setDistance] = useState(store.target_distance?.toString() || '');
  const [date, setDate] = useState(store.target_date || '');
  const [time, setTime] = useState(store.target_time);
  const [unit, setUnit] = useState(store.distance_unit);
  const customDistance = raceType === 'trail' || raceType === 'ultra';
  const eventOptions = useMemo(() => raceType === 'road' || raceType === 'track' ? DISTANCES[raceType] : [], [raceType]);
  const canContinue = Boolean(raceType && event && (!customDistance || Number(distance) > 0));

  const chooseType = (value: RaceType) => {
    setRaceType(value);
    setEvent(value === 'trail' || value === 'ultra' ? value : '');
    if (value !== 'trail' && value !== 'ultra') setDistance('');
  };

  const next = () => {
    if (!canContinue) return;
    store.setGoal({
      target_event: event,
      target_distance: customDistance ? Number(distance) : null,
      target_date: date || null,
      target_time: time,
      distance_unit: unit,
    });
    router.push('/onboarding/experience');
  };

  return (
    <View style={[coachLayout.container, { paddingTop: insets.top }]}>
      <CoachProgress step={2} />
      <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content}>
        <CoachCard
          icon="flag"
          eyebrow="RACE GOAL"
          title="What race are you training for?"
          subtitle="Choose the race type first. We will only show the details that matter."
        >
          <CoachSection title="Race type" />
          {RACE_TYPES.map(item => (
            <CoachOption
              key={item.code}
              title={item.title}
              description={item.description}
              icon={item.icon}
              selected={raceType === item.code}
              onPress={() => chooseType(item.code)}
            />
          ))}

          {eventOptions.length > 0 ? (
            <>
              <CoachSection title="Distance" />
              <View style={coachLayout.chipGrid}>
                {eventOptions.map(item => (
                  <CoachChip key={item.code} label={item.label} selected={event === item.code} onPress={() => setEvent(item.code)} />
                ))}
              </View>
            </>
          ) : null}

          {customDistance ? (
            <>
              <CoachSection title="Race distance" />
              <View style={coachLayout.fieldGrid}>
                <CoachField style={coachLayout.halfField} value={distance} onChangeText={setDistance} placeholder="Distance" keyboardType="decimal-pad" />
                <View style={[coachLayout.halfField, coachLayout.chipGrid]}>
                  <CoachChip label="km" selected={unit === 'km'} onPress={() => setUnit('km')} />
                  <CoachChip label="mi" selected={unit === 'mi'} onPress={() => setUnit('mi')} />
                </View>
              </View>
            </>
          ) : null}

          {event ? (
            <>
              <CoachSection title="Race date" meta="Optional" />
              <CoachField value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" />
              <CoachSection title="Target time" meta="Optional" />
              <CoachField value={time} onChangeText={setTime} placeholder="HH:MM:SS" />
            </>
          ) : null}
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} disabled={!canContinue} onPress={next} />
    </View>
  );
}

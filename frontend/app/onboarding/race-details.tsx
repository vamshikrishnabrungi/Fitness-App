import React, { useMemo, useState } from 'react';
import { Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachProgress, CoachSection, coachColors, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { DistanceUnit, useOnboardingStore } from '../../src/store/onboardingStore';
import { colors } from '../../src/utils/theme';

type RaceType = 'road' | 'track' | 'trail';
type Duration = { hours: number; minutes: number; seconds: number; hundredths: number };
type DurationPart = keyof Duration;
const RACE_TYPES = [['road', 'Road'], ['track', 'Track'], ['trail', 'Trail']] as const;
const DISTANCES = {
  road: [['5k', '5K'], ['10k', '10K'], ['half_marathon', 'Half marathon'], ['marathon', 'Marathon']],
  track: [['100m', '100 m'], ['200m', '200 m'], ['400m', '400 m'], ['800m', '800 m'], ['1500m', '1500 m'], ['mile', 'Mile']],
} as const;
const RECORD_BOUNDS: Record<string, string> = {
  '100m': '00:00:09.58', '200m': '00:00:19.19', '400m': '00:00:43.03', '800m': '00:01:40.91',
  '1500m': '00:03:26.00', mile: '00:03:43.13', '5k': '00:12:49', '10k': '00:26:24',
  half_marathon: '00:57:20', marathon: '02:00:35',
};
const CURRENT_TIME_STARTS: Record<string, string> = {
  '100m': '00:00:15.00', '200m': '00:00:30.00', '400m': '00:01:00.00', '800m': '00:02:30.00',
  '1500m': '00:05:00.00', mile: '00:06:00.00', '5k': '00:30:00', '10k': '01:00:00',
  half_marathon: '02:00:00', marathon: '04:00:00', trail: '01:00:00',
};
const startOfToday = () => { const value = new Date(); value.setHours(0, 0, 0, 0); return value; };
const toLocalIsoDate = (value: Date) => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
const fromIsoDate = (value: string | null) => { if (!value) return null; const [year, month, day] = value.split('-').map(Number); const parsed = new Date(year, month - 1, day); return Number.isNaN(parsed.getTime()) ? null : parsed; };
const parseDuration = (value: string): Duration => {
  const [clock, fraction = '0'] = value.split('.'); const parts = clock.split(':').map(Number);
  if (parts.length !== 3 || parts.some(part => !Number.isFinite(part))) return { hours: 0, minutes: 0, seconds: 0, hundredths: 0 };
  return { hours: Math.min(parts[0], 99), minutes: Math.min(parts[1], 59), seconds: Math.min(parts[2], 59), hundredths: Math.min(Number(fraction.padEnd(2, '0').slice(0, 2)), 99) };
};
const secondsFor = (value: Duration) => value.hours * 3600 + value.minutes * 60 + value.seconds + value.hundredths / 100;
const serializeDuration = (value: Duration, precise: boolean) => `${String(value.hours).padStart(2, '0')}:${String(value.minutes).padStart(2, '0')}:${String(value.seconds).padStart(2, '0')}${precise ? `.${String(value.hundredths).padStart(2, '0')}` : ''}`;
const typeForEvent = (event: string | null): RaceType | null => {
  if (event === 'trail') return 'trail';
  if (DISTANCES.track.some(([code]) => code === event)) return 'track';
  if (DISTANCES.road.some(([code]) => code === event)) return 'road';
  return null;
};

function DurationStepper({ label, value, maximum, onChange }: { label: string; value: number; maximum: number; onChange: (value: number) => void }) {
  return <View style={styles.durationColumn}><Text style={styles.durationLabel}>{label}</Text><View style={styles.stepper}>
    <TouchableOpacity accessibilityLabel={`Decrease ${label}`} style={styles.stepButton} onPress={() => onChange(Math.max(0, value - 1))}><Text style={styles.stepSymbol}>−</Text></TouchableOpacity>
    <Text style={styles.durationValue}>{String(value).padStart(2, '0')}</Text>
    <TouchableOpacity accessibilityLabel={`Increase ${label}`} style={styles.stepButton} onPress={() => onChange(Math.min(maximum, value + 1))}><Text style={styles.stepSymbol}>+</Text></TouchableOpacity>
  </View></View>;
}

export default function RaceDetailsScreen() {
  const router = useRouter(); const insets = useSafeAreaInsets(); const store = useOnboardingStore();
  const goal = store.goal_type; const isRace = goal === 'target_race'; const collectsCurrentTime = isRace || goal === 'run_faster';
  const [raceType, setRaceType] = useState<RaceType | null>(typeForEvent(store.target_event));
  const [event, setEvent] = useState(store.target_event || ''); const [distance, setDistance] = useState(store.target_distance?.toString() || '');
  const [raceDate, setRaceDate] = useState<Date | null>(fromIsoDate(store.target_date)); const [showAndroidDatePicker, setShowAndroidDatePicker] = useState(false);
  const [currentTime, setCurrentTime] = useState(parseDuration(store.current_time)); const [hasCurrentTime, setHasCurrentTime] = useState(Boolean(store.current_time));
  const [unit, setUnit] = useState<DistanceUnit>(store.distance_unit);
  const customDistance = raceType === 'trail'; const preciseTime = raceType === 'track';
  const availableRaceTypes = goal === 'build_endurance' ? RACE_TYPES.filter(([code]) => code !== 'track') : RACE_TYPES;
  const options = useMemo(() => raceType === 'road' || raceType === 'track' ? DISTANCES[raceType] : [], [raceType]);
  const recordBound = RECORD_BOUNDS[event]; const currentSeconds = secondsFor(currentTime); const recordSeconds = recordBound ? secondsFor(parseDuration(recordBound)) : 0; const today = startOfToday();
  const validCurrentTime = !hasCurrentTime || (currentSeconds > 0 && (!recordBound || currentSeconds >= recordSeconds));
  const validDate = !isRace || Boolean(raceDate && raceDate >= today);
  const canContinue = Boolean(raceType && event && (!customDistance || (Number(distance) > 0 && Number(distance) <= 1000)) && validDate && validCurrentTime);

  const chooseRaceType = (value: RaceType) => { setRaceType(value); setEvent(value === 'trail' ? value : ''); setDistance(''); setHasCurrentTime(false); };
  const chooseEvent = (value: string) => { setEvent(value); setHasCurrentTime(false); };
  const updateDuration = (part: DurationPart, value: number) => setCurrentTime(current => ({ ...current, [part]: value }));
  const addCurrentTime = () => { setCurrentTime(parseDuration(CURRENT_TIME_STARTS[event] || '01:00:00')); setHasCurrentTime(true); };
  const handleNext = () => {
    if (!canContinue) return;
    store.setGoal({ goal_type: goal, target_event: event, target_distance: customDistance ? Number(distance) : null,
      target_date: isRace && raceDate ? toLocalIsoDate(raceDate) : null, target_time: '',
      current_time: collectsCurrentTime && hasCurrentTime ? serializeDuration(currentTime, preciseTime) : '', distance_unit: unit });
    router.push('/onboarding/experience');
  };

  return <View style={[coachLayout.container, { paddingTop: insets.top }]}><CoachProgress step={2} total={5} />
    <ScrollView style={coachLayout.scrollView} contentContainerStyle={coachLayout.content} showsVerticalScrollIndicator={false}>
      <CoachCard icon={isRace ? "trophy-outline" : goal === "run_faster" ? "speedometer-outline" : "trending-up-outline"} eyebrow={isRace ? "YOUR RACE" : goal === "run_faster" ? "SPEED FOCUS" : "DISTANCE FOCUS"} title={isRace ? "What are you racing?" : goal === "run_faster" ? "Where do you want to get faster?" : "How far do you want to run?"} subtitle={isRace ? "Choose the event and date so the coach can periodize your plan." : goal === "run_faster" ? "Choose the distance you want to improve. Your current best is optional." : "Choose the distance the coach should build you toward."}>
        <CoachSection title="Running type" /><View style={coachLayout.chipGrid}>{availableRaceTypes.map(([code, label]) => <CoachChip key={code} label={label} selected={raceType === code} onPress={() => chooseRaceType(code)} />)}</View>
        {options.length ? <View style={styles.sectionGap}><CoachSection title="Distance" /><View style={coachLayout.chipGrid}>{options.map(([code, label]) => <CoachChip key={code} label={label} selected={event === code} onPress={() => chooseEvent(code)} />)}</View></View> : null}
        {customDistance ? <View style={styles.sectionGap}><CoachSection title={isRace ? "Race distance" : "Goal distance"} /><CoachField value={distance} onChangeText={value => setDistance(value.replace(/[^0-9.]/g, ''))} placeholder={`Distance (${unit})`} keyboardType="decimal-pad" /><View style={[coachLayout.chipGrid, styles.controlGap]}><CoachChip label="km" selected={unit === 'km'} onPress={() => setUnit('km')} /><CoachChip label="mi" selected={unit === 'mi'} onPress={() => setUnit('mi')} /></View>{Number(distance) > 1000 ? <Text style={styles.errorText}>Enter a distance of 1,000 or less.</Text> : null}</View> : null}
        {event ? <>{isRace ? <View style={styles.sectionGap}><CoachSection title="Race date" meta="Required" />
          {raceDate ? <View style={styles.pickerRow}>{Platform.OS === 'android' ? <TouchableOpacity style={styles.valueButton} onPress={() => setShowAndroidDatePicker(true)}><Text style={styles.valueText}>{toLocalIsoDate(raceDate)}</Text></TouchableOpacity> : <DateTimePicker value={raceDate} mode="date" display="compact" minimumDate={today} onChange={(_, value) => value && setRaceDate(value)} />}<TouchableOpacity onPress={() => setRaceDate(null)}><Text style={styles.removeText}>Remove</Text></TouchableOpacity></View> : <TouchableOpacity style={styles.addButton} onPress={() => Platform.OS === 'android' ? setShowAndroidDatePicker(true) : setRaceDate(today)}><Text style={styles.addText}>+ Add race date</Text></TouchableOpacity>}
          <Text style={styles.todayText}>Today is {toLocalIsoDate(today)}. Past dates are unavailable.</Text>
          {showAndroidDatePicker ? <DateTimePicker value={raceDate || today} mode="date" minimumDate={today} onChange={(_, value) => { setShowAndroidDatePicker(false); if (value) setRaceDate(value); }} /> : null}</View> : null}
          {collectsCurrentTime ? <View style={styles.sectionGap}><CoachSection title="Your current best time" meta="Optional" />
            {hasCurrentTime ? <><View style={styles.durationRow}>{!preciseTime ? <DurationStepper label="Hours" value={currentTime.hours} maximum={99} onChange={value => updateDuration('hours', value)} /> : null}<DurationStepper label="Minutes" value={currentTime.minutes} maximum={59} onChange={value => updateDuration('minutes', value)} /><DurationStepper label="Seconds" value={currentTime.seconds} maximum={59} onChange={value => updateDuration('seconds', value)} />{preciseTime ? <DurationStepper label="1/100" value={currentTime.hundredths} maximum={99} onChange={value => updateDuration('hundredths', value)} /> : null}</View><TouchableOpacity onPress={() => setHasCurrentTime(false)}><Text style={styles.removeText}>Remove current time</Text></TouchableOpacity>{!validCurrentTime ? <Text style={styles.errorText}>Enter a valid current best time.</Text> : null}</> : <TouchableOpacity style={styles.addButton} onPress={addCurrentTime}><Text style={styles.addText}>+ Add current best time</Text></TouchableOpacity>}
          </View> : null}</> : null}
      </CoachCard></ScrollView><CoachBottom bottomInset={insets.bottom} disabled={!canContinue} onPress={handleNext} /></View>;
}

const styles = StyleSheet.create({
  sectionGap: { marginTop: 26 }, controlGap: { marginTop: 10 }, pickerRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  addButton: { minHeight: 52, borderRadius: 16, backgroundColor: coachColors.control, alignItems: 'center', justifyContent: 'center' }, addText: { color: colors.textPrimary, fontSize: 15, fontWeight: '600' },
  valueButton: { flex: 1, minHeight: 52, borderRadius: 16, backgroundColor: coachColors.control, justifyContent: 'center', paddingHorizontal: 16, marginRight: 16 }, valueText: { color: colors.textPrimary, fontSize: 16, fontWeight: '600' }, removeText: { color: colors.textSecondary, fontSize: 13, fontWeight: '600', marginTop: 10 },
  durationRow: { flexDirection: 'row', gap: 7 }, durationColumn: { flex: 1 }, durationLabel: { color: colors.textSecondary, fontSize: 10, fontWeight: '600', marginBottom: 7, textAlign: 'center' }, stepper: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: coachColors.control, borderRadius: 14, paddingHorizontal: 3 }, stepButton: { width: 25, height: 38, alignItems: 'center', justifyContent: 'center' }, stepSymbol: { color: colors.textPrimary, fontSize: 19 }, durationValue: { color: colors.textPrimary, fontSize: 14, fontWeight: '700' }, todayText: { color: colors.textTertiary, fontSize: 11, marginTop: 8 }, errorText: { color: colors.statusWarning, fontSize: 12, marginTop: 8 },
});

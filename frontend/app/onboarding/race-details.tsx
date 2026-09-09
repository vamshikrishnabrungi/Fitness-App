import React, { useMemo, useState } from 'react';
import { Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachBottom, CoachCard, CoachChip, CoachField, CoachProgress, CoachSection, coachColors, coachLayout } from '../../src/components/onboarding/CoachOnboarding';
import { colors } from '../../src/utils/theme';
import { DistanceUnit, useOnboardingStore } from '../../src/store/onboardingStore';

type RaceType = 'road' | 'track' | 'trail' | 'ultra';
type DurationPart = 'hours' | 'minutes' | 'seconds';
const RACE_TYPES = [['road', 'Road'], ['track', 'Track'], ['trail', 'Trail'], ['ultra', 'Ultra']] as const;
const DISTANCES = {
  road: [['5k', '5K'], ['10k', '10K'], ['half_marathon', 'Half marathon'], ['marathon', 'Marathon']],
  track: [['100m', '100 m'], ['200m', '200 m'], ['400m', '400 m'], ['800m', '800 m'], ['1500m', '1500 m'], ['mile', 'Mile']],
} as const;
const startOfToday = () => { const value = new Date(); value.setHours(0, 0, 0, 0); return value; };
const toLocalIsoDate = (value: Date) => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
const fromIsoDate = (value: string | null) => {
  if (!value) return null;
  const [year, month, day] = value.split('-').map(Number);
  const parsed = new Date(year, month - 1, day);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};
const parseDuration = (value: string) => {
  const parts = value.split(':').map(Number);
  if (parts.length !== 3 || parts.some(part => !Number.isInteger(part) || part < 0)) return { hours: 0, minutes: 0, seconds: 0 };
  return { hours: Math.min(parts[0], 99), minutes: Math.min(parts[1], 59), seconds: Math.min(parts[2], 59) };
};
const typeForEvent = (event: string | null): RaceType | null => {
  if (event === 'trail' || event === 'ultra') return event;
  if (DISTANCES.track.some(([code]) => code === event)) return 'track';
  if (DISTANCES.road.some(([code]) => code === event)) return 'road';
  return null;
};

function DurationStepper({ label, value, maximum, onChange }: { label: string; value: number; maximum: number; onChange: (value: number) => void }) {
  return <View style={styles.durationColumn}>
    <Text style={styles.durationLabel}>{label}</Text>
    <View style={styles.stepper}>
      <TouchableOpacity accessibilityLabel={`Decrease ${label}`} style={styles.stepButton} onPress={() => onChange(Math.max(0, value - 1))}><Text style={styles.stepSymbol}>−</Text></TouchableOpacity>
      <Text style={styles.durationValue}>{String(value).padStart(2, '0')}</Text>
      <TouchableOpacity accessibilityLabel={`Increase ${label}`} style={styles.stepButton} onPress={() => onChange(Math.min(maximum, value + 1))}><Text style={styles.stepSymbol}>+</Text></TouchableOpacity>
    </View>
  </View>;
}

export default function RaceDetailsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const store = useOnboardingStore();
  const [raceType, setRaceType] = useState<RaceType | null>(typeForEvent(store.target_event));
  const [event, setEvent] = useState(store.target_event || '');
  const [distance, setDistance] = useState(store.target_distance?.toString() || '');
  const [raceDate, setRaceDate] = useState<Date | null>(fromIsoDate(store.target_date));
  const [showAndroidDatePicker, setShowAndroidDatePicker] = useState(false);
  const [duration, setDuration] = useState(parseDuration(store.target_time));
  const [hasTargetTime, setHasTargetTime] = useState(Boolean(store.target_time));
  const [unit, setUnit] = useState<DistanceUnit>(store.distance_unit);
  const customDistance = raceType === 'trail' || raceType === 'ultra';
  const options = useMemo(() => raceType === 'road' || raceType === 'track' ? DISTANCES[raceType] : [], [raceType]);
  const targetSeconds = duration.hours * 3600 + duration.minutes * 60 + duration.seconds;
  const today = startOfToday();
  const canContinue = Boolean(raceType && event && (!customDistance || (Number(distance) > 0 && Number(distance) <= 1000)) && (!raceDate || raceDate >= today) && (!hasTargetTime || targetSeconds > 0));

  const chooseRaceType = (value: RaceType) => { setRaceType(value); setEvent(value === 'trail' || value === 'ultra' ? value : ''); setDistance(''); };
  const updateDuration = (part: DurationPart, value: number) => setDuration(current => ({ ...current, [part]: value }));
  const handleNext = () => {
    if (!canContinue) return;
    store.setGoal({
      goal_type: 'target_race', target_event: event, target_distance: customDistance ? Number(distance) : null,
      target_date: raceDate ? toLocalIsoDate(raceDate) : null,
      target_time: hasTargetTime ? `${String(duration.hours).padStart(2, '0')}:${String(duration.minutes).padStart(2, '0')}:${String(duration.seconds).padStart(2, '0')}` : '',
      distance_unit: unit,
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
          {options.length ? <View style={styles.sectionGap}><CoachSection title="Distance" /><View style={coachLayout.chipGrid}>{options.map(([code, label]) => <CoachChip key={code} label={label} selected={event === code} onPress={() => setEvent(code)} />)}</View></View> : null}
          {customDistance ? <View style={styles.sectionGap}><CoachSection title="Race distance" /><CoachField value={distance} onChangeText={value => setDistance(value.replace(/[^0-9.]/g, ''))} placeholder={`Distance (${unit})`} keyboardType="decimal-pad" /><View style={[coachLayout.chipGrid, styles.controlGap]}><CoachChip label="km" selected={unit === 'km'} onPress={() => setUnit('km')} /><CoachChip label="mi" selected={unit === 'mi'} onPress={() => setUnit('mi')} /></View>{Number(distance) > 1000 ? <Text style={styles.errorText}>Enter a distance of 1,000 or less.</Text> : null}</View> : null}
          {event ? <>
            <View style={styles.sectionGap}><CoachSection title="Race date" meta={`Today: ${toLocalIsoDate(today)}`} />
              {raceDate ? <View style={styles.pickerRow}>
                {Platform.OS === 'android' ? <TouchableOpacity style={styles.valueButton} onPress={() => setShowAndroidDatePicker(true)}><Text style={styles.valueText}>{toLocalIsoDate(raceDate)}</Text></TouchableOpacity> : <DateTimePicker value={raceDate} mode="date" display="compact" minimumDate={today} onChange={(_, value) => value && setRaceDate(value)} />}
                <TouchableOpacity onPress={() => setRaceDate(null)}><Text style={styles.removeText}>Remove</Text></TouchableOpacity>
              </View> : <TouchableOpacity style={styles.addButton} onPress={() => Platform.OS === 'android' ? setShowAndroidDatePicker(true) : setRaceDate(today)}><Text style={styles.addText}>+ Add race date</Text></TouchableOpacity>}
              {showAndroidDatePicker ? <DateTimePicker value={raceDate || today} mode="date" minimumDate={today} onChange={(_, value) => { setShowAndroidDatePicker(false); if (value) setRaceDate(value); }} /> : null}
            </View>
            <View style={styles.sectionGap}><CoachSection title="Target finish time" meta="Optional" />
              {hasTargetTime ? <><View style={styles.durationRow}><DurationStepper label="Hours" value={duration.hours} maximum={99} onChange={value => updateDuration('hours', value)} /><DurationStepper label="Minutes" value={duration.minutes} maximum={59} onChange={value => updateDuration('minutes', value)} /><DurationStepper label="Seconds" value={duration.seconds} maximum={59} onChange={value => updateDuration('seconds', value)} /></View><TouchableOpacity onPress={() => setHasTargetTime(false)}><Text style={styles.removeText}>Remove target time</Text></TouchableOpacity>{targetSeconds === 0 ? <Text style={styles.errorText}>Target time must be greater than zero.</Text> : null}</> : <TouchableOpacity style={styles.addButton} onPress={() => { setDuration({ hours: 1, minutes: 0, seconds: 0 }); setHasTargetTime(true); }}><Text style={styles.addText}>+ Add target finish time</Text></TouchableOpacity>}
            </View>
          </> : null}
        </CoachCard>
      </ScrollView>
      <CoachBottom bottomInset={insets.bottom} disabled={!canContinue} onPress={handleNext} />
    </View>
  );
}

const styles = StyleSheet.create({
  sectionGap: { marginTop: 26 }, controlGap: { marginTop: 10 }, pickerRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  addButton: { minHeight: 52, borderRadius: 16, backgroundColor: coachColors.control, alignItems: 'center', justifyContent: 'center' }, addText: { color: colors.textPrimary, fontSize: 15, fontWeight: '600' },
  valueButton: { flex: 1, minHeight: 52, borderRadius: 16, backgroundColor: coachColors.control, justifyContent: 'center', paddingHorizontal: 16, marginRight: 16 }, valueText: { color: colors.textPrimary, fontSize: 16, fontWeight: '600' },
  removeText: { color: colors.textSecondary, fontSize: 13, fontWeight: '600', marginTop: 10 }, durationRow: { flexDirection: 'row', gap: 8 }, durationColumn: { flex: 1 }, durationLabel: { color: colors.textSecondary, fontSize: 11, fontWeight: '600', marginBottom: 7, textAlign: 'center' },
  stepper: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: coachColors.control, borderRadius: 14, paddingHorizontal: 5 }, stepButton: { width: 28, height: 38, alignItems: 'center', justifyContent: 'center' }, stepSymbol: { color: colors.textPrimary, fontSize: 20 }, durationValue: { color: colors.textPrimary, fontSize: 15, fontWeight: '700' }, errorText: { color: colors.statusWarning, fontSize: 12, marginTop: 8 },
});

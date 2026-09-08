import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { api } from '../../src/utils/api';
import { colors, spacing, borderRadius } from '../../src/utils/theme';

// Key lifts we anchor load prescription to (estimated 1RM feeds %-based programming).
const LIFTS = [
  { exercise: 'Back Squat', hint: 'Heaviest clean set' },
  { exercise: 'Barbell Bench Press', hint: 'Heaviest clean set' },
  { exercise: 'Deadlift', hint: 'Heaviest clean set' },
  { exercise: 'Overhead Press', hint: 'Standing, strict' },
];

const num = (s: string): number | undefined => {
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : undefined;
};
const int = (s: string): number | undefined => {
  const n = parseInt(s, 10);
  return Number.isFinite(n) ? n : undefined;
};

// Epley estimate — display only; the server recomputes authoritatively.
const estimate1rm = (weight?: number, reps?: number): number | null => {
  if (!weight || !reps || weight <= 0 || reps <= 0) return null;
  if (reps === 1) return Math.round(weight);
  return Math.round(weight * (1 + reps / 30));
};

type LiftEntry = { weight: string; reps: string };

export default function BenchmarksScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const [lifts, setLifts] = useState<LiftEntry[]>(LIFTS.map(() => ({ weight: '', reps: '' })));
  const [cmj, setCmj] = useState('');
  const [broadJump, setBroadJump] = useState('');
  const [hopLeft, setHopLeft] = useState('');
  const [hopRight, setHopRight] = useState('');
  const [visaP, setVisaP] = useState('');
  const [visaA, setVisaA] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);

  const setLift = (idx: number, patch: Partial<LiftEntry>) =>
    setLifts((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));

  const lsi = useMemo(() => {
    const l = num(hopLeft);
    const r = num(hopRight);
    if (!l || !r || Math.max(l, r) <= 0) return null;
    return Math.round((100 * Math.min(l, r)) / Math.max(l, r));
  }, [hopLeft, hopRight]);

  const payloadLifts = useMemo(
    () =>
      LIFTS.map((lift, i) => ({
        exercise: lift.exercise,
        weight_kg: num(lifts[i].weight),
        reps: int(lifts[i].reps),
      })).filter((l) => l.weight_kg !== undefined && l.reps !== undefined),
    [lifts]
  );

  const hasAnything =
    payloadLifts.length > 0 ||
    [cmj, broadJump, hopLeft, hopRight, visaP, visaA].some((v) => num(v) !== undefined);

  const handleSave = async () => {
    if (!hasAnything) {
      Alert.alert('Add a measurement', 'Enter at least one lift or test result before saving.');
      return;
    }
    setSaving(true);
    try {
      const body: Record<string, unknown> = { lifts: payloadLifts };
      if (num(cmj) !== undefined) body.cmj_cm = num(cmj);
      if (num(broadJump) !== undefined) body.broad_jump_cm = num(broadJump);
      if (num(hopLeft) !== undefined) body.single_leg_hop_left_cm = num(hopLeft);
      if (num(hopRight) !== undefined) body.single_leg_hop_right_cm = num(hopRight);
      if (int(visaP) !== undefined) body.visa_p = int(visaP);
      if (int(visaA) !== undefined) body.visa_a = int(visaA);
      if (notes.trim()) body.notes = notes.trim();

      await api.post('/athletes/me/assessments', body);
      Alert.alert('Baselines saved', 'Your next plan will prescribe loads from your real numbers.', [
        { text: 'Done', onPress: () => router.back() },
      ]);
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to save baselines. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Baseline Testing</Text>
        <View style={styles.backButton} />
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={insets.top + 56}
      >
        <ScrollView
          contentContainerStyle={{ padding: spacing.lg, paddingBottom: insets.bottom + 120 }}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.intro}>
            Log a few test results so your coach prescribes loads from your real strength and gates
            return-to-running on objective symmetry rather than guesses. Re-test every few weeks.
          </Text>

          {/* Strength */}
          <Text style={styles.sectionTitle}>Strength (rep-max)</Text>
          <Text style={styles.sectionHint}>Enter the heaviest clean set you can do for each lift.</Text>
          {LIFTS.map((lift, i) => {
            const est = estimate1rm(num(lifts[i].weight), int(lifts[i].reps));
            return (
              <View key={lift.exercise} style={styles.card}>
                <View style={styles.cardHead}>
                  <Text style={styles.liftName}>{lift.exercise}</Text>
                  {est !== null ? <Text style={styles.estBadge}>≈ {est} kg 1RM</Text> : null}
                </View>
                <View style={styles.row}>
                  <View style={styles.field}>
                    <Text style={styles.fieldLabel}>Weight (kg)</Text>
                    <TextInput
                      style={styles.input}
                      value={lifts[i].weight}
                      onChangeText={(t) => setLift(i, { weight: t })}
                      keyboardType="numeric"
                      placeholder="0"
                      placeholderTextColor={colors.textTertiary}
                    />
                  </View>
                  <View style={styles.field}>
                    <Text style={styles.fieldLabel}>Reps</Text>
                    <TextInput
                      style={styles.input}
                      value={lifts[i].reps}
                      onChangeText={(t) => setLift(i, { reps: t })}
                      keyboardType="numeric"
                      placeholder="0"
                      placeholderTextColor={colors.textTertiary}
                    />
                  </View>
                </View>
              </View>
            );
          })}

          {/* Power */}
          <Text style={styles.sectionTitle}>Power</Text>
          <View style={styles.card}>
            <Metric label="Countermovement jump" unit="cm" value={cmj} onChange={setCmj} />
            <View style={styles.divider} />
            <Metric label="Broad jump" unit="cm" value={broadJump} onChange={setBroadJump} />
          </View>

          {/* Symmetry */}
          <Text style={styles.sectionTitle}>Single-leg hop (symmetry)</Text>
          <Text style={styles.sectionHint}>Hop as far as you can on each leg. LSI ≥ 90% clears jumping.</Text>
          <View style={styles.card}>
            <View style={styles.row}>
              <View style={styles.field}>
                <Text style={styles.fieldLabel}>Left (cm)</Text>
                <TextInput style={styles.input} value={hopLeft} onChangeText={setHopLeft} keyboardType="numeric" placeholder="0" placeholderTextColor={colors.textTertiary} />
              </View>
              <View style={styles.field}>
                <Text style={styles.fieldLabel}>Right (cm)</Text>
                <TextInput style={styles.input} value={hopRight} onChangeText={setHopRight} keyboardType="numeric" placeholder="0" placeholderTextColor={colors.textTertiary} />
              </View>
            </View>
            {lsi !== null ? (
              <Text style={[styles.lsi, { color: lsi >= 90 ? colors.accentGreen : colors.statusWarning }]}>
                Limb symmetry: {lsi}% {lsi >= 90 ? '· cleared for jumping' : '· below 90% gate'}
              </Text>
            ) : null}
          </View>

          {/* Tendon */}
          <Text style={styles.sectionTitle}>Tendon status (optional)</Text>
          <Text style={styles.sectionHint}>VISA questionnaire score 0–100 (only if you have tendon pain).</Text>
          <View style={styles.card}>
            <Metric label="VISA-P (patellar / knee)" unit="/100" value={visaP} onChange={setVisaP} />
            <View style={styles.divider} />
            <Metric label="VISA-A (achilles)" unit="/100" value={visaA} onChange={setVisaA} />
          </View>

          {/* Notes */}
          <Text style={styles.sectionTitle}>Notes</Text>
          <View style={styles.card}>
            <TextInput
              style={[styles.input, styles.notes]}
              value={notes}
              onChangeText={setNotes}
              placeholder="Anything relevant (pain, conditions, equipment)…"
              placeholderTextColor={colors.textTertiary}
              multiline
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + spacing.md }]}>
        <TouchableOpacity
          style={[styles.saveButton, (!hasAnything || saving) && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={!hasAnything || saving}
        >
          {saving ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.saveButtonText}>Save baselines</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

function Metric({
  label,
  unit,
  value,
  onChange,
}: {
  label: string;
  unit: string;
  value: string;
  onChange: (t: string) => void;
}) {
  return (
    <View style={styles.metricRow}>
      <Text style={styles.metricLabel}>{label}</Text>
      <View style={styles.metricInputWrap}>
        <TextInput
          style={styles.metricInput}
          value={value}
          onChangeText={onChange}
          keyboardType="numeric"
          placeholder="0"
          placeholderTextColor={colors.textTertiary}
        />
        <Text style={styles.metricUnit}>{unit}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.separator,
  },
  backButton: { width: 32, height: 32, justifyContent: 'center' },
  headerTitle: { fontSize: 17, fontWeight: '600', color: colors.textPrimary },
  intro: { fontSize: 13, lineHeight: 19, color: colors.textSecondary, marginBottom: spacing.lg },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: colors.textPrimary, marginTop: spacing.lg, marginBottom: 4 },
  sectionHint: { fontSize: 12, color: colors.textTertiary, marginBottom: spacing.sm },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.separatorDark,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  cardHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.sm },
  liftName: { fontSize: 15, fontWeight: '600', color: colors.textPrimary },
  estBadge: { fontSize: 12, fontWeight: '600', color: colors.accentGreen },
  row: { flexDirection: 'row', gap: spacing.md },
  field: { flex: 1 },
  fieldLabel: { fontSize: 12, color: colors.textSecondary, marginBottom: 4 },
  input: {
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.separatorDark,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 16,
    color: colors.textPrimary,
    backgroundColor: colors.surfaceSecondary,
  },
  notes: { minHeight: 72, textAlignVertical: 'top' },
  divider: { height: StyleSheet.hairlineWidth, backgroundColor: colors.separator, marginVertical: spacing.sm },
  metricRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  metricLabel: { flex: 1, fontSize: 14, color: colors.textPrimary },
  metricInputWrap: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metricInput: {
    minWidth: 72,
    textAlign: 'right',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.separatorDark,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 16,
    color: colors.textPrimary,
    backgroundColor: colors.surfaceSecondary,
  },
  metricUnit: { fontSize: 13, color: colors.textTertiary, width: 34 },
  lsi: { fontSize: 13, fontWeight: '600', marginTop: spacing.sm },
  footer: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
    backgroundColor: colors.background,
  },
  saveButton: {
    backgroundColor: colors.accent,
    borderRadius: borderRadius.lg,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveButtonDisabled: { opacity: 0.4 },
  saveButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
});

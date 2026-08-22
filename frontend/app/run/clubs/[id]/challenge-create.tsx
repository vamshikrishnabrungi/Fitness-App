import React, { useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../../../src/utils/api';
import { colors, spacing } from '../../../../src/utils/theme';

const METRICS = [
  ['distance', 'Distance (km)'],
  ['duration', 'Moving time (minutes)'],
  ['run_count', 'Run count'],
  ['consistency', 'Consistency (days)'],
  ['territory_gain', 'Territory gain (km)'],
] as const;

export default function ChallengeCreateScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [name, setName] = useState('');
  const [metric, setMetric] = useState<(typeof METRICS)[number][0]>('distance');
  const [target, setTarget] = useState('');
  const [days, setDays] = useState('28');
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try {
      const starts = new Date();
      const ends = new Date(starts.getTime() + Math.max(1, Number(days)) * 86_400_000);
      const enteredTarget = Number(target);
      if (!enteredTarget || enteredTarget <= 0) {
        Alert.alert('Target required', 'Enter a positive target for this challenge.');
        return;
      }
      const canonicalTarget = metric === 'distance' || metric === 'territory_gain'
        ? enteredTarget * 1000
        : metric === 'duration'
          ? enteredTarget * 60
          : enteredTarget;
      await api.post(`/clubs/${id}/challenges`, {
        name: name.trim(),
        challenge_type: metric,
        target: canonicalTarget,
        starts_at: starts.toISOString(),
        ends_at: ends.toISOString(),
      }, { 'Idempotency-Key': `challenge-${Date.now()}-${Math.random()}` });
      router.back();
    } catch (reason) {
      Alert.alert('Challenge not created', reason instanceof Error ? reason.message : 'Please try again.');
    } finally { setSaving(false); }
  };
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}><TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={24} color={colors.textPrimary} /></TouchableOpacity><Text style={styles.headerTitle}>Create challenge</Text><View style={{ width: 24 }} /></View>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Set one measurable team objective.</Text>
        <Text style={styles.label}>Name</Text><TextInput style={styles.input} value={name} onChangeText={setName} placeholder="28-day distance build" placeholderTextColor={colors.textTertiary} />
        <Text style={styles.label}>Metric</Text><View style={styles.chips}>{METRICS.map(([value, label]) => <TouchableOpacity key={value} style={[styles.chip, metric === value && styles.chipActive]} onPress={() => setMetric(value)}><Text style={[styles.chipText, metric === value && styles.chipTextActive]}>{label}</Text></TouchableOpacity>)}</View>
        <Text style={styles.label}>Target</Text><TextInput style={styles.input} value={target} onChangeText={setTarget} keyboardType="decimal-pad" placeholder="Required positive target" placeholderTextColor={colors.textTertiary} />
        <Text style={styles.label}>Duration in days</Text><TextInput style={styles.input} value={days} onChangeText={setDays} keyboardType="number-pad" />
        <TouchableOpacity style={styles.save} onPress={save} disabled={saving || !name.trim()}>{saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveText}>Publish challenge</Text>}</TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background }, header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.page }, headerTitle: { fontWeight: '900', color: colors.textPrimary }, content: { padding: spacing.page }, title: { fontSize: 28, lineHeight: 34, fontWeight: '900', color: colors.textPrimary, marginBottom: 12 }, label: { fontSize: 12, fontWeight: '900', color: colors.textPrimary, marginTop: 20, marginBottom: 8 }, input: { minHeight: 50, borderWidth: 1, borderColor: colors.separator, backgroundColor: colors.surface, color: colors.textPrimary, borderRadius: 15, paddingHorizontal: 14 }, chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 }, chip: { borderRadius: 12, borderWidth: 1, borderColor: colors.separator, paddingHorizontal: 12, paddingVertical: 10 }, chipActive: { backgroundColor: colors.textPrimary }, chipText: { color: colors.textSecondary, fontWeight: '800', fontSize: 10.5 }, chipTextActive: { color: '#fff' }, save: { minHeight: 54, borderRadius: 17, backgroundColor: colors.textPrimary, alignItems: 'center', justifyContent: 'center', marginTop: 30 }, saveText: { color: '#fff', fontWeight: '900' },
});

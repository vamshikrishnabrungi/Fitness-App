import React, { useCallback, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';
import { distanceFromKm, usePreferencesStore } from '../../src/store/preferencesStore';

interface ActivitySummary {
  id: string;
  title?: string | null;
  status: string;
  started_at: string;
  moving_seconds?: number | null;
  distance_m?: number | null;
  calories_kcal?: number | null;
  average_pace_s_per_km?: number | null;
}

const duration = (seconds: number) => `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
const pace = (seconds: number | null | undefined, unit: 'km' | 'mi') => {
  if (!seconds) return '—';
  const adjusted = unit === 'mi' ? seconds * 1.609344 : seconds;
  return `${Math.floor(adjusted / 60)}:${String(Math.round(adjusted % 60)).padStart(2, '0')} /${unit}`;
};

export default function LoadHistoryScreen() {
  const router = useRouter();
  const [items, setItems] = useState<ActivitySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const distanceUnit = usePreferencesStore(state => state.distanceUnit);

  const load = useCallback(async () => {
    try {
      setError(null);
      const page = await api.get<{ items: ActivitySummary[] }>('/activities?limit=100');
      setItems(page.items.filter((item) => item.status === 'complete'));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Activity history is unavailable.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { void load(); }, [load]));

  const todayCode = new Date().toDateString();
  const today = items.filter((item) => new Date(item.started_at).toDateString() === todayCode);
  const movingSeconds = today.reduce((sum, item) => sum + Number(item.moving_seconds || 0), 0);
  const distanceKm = today.reduce((sum, item) => sum + Number(item.distance_m || 0), 0) / 1000;
  const calories = today.reduce((sum, item) => sum + Number(item.calories_kcal || 0), 0);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.iconButton}><Ionicons name="chevron-back" size={23} color={colors.textPrimary} /></TouchableOpacity>
        <View style={{ flex: 1 }}><Text style={styles.title}>Activity load</Text><Text style={styles.subtitle}>Calculated only from processed activities</Text></View>
      </View>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(); }} />}
      >
        {loading ? <ActivityIndicator color={colors.brand} /> : error ? <View style={styles.empty}><Text style={styles.emptyTitle}>Unable to load activity</Text><Text style={styles.emptyBody}>{error}</Text></View> : (
          <>
            <View style={styles.grid}>
              <View style={styles.card}><Text style={styles.value}>{today.length}</Text><Text style={styles.label}>Activities today</Text></View>
              <View style={styles.card}><Text style={styles.value}>{distanceFromKm(distanceKm, distanceUnit).toFixed(2)}</Text><Text style={styles.label}>Distance ({distanceUnit})</Text></View>
              <View style={styles.card}><Text style={styles.value}>{Math.round(movingSeconds / 60)}</Text><Text style={styles.label}>Moving minutes</Text></View>
              <View style={styles.card}><Text style={styles.value}>{Math.round(calories)}</Text><Text style={styles.label}>Estimated kcal</Text></View>
            </View>
            <View style={styles.notice}><Ionicons name="information-circle-outline" size={19} color="#4569A3" /><Text style={styles.noticeText}>Runlete does not show a strain score until the calculation has enough validated inputs. Heart-rate zones and energy values are never fabricated.</Text></View>
            <Text style={styles.sectionTitle}>Recent processed activities</Text>
            {items.slice(0, 20).map((item) => (
              <TouchableOpacity key={item.id} style={styles.row} onPress={() => router.push(`/run/${item.id}`)}>
                <View style={{ flex: 1 }}><Text style={styles.rowTitle}>{item.title || 'Run'}</Text><Text style={styles.rowMeta}>{new Date(item.started_at).toLocaleString()}</Text></View>
                <View style={styles.rowStats}><Text style={styles.rowValue}>{distanceFromKm(Number(item.distance_m || 0) / 1000, distanceUnit).toFixed(2)} {distanceUnit}</Text><Text style={styles.rowMeta}>{duration(Number(item.moving_seconds || 0))} · {pace(item.average_pace_s_per_km, distanceUnit)}</Text></View>
              </TouchableOpacity>
            ))}
            {!items.length && <View style={styles.empty}><Ionicons name="walk-outline" size={34} color={colors.textTertiary} /><Text style={styles.emptyTitle}>No processed activities</Text><Text style={styles.emptyBody}>Completed runs will appear after server-side quality processing.</Text></View>}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: { flexDirection: 'row', gap: 12, alignItems: 'center', padding: spacing.page },
  iconButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  title: { color: colors.textPrimary, fontSize: 20, fontWeight: '900' },
  subtitle: { color: colors.textSecondary, fontSize: 10.5, marginTop: 2 },
  content: { padding: spacing.page, paddingTop: 4, paddingBottom: 50 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  card: { width: '48%', minHeight: 112, borderRadius: 18, backgroundColor: colors.surface, padding: 16, justifyContent: 'center' },
  value: { color: colors.textPrimary, fontSize: 28, fontWeight: '900' },
  label: { color: colors.textSecondary, fontSize: 10.5, marginTop: 6 },
  notice: { flexDirection: 'row', gap: 9, borderRadius: 16, padding: 14, marginTop: 16, backgroundColor: '#EDF3FF' },
  noticeText: { color: '#415474', flex: 1, fontSize: 11, lineHeight: 16 },
  sectionTitle: { color: colors.textPrimary, fontSize: 15, fontWeight: '900', marginTop: 28, marginBottom: 8 },
  row: { minHeight: 72, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.separator },
  rowTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 12.5 },
  rowMeta: { color: colors.textSecondary, fontSize: 9.5, marginTop: 4 },
  rowStats: { alignItems: 'flex-end' },
  rowValue: { color: colors.textPrimary, fontWeight: '900', fontSize: 12 },
  empty: { alignItems: 'center', padding: 30, borderRadius: 18, backgroundColor: colors.surface },
  emptyTitle: { color: colors.textPrimary, fontWeight: '900', marginTop: 8 },
  emptyBody: { color: colors.textSecondary, fontSize: 11, lineHeight: 16, textAlign: 'center', marginTop: 5 },
});

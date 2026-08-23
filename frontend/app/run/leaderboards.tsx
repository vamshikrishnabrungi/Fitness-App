import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api, ApiError } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

type Scope = 'global' | 'cities' | 'countries';
type Metric = 'distance' | 'duration' | 'runs';
type Period = 'week' | 'month' | 'all';

interface Row {
  rank: number;
  display_name: string;
  value: number;
  is_me?: boolean;
  emoji?: string;
  region_id?: string;
  country_code?: string;
  athlete_id?: string;
  club_id?: string;
}

const SCOPES: [Scope, string][] = [
  ['global', 'Solo'],
  ['cities', 'City vs City'],
  ['countries', 'Country'],
];
const METRICS: [Metric, string][] = [
  ['distance', 'Distance'],
  ['duration', 'Time'],
  ['runs', 'Runs'],
];
const PERIODS: [Period, string][] = [
  ['week', 'Week'],
  ['month', 'Month'],
  ['all', 'All'],
];

const formatValue = (value: number, metric: Metric) => {
  if (metric === 'distance') return `${(value / 1000).toFixed(1)} km`;
  if (metric === 'runs') return `${Math.round(value)}`;
  const total = Math.round(value);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m`;
};

const flag = (code?: string) =>
  code && code.length === 2
    ? String.fromCodePoint(...[...code.toUpperCase()].map((c) => 127397 + c.charCodeAt(0)))
    : '🏳️';

export default function LeaderboardsScreen() {
  const router = useRouter();
  const [scope, setScope] = useState<Scope>('global');
  const [metric, setMetric] = useState<Metric>('distance');
  const [period, setPeriod] = useState<Period>('week');
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState<{ id: string; name: string } | null>(null);
  const [citySubject, setCitySubject] = useState<'athlete' | 'club'>('athlete');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = `metric=${metric}&period=${period}`;
      let path: string;
      if (city) path = `/leaderboards/regions/${city.id}?subject=${citySubject}&${qs}`;
      else path = `/leaderboards/${scope}?${qs}`;
      const data = await api.get<{ items: Row[] }>(path);
      setRows(data.items || []);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : 'Leaderboard unavailable.');
    } finally {
      setLoading(false);
    }
  }, [scope, metric, period, city, citySubject]);

  useEffect(() => {
    void load();
  }, [load]);

  const onRowPress = (row: Row) => {
    if (scope === 'cities' && !city && row.region_id) {
      setCity({ id: row.region_id, name: row.display_name });
      setCitySubject('athlete');
    }
  };

  const subtitle = city
    ? `${city.name} · ${citySubject === 'club' ? 'clubs' : 'runners'}`
    : scope === 'global'
      ? 'Every runner, worldwide'
      : scope === 'cities'
        ? 'Cities ranked by their runners'
        : 'Countries ranked by their runners';

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.iconButton}
          onPress={() => (city ? setCity(null) : router.back())}
          testID="leaderboards-back"
        >
          <Ionicons name="chevron-back" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{city ? city.name : 'Leaderboards'}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
        <Ionicons name="trophy" size={22} color={colors.brand} />
      </View>

      {!city && (
        <View style={styles.scopes}>
          {SCOPES.map(([key, label]) => (
            <TouchableOpacity
              key={key}
              testID={`scope-${key}`}
              style={[styles.scopeTab, scope === key && styles.scopeTabActive]}
              onPress={() => setScope(key)}
            >
              <Text style={[styles.scopeText, scope === key && styles.scopeTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {city && (
        <View style={styles.subjectRow}>
          {(['athlete', 'club'] as const).map((s) => (
            <TouchableOpacity
              key={s}
              style={[styles.subjectChip, citySubject === s && styles.subjectChipActive]}
              onPress={() => setCitySubject(s)}
            >
              <Text style={[styles.subjectText, citySubject === s && styles.subjectTextActive]}>
                {s === 'club' ? 'Clubs' : 'Runners'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.filters}>
        <View style={styles.filterGroup}>
          {METRICS.map(([key, label]) => (
            <TouchableOpacity
              key={key}
              style={[styles.chip, metric === key && styles.chipActive]}
              onPress={() => setMetric(key)}
            >
              <Text style={[styles.chipText, metric === key && styles.chipTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        <View style={styles.filterGroup}>
          {PERIODS.map(([key, label]) => (
            <TouchableOpacity
              key={key}
              style={[styles.chipSmall, period === key && styles.chipActive]}
              onPress={() => setPeriod(key)}
            >
              <Text style={[styles.chipText, period === key && styles.chipTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {loading ? (
          <ActivityIndicator color={colors.brand} style={{ marginTop: 60 }} />
        ) : error ? (
          <View style={styles.empty}>
            <Ionicons name="cloud-offline-outline" size={34} color={colors.textTertiary} />
            <Text style={styles.emptyTitle}>Leaderboard unavailable</Text>
            <Text style={styles.emptyBody}>{error}</Text>
          </View>
        ) : !rows.length ? (
          <View style={styles.empty}>
            <Ionicons name="trophy-outline" size={34} color={colors.textTertiary} />
            <Text style={styles.emptyTitle}>No results yet</Text>
            <Text style={styles.emptyBody}>
              Verified runs appear here once they are attributed to a region.
            </Text>
          </View>
        ) : (
          rows.map((row) => {
            const isCity = scope === 'cities' && !city;
            const isCountry = scope === 'countries';
            const tappable = isCity;
            return (
              <TouchableOpacity
                key={`${row.rank}-${row.athlete_id || row.club_id || row.region_id || row.country_code || row.display_name}`}
                activeOpacity={tappable ? 0.7 : 1}
                disabled={!tappable}
                onPress={() => onRowPress(row)}
                style={[styles.row, row.is_me && styles.rowMe]}
                testID="leaderboard-row"
              >
                <Text style={styles.rank}>{row.rank}</Text>
                <View style={styles.mark}>
                  <Text style={styles.markText}>
                    {isCountry ? flag(row.country_code) : row.emoji || (row.display_name || 'R').slice(0, 1).toUpperCase()}
                  </Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.name} numberOfLines={1}>
                    {row.display_name || 'Unknown'}
                    {row.is_me ? ' · You' : ''}
                  </Text>
                  <Text style={styles.meta}>
                    {isCity ? 'Tap to see runners' : isCountry ? 'Country total' : citySubject === 'club' || row.club_id ? 'Club total' : 'Verified total'}
                  </Text>
                </View>
                <Text style={styles.value}>{formatValue(row.value, metric)}</Text>
                {tappable && <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />}
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: spacing.page,
    paddingVertical: 12,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { color: colors.textPrimary, fontSize: 22, fontWeight: '900' },
  subtitle: { color: colors.textSecondary, fontSize: 11.5, marginTop: 2 },
  scopes: { flexDirection: 'row', gap: 8, paddingHorizontal: spacing.page, paddingBottom: 10 },
  scopeTab: {
    flex: 1,
    height: 40,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: colors.separator,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scopeTabActive: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  scopeText: { color: colors.textSecondary, fontSize: 11.5, fontWeight: '900' },
  scopeTextActive: { color: '#FFFFFF' },
  subjectRow: { flexDirection: 'row', gap: 8, paddingHorizontal: spacing.page, paddingBottom: 10 },
  subjectChip: {
    paddingHorizontal: 16,
    height: 34,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: colors.separator,
    alignItems: 'center',
    justifyContent: 'center',
  },
  subjectChipActive: { backgroundColor: colors.brand, borderColor: colors.brand },
  subjectText: { color: colors.textSecondary, fontSize: 11, fontWeight: '900' },
  subjectTextActive: { color: '#FFFFFF' },
  filters: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.page,
    paddingBottom: 12,
    gap: 8,
  },
  filterGroup: { flexDirection: 'row', gap: 6 },
  chip: {
    paddingHorizontal: 12,
    height: 32,
    borderRadius: 10,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipSmall: {
    paddingHorizontal: 10,
    height: 32,
    borderRadius: 10,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipActive: { backgroundColor: colors.textPrimary },
  chipText: { color: colors.textSecondary, fontSize: 10.5, fontWeight: '900' },
  chipTextActive: { color: '#FFFFFF' },
  content: { paddingHorizontal: spacing.page, paddingBottom: 60 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 15,
    marginBottom: 7,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.separator,
  },
  rowMe: { borderColor: colors.brand, backgroundColor: '#FFF5EF' },
  rank: { width: 24, textAlign: 'center', color: colors.textTertiary, fontWeight: '900', fontSize: 13 },
  mark: {
    width: 40,
    height: 40,
    borderRadius: 13,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markText: { fontSize: 20, color: colors.textPrimary, fontWeight: '900' },
  name: { color: colors.textPrimary, fontWeight: '900', fontSize: 13 },
  meta: { color: colors.textSecondary, fontSize: 10, marginTop: 2 },
  value: { color: colors.textPrimary, fontWeight: '900', fontSize: 13 },
  empty: { alignItems: 'center', paddingVertical: 60, gap: 7 },
  emptyTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 16 },
  emptyBody: { color: colors.textSecondary, fontSize: 12, textAlign: 'center', maxWidth: 280 },
});

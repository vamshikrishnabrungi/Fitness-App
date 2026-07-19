import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Modal, Dimensions } from 'react-native';
import MapView, { Polyline } from 'react-native-maps';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../utils/api';
import { colors, spacing, borderRadius, typography } from '../utils/theme';

interface Corridor {
  id: string; name: string; value: number; length_km?: number; segment_count?: number;
  geometry?: number[][]; status: string;
  owner_name?: string | null; owner_emoji?: string | null;
  your_influence: number; rival_influence: number; meters_to_flip: number;
}
interface CorridorDetail extends Corridor {
  need_km: number; reward: { influence: number; segments: number };
  lead_runners: { name: string; km: number }[];
}
interface Mission {
  type: string; corridor_id: string; name: string; value: number; status: string;
  need_km: number; owner_name?: string | null; owner_emoji?: string | null; reward_influence: number;
}

const STATUS: Record<string, { label: string; color: string; verb: string }> = {
  strong:           { label: 'Yours',            color: colors.brand,    verb: 'Defend' },
  under_attack:     { label: 'Under attack',     color: '#DC2626',       verb: 'Defend' },
  easy_capture:     { label: 'Easy capture',     color: '#16A34A',       verb: 'Capture' },
  contested:        { label: 'Contested',        color: '#E0A21F',       verb: 'Capture' },
  enemy_stronghold: { label: 'Enemy stronghold', color: colors.accentBlue, verb: 'Attack' },
  neutral:          { label: 'Unclaimed',        color: '#9AA0AA',       verb: 'Claim' },
};
const lineColor = (s: string) =>
  s === 'strong' || s === 'under_attack' ? colors.brand : s === 'neutral' ? '#C2C3CB' : colors.accentBlue;

const { width } = Dimensions.get('window');
const MAP_W = width - spacing.page * 2;
const MAP_H = 260;
const DEFAULT_REGION = { latitude: 17.42, longitude: 78.47, latitudeDelta: 0.16, longitudeDelta: 0.16 };

// Fit the map to all corridor geometry, with padding so lines aren't flush to the edge.
function regionFor(corridors: Corridor[]) {
  const pts: number[][] = [];
  corridors.forEach((c) => (c.geometry || []).forEach((p) => pts.push(p)));
  if (!pts.length) return DEFAULT_REGION;
  const lats = pts.map((p) => p[0]), lngs = pts.map((p) => p[1]);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats), minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: Math.max(0.02, (maxLat - minLat) * 1.5),
    longitudeDelta: Math.max(0.02, (maxLng - minLng) * 1.5),
  };
}

type Filter = 'all' | 'under_attack' | 'easy_capture' | 'high';

export function TerritoryMap() {
  const router = useRouter();
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [mission, setMission] = useState<Mission | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>('all');
  const [selected, setSelected] = useState<CorridorDetail | null>(null);
  const [selId, setSelId] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      Promise.all([
        api.get<Corridor[]>('/territory/corridors').catch(() => [] as Corridor[]),
        api.get<{ mission: Mission | null }>('/territory/mission').catch(() => ({ mission: null })),
      ]).then(([cs, m]) => { setCorridors(cs || []); setMission(m?.mission ?? null); })
        .finally(() => setLoading(false));
    }, [])
  );

  const region = useMemo(() => regionFor(corridors), [corridors]);
  const filtered = useMemo(() => corridors.filter((c) => {
    if (filter === 'under_attack') return c.status === 'under_attack';
    if (filter === 'easy_capture') return c.status === 'easy_capture';
    if (filter === 'high') return c.value >= 4;
    return true;
  }), [corridors, filter]);

  const counts = useMemo(() => ({
    attack: corridors.filter((c) => c.status === 'under_attack').length,
    easy: corridors.filter((c) => c.status === 'easy_capture').length,
    yours: corridors.filter((c) => c.status === 'strong').length,
  }), [corridors]);

  const openById = useCallback(async (id: string) => {
    setSelId(id);
    const d = await api.get<CorridorDetail>(`/territory/corridors/${id}`).catch(() => null);
    if (d) setSelected(d);
  }, []);
  const openCorridor = useCallback((c: Corridor) => openById(c.id), [openById]);

  if (loading) return <ActivityIndicator size="large" color={colors.textPrimary} style={{ marginTop: 80 }} />;

  return (
    <View>
      {/* Today's mission */}
      {mission && (
        <View style={styles.mission}>
          <View style={styles.missionHalo} />
          <Text style={styles.missionLbl}>🎯 TODAY'S MISSION · {mission.type.toUpperCase()}</Text>
          <Text style={styles.missionTitle}>
            {mission.type} {mission.owner_emoji ? mission.owner_emoji + ' ' : ''}{mission.name}
          </Text>
          <Text style={styles.missionSub}>
            {mission.need_km > 0 ? `Run ${mission.need_km} km here to flip it` : 'Keep it yours — run it again'}
            {mission.owner_name ? ` · held by ${mission.owner_name}` : ''} · +{mission.reward_influence} influence
          </Text>
          <TouchableOpacity style={styles.missionBtn} onPress={() => openById(mission.corridor_id)}>
            <Ionicons name="play" size={15} color="#fff" />
            <Text style={styles.missionBtnText}>View & Start</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Territory map — real tiles (Apple Maps on iOS, Google on Android), corridors colored by control */}
      <View style={styles.mapCard}>
        <MapView
          style={{ width: MAP_W, height: MAP_H }}
          initialRegion={region}
          showsUserLocation
          showsCompass={false}
          showsPointsOfInterest={false}
          toolbarEnabled={false}
        >
          {corridors.map((c) => (
            c.geometry?.length ? (
              <Polyline
                key={c.id}
                coordinates={c.geometry.map((p) => ({ latitude: p[0], longitude: p[1] }))}
                strokeColor={lineColor(c.status)}
                strokeWidth={selId === c.id ? 7 : 4}
                tappable
                onPress={() => openCorridor(c)}
              />
            ) : null
          ))}
        </MapView>
        <View style={styles.legend}>
          <View style={styles.lgItem}><View style={[styles.lgDot, { backgroundColor: colors.brand }]} /><Text style={styles.lgTxt}>Yours</Text></View>
          <View style={styles.lgItem}><View style={[styles.lgDot, { backgroundColor: colors.accentBlue }]} /><Text style={styles.lgTxt}>Rival</Text></View>
          <View style={styles.lgItem}><View style={[styles.lgDot, { backgroundColor: '#C2C3CB' }]} /><Text style={styles.lgTxt}>Neutral</Text></View>
        </View>
      </View>

      {/* Filters */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
        {([['all', `All ${corridors.length}`], ['under_attack', `⚠ Under attack ${counts.attack}`], ['easy_capture', `🌱 Easy ${counts.easy}`], ['high', '👑 High value']] as [Filter, string][]).map(([k, l]) => (
          <TouchableOpacity key={k} style={StyleSheet.flatten([styles.filterChip, filter === k ? styles.filterChipOn : undefined])} onPress={() => setFilter(k)}>
            <Text style={StyleSheet.flatten([styles.filterTxt, filter === k ? styles.filterTxtOn : undefined])}>{l}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Corridor list */}
      {filtered.map((c) => {
        const st = STATUS[c.status] ?? STATUS.neutral;
        return (
          <TouchableOpacity key={c.id} activeOpacity={0.85} onPress={() => openCorridor(c)}>
            <View style={styles.row}>
              <View style={[styles.rowBar, { backgroundColor: lineColor(c.status) }]} />
              <View style={{ flex: 1 }}>
                <Text style={styles.rowName}>{c.name}</Text>
                <Text style={styles.rowMeta}>{'★'.repeat(c.value)}{c.owner_name ? ` · ${c.owner_emoji ?? ''}${c.owner_name}` : ' · unclaimed'}</Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={[styles.rowStatus, { color: st.color }]}>{st.label}</Text>
                {c.meters_to_flip > 0 && <Text style={styles.rowNeed}>need {(c.meters_to_flip / 1000).toFixed(1)} km</Text>}
              </View>
            </View>
          </TouchableOpacity>
        );
      })}

      {/* Corridor detail */}
      <Modal visible={!!selected} transparent animationType="slide" onRequestClose={() => setSelected(null)}>
        <View style={styles.scrim}>
          <View style={styles.sheet}>
            {selected && (
              <>
                <View style={styles.grab} />
                <Text style={styles.dName}>{selected.name}</Text>
                <View style={[styles.dPill, { backgroundColor: (STATUS[selected.status] ?? STATUS.neutral).color + '22' }]}>
                  <Text style={[styles.dPillTxt, { color: (STATUS[selected.status] ?? STATUS.neutral).color }]}>
                    {(STATUS[selected.status] ?? STATUS.neutral).label}
                    {selected.owner_name ? ` · ${selected.owner_emoji ?? ''}${selected.owner_name}` : ''}
                  </Text>
                </View>
                <Text style={styles.dSub}>
                  {selected.need_km > 0
                    ? `Run ${selected.need_km} km more here than them to take it.`
                    : 'You hold this — run it again before your influence decays.'}
                </Text>
                <View style={styles.dRewards}>
                  <View style={styles.dRw}><Text style={styles.dRwV}>+{selected.reward.influence}</Text><Text style={styles.dRwL}>influence</Text></View>
                  <View style={styles.dRw}><Text style={styles.dRwV}>{selected.segment_count}</Text><Text style={styles.dRwL}>segments</Text></View>
                  <View style={styles.dRw}><Text style={styles.dRwV}>{selected.length_km}</Text><Text style={styles.dRwL}>km loop</Text></View>
                </View>
                {selected.lead_runners.length > 0 && (
                  <View style={styles.dLead}>
                    <Text style={styles.dLeadTitle}>Top runners here</Text>
                    {selected.lead_runners.map((r, i) => (
                      <View key={i} style={styles.dLeadRow}>
                        <Text style={styles.dLeadRank}>{i + 1}</Text>
                        <Text style={styles.dLeadName}>{r.name}</Text>
                        <Text style={styles.dLeadKm}>{r.km} km</Text>
                      </View>
                    ))}
                  </View>
                )}
                <TouchableOpacity style={styles.startBtn} onPress={() => { setSelected(null); router.push('/run/track' as any); }}>
                  <LinearGradient colors={[colors.brand, colors.brand2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.startGrad}>
                    <Ionicons name="play" size={18} color="#fff" />
                    <Text style={styles.startTxt}>{(STATUS[selected.status] ?? STATUS.neutral).verb} · Start Run</Text>
                  </LinearGradient>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => setSelected(null)}><Text style={styles.dClose}>Close</Text></TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  mission: { backgroundColor: colors.featureCard, borderRadius: borderRadius.xxl, padding: spacing.lg, marginBottom: spacing.lg, overflow: 'hidden', position: 'relative' },
  missionHalo: { position: 'absolute', width: 180, height: 180, right: -60, top: -70, borderRadius: 90, backgroundColor: 'rgba(255,90,40,0.22)' },
  missionLbl: { fontSize: 10.5, fontWeight: '800', letterSpacing: 1.3, color: colors.brand2 },
  missionTitle: { fontSize: 21, fontWeight: '800', letterSpacing: -0.5, color: '#fff', marginTop: 6 },
  missionSub: { fontSize: 12.5, color: 'rgba(255,255,255,0.66)', marginTop: 5 },
  missionBtn: { flexDirection: 'row', alignItems: 'center', gap: 7, alignSelf: 'flex-start', marginTop: 14, backgroundColor: colors.brand, borderRadius: borderRadius.full, paddingHorizontal: spacing.lg, paddingVertical: 9 },
  missionBtnText: { color: '#fff', fontWeight: '800', fontSize: 13 },

  mapCard: { borderRadius: 20, overflow: 'hidden', marginBottom: spacing.lg, borderWidth: 1, borderColor: colors.separator, position: 'relative' },
  legend: { position: 'absolute', bottom: 10, left: 10, flexDirection: 'row', gap: 12, backgroundColor: 'rgba(255,255,255,0.92)', borderRadius: 10, paddingHorizontal: 10, paddingVertical: 6 },
  lgItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  lgDot: { width: 10, height: 4, borderRadius: 2 },
  lgTxt: { fontSize: 10.5, fontWeight: '700', color: colors.textSecondary },

  filters: { gap: 8, paddingBottom: spacing.md },
  filterChip: { backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.full, paddingHorizontal: spacing.md, paddingVertical: 8 },
  filterChipOn: { backgroundColor: colors.textPrimary },
  filterTxt: { ...typography.caption, fontWeight: '700', color: colors.textSecondary },
  filterTxtOn: { color: '#fff' },

  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.separator },
  rowBar: { width: 4, height: 38, borderRadius: 2 },
  rowName: { ...typography.bodySemibold, color: colors.textPrimary, fontWeight: '800' },
  rowMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 1 },
  rowStatus: { fontSize: 12, fontWeight: '800' },
  rowNeed: { fontSize: 11, color: colors.textTertiary, marginTop: 2 },

  scrim: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: colors.surface, borderTopLeftRadius: 26, borderTopRightRadius: 26, padding: spacing.lg, paddingBottom: spacing.xxl },
  grab: { width: 38, height: 4, borderRadius: 2, backgroundColor: '#DADADD', alignSelf: 'center', marginBottom: spacing.md },
  dName: { fontSize: 22, fontWeight: '800', letterSpacing: -0.5, color: colors.textPrimary },
  dPill: { alignSelf: 'flex-start', borderRadius: borderRadius.full, paddingHorizontal: 12, paddingVertical: 6, marginTop: 8 },
  dPillTxt: { fontSize: 12, fontWeight: '800' },
  dSub: { ...typography.caption, color: colors.textSecondary, marginTop: 12, lineHeight: 19 },
  dRewards: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg },
  dRw: { flex: 1, backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.md, paddingVertical: spacing.md, alignItems: 'center' },
  dRwV: { fontSize: 18, fontWeight: '800', color: colors.textPrimary },
  dRwL: { fontSize: 10.5, color: colors.textSecondary, marginTop: 2 },
  dLead: { marginTop: spacing.lg, gap: 6 },
  dLeadTitle: { ...typography.captionMedium, color: colors.textSecondary, marginBottom: 4 },
  dLeadRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  dLeadRank: { width: 18, fontSize: 13, fontWeight: '800', color: colors.textTertiary },
  dLeadName: { flex: 1, ...typography.captionMedium, color: colors.textPrimary },
  dLeadKm: { ...typography.captionMedium, color: colors.textSecondary },
  startBtn: { marginTop: spacing.lg, borderRadius: borderRadius.lg, overflow: 'hidden' },
  startGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14 },
  startTxt: { color: '#fff', fontWeight: '800', fontSize: 15 },
  dClose: { textAlign: 'center', color: colors.textSecondary, fontWeight: '700', marginTop: spacing.md, fontSize: 13 },
});

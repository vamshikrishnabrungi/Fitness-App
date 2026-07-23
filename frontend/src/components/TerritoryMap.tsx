import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Dimensions } from 'react-native';
import MapView, { Polyline, Marker } from 'react-native-maps';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../utils/api';
import { colors, spacing, borderRadius, typography } from '../utils/theme';

interface Road {
  id: string;
  path: number[][]; // [[lat, lng], ...]
  distance_km: number;
  date?: string | null;
}
interface MyTerritory {
  claimed_km: number;
  road_count: number;
  threshold_km: number;
  roads: Road[];
}

const { width } = Dimensions.get('window');
const MAP_W = width - spacing.page * 2;
const MAP_H = 300;
const DEFAULT_REGION = { latitude: 17.42, longitude: 78.47, latitudeDelta: 0.16, longitudeDelta: 0.16 };

// Fit the map to every claimed road, padded so lines aren't flush to the edge.
function regionFor(roads: Road[]) {
  const pts: number[][] = [];
  roads.forEach((r) => (r.path || []).forEach((p) => pts.push(p)));
  if (!pts.length) return DEFAULT_REGION;
  const lats = pts.map((p) => p[0]), lngs = pts.map((p) => p[1]);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats), minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: Math.max(0.01, (maxLat - minLat) * 1.6),
    longitudeDelta: Math.max(0.01, (maxLng - minLng) * 1.6),
  };
}

const fmtDate = (v?: string | null) => {
  if (!v) return '';
  const d = new Date(v);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

export function TerritoryMap() {
  const router = useRouter();
  const [data, setData] = useState<MyTerritory | null>(null);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      api.get<MyTerritory>('/territory/mine')
        .then((r) => setData(r))
        .catch(() => setData(null))
        .finally(() => setLoading(false));
    }, [])
  );

  const roads = data?.roads ?? [];
  const region = useMemo(() => regionFor(roads), [roads]);
  const threshold = data?.threshold_km ?? 2.5;

  const startRun = () => router.push('/run/track' as any);

  if (loading) return <ActivityIndicator size="large" color={colors.textPrimary} style={{ marginTop: 80 }} />;

  return (
    <View>
      {/* Header — how much road you hold */}
      <View style={styles.hero}>
        <View style={styles.heroHalo} />
        <Text style={styles.heroLbl}>YOUR TERRITORY</Text>
        <Text style={styles.heroNum}>
          {(data?.claimed_km ?? 0).toFixed(1)}<Text style={styles.heroUnit}> km of roads</Text>
        </Text>
        <Text style={styles.heroSub}>
          {data?.road_count ?? 0} {data?.road_count === 1 ? 'run claimed' : 'runs claimed'} · run {threshold} km+ to claim a road
        </Text>
      </View>

      {/* Map — the actual roads you've run */}
      <View style={styles.mapCard}>
        <MapView
          style={{ width: MAP_W, height: MAP_H }}
          initialRegion={region}
          showsUserLocation
          showsCompass={false}
          showsPointsOfInterest={false}
          toolbarEnabled={false}
        >
          {roads.map((r) => (
            r.path?.length >= 2 ? (
              <React.Fragment key={r.id}>
                <Polyline
                  coordinates={r.path.map((p) => ({ latitude: p[0], longitude: p[1] }))}
                  strokeColor={colors.brand}
                  strokeWidth={5}
                  lineCap="round"
                  lineJoin="round"
                />
                <Marker coordinate={{ latitude: r.path[0][0], longitude: r.path[0][1] }} anchor={{ x: 0.5, y: 0.5 }}>
                  <View style={styles.dot} />
                </Marker>
              </React.Fragment>
            ) : null
          ))}
        </MapView>
        {roads.length === 0 && (
          <View style={styles.emptyOverlay} pointerEvents="none">
            <Ionicons name="map-outline" size={30} color={colors.textTertiary} />
            <Text style={styles.emptyTitle}>No territory yet</Text>
            <Text style={styles.emptySub}>Run {threshold} km or more to claim your first road.</Text>
          </View>
        )}
      </View>

      {/* Start run — the only action */}
      <TouchableOpacity style={styles.startBtn} onPress={startRun} activeOpacity={0.9}>
        <LinearGradient colors={[colors.brand, colors.brand2]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.startGrad}>
          <Ionicons name="play" size={18} color="#fff" />
          <Text style={styles.startTxt}>Start a Run</Text>
        </LinearGradient>
      </TouchableOpacity>

      {/* Claimed roads list */}
      {roads.length > 0 && (
        <>
          <Text style={styles.listTitle}>Roads you hold</Text>
          {roads.map((r) => (
            <View key={r.id} style={styles.row}>
              <View style={styles.rowBar} />
              <View style={{ flex: 1 }}>
                <Text style={styles.rowName}>{r.distance_km.toFixed(2)} km run</Text>
                <Text style={styles.rowMeta}>{fmtDate(r.date) || 'Claimed'}</Text>
              </View>
              <Ionicons name="ribbon-outline" size={18} color={colors.brand} />
            </View>
          ))}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  hero: { backgroundColor: colors.featureCard, borderRadius: borderRadius.xxl, padding: spacing.lg, marginBottom: spacing.lg, overflow: 'hidden', position: 'relative' },
  heroHalo: { position: 'absolute', width: 180, height: 180, right: -60, top: -70, borderRadius: 90, backgroundColor: 'rgba(255,90,40,0.22)' },
  heroLbl: { fontSize: 10.5, fontWeight: '800', letterSpacing: 1.3, color: colors.brand2 },
  heroNum: { fontSize: 34, fontWeight: '800', letterSpacing: -0.8, color: '#fff', marginTop: 6 },
  heroUnit: { fontSize: 16, fontWeight: '600', color: 'rgba(255,255,255,0.7)' },
  heroSub: { fontSize: 12.5, color: 'rgba(255,255,255,0.66)', marginTop: 6 },

  mapCard: { borderRadius: 20, overflow: 'hidden', marginBottom: spacing.lg, borderWidth: 1, borderColor: colors.separator, position: 'relative', minHeight: MAP_H },
  emptyOverlay: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: 'rgba(241,241,238,0.55)' },
  emptyTitle: { ...typography.bodySemibold, color: colors.textPrimary, fontWeight: '800' },
  emptySub: { ...typography.caption, color: colors.textSecondary, textAlign: 'center', paddingHorizontal: spacing.xl },
  dot: { width: 12, height: 12, borderRadius: 6, backgroundColor: colors.brand, borderWidth: 2.5, borderColor: '#fff' },

  startBtn: { marginBottom: spacing.lg, borderRadius: borderRadius.lg, overflow: 'hidden' },
  startGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 15 },
  startTxt: { color: '#fff', fontWeight: '800', fontSize: 15 },

  listTitle: { ...typography.h4, color: colors.textPrimary, marginBottom: spacing.sm },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.separator },
  rowBar: { width: 4, height: 34, borderRadius: 2, backgroundColor: colors.brand },
  rowName: { ...typography.bodySemibold, color: colors.textPrimary, fontWeight: '800' },
  rowMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 1 },
});

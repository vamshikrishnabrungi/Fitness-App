import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Mapbox from '@rnmapbox/maps';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { api, ApiError } from '../utils/api';
import { borderRadius, colors, spacing, typography } from '../utils/theme';

const MAPBOX_TOKEN = process.env.EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN || '';
if (MAPBOX_TOKEN) Mapbox.setAccessToken(MAPBOX_TOKEN);

type Layer = 'me' | 'club' | 'competitors';

interface TileSession {
  tile_url: string;
  expires_at: string;
}

interface ClubSummary {
  id: string;
  name: string;
  emoji: string;
  is_primary: boolean;
}

interface TerritoryProperties {
  street_edge_id?: string;
  name?: string | null;
  distance_m?: number;
  score?: number;
  controlled_since?: string;
  expires_at?: string | number;
  controller_id?: string;
  my_score?: number;
  my_score_expires_at?: string;
  public_score?: number;
  public_expires_at?: string;
  primary_club_score?: number;
  primary_club_expires_at?: string;
  control_state?: 'controlled' | 'contested' | 'expiring';
  recent_history?: {
    id: string;
    event_type: string;
    occurred_at: string;
  }[];
}

interface TerritoryCollection {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    id?: string;
    properties: TerritoryProperties;
    geometry: { type: 'LineString'; coordinates: number[][] };
  }[];
  verified: boolean;
}

const DEFAULT_CENTER: [number, number] = [78.4867, 17.385];

const LAYERS: { key: Layer; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { key: 'me', label: 'Me', icon: 'person-outline' },
  { key: 'club', label: 'Primary club', icon: 'people-outline' },
  { key: 'competitors', label: 'Competitors', icon: 'trophy-outline' },
];

const lineColor: Record<Layer, string> = {
  me: '#FF5A36',
  club: '#32D6C0',
  competitors: '#8CA8FF',
};

const expirationLabel = (value?: string | number) => {
  if (!value) return 'Control window unavailable';
  const date = typeof value === 'number' ? new Date(value * 1000) : new Date(value);
  const days = Math.max(0, Math.ceil((date.getTime() - Date.now()) / 86_400_000));
  return days === 0 ? 'Expires today' : `${days} day${days === 1 ? '' : 's'} remaining`;
};

export function TerritoryMap() {
  const router = useRouter();
  const [layer, setLayer] = useState<Layer>('me');
  const [primaryClub, setPrimaryClub] = useState<ClubSummary | null>(null);
  const [tileSession, setTileSession] = useState<TileSession | null>(null);
  const [territory, setTerritory] = useState<TerritoryCollection | null>(null);
  const [selected, setSelected] = useState<TerritoryProperties | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPrimaryClub = useCallback(async () => {
    const page = await api.get<{ items: ClubSummary[] }>('/clubs/mine?limit=100');
    const primary = page.items.find((club) => club.is_primary) || null;
    setPrimaryClub(primary);
    return primary;
  }, []);

  const loadLayer = useCallback(
    async (nextLayer: Layer, knownPrimary?: ClubSummary | null) => {
      setLoading(true);
      setError(null);
      setSelected(null);
      try {
        const club = knownPrimary === undefined ? primaryClub : knownPrimary;
        if (nextLayer === 'club' && !club) {
          setTileSession(null);
          setTerritory(null);
          setError('Choose a primary competitive club to view club territory.');
          return;
        }
        const clubId = nextLayer === 'club' ? club?.id : undefined;
        const session = await api.post<TileSession>('/territory/tile-session', {
          layer: nextLayer,
          club_id: clubId,
        });
        setTileSession(session);
        if (nextLayer === 'me') {
          setTerritory(await api.get<TerritoryCollection>('/territory/mine'));
        } else if (nextLayer === 'club' && clubId) {
          setTerritory(await api.get<TerritoryCollection>(`/territory/club/${clubId}`));
        } else {
          setTerritory(null);
        }
      } catch (reason) {
        setTileSession(null);
        setTerritory(null);
        setError(
          reason instanceof ApiError
            ? reason.message
            : 'Territory could not be loaded. Pull to retry.',
        );
      } finally {
        setLoading(false);
      }
    },
    [primaryClub],
  );

  useFocusEffect(
    useCallback(() => {
      let active = true;
      loadPrimaryClub()
        .then((club) => {
          if (active) return loadLayer(layer, club);
        })
        .catch((reason) => {
          if (active) {
            setLoading(false);
            setError(reason instanceof Error ? reason.message : 'Club data could not be loaded.');
          }
        });
      return () => {
        active = false;
      };
    }, [layer, loadLayer, loadPrimaryClub]),
  );

  useEffect(() => {
    if (!tileSession) return;
    const refreshIn = Math.max(
      30_000,
      new Date(tileSession.expires_at).getTime() - Date.now() - 60_000,
    );
    const timer = setTimeout(() => loadLayer(layer), refreshIn);
    return () => clearTimeout(timer);
  }, [layer, loadLayer, tileSession]);

  const summary = useMemo(() => {
    const features = territory?.features || [];
    return {
      edgeCount: features.length,
      distanceKm:
        features.reduce((sum, feature) => sum + Number(feature.properties.distance_m || 0), 0) /
        1000,
    };
  }, [territory]);

  const chooseLayer = (next: Layer) => {
    setLayer(next);
    loadLayer(next);
  };

  const selectEdge = async (properties?: Record<string, unknown> | null) => {
    const edgeId = String(properties?.street_edge_id || '');
    if (!edgeId) return;
    setSelected({
      street_edge_id: edgeId,
      control_state: properties?.control_state as TerritoryProperties['control_state'],
      score: Number(properties?.score || 0),
      expires_at: properties?.expires_at as string | number | undefined,
    });
    try {
      const detail = await api.get<TerritoryProperties>(`/territory/edges/${edgeId}`);
      const score =
        layer === 'me'
          ? detail.my_score
          : layer === 'club'
            ? detail.primary_club_score
            : detail.public_score;
      const expiresAt =
        layer === 'me'
          ? detail.my_score_expires_at
          : layer === 'club'
            ? detail.primary_club_expires_at
            : detail.public_expires_at;
      setSelected((current) => ({ ...current, ...detail, score, expires_at: expiresAt }));
    } catch {
      setSelected({
        street_edge_id: edgeId,
        score: Number(properties?.score || 0),
        expires_at: properties?.expires_at as string | number | undefined,
      });
    }
  };

  if (!MAPBOX_TOKEN) {
    return (
      <View style={styles.configurationCard}>
        <Ionicons name="map-outline" size={30} color={colors.brand} />
        <Text style={styles.configurationTitle}>Mapbox setup required</Text>
        <Text style={styles.configurationBody}>
          Add EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN to the mobile build environment. Territory data
          remains private and has not fallen back to raw GPS.
        </Text>
      </View>
    );
  }

  return (
    <View>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>
          {layer === 'club' ? primaryClub?.name?.toUpperCase() || 'PRIMARY CLUB' : 'ROAD CONTROL'}
        </Text>
        <Text style={styles.heroValue}>
          {summary.distanceKm.toFixed(1)}
          <Text style={styles.heroUnit}> km controlled</Text>
        </Text>
        <Text style={styles.heroMeta}>
          {summary.edgeCount} verified road edge{summary.edgeCount === 1 ? '' : 's'} · rolling 28
          days
        </Text>
      </View>

      <View style={styles.layerTabs}>
        {LAYERS.map((item) => {
          const active = layer === item.key;
          return (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              key={item.key}
              onPress={() => chooseLayer(item.key)}
              style={[styles.layerTab, active && styles.layerTabActive]}
            >
              <Ionicons
                name={item.icon}
                size={15}
                color={active ? '#FFFFFF' : colors.textSecondary}
              />
              <Text style={[styles.layerText, active && styles.layerTextActive]}>{item.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <View style={styles.mapCard}>
        <Mapbox.MapView
          style={styles.map}
          styleURL={Mapbox.StyleURL.Dark}
          logoEnabled
          attributionEnabled
          compassEnabled
          scaleBarEnabled={false}
        >
          <Mapbox.Camera
            defaultSettings={{ centerCoordinate: DEFAULT_CENTER, zoomLevel: 11.5 }}
            minZoomLevel={3}
            maxZoomLevel={20}
          />
          <Mapbox.UserLocation visible />
          {tileSession && (
            <Mapbox.VectorSource
              id={`runlete-territory-${layer}`}
              key={tileSession.tile_url}
              tileUrlTemplates={[tileSession.tile_url]}
              onPress={(event) => {
                const feature = event.features?.[0];
                void selectEdge(feature?.properties);
              }}
            >
              <Mapbox.LineLayer
                id={`runlete-territory-line-${layer}`}
                sourceLayerID="territory"
                style={{
                  lineColor: [
                    'match',
                    ['get', 'control_state'],
                    'contested',
                    '#FFD166',
                    'expiring',
                    '#FF8C42',
                    lineColor[layer],
                  ] as any,
                  lineWidth: ['interpolate', ['linear'], ['zoom'], 8, 2, 14, 5, 18, 9],
                  lineOpacity: layer === 'competitors' ? 0.62 : 0.94,
                  lineCap: 'round',
                  lineJoin: 'round',
                }}
              />
            </Mapbox.VectorSource>
          )}
        </Mapbox.MapView>

        {loading && (
          <View style={styles.mapOverlay}>
            <ActivityIndicator color="#FFFFFF" />
            <Text style={styles.overlayText}>Loading verified roads…</Text>
          </View>
        )}

        {!loading && (error || (layer !== 'competitors' && summary.edgeCount === 0)) && (
          <View style={styles.mapOverlay}>
            <Ionicons name="trail-sign-outline" size={30} color="#FFFFFF" />
            <Text style={styles.overlayTitle}>
              {error ? 'Territory unavailable' : 'No verified control yet'}
            </Text>
            <Text style={styles.overlayText}>
              {error ||
                'Complete an eligible 2.5 km run. Roads appear after GPS verification and map matching.'}
            </Text>
            {layer === 'club' && !primaryClub && (
              <TouchableOpacity style={styles.overlayButton} onPress={() => router.push('/run/clubs')}>
                <Text style={styles.overlayButtonText}>Choose primary club</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {selected && (
          <View style={styles.edgeSheet}>
            <View style={styles.edgeSheetHeader}>
              <View style={styles.edgeIcon}>
                <Ionicons name="trail-sign" size={16} color={lineColor[layer]} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.edgeName}>
                  {selected.name || (selected.street_edge_id ? 'Mapped road edge' : 'Loading road…')}
                </Text>
                <Text style={styles.edgeMeta}>{expirationLabel(selected.expires_at)}</Text>
                {!!selected.control_state && (
                  <Text style={styles.edgeState}>{selected.control_state}</Text>
                )}
              </View>
              <TouchableOpacity
                accessibilityLabel="Close road details"
                onPress={() => setSelected(null)}
              >
                <Ionicons name="close" size={20} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
            <View style={styles.edgeStats}>
              <View>
                <Text style={styles.edgeStatLabel}>CONTROL</Text>
                <Text style={styles.edgeStatValue}>{Number(selected.score || 0).toFixed(0)} pts</Text>
              </View>
              <View>
                <Text style={styles.edgeStatLabel}>LENGTH</Text>
                <Text style={styles.edgeStatValue}>
                  {Math.round(Number(selected.distance_m || 0))} m
                </Text>
              </View>
              {layer === 'club' && (
                <View>
                  <Text style={styles.edgeStatLabel}>MY SCORE</Text>
                  <Text style={styles.edgeStatValue}>
                    {Number(selected.my_score || 0).toFixed(0)} pts
                  </Text>
                </View>
              )}
            </View>
            {!!selected.recent_history?.length && (
              <Text style={styles.historyText}>
                Latest: {selected.recent_history[0].event_type.replaceAll('_', ' ')} ·{' '}
                {new Date(selected.recent_history[0].occurred_at).toLocaleDateString()}
              </Text>
            )}
          </View>
        )}
      </View>

      <View style={styles.infoRow}>
        <Ionicons name="shield-checkmark-outline" size={17} color={colors.accentTeal} />
        <Text style={styles.infoText}>
          Only Valhalla-matched OSM roads with at least 80% coverage and 85% confidence are shown.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: {
    backgroundColor: '#12151F',
    borderRadius: borderRadius.xxl,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  eyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1.5, color: '#FF7959' },
  heroValue: { color: '#FFFFFF', fontSize: 36, fontWeight: '900', marginTop: 5 },
  heroUnit: { fontSize: 16, fontWeight: '700', color: '#AEB4C3' },
  heroMeta: { marginTop: 5, fontSize: 12, color: '#8E96A8' },
  layerTabs: { flexDirection: 'row', gap: 7, marginBottom: spacing.md },
  layerTab: {
    flex: 1,
    minHeight: 42,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.separator,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 5,
    paddingHorizontal: 7,
  },
  layerTabActive: { backgroundColor: '#181B24', borderColor: '#181B24' },
  layerText: { fontSize: 11, fontWeight: '800', color: colors.textSecondary },
  layerTextActive: { color: '#FFFFFF' },
  mapCard: {
    height: 440,
    borderRadius: 24,
    overflow: 'hidden',
    backgroundColor: '#10141D',
    position: 'relative',
  },
  map: { flex: 1 },
  mapOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'rgba(12,15,22,0.76)',
    paddingHorizontal: 36,
  },
  overlayTitle: { color: '#FFFFFF', fontSize: 16, fontWeight: '900' },
  overlayText: { color: '#CBD0DB', textAlign: 'center', fontSize: 12.5, lineHeight: 18 },
  overlayButton: {
    marginTop: 6,
    backgroundColor: colors.brand,
    borderRadius: 13,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  overlayButtonText: { color: '#FFFFFF', fontWeight: '900', fontSize: 12 },
  edgeSheet: {
    position: 'absolute',
    left: 12,
    right: 12,
    bottom: 12,
    backgroundColor: 'rgba(18,21,31,0.96)',
    borderRadius: 18,
    padding: 14,
  },
  edgeSheetHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  edgeIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: '#272B36',
    alignItems: 'center',
    justifyContent: 'center',
  },
  edgeName: { color: '#FFFFFF', fontSize: 14, fontWeight: '900' },
  edgeMeta: { color: '#9EA5B4', fontSize: 11.5, marginTop: 2 },
  edgeState: { color: '#FFD166', fontSize: 9.5, fontWeight: '900', marginTop: 3, textTransform: 'uppercase' },
  edgeStats: {
    flexDirection: 'row',
    gap: 40,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#343945',
    marginTop: 12,
    paddingTop: 12,
  },
  edgeStatLabel: { color: '#757E91', fontSize: 9, fontWeight: '900', letterSpacing: 1.2 },
  edgeStatValue: { color: '#FFFFFF', fontSize: 15, fontWeight: '900', marginTop: 3 },
  historyText: { color: '#9EA5B4', fontSize: 10.5, marginTop: 10, textTransform: 'capitalize' },
  infoRow: { flexDirection: 'row', gap: 8, alignItems: 'flex-start', marginTop: 12 },
  infoText: { flex: 1, color: colors.textSecondary, fontSize: 11.5, lineHeight: 16 },
  configurationCard: {
    borderRadius: 22,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: spacing.xl,
    alignItems: 'center',
    gap: 8,
  },
  configurationTitle: { ...typography.h4, color: colors.textPrimary },
  configurationBody: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
});

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import Mapbox from '@rnmapbox/maps';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../utils/api';
import { colors, spacing } from '../utils/theme';

const token = process.env.EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN || '';
if (token) Mapbox.setAccessToken(token);

export function ClubTerritoryMap({ clubId }: { clubId: string }) {
  const [tileUrl, setTileUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .post<{ tile_url: string }>('/territory/tile-session', {
        layer: 'club',
        club_id: clubId,
      })
      .then((session) => setTileUrl(session.tile_url))
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : 'Territory unavailable.'),
      );
  }, [clubId]);

  if (!token) {
    return <Text style={styles.message}>Mapbox is not configured for this mobile build.</Text>;
  }
  return (
    <View style={styles.card}>
      <Mapbox.MapView style={styles.map} styleURL={Mapbox.StyleURL.Dark}>
        <Mapbox.Camera
          defaultSettings={{ centerCoordinate: [78.4867, 17.385], zoomLevel: 11 }}
        />
        <Mapbox.UserLocation visible />
        {tileUrl && (
          <Mapbox.VectorSource id={`club-territory-${clubId}`} tileUrlTemplates={[tileUrl]}>
            <Mapbox.LineLayer
              id={`club-territory-line-${clubId}`}
              sourceLayerID="territory"
              style={{
                lineColor: [
                  'match',
                  ['get', 'control_state'],
                  'contested',
                  '#FFD166',
                  'expiring',
                  '#FF8C42',
                  '#32D6C0',
                ] as any,
                lineWidth: ['interpolate', ['linear'], ['zoom'], 8, 2, 14, 5, 18, 9],
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
          </Mapbox.VectorSource>
        )}
      </Mapbox.MapView>
      {!tileUrl && (
        <View style={styles.overlay}>
          {error ? (
            <Ionicons name="alert-circle-outline" size={28} color="#FFFFFF" />
          ) : (
            <ActivityIndicator color="#FFFFFF" />
          )}
          <Text style={styles.overlayText}>{error || 'Loading verified club roads…'}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { height: 440, borderRadius: 22, overflow: 'hidden', backgroundColor: '#11151E' },
  map: { flex: 1 },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: spacing.xl,
    backgroundColor: 'rgba(10,13,20,0.76)',
  },
  overlayText: { color: '#FFFFFF', textAlign: 'center', fontSize: 12 },
  message: { color: colors.textSecondary, padding: spacing.xl, textAlign: 'center' },
});

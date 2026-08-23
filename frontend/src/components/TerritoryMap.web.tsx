import React, { useCallback, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../utils/api';
import { borderRadius, colors, spacing } from '../utils/theme';

interface TerritoryCollection {
  features: { properties: { distance_m?: number } }[];
}

export function TerritoryMap() {
  const [data, setData] = useState<TerritoryCollection | null>(null);
  const [loading, setLoading] = useState(true);
  useFocusEffect(
    useCallback(() => {
      api
        .get<TerritoryCollection>('/territory/mine')
        .then(setData)
        .finally(() => setLoading(false));
    }, []),
  );
  const distance =
    (data?.features || []).reduce(
      (sum, feature) => sum + Number(feature.properties.distance_m || 0),
      0,
    ) / 1000;
  return (
    <View style={styles.card}>
      <Ionicons name="map-outline" size={34} color={colors.brand} />
      <Text style={styles.title}>{distance.toFixed(1)} km controlled</Text>
      {loading ? (
        <ActivityIndicator color={colors.brand} />
      ) : (
        <Text style={styles.body}>
          {data?.features.length || 0} verified road edges. Interactive territory maps are
          available in the iOS and Android apps.
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 260,
    borderRadius: borderRadius.xxl,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  title: { color: colors.textPrimary, fontSize: 26, fontWeight: '900' },
  body: { color: colors.textSecondary, textAlign: 'center', maxWidth: 420, lineHeight: 20 },
});

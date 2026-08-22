import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { RoutePoint } from './RunRouteMap.native';
import { colors, spacing, typography } from '../utils/theme';

export function RunRouteMap({ points }: { points: RoutePoint[] }) {
  return (
    <View style={styles.container} accessibilityLabel={`Recorded route with ${points.length} GPS points`}>
      <Ionicons name="map-outline" size={28} color={colors.textSecondary} />
      <Text style={styles.title}>Route map is available in the Runlete mobile app</Text>
      <Text style={styles.caption}>{points.length.toLocaleString()} recorded points</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
    backgroundColor: colors.surface,
  },
  title: {
    ...typography.body,
    color: colors.textPrimary,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  caption: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
});

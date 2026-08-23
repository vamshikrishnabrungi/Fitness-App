import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { RoutePoint } from './RunRouteMap';
import { colors, spacing, typography } from '../utils/theme';

type Region = RoutePoint & { latitudeDelta: number; longitudeDelta: number };

export function LiveRunMap({
  points,
}: {
  initialRegion: Region;
  points: RoutePoint[];
  following: boolean;
}) {
  return (
    <View style={styles.container}>
      <Ionicons name="phone-portrait-outline" size={32} color={colors.textSecondary} />
      <Text style={styles.title}>Live GPS recording requires the Runlete mobile app</Text>
      {points.length > 0 && <Text style={styles.caption}>{points.length} points buffered</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    backgroundColor: '#DDE6F1',
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

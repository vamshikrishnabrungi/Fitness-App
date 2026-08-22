import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../utils/theme';

export function ClubTerritoryMap({ clubId }: { clubId: string }) {
  return (
    <View style={styles.card} accessibilityLabel={`Club ${clubId} territory map`}>
      <Ionicons name="map-outline" size={30} color={colors.textSecondary} />
      <Text style={styles.text}>
        Interactive club territory is available in the Runlete mobile app.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 220,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    backgroundColor: colors.surface,
  },
  text: { color: colors.textSecondary, textAlign: 'center', marginTop: spacing.sm },
});

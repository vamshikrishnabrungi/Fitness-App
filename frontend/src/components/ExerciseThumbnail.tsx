import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors } from '../utils/theme';

interface ExerciseThumbnailProps {
  name?: string | null;
  size?: number;
  style?: ViewStyle;
}

// Use the same decorative artwork until an exercise media library is available.
export function ExerciseThumbnail({ size = 64, style }: ExerciseThumbnailProps) {
  return (
    <View
      style={[styles.wrap, { width: size, height: size, borderRadius: Math.max(12, size * 0.22) }, style]}
      accessible={false}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Ionicons name="barbell-outline" size={size * 0.48} color={colors.textSecondary} />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: '#F6F5F2',
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
});

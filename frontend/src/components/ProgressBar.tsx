import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { colors, borderRadius } from '../utils/theme';

interface ProgressBarProps {
  progress: number; // 0-100
  height?: number;
  color?: 'default' | 'green' | 'teal' | 'orange' | 'blue';
  style?: ViewStyle;
  showTrack?: boolean;
}

const colorMap = {
  default: colors.progressFill,
  green: colors.accentGreen,
  teal: colors.accentTeal,
  orange: colors.accentOrange,
  blue: colors.accentBlue,
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  height = 6,
  color = 'default',
  style,
  showTrack = true,
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));
  const fillColor = colorMap[color] || colors.progressFill;

  return (
    <View
      style={[
        styles.container,
        { height },
        showTrack && styles.track,
        style,
      ]}
    >
      <View
        style={[
          styles.fill,
          {
            width: `${clampedProgress}%`,
            height,
            backgroundColor: fillColor,
          },
        ]}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  track: {
    backgroundColor: colors.progressTrack,
  },
  fill: {
    borderRadius: borderRadius.full,
  },
});

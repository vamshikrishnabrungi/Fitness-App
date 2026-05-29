import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, borderRadius, shadows, spacing } from '../utils/theme';

interface GlassCardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'hero' | 'subtle' | 'flat';
  noPadding?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  style,
  variant = 'default',
  noPadding = false,
}) => {
  // Flat variant is just a simple white card with no gradient
  if (variant === 'flat') {
    return (
      <View style={[styles.flatContainer, noPadding ? styles.noPadding : styles.content, style]}>
        {children}
      </View>
    );
  }

  const getGradientColors = (): [string, string] => {
    switch (variant) {
      case 'hero':
        return ['rgba(255,255,255,1)', 'rgba(250,250,250,0.98)'];
      case 'subtle':
        return ['rgba(250,250,252,0.95)', 'rgba(248,248,250,0.9)'];
      default:
        return ['rgba(255,255,255,0.99)', 'rgba(252,252,254,0.96)'];
    }
  };

  return (
    <View style={[styles.container, shadows.glass, style]}>
      <LinearGradient
        colors={getGradientColors()}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        <View style={noPadding ? styles.noPadding : styles.content}>{children}</View>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.glassBorder,
    backgroundColor: colors.background,
  },
  flatContainer: {
    borderRadius: borderRadius.xl,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.separator,
  },
  gradient: {
    position: 'relative',
  },
  content: {
    padding: spacing.xl, // Increased from lg (16) to xl (24)
  },
  noPadding: {
    padding: 0,
  },
});

import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors, borderRadius, spacing, typography } from '../utils/theme';

interface BadgeProps {
  label: string;
  variant?: 'filled' | 'outline' | 'success' | 'warning' | 'info' | 'green';
  size?: 'sm' | 'md';
  style?: ViewStyle;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'filled',
  size = 'md',
  style,
  icon,
}) => {
  const isSmall = size === 'sm';

  const getVariantStyles = () => {
    switch (variant) {
      case 'success':
        return {
          container: { backgroundColor: colors.statusSuccessBg, borderWidth: 0 },
          text: { color: colors.statusSuccess },
        };
      case 'warning':
        return {
          container: { backgroundColor: colors.statusWarningBg, borderWidth: 0 },
          text: { color: colors.statusWarning },
        };
      case 'info':
        return {
          container: { backgroundColor: colors.statusInfoBg, borderWidth: 0 },
          text: { color: colors.statusInfo },
        };
      case 'green':
        return {
          container: { backgroundColor: colors.accentGreenLight, borderWidth: 1, borderColor: colors.accentGreenBorder },
          text: { color: colors.accentGreen },
        };
      case 'outline':
        return {
          container: { backgroundColor: colors.badgeOutline, borderWidth: 1, borderColor: colors.badgeOutlineBorder },
          text: { color: colors.badgeOutlineText },
        };
      case 'filled':
      default:
        return {
          container: { backgroundColor: colors.badgeFilled, borderWidth: 0 },
          text: { color: colors.badgeFilledText },
        };
    }
  };

  const variantStyles = getVariantStyles();

  return (
    <View
      style={[
        styles.container,
        isSmall ? styles.small : styles.medium,
        variantStyles.container,
        style,
      ]}
    >
      {icon && <View style={styles.icon}>{icon}</View>}
      <Text
        style={[
          styles.label,
          isSmall && styles.smallText,
          variantStyles.text,
        ]}
      >
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderRadius: borderRadius.full,
  },
  small: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  medium: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
  },
  label: {
    ...typography.captionMedium,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  smallText: {
    fontSize: 10,
  },
  icon: {
    marginRight: spacing.xs,
  },
});

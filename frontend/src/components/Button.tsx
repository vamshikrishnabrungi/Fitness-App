import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  StyleProp,
  ViewStyle,
  TextStyle,
  ActivityIndicator,
} from 'react-native';
import { colors, borderRadius, spacing, typography } from '../utils/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  style?: StyleProp<ViewStyle>;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  style,
  fullWidth = false,
}) => {
  const getContainerStyle = () => {
    const baseStyles: StyleProp<ViewStyle>[] = [styles.container];
    
    // Variant styles
    switch (variant) {
      case 'primary':
        baseStyles.push(styles.primary);
        break;
      case 'secondary':
        baseStyles.push(styles.secondary);
        break;
      case 'outline':
        baseStyles.push(styles.outline);
        break;
      case 'ghost':
        baseStyles.push(styles.ghost);
        break;
    }
    
    // Size styles
    switch (size) {
      case 'sm':
        baseStyles.push(styles.small);
        break;
      case 'lg':
        baseStyles.push(styles.large);
        break;
    }
    
    if (fullWidth) baseStyles.push(styles.fullWidth);
    if (disabled) baseStyles.push(styles.disabled);
    
    return baseStyles;
  };

  const getTextStyle = () => {
    const baseStyles: StyleProp<TextStyle>[] = [styles.text];
    
    switch (variant) {
      case 'primary':
        baseStyles.push(styles.primaryText);
        break;
      case 'secondary':
        baseStyles.push(styles.secondaryText);
        break;
      case 'outline':
      case 'ghost':
        baseStyles.push(styles.outlineText);
        break;
    }
    
    if (size === 'sm') baseStyles.push(styles.smallText);
    if (size === 'lg') baseStyles.push(styles.largeText);
    if (disabled) baseStyles.push(styles.disabledText);
    
    return baseStyles;
  };

  return (
    <TouchableOpacity
      style={[...getContainerStyle(), style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={title}
      // Web-specific attributes
      {...(typeof window !== 'undefined' && {
        role: 'button',
        'aria-label': title,
        tabIndex: disabled ? -1 : 0,
      })}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'primary' ? colors.background : colors.textPrimary}
          size="small"
        />
      ) : (
        <Text style={getTextStyle()}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.full,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
  },
  primary: {
    backgroundColor: colors.textPrimary,
  },
  secondary: {
    backgroundColor: colors.separator,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: colors.textPrimary,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  small: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  large: {
    paddingHorizontal: spacing.xxl,
    paddingVertical: spacing.lg,
  },
  fullWidth: {
    width: '100%',
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    ...typography.bodySemibold,
  },
  primaryText: {
    color: colors.background,
  },
  secondaryText: {
    color: colors.textPrimary,
  },
  outlineText: {
    color: colors.textPrimary,
  },
  smallText: {
    fontSize: 13,
  },
  largeText: {
    fontSize: 17,
  },
  disabledText: {
    color: colors.textDisabled,
  },
});

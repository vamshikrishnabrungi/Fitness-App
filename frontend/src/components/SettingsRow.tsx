import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing } from '../utils/theme';

interface SettingsRowProps {
  title: string;
  subtitle?: string;
  value?: string;
  onPress?: () => void;
  isLast?: boolean;
  icon?: React.ReactNode;
  showChevron?: boolean;
}

export const SettingsRow: React.FC<SettingsRowProps> = ({
  title,
  subtitle,
  value,
  onPress,
  isLast = false,
  icon,
  showChevron = true,
}) => {
  return (
    <TouchableOpacity
      style={[
        styles.container,
        !isLast && styles.borderBottom,
      ]}
      onPress={onPress}
      activeOpacity={0.6}
    >
      {icon && <View style={styles.iconContainer}>{icon}</View>}
      <View style={styles.content}>
        <Text style={styles.title}>{title}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
      {value && <Text style={styles.value}>{value}</Text>}
      {showChevron && (
        <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.xl, // Increased from 16 to 24 for Nike feel
    paddingHorizontal: spacing.xl,
    backgroundColor: colors.background,
    minHeight: 60, // Nike-style taller rows
  },
  borderBottom: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.separator,
  },
  iconContainer: {
    marginRight: spacing.lg,
  },
  content: {
    flex: 1,
  },
  title: {
    ...typography.body,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  value: {
    ...typography.caption,
    color: colors.textSecondary,
    marginRight: spacing.sm,
  },
});

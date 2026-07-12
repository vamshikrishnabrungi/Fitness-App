import React, { ReactNode } from 'react';
import {
  KeyboardTypeOptions,
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextStyle,
  TouchableOpacity,
  View,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { borderRadius, colors, spacing } from '../../utils/theme';

const TOTAL_STEPS = 8;

type IconName = keyof typeof Ionicons.glyphMap;

export function ProgressHeader({ step }: { step: number }) {
  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${(step / TOTAL_STEPS) * 100}%` }]} />
      </View>
      <Text style={styles.progressText}>{step} of {TOTAL_STEPS}</Text>
    </View>
  );
}

export function ScreenHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <View style={styles.header}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  );
}

export function SectionTitle({
  title,
  meta,
  style,
}: {
  title: string;
  meta?: string;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.sectionHeader, style]}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {meta ? <Text style={styles.sectionMeta}>{meta}</Text> : null}
    </View>
  );
}

export function OptionRow({
  title,
  description,
  icon,
  selected,
  onPress,
}: {
  title: string;
  description?: string;
  icon?: IconName;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.84}
      style={[styles.optionRow, selected && styles.optionRowSelected]}
      onPress={onPress}
    >
      {icon ? (
        <View style={[styles.optionIcon, selected && styles.optionIconSelected]}>
          <Ionicons name={icon} size={19} color={selected ? colors.background : colors.textPrimary} />
        </View>
      ) : null}
      <View style={styles.optionCopy}>
        <Text style={[styles.optionTitle, selected && styles.optionTitleSelected]}>{title}</Text>
        {description ? <Text style={[styles.optionDescription, selected && styles.optionDescriptionSelected]}>{description}</Text> : null}
      </View>
      <View style={[styles.checkCircle, selected && styles.checkCircleSelected]}>
        {selected ? <View style={styles.checkDot} /> : null}
      </View>
    </TouchableOpacity>
  );
}

export function SelectChip({
  label,
  selected,
  onPress,
  icon,
  style,
  textStyle,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  icon?: IconName;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.84}
      style={[styles.chip, selected && styles.chipSelected, style]}
      onPress={onPress}
    >
      {icon ? (
        <Ionicons name={icon} size={15} color={colors.textPrimary} />
      ) : null}
      <Text style={[styles.chipText, selected && styles.chipTextSelected, textStyle]} numberOfLines={1}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

export function FormField({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType,
  multiline,
  style,
}: {
  label?: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  keyboardType?: KeyboardTypeOptions;
  multiline?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.field, style]}>
      {label ? <Text style={styles.fieldLabel}>{label}</Text> : null}
      <TextInput
        style={[styles.input, multiline && styles.textArea]}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.textTertiary}
        keyboardType={keyboardType}
        multiline={multiline}
      />
    </View>
  );
}

export function BottomAction({
  bottomInset,
  title = 'Continue',
  disabled,
  onPress,
  secondary,
}: {
  bottomInset: number;
  title?: string;
  disabled?: boolean;
  onPress: () => void;
  secondary?: ReactNode;
}) {
  return (
    <View style={[styles.bottom, { paddingBottom: bottomInset + spacing.lg }]}>
      {secondary}
      <TouchableOpacity
        activeOpacity={0.82}
        disabled={disabled}
        onPress={onPress}
        style={[styles.primaryButton, disabled && styles.primaryButtonDisabled]}
      >
        <Text style={[styles.primaryButtonText, disabled && styles.primaryButtonTextDisabled]}>
          {title}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

export const onboardingStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 24,
    paddingBottom: 42,
  },
  optionStack: {
    gap: 12,
  },
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  twoColumn: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 20,
  },
  halfField: {
    flexGrow: 1,
    flexBasis: '46%',
  },
});

const styles = StyleSheet.create({
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 26,
    paddingTop: 24,
    paddingBottom: 22,
    gap: spacing.md,
  },
  progressBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#F0F0F0',
    borderRadius: 2,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.textPrimary,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '600',
    color: '#9A9A9A',
  },
  header: {
    paddingTop: 8,
    marginBottom: 30,
  },
  title: {
    fontSize: 28,
    lineHeight: 35,
    fontWeight: '600',
    letterSpacing: 0,
    color: colors.textPrimary,
    marginBottom: 14,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 23,
    fontWeight: '400',
    letterSpacing: 0,
    color: colors.textSecondary,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 26,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 14,
    lineHeight: 19,
    fontWeight: '600',
    letterSpacing: 0,
    textTransform: 'uppercase',
    color: colors.textSecondary,
  },
  sectionMeta: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textTertiary,
  },
  optionRow: {
    minHeight: 76,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  optionRowSelected: {
    backgroundColor: colors.background,
    borderColor: colors.textPrimary,
  },
  optionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionIconSelected: {
    backgroundColor: colors.textPrimary,
  },
  optionCopy: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  optionTitleSelected: {
    color: colors.textPrimary,
  },
  optionDescription: {
    fontSize: 12,
    lineHeight: 17,
    fontWeight: '400',
    color: colors.textSecondary,
    marginTop: 4,
  },
  optionDescriptionSelected: {
    color: colors.textSecondary,
  },
  checkCircle: {
    width: 23,
    height: 23,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.separatorDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkCircleSelected: {
    borderColor: colors.textPrimary,
    backgroundColor: colors.textPrimary,
  },
  checkDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.background,
  },
  chip: {
    minHeight: 42,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  chipSelected: {
    backgroundColor: colors.background,
    borderColor: colors.textPrimary,
  },
  chipText: {
    fontSize: 14,
    lineHeight: 19,
    fontWeight: '600',
    color: colors.textPrimary,
    textTransform: 'capitalize',
  },
  chipTextSelected: {
    color: colors.textPrimary,
  },
  field: {
    marginBottom: 14,
  },
  fieldLabel: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 10,
  },
  input: {
    minHeight: 54,
    borderRadius: 14,
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 18,
    paddingVertical: 14,
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '400',
    color: colors.textPrimary,
  },
  textArea: {
    minHeight: 96,
    textAlignVertical: 'top',
  },
  bottom: {
    paddingHorizontal: 26,
    paddingTop: 18,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
    backgroundColor: colors.background,
  },
  primaryButton: {
    height: 62,
    borderRadius: 31,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonDisabled: {
    backgroundColor: '#9A9A9A',
  },
  primaryButtonText: {
    fontSize: 17,
    lineHeight: 23,
    fontWeight: '700',
    color: colors.background,
  },
  primaryButtonTextDisabled: {
    color: 'rgba(255,255,255,0.72)',
  },
});

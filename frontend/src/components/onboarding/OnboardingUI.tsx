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
          <Ionicons name={icon} size={22} color={selected ? colors.background : colors.textPrimary} />
        </View>
      ) : null}
      <View style={styles.optionCopy}>
        <Text style={[styles.optionTitle, selected && styles.optionTitleSelected]}>{title}</Text>
        {description ? <Text style={[styles.optionDescription, selected && styles.optionDescriptionSelected]}>{description}</Text> : null}
      </View>
      <View style={[styles.checkCircle, selected && styles.checkCircleSelected]}>
        {selected ? <Ionicons name="checkmark" size={15} color={colors.background} /> : null}
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
        <Ionicons name={icon} size={16} color={selected ? colors.background : colors.textPrimary} />
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
    paddingHorizontal: 26,
    paddingBottom: 42,
  },
  optionStack: {
    gap: 20,
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
    fontSize: 19,
    lineHeight: 24,
    fontWeight: '600',
    color: '#9A9A9A',
  },
  header: {
    paddingTop: 8,
    marginBottom: 40,
  },
  title: {
    fontSize: 34,
    lineHeight: 42,
    fontWeight: '700',
    letterSpacing: 0,
    color: colors.textPrimary,
    marginBottom: 14,
  },
  subtitle: {
    fontSize: 21,
    lineHeight: 29,
    fontWeight: '400',
    letterSpacing: 0,
    color: '#7F7F7F',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 30,
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 18,
    lineHeight: 24,
    fontWeight: '800',
    letterSpacing: 0,
    textTransform: 'uppercase',
    color: '#7E7E7E',
  },
  sectionMeta: {
    fontSize: 17,
    lineHeight: 22,
    fontWeight: '600',
    color: colors.textTertiary,
  },
  optionRow: {
    minHeight: 82,
    borderRadius: 20,
    backgroundColor: '#F1F1F1',
    paddingHorizontal: 20,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  optionRowSelected: {
    backgroundColor: colors.textPrimary,
  },
  optionIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionIconSelected: {
    backgroundColor: 'rgba(255,255,255,0.16)',
  },
  optionCopy: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 19,
    lineHeight: 25,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  optionTitleSelected: {
    color: colors.background,
  },
  optionDescription: {
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '400',
    color: '#7F7F7F',
    marginTop: 4,
  },
  optionDescriptionSelected: {
    color: 'rgba(255,255,255,0.72)',
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
    borderColor: colors.background,
    backgroundColor: 'rgba(255,255,255,0.16)',
  },
  chip: {
    minHeight: 54,
    borderRadius: borderRadius.full,
    backgroundColor: '#F1F1F1',
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  chipSelected: {
    backgroundColor: colors.textPrimary,
  },
  chipText: {
    fontSize: 20,
    lineHeight: 25,
    fontWeight: '700',
    color: colors.textPrimary,
    textTransform: 'capitalize',
  },
  chipTextSelected: {
    color: colors.background,
  },
  field: {
    marginBottom: 20,
  },
  fieldLabel: {
    fontSize: 18,
    lineHeight: 24,
    fontWeight: '700',
    color: '#7F7F7F',
    marginBottom: 10,
  },
  input: {
    minHeight: 66,
    borderRadius: 14,
    backgroundColor: '#F1F1F1',
    paddingHorizontal: 18,
    paddingVertical: 14,
    fontSize: 20,
    lineHeight: 26,
    fontWeight: '400',
    color: colors.textPrimary,
  },
  textArea: {
    minHeight: 108,
    textAlignVertical: 'top',
  },
  bottom: {
    paddingHorizontal: 26,
    paddingTop: 22,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
    backgroundColor: colors.background,
  },
  primaryButton: {
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonDisabled: {
    backgroundColor: '#9A9A9A',
  },
  primaryButtonText: {
    fontSize: 22,
    lineHeight: 28,
    fontWeight: '700',
    color: colors.background,
  },
  primaryButtonTextDisabled: {
    color: 'rgba(255,255,255,0.72)',
  },
});

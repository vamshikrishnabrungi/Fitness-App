import React, { ReactNode } from 'react';
import {
  KeyboardTypeOptions,
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, spacing } from '../../utils/theme';

export const coachColors = {
  background: colors.background,
  card: colors.background,
  control: colors.surfaceSecondary,
  controlSelected: colors.background,
  muted: colors.textSecondary,
  softText: colors.textTertiary,
  border: colors.separatorDark,
  note: colors.surfaceSecondary,
};

type IconName = keyof typeof Ionicons.glyphMap;

const noWebFocus = { outlineStyle: 'none' } as any;

export function CoachProgress({ step }: { step: number }) {
  const router = useRouter();
  return (
    <View style={styles.progressWrap}>
      {step > 1 ? (
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Go back"
          activeOpacity={0.7}
          hitSlop={8}
          onPress={() => router.canGoBack() ? router.back() : router.replace('/onboarding/goals')}
          style={[styles.progressBack, noWebFocus]}
        >
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
      ) : null}
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${(step / 8) * 100}%` }]} />
      </View>
      <Text style={styles.progressText}>{step} of 8</Text>
    </View>
  );
}

export function CoachCard({
  icon,
  eyebrow,
  title,
  subtitle,
  children,
}: {
  icon: IconName;
  eyebrow: string;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <View style={styles.card}>
      <View style={styles.coachRow}>
        <View style={styles.coachMark}>
          <Ionicons name={icon} size={17} color={colors.background} />
        </View>
        <Text style={styles.eyebrow}>{eyebrow}</Text>
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
      {children}
    </View>
  );
}

export function CoachSection({
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

export function CoachChip({
  label,
  selected,
  onPress,
  style,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.84}
      onPress={onPress}
      style={[styles.chip, noWebFocus, selected && styles.chipSelected, style]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]} numberOfLines={2}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

export function CoachOption({
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
      activeOpacity={0.86}
      onPress={onPress}
      style={[styles.option, noWebFocus, selected && styles.optionSelected]}
    >
      {icon ? (
        <View style={[styles.optionIcon, selected && styles.optionIconSelected]}>
          <Ionicons name={icon} size={20} color={selected ? colors.background : colors.textPrimary} />
        </View>
      ) : null}
      <View style={styles.optionCopy}>
        <Text style={[styles.optionTitle, selected && styles.optionTitleSelected]}>{title}</Text>
        {description ? (
          <Text style={[styles.optionDescription, selected && styles.optionDescriptionSelected]}>
            {description}
          </Text>
        ) : null}
      </View>
      <View style={[styles.radio, selected && styles.radioSelected]}>
        {selected ? <View style={styles.radioDot} /> : null}
      </View>
    </TouchableOpacity>
  );
}

export function CoachField({
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
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.textTertiary}
        keyboardType={keyboardType}
        multiline={multiline}
        style={[styles.input, multiline && styles.textArea]}
      />
    </View>
  );
}

export function CoachNote({ label = 'Coach note', text }: { label?: string; text: string }) {
  return (
    <View style={styles.note}>
      <Text style={styles.noteLabel}>{label}</Text>
      <Text style={styles.noteText}>{text}</Text>
    </View>
  );
}

export function CoachBottom({
  bottomInset,
  disabled,
  onPress,
  children,
}: {
  bottomInset: number;
  disabled?: boolean;
  onPress: () => void;
  children?: ReactNode;
}) {
  return (
    <View style={[styles.bottom, { paddingBottom: bottomInset + spacing.lg }]}>
      {children}
      <TouchableOpacity
        activeOpacity={0.82}
        disabled={disabled}
        onPress={onPress}
        style={[styles.continueButton, disabled && styles.continueButtonDisabled]}
      >
        <Text style={[styles.continueText, disabled && styles.continueTextDisabled]}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
}

export const coachLayout = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: coachColors.background,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 116,
  },
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 9,
  },
  optionStack: {
    gap: 10,
  },
  fieldGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  halfField: {
    flexBasis: '47%',
    flexGrow: 1,
  },
  divider: {
    height: 1,
    backgroundColor: coachColors.border,
    marginVertical: 22,
  },
});

const styles = StyleSheet.create({
  progressWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 18,
    paddingHorizontal: 26,
    paddingTop: 24,
    paddingBottom: 20,
  },
  progressTrack: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.separator,
  },
  progressBack: {
    width: 32,
    height: 40,
    marginLeft: -8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
    backgroundColor: colors.textPrimary,
  },
  progressText: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '600',
    color: coachColors.softText,
  },
  card: {
    backgroundColor: coachColors.card,
    borderRadius: 24,
    paddingHorizontal: 22,
    paddingTop: 24,
    paddingBottom: 22,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0,
    shadowRadius: 28,
    elevation: 0,
  },
  coachRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 18,
  },
  coachMark: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  eyebrow: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '700',
    letterSpacing: 0.6,
    color: coachColors.softText,
  },
  title: {
    fontSize: 27,
    lineHeight: 33,
    fontWeight: '600',
    color: colors.textPrimary,
    letterSpacing: 0,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 23,
    color: coachColors.muted,
    marginBottom: 22,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  sectionMeta: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '600',
    color: colors.textTertiary,
  },
  chip: {
    minHeight: 40,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: coachColors.control,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipSelected: {
    backgroundColor: coachColors.controlSelected,
    borderColor: colors.textPrimary,
  },
  chipText: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: '#252321',
    textAlign: 'center',
    textTransform: 'capitalize',
  },
  chipTextSelected: {
    color: colors.textPrimary,
  },
  option: {
    minHeight: 76,
    marginBottom: 10,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: coachColors.control,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  optionSelected: {
    backgroundColor: coachColors.controlSelected,
    borderColor: colors.textPrimary,
  },
  optionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.background,
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
    color: coachColors.muted,
    marginTop: 3,
  },
  optionDescriptionSelected: {
    color: colors.textSecondary,
  },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: 'rgba(17,17,17,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: {
    borderColor: colors.textPrimary,
    backgroundColor: colors.textPrimary,
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.background,
  },
  field: {
    marginBottom: 12,
  },
  fieldLabel: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '600',
    color: coachColors.softText,
    marginBottom: 7,
  },
  input: {
    minHeight: 52,
    borderRadius: 16,
    backgroundColor: coachColors.control,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  textArea: {
    minHeight: 94,
    textAlignVertical: 'top',
  },
  note: {
    borderRadius: 16,
    backgroundColor: coachColors.note,
    padding: 14,
    marginTop: 22,
  },
  noteLabel: {
    fontSize: 11,
    lineHeight: 15,
    fontWeight: '700',
    letterSpacing: 0.6,
    color: colors.textTertiary,
    textTransform: 'uppercase',
    marginBottom: 5,
  },
  noteText: {
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  bottom: {
    paddingHorizontal: 26,
    paddingTop: 18,
    backgroundColor: coachColors.background,
  },
  continueButton: {
    height: 62,
    borderRadius: 999,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.12,
    shadowRadius: 18,
    elevation: 3,
  },
  continueButtonDisabled: {
    backgroundColor: colors.textTertiary,
    shadowOpacity: 0,
    elevation: 0,
  },
  continueText: {
    fontSize: 17,
    lineHeight: 23,
    fontWeight: '700',
    color: colors.background,
  },
  continueTextDisabled: {
    color: 'rgba(255,255,255,0.72)',
  },
});

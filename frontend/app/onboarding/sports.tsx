import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';

const SPORTS = [
  'Badminton', 'Basketball', 'Boxing', 'Climbing',
  'Cricket', 'Cycling', 'Football', 'Golf',
  'Hockey', 'Horse Riding', 'Hyrox', 'MMA',
  'Pilates', 'Rugby', 'Running', 'Swimming',
  'Table Tennis', 'Tennis', 'Volleyball', 'Yoga',
];

const noWebFocus = { outlineStyle: 'none' } as any;

export default function SportsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setSports, sports } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(sports);

  const toggleSport = (sport: string) => {
    setSelected(current =>
      current.includes(sport) ? current.filter(item => item !== sport) : [...current, sport]
    );
  };

  const handleNext = () => {
    setSports(selected);
    router.push('/onboarding/profile' as any);
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.progressWrap}>
        <View style={styles.progressTrack}>
          <View style={styles.progressFill} />
        </View>
        <Text style={styles.progressText}>3 of 8</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.card}>
          <View style={styles.coachRow}>
            <View style={styles.coachMark}>
              <Ionicons name="football" size={17} color={colors.background} />
            </View>
            <Text style={styles.eyebrow}>SPORT PROFILE</Text>
          </View>

          <Text style={styles.title}>What should your training support?</Text>
          <Text style={styles.subtitle}>
            Select the sports or activities you care about. Your plan will blend strength, conditioning, and movement for them.
          </Text>

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Sports and activities</Text>
            <Text style={styles.sectionMeta}>{selected.length} selected</Text>
          </View>

          <View style={styles.sportGrid}>
            {SPORTS.map(sport => (
              <SportChip
                key={sport}
                label={sport}
                selected={selected.includes(sport)}
                onPress={() => toggleSport(sport)}
              />
            ))}
          </View>

          <View style={styles.insight}>
            <Text style={styles.insightLabel}>Coach note</Text>
            <Text style={styles.insightText}>
              Pick every sport you want supported. We will use this to choose movement patterns, conditioning style, and weekly balance.
            </Text>
          </View>
        </View>
      </ScrollView>

      <View style={[styles.bottom, { paddingBottom: insets.bottom + spacing.lg }]}>
        <TouchableOpacity
          activeOpacity={0.82}
          disabled={selected.length === 0}
          style={[styles.continueButton, selected.length === 0 && styles.continueButtonDisabled]}
          onPress={handleNext}
        >
          <Text style={[styles.continueText, selected.length === 0 && styles.continueTextDisabled]}>
            Continue
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function SportChip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.84}
      onPress={onPress}
      style={[styles.sportChip, noWebFocus, selected && styles.sportChipSelected]}
    >
      <Text style={[styles.sportChipText, selected && styles.sportChipTextSelected]} numberOfLines={2}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
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
  progressFill: {
    width: '37.5%',
    height: '100%',
    borderRadius: 2,
    backgroundColor: colors.textPrimary,
  },
  progressText: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '600',
    color: colors.textTertiary,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 116,
  },
  card: {
    backgroundColor: colors.background,
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
    color: colors.textTertiary,
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
    fontSize: 15,
    lineHeight: 22,
    color: colors.textSecondary,
    marginBottom: 22,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  sectionMeta: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textTertiary,
  },
  sportGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 9,
  },
  sportChip: {
    flexBasis: '30%',
    flexGrow: 1,
    minHeight: 44,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sportChipSelected: {
    backgroundColor: colors.background,
    borderColor: colors.textPrimary,
  },
  sportChipText: {
    fontSize: 13,
    lineHeight: 17,
    fontWeight: '600',
    color: colors.textPrimary,
    textAlign: 'center',
  },
  sportChipTextSelected: {
    color: colors.textPrimary,
  },
  insight: {
    borderRadius: 16,
    backgroundColor: colors.surfaceSecondary,
    padding: 14,
    marginTop: 22,
  },
  insightLabel: {
    fontSize: 11,
    lineHeight: 15,
    fontWeight: '700',
    letterSpacing: 0.6,
    color: colors.textTertiary,
    textTransform: 'uppercase',
    marginBottom: 5,
  },
  insightText: {
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  bottom: {
    paddingHorizontal: 26,
    paddingTop: 18,
    backgroundColor: colors.background,
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

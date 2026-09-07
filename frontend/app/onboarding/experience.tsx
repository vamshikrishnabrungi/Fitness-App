import React, { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';

type Level = {
  id: string;
  label: string;
  description: string;
};

type Location = {
  id: string;
  label: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
};

const LEVELS: Level[] = [
  {
    id: 'beginner',
    label: 'Beginner',
    description: 'Start simple, learn form, and build a consistent training base.',
  },
  {
    id: 'intermediate',
    label: 'Intermediate',
    description: 'You train regularly and can handle structured progression.',
  },
  {
    id: 'advanced',
    label: 'Advanced',
    description: 'You are ready for higher loading, tighter detail, and sport demands.',
  },
];

const LOCATIONS: Location[] = [
  {
    id: 'gym',
    label: 'Gym',
    description: 'Full equipment access for strength, machines, and conditioning.',
    icon: 'barbell-outline',
  },
  {
    id: 'indoor',
    label: 'Indoors',
    description: 'Home or indoor training with limited space and equipment.',
    icon: 'home-outline',
  },
  {
    id: 'outdoor',
    label: 'Outdoors',
    description: 'Road, track, field, court, park, or open-space training.',
    icon: 'leaf-outline',
  },
];

const noWebFocus = { outlineStyle: 'none' } as any;

export default function ExperienceScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setExperience, setFitnessAssessment, setLocation, experience, location } = useOnboardingStore();
  const [level, setLevel] = useState(experience || 'intermediate');
  const [trainingLocation, setTrainingLocation] = useState(location || 'gym');

  const selectedLevel = useMemo(
    () => LEVELS.find(item => item.id === level),
    [level]
  );
  const selectedLocation = useMemo(
    () => LOCATIONS.find(item => item.id === trainingLocation),
    [trainingLocation]
  );

  const handleNext = () => {
    setExperience(level);
    setFitnessAssessment({ level: level as 'beginner' | 'intermediate' | 'advanced' });
    setLocation(trainingLocation);
    router.push('/onboarding/sports');
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.progressWrap}>
        <View style={styles.progressTrack}>
          <View style={styles.progressFill} />
        </View>
        <Text style={styles.progressText}>2 of 8</Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.card}>
          <View style={styles.coachRow}>
            <View style={styles.coachMark}>
              <Ionicons name="speedometer" size={17} color={colors.background} />
            </View>
            <Text style={styles.eyebrow}>TRAINING SETUP</Text>
          </View>

          <Text style={styles.title}>How should we start?</Text>
          <Text style={styles.subtitle}>
            Your level and training access set the first week&apos;s difficulty, exercise choices, and progression speed.
          </Text>

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Fitness level</Text>
          </View>
          <View style={styles.levelGrid}>
            {LEVELS.map(item => (
              <LevelCard
                key={item.id}
                item={item}
                selected={level === item.id}
                onPress={() => setLevel(item.id)}
              />
            ))}
          </View>

          {selectedLevel ? (
            <View style={styles.selectedNote}>
              <Text style={styles.selectedNoteLabel}>{selectedLevel.label}</Text>
              <Text style={styles.selectedNoteText}>{selectedLevel.description}</Text>
            </View>
          ) : null}

          <View style={styles.divider} />

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Training access</Text>
          </View>
          <View style={styles.locationList}>
            {LOCATIONS.map(item => (
              <LocationRow
                key={item.id}
                item={item}
                selected={trainingLocation === item.id}
                onPress={() => setTrainingLocation(item.id)}
              />
            ))}
          </View>

          {selectedLocation ? (
            <View style={styles.insight}>
              <Text style={styles.insightLabel}>Coach note</Text>
              <Text style={styles.insightText}>
                We will bias exercise selection around {selectedLocation.label.toLowerCase()} access.
              </Text>
            </View>
          ) : null}
        </View>
      </ScrollView>

      <View style={[styles.bottom, { paddingBottom: insets.bottom + spacing.lg }]}>
        <TouchableOpacity activeOpacity={0.82} style={styles.continueButton} onPress={handleNext}>
          <Text style={styles.continueText}>Continue</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function LevelCard({
  item,
  selected,
  onPress,
}: {
  item: Level;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.86}
      style={[styles.levelCard, noWebFocus, selected && styles.levelCardSelected]}
      onPress={onPress}
    >
      <Text style={[styles.levelLabel, selected && styles.levelLabelSelected]}>{item.label}</Text>
      <View style={[styles.smallRadio, selected && styles.smallRadioSelected]}>
        {selected ? <View style={styles.smallRadioDot} /> : null}
      </View>
    </TouchableOpacity>
  );
}

function LocationRow({
  item,
  selected,
  onPress,
}: {
  item: Location;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      activeOpacity={0.86}
      style={[styles.locationRow, noWebFocus, selected && styles.locationRowSelected]}
      onPress={onPress}
    >
      <View style={[styles.locationIcon, selected && styles.locationIconSelected]}>
        <Ionicons name={item.icon} size={20} color={selected ? colors.background : colors.textPrimary} />
      </View>
      <View style={styles.locationCopy}>
        <Text style={[styles.locationTitle, selected && styles.locationTitleSelected]}>{item.label}</Text>
        <Text style={[styles.locationDescription, selected && styles.locationDescriptionSelected]}>{item.description}</Text>
      </View>
      <View style={[styles.radio, selected && styles.radioSelected]}>
        {selected ? <View style={styles.radioDot} /> : null}
      </View>
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
    width: '25%',
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
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  levelGrid: {
    flexDirection: 'row',
    gap: 9,
  },
  levelCard: {
    flex: 1,
    minHeight: 72,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 12,
    paddingVertical: 12,
    justifyContent: 'space-between',
  },
  levelCardSelected: {
    backgroundColor: colors.background,
    borderColor: colors.textPrimary,
  },
  levelLabel: {
    fontSize: 14,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  levelLabelSelected: {
    color: colors.textPrimary,
  },
  smallRadio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1,
    borderColor: 'rgba(17,17,17,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'flex-end',
  },
  smallRadioSelected: {
    borderColor: colors.textPrimary,
    backgroundColor: colors.textPrimary,
  },
  smallRadioDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.background,
  },
  selectedNote: {
    borderRadius: 16,
    backgroundColor: colors.surfaceSecondary,
    padding: 14,
    marginTop: 14,
  },
  selectedNoteLabel: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  selectedNoteText: {
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  divider: {
    height: 1,
    backgroundColor: colors.separatorDark,
    marginVertical: 22,
  },
  locationList: {
    gap: 10,
  },
  locationRow: {
    minHeight: 76,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'transparent',
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  locationRowSelected: {
    backgroundColor: colors.background,
    borderColor: colors.textPrimary,
  },
  locationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  locationIconSelected: {
    backgroundColor: colors.textPrimary,
  },
  locationCopy: {
    flex: 1,
  },
  locationTitle: {
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  locationDescription: {
    fontSize: 12,
    lineHeight: 17,
    color: colors.textSecondary,
    marginTop: 3,
  },
  locationTitleSelected: {
    color: colors.textPrimary,
  },
  locationDescriptionSelected: {
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
  continueText: {
    fontSize: 17,
    lineHeight: 23,
    fontWeight: '700',
    color: colors.background,
  },
});

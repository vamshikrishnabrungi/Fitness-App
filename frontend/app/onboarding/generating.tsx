import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Animated, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { api } from '../../src/utils/api';
import { coachColors } from '../../src/components/onboarding/CoachOnboarding';
import { distanceToMetres } from '../../src/data/running';

const parseTimeSeconds = (value: string) => {
  if (!value.trim()) return null;
  const parts = value.split(':').map(Number);
  if (parts.some(part => !Number.isFinite(part))) return null;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return null;
};
const LOADING_MESSAGES = [
  'Saving your athlete profile',
  'Loading your running priorities',
  'Filtering the exercise catalogue',
  'Building your warm-up and main work',
  'Asking the coach to design all four weeks',
  'Adding instructions, cues, and progressions',
];

export default function GeneratingScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { getOnboardingData, reset } = useOnboardingStore();
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress] = useState(new Animated.Value(0));
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const generatePlan = async () => {
      try {
        setError(null);
        progress.stopAnimation();
        progress.setValue(0);
        const onboardingData = getOnboardingData();
        const dayIndex: Record<string, number> = {
          mon: 0, monday: 0,
          tue: 1, tuesday: 1,
          wed: 2, wednesday: 2,
          thu: 3, thursday: 3,
          fri: 4, friday: 4,
          sat: 5, saturday: 5,
          sun: 6, sunday: 6,
        };
        const runVenue = onboardingData.terrains.includes('track') ? 'track'
          : onboardingData.terrains.includes('trail') ? 'trail' : 'road';
        const strengthVenue = onboardingData.strength_access === 'full_gym' ? 'gym' : 'home';
        const maximumMinutes = Math.max(45, ...onboardingData.availability.map(slot => slot.minutes));
        const targetDistanceM = onboardingData.target_distance == null ? null : distanceToMetres(onboardingData.target_distance, onboardingData.distance_unit);
        const weeklyDistanceM = distanceToMetres(onboardingData.weekly_distance, onboardingData.distance_unit);
        const longestRunM = distanceToMetres(onboardingData.longest_recent_run, onboardingData.distance_unit);
        await api.put('/onboarding', {
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
          country_code: onboardingData.country?.length === 2 ? onboardingData.country.toUpperCase() : null,
          height_cm: onboardingData.height_cm,
          weight_kg: onboardingData.weight_kg,
          fitness_level: onboardingData.experience_level,
          runs_per_week: onboardingData.runs_per_week,
          weekly_distance_m: weeklyDistanceM,
          longest_recent_run_m: longestRunM,
          recent_race_event: onboardingData.recent_race_event,
          recent_race_time_seconds: parseTimeSeconds(onboardingData.recent_race_time),
          training_interruption: onboardingData.training_interruption,
          distance_unit: onboardingData.distance_unit,
          terrains: onboardingData.terrains,
          maximum_session_minutes: maximumMinutes,
          season_phase: 'general_preparation',
          target_event: onboardingData.target_event || 'run_walk',
          availability: onboardingData.availability.map(slot=>({weekday:dayIndex[slot.day.toLowerCase()] ?? 0,start_minute:slot.preferredTime==='morning'?420:slot.preferredTime==='afternoon'?780:1080,duration_minutes:slot.minutes,environments:[runVenue]})),
          equipment_access: onboardingData.equipment.map(equipment_code=>({equipment_code,environments:[strengthVenue]})),
          health_context: {
            pain_areas: onboardingData.pain_areas,
            current_injuries: onboardingData.pain_areas.map(area=>({area,note:onboardingData.medical_notes})),
            medical_notes: onboardingData.medical_notes || null,
            stress_level: onboardingData.stress_level,
          },
          goal: {goal_type:onboardingData.goal_type || 'general_fitness',target_date:onboardingData.target_date,target_event:onboardingData.target_event,target_distance_m:targetDistanceM,target_time_seconds:parseTimeSeconds(onboardingData.target_time),target_value:null,target_unit:null},
        });
        await api.postLongRunning('/training/plans', {
          weeks: 4,
          starts_on: onboardingData.start_date,
          fitness_level: onboardingData.experience_level,
          training_days_per_week: onboardingData.availability.length,
          schedule_constraints: onboardingData.schedule_constraints || null,
          health_context: {
            pain_areas: onboardingData.pain_areas,
            current_injuries: onboardingData.pain_areas.map(area=>({area,note:onboardingData.medical_notes})),
            medical_notes: onboardingData.medical_notes || null,
            stress_level: onboardingData.stress_level,
            diet_preference: onboardingData.diet_preference,
            nutrition_goal: onboardingData.nutrition_goal,
          },
        });
        await AsyncStorage.removeItem('needs_onboarding');
        await AsyncStorage.setItem('distance_unit', onboardingData.distance_unit);
        reset();
        router.replace('/(tabs)');
      } catch (err: any) {
        const message = typeof err?.message === 'string' ? err.message : '';
        setError(message && message.length <= 180 ? message : 'We couldn’t finish your training plan. Please try again.');
      }
    };

    const messageInterval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % LOADING_MESSAGES.length);
    }, 1800);

    Animated.timing(progress, {
      toValue: 100,
      duration: 150000,
      useNativeDriver: false,
    }).start();

    generatePlan();
    return () => clearInterval(messageInterval);
  }, [attempt, getOnboardingData, progress, reset, router]);

  const progressWidth = progress.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.card}>
        <View style={styles.mark}>
          <Ionicons name="flash" size={24} color={colors.background} />
        </View>
        <Text style={styles.eyebrow}>SETTING UP RUNLETE</Text>
        <Text style={styles.title}>Building your training plan.</Text>
        <Text style={styles.subtitle}>Your goals, schedule, health context, sport templates, and eligible exercises are being sent to the coach model before training becomes available.</Text>

        <View style={styles.progressTrack}>
          <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
        </View>

        <View style={styles.messageRow}>
          <ActivityIndicator size="small" color={colors.textPrimary} />
          <Text style={styles.message}>{LOADING_MESSAGES[messageIndex]}</Text>
        </View>

        {error ? (
          <View style={styles.errorBlock}>
            <Text style={styles.errorText}>{error}</Text>
            <Text style={styles.errorSubtext}>Your onboarding details are saved. Check that the backend is running, then try again.</Text>
            <TouchableOpacity style={styles.retryButton} onPress={() => setAttempt((current) => current + 1)}>
              <Text style={styles.retryText}>Try again</Text>
            </TouchableOpacity>
          </View>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: coachColors.background,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  card: {
    backgroundColor: colors.background,
    borderRadius: 24,
    padding: 24,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.08,
    shadowRadius: 28,
    elevation: 4,
  },
  mark: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },
  eyebrow: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '800',
    letterSpacing: 0.8,
    color: coachColors.softText,
    marginBottom: 12,
  },
  title: {
    fontSize: 29,
    lineHeight: 35,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: coachColors.muted,
    marginBottom: 28,
  },
  progressTrack: {
    height: 5,
    backgroundColor: 'rgba(17,17,17,0.08)',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 20,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.textPrimary,
  },
  messageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  message: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  errorBlock: {
    marginTop: 18,
  },
  errorText: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
    color: colors.statusWarning,
  },
  errorSubtext: {
    fontSize: 13,
    lineHeight: 18,
    color: coachColors.muted,
    marginTop: 4,
  },
  retryButton: {
    alignSelf: 'flex-start',
    marginTop: 16,
    borderRadius: 999,
    backgroundColor: colors.textPrimary,
    paddingHorizontal: 20,
    paddingVertical: 11,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.background,
  },
});

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Animated, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { api, ApiError } from '../../src/utils/api';
import { coachColors } from '../../src/components/onboarding/CoachOnboarding';

const LOADING_MESSAGES = [
  'Saving your goals',
  'Saving your sport profile',
  'Recording your equipment access',
  'Checking your schedule',
  'Applying privacy defaults',
  'Finishing your athlete profile',
];

export default function GeneratingScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { getOnboardingData, reset } = useOnboardingStore();
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress] = useState(new Animated.Value(0));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const generatePlan = async () => {
      try {
        const onboardingData = getOnboardingData();
        const dayIndex: Record<string,number> = {monday:0,tuesday:1,wednesday:2,thursday:3,friday:4,saturday:5,sunday:6};
        const sports: { sport: string; roleCode?: string; eventCode?: string; disciplineCode?: string; formatCode?: string }[] = onboardingData.sport_details.length
          ? onboardingData.sport_details
          : onboardingData.sports.map(sport => ({ sport }));
        const primarySport = sports[0]?.sport.toLowerCase() ?? 'running';
        const sportVenue: Record<string,string> = {
          swimming:'pool',running:'road',cycling:'road',football:'field',cricket:'field',
          basketball:'court',volleyball:'court',badminton:'court',tennis:'court',
          boxing:'combat_gym',mma:'combat_gym',
        };
        const selectedVenue = onboardingData.training_location === 'gym'
          ? 'gym'
          : onboardingData.training_location === 'indoor'
            ? 'home'
            : (sportVenue[primarySport] ?? 'home');
        await api.put('/onboarding', {
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
          country_code: onboardingData.country?.length === 2 ? onboardingData.country.toUpperCase() : null,
          height_cm: onboardingData.height_cm,
          weight_kg: onboardingData.weight_kg,
          competition_level: onboardingData.competition_level || 'recreational',
          training_age_years: onboardingData.experience === 'advanced' ? 5 : onboardingData.experience === 'intermediate' ? 2 : 0,
          maximum_session_minutes: onboardingData.session_duration_min,
          season_phase: onboardingData.season_phase,
          sports: sports.map((item,index)=>({sport_code:item.sport.toLowerCase(),role_code:item.roleCode||null,event_code:item.eventCode||null,discipline_code:item.disciplineCode||null,format_code:item.formatCode||null,weight_class_code:null,is_primary:index===0,weekly_external_minutes:0,sessions_per_week:0})),
          availability: (onboardingData.preferred_training_days.length ? onboardingData.preferred_training_days : ['Monday','Wednesday','Friday'].slice(0,onboardingData.training_days_per_week || 3)).map((day,index)=>({weekday:dayIndex[day.toLowerCase()] ?? index % 7,start_minute:onboardingData.preferred_training_time==='morning'?420:1080,duration_minutes:onboardingData.session_duration_min,environments:[selectedVenue]})),
          equipment_access: onboardingData.equipment.map(equipment_code=>({equipment_code,environments:[selectedVenue]})),
          method_familiarity: [],
          cross_training_consent: false,
          goal: {goal_type:onboardingData.primary_goal || 'general_fitness',target_date:null,target_value:null,target_unit:null},
        });
        try {
          await api.post('/training/plans', { weeks: 4, starts_on: null });
        } catch (planError) {
          // Onboarding is valid independently of training-content publication.
          // A sport release may deliberately remain gated while its reviewed
          // knowledge package is incomplete; that must not strand the athlete
          // in onboarding or trigger Expo's development error overlay.
          if (!(planError instanceof ApiError && [409, 422, 503].includes(planError.status ?? 0))) {
            throw planError;
          }
        }
        await AsyncStorage.removeItem('needs_onboarding');
        reset();
        router.replace('/(tabs)');
      } catch (err: any) {
        setError(err.message || 'Failed to generate plan');
        setTimeout(() => {
          reset();
          router.replace('/(tabs)');
        }, 2000);
      }
    };

    const messageInterval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % LOADING_MESSAGES.length);
    }, 1800);

    Animated.timing(progress, {
      toValue: 100,
      duration: 40000,
      useNativeDriver: false,
    }).start();

    generatePlan();
    return () => clearInterval(messageInterval);
  }, [getOnboardingData, progress, reset, router]);

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
        <Text style={styles.title}>Saving your athlete profile.</Text>
        <Text style={styles.subtitle}>Your goals, schedule, equipment, and sport context are being checked before training becomes available.</Text>

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
            <Text style={styles.errorSubtext}>Opening the app now.</Text>
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
});

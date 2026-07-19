import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Animated, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors } from '../../src/utils/theme';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { useAuthStore } from '../../src/store/authStore';
import { api } from '../../src/utils/api';
import { coachColors } from '../../src/components/onboarding/CoachOnboarding';

const LOADING_MESSAGES = [
  'Reading your goals',
  'Setting your starting load',
  'Matching exercises to your access',
  'Balancing sport and strength work',
  'Checking recovery limits',
  'Building your first week',
];

export default function GeneratingScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { getOnboardingData, reset } = useOnboardingStore();
  const { updateProfile } = useAuthStore();
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress] = useState(new Animated.Value(0));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const generatePlan = async () => {
      try {
        const onboardingData = getOnboardingData();
        await updateProfile({ profile: onboardingData as any });
        // Kicks off generation in the background (unless generation is paused) and returns immediately.
        const res = await api.post<{ program_generating?: boolean }>('/onboarding/complete', {
          profile: onboardingData,
          generate_program: true,
        });
        await AsyncStorage.removeItem('needs_onboarding');

        // Only wait if generation actually started. Poll until the program is ready (cap ~2 min, then land anyway).
        if (res?.program_generating) {
          const deadline = Date.now() + 120000;
          while (Date.now() < deadline) {
            await new Promise(resolve => setTimeout(resolve, 2500));
            try {
              await api.get('/programs/active'); // 200 once ready; throws on 404 while still building
              break;
            } catch {
              // not ready yet — keep waiting
            }
          }
        }
        reset();
        router.replace('/(tabs)');
      } catch (err: any) {
        console.error('Error generating plan:', err);
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
  }, [getOnboardingData, progress, reset, router, updateProfile]);

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
        <Text style={styles.eyebrow}>COACH IS BUILDING</Text>
        <Text style={styles.title}>Creating your first training week.</Text>
        <Text style={styles.subtitle}>Your profile is being translated into workouts, recovery limits, and daily guidance.</Text>

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

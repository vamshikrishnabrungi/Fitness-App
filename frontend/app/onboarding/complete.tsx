import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useOnboardingStore } from '../../src/store/onboardingStore';
import { api } from '../../src/utils/api';
import { colors } from '../../src/utils/theme';
import { coachColors } from '../../src/components/onboarding/CoachOnboarding';

export default function CompleteScreen() {
  const router = useRouter();
  const { getOnboardingData } = useOnboardingStore();
  const [error, setError] = useState('');

  const generatePlan = useCallback(async () => {
    try {
      const data = getOnboardingData();
      await api.post('/workouts/generate-weekly', data);
      setTimeout(() => router.replace('/(tabs)'), 2000);
    } catch (err: any) {
      console.error(err);
      setError('Failed to generate plan. Opening the app now.');
      setTimeout(() => router.replace('/(tabs)'), 2000);
    }
  }, [getOnboardingData, router]);

  useEffect(() => {
    generatePlan();
  }, [generatePlan]);

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <ActivityIndicator size="large" color={colors.textPrimary} style={styles.spinner} />
        <Text style={styles.eyebrow}>COACH IS BUILDING</Text>
        <Text style={styles.title}>Building your plan.</Text>
        <Text style={styles.subtitle}>AI is matching your profile to your first training week.</Text>
        {error ? <Text style={styles.error}>{error}</Text> : null}
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
  spinner: {
    alignSelf: 'flex-start',
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
  },
  error: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
    color: colors.statusWarning,
    marginTop: 18,
  },
});

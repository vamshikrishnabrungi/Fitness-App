import React, { useEffect } from 'react';
import { Stack, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../src/store/authStore';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { colors } from '../src/utils/theme';

export default function RootLayout() {
  const { isAuthenticated, isLoading, loadAuth } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();
  const navState = useRootNavigationState();

  useEffect(() => {
    loadAuth();
  }, [loadAuth]);

  useEffect(() => {
    const run = async () => {
      if (isLoading || !navState?.key) return;

      const inAuthGroup = segments[0] === '(auth)';
      const inOnboarding = segments[0] === 'onboarding';
      const inTabs = segments[0] === '(tabs)';

      const needsOnboarding = await AsyncStorage.getItem('needs_onboarding');

      if (isAuthenticated && needsOnboarding && !inOnboarding) {
        router.replace('/onboarding/goals');
        return;
      }

      if (isAuthenticated && inAuthGroup) {
        router.replace('/(tabs)');
      }

      if (!isAuthenticated && inTabs) {
        router.replace('/(auth)/welcome');
      }
    };
    run();
  }, [isAuthenticated, isLoading, navState?.key, router, segments]);

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.textPrimary} />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="onboarding" />
      </Stack>
    </>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
});

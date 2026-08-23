import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SettingsRow } from '../../src/components/SettingsRow';
import { GlassCard } from '../../src/components/GlassCard';
import { Button } from '../../src/components/Button';
import { LogoutModal } from '../../src/components/LogoutModal';
import { useAuthStore } from '../../src/store/authStore';
import { api } from '../../src/utils/api';
import { colors, typography, spacing } from '../../src/utils/theme';

interface ProfileStats { activities: number; distance_km: number; moving_minutes: number }

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [stats, setStats] = useState<ProfileStats | null>(null);

  // Refetch whenever the tab regains focus so stats stay current after workouts.
  useFocusEffect(
    React.useCallback(() => {
      api.get<ProfileStats>('/profile/stats').then(setStats).catch(() => {});
    }, [])
  );

  const handleLogout = async () => {
    try {
      await logout();
      setShowLogoutModal(false);
      setTimeout(() => {
        router.replace('/(auth)/welcome');
      }, 100);
    } catch (error) {
      console.error('Logout error:', error);
      setShowLogoutModal(false);
      router.replace('/(auth)/welcome');
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Profile</Text>
        </View>

        {/* Profile Card */}
        <View style={styles.profileSection}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              <Ionicons name="person" size={40} color={colors.textTertiary} />
            </View>
          </View>
          <Text style={styles.userName}>{user?.name || 'Athlete'}</Text>
          <Text style={styles.userEmail}>{user?.email || ''}</Text>
        </View>

        {/* Stats */}
        <GlassCard style={styles.statsCard}>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{stats?.activities ?? 0}</Text>
              <Text style={styles.statLabel}>Activities</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{Number(stats?.distance_km || 0).toFixed(1)}</Text>
              <Text style={styles.statLabel}>Kilometres</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{(Number(stats?.moving_minutes || 0) / 60).toFixed(1)}</Text>
              <Text style={styles.statLabel}>Hours</Text>
            </View>
          </View>
        </GlassCard>

        {/* Account */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="Edit Profile"
            onPress={() => router.push('/profile/edit' as any)}
            isLast
          />
        </View>

        {/* Training */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="📅 Calendar"
            onPress={() => router.push('/calendar')}
          />
          <SettingsRow
            title="📊 Analytics"
            onPress={() => router.push('/analytics')}
            isLast
          />
        </View>

        {/* Legal */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="Terms of Service"
            onPress={() => router.push('/terms-of-use')}
          />
          <SettingsRow
            title="Privacy Policy"
            onPress={() => router.push('/privacy-policy')}
            isLast
          />
        </View>

        <View style={styles.sectionDivider} />

        {/* Sign Out */}
        <View style={styles.signOutContainer}>
          <Button
            title="Sign Out"
            onPress={() => setShowLogoutModal(true)}
            variant="outline"
            fullWidth
          />
        </View>

        {/* App Info */}
        <Text style={styles.appVersion}>Runlete v1.0.0</Text>
      </ScrollView>

      {/* Logout Confirmation Modal */}
      <LogoutModal
        visible={showLogoutModal}
        onCancel={() => setShowLogoutModal(false)}
        onLogout={handleLogout}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 0, // Full width for settings rows
  },
  header: {
    paddingTop: spacing.xl,
    paddingBottom: spacing.section, // Nike-style 40px
    paddingHorizontal: spacing.page, // 24px padding
  },
  title: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  profileSection: {
    alignItems: 'center',
    marginBottom: spacing.section,
    paddingHorizontal: spacing.page,
  },
  avatarContainer: {
    marginBottom: spacing.md,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
  },
  userName: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  userEmail: {
    ...typography.body,
    color: colors.textSecondary,
  },
  statsCard: {
    marginBottom: spacing.section,
    marginHorizontal: spacing.page, // Nike-style horizontal margin
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.separator,
  },
  statValue: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.xs,
  },
  settingsGroup: {
    backgroundColor: colors.background,
  },
  sectionDivider: {
    height: 12, // Nike-style section divider
    backgroundColor: colors.surfaceSecondary,
  },
  signOutContainer: {
    marginTop: spacing.lg,
  },
  appVersion: {
    ...typography.caption,
    color: colors.textTertiary,
    textAlign: 'center',
    marginTop: spacing.xxl,
  },
});

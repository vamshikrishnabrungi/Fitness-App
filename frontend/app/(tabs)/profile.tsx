import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { SettingsRow } from '../../src/components/SettingsRow';
import { GlassCard } from '../../src/components/GlassCard';
import { Button } from '../../src/components/Button';
import { LogoutModal } from '../../src/components/LogoutModal';
import { useAuthStore } from '../../src/store/authStore';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, logout, toggleMode } = useAuthStore();
  const [switching, setSwitching] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);

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

  const handleToggleMode = async () => {
    setSwitching(true);
    try {
      await toggleMode();
    } catch (error) {
      console.error('Error toggling mode:', error);
    } finally {
      setSwitching(false);
    }
  };

  const isCoach = user?.mode === 'coach';

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
              <Text style={styles.statValue}>24</Text>
              <Text style={styles.statLabel}>Workouts</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>7</Text>
              <Text style={styles.statLabel}>Day Streak</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>18</Text>
              <Text style={styles.statLabel}>Hours</Text>
            </View>
          </View>
        </GlassCard>

        {/* Mode Toggle */}
        <View style={styles.settingsGroup}>
          <View style={styles.modeContainer}>
            <Text style={styles.modeLabel}>Mode</Text>
            <View style={styles.modeToggle}>
              <TouchableOpacity
                style={[
                  styles.modeButton,
                  !isCoach && styles.modeButtonActive,
                ]}
                onPress={isCoach ? handleToggleMode : undefined}
                disabled={switching}
              >
                <Text
                  style={[
                    styles.modeButtonText,
                    !isCoach && styles.modeButtonTextActive,
                  ]}
                >
                  User
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.modeButton,
                  isCoach && styles.modeButtonActive,
                ]}
                onPress={!isCoach ? handleToggleMode : undefined}
                disabled={switching}
              >
                <Text
                  style={[
                    styles.modeButtonText,
                    isCoach && styles.modeButtonTextActive,
                  ]}
                >
                  Coach
                </Text>
              </TouchableOpacity>
            </View>
          </View>
          {isCoach && (
            <TouchableOpacity
              style={styles.coachDashboardButton}
              onPress={() => router.push('/coach')}
            >
              <Ionicons name="clipboard-outline" size={20} color={colors.textPrimary} />
              <Text style={styles.coachDashboardText}>Open Coach Dashboard</Text>
              <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
            </TouchableOpacity>
          )}
        </View>

        {/* Settings Group 1 - User */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="Edit Profile"
            onPress={() => { }}
          />
          <SettingsRow
            title="My Goals"
            onPress={() => { }}
          />
          <SettingsRow
            title="Body Measurements"
            onPress={() => { }}
            isLast
          />
        </View>

        {/* Settings Group - Wellness */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="📅 Calendar"
            onPress={() => router.push('/calendar')}
          />
          <SettingsRow
            title="📊 Analytics"
            onPress={() => router.push('/analytics')}
          />
          <SettingsRow
            title="🏋️ From My Coach"
            onPress={() => router.push('/my-coach')}
            isLast
          />
        </View>

        {/* Settings Group 2 - Preferences */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="Units of Measure"
            onPress={() => { }}
          />
          <SettingsRow
            title="Workout Settings"
            onPress={() => { }}
          />
          <SettingsRow
            title="Notification Preferences"
            onPress={() => { }}
          />
          <SettingsRow
            title="Privacy"
            onPress={() => { }}
            isLast
          />
        </View>

        {/* Settings Group 3 - Support */}
        <View style={styles.sectionDivider} />
        <View style={styles.settingsGroup}>
          <SettingsRow
            title="Help & Support"
            onPress={() => { }}
          />
          <SettingsRow
            title="Terms of Service"
            onPress={() => { }}
          />
          <SettingsRow
            title="Privacy Policy"
            onPress={() => { }}
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
        <Text style={styles.appVersion}>SFTC v1.0.0</Text>
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
  modeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.page,
    backgroundColor: colors.background,
  },
  modeLabel: {
    ...typography.body,
    color: colors.textPrimary,
  },
  modeToggle: {
    flexDirection: 'row',
    backgroundColor: colors.separator,
    borderRadius: borderRadius.full,
    padding: 2,
  },
  modeButton: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  modeButtonActive: {
    backgroundColor: colors.textPrimary,
  },
  modeButtonText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  modeButtonTextActive: {
    color: colors.badgeFilledText,
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
  coachDashboardButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    gap: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.separator,
  },
  coachDashboardText: {
    flex: 1,
    ...typography.body,
    color: colors.textPrimary,
  },
});

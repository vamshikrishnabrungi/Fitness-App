import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../src/store/authStore';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

export default function EditProfileScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, updateProfile } = useAuthStore();

  const [name, setName] = useState(user?.name ?? '');
  const [weight, setWeight] = useState(user?.profile?.weight_kg != null ? String(user.profile.weight_kg) : '');
  const [height, setHeight] = useState(user?.profile?.height_cm != null ? String(user.profile.height_cm) : '');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Name required', 'Please enter your name.');
      return;
    }
    setSaving(true);
    try {
      // Spread the existing profile so we don't wipe onboarding data (goals, sport, etc.).
      await updateProfile({
        name: name.trim(),
        profile: {
          ...(user?.profile ?? {}),
          weight_kg: weight ? Number(weight) : undefined,
          height_cm: height ? Number(height) : undefined,
        },
      });
      router.back();
    } catch (error) {
      console.error('Failed to save profile:', error);
      Alert.alert('Could not save', 'Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Edit Profile</Text>
        <View style={styles.headerRight} />
      </View>

      <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]}>
        <Text style={styles.label}>Name</Text>
        <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Your name" placeholderTextColor={colors.textTertiary} />

        <Text style={styles.label}>Email</Text>
        <View style={[styles.input, styles.inputDisabled]}>
          <Text style={styles.disabledText}>{user?.email ?? ''}</Text>
        </View>

        <Text style={styles.label}>Weight (kg)</Text>
        <TextInput style={styles.input} value={weight} onChangeText={setWeight} placeholder="e.g. 72" placeholderTextColor={colors.textTertiary} keyboardType="numeric" />

        <Text style={styles.label}>Height (cm)</Text>
        <TextInput style={styles.input} value={height} onChangeText={setHeight} placeholder="e.g. 178" placeholderTextColor={colors.textTertiary} keyboardType="numeric" />

        <TouchableOpacity style={styles.saveButton} onPress={handleSave} disabled={saving}>
          {saving ? <ActivityIndicator color={colors.background} /> : <Text style={styles.saveText}>Save</Text>}
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingBottom: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.separator,
  },
  backButton: { padding: spacing.xs },
  headerTitle: { ...typography.h3, color: colors.textPrimary },
  headerRight: { width: 40 },
  content: { padding: spacing.lg, gap: spacing.sm },
  label: { ...typography.captionMedium, color: colors.textSecondary, marginTop: spacing.md },
  input: {
    ...typography.body, color: colors.textPrimary,
    backgroundColor: colors.surfaceSecondary, borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
  },
  inputDisabled: { justifyContent: 'center' },
  disabledText: { ...typography.body, color: colors.textTertiary },
  saveButton: {
    backgroundColor: colors.textPrimary, borderRadius: borderRadius.full,
    paddingVertical: spacing.md, alignItems: 'center', marginTop: spacing.xl,
  },
  saveText: { ...typography.bodySemibold, color: colors.background },
});

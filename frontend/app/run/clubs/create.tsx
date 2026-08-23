import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { components } from '../../../src/api/generated';
import { api, ApiError } from '../../../src/utils/api';
import { borderRadius, colors, spacing } from '../../../src/utils/theme';

type ClubCreate = components['schemas']['ClubCreate'];

const EMOJIS = ['🏃', '⚡', '🔥', '🏔️', '🌊', '🚀', '🐺', '🌙'];

export default function CreateClubScreen() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [rules, setRules] = useState('');
  const [emoji, setEmoji] = useState('🏃');
  const [isPrivate, setPrivate] = useState(false);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!name.trim()) {
      Alert.alert('Club name required', 'Give your club a clear name.');
      return;
    }
    setSaving(true);
    try {
      const payload: ClubCreate = {
        name: name.trim(),
        slug: name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''),
        description: description.trim(),
        rules: rules.trim(),
        visibility: isPrivate ? 'private' : 'public',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
        primary_color: '#FF4F2E',
        secondary_color: '#111827',
      };
      const club = await api.post<{ id: string }>(
        '/clubs',
        payload,
        { 'Idempotency-Key': `create-club-${Date.now()}-${Math.random().toString(36).slice(2)}` },
      );
      router.replace(`/run/clubs/${club.id}` as any);
    } catch (reason) {
      Alert.alert(
        'Club not created',
        reason instanceof ApiError ? reason.message : 'Please try again.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
          <Ionicons name="close" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Create a run club</Text>
        <View style={{ width: 40 }} />
      </View>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Text style={styles.eyebrow}>CLUB IDENTITY</Text>
          <Text style={styles.title}>Build the team people want to run for.</Text>
          <Text style={styles.subtitle}>
            You become the owner. Roles, membership decisions, and competition changes are audited.
          </Text>

          <Text style={styles.label}>Badge</Text>
          <View style={styles.emojiRow}>
            {EMOJIS.map((item) => (
              <TouchableOpacity
                key={item}
                style={[styles.emoji, emoji === item && styles.emojiActive]}
                onPress={() => setEmoji(item)}
              >
                <Text style={styles.emojiText}>{item}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Club name</Text>
          <TextInput
            value={name}
            onChangeText={setName}
            maxLength={120}
            placeholder="Hyderabad Distance Collective"
            placeholderTextColor={colors.textTertiary}
            style={styles.input}
          />

          <Text style={styles.label}>Description</Text>
          <TextInput
            value={description}
            onChangeText={setDescription}
            maxLength={2000}
            multiline
            placeholder="Who the club is for and how you train."
            placeholderTextColor={colors.textTertiary}
            style={[styles.input, styles.textarea]}
          />

          <Text style={styles.label}>Club rules</Text>
          <TextInput
            value={rules}
            onChangeText={setRules}
            maxLength={4000}
            multiline
            placeholder="Competition, conduct, safety, and race expectations."
            placeholderTextColor={colors.textTertiary}
            style={[styles.input, styles.textarea]}
          />

          <View style={styles.privacyCard}>
            <View style={{ flex: 1 }}>
              <Text style={styles.privacyTitle}>Private club</Text>
              <Text style={styles.privacyBody}>
                Requests require owner or admin approval. Member activity remains inside the club.
              </Text>
            </View>
            <Switch value={isPrivate} onValueChange={setPrivate} trackColor={{ true: colors.brand }} />
          </View>

          <TouchableOpacity
            style={[styles.saveButton, saving && { opacity: 0.7 }]}
            disabled={saving}
            onPress={save}
          >
            {saving ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <>
                <Ionicons name="shield-checkmark" size={19} color="#FFFFFF" />
                <Text style={styles.saveText}>Create club</Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.page,
    paddingVertical: 10,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 15 },
  content: { padding: spacing.page, paddingBottom: 50 },
  eyebrow: { color: colors.brand, fontSize: 10, fontWeight: '900', letterSpacing: 1.5 },
  title: { color: colors.textPrimary, fontSize: 29, fontWeight: '900', lineHeight: 34, marginTop: 8 },
  subtitle: { color: colors.textSecondary, fontSize: 12.5, lineHeight: 19, marginTop: 8 },
  label: { color: colors.textPrimary, fontSize: 12, fontWeight: '900', marginTop: 22, marginBottom: 8 },
  emojiRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  emoji: {
    width: 48,
    height: 48,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: colors.separator,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emojiActive: { borderColor: colors.brand, backgroundColor: '#FFF0EA' },
  emojiText: { fontSize: 22 },
  input: {
    minHeight: 50,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: colors.separator,
    backgroundColor: colors.surface,
    color: colors.textPrimary,
    paddingHorizontal: 14,
    fontSize: 14,
  },
  textarea: { minHeight: 100, paddingTop: 13, textAlignVertical: 'top' },
  privacyCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    borderRadius: borderRadius.xl,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.separator,
    padding: 16,
    gap: 12,
  },
  privacyTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 14 },
  privacyBody: { color: colors.textSecondary, fontSize: 11.5, lineHeight: 16, marginTop: 3 },
  saveButton: {
    minHeight: 54,
    borderRadius: 17,
    backgroundColor: colors.textPrimary,
    marginTop: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  saveText: { color: '#FFFFFF', fontWeight: '900', fontSize: 14 },
});

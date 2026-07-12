import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Modal, TextInput, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../../src/components/GlassCard';
import { api } from '../../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../../src/utils/theme';

interface RunClub {
  id: string;
  name: string;
  city: string;
  description: string;
  is_public: boolean;
  member_count: number;
}

export default function RunClubsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  
  const [myClubs, setMyClubs] = useState<RunClub[]>([]);
  const [localClubs, setLocalClubs] = useState<RunClub[]>([]);
  const [loading, setLoading] = useState(true);
  const [joiningId, setJoiningId] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: '', city: '', description: '' });

  useEffect(() => {
    fetchClubs();
  }, []);

  const fetchClubs = async () => {
    try {
      setLoading(true);
      // City is derived from the user's profile server-side when no city param is passed.
      const [myRes, localRes] = await Promise.all([
        api.get<RunClub[]>('/terra/clubs/my').catch(() => []),
        api.get<RunClub[]>('/terra/clubs/city').catch(() => [])
      ]);
      setMyClubs(myRes || []);
      setLocalClubs(localRes || []);
    } catch (error) {
      console.error('Failed to load run clubs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async (clubId: string) => {
    setJoiningId(clubId);
    try {
      await api.post(`/terra/clubs/${clubId}/join`, {});
      await fetchClubs();
    } catch (error) {
      console.error('Failed to join club:', error);
      Alert.alert('Could not join', 'Please try again.');
    } finally {
      setJoiningId(null);
    }
  };

  const handleCreate = async () => {
    if (!form.name.trim() || !form.city.trim()) {
      Alert.alert('Missing info', 'Club name and city are required.');
      return;
    }
    setCreating(true);
    try {
      await api.post('/terra/clubs', { ...form, is_public: true });
      setShowCreate(false);
      setForm({ name: '', city: '', description: '' });
      await fetchClubs();
    } catch (error) {
      console.error('Failed to create club:', error);
      Alert.alert('Could not create club', 'Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const renderClubCard = (club: RunClub, isLocal: boolean = false) => (
    <TouchableOpacity
      key={club.id}
      activeOpacity={0.8}
      onPress={() => router.push(`/run/clubs/${club.id}`)}
    >
      <GlassCard style={styles.clubCard}>
        <View style={styles.clubHeader}>
          <Text style={styles.clubName}>{club.name}</Text>
          {!club.is_public && <Ionicons name="lock-closed" size={16} color={colors.textSecondary} />}
        </View>
        <Text style={styles.clubCity}>📍 {club.city}</Text>
        {club.description ? <Text style={styles.clubDesc} numberOfLines={2}>{club.description}</Text> : null}
        
        <View style={styles.clubFooter}>
          <Text style={styles.memberCount}>{club.member_count} Members</Text>
          {isLocal && (
            <TouchableOpacity
              style={styles.joinButton}
              disabled={joiningId === club.id}
              onPress={() => handleJoin(club.id)}
            >
              <Text style={styles.joinText}>{joiningId === club.id ? '…' : 'Join'}</Text>
            </TouchableOpacity>
          )}
        </View>
      </GlassCard>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Run Clubs</Text>
        <TouchableOpacity style={styles.headerRight} onPress={() => setShowCreate(true)}>
           <Ionicons name="add" size={28} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 40 }]}>
        {loading ? (
          <ActivityIndicator size="large" color={colors.textPrimary} style={{ marginTop: 60 }} />
        ) : (
          <>
            <Text style={styles.sectionTitle}>MY CLUBS</Text>
            {myClubs.length > 0 ? (
              myClubs.map(c => renderClubCard(c))
            ) : (
              <GlassCard style={styles.emptyCard}>
                <Text style={styles.emptyText}>You are not in any clubs yet.</Text>
              </GlassCard>
            )}

            <Text style={[styles.sectionTitle, { marginTop: spacing.xl }]}>LOCAL TO YOU</Text>
            {localClubs.length > 0 ? (
              localClubs.map(c => renderClubCard(c, true))
            ) : (
              <Text style={styles.emptyText}>No local clubs found.</Text>
            )}
          </>
        )}
      </ScrollView>

      <Modal visible={showCreate} animationType="slide" transparent onRequestClose={() => setShowCreate(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>New Run Club</Text>
            <TextInput
              style={styles.input}
              placeholder="Club name"
              placeholderTextColor={colors.textTertiary}
              value={form.name}
              onChangeText={(t) => setForm((f) => ({ ...f, name: t }))}
            />
            <TextInput
              style={styles.input}
              placeholder="City"
              placeholderTextColor={colors.textTertiary}
              value={form.city}
              onChangeText={(t) => setForm((f) => ({ ...f, city: t }))}
            />
            <TextInput
              style={[styles.input, styles.inputMultiline]}
              placeholder="Description (optional)"
              placeholderTextColor={colors.textTertiary}
              value={form.description}
              onChangeText={(t) => setForm((f) => ({ ...f, description: t }))}
              multiline
            />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancel} onPress={() => setShowCreate(false)} disabled={creating}>
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalCreate} onPress={handleCreate} disabled={creating}>
                <Text style={styles.modalCreateText}>{creating ? 'Creating…' : 'Create'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.separator,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  headerRight: {
    width: 40,
    alignItems: 'flex-end',
  },
  scrollContent: {
    padding: spacing.lg,
  },
  sectionTitle: {
    ...typography.h4,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  clubCard: {
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  clubHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  clubName: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  clubCity: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  clubDesc: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  clubFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  memberCount: {
    ...typography.captionMedium,
    color: colors.textPrimary,
  },
  joinButton: {
    backgroundColor: colors.textPrimary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  joinText: {
    ...typography.captionMedium,
    color: '#FFF',
  },
  emptyCard: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  emptyText: {
    ...typography.body,
    color: colors.textTertiary,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.lg,
    borderTopRightRadius: borderRadius.lg,
    padding: spacing.lg,
    gap: spacing.md,
  },
  modalTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  input: {
    ...typography.body,
    color: colors.textPrimary,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  inputMultiline: {
    minHeight: 72,
    textAlignVertical: 'top',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  modalCancel: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  modalCancelText: {
    ...typography.captionMedium,
    color: colors.textSecondary,
  },
  modalCreate: {
    backgroundColor: colors.textPrimary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  modalCreateText: {
    ...typography.captionMedium,
    color: '#FFF',
  },
});

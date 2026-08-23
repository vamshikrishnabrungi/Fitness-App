import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Share,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../../../src/utils/api';
import { colors, spacing } from '../../../../src/utils/theme';

interface Member {
  id: string;
  role: 'owner' | 'admin' | 'member';
  status: string;
  version: number;
  athlete?: { name: string };
}

interface Club {
  id: string;
  name: string;
  emoji: string;
  membership_role: 'owner' | 'admin';
  version: number;
}

interface Invitation {
  id: string;
  expires_at: string;
  revoked_at?: string | null;
  maximum_uses: number;
  use_count: number;
}

const mutationKey = (name: string) => ({
  'Idempotency-Key': `${name}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
});

const CLUB_EMOJIS = ['🏃', '🔥', '⚡', '🏔️', '🌅', '🐺', '🦅', '🚀', '💨', '🏆'];

export default function ClubAdminScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [club, setClub] = useState<Club | null>(null);
  const [active, setActive] = useState<Member[]>([]);
  const [pending, setPending] = useState<Member[]>([]);
  const [banned, setBanned] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [emojiSaving, setEmojiSaving] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const [detail, members, requests, bans, invites] = await Promise.all([
        api.get<Club>(`/clubs/${id}`),
        api.get<{ items: Member[] }>(`/clubs/${id}/members?status=active&limit=100`),
        api.get<{ items: Member[] }>(`/clubs/${id}/members?status=requested&limit=100`),
        api.get<{ items: Member[] }>(`/clubs/${id}/members?status=banned&limit=100`),
        api.get<{ items: Invitation[] }>(`/clubs/${id}/invitations?limit=100`),
      ]);
      setClub(detail);
      setActive(members.items);
      setPending(requests.items);
      setBanned(bans.items);
      setInvitations(invites.items);
    } catch (reason) {
      Alert.alert('Admin unavailable', reason instanceof Error ? reason.message : 'Please try again.');
      router.back();
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useFocusEffect(useCallback(() => void load(), [load]));

  const decide = async (member: Member, approve: boolean) => {
    setWorking(member.id);
    try {
      await api.post(
        `/clubs/${id}/memberships/${member.id}/decision`,
        { approve, expected_version: member.version },
        mutationKey(`membership-${approve ? 'approve' : 'reject'}`),
      );
      await load();
    } finally {
      setWorking(null);
    }
  };

  const role = async (member: Member, nextRole: 'admin' | 'member') => {
    setWorking(member.id);
    try {
      await api.patch(
        `/clubs/${id}/memberships/${member.id}/role`,
        { role: nextRole, expected_version: member.version },
        mutationKey('membership-role'),
      );
      await load();
    } finally {
      setWorking(null);
    }
  };

  const remove = (member: Member) => {
    Alert.alert('Remove member?', `${member.athlete?.name || 'This runner'} will lose access.`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          setWorking(member.id);
          try {
            await api.post(
              `/clubs/${id}/memberships/${member.id}/remove`,
              { expected_version: member.version },
              mutationKey('membership-remove'),
            );
            await load();
          } finally {
            setWorking(null);
          }
        },
      },
    ]);
  };

  const ban = (member: Member) => {
    Alert.alert('Ban this member?', 'They will be removed and cannot rejoin until an administrator revokes the ban.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Ban',
        style: 'destructive',
        onPress: async () => {
          setWorking(member.id);
          try {
            await api.post(
              `/clubs/${id}/memberships/${member.id}/ban`,
              { reason: 'Banned by club administrator', expected_version: member.version },
              mutationKey('membership-ban'),
            );
            await load();
          } finally {
            setWorking(null);
          }
        },
      },
    ]);
  };

  const unban = async (member: Member) => {
    setWorking(member.id);
    try {
      await api.post(
        `/clubs/${id}/memberships/${member.id}/unban`,
        { expected_version: member.version },
        mutationKey('membership-unban'),
      );
      await load();
    } finally {
      setWorking(null);
    }
  };

  const invite = async () => {
    setWorking('invite');
    try {
      const created = await api.post<{ accept_token: string }>(
        `/clubs/${id}/invitations`,
        { expires_days: 7, maximum_uses: 1 },
        mutationKey('club-invitation'),
      );
      await load();
      await Share.share({
        message: `Join ${club?.name || 'my Runlete club'}: runlete://club-invitations/${created.accept_token}`,
      });
    } catch (reason) {
      Alert.alert('Invitation not created', reason instanceof Error ? reason.message : 'Please try again.');
    } finally {
      setWorking(null);
    }
  };

  const revokeInvitation = async (invitationId: string) => {
    setWorking(invitationId);
    try {
      await api.delete(
        `/clubs/${id}/invitations/${invitationId}`,
        mutationKey('invitation-revoke'),
      );
      await load();
    } finally {
      setWorking(null);
    }
  };

  const transfer = (member: Member) => {
    const owner = active.find((candidate) => candidate.role === 'owner');
    if (!owner) return;
    Alert.alert(
      'Transfer club ownership?',
      `${member.athlete?.name || 'This runner'} will become the sole owner. You will become a member.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Transfer',
          style: 'destructive',
          onPress: async () => {
            setWorking(member.id);
            try {
              await api.post(
                `/clubs/${id}/transfer-ownership`,
                { membership_id: member.id, owner_expected_version: owner.version, target_expected_version: member.version },
                mutationKey('ownership-transfer'),
              );
              router.back();
            } finally {
              setWorking(null);
            }
          },
        },
      ],
    );
  };

  const archiveClub = () => {
    if (!club) return;
    const expectedVersion = club.version;
    Alert.alert('Archive this club?', 'New competition activity will stop until the club is restored.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Archive',
        style: 'destructive',
        onPress: async () => {
          setWorking('archive');
          try {
            await api.post(`/clubs/${id}/archive`, { expected_version: expectedVersion }, mutationKey('club-archive'));
            router.replace('/run/clubs');
          } finally {
            setWorking(null);
          }
        },
      },
    ]);
  };

  const saveEmoji = async (next: string) => {
    if (!club || next === club.emoji) return;
    setEmojiSaving(true);
    try {
      await api.put(
        `/clubs/${club.id}`,
        { emoji: next, expected_version: club.version },
        mutationKey('club-emoji'),
      );
      await load();
    } catch (reason) {
      Alert.alert('Emoji not updated', reason instanceof Error ? reason.message : 'Please try again.');
    } finally {
      setEmojiSaving(false);
    }
  };

  if (loading || !club) {
    return (
      <SafeAreaView style={styles.loading}>
        <ActivityIndicator color={colors.brand} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Club administration</Text>
          <Text style={styles.subtitle}>{club.name} · {club.membership_role}</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.notice}>
          <Ionicons name="document-text-outline" size={19} color="#4C74C9" />
          <Text style={styles.noticeText}>
            Membership, role, removal, ownership, and competition changes are written to the audit log.
          </Text>
        </View>

        <Text style={styles.sectionTitle}>Club emoji</Text>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 22 }}>
          {CLUB_EMOJIS.map((item) => (
            <TouchableOpacity
              key={item}
              disabled={emojiSaving}
              accessibilityLabel={`Set club emoji ${item}`}
              onPress={() => saveEmoji(item)}
              style={{
                width: 46,
                height: 46,
                borderRadius: 14,
                alignItems: 'center',
                justifyContent: 'center',
                borderWidth: 1.5,
                borderColor: club.emoji === item ? colors.brand : colors.separator,
                backgroundColor: club.emoji === item ? '#FFF0EA' : colors.surface,
                opacity: emojiSaving && club.emoji !== item ? 0.5 : 1,
              }}
            >
              <Text style={{ fontSize: 22 }}>{item}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.sectionTitle}>Invitation links</Text>
        <View style={styles.inviteRow}>
          <Text style={styles.inviteHelp}>Create a private, single-use link that expires in seven days.</Text>
          <TouchableOpacity
            style={styles.inviteButton}
            disabled={working === 'invite'}
            onPress={invite}
          >
            {working === 'invite' ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.inviteButtonText}>Invite</Text>
            )}
          </TouchableOpacity>
        </View>
        {invitations
          .filter((item) => item.use_count < item.maximum_uses && !item.revoked_at)
          .slice(0, 5)
          .map((item) => (
            <View key={item.id} style={styles.invitationRow}>
              <Ionicons name="link-outline" size={16} color={colors.textSecondary} />
              <Text style={styles.invitationText}>
                {item.maximum_uses - item.use_count} use remaining · expires {new Date(item.expires_at).toLocaleDateString()}
              </Text>
              <TouchableOpacity onPress={() => revokeInvitation(item.id)}>
                <Text style={styles.revokeText}>Revoke</Text>
              </TouchableOpacity>
            </View>
          ))}

        <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Pending requests · {pending.length}</Text>
        {pending.map((member) => (
          <View key={member.id} style={styles.memberRow}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{(member.athlete?.name || 'R')[0]}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.memberName}>{member.athlete?.name || 'Runner'}</Text>
              <Text style={styles.memberMeta}>Awaiting review</Text>
            </View>
            {working === member.id ? (
              <ActivityIndicator color={colors.brand} />
            ) : (
              <View style={styles.actions}>
                <TouchableOpacity style={styles.reject} onPress={() => decide(member, false)}>
                  <Ionicons name="close" size={18} color="#B23B3B" />
                </TouchableOpacity>
                <TouchableOpacity style={styles.approve} onPress={() => decide(member, true)}>
                  <Ionicons name="checkmark" size={18} color="#FFFFFF" />
                </TouchableOpacity>
              </View>
            )}
          </View>
        ))}
        {!pending.length && <Text style={styles.empty}>No pending requests.</Text>}

        <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Active members · {active.length}</Text>
        {active.map((member) => (
          <View key={member.id} style={styles.memberRow}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{(member.athlete?.name || 'R')[0]}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.memberName}>{member.athlete?.name || 'Runner'}</Text>
              <Text style={styles.memberMeta}>{member.role}</Text>
            </View>
            {member.role !== 'owner' && working !== member.id && (
              <View style={styles.actions}>
                {club.membership_role === 'owner' && (
                  <>
                    <TouchableOpacity
                      style={styles.roleButton}
                      onPress={() => role(member, member.role === 'admin' ? 'member' : 'admin')}
                    >
                      <Text style={styles.roleText}>
                        {member.role === 'admin' ? 'Demote' : 'Admin'}
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.roleButton} onPress={() => transfer(member)}>
                      <Text style={styles.roleText}>Make owner</Text>
                    </TouchableOpacity>
                  </>
                )}
                <TouchableOpacity style={styles.removeButton} onPress={() => remove(member)}>
                  <Ionicons name="person-remove-outline" size={17} color="#B23B3B" />
                </TouchableOpacity>
                <TouchableOpacity style={styles.removeButton} onPress={() => ban(member)}>
                  <Ionicons name="ban-outline" size={17} color="#B23B3B" />
                </TouchableOpacity>
              </View>
            )}
          </View>
        ))}
        {!!banned.length && (
          <>
            <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Banned members · {banned.length}</Text>
            {banned.map((member) => (
              <View key={member.id} style={styles.memberRow}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{(member.athlete?.name || 'R')[0]}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.memberName}>{member.athlete?.name || 'Runner'}</Text>
                  <Text style={styles.memberMeta}>Banned</Text>
                </View>
                <TouchableOpacity style={styles.roleButton} onPress={() => unban(member)}>
                  <Text style={styles.roleText}>Unban</Text>
                </TouchableOpacity>
              </View>
            ))}
          </>
        )}
        {club.membership_role === 'owner' && (
          <TouchableOpacity style={styles.archiveButton} onPress={archiveClub}>
            <Ionicons name="archive-outline" size={18} color="#B23B3B" />
            <Text style={styles.archiveText}>Archive club</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: spacing.page, paddingVertical: 10 },
  iconButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  title: { color: colors.textPrimary, fontSize: 18, fontWeight: '900' },
  subtitle: { color: colors.textSecondary, fontSize: 11, marginTop: 2, textTransform: 'capitalize' },
  content: { padding: spacing.page, paddingBottom: 50 },
  notice: { flexDirection: 'row', gap: 10, backgroundColor: '#EDF3FF', borderRadius: 16, padding: 14, marginBottom: 24 },
  noticeText: { color: '#415474', fontSize: 11.5, lineHeight: 16, flex: 1 },
  sectionTitle: { color: colors.textPrimary, fontSize: 15, fontWeight: '900', marginBottom: 9 },
  memberRow: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 64, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.separator },
  avatar: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.surfaceSecondary, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: colors.textPrimary, fontWeight: '900' },
  memberName: { color: colors.textPrimary, fontWeight: '900', fontSize: 12.5 },
  memberMeta: { color: colors.textSecondary, fontSize: 10, marginTop: 2, textTransform: 'capitalize' },
  actions: { flexDirection: 'row', gap: 7, alignItems: 'center' },
  reject: { width: 36, height: 36, borderRadius: 11, backgroundColor: '#FBEAEA', alignItems: 'center', justifyContent: 'center' },
  approve: { width: 36, height: 36, borderRadius: 11, backgroundColor: '#168C75', alignItems: 'center', justifyContent: 'center' },
  roleButton: { borderRadius: 9, backgroundColor: colors.surfaceSecondary, paddingHorizontal: 10, paddingVertical: 8 },
  roleText: { color: colors.textPrimary, fontSize: 9.5, fontWeight: '900' },
  removeButton: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center' },
  empty: { color: colors.textSecondary, textAlign: 'center', paddingVertical: 24, fontSize: 11.5 },
  inviteRow: { flexDirection: 'row', gap: 8, marginBottom: 8 },
  inviteHelp: { flex: 1, color: colors.textSecondary, fontSize: 10.5, lineHeight: 15 },
  inviteButton: { minWidth: 76, height: 44, borderRadius: 12, backgroundColor: colors.textPrimary, alignItems: 'center', justifyContent: 'center' },
  inviteButtonText: { color: '#FFFFFF', fontWeight: '900', fontSize: 11 },
  invitationRow: { minHeight: 40, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.separator },
  invitationText: { flex: 1, color: colors.textSecondary, fontSize: 10.5 },
  revokeText: { color: '#B23B3B', fontSize: 10.5, fontWeight: '800' },
  archiveButton: { marginTop: 32, height: 48, borderRadius: 14, borderWidth: 1, borderColor: '#EDCACA', backgroundColor: '#FFF4F4', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  archiveText: { color: '#B23B3B', fontWeight: '900', fontSize: 12 },
});

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

export default function AcceptClubInvitationScreen() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const router = useRouter();
  const [message, setMessage] = useState('Accepting your club invitation…');
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    api
      .post<{ club_id: string }>(
        `/club-invitations/${encodeURIComponent(token)}/accept`,
        {},
        { 'Idempotency-Key': `accept-invite-${token.slice(-24)}` },
      )
      .then((membership) => {
        setMessage('Invitation accepted. Opening your club…');
        setTimeout(() => router.replace(`/run/clubs/${membership.club_id}` as any), 500);
      })
      .catch((reason) => {
        setFailed(true);
        setMessage(reason instanceof Error ? reason.message : 'This invitation is invalid or expired.');
      });
  }, [router, token]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.card}>
        {failed ? (
          <Ionicons name="alert-circle-outline" size={38} color="#B23B3B" />
        ) : (
          <ActivityIndicator size="large" color={colors.brand} />
        )}
        <Text style={styles.title}>{failed ? 'Could not join club' : 'Joining club'}</Text>
        <Text style={styles.message}>{message}</Text>
        {failed && (
          <TouchableOpacity style={styles.button} onPress={() => router.replace('/run/clubs')}>
            <Text style={styles.buttonText}>Browse clubs</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center', padding: spacing.page },
  card: { width: '100%', maxWidth: 420, borderRadius: 24, backgroundColor: colors.surface, padding: spacing.xl, alignItems: 'center' },
  title: { color: colors.textPrimary, fontSize: 19, fontWeight: '900', marginTop: 14 },
  message: { color: colors.textSecondary, textAlign: 'center', fontSize: 12, lineHeight: 18, marginTop: 7 },
  button: { marginTop: 18, borderRadius: 14, backgroundColor: colors.textPrimary, paddingHorizontal: 18, paddingVertical: 12 },
  buttonText: { color: '#FFFFFF', fontWeight: '900', fontSize: 12 },
});

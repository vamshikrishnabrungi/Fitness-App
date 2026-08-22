import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface Review {
  id: string;
  subject_id: string;
  flag_code: string;
  status: 'open' | 'under_review' | 'confirmed' | 'cleared' | 'appealed';
  created_at: string;
}

interface ReviewPage { items: Review[]; next_cursor?: string | null }

const mutationHeaders = () => ({
  'Idempotency-Key': `moderation-appeal-${Date.now()}-${Math.random().toString(36).slice(2)}`,
});

export default function ActivityReviewsScreen() {
  const router = useRouter();
  const [items, setItems] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [appealing, setAppealing] = useState<Review | null>(null);
  const [reason, setReason] = useState('');
  const [working, setWorking] = useState(false);

  const load = useCallback(async () => {
    try {
      const page = await api.get<ReviewPage>('/moderation/my-flags?limit=100');
      setItems(page.items);
    } catch (error) {
      Alert.alert('Reviews unavailable', error instanceof Error ? error.message : 'Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => void load(), [load]));

  const submitAppeal = async () => {
    if (!appealing || reason.trim().length < 20) return;
    setWorking(true);
    try {
      await api.post(
        `/moderation/flags/${appealing.id}/appeal`,
        { reason: reason.trim() },
        mutationHeaders(),
      );
      setAppealing(null);
      setReason('');
      await load();
    } catch (error) {
      Alert.alert('Appeal not submitted', error instanceof Error ? error.message : 'Please try again.');
    } finally {
      setWorking(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity accessibilityLabel="Back" style={styles.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Activity reviews</Text>
          <Text style={styles.subtitle}>Competition decisions and appeals</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.notice}>
          <Ionicons name="shield-checkmark-outline" size={21} color="#4C74C9" />
          <Text style={styles.noticeText}>
            Flagged activities stay out of territory, races, and leaderboards until review is complete.
          </Text>
        </View>
        {loading ? (
          <ActivityIndicator color={colors.brand} style={{ marginTop: 50 }} />
        ) : !items.length ? (
          <View style={styles.empty}>
            <Ionicons name="checkmark-circle-outline" size={34} color="#168C75" />
            <Text style={styles.emptyTitle}>No activity reviews</Text>
            <Text style={styles.emptyBody}>Your competition activities have no moderation decisions.</Text>
          </View>
        ) : (
          items.map((item) => (
            <View key={item.id} style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.reason}>{item.flag_code.replaceAll('_', ' ')}</Text>
                <Text style={[styles.status, item.status === 'confirmed' && styles.statusRejected]}>
                  {item.status}
                </Text>
              </View>
              <Text style={styles.meta}>
                Activity {item.subject_id.slice(0, 8)} · {new Date(item.created_at).toLocaleDateString()}
              </Text>
              {item.status === 'appealed' ? (
                <Text style={styles.appealState}>Appeal: under review</Text>
              ) : item.status === 'confirmed' ? (
                <TouchableOpacity style={styles.appealButton} onPress={() => setAppealing(item)}>
                  <Text style={styles.appealButtonText}>Appeal decision</Text>
                </TouchableOpacity>
              ) : null}
            </View>
          ))
        )}
        {appealing && (
          <View style={styles.form}>
            <Text style={styles.formTitle}>Appeal this decision</Text>
            <Text style={styles.formHelp}>
              Explain why the activity is legitimate. Administrators receive the original evidence and this statement.
            </Text>
            <TextInput
              value={reason}
              onChangeText={setReason}
              multiline
              maxLength={4000}
              placeholder="Provide the relevant details…"
              placeholderTextColor={colors.textTertiary}
              style={styles.input}
            />
            <View style={styles.formActions}>
              <TouchableOpacity style={styles.cancel} onPress={() => setAppealing(null)}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                disabled={reason.trim().length < 20 || working}
                style={[styles.submit, reason.trim().length < 20 && styles.disabled]}
                onPress={submitAppeal}
              >
                {working ? <ActivityIndicator size="small" color="#FFFFFF" /> : (
                  <Text style={styles.submitText}>Submit appeal</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: spacing.page, paddingVertical: 10 },
  back: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  title: { color: colors.textPrimary, fontSize: 18, fontWeight: '900' },
  subtitle: { color: colors.textSecondary, fontSize: 10.5, marginTop: 2 },
  content: { padding: spacing.page, paddingBottom: 50 },
  notice: { flexDirection: 'row', gap: 10, padding: 14, borderRadius: 16, backgroundColor: '#EDF3FF', marginBottom: 16 },
  noticeText: { flex: 1, color: '#415474', fontSize: 11.5, lineHeight: 17 },
  card: { borderRadius: 17, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.separator, padding: 15, marginBottom: 10 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  reason: { color: colors.textPrimary, fontWeight: '900', fontSize: 13, textTransform: 'capitalize' },
  status: { color: '#4C74C9', fontSize: 10, fontWeight: '900', textTransform: 'uppercase' },
  statusRejected: { color: '#B23B3B' },
  meta: { color: colors.textSecondary, fontSize: 10.5, marginTop: 5 },
  appealState: { color: '#94630A', fontWeight: '800', fontSize: 10.5, marginTop: 12, textTransform: 'capitalize' },
  appealButton: { alignSelf: 'flex-start', marginTop: 12, borderRadius: 11, backgroundColor: '#FFF0EA', paddingHorizontal: 12, paddingVertical: 9 },
  appealButtonText: { color: colors.brand, fontSize: 10.5, fontWeight: '900' },
  empty: { alignItems: 'center', paddingVertical: 54 },
  emptyTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 16, marginTop: 10 },
  emptyBody: { color: colors.textSecondary, textAlign: 'center', fontSize: 11.5, marginTop: 5 },
  form: { marginTop: 8, borderRadius: 18, padding: 16, backgroundColor: colors.surfaceSecondary },
  formTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 15 },
  formHelp: { color: colors.textSecondary, fontSize: 10.5, lineHeight: 16, marginTop: 5 },
  input: { minHeight: 115, marginTop: 12, borderRadius: 13, borderWidth: 1, borderColor: colors.separator, backgroundColor: colors.surface, padding: 12, color: colors.textPrimary, textAlignVertical: 'top' },
  formActions: { flexDirection: 'row', gap: 8, marginTop: 10 },
  cancel: { flex: 1, height: 43, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  cancelText: { color: colors.textSecondary, fontWeight: '800', fontSize: 11 },
  submit: { flex: 1.4, height: 43, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.textPrimary },
  disabled: { opacity: 0.4 },
  submitText: { color: '#FFFFFF', fontWeight: '900', fontSize: 11 },
});

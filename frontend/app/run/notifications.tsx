import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface Notification {
  id: string;
  type: string;
  title: string;
  body: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string;
}

export default function NotificationsScreen() {
  const router = useRouter();
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const page = await api.get<{ items: Notification[] }>('/notifications?limit=100');
      setItems(page.items);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => void load(), [load]));

  const markRead = async (item: Notification) => {
    if (!item.read) {
      await api.post(`/notifications/${item.id}/read`);
      setItems((current) =>
        current.map((candidate) =>
          candidate.id === item.id
            ? { ...candidate, read: true }
            : candidate,
        ),
      );
    }
    const clubId = String(item.payload?.club_id || '');
    if (clubId) router.push(`/run/clubs/${clubId}` as any);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={23} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Notifications</Text>
          <Text style={styles.subtitle}>Competition, territory, races, and club updates</Text>
        </View>
      </View>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              void load();
            }}
          />
        }
      >
        {loading ? (
          <ActivityIndicator color={colors.brand} style={{ marginTop: 60 }} />
        ) : items.length ? (
          items.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={[styles.item, !item.read && styles.unread]}
              onPress={() => void markRead(item)}
            >
              <View style={styles.icon}>
                <Ionicons
                  name={
                    item.type.includes('territory')
                      ? 'map-outline'
                      : item.type.includes('race')
                        ? 'stopwatch-outline'
                        : 'ribbon-outline'
                  }
                  size={19}
                  color={colors.brand}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.itemTitle}>{item.title}</Text>
                <Text style={styles.body}>{item.body}</Text>
                <Text style={styles.time}>{new Date(item.created_at).toLocaleString()}</Text>
              </View>
              {!item.read && <View style={styles.dot} />}
            </TouchableOpacity>
          ))
        ) : (
          <View style={styles.empty}>
            <Ionicons name="notifications-off-outline" size={36} color={colors.textTertiary} />
            <Text style={styles.emptyTitle}>No notifications yet</Text>
            <Text style={styles.body}>Verified competition updates will appear here.</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: { flexDirection: 'row', alignItems: 'center', gap: 11, paddingHorizontal: spacing.page, paddingVertical: 10 },
  back: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  title: { color: colors.textPrimary, fontSize: 20, fontWeight: '900' },
  subtitle: { color: colors.textSecondary, fontSize: 10.5, marginTop: 2 },
  content: { padding: spacing.page, paddingBottom: 60 },
  item: { minHeight: 86, flexDirection: 'row', alignItems: 'center', gap: 11, borderRadius: 17, padding: 13, marginBottom: 8, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.separator },
  unread: { backgroundColor: '#FFF7F2', borderColor: '#F3D6C8' },
  icon: { width: 40, height: 40, borderRadius: 13, backgroundColor: '#FFF0E9', alignItems: 'center', justifyContent: 'center' },
  itemTitle: { color: colors.textPrimary, fontSize: 12.5, fontWeight: '900' },
  body: { color: colors.textSecondary, fontSize: 10.5, lineHeight: 15, marginTop: 2 },
  time: { color: colors.textTertiary, fontSize: 9, marginTop: 5 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.brand },
  empty: { alignItems: 'center', paddingTop: 90, gap: 8 },
  emptyTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 16 },
});

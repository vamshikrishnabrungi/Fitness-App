import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../../../../src/utils/api';
import { colors, spacing } from '../../../../src/utils/theme';

export default function RaceCreateScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [name, setName] = useState('');
  const [capacity, setCapacity] = useState('100');
  const [routes, setRoutes] = useState<{ id: string; name: string; distance_m: number; path: { latitude: number; longitude: number }[] }[]>([]);
  const [routeId, setRouteId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  useFocusEffect(useCallback(() => {
    api.get<{items:typeof routes}>('/routes?limit=100').then(page=>setRoutes(page.items)).catch(() => setRoutes([]));
  }, []));
  const save = async () => {
    const route = routes.find((item) => item.id === routeId);
    if (!route) {
      Alert.alert('Route required', 'Select one of your saved routes or create one in Run Lab.');
      return;
    }
    setSaving(true);
    try {
      const starts = new Date();
      starts.setDate(starts.getDate() + 7);
      starts.setHours(6, 0, 0, 0);
      const cutoff = new Date(starts.getTime() + 6 * 60 * 60 * 1000);
      await api.post(`/clubs/${id}/races`, {
        name: name.trim(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
        starts_at: starts.toISOString(),
        start_window_minutes: 30,
        result_cutoff_at: cutoff.toISOString(),
        participant_capacity: Number(capacity) || 100,
        route_id: route.id,
      }, { 'Idempotency-Key': `race-${Date.now()}-${Math.random()}` });
      router.back();
    } catch (reason) {
      Alert.alert('Race not scheduled', reason instanceof Error ? reason.message : 'Please try again.');
    } finally {
      setSaving(false);
    }
  };
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}><TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={24} color={colors.textPrimary} /></TouchableOpacity><Text style={styles.headerTitle}>Schedule race</Text><View style={{ width: 24 }} /></View>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>A race is verified against its exact route.</Text>
        <View style={styles.notice}><Ionicons name="shield-checkmark-outline" size={20} color="#3370C7" /><Text style={styles.noticeText}>Results require 90% route coverage, valid start and finish proximity, and completed anti-cheat checks.</Text></View>
        <Text style={styles.label}>Race name</Text><TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Sunday 5K" placeholderTextColor={colors.textTertiary} />
        <Text style={styles.label}>Capacity</Text><TextInput style={styles.input} value={capacity} onChangeText={setCapacity} keyboardType="number-pad" />
        <Text style={styles.label}>Verified route</Text>
        {routes.map((route) => <TouchableOpacity key={route.id} style={[styles.route, routeId === route.id && styles.routeActive]} onPress={() => setRouteId(route.id)}><View><Text style={styles.routeTitle}>{route.name}</Text><Text style={styles.routeBody}>{((route.distance_m || 0) / 1000).toFixed(1)} km saved route</Text></View><Ionicons name={routeId === route.id ? 'checkmark-circle' : 'ellipse-outline'} size={20} color={routeId === route.id ? colors.brand : colors.textTertiary} /></TouchableOpacity>)}
        {!routes.length && <TouchableOpacity style={styles.route} onPress={() => router.push('/run/explore')}><View><Text style={styles.routeTitle}>Create a route first</Text><Text style={styles.routeBody}>Open Run Lab to generate and save one</Text></View><Ionicons name="chevron-forward" size={20} color={colors.textTertiary} /></TouchableOpacity>}
        <TouchableOpacity style={styles.save} onPress={save} disabled={saving || !name.trim()}>{saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveText}>Continue with route</Text>}</TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background }, header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.page }, headerTitle: { fontWeight: '900', color: colors.textPrimary }, content: { padding: spacing.page }, title: { fontSize: 28, lineHeight: 34, fontWeight: '900', color: colors.textPrimary, marginBottom: 14 }, notice: { flexDirection: 'row', gap: 10, borderRadius: 16, padding: 14, backgroundColor: '#EDF3FF' }, noticeText: { flex: 1, color: '#415474', fontSize: 11.5, lineHeight: 16 }, label: { fontSize: 12, fontWeight: '900', color: colors.textPrimary, marginTop: 20, marginBottom: 8 }, input: { minHeight: 50, borderWidth: 1, borderColor: colors.separator, backgroundColor: colors.surface, color: colors.textPrimary, borderRadius: 15, paddingHorizontal: 14 }, route: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1, borderColor: colors.separator, backgroundColor: colors.surface, borderRadius: 16, padding: 15, marginBottom: 8 }, routeActive: { borderColor: colors.brand, backgroundColor: '#FFF4EF' }, routeTitle: { color: colors.textPrimary, fontWeight: '900', fontSize: 13 }, routeBody: { color: colors.textSecondary, fontSize: 10.5, marginTop: 3 }, save: { minHeight: 54, borderRadius: 17, backgroundColor: colors.textPrimary, alignItems: 'center', justifyContent: 'center', marginTop: 26 }, saveText: { color: '#fff', fontWeight: '900' },
});

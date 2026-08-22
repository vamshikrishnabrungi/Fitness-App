import React, { useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CryptoDigestAlgorithm, digest, randomUUID } from 'expo-crypto';
import { File } from 'expo-file-system';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface UploadTicket {
  id: string;
  status: string;
  upload_url: string;
  expires_at: string;
}

const hex = (buffer: ArrayBuffer) =>
  Array.from(new Uint8Array(buffer), (value) => value.toString(16).padStart(2, '0')).join('');

const contentTypeFor = (extension: string) => {
  if (extension === '.gpx') return 'application/gpx+xml';
  if (extension === '.tcx') return 'application/vnd.garmin.tcx+xml';
  return 'application/octet-stream';
};

export default function ImportActivityScreen() {
  const router = useRouter();
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const chooseFile = async () => {
    setWorking(true);
    setMessage('Choose a GPX, TCX or FIT file.');
    try {
      const selected = await File.pickFileAsync(undefined, '*/*');
      const picked = Array.isArray(selected) ? selected[0] : selected;
      if (!picked) return;
      const file = new File(picked.uri);
      const extension = file.extension.toLowerCase();
      if (!['.gpx', '.tcx', '.fit'].includes(extension)) {
        throw new Error('Runlete supports GPX, TCX and FIT activity files.');
      }
      if (!file.size || file.size > 25 * 1024 * 1024) {
        throw new Error('Choose a file between 1 byte and 25 MB.');
      }
      setMessage('Checking the file…');
      const bytes = await file.bytes();
      const contentHash = hex(await digest(CryptoDigestAlgorithm.SHA256, bytes));
      const contentType = contentTypeFor(extension);
      const ticket = await api.post<UploadTicket>(
        '/imports/uploads',
        {
          filename: file.name,
          content_type: contentType,
          content_hash: contentHash,
          size_bytes: file.size,
          visibility: 'private',
        },
        { 'Idempotency-Key': `activity-import-${randomUUID()}` },
      );
      setMessage('Uploading securely…');
      const upload = await fetch(ticket.upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': contentType },
        body: file,
      });
      if (!upload.ok) throw new Error('The file upload did not complete. Please try again.');
      await api.post(
        `/imports/${ticket.id}/complete`,
        { expected_version: 1 },
        { 'Idempotency-Key': `activity-import-complete-${ticket.id}` },
      );
      setMessage('Uploaded. Runlete is verifying the activity.');
      Alert.alert('Import queued', 'Your activity will appear after GPS and duplicate checks finish.', [
        { text: 'Done', onPress: () => router.back() },
      ]);
    } catch (error) {
      if (error instanceof Error && /cancel/i.test(error.message)) return;
      Alert.alert('Import failed', error instanceof Error ? error.message : 'Please try again.');
      setMessage(null);
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
        <Text style={styles.title}>Import an activity</Text>
      </View>
      <View style={styles.content}>
        <View style={styles.icon}><Ionicons name="cloud-upload-outline" size={34} color={colors.brand} /></View>
        <Text style={styles.heading}>Use a watch or another running app</Text>
        <Text style={styles.body}>
          Import a GPX, TCX or FIT file. Runlete keeps the original file, verifies its GPS data, and processes it exactly like a recorded run.
        </Text>
        <View style={styles.notice}>
          <Ionicons name="lock-closed-outline" size={18} color="#31568D" />
          <Text style={styles.noticeText}>New imports are private by default. You can change visibility after processing.</Text>
        </View>
        <TouchableOpacity disabled={working} style={[styles.button, working && styles.disabled]} onPress={chooseFile}>
          {working ? <ActivityIndicator color="#FFFFFF" /> : <Ionicons name="document-attach-outline" size={19} color="#FFFFFF" />}
          <Text style={styles.buttonText}>{working ? 'Working…' : 'Choose activity file'}</Text>
        </TouchableOpacity>
        {message ? <Text style={styles.status}>{message}</Text> : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: spacing.page, paddingVertical: 10 },
  back: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  title: { color: colors.textPrimary, fontSize: 18, fontWeight: '900' },
  content: { flex: 1, padding: spacing.page, paddingTop: 50, alignItems: 'center' },
  icon: { width: 74, height: 74, borderRadius: 37, backgroundColor: '#FFF0EA', alignItems: 'center', justifyContent: 'center' },
  heading: { marginTop: 20, color: colors.textPrimary, fontSize: 20, fontWeight: '900', textAlign: 'center' },
  body: { marginTop: 10, color: colors.textSecondary, fontSize: 13, lineHeight: 20, textAlign: 'center' },
  notice: { marginTop: 22, flexDirection: 'row', gap: 9, padding: 14, borderRadius: 15, backgroundColor: '#EDF3FF' },
  noticeText: { flex: 1, color: '#415474', fontSize: 11.5, lineHeight: 17 },
  button: { marginTop: 28, width: '100%', height: 52, borderRadius: 16, backgroundColor: colors.textPrimary, flexDirection: 'row', gap: 9, alignItems: 'center', justifyContent: 'center' },
  disabled: { opacity: 0.55 },
  buttonText: { color: '#FFFFFF', fontSize: 13, fontWeight: '900' },
  status: { marginTop: 14, color: colors.textSecondary, fontSize: 11.5, textAlign: 'center' },
});

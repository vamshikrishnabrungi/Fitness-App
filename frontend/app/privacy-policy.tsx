/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function PrivacyPolicyScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={26} color="#000000" />
        </TouchableOpacity>
      </View>
      <ScrollView
        style={styles.content}
        contentContainerStyle={{ paddingBottom: insets.bottom + 32 }}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Runlete Privacy Policy</Text>
        <Text style={styles.paragraph}>Last updated: October 2025</Text>
        <Text style={styles.paragraph}>
          This Privacy Policy explains what information Runlete ("Runlete", "we", "us", or "our") collects,
          how we use it, and the choices you have. It applies to the Runlete mobile app and related services
          (the "Services"). By using Runlete, you agree to this policy.
        </Text>

        <Text style={styles.heading}>1. Information We Collect</Text>
        <Text style={styles.subheading}>Account information</Text>
        <Text style={styles.paragraph}>
          Your name, email address, and password (stored in encrypted form) when you register.
        </Text>
        <Text style={styles.subheading}>Profile and fitness data</Text>
        <Text style={styles.paragraph}>
          Information you provide to personalize training, such as your sport, goals, experience level,
          height, weight, age, equipment, schedule, injuries, and how you feel (mood, sleep, stress). This
          may include health and fitness data, which we treat as sensitive.
        </Text>
        <Text style={styles.subheading}>Activity and location data</Text>
        <Text style={styles.paragraph}>
          Workouts you complete and, if you use run tracking, your run routes and location while a run is
          active. Location is only collected when you grant permission and use location-based features.
        </Text>
        <Text style={styles.subheading}>Usage and device data</Text>
        <Text style={styles.paragraph}>
          Basic technical information such as device type, app version, and how you interact with features,
          used to keep the app working and improve it.
        </Text>

        <Text style={styles.heading}>2. How We Use Your Information</Text>
        <Text style={styles.listItem}>• To generate and adapt your training plans, workouts, and insights.</Text>
        <Text style={styles.listItem}>• To provide run tracking, run clubs, leaderboards, and other features.</Text>
        <Text style={styles.listItem}>• To operate, secure, maintain, and improve the Services.</Text>
        <Text style={styles.listItem}>• To communicate with you about your account and important updates.</Text>
        <Text style={styles.listItem}>• To comply with legal obligations.</Text>
        <Text style={styles.paragraph}>
          We do not sell your personal information.
        </Text>

        <Text style={styles.heading}>3. How We Share Information</Text>
        <Text style={styles.paragraph}>We share information only as needed to run Runlete:</Text>
        <Text style={styles.listItem}>
          • Service providers who host our systems and help operate the app (for example, cloud hosting and
          AI providers that help generate your training plans), under agreements that require them to protect
          your data.
        </Text>
        <Text style={styles.listItem}>
          • Other members, when you choose to share activity in a run club — for example, your name and run
          stats may appear on a club feed or leaderboard.
        </Text>
        <Text style={styles.listItem}>
          • Legal and safety reasons, when required by law or to protect rights and safety.
        </Text>

        <Text style={styles.heading}>4. Health and Location Data</Text>
        <Text style={styles.paragraph}>
          We treat your health, fitness, and location data as sensitive. We use it to deliver the features
          you ask for and do not use it for advertising. You can turn off location access at any time in your
          device settings, though some features may stop working.
        </Text>

        <Text style={styles.heading}>5. Data Retention</Text>
        <Text style={styles.paragraph}>
          We keep your information for as long as your account is active or as needed to provide the
          Services. When you delete your account, we delete or anonymize your personal data, except where we
          must keep it to meet legal obligations.
        </Text>

        <Text style={styles.heading}>6. Your Rights and Choices</Text>
        <Text style={styles.paragraph}>
          You can view and edit much of your information in the app. Depending on where you live, you may also
          have the right to access, correct, export, or delete your personal data, or object to certain
          processing. To make a request or delete your account, contact us at privacy@runlete.com.
        </Text>

        <Text style={styles.heading}>7. Security</Text>
        <Text style={styles.paragraph}>
          We use reasonable technical and organizational measures to protect your information, including
          encrypted passwords and secure connections. No system is perfectly secure, so we cannot guarantee
          absolute security.
        </Text>

        <Text style={styles.heading}>8. Children's Privacy</Text>
        <Text style={styles.paragraph}>
          Runlete is designed for athletes aged 16 and over. Users under 18 should only use Runlete with a
          parent or guardian's consent and involvement. We do not knowingly collect data from children under
          16. If you believe a child has provided us data without proper consent, contact us and we will
          remove it.
        </Text>

        <Text style={styles.heading}>9. International Data Transfers</Text>
        <Text style={styles.paragraph}>
          Your information may be processed in countries other than your own. Where required, we take steps to
          ensure it is protected in line with applicable data protection laws.
        </Text>

        <Text style={styles.heading}>10. Changes to This Policy</Text>
        <Text style={styles.paragraph}>
          We may update this Privacy Policy from time to time. If we make material changes, we will notify you
          in the app or by email. Continuing to use Runlete after changes take effect means you accept the
          updated policy.
        </Text>

        <Text style={styles.heading}>11. Contact</Text>
        <Text style={styles.paragraph}>
          Questions or privacy requests? Contact us at privacy@runlete.com.
        </Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 10,
    lineHeight: 36,
    letterSpacing: -0.3,
  },
  heading: {
    fontSize: 16,
    fontWeight: '700',
    color: '#000000',
    marginTop: 16,
    marginBottom: 6,
  },
  subheading: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
    marginTop: 12,
    marginBottom: 4,
  },
  paragraph: {
    fontSize: 14,
    color: '#111111',
    lineHeight: 22,
    marginBottom: 10,
  },
  listItem: {
    fontSize: 14,
    color: '#111111',
    lineHeight: 22,
    marginBottom: 6,
  },
});

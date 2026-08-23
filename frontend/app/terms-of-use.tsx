/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TermsOfUseScreen() {
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
        <Text style={styles.title}>Runlete Terms of Use</Text>
        <Text style={styles.paragraph}>Last updated: October 2025</Text>
        <Text style={styles.paragraph}>
          Welcome to Runlete. These Terms of Use ("Terms") are an agreement between you and Runlete
          ("Runlete", "we", "us", or "our") and govern your use of the Runlete mobile app and related
          services (the "Services"). By creating an account or using the Services, you agree to these Terms.
          If you do not agree, please do not use the Services.
        </Text>

        <Text style={styles.heading}>1. Who Can Use Runlete</Text>
        <Text style={styles.paragraph}>
          You must be at least 16 years old to create your own account. If you are under 18, you may only
          use Runlete with the involvement and consent of a parent or legal guardian, who agrees to these
          Terms on your behalf. If you are a coach, parent, or guardian setting up or supervising an account
          for a young athlete, you are responsible for that use.
        </Text>

        <Text style={styles.heading}>2. Your Account</Text>
        <Text style={styles.paragraph}>
          You are responsible for the information you provide, for keeping your login secure, and for all
          activity under your account. Please give us accurate profile and health information, since Runlete
          uses it to generate your training. Tell us right away if you believe your account has been
          compromised.
        </Text>

        <Text style={styles.heading}>3. What Runlete Provides</Text>
        <Text style={styles.paragraph}>
          Runlete offers AI-generated training and workout plans, sport-specific guidance, activity and run
          tracking, nutrition and recovery insights, and social features such as run clubs. Training plans
          and insights are generated automatically based on the information you provide and general
          principles of exercise science. They are suggestions, not personalized professional instruction,
          and may not be suitable for everyone.
        </Text>

        <Text style={styles.heading}>4. Health & Safety Disclaimer</Text>
        <Text style={styles.paragraph}>
          RUNLETE IS NOT A MEDICAL SERVICE AND DOES NOT PROVIDE MEDICAL ADVICE. The plans, workouts,
          nutrition suggestions, and other content are for general fitness and informational purposes only
          and are not a substitute for advice from a qualified physician, physical therapist, dietitian, or
          coach.
        </Text>
        <Text style={styles.paragraph}>
          Consult a healthcare professional before starting any exercise or nutrition program, especially if
          you are pregnant, injured, recovering from illness, under 18, or have any medical condition.
          Exercise carries inherent risks, including injury. You participate voluntarily and assume full
          responsibility for your own health and safety. Stop and seek medical attention if you experience
          pain, dizziness, or any warning sign. To the fullest extent permitted by law, Runlete is not
          liable for any injury or health outcome arising from your use of the Services.
        </Text>

        <Text style={styles.heading}>5. Your Content and Conduct</Text>
        <Text style={styles.paragraph}>
          You may share content such as run activity, posts, and messages within run clubs ("User Content").
          You keep ownership of your User Content, and you grant Runlete a non-exclusive, worldwide license
          to host, display, and share it as needed to operate the Services (for example, showing your run on
          a club feed or leaderboard). You are responsible for what you share and confirm you have the right
          to share it.
        </Text>
        <Text style={styles.paragraph}>You agree not to:</Text>
        <Text style={styles.listItem}>• Harass, abuse, threaten, or impersonate others.</Text>
        <Text style={styles.listItem}>• Post content that is illegal, hateful, or infringes others' rights.</Text>
        <Text style={styles.listItem}>• Cheat, falsify activity data, or manipulate leaderboards.</Text>
        <Text style={styles.listItem}>• Attempt to hack, disrupt, reverse-engineer, or misuse the Services.</Text>
        <Text style={styles.paragraph}>
          We may remove content or suspend accounts that violate these Terms.
        </Text>

        <Text style={styles.heading}>6. Location and Activity Data</Text>
        <Text style={styles.paragraph}>
          Some features, such as run tracking and location-based run clubs, require access to your device
          location. You control these permissions in your device settings. How we handle your data is
          described in our Privacy Policy.
        </Text>

        <Text style={styles.heading}>7. Intellectual Property</Text>
        <Text style={styles.paragraph}>
          The Runlete name, logo, app, and content (excluding User Content) are owned by Runlete and
          protected by law. We grant you a limited, personal, non-transferable license to use the app for
          your own, non-commercial fitness use. Please don't copy, resell, or redistribute it.
        </Text>

        <Text style={styles.heading}>8. Third-Party Services</Text>
        <Text style={styles.paragraph}>
          Runlete relies on third-party providers (for example, cloud hosting, mapping, and AI providers
          that help generate your plans). Their handling of data is governed by their own terms and
          policies. We are not responsible for third-party services we do not control.
        </Text>

        <Text style={styles.heading}>9. Fees</Text>
        <Text style={styles.paragraph}>
          Runlete is currently free to use. If we introduce paid features or subscriptions in the future, we
          will present the pricing and terms clearly before you are charged.
        </Text>

        <Text style={styles.heading}>10. Termination</Text>
        <Text style={styles.paragraph}>
          You may stop using Runlete and delete your account at any time. We may suspend or terminate your
          access if you violate these Terms or misuse the Services. Sections that by their nature should
          survive termination (such as disclaimers and limitations of liability) will continue to apply.
        </Text>

        <Text style={styles.heading}>11. Disclaimers and Limitation of Liability</Text>
        <Text style={styles.paragraph}>
          The Services are provided "as is" without warranties of any kind. We do not guarantee that the
          Services will be uninterrupted, error-free, or that any fitness result will be achieved. To the
          fullest extent permitted by law, Runlete will not be liable for indirect, incidental, or
          consequential damages, and our total liability relating to the Services is limited to the amount
          you paid us (if any) in the 12 months before the claim.
        </Text>

        <Text style={styles.heading}>12. Changes to These Terms</Text>
        <Text style={styles.paragraph}>
          We may update these Terms from time to time. If we make material changes, we will notify you in the
          app or by email. Continuing to use Runlete after changes take effect means you accept the updated
          Terms.
        </Text>

        <Text style={styles.heading}>13. Governing Law</Text>
        <Text style={styles.paragraph}>
          These Terms are governed by the laws of [your jurisdiction], without regard to conflict-of-law
          rules. Any disputes will be handled by the courts located in [your jurisdiction], unless
          applicable law requires otherwise.
        </Text>

        <Text style={styles.heading}>14. Contact</Text>
        <Text style={styles.paragraph}>
          Questions about these Terms? Contact us at support@runlete.com.
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

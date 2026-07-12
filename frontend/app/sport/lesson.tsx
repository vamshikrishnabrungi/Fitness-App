import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, spacing } from '../../src/utils/theme';

const CATEGORY_COPY: Record<string, { label: string; icon: keyof typeof Ionicons.glyphMap }> = {
  Fundamentals: { label: 'Foundation lesson', icon: 'school-outline' },
  Drills: { label: 'Practice drill', icon: 'fitness-outline' },
  Tactics: { label: 'Sport IQ', icon: 'bulb-outline' },
  Recovery: { label: 'Recovery focus', icon: 'leaf-outline' },
};

function paramText(value: string | string[] | undefined, fallback = '') {
  if (Array.isArray(value)) return value[0] || fallback;
  return value || fallback;
}

export default function LessonDetailScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{
    title?: string;
    category?: string;
    sport?: string;
    duration?: string;
    difficulty?: string;
    description?: string;
  }>();

  const title = paramText(params.title, 'Lesson');
  const category = paramText(params.category, 'Fundamentals');
  const sport = paramText(params.sport, 'Sport');
  const difficulty = paramText(params.difficulty, 'All levels');
  const duration = paramText(params.duration, '10');
  const description = paramText(params.description, 'Lesson details will appear here.');
  const categoryCopy = CATEGORY_COPY[category] || CATEGORY_COPY.Fundamentals;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()} activeOpacity={0.75}>
          <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Lesson</Text>
        <View style={styles.headerRight} />
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.heroIcon}>
          <Ionicons name={categoryCopy.icon} size={26} color={colors.textPrimary} />
        </View>

        <Text style={styles.eyebrow}>{sport} · {categoryCopy.label}</Text>
        <Text style={styles.title}>{title}</Text>

        <View style={styles.metaRow}>
          <View style={styles.metaPill}>
            <Text style={styles.metaText}>{difficulty}</Text>
          </View>
          <View style={styles.metaPill}>
            <Text style={styles.metaText}>{duration} min</Text>
          </View>
          <View style={styles.metaPill}>
            <Text style={styles.metaText}>{category}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Focus</Text>
          <Text style={styles.bodyText}>{description}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>How to use this</Text>
          <View style={styles.bulletRow}>
            <View style={styles.dot} />
            <Text style={styles.bulletText}>Read the focus before practice so you know what the session is trying to improve.</Text>
          </View>
          <View style={styles.bulletRow}>
            <View style={styles.dot} />
            <Text style={styles.bulletText}>Use it alongside your training plan, not as a replacement for the workout.</Text>
          </View>
          <View style={styles.bulletRow}>
            <View style={styles.dot} />
            <Text style={styles.bulletText}>Keep notes on what felt sharp, confusing, or hard to repeat.</Text>
          </View>
        </View>

        <TouchableOpacity style={styles.primaryButton} activeOpacity={0.82}>
          <Text style={styles.primaryButtonText}>Mark as viewed</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    height: 58,
    paddingHorizontal: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'flex-start',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 17,
    lineHeight: 22,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  headerRight: {
    width: 40,
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingHorizontal: spacing.lg,
    paddingTop: 18,
  },
  heroIcon: {
    width: 58,
    height: 58,
    borderRadius: 18,
    backgroundColor: colors.surfaceSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 22,
  },
  eyebrow: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 10,
  },
  title: {
    fontSize: 28,
    lineHeight: 35,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 16,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 30,
  },
  metaPill: {
    minHeight: 36,
    borderRadius: 18,
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 13,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metaText: {
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  section: {
    marginBottom: 28,
  },
  sectionTitle: {
    fontSize: 17,
    lineHeight: 23,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 10,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 23,
    color: colors.textSecondary,
  },
  bulletRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 11,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: colors.textPrimary,
    marginTop: 9,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
    color: colors.textSecondary,
  },
  primaryButton: {
    height: 58,
    borderRadius: 29,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 6,
  },
  primaryButtonText: {
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '700',
    color: colors.background,
  },
});

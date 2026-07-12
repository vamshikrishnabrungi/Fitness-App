import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface Lesson {
  id: string;
  title: string;
  category: string;
  sport: string;
  duration: number;
  difficulty: string;
  description: string;
}

const LESSON_CATEGORY_CONFIG: Record<string, { color: string; icon: string }> = {
  Fundamentals: { color: '#F97316', icon: 'school-outline' },
  Drills: { color: '#F97316', icon: 'fitness-outline' },
  Tactics: { color: '#F97316', icon: 'bulb-outline' },
  Recovery: { color: '#F97316', icon: 'leaf-outline' },
};

export default function SportScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [query, setQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const categories = ['All', 'Fundamentals', 'Drills', 'Tactics', 'Recovery'];

  useEffect(() => {
    fetchLessons();
  }, []);

  const fetchLessons = async () => {
    try {
      setLoading(true);
      const data = await api.get<Lesson[]>('/lessons');
      setLessons(data || []);
    } catch (error) {
      console.error('Error fetching lessons:', error);
      setLessons([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchLessons();
    setRefreshing(false);
  };

  const categoryFilteredLessons = selectedCategory === 'All'
    ? lessons
    : lessons.filter(l => l.category === selectedCategory);

  const filteredLessons = query.trim()
    ? categoryFilteredLessons.filter((lesson) =>
      [lesson.title, lesson.category, lesson.sport, lesson.difficulty, lesson.description]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query.trim().toLowerCase()))
    )
    : categoryFilteredLessons;

  const groupedLessons = filteredLessons.reduce((acc, lesson) => {
    const sport = lesson.sport;
    if (!acc[sport]) acc[sport] = [];
    acc[sport].push(lesson);
    return acc;
  }, {} as Record<string, Lesson[]>);

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color={colors.textPrimary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>VK</Text>
            </View>
            <Text style={styles.headerTitle}>Sport</Text>
          </View>
          <TouchableOpacity style={styles.headerButton}>
            <Ionicons name="bookmark-outline" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
        </View>

        <View style={styles.searchContainer}>
          <Ionicons name="search-outline" size={18} color="#9CA3AF" />
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search"
            placeholderTextColor="#9CA3AF"
            style={styles.searchInput}
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoriesScroll}
          style={styles.categoriesContainer}
        >
          {categories.map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[
                styles.categoryChip,
                selectedCategory === cat && styles.categoryChipActive,
              ]}
              onPress={() => setSelectedCategory(cat)}
            >
              <Text
                style={[
                  styles.categoryChipText,
                  selectedCategory === cat && styles.categoryChipTextActive,
                ]}
              >
                {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {Object.keys(groupedLessons).length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No lessons yet</Text>
            <Text style={styles.emptySubtitle}>Lessons for your sports will appear here.</Text>
          </View>
        ) : (
          Object.entries(groupedLessons).map(([sport, sportLessons]) => (
            <View key={sport} style={styles.section}>
              <Text style={styles.sectionTitle}>{sport}</Text>
              <Text style={styles.sectionDescription}>Recommended lessons and drills for you.</Text>
              {sportLessons.map((lesson) => (
                <LessonRow
                  key={lesson.id}
                  lesson={lesson}
                  onPress={() => router.push({
                    pathname: '/sport/lesson' as any,
                    params: {
                      id: lesson.id,
                      title: lesson.title,
                      category: lesson.category,
                      sport: lesson.sport,
                      duration: String(lesson.duration || 0),
                      difficulty: lesson.difficulty,
                      description: lesson.description || '',
                    },
                  })}
                />
              ))}
            </View>
          ))
        )}

        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

function LessonRow({ lesson, onPress }: { lesson: Lesson; onPress: () => void }) {
  const category = LESSON_CATEGORY_CONFIG[lesson.category] || LESSON_CATEGORY_CONFIG.Fundamentals;

  return (
    <TouchableOpacity style={styles.lessonRow} activeOpacity={0.7} onPress={onPress}>
      <View style={[styles.thumb, { backgroundColor: category.color + '22' }]}>
        <Ionicons name={category.icon as any} size={22} color={category.color} />
        <View style={[styles.categoryPill, { backgroundColor: category.color + '16' }]}>
          <Text style={[styles.categoryPillText, { color: category.color }]}>{lesson.category}</Text>
        </View>
      </View>
      <View style={styles.rowContent}>
        <Text style={styles.rowTitle} numberOfLines={2}>{lesson.title}</Text>
        <Text style={styles.rowMeta} numberOfLines={1}>
          {lesson.difficulty} · {lesson.sport} · {lesson.category}
        </Text>
        <Text style={styles.rowDuration}>{lesson.duration} min</Text>
      </View>
      <View style={styles.bookmarkButton}>
        <Ionicons name="bookmark-outline" size={18} color="#9CA3AF" />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.lg,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#E5E7EB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  headerButton: {
    padding: spacing.xs,
  },
  content: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: spacing.md,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: colors.textPrimary,
  },
  categoriesContainer: {
    marginBottom: spacing.xl,
  },
  categoriesScroll: {
    gap: spacing.sm,
  },
  categoryChip: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 22,
  },
  categoryChipActive: {
    backgroundColor: '#111111',
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  categoryChipTextActive: {
    color: '#FFFFFF',
  },
  section: {
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 6,
  },
  sectionDescription: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: spacing.lg,
    lineHeight: 19,
  },
  lessonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.05)',
  },
  thumb: {
    width: 78,
    height: 78,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    overflow: 'hidden',
  },
  categoryPill: {
    position: 'absolute',
    left: 7,
    right: 7,
    bottom: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  categoryPillText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#6B7280',
    textAlign: 'center',
  },
  rowContent: {
    flex: 1,
  },
  rowTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  rowMeta: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  rowDuration: {
    fontSize: 12,
    color: '#6B7280',
  },
  bookmarkButton: {
    padding: 6,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#6B7280',
  },
});

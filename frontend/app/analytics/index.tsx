import React, { useState, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    ActivityIndicator,
    Dimensions,
    Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../src/components/GlassCard';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

const { width } = Dimensions.get('window');

type AnalyticsType = 'workout' | 'food';

interface AnalyticsData {
    workout: {
        totalWorkouts: number;
        totalDuration: number;
        avgDuration: number;
    } | null;
    food: {
        avgCalories: number;
        avgProtein: number;
        avgCarbs: number;
        avgFat: number;
        avgFiber: number;
        daysLogged: number;
    } | null;
}

const ANALYTICS_OPTIONS: { id: AnalyticsType; label: string; icon: string; color: string }[] = [
    { id: 'workout', label: 'Workout', icon: 'fitness-outline', color: '#F59E0B' },
    { id: 'food', label: 'Food', icon: 'restaurant-outline', color: '#10B981' },
];

export default function AnalyticsScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    // State
    const [selectedType, setSelectedType] = useState<AnalyticsType>('workout');
    const [dropdownVisible, setDropdownVisible] = useState(false);
    const [loading, setLoading] = useState(true);
    const [analytics, setAnalytics] = useState<AnalyticsData>({
        workout: null,
        food: null,
    });

    // Fetch analytics data
    const fetchAnalytics = async () => {
        setLoading(true);
        try {
            // Fetch all analytics in parallel
            const [workoutsRes, nutritionRes] = await Promise.all([
                api.get('/training/history').catch(() => []),
                api.get('/nutrition/daily-summary').catch(() => null),
            ]);

            // Process workout data
            const workouts = ((workoutsRes as any[]) || []).filter((workout: any) => workout.status === 'complete');
            const workoutData = {
                totalWorkouts: workouts.length,
                totalDuration: workouts.reduce((sum: number, w: any) => sum + Number(w.estimated_minutes || 0), 0),
                avgDuration: workouts.length > 0
                    ? Math.round(workouts.reduce((sum: number, w: any) => sum + Number(w.estimated_minutes || 0), 0) / workouts.length)
                    : 0,
            };

            // Process food data
            const nutrition = nutritionRes as any;
            const foodData = nutrition ? {
                avgCalories: nutrition.calories_kcal || 0,
                avgProtein: nutrition.protein_g || 0,
                avgCarbs: nutrition.carbohydrate_g || 0,
                avgFat: nutrition.fat_g || 0,
                avgFiber: nutrition.fibre_g || 0,
                daysLogged: nutrition.meals?.length ? 1 : 0,
            } : null;

            setAnalytics({
                workout: workoutData,
                food: foodData,
            });
        } catch (error) {
            console.error('Error fetching analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchAnalytics();
        }, [])
    );

    // Get current option
    const currentOption = ANALYTICS_OPTIONS.find(o => o.id === selectedType)!;

    // Render stat card
    const renderStatCard = (label: string, value: string | number, unit?: string, color?: string) => (
        <View style={styles.statCard}>
            <Text style={[styles.statValue, color ? { color } : {}]}>
                {value}{unit && <Text style={styles.statUnit}>{unit}</Text>}
            </Text>
            <Text style={styles.statLabel}>{label}</Text>
        </View>
    );

    // Render workout analytics
    const renderWorkoutAnalytics = () => {
        const data = analytics.workout;
        if (!data || data.totalWorkouts === 0) {
            return (
                <View style={styles.emptyState}>
                    <Text style={styles.emptyIcon}>💪</Text>
                    <Text style={styles.emptyText}>No workout data yet</Text>
                    <Text style={styles.emptySubtext}>Complete workouts to see analytics</Text>
                </View>
            );
        }

        return (
            <>
                {/* Main Stats */}
                <View style={styles.statsGrid}>
                    {renderStatCard('Total Workouts', data.totalWorkouts, '', '#F59E0B')}
                    {renderStatCard('Total Time', data.totalDuration, ' min', '#F59E0B')}
                    {renderStatCard('Avg Duration', data.avgDuration, ' min')}
                    {renderStatCard('Completed Sessions', data.totalWorkouts)}
                </View>
            </>
        );
    };

    // Render food analytics
    const renderFoodAnalytics = () => {
        const data = analytics.food;
        if (!data) {
            return (
                <View style={styles.emptyState}>
                    <Text style={styles.emptyIcon}>🍽️</Text>
                    <Text style={styles.emptyText}>No nutrition data yet</Text>
                    <Text style={styles.emptySubtext}>Log your meals to see analytics</Text>
                </View>
            );
        }

        return (
            <>
                {/* Calories Card */}
                <GlassCard style={styles.mainCard}>
                    <View style={styles.caloriesContainer}>
                        <Text style={styles.caloriesValue}>{data.avgCalories}</Text>
                        <Text style={styles.caloriesLabel}>Calories Today</Text>
                    </View>
                </GlassCard>

                {/* Macros */}
                <GlassCard style={styles.sectionCard}>
                    <Text style={styles.sectionTitle}>Macronutrients</Text>
                    <Text style={styles.sectionTitle}>Confirmed totals for today</Text>
                </GlassCard>

                {/* Stats Grid */}
                <View style={styles.statsGrid}>
                    {renderStatCard('Protein', `${data.avgProtein}`, 'g', '#10B981')}
                    {renderStatCard('Carbs', `${data.avgCarbs}`, 'g', '#3B82F6')}
                    {renderStatCard('Fat', `${data.avgFat}`, 'g', '#F59E0B')}
                    {renderStatCard('Fiber', `${data.avgFiber}`, 'g', '#8B5CF6')}
                </View>
            </>
        );
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Analytics</Text>
                <View style={{ width: 44 }} />
            </View>

            {/* Dropdown Selector */}
            <TouchableOpacity
                style={styles.dropdown}
                onPress={() => setDropdownVisible(true)}
            >
                <Ionicons name={currentOption.icon as any} size={20} color={currentOption.color} />
                <Text style={styles.dropdownText}>{currentOption.label}</Text>
                <Ionicons name="chevron-down" size={20} color={colors.textSecondary} />
            </TouchableOpacity>

            {/* Content */}
            <ScrollView
                style={styles.content}
                contentContainerStyle={styles.contentContainer}
                showsVerticalScrollIndicator={false}
            >
                {loading ? (
                    <ActivityIndicator size="large" color={colors.accentOrange} style={{ marginTop: 60 }} />
                ) : (
                    <>
                        {selectedType === 'workout' && renderWorkoutAnalytics()}
                        {selectedType === 'food' && renderFoodAnalytics()}
                    </>
                )}

                <View style={{ height: 100 }} />
            </ScrollView>

            {/* Dropdown Modal */}
            <Modal
                visible={dropdownVisible}
                transparent
                animationType="fade"
                onRequestClose={() => setDropdownVisible(false)}
            >
                <TouchableOpacity
                    style={styles.modalOverlay}
                    activeOpacity={1}
                    onPress={() => setDropdownVisible(false)}
                >
                    <View style={styles.dropdownMenu}>
                        {ANALYTICS_OPTIONS.map((option) => (
                            <TouchableOpacity
                                key={option.id}
                                style={[
                                    styles.dropdownOption,
                                    selectedType === option.id && styles.dropdownOptionSelected
                                ]}
                                onPress={() => {
                                    setSelectedType(option.id);
                                    setDropdownVisible(false);
                                }}
                            >
                                <Ionicons name={option.icon as any} size={20} color={option.color} />
                                <Text style={[
                                    styles.dropdownOptionText,
                                    selectedType === option.id && styles.dropdownOptionTextSelected
                                ]}>
                                    {option.label}
                                </Text>
                                {selectedType === option.id && (
                                    <Ionicons name="checkmark" size={20} color={colors.accentOrange} />
                                )}
                            </TouchableOpacity>
                        ))}
                    </View>
                </TouchableOpacity>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.md,
    },
    backButton: {
        width: 44,
        height: 44,
        justifyContent: 'center',
    },
    headerTitle: {
        ...typography.h3,
        color: colors.textPrimary,
    },
    dropdown: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.surface,
        marginHorizontal: spacing.lg,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.lg,
        gap: spacing.sm,
    },
    dropdownText: {
        ...typography.body,
        color: colors.textPrimary,
        flex: 1,
        fontWeight: '600',
    },
    content: {
        flex: 1,
    },
    contentContainer: {
        padding: spacing.lg,
    },
    // Stats Grid
    statsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
        marginBottom: spacing.md,
    },
    statCard: {
        width: (width - spacing.lg * 2 - spacing.sm) / 2,
        backgroundColor: colors.surface,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
        alignItems: 'center',
    },
    statValue: {
        fontSize: 28,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    statUnit: {
        fontSize: 14,
        fontWeight: '400',
        color: colors.textSecondary,
    },
    statLabel: {
        ...typography.caption,
        color: colors.textSecondary,
        marginTop: 4,
    },
    // Main Card (Score/Calories)
    mainCard: {
        marginBottom: spacing.md,
        alignItems: 'center',
        paddingVertical: spacing.xl,
    },
    // Calories
    caloriesContainer: {
        alignItems: 'center',
    },
    caloriesValue: {
        fontSize: 56,
        fontWeight: '700',
        color: '#10B981',
    },
    caloriesLabel: {
        ...typography.body,
        color: colors.textSecondary,
    },
    // Section Card
    sectionCard: {
        marginBottom: spacing.md,
        padding: spacing.md,
    },
    sectionTitle: {
        ...typography.body,
        fontWeight: '600',
        color: colors.textPrimary,
        marginBottom: spacing.md,
    },
    // Progress Bars
    progressItem: {
        marginBottom: spacing.md,
    },
    progressHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 6,
    },
    progressLabel: {
        ...typography.caption,
        color: colors.textSecondary,
    },
    progressValue: {
        ...typography.caption,
        color: colors.textPrimary,
    },
    progressBar: {
        height: 8,
        backgroundColor: colors.background,
        borderRadius: 4,
        overflow: 'hidden',
    },
    progressFill: {
        height: '100%',
        borderRadius: 4,
    },
    // Streak
    streakContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.md,
    },
    streakEmoji: {
        fontSize: 40,
    },
    streakValue: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    streakLabel: {
        ...typography.caption,
        color: colors.textSecondary,
    },
    // Empty State
    emptyState: {
        alignItems: 'center',
        paddingVertical: spacing.xl * 2,
    },
    emptyIcon: {
        fontSize: 64,
        marginBottom: spacing.md,
    },
    emptyText: {
        ...typography.h4,
        color: colors.textPrimary,
        marginBottom: spacing.xs,
    },
    emptySubtext: {
        ...typography.body,
        color: colors.textSecondary,
    },
    // Modal
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'flex-start',
        paddingTop: 150,
    },
    dropdownMenu: {
        marginHorizontal: spacing.lg,
        backgroundColor: colors.surface,
        borderRadius: borderRadius.lg,
        overflow: 'hidden',
    },
    dropdownOption: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: spacing.md,
        gap: spacing.sm,
        borderBottomWidth: 1,
        borderBottomColor: colors.separator,
    },
    dropdownOptionSelected: {
        backgroundColor: colors.background,
    },
    dropdownOptionText: {
        ...typography.body,
        color: colors.textPrimary,
        flex: 1,
    },
    dropdownOptionTextSelected: {
        fontWeight: '600',
    },
});

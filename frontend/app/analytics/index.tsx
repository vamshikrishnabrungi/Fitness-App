import React, { useState, useEffect, useCallback } from 'react';
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

type AnalyticsType = 'sleep' | 'workout' | 'food';

interface AnalyticsData {
    sleep: {
        avgScore: number;
        avgDuration: number;
        avgDeep: number;
        avgRem: number;
        totalSessions: number;
        sleepDebt: number;
    } | null;
    workout: {
        totalWorkouts: number;
        totalDuration: number;
        avgDuration: number;
        caloriesBurned: number;
        streak: number;
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
    { id: 'sleep', label: 'Sleep', icon: 'moon-outline', color: '#6366F1' },
    { id: 'workout', label: 'Workout', icon: 'fitness-outline', color: '#F59E0B' },
    { id: 'food', label: 'Food', icon: 'restaurant-outline', color: '#10B981' },
];

export default function AnalyticsScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    // State
    const [selectedType, setSelectedType] = useState<AnalyticsType>('sleep');
    const [dropdownVisible, setDropdownVisible] = useState(false);
    const [loading, setLoading] = useState(true);
    const [analytics, setAnalytics] = useState<AnalyticsData>({
        sleep: null,
        workout: null,
        food: null,
    });

    // Fetch analytics data
    const fetchAnalytics = async () => {
        setLoading(true);
        try {
            // Fetch all analytics in parallel
            const [sleepRes, workoutsRes, nutritionRes] = await Promise.all([
                api.get('/sleep/stats').catch(() => null),
                api.get('/workouts').catch(() => []),
                api.get('/daily-summary').catch(() => null),
            ]);

            // Process sleep data
            const sleepData = sleepRes ? {
                avgScore: (sleepRes as any).avg_score || 0,
                avgDuration: (sleepRes as any).avg_duration || 0,
                avgDeep: (sleepRes as any).avg_deep_sleep || 0,
                avgRem: (sleepRes as any).avg_rem_sleep || 0,
                totalSessions: (sleepRes as any).total_sessions || 0,
                sleepDebt: (sleepRes as any).sleep_debt?.total_debt_hours || 0,
            } : null;

            // Process workout data
            const workouts = workoutsRes as any[] || [];
            const workoutData = {
                totalWorkouts: workouts.length,
                totalDuration: workouts.reduce((sum: number, w: any) => sum + (w.duration || 0), 0),
                avgDuration: workouts.length > 0
                    ? Math.round(workouts.reduce((sum: number, w: any) => sum + (w.duration || 0), 0) / workouts.length)
                    : 0,
                caloriesBurned: workouts.reduce((sum: number, w: any) => sum + (w.calories_burned || 0), 0),
                streak: 0, // Could calculate from dates
            };

            // Process food data
            const nutrition = nutritionRes as any;
            const foodData = nutrition ? {
                avgCalories: nutrition.total_calories || 0,
                avgProtein: nutrition.total_protein || 0,
                avgCarbs: nutrition.total_carbs || 0,
                avgFat: nutrition.total_fat || 0,
                avgFiber: nutrition.total_fiber || 0,
                daysLogged: 1, // Today
            } : null;

            setAnalytics({
                sleep: sleepData,
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

    // Render progress bar
    const renderProgressBar = (label: string, value: number, max: number, color: string) => {
        const percent = Math.min((value / max) * 100, 100);
        return (
            <View style={styles.progressItem}>
                <View style={styles.progressHeader}>
                    <Text style={styles.progressLabel}>{label}</Text>
                    <Text style={styles.progressValue}>{value.toFixed(1)} / {max}</Text>
                </View>
                <View style={styles.progressBar}>
                    <View style={[styles.progressFill, { width: `${percent}%`, backgroundColor: color }]} />
                </View>
            </View>
        );
    };

    // Render sleep analytics
    const renderSleepAnalytics = () => {
        const data = analytics.sleep;
        if (!data) {
            return (
                <View style={styles.emptyState}>
                    <Text style={styles.emptyIcon}>😴</Text>
                    <Text style={styles.emptyText}>No sleep data yet</Text>
                    <Text style={styles.emptySubtext}>Start tracking your sleep to see analytics</Text>
                </View>
            );
        }

        return (
            <>
                {/* Score Card */}
                <GlassCard style={styles.mainCard}>
                    <View style={styles.scoreContainer}>
                        <View style={styles.scoreCircle}>
                            <Text style={styles.scoreValue}>{data.avgScore}</Text>
                            <Text style={styles.scoreLabel}>Avg Score</Text>
                        </View>
                    </View>
                    <View style={styles.scoreStats}>
                        <View style={styles.scoreStat}>
                            <Text style={styles.scoreStatValue}>{data.avgDuration.toFixed(1)}h</Text>
                            <Text style={styles.scoreStatLabel}>Avg Duration</Text>
                        </View>
                        <View style={styles.scoreStat}>
                            <Text style={styles.scoreStatValue}>{data.totalSessions}</Text>
                            <Text style={styles.scoreStatLabel}>Sessions</Text>
                        </View>
                        <View style={styles.scoreStat}>
                            <Text style={styles.scoreStatValue}>{data.sleepDebt.toFixed(1)}h</Text>
                            <Text style={styles.scoreStatLabel}>Sleep Debt</Text>
                        </View>
                    </View>
                </GlassCard>

                {/* Sleep Stages */}
                <GlassCard style={styles.sectionCard}>
                    <Text style={styles.sectionTitle}>Sleep Stages</Text>
                    {renderProgressBar('Deep Sleep', data.avgDeep, 25, '#6366F1')}
                    {renderProgressBar('REM Sleep', data.avgRem, 25, '#8B5CF6')}
                    {renderProgressBar('Light Sleep', 100 - data.avgDeep - data.avgRem, 60, '#A78BFA')}
                </GlassCard>
            </>
        );
    };

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
                    {renderStatCard('Calories Burned', data.caloriesBurned, ' cal')}
                </View>

                {/* Streak Card */}
                <GlassCard style={styles.sectionCard}>
                    <View style={styles.streakContainer}>
                        <Text style={styles.streakEmoji}>🔥</Text>
                        <View>
                            <Text style={styles.streakValue}>{data.streak} Day Streak</Text>
                            <Text style={styles.streakLabel}>Keep it going!</Text>
                        </View>
                    </View>
                </GlassCard>
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
                    {renderProgressBar('Protein', data.avgProtein, 150, '#10B981')}
                    {renderProgressBar('Carbs', data.avgCarbs, 250, '#3B82F6')}
                    {renderProgressBar('Fat', data.avgFat, 65, '#F59E0B')}
                    {renderProgressBar('Fiber', data.avgFiber, 30, '#8B5CF6')}
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
                        {selectedType === 'sleep' && renderSleepAnalytics()}
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
    scoreContainer: {
        marginBottom: spacing.lg,
    },
    scoreCircle: {
        width: 120,
        height: 120,
        borderRadius: 60,
        backgroundColor: '#6366F1',
        alignItems: 'center',
        justifyContent: 'center',
    },
    scoreValue: {
        fontSize: 40,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    scoreLabel: {
        fontSize: 12,
        color: 'rgba(255,255,255,0.8)',
    },
    scoreStats: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        width: '100%',
    },
    scoreStat: {
        alignItems: 'center',
    },
    scoreStatValue: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    scoreStatLabel: {
        ...typography.caption,
        color: colors.textSecondary,
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

/* eslint-disable react/no-unescaped-entities */
import React, { useState, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    Alert,
    ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../src/components/GlassCard';
import { Button } from '../../src/components/Button';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

interface CoachRequest {
    id: string;
    coach_id: string;
    coach_name: string;
    message?: string;
    created_at: string;
}

interface CoachWorkout {
    id: string;
    title: string;
    description?: string;
    workout_type: string;
    difficulty: string;
    duration: number;
    scheduled_date?: string;
    is_completed: boolean;
}

interface CoachMeal {
    id: string;
    title: string;
    description?: string;
    meal_type: string;
    total_calories: number;
}

interface CoachGoal {
    id: string;
    title: string;
    description?: string;
    goal_type: string;
    target_value?: number;
    current_value?: number;
    unit?: string;
    is_completed: boolean;
}

type TabType = 'requests' | 'workouts' | 'meals' | 'goals';

export default function MyCoachScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<TabType>('workouts');

    const [pendingRequests, setPendingRequests] = useState<CoachRequest[]>([]);
    const [workouts, setWorkouts] = useState<CoachWorkout[]>([]);
    const [meals, setMeals] = useState<CoachMeal[]>([]);
    const [goals, setGoals] = useState<CoachGoal[]>([]);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [requestsData, workoutsData, mealsData, goalsData] = await Promise.all([
                api.get<CoachRequest[]>('/client/pending-requests').catch(() => []),
                api.get<CoachWorkout[]>('/my-coach-workouts').catch(() => []),
                api.get<CoachMeal[]>('/my-coach-meals').catch(() => []),
                api.get<CoachGoal[]>('/my-coach-goals').catch(() => []),
            ]);

            setPendingRequests(requestsData);
            setWorkouts(workoutsData);
            setMeals(mealsData);
            setGoals(goalsData);
        } catch (error) {
            console.error('Error fetching coach data:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useFocusEffect(
        useCallback(() => {
            fetchData();
        }, [fetchData])
    );

    const respondToRequest = async (requestId: string, approve: boolean) => {
        try {
            await api.post(`/client/respond-request/${requestId}?approve=${approve}`);
            Alert.alert('Success', approve ? 'Coach connected!' : 'Request declined');
            fetchData();
        } catch (error) {
            console.error('Error responding to coach request:', error);
            Alert.alert('Error', 'Failed to respond to request');
        }
    };

    const completeWorkout = async (workoutId: string) => {
        try {
            await api.post(`/coach/workouts/${workoutId}/complete`);
            Alert.alert('Success', 'Workout marked as completed!');
            fetchData();
        } catch (error) {
            console.error('Error completing workout:', error);
            Alert.alert('Error', 'Failed to complete workout');
        }
    };

    const tabs: { key: TabType; label: string; icon: string; count: number }[] = [
        { key: 'workouts', label: 'Workouts', icon: 'barbell-outline', count: workouts.filter(w => !w.is_completed).length },
        { key: 'meals', label: 'Meals', icon: 'restaurant-outline', count: meals.length },
        { key: 'goals', label: 'Goals', icon: 'flag-outline', count: goals.filter(g => !g.is_completed).length },
        { key: 'requests', label: 'Requests', icon: 'mail-outline', count: pendingRequests.length },
    ];

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.title}>From My Coach</Text>
                <View style={{ width: 44 }} />
            </View>

            {/* Tabs */}
            <View style={styles.tabsContainer}>
                {tabs.map((tab) => (
                    <TouchableOpacity
                        key={tab.key}
                        style={[styles.tab, activeTab === tab.key && styles.tabActive]}
                        onPress={() => setActiveTab(tab.key)}
                    >
                        <Ionicons
                            name={tab.icon as any}
                            size={20}
                            color={activeTab === tab.key ? '#FFFFFF' : colors.textTertiary}
                        />
                        <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
                            {tab.label}
                        </Text>
                        {tab.count > 0 && (
                            <View style={styles.tabBadge}>
                                <Text style={styles.tabBadgeText}>{tab.count}</Text>
                            </View>
                        )}
                    </TouchableOpacity>
                ))}
            </View>

            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 40 }]}
                showsVerticalScrollIndicator={false}
            >
                {loading ? (
                    <ActivityIndicator size="large" color={colors.accentOrange} style={{ marginTop: 60 }} />
                ) : (
                    <>
                        {/* Pending Requests Tab */}
                        {activeTab === 'requests' && (
                            <View>
                                {pendingRequests.length === 0 ? (
                                    <GlassCard style={styles.emptyCard}>
                                        <Ionicons name="mail-outline" size={48} color={colors.textTertiary} />
                                        <Text style={styles.emptyText}>No pending requests</Text>
                                    </GlassCard>
                                ) : (
                                    pendingRequests.map((request) => (
                                        <GlassCard key={request.id} style={styles.requestCard}>
                                            <View style={styles.requestHeader}>
                                                <View style={styles.requestAvatar}>
                                                    <Ionicons name="person" size={24} color={colors.textTertiary} />
                                                </View>
                                                <View style={styles.requestInfo}>
                                                    <Text style={styles.requestName}>{request.coach_name}</Text>
                                                    <Text style={styles.requestLabel}>wants to coach you</Text>
                                                </View>
                                            </View>
                                            {request.message && (
                                                <Text style={styles.requestMessage}>"{request.message}"</Text>
                                            )}
                                            <View style={styles.requestActions}>
                                                <TouchableOpacity
                                                    style={styles.declineButton}
                                                    onPress={() => respondToRequest(request.id, false)}
                                                >
                                                    <Text style={styles.declineText}>Decline</Text>
                                                </TouchableOpacity>
                                                <TouchableOpacity
                                                    style={styles.acceptButton}
                                                    onPress={() => respondToRequest(request.id, true)}
                                                >
                                                    <Text style={styles.acceptText}>Accept</Text>
                                                </TouchableOpacity>
                                            </View>
                                        </GlassCard>
                                    ))
                                )}
                            </View>
                        )}

                        {/* Workouts Tab */}
                        {activeTab === 'workouts' && (
                            <View>
                                {workouts.length === 0 ? (
                                    <GlassCard style={styles.emptyCard}>
                                        <Ionicons name="barbell-outline" size={48} color={colors.textTertiary} />
                                        <Text style={styles.emptyText}>No workouts assigned</Text>
                                        <Text style={styles.emptySubtext}>Your coach will assign workouts here</Text>
                                    </GlassCard>
                                ) : (
                                    workouts.map((workout) => (
                                        <GlassCard key={workout.id} style={styles.itemCard}>
                                            <View style={styles.itemHeader}>
                                                <View style={[styles.itemIcon, { backgroundColor: colors.goalWorkout }]}>
                                                    <Ionicons name="barbell-outline" size={20} color={colors.statusWarning} />
                                                </View>
                                                <View style={styles.itemInfo}>
                                                    <Text style={styles.itemTitle}>{workout.title}</Text>
                                                    <Text style={styles.itemMeta}>
                                                        {workout.workout_type} • {workout.difficulty} • {workout.duration} min
                                                    </Text>
                                                </View>
                                                {workout.is_completed && (
                                                    <Ionicons name="checkmark-circle" size={24} color={colors.statusSuccess} />
                                                )}
                                            </View>
                                            {workout.description && (
                                                <Text style={styles.itemDescription}>{workout.description}</Text>
                                            )}
                                            {!workout.is_completed && (
                                                <Button
                                                    title="Mark Complete"
                                                    onPress={() => completeWorkout(workout.id)}
                                                    variant="primary"
                                                    fullWidth
                                                    style={styles.completeButton}
                                                />
                                            )}
                                        </GlassCard>
                                    ))
                                )}
                            </View>
                        )}

                        {/* Meals Tab */}
                        {activeTab === 'meals' && (
                            <View>
                                {meals.length === 0 ? (
                                    <GlassCard style={styles.emptyCard}>
                                        <Ionicons name="restaurant-outline" size={48} color={colors.textTertiary} />
                                        <Text style={styles.emptyText}>No meal plans assigned</Text>
                                        <Text style={styles.emptySubtext}>Your coach will assign meals here</Text>
                                    </GlassCard>
                                ) : (
                                    meals.map((meal) => (
                                        <GlassCard key={meal.id} style={styles.itemCard}>
                                            <View style={styles.itemHeader}>
                                                <View style={[styles.itemIcon, { backgroundColor: '#E8F5E9' }]}>
                                                    <Ionicons name="restaurant-outline" size={20} color={colors.statusSuccess} />
                                                </View>
                                                <View style={styles.itemInfo}>
                                                    <Text style={styles.itemTitle}>{meal.title}</Text>
                                                    <Text style={styles.itemMeta}>
                                                        {meal.meal_type} • {meal.total_calories} cal
                                                    </Text>
                                                </View>
                                            </View>
                                            {meal.description && (
                                                <Text style={styles.itemDescription}>{meal.description}</Text>
                                            )}
                                        </GlassCard>
                                    ))
                                )}
                            </View>
                        )}

                        {/* Goals Tab */}
                        {activeTab === 'goals' && (
                            <View>
                                {goals.length === 0 ? (
                                    <GlassCard style={styles.emptyCard}>
                                        <Ionicons name="flag-outline" size={48} color={colors.textTertiary} />
                                        <Text style={styles.emptyText}>No goals set</Text>
                                        <Text style={styles.emptySubtext}>Your coach will set goals here</Text>
                                    </GlassCard>
                                ) : (
                                    goals.map((goal) => (
                                        <GlassCard key={goal.id} style={styles.itemCard}>
                                            <View style={styles.itemHeader}>
                                                <View style={[styles.itemIcon, { backgroundColor: '#E3F2FD' }]}>
                                                    <Ionicons name="flag-outline" size={20} color={colors.accentBlue} />
                                                </View>
                                                <View style={styles.itemInfo}>
                                                    <Text style={styles.itemTitle}>{goal.title}</Text>
                                                    <Text style={styles.itemMeta}>
                                                        {goal.goal_type.replace('_', ' ')}
                                                        {goal.target_value && ` • Target: ${goal.target_value} ${goal.unit || ''}`}
                                                    </Text>
                                                </View>
                                                {goal.is_completed && (
                                                    <Ionicons name="checkmark-circle" size={24} color={colors.statusSuccess} />
                                                )}
                                            </View>
                                            {goal.description && (
                                                <Text style={styles.itemDescription}>{goal.description}</Text>
                                            )}
                                            {goal.current_value !== undefined && goal.target_value && (
                                                <View style={styles.progressContainer}>
                                                    <View style={styles.progressBar}>
                                                        <View
                                                            style={[
                                                                styles.progressFill,
                                                                { width: `${Math.min((goal.current_value / goal.target_value) * 100, 100)}%` }
                                                            ]}
                                                        />
                                                    </View>
                                                    <Text style={styles.progressText}>
                                                        {goal.current_value} / {goal.target_value} {goal.unit}
                                                    </Text>
                                                </View>
                                            )}
                                        </GlassCard>
                                    ))
                                )}
                            </View>
                        )}
                    </>
                )}
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
    title: {
        ...typography.h3,
        color: colors.textPrimary,
    },
    tabsContainer: {
        flexDirection: 'row',
        paddingHorizontal: spacing.lg,
        marginBottom: spacing.md,
    },
    tab: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.md,
        gap: spacing.xs,
    },
    tabActive: {
        backgroundColor: colors.accentOrange,
    },
    tabText: {
        ...typography.caption,
        color: colors.textTertiary,
    },
    tabTextActive: {
        color: '#FFFFFF',
        fontWeight: '600',
    },
    tabBadge: {
        backgroundColor: '#E85A4A',
        borderRadius: 10,
        minWidth: 18,
        height: 18,
        alignItems: 'center',
        justifyContent: 'center',
        paddingHorizontal: 4,
    },
    tabBadgeText: {
        color: '#FFFFFF',
        fontSize: 11,
        fontWeight: '700',
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        paddingHorizontal: spacing.lg,
        paddingTop: spacing.md,
    },
    emptyCard: {
        alignItems: 'center',
        paddingVertical: spacing.xxxl,
    },
    emptyText: {
        ...typography.h4,
        color: colors.textSecondary,
        marginTop: spacing.lg,
    },
    emptySubtext: {
        ...typography.caption,
        color: colors.textTertiary,
        marginTop: spacing.xs,
    },
    // Request Card
    requestCard: {
        marginBottom: spacing.md,
    },
    requestHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    requestAvatar: {
        width: 48,
        height: 48,
        borderRadius: 24,
        backgroundColor: colors.separator,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: spacing.md,
    },
    requestInfo: {
        flex: 1,
    },
    requestName: {
        ...typography.body,
        fontWeight: '600',
        color: colors.textPrimary,
    },
    requestLabel: {
        ...typography.caption,
        color: colors.textTertiary,
    },
    requestMessage: {
        ...typography.body,
        color: colors.textSecondary,
        fontStyle: 'italic',
        marginBottom: spacing.md,
    },
    requestActions: {
        flexDirection: 'row',
        gap: spacing.md,
    },
    declineButton: {
        flex: 1,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.md,
        backgroundColor: colors.separator,
        alignItems: 'center',
    },
    declineText: {
        ...typography.body,
        color: colors.textSecondary,
    },
    acceptButton: {
        flex: 1,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.md,
        backgroundColor: colors.accentOrange,
        alignItems: 'center',
    },
    acceptText: {
        ...typography.body,
        color: '#FFFFFF',
        fontWeight: '600',
    },
    // Item Card (Workouts, Meals, Goals)
    itemCard: {
        marginBottom: spacing.md,
    },
    itemHeader: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    itemIcon: {
        width: 40,
        height: 40,
        borderRadius: 20,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: spacing.md,
    },
    itemInfo: {
        flex: 1,
    },
    itemTitle: {
        ...typography.body,
        fontWeight: '600',
        color: colors.textPrimary,
    },
    itemMeta: {
        ...typography.caption,
        color: colors.textTertiary,
    },
    itemDescription: {
        ...typography.body,
        color: colors.textSecondary,
        marginTop: spacing.sm,
    },
    completeButton: {
        marginTop: spacing.md,
    },
    progressContainer: {
        marginTop: spacing.md,
    },
    progressBar: {
        height: 8,
        backgroundColor: colors.separator,
        borderRadius: 4,
        overflow: 'hidden',
        marginBottom: spacing.xs,
    },
    progressFill: {
        height: '100%',
        backgroundColor: colors.accentOrange,
        borderRadius: 4,
    },
    progressText: {
        ...typography.caption,
        color: colors.textSecondary,
        textAlign: 'right',
    },
});

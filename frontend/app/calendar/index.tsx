import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    ActivityIndicator,
    Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../src/components/GlassCard';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

const { width } = Dimensions.get('window');

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

interface DayLog {
    meals: any[];
    workouts: any[];
    sleepSessions: any[];
    moods: any[];
    water: number;
}

export default function CalendarScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    // Calendar state
    const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
    const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());

    // Data state
    const [loading, setLoading] = useState(false);
    const [dayLogs, setDayLogs] = useState<DayLog | null>(null);

    // Fetch logs for selected date
    const fetchDayLogs = async (date: Date) => {
        setLoading(true);
        try {
            const dateStr = date.toISOString().split('T')[0];

            // Fetch all data in parallel
            const [mealsRes, workoutsRes, sleepRes, moodsRes] = await Promise.all([
                api.get(`/daily-summary?date=${dateStr}`).catch(() => ({ meals: [] })),
                api.get('/workouts').catch(() => []),
                api.get('/sleep/sessions').catch(() => []),
                api.get('/mood').catch(() => []),
            ]);

            // Filter by date
            const filterByDate = (items: any[], dateField: string = 'created_at') => {
                return items.filter((item: any) => {
                    const source = item[dateField] || item.timestamp || item.start_time || item.created_at;
                    const itemDate = new Date(source);
                    return itemDate.toISOString().split('T')[0] === dateStr;
                });
            };

            setDayLogs({
                meals: (mealsRes as any)?.meals || [],
                workouts: filterByDate(workoutsRes as any[] || []),
                sleepSessions: filterByDate(sleepRes as any[] || []),
                moods: filterByDate(moodsRes as any[] || [], 'timestamp'),
                water: (mealsRes as any)?.water_intake || 0,
            });
        } catch (error) {
            console.error('Error fetching day logs:', error);
            setDayLogs(null);
        } finally {
            setLoading(false);
        }
    };

    // Fetch on date change
    useEffect(() => {
        fetchDayLogs(selectedDate);
    }, [selectedDate]);

    // Calendar helpers
    const getDaysInMonth = (month: number, year: number) => {
        return new Date(year, month + 1, 0).getDate();
    };

    const getFirstDayOfMonth = (month: number, year: number) => {
        return new Date(year, month, 1).getDay();
    };

    const goToPrevMonth = () => {
        if (currentMonth === 0) {
            setCurrentMonth(11);
            setCurrentYear(currentYear - 1);
        } else {
            setCurrentMonth(currentMonth - 1);
        }
    };

    const goToNextMonth = () => {
        if (currentMonth === 11) {
            setCurrentMonth(0);
            setCurrentYear(currentYear + 1);
        } else {
            setCurrentMonth(currentMonth + 1);
        }
    };

    const selectDate = (day: number) => {
        const date = new Date(currentYear, currentMonth, day);
        setSelectedDate(date);
    };

    const isToday = (day: number) => {
        const today = new Date();
        return day === today.getDate() &&
            currentMonth === today.getMonth() &&
            currentYear === today.getFullYear();
    };

    const isSelected = (day: number) => {
        return day === selectedDate.getDate() &&
            currentMonth === selectedDate.getMonth() &&
            currentYear === selectedDate.getFullYear();
    };

    const formatSelectedDate = () => {
        const today = new Date();
        if (selectedDate.toDateString() === today.toDateString()) {
            return 'Today';
        }
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        if (selectedDate.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        }
        return selectedDate.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
        });
    };

    // Render calendar grid
    const renderCalendarGrid = () => {
        const daysInMonth = getDaysInMonth(currentMonth, currentYear);
        const firstDay = getFirstDayOfMonth(currentMonth, currentYear);
        const days = [];

        // Empty cells for days before first of month
        for (let i = 0; i < firstDay; i++) {
            days.push(<View key={`empty-${i}`} style={styles.calendarDay} />);
        }

        // Days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const today = isToday(day);
            const selected = isSelected(day);

            days.push(
                <TouchableOpacity
                    key={day}
                    style={[
                        styles.calendarDay,
                        today && styles.calendarDayToday,
                        selected && styles.calendarDaySelected,
                    ]}
                    onPress={() => selectDate(day)}
                >
                    <Text style={[
                        styles.calendarDayText,
                        today && styles.calendarDayTextToday,
                        selected && styles.calendarDayTextSelected,
                    ]}>
                        {day}
                    </Text>
                </TouchableOpacity>
            );
        }

        return days;
    };

    // Render log section
    const renderLogSection = (title: string, icon: string, items: any[], renderItem: (item: any) => React.ReactNode) => {
        if (items.length === 0) return null;

        return (
            <View style={styles.logSection}>
                <View style={styles.logHeader}>
                    <Ionicons name={icon as any} size={20} color={colors.accentOrange} />
                    <Text style={styles.logTitle}>{title}</Text>
                    <Text style={styles.logCount}>{items.length}</Text>
                </View>
                {items.map((item, index) => (
                    <View key={item.id || index} style={styles.logItem}>
                        {renderItem(item)}
                    </View>
                ))}
            </View>
        );
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Calendar</Text>
                <View style={{ width: 44 }} />
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
                {/* Calendar */}
                <GlassCard style={styles.calendarCard}>
                    {/* Month Navigation */}
                    <View style={styles.monthNav}>
                        <TouchableOpacity onPress={goToPrevMonth}>
                            <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
                        </TouchableOpacity>
                        <Text style={styles.monthTitle}>
                            {MONTHS[currentMonth]} {currentYear}
                        </Text>
                        <TouchableOpacity onPress={goToNextMonth}>
                            <Ionicons name="chevron-forward" size={24} color={colors.textPrimary} />
                        </TouchableOpacity>
                    </View>

                    {/* Day Headers */}
                    <View style={styles.dayHeaders}>
                        {DAYS.map(day => (
                            <Text key={day} style={styles.dayHeader}>{day}</Text>
                        ))}
                    </View>

                    {/* Calendar Grid */}
                    <View style={styles.calendarGrid}>
                        {renderCalendarGrid()}
                    </View>
                </GlassCard>

                {/* Selected Date Logs */}
                <View style={styles.logsContainer}>
                    <Text style={styles.selectedDateTitle}>{formatSelectedDate()}</Text>

                    {loading ? (
                        <ActivityIndicator size="large" color={colors.accentOrange} style={{ marginTop: 40 }} />
                    ) : dayLogs ? (
                        <>
                            {/* Meals */}
                            {renderLogSection('Meals', 'restaurant-outline', dayLogs.meals, (meal) => (
                                <View style={styles.mealItem}>
                                    <View style={styles.mealInfo}>
                                        <Text style={styles.mealName}>{meal.name}</Text>
                                        <Text style={styles.mealType}>{meal.meal_type}</Text>
                                    </View>
                                    <Text style={styles.mealCalories}>{meal.calories} cal</Text>
                                </View>
                            ))}

                            {/* Workouts */}
                            {renderLogSection('Workouts', 'fitness-outline', dayLogs.workouts, (workout) => (
                                <View style={styles.workoutItem}>
                                    <Text style={styles.workoutName}>{workout.name || 'Workout'}</Text>
                                    <Text style={styles.workoutDuration}>{workout.duration} min</Text>
                                </View>
                            ))}

                            {/* Sleep */}
                            {renderLogSection('Sleep', 'moon-outline', dayLogs.sleepSessions, (sleep) => (
                                <View style={styles.sleepItem}>
                                    <View style={styles.sleepInfo}>
                                        <Text style={styles.sleepScore}>
                                            {sleep.pre_sleep_mood || 'Tracked sleep'}
                                        </Text>
                                        <Text style={styles.sleepMeta}>
                                            {sleep.alarm_time || 'No alarm'} • {sleep.pre_sleep_activities?.length || 0} activities
                                        </Text>
                                    </View>
                                    <Text style={styles.sleepDuration}>
                                        {(sleep.duration_hours != null
                                            ? sleep.duration_hours
                                            : sleep.start_time && sleep.end_time
                                                ? (new Date(sleep.end_time).getTime() - new Date(sleep.start_time).getTime()) / (1000 * 60 * 60)
                                                : 0
                                        ).toFixed(1)}h
                                    </Text>
                                </View>
                            ))}

                            {/* Moods */}
                            {renderLogSection('Moods', 'happy-outline', dayLogs.moods, (mood) => (
                                <View style={styles.moodItem}>
                                    <Text style={styles.moodEmoji}>{mood.mood_emoji}</Text>
                                    <Text style={styles.moodNote}>{mood.note || 'No note'}</Text>
                                </View>
                            ))}

                            {/* Water */}
                            {dayLogs.water > 0 && (
                                <View style={styles.logSection}>
                                    <View style={styles.logHeader}>
                                        <Ionicons name="water-outline" size={20} color={colors.accentTeal} />
                                        <Text style={styles.logTitle}>Water Intake</Text>
                                    </View>
                                    <Text style={styles.waterAmount}>{dayLogs.water} glasses</Text>
                                </View>
                            )}

                            {/* Empty state */}
                            {dayLogs.meals.length === 0 &&
                                dayLogs.workouts.length === 0 &&
                                dayLogs.sleepSessions.length === 0 &&
                                dayLogs.moods.length === 0 &&
                                dayLogs.water === 0 && (
                                    <View style={styles.emptyState}>
                                        <Text style={styles.emptyIcon}>📅</Text>
                                        <Text style={styles.emptyText}>No logs for this day</Text>
                                    </View>
                                )}
                        </>
                    ) : (
                        <View style={styles.emptyState}>
                            <Text style={styles.emptyIcon}>📅</Text>
                            <Text style={styles.emptyText}>Select a date to view logs</Text>
                        </View>
                    )}
                </View>

                <View style={{ height: 100 }} />
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
    headerTitle: {
        ...typography.h3,
        color: colors.textPrimary,
    },
    calendarCard: {
        marginHorizontal: spacing.lg,
        marginTop: spacing.md,
        padding: spacing.md,
    },
    monthNav: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    monthTitle: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    dayHeaders: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: spacing.sm,
    },
    dayHeader: {
        width: (width - 80) / 7,
        textAlign: 'center',
        ...typography.caption,
        color: colors.textSecondary,
        fontWeight: '600',
    },
    calendarGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
    },
    calendarDay: {
        width: (width - 80) / 7,
        height: 40,
        alignItems: 'center',
        justifyContent: 'center',
    },
    calendarDayToday: {
        borderRadius: 20,
        borderWidth: 1,
        borderColor: colors.accentOrange,
    },
    calendarDaySelected: {
        backgroundColor: colors.accentOrange,
        borderRadius: 20,
    },
    calendarDayText: {
        ...typography.body,
        color: colors.textPrimary,
    },
    calendarDayTextToday: {
        color: colors.accentOrange,
        fontWeight: '600',
    },
    calendarDayTextSelected: {
        color: '#FFFFFF',
        fontWeight: '600',
    },
    logsContainer: {
        padding: spacing.lg,
    },
    selectedDateTitle: {
        ...typography.h3,
        color: colors.textPrimary,
        marginBottom: spacing.lg,
    },
    logSection: {
        backgroundColor: colors.surface,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
        marginBottom: spacing.md,
    },
    logHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.sm,
    },
    logTitle: {
        ...typography.body,
        fontWeight: '600',
        color: colors.textPrimary,
        marginLeft: spacing.sm,
        flex: 1,
    },
    logCount: {
        ...typography.caption,
        color: colors.textSecondary,
        backgroundColor: colors.background,
        paddingHorizontal: spacing.sm,
        paddingVertical: 2,
        borderRadius: 10,
    },
    logItem: {
        paddingVertical: spacing.sm,
        borderBottomWidth: 1,
        borderBottomColor: colors.separator,
    },
    // Meal styles
    mealItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    mealInfo: {
        flex: 1,
    },
    mealName: {
        ...typography.body,
        color: colors.textPrimary,
    },
    mealType: {
        ...typography.caption,
        color: colors.textSecondary,
    },
    mealCalories: {
        ...typography.body,
        fontWeight: '600',
        color: colors.accentOrange,
    },
    // Workout styles
    workoutItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    workoutName: {
        ...typography.body,
        color: colors.textPrimary,
    },
    workoutDuration: {
        ...typography.body,
        color: colors.textSecondary,
    },
    // Sleep styles
    sleepItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    sleepInfo: {
        flex: 1,
        paddingRight: spacing.sm,
    },
    sleepScore: {
        ...typography.body,
        color: colors.textPrimary,
    },
    sleepMeta: {
        ...typography.caption,
        color: colors.textSecondary,
        marginTop: 2,
    },
    sleepDuration: {
        ...typography.body,
        fontWeight: '600',
        color: colors.accentBlue,
    },
    // Mood styles
    moodItem: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    moodEmoji: {
        fontSize: 24,
        marginRight: spacing.sm,
    },
    moodNote: {
        ...typography.body,
        color: colors.textSecondary,
    },
    // Water
    waterAmount: {
        ...typography.h4,
        color: colors.accentTeal,
    },
    // Empty state
    emptyState: {
        alignItems: 'center',
        paddingVertical: spacing.xl,
    },
    emptyIcon: {
        fontSize: 48,
        marginBottom: spacing.md,
    },
    emptyText: {
        ...typography.body,
        color: colors.textSecondary,
    },
});

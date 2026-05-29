import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../utils/theme';
import { CardContainer, CardHeader, CardFooter, EmptyState } from './HomeCard';

interface QuickLogData {
    mood?: number;
    energy?: number;
    stress?: number;
    sleep_rating?: number;
    notes?: string;
}

interface QuickLogCardProps {
    todayLog?: QuickLogData | null;
    onComplete?: (data: QuickLogData) => void;
}

const MOODS = [
    { value: 1, emoji: '😫', label: 'Rough', color: '#EF4444' },
    { value: 2, emoji: '😔', label: 'Low', color: '#F59E0B' },
    { value: 3, emoji: '😐', label: 'Okay', color: '#9E9E9E' },
    { value: 4, emoji: '🙂', label: 'Good', color: '#22C55E' },
    { value: 5, emoji: '😄', label: 'Great', color: '#22C55E' },
];

const ENERGY_LEVELS = ['Low', 'Moderate', 'High'];
const STRESS_LEVELS = ['Low', 'Moderate', 'High'];

/**
 * QuickLogCard - Morning Check-in (simplified < 10 second flow)
 */
export function QuickLogCard({ todayLog, onComplete }: QuickLogCardProps) {
    const [selectedMood, setSelectedMood] = useState<number | null>(null);
    const [selectedEnergy, setSelectedEnergy] = useState<number | null>(null);
    const [selectedStress, setSelectedStress] = useState<number | null>(null);
    const [showMore, setShowMore] = useState(false);
    const [sleepRating, setSleepRating] = useState(0);

    const hasLoggedToday = todayLog?.mood != null;

    const handleComplete = () => {
        if (selectedMood !== null && selectedEnergy !== null && selectedStress !== null) {
            onComplete?.({
                mood: selectedMood,
                energy: selectedEnergy,
                stress: selectedStress,
                sleep_rating: sleepRating > 0 ? sleepRating : undefined,
            });
        }
    };

    const isComplete = selectedMood !== null && selectedEnergy !== null && selectedStress !== null;

    // Show completed state
    if (hasLoggedToday) {
        const loggedMood = MOODS.find(m => m.value === todayLog?.mood);
        return (
            <CardContainer>
                <View style={styles.completedHeader}>
                    <View style={styles.headerLeft}>
                        <View style={styles.iconContainer}>
                            <Ionicons name="sunny-outline" size={18} color="#F59E0B" />
                        </View>
                        <View>
                            <Text style={styles.title}>Morning Check-in</Text>
                            <Text style={styles.completedText}>Completed today</Text>
                        </View>
                    </View>
                    <View style={styles.completedBadge}>
                        <Ionicons name="checkmark" size={12} color="#FFFFFF" />
                    </View>
                </View>
                <View style={styles.summaryRow}>
                    <View style={styles.summaryItem}>
                        <Text style={styles.summaryLabel}>Mood</Text>
                        <Text style={styles.summaryEmoji}>{loggedMood?.emoji || '🙂'}</Text>
                    </View>
                    <View style={styles.summaryDivider} />
                    <View style={styles.summaryItem}>
                        <Text style={styles.summaryLabel}>Energy</Text>
                        <Text style={styles.summaryValue}>{ENERGY_LEVELS[todayLog?.energy ?? 1]}</Text>
                    </View>
                    <View style={styles.summaryDivider} />
                    <View style={styles.summaryItem}>
                        <Text style={styles.summaryLabel}>Stress</Text>
                        <Text style={styles.summaryValue}>{STRESS_LEVELS[todayLog?.stress ?? 1]}</Text>
                    </View>
                </View>
            </CardContainer>
        );
    }

    return (
        <CardContainer>
            <View style={styles.header}>
                <View style={styles.headerLeft}>
                    <View style={styles.iconContainer}>
                        <Ionicons name="sunny-outline" size={18} color="#F59E0B" />
                    </View>
                    <Text style={styles.title}>Morning Check-in</Text>
                </View>
            </View>

            <Text style={styles.prompt}>How are you feeling today?</Text>

            {/* Mood Row */}
            <View style={styles.moodRow}>
                {MOODS.map((mood) => (
                    <TouchableOpacity
                        key={mood.value}
                        style={[
                            styles.moodButton,
                            selectedMood === mood.value && { backgroundColor: mood.color + '20', borderColor: mood.color },
                        ]}
                        onPress={() => setSelectedMood(mood.value)}
                    >
                        <Text style={styles.moodEmoji}>{mood.emoji}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Energy & Stress - 3 options each */}
            <View style={styles.quickRow}>
                <View style={styles.quickColumn}>
                    <Text style={styles.quickLabel}>Energy</Text>
                    <View style={styles.pillRow}>
                        {ENERGY_LEVELS.map((level, i) => (
                            <TouchableOpacity
                                key={i}
                                style={[styles.pill, selectedEnergy === i && styles.pillActive]}
                                onPress={() => setSelectedEnergy(i)}
                            >
                                <Text style={[styles.pillText, selectedEnergy === i && styles.pillTextActive]}>
                                    {level}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>
                <View style={styles.quickColumn}>
                    <Text style={styles.quickLabel}>Stress</Text>
                    <View style={styles.pillRow}>
                        {STRESS_LEVELS.map((level, i) => (
                            <TouchableOpacity
                                key={i}
                                style={[styles.pill, selectedStress === i && styles.pillActive]}
                                onPress={() => setSelectedStress(i)}
                            >
                                <Text style={[styles.pillText, selectedStress === i && styles.pillTextActive]}>
                                    {level}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>
            </View>

            {/* Optional: Add more (sleep) */}
            {!showMore ? (
                <TouchableOpacity style={styles.addMoreButton} onPress={() => setShowMore(true)}>
                    <Ionicons name="add-circle-outline" size={16} color={colors.textSecondary} />
                    <Text style={styles.addMoreText}>Add sleep rating</Text>
                </TouchableOpacity>
            ) : (
                <View style={styles.sleepSection}>
                    <Text style={styles.quickLabel}>Sleep Quality</Text>
                    <View style={styles.starsRow}>
                        {[1, 2, 3, 4, 5].map((i) => (
                            <TouchableOpacity key={i} onPress={() => setSleepRating(i)}>
                                <Ionicons
                                    name={i <= sleepRating ? 'star' : 'star-outline'}
                                    size={28}
                                    color={i <= sleepRating ? '#F59E0B' : colors.border}
                                />
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>
            )}

            {/* Complete Button */}
            <TouchableOpacity
                style={[styles.completeButton, !isComplete && styles.completeButtonDisabled]}
                onPress={handleComplete}
                disabled={!isComplete}
            >
                <Ionicons name="checkmark-circle" size={18} color="#FFFFFF" />
                <Text style={styles.completeButtonText}>Complete Check-in</Text>
            </TouchableOpacity>
        </CardContainer>
    );
}

const styles = StyleSheet.create({
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    headerLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    iconContainer: {
        width: 36,
        height: 36,
        borderRadius: 12,
        backgroundColor: '#FEF3C7',
        alignItems: 'center',
        justifyContent: 'center',
    },
    title: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    prompt: {
        fontSize: 14,
        color: colors.textSecondary,
        marginBottom: spacing.md,
    },
    moodRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
    },
    moodButton: {
        width: 52,
        height: 52,
        borderRadius: 16,
        backgroundColor: colors.surfaceSecondary,
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 2,
        borderColor: 'transparent',
    },
    moodEmoji: {
        fontSize: 24,
    },
    quickRow: {
        flexDirection: 'row',
        gap: spacing.lg,
        marginBottom: spacing.md,
    },
    quickColumn: {
        flex: 1,
    },
    quickLabel: {
        fontSize: 12,
        fontWeight: '600',
        color: colors.textSecondary,
        marginBottom: spacing.sm,
    },
    pillRow: {
        flexDirection: 'row',
        gap: 6,
    },
    pill: {
        flex: 1,
        paddingVertical: 8,
        paddingHorizontal: 8,
        borderRadius: 20,
        backgroundColor: colors.surfaceSecondary,
        alignItems: 'center',
    },
    pillActive: {
        backgroundColor: colors.textPrimary,
    },
    pillText: {
        fontSize: 11,
        fontWeight: '600',
        color: colors.textSecondary,
    },
    pillTextActive: {
        color: '#FFFFFF',
    },
    addMoreButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        paddingVertical: spacing.sm,
    },
    addMoreText: {
        fontSize: 13,
        color: colors.textSecondary,
    },
    sleepSection: {
        marginBottom: spacing.md,
    },
    starsRow: {
        flexDirection: 'row',
        gap: spacing.sm,
    },
    completeButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        backgroundColor: '#22C55E',
        paddingVertical: 14,
        borderRadius: 24,
        marginTop: spacing.sm,
    },
    completeButtonDisabled: {
        backgroundColor: colors.textDisabled,
    },
    completeButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    // Completed state
    completedHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    completedText: {
        fontSize: 12,
        color: colors.accentGreen,
        fontWeight: '500',
    },
    completedBadge: {
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: '#22C55E',
        alignItems: 'center',
        justifyContent: 'center',
    },
    summaryRow: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.surfaceSecondary,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
    },
    summaryItem: {
        flex: 1,
        alignItems: 'center',
    },
    summaryDivider: {
        width: 1,
        height: 30,
        backgroundColor: colors.border,
    },
    summaryLabel: {
        fontSize: 11,
        color: colors.textSecondary,
        marginBottom: 4,
    },
    summaryEmoji: {
        fontSize: 24,
    },
    summaryValue: {
        fontSize: 13,
        fontWeight: '600',
        color: colors.textPrimary,
    },
});

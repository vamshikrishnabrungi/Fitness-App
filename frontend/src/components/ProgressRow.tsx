import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, borderRadius } from '../utils/theme';

interface ProgressRowProps {
    xp?: number;
    level?: number;
    streak?: number;
    adherence?: { completed: number; total: number };
}

/**
 * ProgressRow - Subtle gamification row with XP, streak, and program adherence
 */
export function ProgressRow({ xp = 0, level = 1, streak = 0, adherence }: ProgressRowProps) {
    return (
        <View style={styles.container}>
            {/* XP + Level */}
            <View style={styles.item}>
                <View style={[styles.badge, styles.xpBadge]}>
                    <Ionicons name="star" size={12} color="#F59E0B" />
                    <Text style={styles.badgeText}>Lvl {level}</Text>
                </View>
                <Text style={styles.valueText}>{xp} XP</Text>
            </View>

            <View style={styles.divider} />

            {/* Streak */}
            <View style={styles.item}>
                <View style={[styles.badge, styles.streakBadge]}>
                    <Ionicons name="flame" size={12} color="#EF4444" />
                    <Text style={styles.badgeText}>{streak}</Text>
                </View>
                <Text style={styles.valueText}>day streak</Text>
            </View>

            {adherence && (
                <>
                    <View style={styles.divider} />
                    {/* Program adherence */}
                    <View style={styles.item}>
                        <View style={[styles.badge, styles.adherenceBadge]}>
                            <Ionicons name="checkmark-circle" size={12} color={colors.accentGreen} />
                            <Text style={styles.badgeText}>{adherence.completed}/{adherence.total}</Text>
                        </View>
                        <Text style={styles.valueText}>sessions</Text>
                    </View>
                </>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: colors.surfaceSecondary,
        borderRadius: borderRadius.lg,
        paddingVertical: spacing.sm,
        paddingHorizontal: spacing.md,
        gap: spacing.md,
    },
    item: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
    },
    badge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 12,
    },
    xpBadge: {
        backgroundColor: '#FEF3C7',
    },
    streakBadge: {
        backgroundColor: '#FEE2E2',
    },
    adherenceBadge: {
        backgroundColor: colors.accentGreenLight,
    },
    badgeText: {
        fontSize: 11,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    valueText: {
        fontSize: 11,
        color: colors.textSecondary,
    },
    divider: {
        width: 1,
        height: 20,
        backgroundColor: colors.border,
    },
});

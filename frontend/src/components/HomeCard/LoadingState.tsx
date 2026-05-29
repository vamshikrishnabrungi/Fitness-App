import React from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { colors, borderRadius, spacing } from '../../utils/theme';

interface LoadingStateProps {
    variant?: 'card' | 'inline' | 'metric';
}

/**
 * LoadingState - Skeleton shimmer for loading states
 */
export function LoadingState({ variant = 'card' }: LoadingStateProps) {
    if (variant === 'metric') {
        return (
            <View style={styles.metricContainer}>
                <View style={styles.metricIcon} />
                <View style={styles.metricValue} />
                <View style={styles.metricLabel} />
            </View>
        );
    }

    if (variant === 'inline') {
        return (
            <View style={styles.inlineContainer}>
                <View style={styles.inlineCircle} />
                <View style={styles.inlineContent}>
                    <View style={styles.inlineTitle} />
                    <View style={styles.inlineText} />
                </View>
            </View>
        );
    }

    return (
        <View style={styles.cardContainer}>
            <View style={styles.cardHeader}>
                <View style={styles.cardTitle} />
                <View style={styles.cardBadge} />
            </View>
            <View style={styles.cardBody}>
                <View style={styles.cardCircle} />
                <View style={styles.cardContent}>
                    <View style={styles.cardTextLong} />
                    <View style={styles.cardTextShort} />
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    // Card variant
    cardContainer: {
        padding: spacing.xl,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
    },
    cardTitle: {
        width: 100,
        height: 14,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
    },
    cardBadge: {
        width: 60,
        height: 14,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 10,
    },
    cardBody: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    cardCircle: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: colors.surfaceSecondary,
        marginRight: spacing.lg,
    },
    cardContent: {
        flex: 1,
    },
    cardTextLong: {
        width: '100%',
        height: 12,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
        marginBottom: 8,
    },
    cardTextShort: {
        width: '60%',
        height: 12,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
    },
    // Inline variant
    inlineContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: spacing.md,
    },
    inlineCircle: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: colors.surfaceSecondary,
        marginRight: spacing.md,
    },
    inlineContent: {
        flex: 1,
    },
    inlineTitle: {
        width: 120,
        height: 12,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
        marginBottom: 6,
    },
    inlineText: {
        width: 80,
        height: 10,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
    },
    // Metric variant
    metricContainer: {
        alignItems: 'center',
        padding: spacing.sm,
    },
    metricIcon: {
        width: 16,
        height: 16,
        borderRadius: 4,
        backgroundColor: colors.surfaceSecondary,
        marginBottom: 4,
    },
    metricValue: {
        width: 40,
        height: 20,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
        marginBottom: 4,
    },
    metricLabel: {
        width: 50,
        height: 10,
        backgroundColor: colors.surfaceSecondary,
        borderRadius: 4,
    },
});

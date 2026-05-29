import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, spacing } from '../../utils/theme';

type SourceType = 'apple_health' | 'garmin' | 'runs' | 'workouts' | 'manual' | 'demo';

interface SourceChipProps {
    sources: SourceType[];
}

const SOURCE_LABELS: Record<SourceType, string> = {
    apple_health: 'Apple Health',
    garmin: 'Garmin',
    runs: 'Runs',
    workouts: 'Workouts',
    manual: 'Manual logs',
    demo: 'Demo data',
};

/**
 * SourceChip - Shows data source attribution
 * "From: Apple Health" | "From: Runs + Workouts" | "Demo data"
 */
export function SourceChip({ sources }: SourceChipProps) {
    const isDemo = sources.includes('demo');

    const label = isDemo
        ? 'Demo data'
        : `From: ${sources.map(s => SOURCE_LABELS[s]).join(' + ')}`;

    return (
        <View style={[styles.container, isDemo && styles.demoContainer]}>
            <Ionicons
                name={isDemo ? 'flask-outline' : 'link-outline'}
                size={12}
                color={isDemo ? colors.statusWarning : colors.textTertiary}
            />
            <Text style={[styles.text, isDemo && styles.demoText]}>{label}</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        backgroundColor: colors.surfaceSecondary,
        paddingHorizontal: spacing.sm,
        paddingVertical: 4,
        borderRadius: borderRadius.sm,
        alignSelf: 'flex-start',
    },
    demoContainer: {
        backgroundColor: colors.statusWarningBg,
    },
    text: {
        fontSize: 11,
        color: colors.textTertiary,
        fontWeight: '500',
    },
    demoText: {
        color: colors.statusWarning,
    },
});

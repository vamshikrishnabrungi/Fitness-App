import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../utils/theme';

interface MetricTileProps {
    icon: React.ReactNode;
    label: string;
    value: number | string | null | undefined;
    unit?: string;
    delta?: number | null;
    available?: boolean;
    compact?: boolean;
}

/**
 * MetricTile - Displays a single metric with availability state
 * Shows "—" and "Not available" when data is missing
 * NEVER shows "0" for missing data
 */
export function MetricTile({
    icon,
    label,
    value,
    unit = '',
    delta,
    available = true,
    compact = false,
}: MetricTileProps) {
    // Determine if value is missing (null, undefined, or 0 with !available)
    const isMissing = value === null || value === undefined || (value === 0 && !available);

    const displayValue = isMissing ? '—' : String(value);
    const displayUnit = isMissing ? '' : unit;

    // Format delta
    const getDeltaDisplay = () => {
        if (delta === null || delta === undefined || isMissing) return null;
        const threshold = 0.05; // 5% threshold
        if (Math.abs(delta) < threshold) {
            return { text: '→ same', color: colors.textTertiary };
        } else if (delta > 0) {
            return { text: `↑ +${Math.abs(delta).toFixed(0)}`, color: '#22C55E' };
        } else {
            return { text: `↓ ${Math.abs(delta).toFixed(0)}`, color: '#EF4444' };
        }
    };

    const deltaInfo = getDeltaDisplay();

    return (
        <View style={[styles.container, compact && styles.compact]}>
            <View style={styles.header}>
                {icon}
                <Text style={styles.label}>{label}</Text>
            </View>
            <View style={styles.valueRow}>
                <Text style={[styles.value, isMissing && styles.valueMissing]}>
                    {displayValue}
                </Text>
                {displayUnit && <Text style={styles.unit}>{displayUnit}</Text>}
            </View>
            {isMissing ? (
                <Text style={styles.unavailable}>Not available</Text>
            ) : deltaInfo ? (
                <Text style={[styles.delta, { color: deltaInfo.color }]}>{deltaInfo.text}</Text>
            ) : null}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: 'center',
        padding: spacing.sm,
    },
    compact: {
        padding: spacing.xs,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        marginBottom: 4,
    },
    label: {
        fontSize: 11,
        fontWeight: '600',
        color: colors.textSecondary,
    },
    valueRow: {
        flexDirection: 'row',
        alignItems: 'baseline',
    },
    value: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    valueMissing: {
        color: colors.textTertiary,
    },
    unit: {
        fontSize: 11,
        color: colors.textSecondary,
        marginLeft: 2,
    },
    delta: {
        fontSize: 10,
        fontWeight: '600',
        marginTop: 2,
    },
    unavailable: {
        fontSize: 10,
        color: colors.textTertiary,
        marginTop: 2,
    },
});

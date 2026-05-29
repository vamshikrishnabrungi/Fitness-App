import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../utils/theme';

interface RecoveryCardProps {
    data?: {
        score: number | null;
        status: 'low' | 'moderate' | 'high';
        sleep?: { value: number | null; quality?: string };
        hrv?: { value: number | null; unit: string; trend?: 'up' | 'down' | 'stable' };
        rhr?: { value: number | null; unit: string; trend?: 'up' | 'down' | 'stable' };
    } | null;
}

const STATUS_CONFIG = {
    low: { color: '#DC2626', label: 'Low', bg: '#FEE2E2' },
    moderate: { color: '#D97706', label: 'Moderate', bg: '#FEF3C7' },
    high: { color: '#16A34A', label: 'High', bg: '#DCFCE7' },
};

export function RecoveryCard({ data }: RecoveryCardProps) {
    const router = useRouter();
    const config = STATUS_CONFIG[data?.status || 'moderate'];

    const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
        if (trend === 'up') return 'trending-up';
        if (trend === 'down') return 'trending-down';
        return 'remove';
    };

    const getTrendColor = (trend?: 'up' | 'down' | 'stable', isGoodUp = true) => {
        if (!trend || trend === 'stable') return '#9CA3AF';
        if (trend === 'up') return isGoodUp ? '#16A34A' : '#DC2626';
        return isGoodUp ? '#DC2626' : '#16A34A';
    };

    return (
        <TouchableOpacity
            style={styles.container}
            onPress={() => router.push('/analytics/recovery-detail')}
            activeOpacity={0.7}
        >
            {/* Header */}
            <View style={styles.header}>
                <View style={styles.titleRow}>
                    <View style={styles.iconContainer}>
                        <Ionicons name="battery-charging" size={18} color="#8B5CF6" />
                    </View>
                    <Text style={styles.title}>Recovery</Text>
                </View>
                <View style={[styles.statusPill, { backgroundColor: config.bg }]}>
                    <Text style={[styles.statusText, { color: config.color }]}>{config.label}</Text>
                </View>
            </View>

            {/* Score + Metrics Row */}
            <View style={styles.contentRow}>
                {/* Score */}
                <View style={styles.scoreContainer}>
                    <Text style={[styles.scoreValue, { color: config.color }]}>
                        {data?.score ?? '—'}
                    </Text>
                    <Text style={styles.scoreLabel}>%</Text>
                </View>

                {/* Metrics */}
                <View style={styles.metricsContainer}>
                    <MetricRow
                        icon="moon"
                        iconColor="#3B82F6"
                        label="Sleep"
                        value={data?.sleep?.value}
                        unit="hrs"
                    />
                    <MetricRow
                        icon="pulse"
                        iconColor="#8B5CF6"
                        label="HRV"
                        value={data?.hrv?.value}
                        unit="ms"
                        trend={data?.hrv?.trend}
                        trendColor={getTrendColor(data?.hrv?.trend, true)}
                    />
                    <MetricRow
                        icon="heart"
                        iconColor="#DC2626"
                        label="RHR"
                        value={data?.rhr?.value}
                        unit="bpm"
                        trend={data?.rhr?.trend}
                        trendColor={getTrendColor(data?.rhr?.trend, false)}
                    />
                </View>
            </View>

            {/* Footer */}
            <View style={styles.footer}>
                <Text style={styles.footerText}>Learn about recovery</Text>
                <Ionicons name="chevron-forward" size={14} color="#9CA3AF" />
            </View>
        </TouchableOpacity>
    );
}

function MetricRow({
    icon,
    iconColor,
    label,
    value,
    unit,
    trend,
    trendColor,
}: {
    icon: string;
    iconColor: string;
    label: string;
    value?: number | null;
    unit: string;
    trend?: 'up' | 'down' | 'stable';
    trendColor?: string;
}) {
    return (
        <View style={styles.metricRow}>
            <Ionicons name={icon as any} size={14} color={iconColor} />
            <Text style={styles.metricLabel}>{label}</Text>
            <Text style={styles.metricValue}>
                {value ?? '—'} {value && <Text style={styles.metricUnit}>{unit}</Text>}
            </Text>
            {trend && (
                <Ionicons
                    name={trend === 'up' ? 'trending-up' : trend === 'down' ? 'trending-down' : 'remove'}
                    size={12}
                    color={trendColor || '#9CA3AF'}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        padding: spacing.lg,
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.06)',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    titleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    iconContainer: {
        width: 32,
        height: 32,
        borderRadius: 10,
        backgroundColor: '#F3E8FF',
        alignItems: 'center',
        justifyContent: 'center',
    },
    title: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    statusPill: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
    },
    statusText: {
        fontSize: 12,
        fontWeight: '600',
    },
    contentRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    scoreContainer: {
        flexDirection: 'row',
        alignItems: 'baseline',
        marginRight: spacing.xl,
    },
    scoreValue: {
        fontSize: 48,
        fontWeight: '800',
        letterSpacing: -2,
    },
    scoreLabel: {
        fontSize: 18,
        color: '#9CA3AF',
        marginLeft: 2,
    },
    metricsContainer: {
        flex: 1,
        gap: 6,
    },
    metricRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
    },
    metricLabel: {
        fontSize: 12,
        color: '#6B7280',
        width: 36,
    },
    metricValue: {
        fontSize: 13,
        fontWeight: '600',
        color: colors.textPrimary,
        flex: 1,
    },
    metricUnit: {
        fontSize: 11,
        fontWeight: '400',
        color: '#9CA3AF',
    },
    footer: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 4,
        paddingTop: spacing.sm,
        borderTopWidth: 1,
        borderTopColor: 'rgba(0,0,0,0.05)',
    },
    footerText: {
        fontSize: 13,
        color: '#9CA3AF',
    },
});

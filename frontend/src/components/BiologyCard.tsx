import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../utils/theme';

interface BiologyCardProps {
    data?: {
        leanMass?: { value: number | null; unit: string; trend?: 'up' | 'down' | 'stable' };
        bodyFat?: { value: number | null; unit: string; trend?: 'up' | 'down' | 'stable' };
        weight?: { value: number | null; unit: string };
        status?: 'stable' | 'trending_up' | 'needs_update';
        insight?: string;
    } | null;
}

const STATUS_CONFIG = {
    stable: { label: 'Stable', color: '#16A34A', bg: '#DCFCE7' },
    trending_up: { label: 'Trending up', color: '#3B82F6', bg: '#DBEAFE' },
    needs_update: { label: 'Needs update', color: '#D97706', bg: '#FEF3C7' },
};

export function BiologyCard({ data }: BiologyCardProps) {
    const router = useRouter();
    const status = data?.status || 'stable';
    const config = STATUS_CONFIG[status];

    return (
        <TouchableOpacity
            style={styles.container}
            onPress={() => router.push('/health/biology')}
            activeOpacity={0.7}
        >
            {/* Header */}
            <View style={styles.header}>
                <View style={styles.titleRow}>
                    <View style={styles.iconContainer}>
                        <Ionicons name="body" size={18} color="#3B82F6" />
                    </View>
                    <View>
                        <Text style={styles.title}>Biology</Text>
                        <Text style={styles.subtitle}>Body composition</Text>
                    </View>
                </View>
                <View style={[styles.statusPill, { backgroundColor: config.bg }]}>
                    <Text style={[styles.statusText, { color: config.color }]}>{config.label}</Text>
                </View>
            </View>

            {/* Metrics Row */}
            <View style={styles.metricsRow}>
                <BiologyMetric
                    icon="pulse"
                    iconColor="#16A34A"
                    label="Lean Mass"
                    value={data?.leanMass?.value}
                    unit="kg"
                    trend={data?.leanMass?.trend}
                />
                <View style={styles.metricDivider} />
                <BiologyMetric
                    icon="flame"
                    iconColor="#F97316"
                    label="Body Fat"
                    value={data?.bodyFat?.value}
                    unit="%"
                    trend={data?.bodyFat?.trend}
                />
                <View style={styles.metricDivider} />
                <BiologyMetric
                    icon="scale"
                    iconColor="#6B7280"
                    label="Weight"
                    value={data?.weight?.value}
                    unit="kg"
                />
            </View>

            {/* Insight */}
            {data?.insight && (
                <Text style={styles.insight}>{data.insight}</Text>
            )}

            {/* Footer */}
            <View style={styles.footer}>
                <Text style={styles.footerText}>View body metrics</Text>
                <Ionicons name="chevron-forward" size={14} color="#9CA3AF" />
            </View>
        </TouchableOpacity>
    );
}

function BiologyMetric({
    icon,
    iconColor,
    label,
    value,
    unit,
    trend,
}: {
    icon: string;
    iconColor: string;
    label: string;
    value?: number | null;
    unit: string;
    trend?: 'up' | 'down' | 'stable';
}) {
    const getTrendIcon = (t?: 'up' | 'down' | 'stable') => {
        if (t === 'up') return 'caret-up';
        if (t === 'down') return 'caret-down';
        return null;
    };

    return (
        <View style={styles.metric}>
            <View style={styles.metricHeader}>
                <Ionicons name={icon as any} size={14} color={iconColor} />
                <Text style={styles.metricLabel}>{label}</Text>
            </View>
            <View style={styles.metricValueRow}>
                <Text style={styles.metricValue}>
                    {value ?? '—'}
                    {value && <Text style={styles.metricUnit}> {unit}</Text>}
                </Text>
                {trend && getTrendIcon(trend) && (
                    <Ionicons
                        name={getTrendIcon(trend) as any}
                        size={12}
                        color={trend === 'up' ? '#16A34A' : trend === 'down' ? '#DC2626' : '#9CA3AF'}
                    />
                )}
            </View>
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
        alignItems: 'flex-start',
        marginBottom: spacing.md,
    },
    titleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
    },
    iconContainer: {
        width: 36,
        height: 36,
        borderRadius: 12,
        backgroundColor: '#EFF6FF',
        alignItems: 'center',
        justifyContent: 'center',
    },
    title: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    subtitle: {
        fontSize: 12,
        color: '#9CA3AF',
        marginTop: 1,
    },
    statusPill: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
    },
    statusText: {
        fontSize: 11,
        fontWeight: '600',
    },
    metricsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: spacing.md,
    },
    metricDivider: {
        width: 1,
        height: 36,
        backgroundColor: 'rgba(0,0,0,0.06)',
        marginHorizontal: spacing.sm,
    },
    metric: {
        flex: 1,
        alignItems: 'center',
    },
    metricHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        marginBottom: 4,
    },
    metricLabel: {
        fontSize: 11,
        color: '#9CA3AF',
    },
    metricValueRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 2,
    },
    metricValue: {
        fontSize: 18,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    metricUnit: {
        fontSize: 12,
        fontWeight: '400',
        color: '#9CA3AF',
    },
    insight: {
        fontSize: 12,
        color: '#6B7280',
        textAlign: 'center',
        marginBottom: spacing.sm,
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

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../utils/theme';

interface StrainCardProps {
    data?: {
        today: number | null;
        status: 'low' | 'moderate' | 'high';
        weeklyAvg: number | null;
        history?: { day: string; value: number }[];
    } | null;
}

const STATUS_CONFIG = {
    low: { color: '#16A34A', label: 'Low', bg: '#DCFCE7' },
    moderate: { color: '#D97706', label: 'Optimal', bg: '#FEF3C7' },
    high: { color: '#DC2626', label: 'High', bg: '#FEE2E2' },
};

export function StrainCard({ data }: StrainCardProps) {
    const router = useRouter();
    const config = STATUS_CONFIG[data?.status || 'moderate'];

    // Generate 7-day mini chart bars
    const history = data?.history || [];
    const maxValue = Math.max(...history.map(h => h.value), 1);

    return (
        <TouchableOpacity
            style={styles.container}
            onPress={() => router.push('/analytics/load-history')}
            activeOpacity={0.7}
        >
            {/* Header */}
            <View style={styles.header}>
                <View style={styles.titleRow}>
                    <View style={styles.iconContainer}>
                        <Ionicons name="flame" size={18} color="#F97316" />
                    </View>
                    <Text style={styles.title}>Strain</Text>
                </View>
                <View style={[styles.statusPill, { backgroundColor: config.bg }]}>
                    <Text style={[styles.statusText, { color: config.color }]}>{config.label}</Text>
                </View>
            </View>

            {/* Mini Chart */}
            <View style={styles.chartContainer}>
                {history.length > 0 ? (
                    <View style={styles.miniChart}>
                        {history.slice(-7).map((item, i) => (
                            <View key={i} style={styles.barColumn}>
                                <View
                                    style={[
                                        styles.bar,
                                        {
                                            height: Math.max((item.value / maxValue) * 40, 4),
                                            backgroundColor: i === history.length - 1 ? config.color : '#E5E7EB',
                                        },
                                    ]}
                                />
                                <Text style={styles.barLabel}>{item.day.slice(0, 1)}</Text>
                            </View>
                        ))}
                    </View>
                ) : (
                    <View style={styles.noDataChart}>
                        <Text style={styles.noDataText}>No data yet</Text>
                    </View>
                )}
            </View>

            {/* Stats Row */}
            <View style={styles.statsRow}>
                <View style={styles.stat}>
                    <Text style={styles.statValue}>{data?.today ?? '—'}</Text>
                    <Text style={styles.statLabel}>Today</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.stat}>
                    <Text style={styles.statValue}>{data?.weeklyAvg ?? '—'}</Text>
                    <Text style={styles.statLabel}>7-day avg</Text>
                </View>
            </View>

            {/* Footer */}
            <View style={styles.footer}>
                <Text style={styles.footerText}>View strain history</Text>
                <Ionicons name="chevron-forward" size={14} color="#9CA3AF" />
            </View>
        </TouchableOpacity>
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
        backgroundColor: '#FFF7ED',
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
    chartContainer: {
        marginVertical: spacing.md,
    },
    miniChart: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        height: 56,
        paddingTop: 8,
    },
    barColumn: {
        alignItems: 'center',
        flex: 1,
    },
    bar: {
        width: 20,
        borderRadius: 4,
        marginBottom: 4,
    },
    barLabel: {
        fontSize: 10,
        color: '#9CA3AF',
    },
    noDataChart: {
        height: 56,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#F9FAFB',
        borderRadius: 12,
    },
    noDataText: {
        fontSize: 13,
        color: '#9CA3AF',
    },
    statsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingTop: spacing.md,
        borderTopWidth: 1,
        borderTopColor: 'rgba(0,0,0,0.05)',
    },
    stat: {
        flex: 1,
        alignItems: 'center',
    },
    statValue: {
        fontSize: 20,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    statLabel: {
        fontSize: 11,
        color: '#9CA3AF',
        marginTop: 2,
    },
    statDivider: {
        width: 1,
        height: 32,
        backgroundColor: 'rgba(0,0,0,0.08)',
    },
    footer: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 4,
        marginTop: spacing.md,
        paddingTop: spacing.sm,
    },
    footerText: {
        fontSize: 13,
        color: '#9CA3AF',
    },
});

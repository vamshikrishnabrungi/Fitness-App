import React, { useState, useEffect, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    ActivityIndicator,
    Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useFocusEffect } from 'expo-router';
import { api } from '../../src/utils/api';
import { colors, spacing } from '../../src/utils/theme';

interface HealthSummary {
    readiness?: number | null;
    sleep_minutes?: number | null;
    stress?: number | null;
    open_pain_reports: number;
    connected_metrics?: Record<string, {value:number;unit:string;measured_at:string;provider:string}>;
}

interface InjuryLog {
    id: string;
    region_code: string;
    severity: number;
    action: string;
    status: string;
    reported_at: string;
}


interface DataSource {
    provider: string;
    name: string;
    connected: boolean;
    icon: string;
    color: string;
}

const DATA_SOURCES: DataSource[] = [
    { provider: 'apple_health', name: 'Apple Health', connected: false, icon: 'heart-circle', color: '#FF2D55' },
    { provider: 'health_connect', name: 'Health Connect', connected: false, icon: 'fitness', color: '#4285F4' },
];

export default function HealthHubScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [healthSummary, setHealthSummary] = useState<HealthSummary | null>(null);
    const [injuries, setInjuries] = useState<InjuryLog[]>([]);
    const [connections, setConnections] = useState<string[]>([]);

    useEffect(() => {
        fetchData();
    }, []);

    useFocusEffect(
        useCallback(() => {
            fetchData();
        }, [])
    );

    const fetchData = async () => {
        try {
            setLoading(true);
            const [summaryRes, injuriesRes, connectionRes] = await Promise.all([
                api.get<HealthSummary>('/health/summary').catch(() => null),
                api.get<InjuryLog[]>('/health/pain-reports').catch(() => []),
                api.get<{items:{provider:string;status:string}[]}>('/imports/connections').catch(() => ({items:[]})),
            ]);
            setHealthSummary(summaryRes);
            setInjuries(injuriesRes || []);
            setConnections(connectionRes.items.filter(item => item.status === 'active').map(item => item.provider));
        } catch (error) {
            console.error('Error fetching health data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleLogInjury = () => {
        router.push('/health/injury');
    };

    const handleResolveInjury = async (id: string) => {
        try {
            await api.put(`/health/pain-reports/${id}/resolve`);
            fetchData();
        } catch {
            Alert.alert('Error', 'Failed to resolve injury');
        }
    };

    const getSeverityColor = (severity: number) => {
        if (severity >= 8) return '#DC2626';
        if (severity >= 5) return '#D97706';
        return '#16A34A';
    };

    if (loading) {
        return (
            <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
                <ActivityIndicator size="large" color={colors.textPrimary} />
            </View>
        );
    }

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Health Hub</Text>
                <TouchableOpacity onPress={() => router.push('/education/recovery')} style={styles.infoButton}>
                    <Ionicons name="information-circle-outline" size={24} color={colors.textSecondary} />
                </TouchableOpacity>
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                {/* A. Quick Actions */}
                <View style={styles.actionsRow}>
                    <TouchableOpacity
                        style={styles.actionButton}
                        onPress={handleLogInjury}
                    >
                        <Ionicons name="medkit-outline" size={20} color={colors.textPrimary} />
                        <Text style={styles.actionText}>Log Injury</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => router.push('/health/benchmarks' as any)}
                    >
                        <Ionicons name="barbell-outline" size={20} color={colors.textPrimary} />
                        <Text style={styles.actionText}>Baseline Testing</Text>
                    </TouchableOpacity>
                </View>

                {/* C. Vitals Grid */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Vitals</Text>
                    <View style={styles.vitalsGrid}>
                        <VitalCard
                            icon="heart"
                            iconColor="#DC2626"
                            label="Resting HR"
                            value={healthSummary?.connected_metrics?.resting_hr_bpm?.value}
                            unit="bpm"
                            state={healthSummary?.connected_metrics?.resting_hr_bpm ? 'Connected health' : 'Waiting for sync'}
                            onLearnMore={() => router.push('/education/recovery')}
                        />
                        <VitalCard
                            icon="pulse"
                            iconColor="#8B5CF6"
                            label="Sleep"
                            value={healthSummary?.sleep_minutes ? Math.round(healthSummary.sleep_minutes / 6) / 10 : null}
                            unit="h"
                            state="Latest check-in"
                            onLearnMore={() => router.push('/education/recovery')}
                        />
                        <VitalCard
                            icon="body"
                            iconColor="#F59E0B"
                            label="HRV"
                            value={healthSummary?.connected_metrics?.hrv_rmssd_ms?.value}
                            unit="ms"
                            state={healthSummary?.connected_metrics?.hrv_rmssd_ms ? 'Connected health' : 'Waiting for sync'}
                            onLearnMore={() => router.push('/education/biology')}
                        />
                    </View>
                </View>

                {/* D. Injuries Section */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={styles.sectionTitle}>Active Injuries</Text>
                        <TouchableOpacity onPress={handleLogInjury}>
                            <Ionicons name="add-circle-outline" size={24} color={colors.textPrimary} />
                        </TouchableOpacity>
                    </View>

                    {injuries.length === 0 ? (
                        <View style={styles.emptyState}>
                            <Ionicons name="checkmark-circle" size={32} color="#16A34A" />
                            <Text style={styles.emptyText}>No active injuries</Text>
                        </View>
                    ) : (
                        injuries.map((injury) => (
                            <View key={injury.id} style={styles.injuryCard}>
                                <View style={styles.injuryHeader}>
                                    <View style={styles.injuryTitle}>
                                        <View style={[styles.severityDot, { backgroundColor: getSeverityColor(injury.severity) }]} />
                                        <Text style={styles.injuryArea}>{injury.region_code.replaceAll('_', ' ')}</Text>
                                    </View>
                                    <View style={[styles.severityBadge, { backgroundColor: getSeverityColor(injury.severity) + '15' }]}>
                                        <Text style={[styles.severityText, { color: getSeverityColor(injury.severity) }]}>
                                            {injury.severity}/10
                                        </Text>
                                    </View>
                                </View>
                                <View style={styles.injuryDetails}>
                                    <Text style={styles.painScale}>{injury.action.replaceAll('_', ' ')}</Text>
                                    <Text style={styles.injuryDate}>
                                        {new Date(injury.reported_at).toLocaleDateString()}
                                    </Text>
                                </View>
                                <TouchableOpacity
                                    style={styles.resolveButton}
                                    onPress={() => handleResolveInjury(injury.id)}
                                >
                                    <Text style={styles.resolveText}>Mark Resolved</Text>
                                </TouchableOpacity>
                            </View>
                        ))
                    )}
                </View>

                {/* E. Data Sources */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Data Sources</Text>
                    {DATA_SOURCES.map((source) => {
                        const connected = connections.includes(source.provider);
                        return <TouchableOpacity key={source.provider} style={styles.sourceCard} onPress={() => !connected && Alert.alert('Production build required', `${source.name} sync requires native health permissions and explicit connected-health consent.`)}>
                            <Ionicons name={source.icon as any} size={28} color={source.color} />
                            <View style={styles.sourceInfo}>
                                <Text style={styles.sourceName}>{source.name}</Text>
                                <Text style={[styles.sourceStatus, { color: connected ? '#16A34A' : colors.textSecondary }]}>
                                    {connected ? 'Connected' : 'Not connected'}
                                </Text>
                            </View>
                            <Ionicons
                                name={connected ? 'checkmark-circle' : 'add-circle-outline'}
                                size={22}
                                color={connected ? '#16A34A' : colors.textSecondary}
                            />
                        </TouchableOpacity>
                    })}
                </View>

                <View style={{ height: 100 }} />
            </ScrollView>
        </View>
    );
}

// VitalCard Component
function VitalCard({
    icon,
    iconColor,
    label,
    value,
    unit,
    state,
    onLearnMore,
}: {
    icon: string;
    iconColor: string;
    label: string;
    value?: number | null;
    unit: string;
    state: string;
    onLearnMore?: () => void;
}) {
    const hasData = value !== null && value !== undefined && value !== 0;
    const displayValue = hasData ? String(value) : '—';

    return (
        <TouchableOpacity style={styles.vitalCard} onPress={onLearnMore} activeOpacity={0.7}>
            <Ionicons name={icon as any} size={20} color={iconColor} />
            <Text style={styles.vitalValue}>
                {displayValue}
                {hasData && <Text style={styles.vitalUnit}> {unit}</Text>}
            </Text>
            <Text style={styles.vitalLabel}>{label}</Text>
            <Text style={[styles.vitalState, { color: hasData ? colors.textTertiary : '#D97706' }]}>
                {hasData ? state : 'Waiting for sync'}
            </Text>
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#FFFFFF',
    },
    centered: {
        justifyContent: 'center',
        alignItems: 'center',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.md,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(0,0,0,0.08)',
    },
    backButton: {
        padding: spacing.xs,
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    infoButton: {
        padding: spacing.xs,
    },
    content: {
        flex: 1,
        paddingHorizontal: spacing.lg,
    },
    // Actions
    actionsRow: {
        flexDirection: 'row',
        gap: spacing.md,
        paddingVertical: spacing.lg,
    },
    actionButton: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        paddingVertical: 14,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.12)',
    },
    actionText: {
        fontSize: 14,
        fontWeight: '600',
        color: colors.textPrimary,
    },
    // Sections
    section: {
        marginTop: spacing.xl,
    },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    sectionTitle: {
        fontSize: 14,
        fontWeight: '700',
        color: colors.textSecondary,
        letterSpacing: 0.5,
        marginBottom: spacing.md,
    },
    // Vitals
    vitalsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    vitalCard: {
        width: '48%',
        backgroundColor: '#FAFAFA',
        padding: spacing.md,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.05)',
    },
    vitalValue: {
        fontSize: 24,
        fontWeight: '700',
        color: colors.textPrimary,
        marginTop: 8,
    },
    vitalUnit: {
        fontSize: 13,
        fontWeight: '400',
        color: colors.textSecondary,
    },
    vitalLabel: {
        fontSize: 13,
        color: colors.textSecondary,
        marginTop: 2,
    },
    vitalState: {
        fontSize: 11,
        marginTop: 4,
    },
    // Empty state
    emptyState: {
        alignItems: 'center',
        paddingVertical: spacing.xl,
        backgroundColor: '#FAFAFA',
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.05)',
    },
    emptyText: {
        fontSize: 14,
        color: colors.textSecondary,
        marginTop: 8,
    },
    // Injuries
    injuryCard: {
        backgroundColor: '#FAFAFA',
        padding: spacing.md,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.05)',
        marginBottom: spacing.sm,
    },
    injuryHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    injuryTitle: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
    },
    severityDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
    },
    injuryArea: {
        fontSize: 15,
        fontWeight: '600',
        color: colors.textPrimary,
        textTransform: 'capitalize',
    },
    severityBadge: {
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 8,
    },
    severityText: {
        fontSize: 11,
        fontWeight: '600',
    },
    injuryDetails: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 8,
    },
    painScale: {
        fontSize: 13,
        color: colors.textSecondary,
    },
    injuryDate: {
        fontSize: 13,
        color: colors.textTertiary,
    },
    restrictionsRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 6,
        marginBottom: 12,
    },
    restrictionChip: {
        backgroundColor: '#FEE2E2',
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 6,
    },
    restrictionText: {
        fontSize: 11,
        fontWeight: '600',
        color: '#DC2626',
    },
    resolveButton: {
        alignSelf: 'flex-end',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 8,
        backgroundColor: 'rgba(22, 163, 74, 0.1)',
    },
    resolveText: {
        fontSize: 12,
        fontWeight: '600',
        color: '#16A34A',
    },
    // Data sources
    sourceCard: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: spacing.md,
        paddingHorizontal: spacing.md,
        backgroundColor: '#FAFAFA',
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.05)',
        marginBottom: spacing.sm,
        gap: spacing.md,
    },
    sourceInfo: {
        flex: 1,
    },
    sourceName: {
        fontSize: 15,
        fontWeight: '600',
        color: colors.textPrimary,
    },
    sourceStatus: {
        fontSize: 13,
    },
});

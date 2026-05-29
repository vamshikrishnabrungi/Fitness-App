import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Circle } from 'react-native-svg';
import { spacing } from '../../src/utils/theme';

// Mock data
const mockRecoveryData = {
    score: null, // null means no data
    status: 'Recovered',
    restingHRV: null,
    restingHR: null,
    activities: [],
    trends: [
        { key: 'recovery-score', icon: 'fitness-outline', iconColor: '#8B5CF6', label: 'Recovery Score', value: null, status: 'nodata' },
        { key: 'resting-hrv', icon: 'pulse-outline', iconColor: '#8B5CF6', label: 'Resting HRV', value: null, status: 'nodata' },
        { key: 'resting-hr', icon: 'heart', iconColor: '#EF4444', label: 'Resting HR', value: null, status: 'nodata' },
        { key: 'respiratory-rate', icon: 'fitness', iconColor: '#3B82F6', label: 'Respiratory Rate', value: null, status: 'nodata' },
        { key: 'oxygen-saturation', icon: 'water-outline', iconColor: '#06B6D4', label: 'Oxygen Saturation', value: null, status: 'nodata' },
        { key: 'wrist-temperature', icon: 'thermometer-outline', iconColor: '#F97316', label: 'Wrist Temperature', value: null, status: 'nodata' },
    ],
};

// Recovery Ring Component
function RecoveryRing({ score, size = 180 }: { score: number | null; size?: number }) {
    const strokeWidth = 14;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const percentage = score ?? 0;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;
    const center = size / 2;

    const getColor = () => {
        if (score === null) return '#4B5563';
        if (score < 34) return '#EF4444';
        if (score < 67) return '#F59E0B';
        return '#16A34A';
    };

    return (
        <View style={styles.ringContainer}>
            <Svg width={size} height={size}>
                {/* Background circle */}
                <Circle
                    cx={center}
                    cy={center}
                    r={radius}
                    stroke="#374151"
                    strokeWidth={strokeWidth}
                    fill="none"
                />
                {/* Progress arc */}
                {score !== null && (
                    <Circle
                        cx={center}
                        cy={center}
                        r={radius}
                        stroke={getColor()}
                        strokeWidth={strokeWidth}
                        fill="none"
                        strokeDasharray={`${circumference}`}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        rotation="-90"
                        origin={`${center}, ${center}`}
                    />
                )}
            </Svg>
            {/* Center content */}
            <View style={styles.ringCenter}>
                <Text style={styles.ringValue}>{score !== null ? `${score}%` : '—%'}</Text>
                <Text style={styles.ringLabel}>Recovered</Text>
            </View>
        </View>
    );
}

export default function RecoveryDetailScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [refreshing, setRefreshing] = useState(false);
    const [data] = useState(mockRecoveryData);

    const today = new Date();
    const monthDay = today.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

    const onRefresh = async () => {
        setRefreshing(true);
        await new Promise(resolve => setTimeout(resolve, 500));
        setRefreshing(false);
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="chevron-back" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Recovery</Text>
                <TouchableOpacity style={styles.infoButton}>
                    <Ionicons name="information-circle-outline" size={24} color="#9CA3AF" />
                </TouchableOpacity>
            </View>

            {/* Date Selector */}
            <TouchableOpacity style={styles.dateSelector}>
                <Text style={styles.dateText}>Today, {monthDay}</Text>
                <Ionicons name="chevron-down" size={16} color="#9CA3AF" />
            </TouchableOpacity>

            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFFFFF" />
                }
            >
                {/* Recovery Ring */}
                <View style={styles.ringSection}>
                    <RecoveryRing score={data.score} />
                </View>

                {/* Stats Tiles */}
                <View style={styles.statsTiles}>
                    <View style={styles.statTile}>
                        <View style={styles.statHeader}>
                            <Ionicons name="pulse-outline" size={16} color="#8B5CF6" />
                            <Text style={styles.statLabel}>Resting HRV</Text>
                        </View>
                        <Text style={styles.statValue}>
                            {data.restingHRV ?? '—'} <Text style={styles.statUnit}>ms</Text>
                        </Text>
                    </View>
                    <View style={styles.statTile}>
                        <View style={styles.statHeader}>
                            <Ionicons name="heart" size={16} color="#EF4444" />
                            <Text style={styles.statLabel}>Resting HR</Text>
                        </View>
                        <Text style={styles.statValue}>
                            {data.restingHR ?? '—'} <Text style={styles.statUnit}>bpm</Text>
                        </Text>
                    </View>
                </View>

                {/* Action Links */}
                <View style={styles.actionLinks}>
                    <TouchableOpacity style={styles.actionLink}>
                        <Ionicons name="help-circle-outline" size={18} color="#F59E0B" />
                        <Text style={styles.actionLinkText}>Why do I have no data?</Text>
                        <Ionicons name="chevron-forward" size={18} color="#6B7280" />
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.actionLink}>
                        <Ionicons name="sparkles" size={18} color="#8B5CF6" />
                        <Text style={styles.actionLinkText}>View insights</Text>
                        <Ionicons name="chevron-forward" size={18} color="#6B7280" />
                    </TouchableOpacity>
                </View>

                {/* Timeline Section */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Timeline</Text>
                    {data.activities.length === 0 ? (
                        <View style={styles.emptyTimeline}>
                            <Text style={styles.emptyTitle}>No activities</Text>
                            <Text style={styles.emptySubtitle}>There were no activities done this period.</Text>
                        </View>
                    ) : (
                        data.activities.map((activity: any, index: number) => (
                            <View key={index} style={styles.activityRow}>
                                <Text style={styles.activityText}>{activity.name}</Text>
                            </View>
                        ))
                    )}
                </View>

                {/* Trends Section */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Trends</Text>
                    {data.trends.map((trend, index) => (
                        <TouchableOpacity
                            key={index}
                            style={styles.trendCard}
                            onPress={() => router.push(`/analytics/recovery-metric-detail?type=${trend.key}`)}
                        >
                            <View style={styles.trendHeader}>
                                <Ionicons name={trend.icon as any} size={18} color={trend.iconColor} />
                                <Text style={styles.trendLabel}>{trend.label}</Text>
                                <Ionicons name="chevron-forward" size={18} color="#6B7280" />
                            </View>
                            <View style={styles.trendContent}>
                                <Text style={styles.trendValue}>
                                    {trend.value !== null ? trend.value : 'No data'}
                                </Text>
                                <View style={styles.trendStatusRow}>
                                    <Ionicons name="close-circle" size={14} color="#6B7280" />
                                    <Text style={styles.trendStatusText}>No trends available</Text>
                                </View>
                            </View>
                        </TouchableOpacity>
                    ))}
                </View>

                <View style={{ height: 40 }} />
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#FFFFFF',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.md,
    },
    backButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#374151',
        alignItems: 'center',
        justifyContent: 'center',
    },
    headerTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: '#1F2937',
    },
    infoButton: {
        width: 40,
        height: 40,
        alignItems: 'center',
        justifyContent: 'center',
    },
    dateSelector: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        paddingBottom: spacing.md,
    },
    dateText: {
        fontSize: 14,
        color: '#6B7280',
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        paddingHorizontal: spacing.lg,
    },
    // Ring Section
    ringSection: {
        alignItems: 'center',
        paddingVertical: spacing.xl,
        backgroundColor: '#F3F4F6',
        marginHorizontal: -spacing.lg,
        paddingHorizontal: spacing.lg,
    },
    ringContainer: {
        alignItems: 'center',
        justifyContent: 'center',
    },
    ringCenter: {
        position: 'absolute',
        alignItems: 'center',
    },
    ringValue: {
        fontSize: 42,
        fontWeight: '700',
        color: '#4B5563',
    },
    ringLabel: {
        fontSize: 14,
        color: '#9CA3AF',
        marginTop: 2,
    },
    // Stats Tiles
    statsTiles: {
        flexDirection: 'row',
        gap: 12,
        marginVertical: spacing.lg,
    },
    statTile: {
        flex: 1,
        backgroundColor: '#F9FAFB',
        borderRadius: 16,
        padding: spacing.lg,
    },
    statHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 10,
    },
    statLabel: {
        fontSize: 13,
        color: '#6B7280',
    },
    statValue: {
        fontSize: 28,
        fontWeight: '700',
        color: '#1F2937',
    },
    statUnit: {
        fontSize: 14,
        fontWeight: '400',
        color: '#9CA3AF',
    },
    // Action Links
    actionLinks: {
        gap: 1,
        backgroundColor: '#E5E7EB',
        borderRadius: 16,
        overflow: 'hidden',
        marginBottom: spacing.lg,
    },
    actionLink: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        paddingVertical: 16,
        paddingHorizontal: spacing.lg,
        gap: 12,
    },
    actionLinkText: {
        flex: 1,
        fontSize: 15,
        fontWeight: '500',
        color: '#1F2937',
    },
    // Sections
    section: {
        marginBottom: spacing.xl,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#1F2937',
        marginBottom: spacing.md,
    },
    // Empty Timeline
    emptyTimeline: {
        alignItems: 'center',
        paddingVertical: 40,
    },
    emptyTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#6B7280',
    },
    emptySubtitle: {
        fontSize: 13,
        color: '#9CA3AF',
        marginTop: 4,
        textAlign: 'center',
    },
    activityRow: {
        padding: spacing.md,
        backgroundColor: '#F9FAFB',
        borderRadius: 12,
        marginBottom: 8,
    },
    activityText: {
        fontSize: 14,
        color: '#1F2937',
    },
    // Trend Cards
    trendCard: {
        backgroundColor: '#F9FAFB',
        borderRadius: 16,
        padding: spacing.lg,
        marginBottom: 12,
    },
    trendHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: 12,
    },
    trendLabel: {
        flex: 1,
        fontSize: 14,
        color: '#6B7280',
    },
    trendContent: {},
    trendValue: {
        fontSize: 24,
        fontWeight: '700',
        color: '#1F2937',
        marginBottom: 4,
    },
    trendStatusRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    trendStatusText: {
        fontSize: 13,
        color: '#6B7280',
    },
});

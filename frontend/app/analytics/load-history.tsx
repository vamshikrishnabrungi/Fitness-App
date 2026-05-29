import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Circle, Path } from 'react-native-svg';
import { spacing } from '../../src/utils/theme';

// Mock data - replace with API later
const mockStrainData = {
    strainPercent: 1,
    duration: 0,
    totalEnergy: 3485,
    activities: [],
    heartRateZones: [
        { zone: 0, time: '00:00:00', range: '0 – 97 bpm' },
        { zone: 1, time: '00:00:00', range: '98 – 116 bpm' },
        { zone: 2, time: '00:00:00', range: '117 – 136 bpm' },
        { zone: 3, time: '00:00:00', range: '137 – 155 bpm' },
        { zone: 4, time: '00:00:00', range: '156 – 175 bpm' },
        { zone: 5, time: '00:00:00', range: '176 – 194 bpm' },
    ],
    trends: {
        strainScore: { value: 1, status: 'below', data: [2, 3, 1, 4, 2, 5, 3, 2, 1] },
        exerciseDuration: { value: 0, unit: 'm', status: 'normal', progress: 0 },
        daytimeHR: { value: null, status: 'nodata' },
        totalEnergy: { value: 3485, unit: 'kJ', status: 'below', data: [3200, 3400, 3100, 3600, 3485] },
        stepCount: { value: 308, status: 'below', data: [400, 300, 500, 350, 308] },
    },
};

// Strain Ring Component
function StrainRing({ percent, size = 200 }: { percent: number; size?: number }) {
    const strokeWidth = 14;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percent / 100) * circumference;
    const center = size / 2;

    return (
        <View style={styles.ringContainer}>
            <Svg width={size} height={size}>
                {/* Background circle */}
                <Circle
                    cx={center}
                    cy={center}
                    r={radius}
                    stroke="#E5E7EB"
                    strokeWidth={strokeWidth}
                    fill="none"
                />
                {/* Progress arc */}
                <Circle
                    cx={center}
                    cy={center}
                    r={radius}
                    stroke="#F59E0B"
                    strokeWidth={strokeWidth}
                    fill="none"
                    strokeDasharray={`${circumference}`}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    rotation="-90"
                    origin={`${center}, ${center}`}
                />
                {/* Indicator dot at top */}
                <Circle
                    cx={center}
                    cy={strokeWidth / 2 + 1}
                    r={10}
                    fill="#F59E0B"
                />
            </Svg>
            {/* Center content */}
            <View style={styles.ringCenter}>
                <Text style={styles.ringValue}>{percent}%</Text>
                <Text style={styles.ringLabel}>Strain</Text>
            </View>
        </View>
    );
}

// Sparkline Component
function Sparkline({ data, color = '#F97316', width = 120, height = 40 }: { data: number[]; color?: string; width?: number; height?: number }) {
    if (!data || data.length < 2) return null;

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const padding = 6;

    const points = data.map((value, index) => {
        const x = padding + (index / (data.length - 1)) * (width - padding * 2);
        const y = padding + (1 - (value - min) / range) * (height - padding * 2);
        return { x, y };
    });

    let pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
        pathD += ` L ${points[i].x} ${points[i].y}`;
    }

    const lastPoint = points[points.length - 1];

    return (
        <View style={{ width, height }}>
            <Svg width={width} height={height}>
                <Path
                    d={pathD}
                    stroke={color}
                    strokeWidth={2.5}
                    fill="none"
                />
                <Circle
                    cx={lastPoint.x}
                    cy={lastPoint.y}
                    r={5}
                    fill={color}
                />
            </Svg>
        </View>
    );
}

// Progress Line Component
function ProgressLine({ progress, color = '#F59E0B' }: { progress: number; color?: string }) {
    return (
        <View style={styles.progressLineContainer}>
            <View style={[styles.progressLineTrack]}>
                <View style={[styles.progressLine, { width: `${Math.max(progress, 5)}%`, backgroundColor: color }]} />
            </View>
            <View style={[styles.progressDot, { backgroundColor: color }]} />
        </View>
    );
}

export default function LoadHistoryScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [refreshing, setRefreshing] = useState(false);
    const [data, setData] = useState(mockStrainData);

    const today = new Date();
    const monthDay = today.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

    const onRefresh = async () => {
        setRefreshing(true);
        await new Promise(resolve => setTimeout(resolve, 500));
        setRefreshing(false);
    };

    const getStatusColor = (status: string) => {
        if (status === 'below') return '#F97316';
        if (status === 'normal') return '#16A34A';
        return '#9CA3AF';
    };

    const getStatusText = (status: string) => {
        if (status === 'below') return 'Below normal';
        if (status === 'normal') return 'Normal range';
        return 'No data';
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="chevron-back" size={24} color="#1F2937" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Strain</Text>
                <TouchableOpacity style={styles.infoButton}>
                    <Ionicons name="information-circle-outline" size={24} color="#6B7280" />
                </TouchableOpacity>
            </View>

            {/* Date Selector */}
            <TouchableOpacity style={styles.dateSelector}>
                <Text style={styles.dateText}>Today, {monthDay}</Text>
                <Ionicons name="chevron-down" size={16} color="#6B7280" />
            </TouchableOpacity>

            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
            >
                {/* Strain Ring */}
                <View style={styles.ringSection}>
                    <StrainRing percent={data.strainPercent} />
                </View>

                {/* Stats Tiles */}
                <View style={styles.statsTiles}>
                    <View style={styles.statTile}>
                        <View style={styles.statHeader}>
                            <Ionicons name="time-outline" size={16} color="#6B7280" />
                            <Text style={styles.statLabel}>Duration</Text>
                        </View>
                        <Text style={styles.statValue}>{data.duration}m</Text>
                    </View>
                    <View style={styles.statTile}>
                        <View style={styles.statHeader}>
                            <Ionicons name="flash-outline" size={16} color="#6B7280" />
                            <Text style={styles.statLabel}>Total Energy</Text>
                        </View>
                        <View style={styles.statValueRow}>
                            <Text style={styles.statValue}>{data.totalEnergy.toLocaleString()}</Text>
                            <Text style={styles.statUnit}> kJ</Text>
                            <Ionicons name="caret-down" size={14} color="#F97316" style={{ marginLeft: 8 }} />
                        </View>
                    </View>
                </View>

                {/* Timeline Section */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Timeline</Text>
                    {data.activities.length === 0 ? (
                        <View style={styles.emptyTimeline}>
                            <Ionicons name="calendar-outline" size={36} color="#D1D5DB" />
                            <Text style={styles.emptyTitle}>No activities</Text>
                            <Text style={styles.emptySubtitle}>There were no activities done this period.</Text>
                        </View>
                    ) : (
                        data.activities.map((activity: any, index: number) => (
                            <View key={index} style={styles.activityRow}>
                                <Text>{activity.name}</Text>
                            </View>
                        ))
                    )}
                </View>

                {/* Heart Rate Zones */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Heart Rate Zones</Text>
                    <View style={styles.zonesCard}>
                        {data.heartRateZones.map((zone, index) => (
                            <View key={index} style={[styles.zoneRow, index < data.heartRateZones.length - 1 && styles.zoneBorder]}>
                                <Text style={styles.zoneNumber}>{zone.zone}</Text>
                                <Text style={styles.zoneTime}>{zone.time}</Text>
                                <Text style={styles.zoneRange}>{zone.range}</Text>
                            </View>
                        ))}
                    </View>
                </View>

                {/* Trends Section */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Trends</Text>

                    {/* Strain Score Card */}
                    <TouchableOpacity style={styles.trendCard} onPress={() => router.push('/analytics/strain-detail')}>
                        <View style={styles.trendHeader}>
                            <Ionicons name="flame-outline" size={18} color="#F97316" />
                            <Text style={styles.trendLabel}>Strain Score</Text>
                            <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                        </View>
                        <View style={styles.trendContent}>
                            <View>
                                <Text style={styles.trendValue}>{data.trends.strainScore.value}%</Text>
                                <View style={styles.statusRow}>
                                    <View style={[styles.statusDot, { backgroundColor: getStatusColor(data.trends.strainScore.status) }]} />
                                    <Text style={[styles.statusText, { color: getStatusColor(data.trends.strainScore.status) }]}>
                                        {getStatusText(data.trends.strainScore.status)}
                                    </Text>
                                </View>
                            </View>
                            <Sparkline data={data.trends.strainScore.data} color="#F97316" width={130} height={45} />
                        </View>
                    </TouchableOpacity>

                    {/* Exercise Duration Card */}
                    <TouchableOpacity style={styles.trendCard} onPress={() => router.push('/analytics/strain-detail?type=duration')}>
                        <View style={styles.trendHeader}>
                            <Ionicons name="time-outline" size={18} color="#6B7280" />
                            <Text style={styles.trendLabel}>Exercise Duration</Text>
                            <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                        </View>
                        <View style={styles.trendContent}>
                            <View>
                                <Text style={styles.trendValue}>{data.trends.exerciseDuration.value}m</Text>
                                <View style={styles.statusRow}>
                                    <Ionicons name="checkmark-circle" size={14} color="#16A34A" />
                                    <Text style={[styles.statusText, { color: '#16A34A', marginLeft: 4 }]}>Normal range</Text>
                                </View>
                            </View>
                            <View style={styles.progressContainer}>
                                <ProgressLine progress={data.trends.exerciseDuration.progress || 5} color="#F59E0B" />
                            </View>
                        </View>
                    </TouchableOpacity>

                    {/* Daytime HR Card */}
                    <TouchableOpacity style={styles.trendCard} onPress={() => router.push('/analytics/strain-detail?type=daytime-hr')}>
                        <View style={styles.trendHeader}>
                            <Ionicons name="heart" size={18} color="#EF4444" />
                            <Text style={styles.trendLabel}>Daytime HR</Text>
                            <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                        </View>
                        <View style={styles.trendContent}>
                            <View>
                                <Text style={styles.trendValue}>No data</Text>
                                <View style={styles.statusRow}>
                                    <Ionicons name="close-circle" size={14} color="#9CA3AF" />
                                    <Text style={[styles.statusText, { color: '#9CA3AF', marginLeft: 4 }]}>No trends available</Text>
                                </View>
                            </View>
                        </View>
                    </TouchableOpacity>

                    {/* Total Energy Card */}
                    <TouchableOpacity style={styles.trendCard} onPress={() => router.push('/analytics/strain-detail?type=energy')}>
                        <View style={styles.trendHeader}>
                            <Ionicons name="flash" size={18} color="#F97316" />
                            <Text style={styles.trendLabel}>Total Energy</Text>
                            <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                        </View>
                        <View style={styles.trendContent}>
                            <View>
                                <Text style={styles.trendValue}>
                                    {data.trends.totalEnergy.value.toLocaleString()}
                                    <Text style={styles.trendUnit}> kJ</Text>
                                </Text>
                                <View style={styles.statusRow}>
                                    <View style={[styles.statusDot, { backgroundColor: '#F97316' }]} />
                                    <Text style={[styles.statusText, { color: '#F97316' }]}>Below normal</Text>
                                </View>
                            </View>
                            <Sparkline data={data.trends.totalEnergy.data} color="#F97316" width={130} height={45} />
                        </View>
                    </TouchableOpacity>


                    {/* Step Count Card */}
                    <TouchableOpacity style={styles.trendCard} onPress={() => router.push('/analytics/strain-detail?type=steps')}>
                        <View style={styles.trendHeader}>
                            <Ionicons name="footsteps-outline" size={18} color="#F97316" />
                            <Text style={styles.trendLabel}>Step Count</Text>
                            <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                        </View>
                        <View style={styles.trendContent}>
                            <View>
                                <Text style={styles.trendValue}>{data.trends.stepCount.value}</Text>
                                <View style={styles.statusRow}>
                                    <View style={[styles.statusDot, { backgroundColor: '#F97316' }]} />
                                    <Text style={[styles.statusText, { color: '#F97316' }]}>Below normal</Text>
                                </View>
                            </View>
                            <Sparkline data={data.trends.stepCount.data} color="#F97316" width={130} height={45} />
                        </View>
                    </TouchableOpacity>
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
        backgroundColor: '#F3F4F6',
        alignItems: 'center',
        justifyContent: 'center',
    },
    headerTitle: {
        fontSize: 18,
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
        fontSize: 48,
        fontWeight: '700',
        color: '#1F2937',
    },
    ringLabel: {
        fontSize: 16,
        color: '#9CA3AF',
        marginTop: 2,
    },
    // Stats Tiles
    statsTiles: {
        flexDirection: 'row',
        gap: 12,
        marginBottom: spacing.xl,
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
        fontSize: 32,
        fontWeight: '700',
        color: '#1F2937',
    },
    statValueRow: {
        flexDirection: 'row',
        alignItems: 'baseline',
    },
    statUnit: {
        fontSize: 16,
        color: '#6B7280',
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
        marginTop: spacing.md,
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
    // Heart Rate Zones
    zonesCard: {
        backgroundColor: '#F9FAFB',
        borderRadius: 16,
        overflow: 'hidden',
    },
    zoneRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 16,
        paddingHorizontal: spacing.lg,
    },
    zoneBorder: {
        borderBottomWidth: 1,
        borderBottomColor: '#E5E7EB',
    },
    zoneNumber: {
        width: 28,
        fontSize: 16,
        fontWeight: '600',
        color: '#6B7280',
    },
    zoneTime: {
        flex: 1,
        fontSize: 15,
        color: '#9CA3AF',
    },
    zoneRange: {
        fontSize: 13,
        color: '#9CA3AF',
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
        marginBottom: 14,
    },
    trendLabel: {
        flex: 1,
        fontSize: 14,
        color: '#6B7280',
    },
    trendContent: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
    },
    trendValue: {
        fontSize: 32,
        fontWeight: '700',
        color: '#1F2937',
    },
    trendUnit: {
        fontSize: 16,
        fontWeight: '400',
        color: '#6B7280',
    },
    statusRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        marginTop: 6,
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
    },
    statusText: {
        fontSize: 13,
        fontWeight: '500',
    },
    progressContainer: {
        flex: 1,
        maxWidth: 160,
        marginLeft: spacing.lg,
    },
    progressLineContainer: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    progressLineTrack: {
        flex: 1,
        height: 8,
        backgroundColor: '#E5E7EB',
        borderRadius: 4,
    },
    progressLine: {
        height: 8,
        borderRadius: 4,
    },
    progressDot: {
        width: 14,
        height: 14,
        borderRadius: 7,
        marginLeft: -3,
    },
});

import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Path, Circle, Line, Rect, G, Text as SvgText, Defs, LinearGradient, Stop } from 'react-native-svg';
import { spacing } from '../../src/utils/theme';

const { width } = Dimensions.get('window');
const CHART_WIDTH = width - 48;
const CHART_HEIGHT = 200;

type MetricType = 'recovery-score' | 'resting-hrv' | 'resting-hr' | 'respiratory-rate' | 'oxygen-saturation' | 'wrist-temperature';

interface MetricConfig {
    title: string;
    value: string;
    unit: string;
    date: string;
    status: 'above' | 'below' | 'normal' | 'nodata';
    range: string;
    average: string;
    hasData: boolean;
    chartData: { date: string; value: number }[];
    yAxisLabels: string[];
    maxY: number;
    breakdown?: { poor: number; normal: number; optimal: number };
    trends: { period: string; change: string; up: boolean | null; sparkline: number[] }[];
    resources: { title: string; subtitle: string; icon: string; iconColor: string; bgColor: string }[];
    explanation: { title: string; paragraphs: string[] };
}

// Mock data for each metric type
const metricsData: Record<MetricType, MetricConfig> = {
    'recovery-score': {
        title: 'Recovery Score',
        value: '—',
        unit: '%',
        date: 'Jan 1, 2026',
        status: 'nodata',
        range: '',
        average: '',
        hasData: false,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 9', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 24', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['100', '67', '33', '0'],
        maxY: 100,
        breakdown: { poor: 33, normal: 34, optimal: 33 },
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'What is Recovery Score?', subtitle: 'Discover how our Recovery Score evaluates and optimizes your post-wor...', icon: 'fitness', iconColor: '#16A34A', bgColor: '#DCFCE7' },
            { title: 'The Basics: Heart Rate Variability', subtitle: 'Heart rate variability (HRV) offers valuable insights into your ove...', icon: 'pulse', iconColor: '#8B5CF6', bgColor: '#F3E8FF' },
        ],
        explanation: {
            title: 'Recovery Score',
            paragraphs: [
                "Recovery Score measures how ready your body is to handle strain and perform optimally. It's calculated using RHR, HRV, RR, SpO2, and Temperature.",
                "Factors like Strain, stress, and lifestyle choices can all affect your Recovery. This is why you can have a low Recovery even with good sleep, and vice versa."
            ]
        }
    },
    'resting-hrv': {
        title: 'Resting HRV',
        value: '—',
        unit: 'ms',
        date: 'Jan 1, 2026',
        status: 'nodata',
        range: '',
        average: '',
        hasData: false,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 9', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 24', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['100', '66.7', '33.3', '0'],
        maxY: 100,
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'The Basics: Heart Rate Variability', subtitle: 'Heart rate variability (HRV) offers valuable insights into your overall health...', icon: 'pulse', iconColor: '#8B5CF6', bgColor: '#F3E8FF' },
            { title: 'HRV by Age', subtitle: 'Understanding the correlation between HRV and age can help you est...', icon: 'analytics', iconColor: '#3B82F6', bgColor: '#EFF6FF' },
        ],
        explanation: {
            title: 'Resting HRV',
            paragraphs: [
                "Resting Heart Rate Variability (HRV) is the variance between heartbeats while sleeping. It shows how well your body adapts.",
                "Higher HRV generally equals better fitness. However, HRV is unique to each person based on factors like age, gender, and lifestyle so look for relative trends rather than at absolute quantities.",
                "Rising HRV suggests improving fitness and health. Dropping HRV may suggest overtraining, poor sleep, and high stress."
            ]
        }
    },
    'resting-hr': {
        title: 'Resting HR',
        value: '—',
        unit: 'bpm',
        date: 'Jan 1, 2026',
        status: 'nodata',
        range: '',
        average: '',
        hasData: false,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 9', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 24', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['100', '75', '50', '25'],
        maxY: 100,
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'Understanding Resting HR', subtitle: 'Your resting heart rate is a key indicator of cardiovascular health...', icon: 'heart', iconColor: '#EF4444', bgColor: '#FEE2E2' },
            { title: 'Lower Your RHR', subtitle: 'Tips on how to improve your resting heart rate...', icon: 'trending-down', iconColor: '#16A34A', bgColor: '#DCFCE7' },
        ],
        explanation: {
            title: 'Resting HR',
            paragraphs: [
                "Resting Heart Rate (RHR) is the number of times your heart beats per minute while at complete rest. It's measured during your deepest sleep.",
                "A lower RHR typically indicates better cardiovascular fitness. Athletes often have RHRs in the 40-60 bpm range, while the average adult ranges from 60-100 bpm."
            ]
        }
    },
    'respiratory-rate': {
        title: 'Respiratory Rate',
        value: '—',
        unit: 'rpm',
        date: 'Jan 1, 2026',
        status: 'nodata',
        range: '',
        average: '',
        hasData: false,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 9', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 24', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['30', '20', '10', '0'],
        maxY: 30,
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'The Basics: Respiratory Rate', subtitle: 'Respiratory rate not only helps you gauge the performance of your respiratory sys...', icon: 'fitness', iconColor: '#3B82F6', bgColor: '#EFF6FF' },
            { title: 'Improving Your RR', subtitle: 'Consider making these changes to strengthen your respiratory sys...', icon: 'leaf', iconColor: '#16A34A', bgColor: '#DCFCE7' },
        ],
        explanation: {
            title: 'Respiratory Rate',
            paragraphs: [
                "Respiratory Rate (RR) tracks your breaths per minute during sleep.",
                "It calculates your average rate over the whole night from the rhythmic pattern of your heartbeat as you inhale and exhale.",
                "RR is usually stable night to night, so big shifts likely have meaning. Causes may be illness, tiredness, allergies or altitude changes. Unusually high or low RR could indicate health problems."
            ]
        }
    },
    'oxygen-saturation': {
        title: 'Oxygen Saturation',
        value: '—',
        unit: '%',
        date: 'Jan 1, 2026',
        status: 'nodata',
        range: '',
        average: '',
        hasData: false,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 9', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 24', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['100', '66.7', '33.3', '0'],
        maxY: 100,
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'The Basics: SpO2', subtitle: 'Advanced health monitoring features, such as SpO2 measurement, can transf...', icon: 'water-outline', iconColor: '#06B6D4', bgColor: '#ECFEFF' },
            { title: 'How Your Apple Watch Measures SpO2', subtitle: 'With its advanced sensors and edge technology, the Apple W...', icon: 'watch', iconColor: '#EF4444', bgColor: '#FEE2E2' },
        ],
        explanation: {
            title: 'Oxygen Saturation',
            paragraphs: [
                "SpO2, or peripheral capillary oxygen saturation, measures the percentage of your blood that is saturated with oxygen. SpO2 is sampled regularly while you are asleep and throughout the day if background measurements are turned on. You can also use Apple's Blood Oxygen app to measure more frequently.",
                "Your oxygen saturation can be affected by a variety of factors, including: changes in altitude, physical activity, dehydration, smoking, and certain cardiovascular and respiratory conditions."
            ]
        }
    },
    'wrist-temperature': {
        title: 'Wrist Temperature',
        value: '—',
        unit: '°F',
        date: 'Jan 1, 2026',
        status: 'nodata',
        range: '',
        average: '',
        hasData: false,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 9', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 24', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['100', '66.7', '33.3', '0'],
        maxY: 100,
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'The Basics: Wrist Temperature', subtitle: 'Learn how to leverage temperature measurements as they gain recognition...', icon: 'thermometer-outline', iconColor: '#F97316', bgColor: '#FEF3C7' },
            { title: 'Can Wrist Temperature Signal Fevers', subtitle: 'The most common method of checking for a fever is by using a therm...', icon: 'medical', iconColor: '#EF4444', bgColor: '#FEE2E2' },
        ],
        explanation: {
            title: 'Wrist Temperature',
            paragraphs: [
                "Temperature reflects the average temperature of your skin during your previous night of sleep. Measurements are taken every 5 seconds while you are asleep to minimize interference from external factors, such as movement and changes in ambient temperature.",
                "As a general guideline, you can expect the skin temperature on your wrist to be around 2-4°F or 1-2°C lower than your core body temperature."
            ]
        }
    }
};

// Mini Sparkline for trend table
function MiniSparkline({ data, color, width = 60, height = 20 }: { data: number[]; color: string; width?: number; height?: number }) {
    if (!data || data.length < 2) {
        return (
            <Svg width={width} height={height}>
                <Line x1={0} y1={height / 2} x2={width} y2={height / 2} stroke="#E5E7EB" strokeWidth={2} />
            </Svg>
        );
    }

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
        const x = (index / (data.length - 1)) * width;
        const y = height - ((value - min) / range) * height;
        return { x, y };
    });

    let pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
        pathD += ` L ${points[i].x} ${points[i].y}`;
    }

    return (
        <Svg width={width} height={height}>
            <Path d={pathD} stroke={color} strokeWidth={2} fill="none" />
        </Svg>
    );
}

// Chart Component
function MetricChart({ data, yAxisLabels, maxY, hasData }: { data: { date: string; value: number }[]; yAxisLabels: string[]; maxY: number; hasData: boolean }) {
    const padding = { top: 20, right: 10, bottom: 40, left: 50 };
    const chartW = CHART_WIDTH - padding.left - padding.right;
    const chartH = CHART_HEIGHT - padding.top - padding.bottom;

    const getX = (index: number) => padding.left + (index / (data.length - 1)) * chartW;
    const getY = (value: number) => padding.top + chartH - (value / maxY) * chartH;

    return (
        <View style={styles.chartContainer}>
            <Svg width={CHART_WIDTH} height={CHART_HEIGHT}>
                {/* Y-axis labels and grid lines */}
                {yAxisLabels.map((label, i) => {
                    const yPos = padding.top + (i / (yAxisLabels.length - 1)) * chartH;
                    return (
                        <G key={i}>
                            <Line
                                x1={padding.left}
                                y1={yPos}
                                x2={CHART_WIDTH - padding.right}
                                y2={yPos}
                                stroke="#E5E7EB"
                                strokeWidth={1}
                                strokeDasharray="4,4"
                            />
                            <SvgText
                                x={padding.left - 8}
                                y={yPos + 4}
                                fontSize={10}
                                fill="#9CA3AF"
                                textAnchor="end"
                            >
                                {label}
                            </SvgText>
                        </G>
                    );
                })}

                {/* X-axis labels */}
                {data.map((d, i) => (
                    <SvgText
                        key={i}
                        x={getX(i)}
                        y={CHART_HEIGHT - 10}
                        fontSize={10}
                        fill="#9CA3AF"
                        textAnchor="middle"
                    >
                        {d.date}
                    </SvgText>
                ))}
            </Svg>
        </View>
    );
}

export default function RecoveryMetricDetailScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const params = useLocalSearchParams();
    const [selectedPeriod, setSelectedPeriod] = useState('1M');
    const [selectedTab, setSelectedTab] = useState<MetricType>('recovery-score');

    useEffect(() => {
        const type = params.type as MetricType;
        if (type && metricsData[type]) {
            setSelectedTab(type);
        }
    }, [params.type]);

    const metric = metricsData[selectedTab];
    const tabs: { key: MetricType; label: string }[] = [
        { key: 'recovery-score', label: 'Recovery Score' },
        { key: 'resting-hrv', label: 'Resting HRV' },
        { key: 'resting-hr', label: 'Resting HR' },
        { key: 'respiratory-rate', label: 'Respiratory Rate' },
        { key: 'oxygen-saturation', label: 'Oxygen Saturation' },
        { key: 'wrist-temperature', label: 'Wrist Temperature' },
    ];
    const periods = ['1M', '3M', '6M', '1Y'];

    const getStatusText = (status: string) => {
        if (status === 'above') return 'Above normal';
        if (status === 'below') return 'Below normal';
        if (status === 'normal') return 'Normal range';
        return 'No trends available';
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
                    <Ionicons name="close" size={24} color="#1F2937" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>{metric.title}</Text>
                <View style={{ width: 40 }} />
            </View>

            <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
                {/* Value Display */}
                <View style={styles.valueSection}>
                    <View>
                        <Text style={styles.mainValue}>{metric.value}{metric.unit}</Text>
                        <Text style={styles.dateText}>{metric.date}</Text>
                    </View>
                    <View style={styles.statusSection}>
                        <Text style={styles.statusText}>{getStatusText(metric.status)}</Text>
                        {metric.range ? (
                            <View style={styles.rangeRow}>
                                <Ionicons name="stats-chart" size={14} color="#9CA3AF" />
                                <Text style={styles.rangeText}>{metric.range}</Text>
                            </View>
                        ) : null}
                    </View>
                </View>

                {/* Tabs */}
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsScroll}>
                    <View style={styles.tabsRow}>
                        {tabs.map((tab) => (
                            <TouchableOpacity
                                key={tab.key}
                                style={[styles.tab, selectedTab === tab.key && styles.tabActive]}
                                onPress={() => setSelectedTab(tab.key)}
                            >
                                <Text style={[styles.tabText, selectedTab === tab.key && styles.tabTextActive]}>
                                    {tab.label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </ScrollView>

                {/* Chart */}
                <View style={styles.chartSection}>
                    <MetricChart
                        data={metric.chartData}
                        yAxisLabels={metric.yAxisLabels}
                        maxY={metric.maxY}
                        hasData={metric.hasData}
                    />
                </View>

                {/* Period Selector */}
                <View style={styles.periodSelector}>
                    <TouchableOpacity style={styles.periodArrow}>
                        <Ionicons name="chevron-back" size={20} color="#1F2937" />
                    </TouchableOpacity>
                    <View style={styles.periodTabs}>
                        {periods.map((period) => (
                            <TouchableOpacity
                                key={period}
                                style={[styles.periodTab, selectedPeriod === period && styles.periodTabActive]}
                                onPress={() => setSelectedPeriod(period)}
                            >
                                <Text style={[styles.periodTabText, selectedPeriod === period && styles.periodTabTextActive]}>
                                    {period}
                                </Text>
                            </TouchableOpacity>
                        ))}
                        <TouchableOpacity style={styles.calendarButton}>
                            <Ionicons name="calendar-outline" size={18} color="#6B7280" />
                        </TouchableOpacity>
                    </View>
                    <TouchableOpacity style={styles.periodArrow}>
                        <Ionicons name="chevron-forward" size={20} color="#1F2937" />
                    </TouchableOpacity>
                </View>

                {/* Recovery Breakdown (only for recovery-score) */}
                {metric.breakdown && (
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}>Recovery Breakdown</Text>
                        <View style={styles.breakdownBar}>
                            <View style={[styles.breakdownSegment, { flex: metric.breakdown.poor, backgroundColor: '#EF4444' }]} />
                            <View style={[styles.breakdownSegment, { flex: metric.breakdown.normal, backgroundColor: '#F59E0B' }]} />
                            <View style={[styles.breakdownSegment, { flex: metric.breakdown.optimal, backgroundColor: '#16A34A' }]} />
                        </View>
                        <View style={styles.legendRow}>
                            <View style={styles.legendItem}>
                                <View style={[styles.legendDot, { backgroundColor: '#EF4444' }]} />
                                <Text style={styles.legendLabel}>Poor</Text>
                                <Text style={styles.legendValue}>&lt;34.0%</Text>
                            </View>
                            <View style={styles.legendItem}>
                                <View style={[styles.legendDot, { backgroundColor: '#F59E0B' }]} />
                                <Text style={styles.legendLabel}>Normal</Text>
                                <Text style={styles.legendValue}>34.0% – 67.0%</Text>
                            </View>
                            <View style={styles.legendItem}>
                                <View style={[styles.legendDot, { backgroundColor: '#16A34A' }]} />
                                <Text style={styles.legendLabel}>Optimal</Text>
                                <Text style={styles.legendValue}>&gt;67.0%</Text>
                            </View>
                        </View>
                    </View>
                )}

                {/* Trends Analysis */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Trends Analysis</Text>
                    <Text style={styles.sectionSubtitle}>Based on data from {metric.date}</Text>

                    <View style={styles.trendsTable}>
                        <View style={styles.trendsHeader}>
                            <Text style={[styles.trendsHeaderText, { flex: 1 }]}>Period</Text>
                            <Text style={[styles.trendsHeaderText, { flex: 1 }]}>Change</Text>
                            <Text style={[styles.trendsHeaderText, { flex: 1, textAlign: 'right' }]}>Trend</Text>
                        </View>

                        {metric.trends.map((trend, index) => (
                            <View key={index} style={styles.trendsRow}>
                                <Text style={[styles.trendsCell, { flex: 1 }]}>{trend.period}</Text>
                                <View style={styles.changeCellContainer}>
                                    <View style={[styles.changeIcon, { backgroundColor: '#F3F4F6' }]}>
                                        <Ionicons name="remove" size={12} color="#9CA3AF" />
                                    </View>
                                    <Text style={styles.changeText}>{trend.change}</Text>
                                </View>
                                <View style={{ flex: 1, alignItems: 'flex-end' }}>
                                    <MiniSparkline data={trend.sparkline} color="#9CA3AF" />
                                </View>
                            </View>
                        ))}
                    </View>

                    <Text style={styles.trendsNote}>
                        Based on 7-day rolling averages for the select period.
                    </Text>
                </View>

                {/* Resources */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Resources</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                        <View style={styles.resourcesRow}>
                            {metric.resources.map((resource, index) => (
                                <TouchableOpacity key={index} style={styles.resourceCard}>
                                    <View style={[styles.resourceImage, { backgroundColor: resource.bgColor }]}>
                                        <Ionicons name={resource.icon as any} size={32} color={resource.iconColor} />
                                    </View>
                                    <Text style={styles.resourceTitle}>{resource.title}</Text>
                                    <Text style={styles.resourceDesc} numberOfLines={2}>{resource.subtitle}</Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                    </ScrollView>
                </View>

                {/* Explanation */}
                <View style={styles.section}>
                    <View style={styles.explanationHeader}>
                        <Ionicons name="information-circle-outline" size={20} color="#6B7280" />
                        <Text style={styles.explanationTitle}>{metric.explanation.title}</Text>
                    </View>
                    {metric.explanation.paragraphs.map((paragraph, index) => (
                        <Text key={index} style={styles.explanationText}>{paragraph}</Text>
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
        borderBottomWidth: 1,
        borderBottomColor: '#F3F4F6',
    },
    closeButton: {
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
    scrollView: {
        flex: 1,
    },
    valueSection: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.xl,
    },
    mainValue: {
        fontSize: 48,
        fontWeight: '700',
        color: '#1F2937',
    },
    dateText: {
        fontSize: 14,
        color: '#6B7280',
        marginTop: 4,
    },
    statusSection: {
        alignItems: 'flex-end',
    },
    statusText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#9CA3AF',
    },
    rangeRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        marginTop: 4,
    },
    rangeText: {
        fontSize: 13,
        color: '#9CA3AF',
    },
    tabsScroll: {
        paddingHorizontal: spacing.lg,
    },
    tabsRow: {
        flexDirection: 'row',
        gap: 8,
    },
    tab: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: '#F3F4F6',
    },
    tabActive: {
        backgroundColor: '#1F2937',
    },
    tabText: {
        fontSize: 13,
        fontWeight: '500',
        color: '#6B7280',
    },
    tabTextActive: {
        color: '#FFFFFF',
    },
    chartSection: {
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.xl,
    },
    chartContainer: {
        position: 'relative',
    },
    periodSelector: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.md,
        borderTopWidth: 1,
        borderTopColor: '#F3F4F6',
    },
    periodArrow: {
        width: 36,
        height: 36,
        borderRadius: 18,
        backgroundColor: '#F3F4F6',
        alignItems: 'center',
        justifyContent: 'center',
    },
    periodTabs: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    periodTab: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 16,
    },
    periodTabActive: {
        backgroundColor: '#1F2937',
    },
    periodTabText: {
        fontSize: 13,
        fontWeight: '500',
        color: '#6B7280',
    },
    periodTabTextActive: {
        color: '#FFFFFF',
    },
    calendarButton: {
        width: 36,
        height: 36,
        alignItems: 'center',
        justifyContent: 'center',
    },
    section: {
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.lg,
        borderTopWidth: 1,
        borderTopColor: '#F3F4F6',
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#1F2937',
        marginBottom: 4,
    },
    sectionSubtitle: {
        fontSize: 13,
        color: '#9CA3AF',
        marginBottom: spacing.lg,
    },
    breakdownBar: {
        flexDirection: 'row',
        height: 12,
        borderRadius: 6,
        overflow: 'hidden',
        marginBottom: spacing.lg,
    },
    breakdownSegment: {
        height: '100%',
    },
    legendRow: {
        gap: 12,
    },
    legendItem: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingVertical: 6,
    },
    legendDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
    },
    legendLabel: {
        fontSize: 14,
        fontWeight: '500',
        color: '#1F2937',
    },
    legendValue: {
        fontSize: 13,
        color: '#9CA3AF',
    },
    trendsTable: {
        backgroundColor: '#F9FAFB',
        borderRadius: 16,
        overflow: 'hidden',
    },
    trendsHeader: {
        flexDirection: 'row',
        paddingHorizontal: spacing.lg,
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#E5E7EB',
    },
    trendsHeaderText: {
        fontSize: 12,
        fontWeight: '500',
        color: '#9CA3AF',
    },
    trendsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: spacing.lg,
        paddingVertical: 14,
        borderBottomWidth: 1,
        borderBottomColor: '#E5E7EB',
    },
    trendsCell: {
        fontSize: 14,
        color: '#1F2937',
    },
    changeCellContainer: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    changeIcon: {
        width: 20,
        height: 20,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
    },
    changeText: {
        fontSize: 14,
        fontWeight: '500',
        color: '#1F2937',
    },
    trendsNote: {
        fontSize: 12,
        color: '#9CA3AF',
        textAlign: 'center',
        marginTop: spacing.md,
    },
    resourcesRow: {
        flexDirection: 'row',
        gap: 12,
        paddingTop: spacing.md,
    },
    resourceCard: {
        width: 160,
        backgroundColor: '#F9FAFB',
        borderRadius: 16,
        padding: spacing.md,
    },
    resourceImage: {
        width: '100%',
        height: 80,
        borderRadius: 12,
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 12,
    },
    resourceTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: '#1F2937',
        marginBottom: 4,
    },
    resourceDesc: {
        fontSize: 12,
        color: '#9CA3AF',
        lineHeight: 16,
    },
    explanationHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: spacing.md,
    },
    explanationTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1F2937',
    },
    explanationText: {
        fontSize: 14,
        color: '#6B7280',
        lineHeight: 22,
        marginBottom: spacing.md,
    },
});

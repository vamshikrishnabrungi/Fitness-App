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

type MetricType = 'strain' | 'duration' | 'daytime-hr' | 'energy' | 'steps';

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
    trends: { period: string; change: string; up: boolean | null; sparkline: number[] }[];
    resources: { title: string; subtitle: string; icon: string; iconColor: string; bgColor: string }[];
    explanation: { title: string; paragraphs: string[] };
}

// Mock data for each metric type
const metricsData: Record<MetricType, MetricConfig> = {
    strain: {
        title: 'Strain Score',
        value: '15',
        unit: '%',
        date: 'Jan 1, 2026',
        status: 'above',
        range: '3 - 10%',
        average: '6%',
        hasData: true,
        chartData: [
            { date: 'Dec 2', value: 4 }, { date: 'Dec 5', value: 6 }, { date: 'Dec 9', value: 5 },
            { date: 'Dec 12', value: 8 }, { date: 'Dec 15', value: 14 }, { date: 'Dec 17', value: 16 },
            { date: 'Dec 19', value: 7 }, { date: 'Dec 22', value: 12 }, { date: 'Dec 24', value: 9 },
            { date: 'Dec 27', value: 14 }, { date: 'Dec 30', value: 11 }, { date: 'Jan 1', value: 15 },
        ],
        yAxisLabels: ['18', '12', '6', '0'],
        maxY: 18,
        trends: [
            { period: '3-day', change: '+1%', up: true, sparkline: [10, 12, 15] },
            { period: '7-day', change: '-1%', up: false, sparkline: [14, 12, 10, 11, 9, 12, 15] },
            { period: '14-day', change: '+2%', up: true, sparkline: [8, 10, 12, 11, 14, 13, 15] },
            { period: '30-day', change: '+2%', up: true, sparkline: [6, 8, 10, 12, 11, 14, 15] },
            { period: '90-day', change: '-1%', up: false, sparkline: [12, 10, 8, 10, 12, 14, 15] },
        ],
        resources: [
            { title: 'What is Strain Score?', subtitle: 'Understand the intensity of your workouts...', icon: 'fitness', iconColor: '#F97316', bgColor: '#FEF3C7' },
            { title: 'Exercise Duration', subtitle: 'The Basics: The amount of time you spend...', icon: 'time', iconColor: '#3B82F6', bgColor: '#F0F9FF' },
        ],
        explanation: {
            title: 'Strain Score',
            paragraphs: [
                "Strain Score calculates your total exertion for the day. It's based on your time spent in personalized heart rate zones set from your max heart rate. Strain rises logarithmically, not linearly. So the higher your Strain, the harder it is to increase.",
                "To build more Strain, spend more time at higher heart rates. The higher and longer your elevated HR, the more Strain accrues. Too many high Strain days without enough Recovery can lead to overtraining or injury."
            ]
        }
    },
    duration: {
        title: 'Exercise Duration',
        value: '0',
        unit: 'm',
        date: 'Jan 1, 2026',
        status: 'normal',
        range: '0m - 0m',
        average: '0m',
        hasData: true,
        chartData: [
            { date: 'Dec 2', value: 0 }, { date: 'Dec 5', value: 0 }, { date: 'Dec 9', value: 0 },
            { date: 'Dec 12', value: 0 }, { date: 'Dec 15', value: 0 }, { date: 'Dec 17', value: 0 },
            { date: 'Dec 19', value: 0 }, { date: 'Dec 22', value: 0 }, { date: 'Dec 24', value: 0 },
            { date: 'Dec 27', value: 0 }, { date: 'Dec 30', value: 0 }, { date: 'Jan 1', value: 0 },
        ],
        yAxisLabels: ['2h 0m', '1h 20m', '40m', '0m'],
        maxY: 120,
        trends: [
            { period: '3-day', change: '0m', up: null, sparkline: [] },
            { period: '7-day', change: '0m', up: null, sparkline: [] },
            { period: '14-day', change: '0m', up: null, sparkline: [] },
            { period: '30-day', change: '0m', up: null, sparkline: [] },
            { period: '90-day', change: '0m', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'Exercise Duration', subtitle: 'The amount of time you spend exercising per day plays a crucial role...', icon: 'time', iconColor: '#3B82F6', bgColor: '#F0F9FF' },
            { title: 'Heart Rate Zones', subtitle: 'Embarking on a fitness journey is empowering...', icon: 'heart', iconColor: '#EF4444', bgColor: '#FEF2F2' },
        ],
        explanation: {
            title: 'Exercise Duration',
            paragraphs: [
                "Exercise Duration measures the total time spent actively moving and exercising each day.",
                "To increase your Exercise Duration, find forms of movement you enjoy and set reminders to stay active daily. Going for walks, runs, swims, playing sports, strength training at the gym, or taking fitness classes will all contribute to your Exercise Duration."
            ]
        }
    },
    'daytime-hr': {
        title: 'Daytime HR',
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
        yAxisLabels: ['100', '67', '33', '0'],
        maxY: 100,
        trends: [
            { period: '3-day', change: '—', up: null, sparkline: [] },
            { period: '7-day', change: '—', up: null, sparkline: [] },
            { period: '14-day', change: '—', up: null, sparkline: [] },
            { period: '30-day', change: '—', up: null, sparkline: [] },
            { period: '90-day', change: '—', up: null, sparkline: [] },
        ],
        resources: [
            { title: 'Daytime Heart Rate', subtitle: 'Tracking your daytime heart rate can give valuable insights...', icon: 'heart', iconColor: '#EF4444', bgColor: '#FEF2F2' },
            { title: 'Heart Rate Zones', subtitle: 'Embarking on a fitness journey is empowering...', icon: 'pulse', iconColor: '#F97316', bgColor: '#FEF3C7' },
        ],
        explanation: {
            title: 'Daytime HR',
            paragraphs: [
                "Daytime HR calculates the average of your heart rate during waking hours. It provides insights into your cardiovascular health and daily stress levels.",
                "A lower resting daytime heart rate often indicates better cardiovascular fitness. Monitoring trends over time can help you understand how your lifestyle, sleep, and training affect your heart health."
            ]
        }
    },
    energy: {
        title: 'Total Energy',
        value: '3,485',
        unit: 'kJ',
        date: 'Jan 1, 2026',
        status: 'below',
        range: '4,000 - 5,000 kJ',
        average: '3,200 kJ',
        hasData: true,
        chartData: [
            { date: 'Dec 2', value: 3200 }, { date: 'Dec 5', value: 3400 }, { date: 'Dec 9', value: 3100 },
            { date: 'Dec 12', value: 3600 }, { date: 'Dec 15', value: 3300 }, { date: 'Dec 17', value: 3500 },
            { date: 'Dec 19', value: 3200 }, { date: 'Dec 22', value: 3485 }, { date: 'Dec 24', value: 3300 },
            { date: 'Dec 27', value: 3400 }, { date: 'Dec 30', value: 3500 }, { date: 'Jan 1', value: 3485 },
        ],
        yAxisLabels: ['5000', '4000', '3000', '2000'],
        maxY: 5000,
        trends: [
            { period: '3-day', change: '-5%', up: false, sparkline: [3500, 3400, 3485] },
            { period: '7-day', change: '+2%', up: true, sparkline: [3300, 3400, 3200, 3500, 3485] },
            { period: '14-day', change: '-3%', up: false, sparkline: [3600, 3400, 3300, 3500, 3485] },
            { period: '30-day', change: '+1%', up: true, sparkline: [3300, 3400, 3500, 3400, 3485] },
            { period: '90-day', change: '-2%', up: false, sparkline: [3600, 3500, 3400, 3485] },
        ],
        resources: [
            { title: 'What is Total Energy?', subtitle: 'Understanding your daily energy expenditure...', icon: 'flash', iconColor: '#F97316', bgColor: '#FEF3C7' },
            { title: 'Calorie Tracking', subtitle: 'Monitor your energy balance for better health...', icon: 'restaurant', iconColor: '#16A34A', bgColor: '#DCFCE7' },
        ],
        explanation: {
            title: 'Total Energy',
            paragraphs: [
                "Total Energy represents your daily energy expenditure measured in kilojoules (kJ). It includes your basal metabolic rate plus energy burned through activity.",
                "Tracking total energy helps you understand your energy balance. If your goal is weight loss, you'll want to consume fewer calories than you burn. For muscle building, a small surplus is often recommended."
            ]
        }
    },
    steps: {
        title: 'Step Count',
        value: '9,660',
        unit: '',
        date: 'Jan 1, 2026',
        status: 'above',
        range: '981 - 5,477',
        average: '3,200',
        hasData: true,
        chartData: [
            { date: 'Dec 2', value: 2100 }, { date: 'Dec 5', value: 1800 }, { date: 'Dec 9', value: 2500 },
            { date: 'Dec 12', value: 4200 }, { date: 'Dec 15', value: 8500 }, { date: 'Dec 17', value: 11200 },
            { date: 'Dec 19', value: 3800 }, { date: 'Dec 22', value: 5200 }, { date: 'Dec 24', value: 6100 },
            { date: 'Dec 27', value: 4500 }, { date: 'Dec 30', value: 7800 }, { date: 'Jan 1', value: 9660 },
        ],
        yAxisLabels: ['11.6K', '7.76K', '3.88K', '0'],
        maxY: 11600,
        trends: [
            { period: '3-day', change: '+725', up: true, sparkline: [7800, 8500, 9660] },
            { period: '7-day', change: '-901', up: false, sparkline: [11200, 8500, 6100, 7800, 9660] },
            { period: '14-day', change: '+1,290', up: true, sparkline: [4200, 8500, 5200, 7800, 9660] },
            { period: '30-day', change: '+1,160', up: true, sparkline: [2500, 4200, 6100, 7800, 9660] },
            { period: '90-day', change: '+21', up: null, sparkline: [3500, 4200, 5200, 6800, 7800, 9660] },
        ],
        resources: [
            { title: 'The Basics: Step Count', subtitle: 'While it might seem like a simple measure of movement, understanding t...', icon: 'footsteps', iconColor: '#3B82F6', bgColor: '#EFF6FF' },
            { title: 'Heart Rate Zones', subtitle: 'Embarking on a fitness journey is empowering, and understanding...', icon: 'heart', iconColor: '#EF4444', bgColor: '#FEF2F2' },
        ],
        explanation: {
            title: 'Step Count',
            paragraphs: [
                "Step Count tracks the number of steps you take daily, including steps during exercises.",
                "A higher count usually signifies more activity. To increase your Step Count, consider incorporating more walking into your routine, like taking the stairs or parking farther away.",
                "Simple changes can significantly boost your daily steps and overall activity."
            ]
        }
    }
};

// Mini Sparkline for trend table
function MiniSparkline({ data, color, width = 60, height = 20 }: { data: number[]; color: string; width?: number; height?: number }) {
    if (!data || data.length < 2) {
        // Empty line when no data
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
function MetricChart({ data, average, yAxisLabels, maxY, hasData }: { data: { date: string; value: number }[]; average: string; yAxisLabels: string[]; maxY: number; hasData: boolean }) {
    const padding = { top: 20, right: 10, bottom: 40, left: 50 };
    const chartW = CHART_WIDTH - padding.left - padding.right;
    const chartH = CHART_HEIGHT - padding.top - padding.bottom;

    const getX = (index: number) => padding.left + (index / (data.length - 1)) * chartW;
    const getY = (value: number) => padding.top + chartH - (value / maxY) * chartH;

    // Build path
    let pathD = `M ${getX(0)} ${getY(data[0].value)}`;
    for (let i = 1; i < data.length; i++) {
        pathD += ` L ${getX(i)} ${getY(data[i].value)}`;
    }

    const avgValue = hasData ? parseFloat(average) || 0 : 0;
    const avgY = getY(avgValue);

    return (
        <View style={styles.chartContainer}>
            <Svg width={CHART_WIDTH} height={CHART_HEIGHT}>
                <Defs>
                    <LinearGradient id="zoneGrad" x1="0" y1="0" x2="0" y2="1">
                        <Stop offset="0%" stopColor="#7C3AED" stopOpacity="0.2" />
                        <Stop offset="100%" stopColor="#7C3AED" stopOpacity="0.05" />
                    </LinearGradient>
                </Defs>

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

                {/* Average line */}
                {hasData && avgValue > 0 && (
                    <Line
                        x1={padding.left}
                        y1={avgY}
                        x2={CHART_WIDTH - padding.right}
                        y2={avgY}
                        stroke="#F97316"
                        strokeWidth={1}
                        strokeDasharray="6,4"
                    />
                )}

                {/* Main line */}
                <Path
                    d={pathD}
                    stroke="#F59E0B"
                    strokeWidth={2.5}
                    fill="none"
                />

                {/* Data points */}
                {data.map((d, i) => (
                    <Circle
                        key={i}
                        cx={getX(i)}
                        cy={getY(d.value)}
                        r={4}
                        fill="#FFFFFF"
                        stroke="#F59E0B"
                        strokeWidth={2}
                    />
                ))}

                {/* Last point highlight */}
                <Circle
                    cx={getX(data.length - 1)}
                    cy={getY(data[data.length - 1].value)}
                    r={6}
                    fill="#F59E0B"
                />

                {/* X-axis labels */}
                {data.filter((_, i) => i === 0 || i === Math.floor(data.length / 4) || i === Math.floor(data.length / 2) || i === Math.floor(3 * data.length / 4) || i === data.length - 1).map((d, i, arr) => (
                    <SvgText
                        key={i}
                        x={getX(i === 0 ? 0 : i === arr.length - 1 ? data.length - 1 : Math.floor(i * data.length / 4))}
                        y={CHART_HEIGHT - 10}
                        fontSize={10}
                        fill="#9CA3AF"
                        textAnchor="middle"
                    >
                        {d.date}
                    </SvgText>
                ))}
            </Svg>

            {/* Average label */}
            {hasData && average && (
                <View style={[styles.avgLabel, { top: avgY - 10, left: padding.left + 20 }]}>
                    <Text style={styles.avgLabelText}>Avg. {average}</Text>
                </View>
            )}
        </View>
    );
}

export default function StrainDetailScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const params = useLocalSearchParams();
    const [selectedPeriod, setSelectedPeriod] = useState('1M');
    const [selectedTab, setSelectedTab] = useState<MetricType>('strain');

    // Get metric type from URL params or default to strain
    useEffect(() => {
        const type = params.type as MetricType;
        if (type && metricsData[type]) {
            setSelectedTab(type);
        }
    }, [params.type]);

    const metric = metricsData[selectedTab];
    const tabs: { key: MetricType; label: string }[] = [
        { key: 'strain', label: 'Strain Score' },
        { key: 'duration', label: 'Exercise Duration' },
        { key: 'daytime-hr', label: 'Daytime HR' },
        { key: 'energy', label: 'Total Energy' },
        { key: 'steps', label: 'Step Count' },
    ];
    const periods = ['1M', '3M', '6M', '1Y'];

    const getStatusColor = (status: string) => {
        if (status === 'above') return '#3B82F6';
        if (status === 'below') return '#F97316';
        if (status === 'normal') return '#16A34A';
        return '#9CA3AF';
    };

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
                        <Text style={[styles.statusText, { color: getStatusColor(metric.status) }]}>
                            {getStatusText(metric.status)}
                        </Text>
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
                        average={metric.average}
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

                {/* Trends Analysis */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Trends Analysis</Text>
                    <Text style={styles.sectionSubtitle}>
                        {metric.hasData ? `Last data point on ${metric.date}` : `Based on data from ${metric.date}`}
                    </Text>

                    <View style={styles.trendsTable}>
                        {/* Header */}
                        <View style={styles.trendsHeader}>
                            <Text style={[styles.trendsHeaderText, { flex: 1 }]}>Period</Text>
                            <Text style={[styles.trendsHeaderText, { flex: 1 }]}>Change</Text>
                            <Text style={[styles.trendsHeaderText, { flex: 1, textAlign: 'right' }]}>Trend</Text>
                        </View>

                        {/* Rows */}
                        {metric.trends.map((trend, index) => (
                            <View key={index} style={styles.trendsRow}>
                                <Text style={[styles.trendsCell, { flex: 1 }]}>{trend.period}</Text>
                                <View style={styles.changeCellContainer}>
                                    {trend.up !== null ? (
                                        <View style={[styles.changeIcon, { backgroundColor: trend.up ? '#DCFCE7' : '#FEE2E2' }]}>
                                            <Ionicons
                                                name={trend.up ? 'arrow-up' : 'arrow-down'}
                                                size={12}
                                                color={trend.up ? '#16A34A' : '#EF4444'}
                                            />
                                        </View>
                                    ) : (
                                        <View style={[styles.changeIcon, { backgroundColor: '#F3F4F6' }]}>
                                            <Ionicons name="remove" size={12} color="#9CA3AF" />
                                        </View>
                                    )}
                                    <Text style={styles.changeText}>{trend.change}</Text>
                                </View>
                                <View style={{ flex: 1, alignItems: 'flex-end' }}>
                                    <MiniSparkline
                                        data={trend.sparkline}
                                        color={trend.up === true ? '#3B82F6' : trend.up === false ? '#F97316' : '#9CA3AF'}
                                    />
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
    avgLabel: {
        position: 'absolute',
        backgroundColor: '#F97316',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
    },
    avgLabelText: {
        fontSize: 11,
        fontWeight: '600',
        color: '#FFFFFF',
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

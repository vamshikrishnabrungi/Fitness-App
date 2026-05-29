import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    ActivityIndicator,
    Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Path, Line, Circle } from 'react-native-svg';
import { api } from '../../src/utils/api';
import { spacing } from '../../src/utils/theme';

const { width } = Dimensions.get('window');

interface BiologyData {
    vo2_max?: { value: number | null; range?: string; last_updated?: string };
    hrv_baseline?: { value: number | null; trend?: string; range?: string; last_updated?: string };
    rhr_baseline?: { value: number | null; trend?: string; range?: string; last_updated?: string };
    weight?: { value: number | null; trend?: string; last_updated?: string };
    lean_mass?: { value: number | null; trend?: string; last_updated?: string };
    body_fat?: { value: number | null; trend?: string; range?: string; last_updated?: string };
}

// Mini Sparkline Component
function MiniSparkline({ width: w = 100, height: h = 30, color = '#6B7280' }: { width?: number; height?: number; color?: string }) {
    // Empty sparkline with just a horizontal line
    return (
        <Svg width={w} height={h}>
            <Line x1={0} y1={h / 2} x2={w} y2={h / 2} stroke={color} strokeWidth={2} />
            <Circle cx={w} cy={h / 2} r={4} fill={color} />
        </Svg>
    );
}

// Mini Chart Component (for VO2 Max style)
function MiniChart({ width: w = 120, height: h = 50 }: { width?: number; height?: number }) {
    return (
        <Svg width={w} height={h}>
            {[0, 1, 2, 3].map((i) => (
                <Line
                    key={i}
                    x1={0}
                    y1={h * (i / 3)}
                    x2={w}
                    y2={h * (i / 3)}
                    stroke="#4B5563"
                    strokeWidth={1}
                />
            ))}
        </Svg>
    );
}

// Gauge Component (for RHR and Body Fat)
function GaugeArc({ size = 100, progress = 0.5 }: { size?: number; progress?: number }) {
    const strokeWidth = 8;
    const radius = (size - strokeWidth) / 2;
    const circumference = Math.PI * radius; // Half circle
    const offset = circumference - progress * circumference;
    const center = size / 2;

    return (
        <Svg width={size} height={size / 2 + 10}>
            {/* Background arc */}
            <Path
                d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
                stroke="#374151"
                strokeWidth={strokeWidth}
                fill="none"
            />
            {/* Progress arc */}
            <Path
                d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
                stroke="#F59E0B"
                strokeWidth={strokeWidth}
                fill="none"
                strokeDasharray={`${circumference}`}
                strokeDashoffset={offset}
                strokeLinecap="round"
            />
        </Svg>
    );
}

export default function BiologyScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<BiologyData | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const res = await api.get<BiologyData>('/health/biology').catch(() => null);
            setData(res);
        } catch (error) {
            console.error('Error fetching biology:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
                <ActivityIndicator size="large" color="#FFFFFF" />
            </View>
        );
    }

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Biology</Text>
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                {/* VO2 Max Card - Full Width */}
                <View style={styles.fullCard}>
                    <View style={styles.cardHeader}>
                        <Ionicons name="fitness" size={18} color="#16A34A" />
                        <Text style={styles.cardTitle}>VO₂ Max</Text>
                    </View>
                    <View style={styles.cardContent}>
                        <View style={styles.valueSection}>
                            <Text style={styles.valueText}>No data</Text>
                            <Text style={styles.rangeText}>No range</Text>
                        </View>
                        <View style={styles.chartSection}>
                            <MiniChart width={140} height={60} />
                        </View>
                    </View>
                </View>

                {/* HRV & RHR Baselines Row */}
                <View style={styles.cardRow}>
                    {/* HRV Baselines */}
                    <View style={styles.halfCard}>
                        <View style={styles.cardHeader}>
                            <Ionicons name="pulse" size={16} color="#8B5CF6" />
                            <Text style={styles.cardTitle}>HRV Baselines</Text>
                        </View>
                        <View style={styles.halfCardContent}>
                            <MiniSparkline width={80} height={30} color="#6B7280" />
                            <Text style={styles.valueText}>No data</Text>
                            <View style={styles.trendRow}>
                                <Ionicons name="close-circle" size={12} color="#6B7280" />
                                <Text style={styles.trendText}>No trend</Text>
                            </View>
                        </View>
                    </View>

                    {/* RHR Baselines */}
                    <View style={styles.halfCard}>
                        <View style={styles.cardHeader}>
                            <Ionicons name="heart" size={16} color="#EF4444" />
                            <Text style={styles.cardTitle}>RHR Baselines</Text>
                        </View>
                        <View style={styles.halfCardContent}>
                            <Text style={styles.valueText}>No data</Text>
                            <Text style={styles.rangeTextSmall}>No range</Text>
                            <GaugeArc size={100} progress={0.5} />
                            <View style={styles.gaugeButtons}>
                                <TouchableOpacity style={styles.gaugeButton}>
                                    <Ionicons name="remove" size={16} color="#3B82F6" />
                                </TouchableOpacity>
                                <TouchableOpacity style={styles.gaugeButton}>
                                    <Ionicons name="add" size={16} color="#EF4444" />
                                </TouchableOpacity>
                            </View>
                        </View>
                    </View>
                </View>

                {/* Weight Card - Full Width */}
                <View style={styles.fullCard}>
                    <View style={styles.cardHeader}>
                        <Ionicons name="scale" size={18} color="#9CA3AF" />
                        <Text style={styles.cardTitle}>Weight</Text>
                    </View>
                    <View style={styles.cardContent}>
                        <View style={styles.valueSection}>
                            <Text style={styles.valueText}>No data</Text>
                            <View style={styles.trendRow}>
                                <Ionicons name="close-circle" size={12} color="#6B7280" />
                                <Text style={styles.trendText}>No trend</Text>
                            </View>
                        </View>
                        <View style={styles.chartSection}>
                            <MiniSparkline width={140} height={30} color="#6B7280" />
                        </View>
                    </View>
                </View>

                {/* Lean Body Mass & Body Fat Row */}
                <View style={styles.cardRow}>
                    {/* Lean Body Mass */}
                    <View style={styles.halfCard}>
                        <View style={styles.cardHeader}>
                            <Ionicons name="body" size={16} color="#3B82F6" />
                            <Text style={styles.cardTitle}>Lean Body Mass</Text>
                        </View>
                        <View style={styles.halfCardContent}>
                            <MiniSparkline width={80} height={30} color="#6B7280" />
                            <Text style={styles.valueText}>No data</Text>
                            <View style={styles.trendRow}>
                                <Ionicons name="close-circle" size={12} color="#6B7280" />
                                <Text style={styles.trendText}>No trend</Text>
                            </View>
                        </View>
                    </View>

                    {/* Body Fat */}
                    <View style={styles.halfCard}>
                        <View style={styles.cardHeader}>
                            <Ionicons name="cellular" size={16} color="#F97316" />
                            <Text style={styles.cardTitle}>Body Fat</Text>
                        </View>
                        <View style={styles.halfCardContent}>
                            <Text style={styles.valueText}>No data</Text>
                            <Text style={styles.rangeTextSmall}>No range</Text>
                            <GaugeArc size={100} progress={0.5} />
                            <View style={styles.gaugeButtons}>
                                <TouchableOpacity style={styles.gaugeButton}>
                                    <Ionicons name="remove" size={16} color="#3B82F6" />
                                </TouchableOpacity>
                                <TouchableOpacity style={styles.gaugeButton}>
                                    <Ionicons name="add" size={16} color="#EF4444" />
                                </TouchableOpacity>
                            </View>
                        </View>
                    </View>
                </View>

                <View style={{ height: 100 }} />
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#111111',
    },
    centered: {
        justifyContent: 'center',
        alignItems: 'center',
    },
    header: {
        alignItems: 'center',
        paddingVertical: spacing.lg,
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    content: {
        flex: 1,
        paddingHorizontal: spacing.md,
    },
    // Full Width Card
    fullCard: {
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        padding: spacing.lg,
        marginBottom: spacing.md,
    },
    cardHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: spacing.md,
    },
    cardTitle: {
        fontSize: 14,
        fontWeight: '500',
        color: '#FFFFFF',
    },
    cardContent: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
    },
    valueSection: {
        flex: 1,
    },
    valueText: {
        fontSize: 24,
        fontWeight: '300',
        color: '#6B7280',
        marginBottom: 4,
    },
    rangeText: {
        fontSize: 13,
        color: '#6B7280',
    },
    rangeTextSmall: {
        fontSize: 12,
        color: '#6B7280',
        marginBottom: 8,
    },
    chartSection: {
        alignItems: 'flex-end',
    },
    trendRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    trendText: {
        fontSize: 12,
        color: '#6B7280',
    },
    // Card Row
    cardRow: {
        flexDirection: 'row',
        gap: spacing.md,
        marginBottom: spacing.md,
    },
    halfCard: {
        flex: 1,
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        padding: spacing.lg,
    },
    halfCardContent: {
        alignItems: 'flex-start',
    },
    // Gauge
    gaugeButtons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        width: '100%',
        marginTop: -10,
    },
    gaugeButton: {
        width: 28,
        height: 28,
        borderRadius: 14,
        backgroundColor: '#2A2A2A',
        alignItems: 'center',
        justifyContent: 'center',
    },
});

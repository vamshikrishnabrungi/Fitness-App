import React, { useCallback, useEffect, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../utils/api';
import { colors, typography, spacing, borderRadius } from '../utils/theme';

interface Insight {
    summary: string;
    strength: string | null;
    improvement: string | null;
    recommendation: string | null;
}

interface AIInsightsCardProps {
    onPress?: () => void;
}

export function AIInsightsCard({ onPress }: AIInsightsCardProps) {
    const [loading, setLoading] = useState(true);
    const [insights, setInsights] = useState<Insight | null>(null);
    const [period, setPeriod] = useState<'week' | 'month'>('week');

    const fetchInsights = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get<{ insights: Insight | string; period: string }>(`/ai/journal/insights?period=${period}`);
            if (typeof response?.insights === 'object') {
                setInsights(response.insights);
            } else {
                setInsights({ summary: response?.insights || 'Keep logging to get insights!', strength: null, improvement: null, recommendation: null });
            }
        } catch (error) {
            console.error('Error fetching insights:', error);
            setInsights({ summary: 'Log your mood and energy to get AI-powered insights.', strength: null, improvement: null, recommendation: null });
        } finally {
            setLoading(false);
        }
    }, [period]);

    useEffect(() => {
        fetchInsights();
    }, [fetchInsights]);

    return (
        <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.9}>
            <LinearGradient
                colors={['#667eea', '#764ba2']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.gradient}
            >
                {/* Header */}
                <View style={styles.header}>
                    <View style={styles.headerLeft}>
                        <Ionicons name="sparkles" size={18} color="rgba(255,255,255,0.9)" />
                        <Text style={styles.title}>AI Insights</Text>
                    </View>
                    <View style={styles.periodToggle}>
                        <TouchableOpacity
                            style={[styles.periodButton, period === 'week' && styles.periodButtonActive]}
                            onPress={() => setPeriod('week')}
                        >
                            <Text style={[styles.periodText, period === 'week' && styles.periodTextActive]}>Week</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={[styles.periodButton, period === 'month' && styles.periodButtonActive]}
                            onPress={() => setPeriod('month')}
                        >
                            <Text style={[styles.periodText, period === 'month' && styles.periodTextActive]}>Month</Text>
                        </TouchableOpacity>
                    </View>
                </View>

                {/* Content */}
                {loading ? (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="small" color="rgba(255,255,255,0.8)" />
                    </View>
                ) : insights ? (
                    <View style={styles.content}>
                        <Text style={styles.summary}>{insights.summary}</Text>

                        {insights.recommendation && (
                            <View style={styles.recommendation}>
                                <Text style={styles.recommendationLabel}>💡 Recommendation</Text>
                                <Text style={styles.recommendationText}>{insights.recommendation}</Text>
                            </View>
                        )}

                        {(insights.strength || insights.improvement) && (
                            <View style={styles.highlights}>
                                {insights.strength && (
                                    <View style={styles.highlightItem}>
                                        <Ionicons name="trending-up" size={12} color="#4CAF50" />
                                        <Text style={styles.highlightText}>{insights.strength}</Text>
                                    </View>
                                )}
                                {insights.improvement && (
                                    <View style={styles.highlightItem}>
                                        <Ionicons name="arrow-forward" size={12} color="#FFC107" />
                                        <Text style={styles.highlightText}>{insights.improvement}</Text>
                                    </View>
                                )}
                            </View>
                        )}
                    </View>
                ) : (
                    <Text style={styles.emptyText}>Log more entries to unlock insights</Text>
                )}
            </LinearGradient>
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    card: {
        borderRadius: borderRadius.lg,
        overflow: 'hidden',
        marginBottom: spacing.md,
    },
    gradient: {
        padding: spacing.md,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    headerLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
    },
    title: {
        ...typography.bodySemibold,
        color: colors.background,
    },
    periodToggle: {
        flexDirection: 'row',
        backgroundColor: 'rgba(255,255,255,0.2)',
        borderRadius: borderRadius.sm,
        padding: 2,
    },
    periodButton: {
        paddingHorizontal: spacing.sm,
        paddingVertical: 4,
        borderRadius: borderRadius.sm,
    },
    periodButtonActive: {
        backgroundColor: 'rgba(255,255,255,0.3)',
    },
    periodText: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.7)',
        fontSize: 11,
    },
    periodTextActive: {
        color: colors.background,
        fontWeight: '600',
    },
    loadingContainer: {
        padding: spacing.lg,
        alignItems: 'center',
    },
    content: {
        gap: spacing.sm,
    },
    summary: {
        ...typography.body,
        color: colors.background,
        lineHeight: 22,
    },
    recommendation: {
        backgroundColor: 'rgba(255,255,255,0.15)',
        padding: spacing.sm,
        borderRadius: borderRadius.md,
        marginTop: spacing.xs,
    },
    recommendationLabel: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.9)',
        fontWeight: '600',
        marginBottom: 4,
    },
    recommendationText: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.9)',
        lineHeight: 18,
    },
    highlights: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
        marginTop: spacing.xs,
    },
    highlightItem: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        backgroundColor: 'rgba(255,255,255,0.15)',
        paddingHorizontal: spacing.sm,
        paddingVertical: 4,
        borderRadius: borderRadius.sm,
    },
    highlightText: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.9)',
        fontSize: 11,
    },
    emptyText: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.7)',
        textAlign: 'center',
        padding: spacing.md,
    },
});

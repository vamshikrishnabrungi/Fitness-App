import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, borderRadius } from '../utils/theme';
import { CardContainer, CardFooter, EmptyState } from './HomeCard';

type ActivityType = 'run' | 'strength' | 'boxing' | 'mobility' | 'yoga' | 'recovery';

interface ActivityData {
    type: ActivityType;
    // Run specific
    distance?: number;
    pace?: string;
    duration?: number;
    // Strength specific
    total_sets?: number;
    volume?: number;
    muscle_groups?: string[];
    rpe?: number;
    // Boxing specific
    rounds?: number;
    session_focus?: string;
    skill_chips?: string[];
    // Mobility/Recovery
    focus_area?: string;
    // Common
    fatigue?: 'Low' | 'Moderate' | 'High';
    consistency?: number;
    timestamp?: string;
}

interface ActivityCardProps {
    data?: ActivityData | null;
    onStartSession?: (type: ActivityType) => void;
}

const ACTIVITY_CONFIG: Record<ActivityType, { icon: string; color: string; label: string }> = {
    run: { icon: 'walk-outline', color: colors.accentBlue, label: 'Run' },
    strength: { icon: 'barbell-outline', color: colors.accentOrange, label: 'Strength' },
    boxing: { icon: 'hand-left-outline', color: '#EF4444', label: 'Boxing' },
    mobility: { icon: 'body-outline', color: colors.accentTeal, label: 'Mobility' },
    yoga: { icon: 'leaf-outline', color: '#8B5CF6', label: 'Yoga' },
    recovery: { icon: 'bed-outline', color: colors.accentGreen, label: 'Recovery' },
};

const SHORTCUTS: ActivityType[] = ['run', 'strength', 'boxing', 'mobility'];

/**
 * ActivityCard - Polymorphic based on last activity type
 */
export function ActivityCard({ data, onStartSession }: ActivityCardProps) {
    const router = useRouter();

    // Empty state
    if (!data) {
        return (
            <CardContainer variant="outlined">
                <EmptyState
                    icon="flash-outline"
                    title="No recent activity"
                    subtitle="Start a session to track your training"
                >
                </EmptyState>
                <View style={styles.shortcutsRow}>
                    {SHORTCUTS.map((type) => {
                        const config = ACTIVITY_CONFIG[type];
                        return (
                            <TouchableOpacity
                                key={type}
                                style={[styles.shortcutButton, { backgroundColor: config.color + '15' }]}
                                onPress={() => onStartSession?.(type)}
                            >
                                <Ionicons name={config.icon as any} size={20} color={config.color} />
                                <Text style={[styles.shortcutText, { color: config.color }]}>{config.label}</Text>
                            </TouchableOpacity>
                        );
                    })}
                </View>
            </CardContainer>
        );
    }

    const config = ACTIVITY_CONFIG[data.type];

    const handlePress = () => {
        if (data.type === 'run') {
            router.push('/(tabs)/run');
        } else {
            router.push('/(tabs)/train');
        }
    };

    // Render based on activity type
    const renderContent = () => {
        switch (data.type) {
            case 'run':
                return <RunContent data={data} />;
            case 'strength':
                return <StrengthContent data={data} />;
            case 'boxing':
                return <BoxingContent data={data} />;
            case 'mobility':
            case 'yoga':
            case 'recovery':
                return <RecoveryContent data={data} />;
            default:
                return <RunContent data={data} />;
        }
    };

    return (
        <TouchableOpacity onPress={handlePress} activeOpacity={0.8}>
            <CardContainer>
                <View style={styles.header}>
                    <View style={styles.titleRow}>
                        <View style={[styles.iconContainer, { backgroundColor: config.color + '20' }]}>
                            <Ionicons name={config.icon as any} size={20} color={config.color} />
                        </View>
                        <Text style={styles.title}>{config.label}</Text>
                    </View>
                </View>
                {renderContent()}
                <CardFooter text="Tap to view details" />
            </CardContainer>
        </TouchableOpacity>
    );
}

// Run display
function RunContent({ data }: { data: ActivityData }) {
    return (
        <>
            <View style={styles.statsRow}>
                <StatItem value={data.distance ?? '—'} unit="km" label="Distance" />
                <StatItem value={data.pace ?? '—'} label="Pace" />
                <StatItem value={data.fatigue ?? '—'} label="Fatigue" />
                <StatItem value={data.consistency ? `${data.consistency}%` : '—'} label="Consistency" />
            </View>
            <View style={styles.miniChart}>
                {[0.3, 0.5, 0.2, 0.7, 0.4, 0.9, 0.5].map((h, i) => (
                    <View key={i} style={[styles.chartBar, { height: h * 40, backgroundColor: colors.accentBlue }]} />
                ))}
            </View>
        </>
    );
}

// Strength display
function StrengthContent({ data }: { data: ActivityData }) {
    return (
        <>
            <View style={styles.statsRow}>
                <StatItem value={data.total_sets ?? '—'} label="Sets" />
                <StatItem value={data.volume ?? '—'} unit="kg" label="Volume" />
                <StatItem value={data.rpe ?? '—'} label="RPE" />
            </View>
            {data.muscle_groups && data.muscle_groups.length > 0 && (
                <View style={styles.chipsRow}>
                    {data.muscle_groups.map((group, i) => (
                        <View key={i} style={styles.chip}>
                            <Text style={styles.chipText}>{group}</Text>
                        </View>
                    ))}
                </View>
            )}
        </>
    );
}

// Boxing display
function BoxingContent({ data }: { data: ActivityData }) {
    return (
        <>
            <View style={styles.statsRow}>
                <StatItem value={data.rounds ?? '—'} label="Rounds" />
                <StatItem value={data.duration ?? '—'} unit="min" label="Duration" />
                <StatItem value={data.fatigue ?? '—'} label="Effort" />
            </View>
            {data.session_focus && (
                <Text style={styles.sessionFocus}>Focus: {data.session_focus}</Text>
            )}
            {data.skill_chips && data.skill_chips.length > 0 && (
                <View style={styles.chipsRow}>
                    {data.skill_chips.map((skill, i) => (
                        <View key={i} style={[styles.chip, { backgroundColor: '#EF444415' }]}>
                            <Text style={[styles.chipText, { color: '#EF4444' }]}>{skill}</Text>
                        </View>
                    ))}
                </View>
            )}
        </>
    );
}

// Recovery/Mobility/Yoga display
function RecoveryContent({ data }: { data: ActivityData }) {
    return (
        <>
            <View style={styles.statsRow}>
                <StatItem value={data.duration ?? '—'} unit="min" label="Duration" />
                <StatItem value={data.focus_area ?? '—'} label="Focus" />
            </View>
            <View style={styles.recoveryNudge}>
                <Ionicons name="leaf-outline" size={14} color={colors.accentGreen} />
                <Text style={styles.recoveryNudgeText}>Great recovery session! +10 recovery credit</Text>
            </View>
        </>
    );
}

// Stat item component
function StatItem({ value, unit, label }: { value: string | number; unit?: string; label: string }) {
    return (
        <View style={styles.statItem}>
            <View style={styles.statValueRow}>
                <Text style={styles.statValue}>{value}</Text>
                {unit && <Text style={styles.statUnit}>{unit}</Text>}
            </View>
            <Text style={styles.statLabel}>{label}</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    header: {
        marginBottom: spacing.md,
    },
    titleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    iconContainer: {
        width: 36,
        height: 36,
        borderRadius: 12,
        alignItems: 'center',
        justifyContent: 'center',
    },
    title: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: spacing.md,
    },
    statItem: {
        alignItems: 'center',
    },
    statValueRow: {
        flexDirection: 'row',
        alignItems: 'baseline',
    },
    statValue: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    statUnit: {
        fontSize: 11,
        color: colors.textSecondary,
        marginLeft: 2,
    },
    statLabel: {
        ...typography.caption,
        color: colors.textTertiary,
    },
    miniChart: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        height: 40,
        marginBottom: spacing.sm,
    },
    chartBar: {
        width: 24,
        borderRadius: 4,
    },
    chipsRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.xs,
        marginBottom: spacing.sm,
    },
    chip: {
        backgroundColor: colors.surfaceSecondary,
        paddingHorizontal: spacing.sm,
        paddingVertical: 4,
        borderRadius: borderRadius.sm,
    },
    chipText: {
        fontSize: 11,
        fontWeight: '600',
        color: colors.textSecondary,
        textTransform: 'capitalize',
    },
    sessionFocus: {
        fontSize: 13,
        color: colors.textSecondary,
        marginBottom: spacing.sm,
    },
    recoveryNudge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        backgroundColor: colors.accentGreenLight,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.md,
    },
    recoveryNudgeText: {
        fontSize: 12,
        color: colors.accentGreen,
        fontWeight: '500',
    },
    shortcutsRow: {
        flexDirection: 'row',
        gap: spacing.sm,
        marginTop: spacing.md,
    },
    shortcutButton: {
        flex: 1,
        alignItems: 'center',
        paddingVertical: spacing.md,
        borderRadius: borderRadius.lg,
        gap: 4,
    },
    shortcutText: {
        fontSize: 11,
        fontWeight: '600',
    },
});

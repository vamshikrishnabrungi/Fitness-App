import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';

export default function SleepEducationScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Sleep</Text>
                <View style={{ width: 40 }} />
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                {/* Hero */}
                <View style={styles.heroSection}>
                    <View style={styles.heroIcon}>
                        <Ionicons name="moon" size={40} color="#3B82F6" />
                    </View>
                    <Text style={styles.heroTitle}>Sleep</Text>
                    <Text style={styles.heroDescription}>
                        Sleep is a measurement of your sleep quality from the previous night.
                        It is based on the longest sleep session of the day.
                    </Text>
                </View>

                {/* How Sleep is Calculated */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>How Sleep is calculated</Text>

                    <InfoCard
                        icon="time-outline"
                        iconColor="#3B82F6"
                        title="Time Asleep"
                        description="The total duration of your sleep session excluding awake segments."
                    />

                    <InfoCard
                        icon="moon-outline"
                        iconColor="#8B5CF6"
                        title="Sleep Stages"
                        description="The distribution of Light, Deep, Core, and REM sleep."
                    />

                    <InfoCard
                        icon="heart-outline"
                        iconColor="#DC2626"
                        title="Heart Rate Dip"
                        description="The difference between your daytime heart rate and your nighttime heart rate."
                    />

                    <InfoCard
                        icon="analytics-outline"
                        iconColor="#16A34A"
                        title="Sleep Efficiency"
                        description="The percentage of time spent asleep vs. time in bed."
                    />
                </View>

                {/* Related */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Related</Text>
                    <TouchableOpacity
                        style={styles.relatedButton}
                        onPress={() => router.push('/education/recovery')}
                    >
                        <View style={styles.relatedIcon}>
                            <Ionicons name="pulse" size={20} color="#8B5CF6" />
                        </View>
                        <Text style={styles.relatedText}>Recovery & HRV</Text>
                        <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={styles.relatedButton}
                        onPress={() => router.push('/health/biology')}
                    >
                        <View style={styles.relatedIcon}>
                            <Ionicons name="body" size={20} color="#3B82F6" />
                        </View>
                        <Text style={styles.relatedText}>Biology</Text>
                        <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                    </TouchableOpacity>
                </View>

                <View style={{ height: 100 }} />
            </ScrollView>
        </View>
    );
}

function InfoCard({
    icon,
    iconColor,
    title,
    description,
}: {
    icon: string;
    iconColor: string;
    title: string;
    description: string;
}) {
    return (
        <View style={styles.infoCard}>
            <View style={[styles.infoIcon, { backgroundColor: iconColor + '15' }]}>
                <Ionicons name={icon as any} size={18} color={iconColor} />
            </View>
            <View style={styles.infoContent}>
                <Text style={styles.infoTitle}>{title}</Text>
                <Text style={styles.infoDescription}>{description}</Text>
            </View>
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
        borderBottomColor: 'rgba(0,0,0,0.05)',
    },
    backButton: {
        padding: spacing.xs,
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    content: {
        flex: 1,
        paddingHorizontal: spacing.lg,
    },
    // Hero
    heroSection: {
        alignItems: 'center',
        paddingVertical: spacing.xxl,
    },
    heroIcon: {
        width: 80,
        height: 80,
        borderRadius: 24,
        backgroundColor: '#EFF6FF',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: spacing.lg,
    },
    heroTitle: {
        fontSize: 28,
        fontWeight: '800',
        color: colors.textPrimary,
        marginBottom: spacing.md,
    },
    heroDescription: {
        fontSize: 15,
        color: colors.textSecondary,
        textAlign: 'center',
        lineHeight: 24,
        paddingHorizontal: spacing.lg,
    },
    // Section
    section: {
        marginBottom: spacing.xxl,
    },
    sectionTitle: {
        fontSize: 13,
        fontWeight: '700',
        color: '#6B7280',
        letterSpacing: 0.5,
        marginBottom: spacing.md,
    },
    // Info Card
    infoCard: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        backgroundColor: '#FAFAFA',
        padding: spacing.md,
        borderRadius: 12,
        marginBottom: spacing.sm,
        gap: spacing.md,
    },
    infoIcon: {
        width: 36,
        height: 36,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
    },
    infoContent: {
        flex: 1,
    },
    infoTitle: {
        fontSize: 15,
        fontWeight: '600',
        color: colors.textPrimary,
        marginBottom: 4,
    },
    infoDescription: {
        fontSize: 13,
        color: colors.textSecondary,
        lineHeight: 18,
    },
    // Related
    relatedButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FAFAFA',
        padding: spacing.md,
        borderRadius: 12,
        marginBottom: spacing.sm,
        gap: spacing.md,
    },
    relatedIcon: {
        width: 40,
        height: 40,
        borderRadius: 12,
        backgroundColor: '#FFFFFF',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.08)',
    },
    relatedText: {
        flex: 1,
        fontSize: 15,
        fontWeight: '600',
        color: colors.textPrimary,
    },
});

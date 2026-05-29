/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';

export default function RecoveryEducationScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Recovery</Text>
                <View style={{ width: 40 }} />
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                {/* Hero */}
                <View style={styles.heroSection}>
                    <View style={styles.heroIcon}>
                        <Ionicons name="pulse" size={40} color="#8B5CF6" />
                    </View>
                    <Text style={styles.heroTitle}>Recovery</Text>
                    <Text style={styles.heroDescription}>
                        Recovery reflects your body's readiness for physical activities.
                        It is calculated once a day after waking up.
                    </Text>
                </View>

                {/* How to Interpret */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>How to interpret</Text>
                    <View style={styles.interpretCard}>
                        <View style={styles.interpretRow}>
                            <View style={[styles.interpretDot, { backgroundColor: '#16A34A' }]} />
                            <View style={styles.interpretContent}>
                                <Text style={styles.interpretLabel}>High Recovery</Text>
                                <Text style={styles.interpretDesc}>
                                    You're ready to take on physical challenges.
                                </Text>
                            </View>
                        </View>
                        <View style={styles.divider} />
                        <View style={styles.interpretRow}>
                            <View style={[styles.interpretDot, { backgroundColor: '#DC2626' }]} />
                            <View style={styles.interpretContent}>
                                <Text style={styles.interpretLabel}>Low Recovery</Text>
                                <Text style={styles.interpretDesc}>
                                    Take some rest and prioritize recovery.
                                </Text>
                            </View>
                        </View>
                    </View>
                </View>

                {/* How Recovery is Calculated */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>How Recovery is calculated</Text>

                    <InfoCard
                        icon="pulse"
                        iconColor="#8B5CF6"
                        title="Heart Rate Variability"
                        description="HRV is an indicator of your autonomic nervous system. Recovery score pulls HRV samples from the deepest stages of your sleep cycle."
                    />

                    <InfoCard
                        icon="heart"
                        iconColor="#DC2626"
                        title="Resting Heart Rate"
                        description="RHR measures how well your heart rate returns to normal after strenuous activity. Data is pulled from the deepest stages of your sleep cycle."
                    />

                    <InfoCard
                        icon="fitness"
                        iconColor="#F59E0B"
                        title="Respiratory Rate"
                        description="An increased respiratory rate could indicate fever, illness, or heightened stress levels."
                    />

                    <InfoCard
                        icon="water"
                        iconColor="#3B82F6"
                        title="Blood Oxygen"
                        description="A lower than normal SpO₂ level could impair muscle recovery and reduce overall energy levels."
                    />

                    <InfoCard
                        icon="thermometer"
                        iconColor="#EF4444"
                        title="Temperature"
                        description="High body temperature could indicate illness, fever, or overtraining."
                    />
                </View>

                {/* Related */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Related</Text>
                    <TouchableOpacity
                        style={styles.relatedButton}
                        onPress={() => router.push('/education/sleep')}
                    >
                        <View style={styles.relatedIcon}>
                            <Ionicons name="moon" size={20} color="#3B82F6" />
                        </View>
                        <Text style={styles.relatedText}>Sleep</Text>
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
        backgroundColor: '#F3E8FF',
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
    // Interpret
    interpretCard: {
        backgroundColor: '#FAFAFA',
        borderRadius: 16,
        padding: spacing.lg,
    },
    interpretRow: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.md,
    },
    interpretDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginTop: 4,
    },
    interpretContent: {
        flex: 1,
    },
    interpretLabel: {
        fontSize: 15,
        fontWeight: '600',
        color: colors.textPrimary,
        marginBottom: 2,
    },
    interpretDesc: {
        fontSize: 13,
        color: colors.textSecondary,
        lineHeight: 18,
    },
    divider: {
        height: 1,
        backgroundColor: 'rgba(0,0,0,0.05)',
        marginVertical: spacing.md,
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

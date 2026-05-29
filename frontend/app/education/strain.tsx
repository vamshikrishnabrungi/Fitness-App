import React, { useState } from 'react';
import { View, Text, StyleSheet, Dimensions, TouchableOpacity, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/utils/theme';

const { width } = Dimensions.get('window');

interface Page {
    title: string;
    description: string;
    items?: { icon: string; title: string; description: string }[];
}

const PAGES: Page[] = [
    {
        title: 'Strain',
        description: 'Strain is a continuous measurement of your cardio and muscular exertion throughout the day. It resets at midnight.',
        items: [
            {
                icon: 'analytics-outline',
                title: 'Strain is logarithmic',
                description: 'It will progressively get harder to increase.',
            },
            {
                icon: 'infinite-outline',
                title: 'Strain has no limit',
                description: 'It can go over 100%.',
            },
        ],
    },
    {
        title: 'How Strain works',
        description: 'Strain is calculated from three types of exertion:',
        items: [
            {
                icon: 'fitness-outline',
                title: 'Cardio exertion',
                description: 'Movement and HR data associated with your cardio activities.',
            },
            {
                icon: 'barbell-outline',
                title: 'Muscular exertion',
                description: 'Data associated strength training sessions (i.e. motion data, weights, reps, sets).',
            },
            {
                icon: 'walk-outline',
                title: 'Passive strain',
                description: 'HR data from activities that are not recorded (i.e. walking to the grocery store).',
            },
        ],
    },
];

export default function StrainEducationScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const [currentPage, setCurrentPage] = useState(0);

    const handleScroll = (event: any) => {
        const pageIndex = Math.round(event.nativeEvent.contentOffset.x / width);
        setCurrentPage(pageIndex);
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
                </TouchableOpacity>
                <View style={styles.dotsContainer}>
                    {PAGES.map((_, i) => (
                        <View
                            key={i}
                            style={[
                                styles.dot,
                                { opacity: currentPage === i ? 1 : 0.3 }
                            ]}
                        />
                    ))}
                </View>
                <View style={{ width: 40 }} />
            </View>

            {/* Pages */}
            <ScrollView
                horizontal
                pagingEnabled
                showsHorizontalScrollIndicator={false}
                onScroll={handleScroll}
                scrollEventThrottle={16}
            >
                {PAGES.map((page, i) => (
                    <View key={i} style={styles.page}>
                        <Text style={styles.pageTitle}>{page.title}</Text>
                        <Text style={styles.pageDescription}>{page.description}</Text>

                        {page.items && (
                            <View style={styles.itemsContainer}>
                                {page.items.map((item, j) => (
                                    <View key={j} style={styles.item}>
                                        <View style={styles.itemIcon}>
                                            <Ionicons name={item.icon as any} size={20} color={colors.textPrimary} />
                                        </View>
                                        <View style={styles.itemContent}>
                                            <Text style={styles.itemTitle}>{item.title}</Text>
                                            <Text style={styles.itemDescription}>{item.description}</Text>
                                        </View>
                                    </View>
                                ))}
                            </View>
                        )}
                    </View>
                ))}
            </ScrollView>

            {/* Footer */}
            <View style={styles.footer}>
                <TouchableOpacity onPress={() => router.back()} style={styles.doneButton}>
                    <Text style={styles.doneText}>Done</Text>
                    <Ionicons name="checkmark" size={18} color="#FFFFFF" />
                </TouchableOpacity>
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
    },
    backButton: {
        padding: spacing.xs,
    },
    dotsContainer: {
        flexDirection: 'row',
        gap: 8,
    },
    dot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: colors.textPrimary,
    },
    page: {
        width,
        paddingHorizontal: spacing.xl,
        paddingTop: spacing.xl,
    },
    pageTitle: {
        fontSize: 32,
        fontWeight: '800',
        color: colors.textPrimary,
        marginBottom: spacing.md,
    },
    pageDescription: {
        fontSize: 16,
        color: colors.textSecondary,
        lineHeight: 24,
        marginBottom: spacing.xl,
    },
    itemsContainer: {
        backgroundColor: '#F9FAFB',
        borderRadius: 16,
        padding: spacing.lg,
        gap: spacing.lg,
    },
    item: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.md,
    },
    itemIcon: {
        width: 36,
        height: 36,
        borderRadius: 10,
        backgroundColor: '#FFFFFF',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.08)',
    },
    itemContent: {
        flex: 1,
    },
    itemTitle: {
        fontSize: 15,
        fontWeight: '700',
        color: colors.textPrimary,
        marginBottom: 4,
    },
    itemDescription: {
        fontSize: 14,
        color: colors.textSecondary,
        lineHeight: 20,
    },
    footer: {
        paddingHorizontal: spacing.xl,
        paddingVertical: spacing.lg,
    },
    doneButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        backgroundColor: colors.textPrimary,
        paddingVertical: 16,
        borderRadius: 28,
    },
    doneText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#FFFFFF',
    },
});

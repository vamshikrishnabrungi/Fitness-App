import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, spacing } from '../../utils/theme';

interface EmptyStateProps {
    icon?: string;
    title: string;
    subtitle?: string;
    ctaLabel?: string;
    ctaSecondaryLabel?: string;
    onCtaPress?: () => void;
    onCtaSecondaryPress?: () => void;
    variant?: 'default' | 'compact';
}

/**
 * EmptyState - Shows when no data is available
 * Icon + title + description + CTA button(s)
 */
export function EmptyState({
    icon = 'pulse-outline',
    title,
    subtitle,
    ctaLabel,
    ctaSecondaryLabel,
    onCtaPress,
    onCtaSecondaryPress,
    variant = 'default',
}: EmptyStateProps) {
    return (
        <View style={[styles.container, variant === 'compact' && styles.compact]}>
            <View style={styles.iconContainer}>
                <Ionicons name={icon as any} size={variant === 'compact' ? 24 : 32} color={colors.textTertiary} />
            </View>
            <Text style={[styles.title, variant === 'compact' && styles.titleCompact]}>{title}</Text>
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
            <View style={styles.ctaRow}>
                {ctaLabel && onCtaPress && (
                    <TouchableOpacity style={styles.ctaButton} onPress={onCtaPress}>
                        <Text style={styles.ctaText}>{ctaLabel}</Text>
                        <Ionicons name="chevron-forward" size={14} color="#22C55E" />
                    </TouchableOpacity>
                )}
                {ctaSecondaryLabel && onCtaSecondaryPress && (
                    <TouchableOpacity style={styles.ctaButtonSecondary} onPress={onCtaSecondaryPress}>
                        <Text style={styles.ctaTextSecondary}>{ctaSecondaryLabel}</Text>
                    </TouchableOpacity>
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        alignItems: 'center',
        padding: spacing.xl,
    },
    compact: {
        padding: spacing.md,
    },
    iconContainer: {
        width: 64,
        height: 64,
        borderRadius: 32,
        backgroundColor: 'rgba(0,0,0,0.04)',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: spacing.md,
    },
    title: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.textPrimary,
        marginBottom: 6,
        textAlign: 'center',
    },
    titleCompact: {
        fontSize: 14,
    },
    subtitle: {
        fontSize: 13,
        color: colors.textSecondary,
        textAlign: 'center',
        lineHeight: 18,
        marginBottom: spacing.md,
        paddingHorizontal: spacing.lg,
    },
    ctaRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.md,
    },
    ctaButton: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        paddingHorizontal: 16,
        paddingVertical: 10,
        borderRadius: 20,
    },
    ctaText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#22C55E',
    },
    ctaButtonSecondary: {
        paddingHorizontal: 16,
        paddingVertical: 10,
    },
    ctaTextSecondary: {
        fontSize: 14,
        fontWeight: '500',
        color: colors.textSecondary,
    },
});

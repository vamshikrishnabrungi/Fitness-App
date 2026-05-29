import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing } from '../../utils/theme';

interface CardHeaderProps {
    title: string;
    icon?: React.ReactNode;
    badge?: React.ReactNode;
    onInfoPress?: () => void;
    rightElement?: React.ReactNode;
}

/**
 * CardHeader - Consistent header for all Home cards
 * Title + optional info icon + optional badge
 */
export function CardHeader({
    title,
    icon,
    badge,
    onInfoPress,
    rightElement,
}: CardHeaderProps) {
    return (
        <View style={styles.container}>
            <View style={styles.left}>
                {icon && <View style={styles.iconContainer}>{icon}</View>}
                <Text style={styles.title}>{title}</Text>
            </View>
            <View style={styles.right}>
                {badge}
                {onInfoPress && (
                    <TouchableOpacity onPress={onInfoPress} style={styles.infoButton}>
                        <Ionicons name="information-circle-outline" size={22} color={colors.textSecondary} />
                    </TouchableOpacity>
                )}
                {rightElement}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.md,
    },
    left: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    iconContainer: {
        width: 32,
        height: 32,
        borderRadius: 10,
        backgroundColor: colors.surfaceSecondary,
        alignItems: 'center',
        justifyContent: 'center',
    },
    title: {
        ...typography.h4,
        color: colors.textPrimary,
    },
    right: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    infoButton: {
        padding: 4,
    },
});

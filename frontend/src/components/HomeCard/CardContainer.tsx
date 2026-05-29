import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { colors, borderRadius, spacing } from '../../utils/theme';

interface CardContainerProps {
    children: React.ReactNode;
    style?: ViewStyle;
    variant?: 'default' | 'outlined' | 'subtle';
    noPadding?: boolean;
}

/**
 * CardContainer - Unified card wrapper for all Home cards
 * White background, subtle borders, no gradients
 * Consistent padding (24px), radius (16px)
 */
export function CardContainer({
    children,
    style,
    variant = 'default',
    noPadding = false,
}: CardContainerProps) {
    const containerStyle = [
        styles.container,
        variant === 'outlined' && styles.outlined,
        variant === 'subtle' && styles.subtle,
        style,
    ];

    return (
        <View style={containerStyle}>
            <View style={noPadding ? undefined : styles.content}>
                {children}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        borderRadius: borderRadius.lg, // 16px
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.08)',
    },
    outlined: {
        borderWidth: 1.5,
        borderColor: 'rgba(0,0,0,0.12)',
        borderStyle: 'dashed',
    },
    subtle: {
        borderColor: 'rgba(0,0,0,0.04)',
        backgroundColor: '#FAFAFA',
    },
    content: {
        padding: spacing.xl, // 24px
    },
});

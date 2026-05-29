import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing } from '../../utils/theme';

interface CardFooterProps {
    text: string;
    onPress?: () => void;
    showChevron?: boolean;
}

/**
 * CardFooter - CTA row with "Tap for details" hint
 */
export function CardFooter({ text, onPress, showChevron = true }: CardFooterProps) {
    const content = (
        <View style={styles.container}>
            <Text style={styles.text}>{text}</Text>
            {showChevron && (
                <Ionicons name="chevron-forward" size={16} color={colors.textTertiary} />
            )}
        </View>
    );

    if (onPress) {
        return (
            <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
                {content}
            </TouchableOpacity>
        );
    }

    return content;
}

const styles = StyleSheet.create({
    container: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 4,
        paddingTop: spacing.md,
        borderTopWidth: 1,
        borderTopColor: 'rgba(0,0,0,0.05)',
        marginTop: spacing.md,
    },
    text: {
        fontSize: 12,
        color: colors.textTertiary,
        fontWeight: '500',
    },
});

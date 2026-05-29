import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors, typography } from '../utils/theme';

interface CircularProgressProps {
    progress: number; // 0-100
    size?: number;
    strokeWidth?: number;
    color?: string;
    trackColor?: string;
    value?: string;
    label?: string;
    showPercentage?: boolean;
    style?: ViewStyle;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
    progress,
    size = 70,
    strokeWidth = 6,
    color = colors.accentOrange,
    trackColor = colors.progressTrack,
    value,
    label,
    showPercentage = false,
    style,
}) => {
    const clampedProgress = Math.min(100, Math.max(0, progress));

    return (
        <View style={[styles.container, { width: size, height: size }, style]}>
            {/* SVG-like circle using Views */}
            <View style={[styles.track, {
                width: size,
                height: size,
                borderRadius: size / 2,
                borderWidth: strokeWidth,
                borderColor: trackColor,
            }]} />

            {/* Progress arc - using a rotated border technique */}
            <View style={[styles.progressWrapper, { width: size, height: size }]}>
                <View
                    style={[
                        styles.progressArc,
                        {
                            width: size,
                            height: size,
                            borderRadius: size / 2,
                            borderWidth: strokeWidth,
                            borderColor: color,
                            borderTopColor: clampedProgress > 25 ? color : 'transparent',
                            borderRightColor: clampedProgress > 50 ? color : 'transparent',
                            borderBottomColor: clampedProgress > 75 ? color : 'transparent',
                            borderLeftColor: 'transparent',
                            transform: [{ rotate: '-90deg' }],
                        },
                    ]}
                />
            </View>

            {/* Center content */}
            <View style={styles.centerContent}>
                {showPercentage ? (
                    <>
                        <Text style={[styles.percentValue, { color }]}>{Math.round(clampedProgress)}%</Text>
                        {label && <Text style={styles.label}>{label}</Text>}
                    </>
                ) : (
                    <>
                        {value && <Text style={styles.value}>{value}</Text>}
                        {label && <Text style={styles.label}>{label}</Text>}
                    </>
                )}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        position: 'relative',
        justifyContent: 'center',
        alignItems: 'center',
    },
    track: {
        position: 'absolute',
    },
    progressWrapper: {
        position: 'absolute',
    },
    progressArc: {
        position: 'absolute',
    },
    centerContent: {
        position: 'absolute',
        justifyContent: 'center',
        alignItems: 'center',
    },
    value: {
        ...typography.h4,
        color: colors.textPrimary,
        fontWeight: '600',
    },
    percentValue: {
        fontSize: 14,
        fontWeight: '700',
    },
    label: {
        ...typography.caption,
        color: colors.textTertiary,
        fontSize: 10,
        marginTop: 2,
    },
});

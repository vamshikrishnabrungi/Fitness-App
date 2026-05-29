import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Modal,
    TouchableOpacity,
} from 'react-native';
import { BlurView } from 'expo-blur';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors, spacing } from '../utils/theme';

const MOODS = ['😫', '😔', '😐', '🙂', '😄'];
const SLEEP_STARS = [1, 2, 3, 4, 5];

interface MorningCheckInModalProps {
    visible: boolean;
    onClose: () => void;
    onComplete: (data: CheckInData) => void;
}

interface CheckInData {
    mood: number;
    sleepQuality: number;
}

const STORAGE_KEY = 'morning_checkin_date';

export function MorningCheckInModal({ visible, onClose, onComplete }: MorningCheckInModalProps) {
    const [mood, setMood] = useState<number | null>(null);
    const [sleepQuality, setSleepQuality] = useState<number>(0);

    const isComplete = mood !== null && sleepQuality > 0;

    const handleComplete = async () => {
        if (!isComplete) return;

        // Save today's date to prevent showing again
        const today = new Date().toDateString();
        await AsyncStorage.setItem(STORAGE_KEY, today);

        onComplete({
            mood: mood!,
            sleepQuality,
        });
    };

    return (
        <Modal
            visible={visible}
            transparent
            animationType="fade"
            statusBarTranslucent
        >
            <BlurView intensity={80} tint="light" style={styles.blurContainer}>
                <View style={styles.backdrop} />
                <View style={styles.modalContent}>
                    {/* Header */}
                    <View style={styles.header}>
                        <View style={styles.sunIcon}>
                            <Text style={styles.sunEmoji}>☀️</Text>
                        </View>
                        <Text style={styles.title}>Morning Check-in</Text>
                    </View>

                    {/* Question */}
                    <Text style={styles.question}>How are you feeling today?</Text>

                    {/* Mood Selection */}
                    <View style={styles.moodRow}>
                        {MOODS.map((emoji, index) => (
                            <TouchableOpacity
                                key={index}
                                style={[
                                    styles.moodButton,
                                    mood === index && styles.moodButtonActive,
                                ]}
                                onPress={() => setMood(index)}
                            >
                                <Text style={styles.moodEmoji}>{emoji}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    {/* Sleep Quality */}
                    <View style={styles.sleepSection}>
                        <Text style={styles.levelLabel}>Sleep Quality</Text>
                        <View style={styles.starRow}>
                            {SLEEP_STARS.map((star) => (
                                <TouchableOpacity
                                    key={star}
                                    onPress={() => setSleepQuality(star)}
                                    style={styles.starButton}
                                >
                                    <Ionicons
                                        name={sleepQuality >= star ? 'star' : 'star-outline'}
                                        size={28}
                                        color={sleepQuality >= star ? '#F59E0B' : '#D1D5DB'}
                                    />
                                </TouchableOpacity>
                            ))}
                        </View>
                    </View>

                    {/* Complete Button */}
                    <TouchableOpacity
                        style={[
                            styles.completeButton,
                            !isComplete && styles.completeButtonDisabled,
                        ]}
                        onPress={handleComplete}
                        disabled={!isComplete}
                    >
                        <Ionicons
                            name="checkmark-circle"
                            size={20}
                            color={isComplete ? '#FFFFFF' : '#9CA3AF'}
                        />
                        <Text style={[
                            styles.completeText,
                            !isComplete && styles.completeTextDisabled,
                        ]}>
                            Complete Check-in
                        </Text>
                    </TouchableOpacity>
                </View>
            </BlurView>
        </Modal>
    );
}

// Helper function to check if modal should show
export async function shouldShowMorningCheckIn(): Promise<boolean> {
    try {
        const lastCheckIn = await AsyncStorage.getItem(STORAGE_KEY);
        const today = new Date().toDateString();

        // Show if no check-in logged today AND it's morning (before noon)
        const hour = new Date().getHours();
        const isMorning = hour >= 5 && hour < 12;

        return lastCheckIn !== today && isMorning;
    } catch {
        return false;
    }
}

const styles = StyleSheet.create({
    blurContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    backdrop: {
        ...StyleSheet.absoluteFillObject,
    },
    modalContent: {
        backgroundColor: '#FFFFFF',
        borderRadius: 24,
        padding: spacing.xl,
        width: '90%',
        maxWidth: 380,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.15,
        shadowRadius: 30,
        elevation: 20,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        marginBottom: spacing.lg,
    },
    sunIcon: {
        width: 44,
        height: 44,
        borderRadius: 14,
        backgroundColor: '#FEF9C3',
        alignItems: 'center',
        justifyContent: 'center',
    },
    sunEmoji: {
        fontSize: 22,
    },
    title: {
        fontSize: 20,
        fontWeight: '700',
        color: colors.textPrimary,
    },
    question: {
        fontSize: 15,
        color: '#6B7280',
        marginBottom: spacing.lg,
    },
    // Mood
    moodRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: spacing.xl,
    },
    moodButton: {
        width: 52,
        height: 52,
        borderRadius: 16,
        backgroundColor: '#F9FAFB',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 2,
        borderColor: 'transparent',
    },
    moodButtonActive: {
        borderColor: '#F59E0B',
        backgroundColor: '#FEF3C7',
    },
    moodEmoji: {
        fontSize: 26,
    },
    levelLabel: {
        fontSize: 13,
        fontWeight: '600',
        color: colors.textPrimary,
        marginBottom: 8,
    },
    // Sleep
    sleepSection: {
        marginBottom: spacing.xl,
    },
    starRow: {
        flexDirection: 'row',
        gap: 8,
    },
    starButton: {
        padding: 4,
    },
    // Complete
    completeButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        backgroundColor: '#1F2937',
        paddingVertical: 14,
        borderRadius: 16,
    },
    completeButtonDisabled: {
        backgroundColor: '#E5E7EB',
    },
    completeText: {
        fontSize: 15,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    completeTextDisabled: {
        color: '#9CA3AF',
    },
});

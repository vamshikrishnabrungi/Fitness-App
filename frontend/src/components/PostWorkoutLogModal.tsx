import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    Modal,
    TextInput,
    ActivityIndicator,
    Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../utils/api';
import { colors, typography, spacing, borderRadius } from '../utils/theme';

// Quick mood/RPE options
const MOODS = [
    { value: 'great', emoji: '😄', label: 'Great' },
    { value: 'good', emoji: '🙂', label: 'Good' },
    { value: 'okay', emoji: '😐', label: 'Okay' },
    { value: 'bad', emoji: '😟', label: 'Bad' },
    { value: 'awful', emoji: '😢', label: 'Awful' },
];

interface PostWorkoutLogModalProps {
    visible: boolean;
    onClose: () => void;
    onComplete: () => void;
    workoutId?: string;
    runId?: string;
    workoutType: 'workout' | 'run';
    workoutSummary?: {
        duration?: number;
        distance?: number;
        xpEarned?: number;
        title?: string;
    };
}

export function PostWorkoutLogModal({
    visible,
    onClose,
    onComplete,
    workoutId,
    runId,
    workoutType,
    workoutSummary,
}: PostWorkoutLogModalProps) {
    const [mood, setMood] = useState<string>('');
    const [rpe, setRpe] = useState<number | null>(null);
    const [note, setNote] = useState('');
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        if (!mood) {
            Alert.alert('Missing Info', 'Please select how you felt');
            return;
        }
        if (rpe === null) {
            Alert.alert('Missing Info', 'Please rate the effort level');
            return;
        }

        try {
            setSaving(true);
            await api.post('/log/quick', {
                mood,
                energy: 'normal', // Default for post-workout
                stress: 'calm', // Default for post-workout
                sleep_quality: 3, // Default
                soreness_regions: [],
                note: note.trim(),
                rpe,
                linked_workout_id: workoutId,
                linked_run_id: runId,
            });
            onComplete();
        } catch (error) {
            console.error('Error saving log:', error);
            Alert.alert('Error', 'Failed to save. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const handleSkip = () => {
        onClose();
    };

    return (
        <Modal
            visible={visible}
            transparent
            animationType="slide"
            onRequestClose={onClose}
        >
            <View style={styles.overlay}>
                <View style={styles.modal}>
                    {/* Celebration Header */}
                    <LinearGradient
                        colors={['#4CAF50', '#2E7D32']}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 0 }}
                        style={styles.celebrationHeader}
                    >
                        <Ionicons name="trophy" size={32} color="#FFD700" />
                        <Text style={styles.celebrationText}>
                            {workoutType === 'run' ? 'Run Complete!' : 'Workout Complete!'}
                        </Text>
                        {workoutSummary && (
                            <View style={styles.summaryRow}>
                                {workoutSummary.duration && (
                                    <View style={styles.summaryItem}>
                                        <Text style={styles.summaryValue}>{Math.round(workoutSummary.duration / 60)}</Text>
                                        <Text style={styles.summaryLabel}>min</Text>
                                    </View>
                                )}
                                {workoutSummary.distance && (
                                    <View style={styles.summaryItem}>
                                        <Text style={styles.summaryValue}>{workoutSummary.distance.toFixed(2)}</Text>
                                        <Text style={styles.summaryLabel}>km</Text>
                                    </View>
                                )}
                                {workoutSummary.xpEarned && (
                                    <View style={styles.summaryItem}>
                                        <Text style={styles.summaryValue}>+{workoutSummary.xpEarned}</Text>
                                        <Text style={styles.summaryLabel}>XP</Text>
                                    </View>
                                )}
                            </View>
                        )}
                    </LinearGradient>

                    {/* Quick Log Section */}
                    <View style={styles.logSection}>
                        <Text style={styles.sectionTitle}>How do you feel?</Text>
                        <View style={styles.moodRow}>
                            {MOODS.map((item) => (
                                <TouchableOpacity
                                    key={item.value}
                                    style={[
                                        styles.moodButton,
                                        mood === item.value && styles.moodButtonActive,
                                    ]}
                                    onPress={() => setMood(item.value)}
                                >
                                    <Text style={styles.moodEmoji}>{item.emoji}</Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={styles.sectionTitle}>How hard was that? (RPE)</Text>
                        <View style={styles.rpeRow}>
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => (
                                <TouchableOpacity
                                    key={value}
                                    style={[
                                        styles.rpeButton,
                                        rpe === value && styles.rpeButtonActive,
                                        rpe === value && value <= 3 && { backgroundColor: '#4CAF50' },
                                        rpe === value && value >= 4 && value <= 6 && { backgroundColor: '#FFC107' },
                                        rpe === value && value >= 7 && value <= 8 && { backgroundColor: '#FF9800' },
                                        rpe === value && value >= 9 && { backgroundColor: '#F44336' },
                                    ]}
                                    onPress={() => setRpe(value)}
                                >
                                    <Text style={[
                                        styles.rpeText,
                                        rpe === value && styles.rpeTextActive,
                                    ]}>
                                        {value}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                        <Text style={styles.rpeHint}>
                            {rpe === null ? '1 = Easy · 10 = Max effort' :
                                rpe <= 3 ? 'Easy effort ✓' :
                                    rpe <= 6 ? 'Moderate effort' :
                                        rpe <= 8 ? 'Hard effort 💪' : 'Maximum effort 🔥'}
                        </Text>

                        <Text style={styles.sectionTitle}>Notes (optional)</Text>
                        <TextInput
                            style={styles.noteInput}
                            placeholder="How did the session go?"
                            placeholderTextColor={colors.textTertiary}
                            value={note}
                            onChangeText={setNote}
                            multiline
                            numberOfLines={2}
                            maxLength={200}
                        />
                    </View>

                    {/* Actions */}
                    <View style={styles.actions}>
                        <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
                            <Text style={styles.skipButtonText}>Skip</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={[styles.saveButton, saving && styles.saveButtonDisabled]}
                            onPress={handleSave}
                            disabled={saving}
                        >
                            {saving ? (
                                <ActivityIndicator color={colors.background} size="small" />
                            ) : (
                                <>
                                    <Ionicons name="checkmark" size={20} color={colors.background} />
                                    <Text style={styles.saveButtonText}>Save Log</Text>
                                </>
                            )}
                        </TouchableOpacity>
                    </View>
                </View>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'flex-end',
    },
    modal: {
        backgroundColor: colors.background,
        borderTopLeftRadius: borderRadius.xl,
        borderTopRightRadius: borderRadius.xl,
        maxHeight: '85%',
    },
    celebrationHeader: {
        padding: spacing.lg,
        alignItems: 'center',
        borderTopLeftRadius: borderRadius.xl,
        borderTopRightRadius: borderRadius.xl,
    },
    celebrationText: {
        ...typography.h2,
        color: colors.background,
        marginTop: spacing.sm,
    },
    summaryRow: {
        flexDirection: 'row',
        gap: spacing.xl,
        marginTop: spacing.md,
    },
    summaryItem: {
        alignItems: 'center',
    },
    summaryValue: {
        ...typography.stat,
        color: colors.background,
    },
    summaryLabel: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.8)',
    },
    logSection: {
        padding: spacing.lg,
    },
    sectionTitle: {
        ...typography.h4,
        color: colors.textPrimary,
        marginBottom: spacing.sm,
        marginTop: spacing.md,
    },
    moodRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    moodButton: {
        width: 52,
        height: 52,
        borderRadius: 26,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: colors.surface,
        borderWidth: 2,
        borderColor: colors.border,
    },
    moodButtonActive: {
        backgroundColor: colors.accentGreenLight,
        borderColor: colors.accentGreen,
    },
    moodEmoji: {
        fontSize: 24,
    },
    rpeRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.xs,
    },
    rpeButton: {
        width: 36,
        height: 36,
        borderRadius: 18,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: colors.surface,
        borderWidth: 1,
        borderColor: colors.border,
    },
    rpeButtonActive: {
        borderColor: 'transparent',
    },
    rpeText: {
        ...typography.bodySemibold,
        fontSize: 14,
        color: colors.textSecondary,
    },
    rpeTextActive: {
        color: colors.background,
    },
    rpeHint: {
        ...typography.caption,
        color: colors.textSecondary,
        textAlign: 'center',
        marginTop: spacing.sm,
    },
    noteInput: {
        backgroundColor: colors.surface,
        borderRadius: borderRadius.md,
        borderWidth: 1,
        borderColor: colors.border,
        padding: spacing.md,
        color: colors.textPrimary,
        ...typography.body,
        minHeight: 60,
        textAlignVertical: 'top',
    },
    actions: {
        flexDirection: 'row',
        gap: spacing.md,
        padding: spacing.lg,
        paddingTop: 0,
        paddingBottom: spacing.xl,
    },
    skipButton: {
        flex: 1,
        paddingVertical: spacing.md,
        alignItems: 'center',
        borderRadius: borderRadius.lg,
        borderWidth: 1,
        borderColor: colors.border,
    },
    skipButtonText: {
        ...typography.bodySemibold,
        color: colors.textSecondary,
    },
    saveButton: {
        flex: 2,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.sm,
        paddingVertical: spacing.md,
        backgroundColor: colors.accentGreen,
        borderRadius: borderRadius.lg,
    },
    saveButtonDisabled: {
        opacity: 0.6,
    },
    saveButtonText: {
        ...typography.bodySemibold,
        color: colors.background,
    },
});

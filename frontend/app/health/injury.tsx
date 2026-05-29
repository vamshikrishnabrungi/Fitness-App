import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    TextInput,
    ActivityIndicator,
    Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

// Body regions for injury selection
const BODY_REGIONS = [
    { id: 'head', label: 'Head', icon: 'ellipse-outline' },
    { id: 'neck', label: 'Neck', icon: 'remove-outline' },
    { id: 'left_shoulder', label: 'Left Shoulder', icon: 'radio-button-off' },
    { id: 'right_shoulder', label: 'Right Shoulder', icon: 'radio-button-off' },
    { id: 'upper_back', label: 'Upper Back', icon: 'square-outline' },
    { id: 'lower_back', label: 'Lower Back', icon: 'square-outline' },
    { id: 'chest', label: 'Chest', icon: 'square-outline' },
    { id: 'left_arm', label: 'Left Arm', icon: 'remove-outline' },
    { id: 'right_arm', label: 'Right Arm', icon: 'remove-outline' },
    { id: 'left_elbow', label: 'Left Elbow', icon: 'radio-button-off' },
    { id: 'right_elbow', label: 'Right Elbow', icon: 'radio-button-off' },
    { id: 'left_wrist', label: 'Left Wrist', icon: 'radio-button-off' },
    { id: 'right_wrist', label: 'Right Wrist', icon: 'radio-button-off' },
    { id: 'hip', label: 'Hip', icon: 'square-outline' },
    { id: 'left_quad', label: 'Left Quad', icon: 'remove-outline' },
    { id: 'right_quad', label: 'Right Quad', icon: 'remove-outline' },
    { id: 'left_hamstring', label: 'Left Hamstring', icon: 'remove-outline' },
    { id: 'right_hamstring', label: 'Right Hamstring', icon: 'remove-outline' },
    { id: 'left_knee', label: 'Left Knee', icon: 'radio-button-off' },
    { id: 'right_knee', label: 'Right Knee', icon: 'radio-button-off' },
    { id: 'left_calf', label: 'Left Calf', icon: 'remove-outline' },
    { id: 'right_calf', label: 'Right Calf', icon: 'remove-outline' },
    { id: 'left_ankle', label: 'Left Ankle', icon: 'radio-button-off' },
    { id: 'right_ankle', label: 'Right Ankle', icon: 'radio-button-off' },
    { id: 'left_foot', label: 'Left Foot', icon: 'footsteps-outline' },
    { id: 'right_foot', label: 'Right Foot', icon: 'footsteps-outline' },
];

const READINESS_OPTIONS = [
    { value: 'green', label: 'Ready to Train', color: '#4CAF50', description: 'Full training allowed' },
    { value: 'yellow', label: 'Modified Training', color: '#FFC107', description: 'Avoid aggravating movements' },
    { value: 'red', label: 'Rest Required', color: '#F44336', description: 'No training on this area' },
];

export default function InjuryLogScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    const [saving, setSaving] = useState(false);
    const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
    const [painLevel, setPainLevel] = useState<number>(5);
    const [readiness, setReadiness] = useState<string>('yellow');
    const [notes, setNotes] = useState('');

    const handleSave = async () => {
        if (!selectedRegion) {
            Alert.alert('Select Region', 'Please select the affected body region.');
            return;
        }

        try {
            setSaving(true);
            await api.post('/health/injuries', {
                body_region: selectedRegion,
                pain_level: painLevel,
                readiness,
                description: notes.trim() || undefined,
            });

            Alert.alert('Logged', 'Injury has been recorded.', [
                { text: 'OK', onPress: () => router.back() }
            ]);
        } catch (error) {
            console.error('Error logging injury:', error);
            Alert.alert('Error', 'Failed to log injury. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="close" size={24} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Log Injury</Text>
                <View style={{ width: 40 }} />
            </View>

            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                {/* Body Region Selection */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Affected Area</Text>
                    <View style={styles.regionsGrid}>
                        {BODY_REGIONS.map((region) => (
                            <TouchableOpacity
                                key={region.id}
                                style={[
                                    styles.regionButton,
                                    selectedRegion === region.id && styles.regionButtonActive,
                                ]}
                                onPress={() => setSelectedRegion(region.id)}
                            >
                                <Text
                                    style={[
                                        styles.regionLabel,
                                        selectedRegion === region.id && styles.regionLabelActive,
                                    ]}
                                    numberOfLines={1}
                                >
                                    {region.label}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                {/* Pain Level */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Pain Level</Text>
                    <View style={styles.painContainer}>
                        <View style={styles.painScale}>
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((level) => (
                                <TouchableOpacity
                                    key={level}
                                    style={[
                                        styles.painButton,
                                        painLevel === level && styles.painButtonActive,
                                        painLevel === level && level <= 3 && { backgroundColor: '#4CAF50' },
                                        painLevel === level && level >= 4 && level <= 6 && { backgroundColor: '#FFC107' },
                                        painLevel === level && level >= 7 && level <= 8 && { backgroundColor: '#FF9800' },
                                        painLevel === level && level >= 9 && { backgroundColor: '#F44336' },
                                    ]}
                                    onPress={() => setPainLevel(level)}
                                >
                                    <Text style={[
                                        styles.painText,
                                        painLevel === level && styles.painTextActive,
                                    ]}>
                                        {level}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                        <View style={styles.painLabels}>
                            <Text style={styles.painLabel}>Mild</Text>
                            <Text style={styles.painLabel}>Moderate</Text>
                            <Text style={styles.painLabel}>Severe</Text>
                        </View>
                    </View>
                </View>

                {/* Readiness Status */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Training Readiness</Text>
                    {READINESS_OPTIONS.map((option) => (
                        <TouchableOpacity
                            key={option.value}
                            style={[
                                styles.readinessOption,
                                readiness === option.value && { backgroundColor: option.color + '15', borderColor: option.color },
                            ]}
                            onPress={() => setReadiness(option.value)}
                        >
                            <View style={[styles.readinessIndicator, { backgroundColor: option.color }]} />
                            <View style={styles.readinessInfo}>
                                <Text style={[
                                    styles.readinessLabel,
                                    readiness === option.value && { color: option.color },
                                ]}>
                                    {option.label}
                                </Text>
                                <Text style={styles.readinessDescription}>{option.description}</Text>
                            </View>
                            {readiness === option.value && (
                                <Ionicons name="checkmark-circle" size={22} color={option.color} />
                            )}
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Notes */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Notes (Optional)</Text>
                    <TextInput
                        style={styles.notesInput}
                        placeholder="Describe the injury, how it happened, etc."
                        placeholderTextColor={colors.textTertiary}
                        value={notes}
                        onChangeText={setNotes}
                        multiline
                        numberOfLines={3}
                        maxLength={500}
                    />
                    <Text style={styles.charCount}>{notes.length}/500</Text>
                </View>

                <View style={{ height: 120 }} />
            </ScrollView>

            {/* Save Button */}
            <View style={[styles.bottomBar, { paddingBottom: insets.bottom + 16 }]}>
                <TouchableOpacity
                    style={[styles.saveButton, saving && styles.saveButtonDisabled]}
                    onPress={handleSave}
                    disabled={saving}
                >
                    {saving ? (
                        <ActivityIndicator size="small" color={colors.background} />
                    ) : (
                        <>
                            <Ionicons name="medkit" size={20} color={colors.background} />
                            <Text style={styles.saveButtonText}>Log Injury</Text>
                        </>
                    )}
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.md,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    backButton: {
        padding: spacing.xs,
    },
    headerTitle: {
        ...typography.h2,
        color: colors.textPrimary,
    },
    content: {
        flex: 1,
        paddingHorizontal: spacing.md,
    },
    section: {
        marginTop: spacing.lg,
    },
    sectionTitle: {
        ...typography.h4,
        color: colors.textPrimary,
        marginBottom: spacing.md,
    },
    // Regions Grid
    regionsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.xs,
    },
    regionButton: {
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.xs,
        borderRadius: borderRadius.full,
        borderWidth: 1,
        borderColor: colors.border,
        backgroundColor: colors.surface,
    },
    regionButtonActive: {
        backgroundColor: colors.accentOrange,
        borderColor: colors.accentOrange,
    },
    regionLabel: {
        ...typography.caption,
        color: colors.textSecondary,
    },
    regionLabelActive: {
        color: colors.background,
        fontWeight: '600',
    },
    // Pain Scale
    painContainer: {
        marginBottom: spacing.md,
    },
    painScale: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    painButton: {
        width: 32,
        height: 32,
        borderRadius: 16,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: colors.surface,
        borderWidth: 1,
        borderColor: colors.border,
    },
    painButtonActive: {
        borderColor: 'transparent',
    },
    painText: {
        ...typography.bodySemibold,
        fontSize: 12,
        color: colors.textSecondary,
    },
    painTextActive: {
        color: colors.background,
    },
    painLabels: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: spacing.sm,
        paddingHorizontal: spacing.sm,
    },
    painLabel: {
        ...typography.caption,
        color: colors.textTertiary,
    },
    // Readiness
    readinessOption: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: spacing.md,
        borderRadius: borderRadius.lg,
        borderWidth: 2,
        borderColor: colors.border,
        marginBottom: spacing.sm,
    },
    readinessIndicator: {
        width: 16,
        height: 16,
        borderRadius: 8,
        marginRight: spacing.md,
    },
    readinessInfo: {
        flex: 1,
    },
    readinessLabel: {
        ...typography.bodySemibold,
        color: colors.textPrimary,
        marginBottom: 2,
    },
    readinessDescription: {
        ...typography.caption,
        color: colors.textSecondary,
    },
    // Notes
    notesInput: {
        backgroundColor: colors.surface,
        borderRadius: borderRadius.lg,
        borderWidth: 1,
        borderColor: colors.border,
        padding: spacing.md,
        color: colors.textPrimary,
        ...typography.body,
        minHeight: 80,
        textAlignVertical: 'top',
    },
    charCount: {
        ...typography.caption,
        color: colors.textTertiary,
        textAlign: 'right',
        marginTop: spacing.xs,
    },
    // Bottom Bar
    bottomBar: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        paddingHorizontal: spacing.md,
        paddingTop: spacing.md,
        backgroundColor: colors.background,
        borderTopWidth: 1,
        borderTopColor: colors.border,
    },
    saveButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: spacing.sm,
        paddingVertical: spacing.md,
        backgroundColor: colors.accentOrange,
        borderRadius: borderRadius.lg,
    },
    saveButtonDisabled: {
        opacity: 0.6,
    },
    saveButtonText: {
        ...typography.bodySemibold,
        color: colors.background,
        fontSize: 16,
    },
});

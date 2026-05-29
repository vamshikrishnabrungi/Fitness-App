import React, { useState, useEffect, useRef } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    Dimensions,
    Animated,
    Alert,
    ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../../src/utils/api';
import { typography, spacing, borderRadius } from '../../src/utils/theme';

const { width } = Dimensions.get('window');

// Pre-sleep moods
const MOODS = [
    { id: 'stress', label: 'Stress', emoji: '😣' },
    { id: 'depressed', label: 'Depressed', emoji: '😔' },
    { id: 'tired', label: 'Tired', emoji: '😵' },
    { id: 'hungry', label: 'Hungry', emoji: '😤' },
    { id: 'relaxed', label: 'Relaxed', emoji: '😊' },
];

// Pre-sleep activities
const ACTIVITIES = [
    { id: 'coffee', label: 'Coffee', emoji: '☕' },
    { id: 'nicotine', label: 'Nicotine', emoji: '🚬' },
    { id: 'alcohol', label: 'Alcohol', emoji: '🍷' },
    { id: 'ate_late', label: 'Ate Late', emoji: '🍽️' },
    { id: 'workout', label: 'Workout', emoji: '💪' },
    { id: 'nap', label: 'Nap', emoji: '😴' },
    { id: 'yoga', label: 'Yoga', emoji: '🧘' },
    { id: 'meditation', label: 'Meditation', emoji: '🧘‍♀️' },
    { id: 'bath', label: 'Bath/Shower', emoji: '🛁' },
    { id: 'milk', label: 'Milk', emoji: '🥛' },
    { id: 'tea', label: 'Tea', emoji: '🍵' },
];

// Alarm sounds
const SOUNDS = [
    { id: 'beat_insomnia', name: 'Beat Insomnia', duration: '60 MIN' },
    { id: 'forest_dreams', name: 'Forest Dreams', duration: '30 MIN' },
    { id: 'ocean_waves', name: 'Ocean Waves', duration: '45 MIN' },
    { id: 'rain', name: 'Rainfall', duration: '∞' },
];

type ScreenState = 'setup' | 'notes' | 'starting' | 'tracking';

interface SleepStats {
    avg_score: number;
    avg_duration: number;
    avg_deep_sleep: number;
    avg_rem_sleep: number;
    total_sessions: number;
    sleep_debt?: {
        total_debt_hours?: number;
    };
}

interface SleepSession {
    id: string;
    created_at?: string;
    start_time?: string;
    end_time?: string;
    duration_hours?: number;
    alarm_time?: string;
    pre_sleep_mood?: string | null;
    pre_sleep_activities?: string[];
    deep_sleep_hours?: number;
    rem_sleep_hours?: number;
}

export default function SleepScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();

    // Screen state
    const [screenState, setScreenState] = useState<ScreenState>('setup');

    // Alarm setup
    const [alarmHour, setAlarmHour] = useState(8);
    const [alarmMinute, setAlarmMinute] = useState(55);
    const [alarmPeriod, setAlarmPeriod] = useState<'AM' | 'PM'>('AM');

    // Pre-sleep notes
    const [selectedMood, setSelectedMood] = useState<string | null>(null);
    const [selectedActivities, setSelectedActivities] = useState<string[]>([]);

    // Tracking
    const [currentTime, setCurrentTime] = useState(new Date());
    const [selectedSound] = useState(SOUNDS[0]);
    const [isPlaying, setIsPlaying] = useState(false);
    const [trackingStartTime, setTrackingStartTime] = useState<Date | null>(null);
    const [sleepStats, setSleepStats] = useState<SleepStats | null>(null);
    const [recentSessions, setRecentSessions] = useState<SleepSession[]>([]);
    const [sleepDataLoading, setSleepDataLoading] = useState(true);

    // Animations
    const waveAnim = useRef(new Animated.Value(0)).current;

    // Update current time every second during tracking
    useEffect(() => {
        if (screenState === 'tracking') {
            const interval = setInterval(() => {
                setCurrentTime(new Date());
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [screenState]);

    // Wave animation
    useEffect(() => {
        Animated.loop(
            Animated.sequence([
                Animated.timing(waveAnim, {
                    toValue: 1,
                    duration: 3000,
                    useNativeDriver: true,
                }),
                Animated.timing(waveAnim, {
                    toValue: 0,
                    duration: 3000,
                    useNativeDriver: true,
                }),
            ])
        ).start();
    }, [waveAnim]);

    useEffect(() => {
        const loadSleepData = async () => {
            try {
                setSleepDataLoading(true);
                const [statsRes, sessionsRes] = await Promise.all([
                    api.get<SleepStats>('/sleep/stats').catch(() => null),
                    api.get<SleepSession[]>('/sleep/sessions').catch(() => []),
                ]);
                setSleepStats(statsRes || null);
                setRecentSessions(sessionsRes || []);
            } catch (error) {
                console.error('Failed to load sleep data:', error);
            } finally {
                setSleepDataLoading(false);
            }
        };

        loadSleepData();
    }, []);

    // Format time for display
    const formatTime = (date: Date) => {
        const hours = date.getHours();
        const minutes = date.getMinutes();
        const period = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        return {
            time: `${displayHours}:${minutes.toString().padStart(2, '0')}`,
            period
        };
    };

    // Get alarm time string
    const getAlarmTimeString = () => {
        const displayHour = alarmHour === 0 ? 12 : alarmHour > 12 ? alarmHour - 12 : alarmHour;
        return `${displayHour}:${alarmMinute.toString().padStart(2, '0')} ${alarmPeriod}`;
    };

    const formatSessionDuration = (session: SleepSession) => {
        if (session.duration_hours != null) {
            return `${session.duration_hours.toFixed(1)}h`;
        }

        const start = session.start_time ? new Date(session.start_time) : null;
        const end = session.end_time ? new Date(session.end_time) : null;
        if (start && end && end > start) {
            return `${((end.getTime() - start.getTime()) / (1000 * 60 * 60)).toFixed(1)}h`;
        }

        return '—';
    };

    const formatSessionDate = (session: SleepSession) => {
        const source = session.start_time || session.created_at;
        if (!source) return 'Recent';
        return new Date(source).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    // Handle start sleep tracking
    const handleStartTracking = () => {
        setScreenState('notes');
    };

    // Handle notes done
    const handleNotesDone = async () => {
        // Save pre-sleep note
        try {
            await api.post('/sleep/notes', {
                mood: selectedMood || 'relaxed',
                activities: selectedActivities,
            });
        } catch {
            console.log('Note save skipped');
        }

        setScreenState('starting');

        // Show "Good Night" screen for 3 seconds
        setTimeout(() => {
            setTrackingStartTime(new Date());
            setScreenState('tracking');
        }, 3000);
    };

    // Handle quit tracking
    const handleQuitTracking = async () => {
        Alert.alert(
            'Stop Tracking?',
            'Would you like to save this sleep session?',
            [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Discard', style: 'destructive', onPress: () => router.back() },
                {
                    text: 'Save',
                    onPress: async () => {
                        if (trackingStartTime) {
                            try {
                                await api.post('/sleep/sessions', {
                                    start_time: trackingStartTime.toISOString(),
                                    end_time: new Date().toISOString(),
                                    alarm_time: getAlarmTimeString(),
                                    pre_sleep_mood: selectedMood,
                                    pre_sleep_activities: selectedActivities,
                                });
                                Alert.alert('Sleep Logged!', 'Your sleep session has been saved.');
                            } catch (error) {
                                console.error('Failed to save sleep:', error);
                            }
                        }
                        router.back();
                    }
                },
            ]
        );
    };

    // Toggle activity selection
    const toggleActivity = (id: string) => {
        if (selectedActivities.includes(id)) {
            setSelectedActivities(selectedActivities.filter(a => a !== id));
        } else {
            setSelectedActivities([...selectedActivities, id]);
        }
    };

    // Render time picker wheel
    const renderTimePicker = () => {
        return (
            <View style={styles.timePicker}>
                {/* Hours before selected */}
                <Text style={styles.timePickerFaded}>
                    {alarmHour === 1 ? 12 : alarmHour - 1 < 10 ? `0${alarmHour - 1 || 12}` : alarmHour - 1}
                </Text>

                {/* Selected time */}
                <View style={styles.selectedTimeContainer}>
                    <Text style={styles.selectedTime}>
                        {alarmHour.toString().padStart(2, '0')}
                    </Text>
                    <Text style={styles.selectedTimeColon}>:</Text>
                    <Text style={styles.selectedTime}>
                        {alarmMinute.toString().padStart(2, '0')}
                    </Text>
                    <TouchableOpacity
                        style={styles.periodToggle}
                        onPress={() => setAlarmPeriod(alarmPeriod === 'AM' ? 'PM' : 'AM')}
                    >
                        <Text style={styles.periodText}>{alarmPeriod}</Text>
                    </TouchableOpacity>
                </View>

                {/* Hours after selected */}
                <Text style={styles.timePickerFaded}>
                    {alarmHour === 12 ? '01' : (alarmHour + 1).toString().padStart(2, '0')}   {(alarmMinute + 1) % 60 < 10 ? `0${(alarmMinute + 1) % 60}` : (alarmMinute + 1) % 60}   PM
                </Text>

                {/* Touch controls for hour/minute */}
                <View style={styles.timeControls}>
                    <TouchableOpacity
                        style={styles.timeControl}
                        onPress={() => setAlarmHour(alarmHour === 12 ? 1 : alarmHour + 1)}
                    >
                        <Ionicons name="chevron-up" size={24} color="rgba(255,255,255,0.5)" />
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={styles.timeControl}
                        onPress={() => setAlarmMinute((alarmMinute + 5) % 60)}
                    >
                        <Ionicons name="chevron-up" size={24} color="rgba(255,255,255,0.5)" />
                    </TouchableOpacity>
                </View>
            </View>
        );
    };

    // Render setup screen
    const renderSetupScreen = () => (
        <View style={styles.setupContainer}>
            {/* Back button */}
            <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
                <Ionicons name="chevron-back" size={28} color="#FFFFFF" />
            </TouchableOpacity>

            <View style={styles.summaryContainer}>
                <Text style={styles.summaryTitle}>Sleep Snapshot</Text>
                {sleepDataLoading ? (
                    <ActivityIndicator size="small" color="#FFFFFF" />
                ) : sleepStats ? (
                    <>
                        <View style={styles.summaryGrid}>
                            <View style={styles.summaryCard}>
                                <Text style={styles.summaryValue}>{sleepStats.avg_score}</Text>
                                <Text style={styles.summaryLabel}>Avg score</Text>
                            </View>
                            <View style={styles.summaryCard}>
                                <Text style={styles.summaryValue}>{sleepStats.avg_duration.toFixed(1)}h</Text>
                                <Text style={styles.summaryLabel}>Avg duration</Text>
                            </View>
                            <View style={styles.summaryCard}>
                                <Text style={styles.summaryValue}>{sleepStats.total_sessions}</Text>
                                <Text style={styles.summaryLabel}>Sessions</Text>
                            </View>
                        </View>
                        <Text style={styles.summaryFootnote}>
                            Sleep debt: {(sleepStats.sleep_debt?.total_debt_hours || 0).toFixed(1)}h
                        </Text>
                    </>
                ) : (
                    <Text style={styles.summaryFootnote}>
                        Start logging sleep sessions to build your sleep history.
                    </Text>
                )}
            </View>

            {/* Time Picker */}
            {renderTimePicker()}

            {/* Wake up text */}
            <Text style={styles.wakeUpText}>
                Wake you up at {getAlarmTimeString()}
            </Text>
            <Text style={styles.wakeUpSubtext}>after starting the tracker</Text>

            {/* Pagination dots */}
            <View style={styles.paginationDots}>
                <View style={[styles.dot, styles.dotInactive]} />
                <View style={[styles.dot, styles.dotActive]} />
            </View>

            {/* Wave animation at bottom */}
            <View style={styles.waveContainer}>
                <Animated.View
                    style={[
                        styles.wave,
                        {
                            transform: [{
                                translateY: waveAnim.interpolate({
                                    inputRange: [0, 1],
                                    outputRange: [0, -10]
                                })
                            }]
                        }
                    ]}
                />
            </View>

            {/* Start button */}
            <TouchableOpacity
                style={styles.startButton}
                onPress={handleStartTracking}
            >
                <Ionicons name="moon" size={24} color="#FFFFFF" />
                <Text style={styles.startButtonText}>Start Sleep Tracker</Text>
            </TouchableOpacity>

            {/* Cancel */}
            <TouchableOpacity onPress={() => router.back()}>
                <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>

            {recentSessions.length > 0 && (
                <View style={styles.recentSessionsContainer}>
                    <Text style={styles.recentSessionsTitle}>Recent Sessions</Text>
                    {recentSessions.slice(0, 3).map((session) => (
                        <View key={session.id} style={styles.recentSessionCard}>
                            <View>
                                <Text style={styles.recentSessionDate}>{formatSessionDate(session)}</Text>
                                <Text style={styles.recentSessionMeta}>
                                    {session.pre_sleep_mood || 'No mood'} • {session.alarm_time || 'No alarm'}
                                </Text>
                            </View>
                            <Text style={styles.recentSessionDuration}>{formatSessionDuration(session)}</Text>
                        </View>
                    ))}
                </View>
            )}
        </View>
    );

    // Render notes screen
    const renderNotesScreen = () => (
        <ScrollView
            style={styles.notesContainer}
            contentContainerStyle={styles.notesContent}
        >
            <Text style={styles.notesTitle}>Add Sleep Note</Text>

            {/* Mood section */}
            <Text style={styles.sectionLabel}>How do you feel now?</Text>
            <View style={styles.moodsGrid}>
                {MOODS.map((mood) => (
                    <TouchableOpacity
                        key={mood.id}
                        style={[
                            styles.moodItem,
                            selectedMood === mood.id && styles.moodItemSelected
                        ]}
                        onPress={() => setSelectedMood(mood.id)}
                    >
                        <View style={[
                            styles.moodIcon,
                            selectedMood === mood.id && styles.moodIconSelected
                        ]}>
                            <Text style={styles.moodEmoji}>{mood.emoji}</Text>
                        </View>
                        <Text style={styles.moodLabel}>{mood.label}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Activities section */}
            <Text style={styles.sectionLabel}>Pre-sleep Activities</Text>
            <View style={styles.activitiesGrid}>
                {ACTIVITIES.map((activity) => (
                    <TouchableOpacity
                        key={activity.id}
                        style={[
                            styles.activityItem,
                            selectedActivities.includes(activity.id) && styles.activityItemSelected
                        ]}
                        onPress={() => toggleActivity(activity.id)}
                    >
                        <View style={[
                            styles.activityIcon,
                            selectedActivities.includes(activity.id) && styles.activityIconSelected
                        ]}>
                            <Text style={styles.activityEmoji}>{activity.emoji}</Text>
                        </View>
                        <Text style={[
                            styles.activityLabel,
                            selectedActivities.includes(activity.id) && styles.activityLabelSelected
                        ]}>
                            {activity.label}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Done button */}
            <TouchableOpacity
                style={styles.doneButton}
                onPress={handleNotesDone}
            >
                <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
        </ScrollView>
    );

    // Render starting screen (Good Night)
    const renderStartingScreen = () => (
        <View style={styles.startingContainer}>
            {/* Moon */}
            <View style={styles.moonContainer}>
                <Text style={styles.moonEmoji}>🌕</Text>
            </View>

            {/* Text */}
            <Text style={styles.goodNightText}>Good Night</Text>
            <Text style={styles.startingText}>Starting Sleep Tracker...</Text>
            <Text style={styles.chargerText}>Keep the charger connected.</Text>
        </View>
    );

    // Render tracking screen
    const renderTrackingScreen = () => {
        const { time, period } = formatTime(currentTime);

        return (
            <View style={styles.trackingContainer}>
                {/* Header */}
                <View style={styles.trackingHeader}>
                    <View>
                        <Text style={styles.trackingLabel}>Tracking...</Text>
                        <Text style={styles.ambientNoise}>Ambient Noise: <Text style={styles.noiseValue}>0dB</Text></Text>
                    </View>
                    <Text style={styles.moonEmojiSmall}>🌕</Text>
                </View>

                {/* Current Time */}
                <View style={styles.currentTimeContainer}>
                    <Text style={styles.currentTime}>{time}</Text>
                    <Text style={styles.currentPeriod}>{period}</Text>
                </View>

                {/* Alarm time */}
                <Text style={styles.alarmInfo}>
                    Alarm <Text style={styles.alarmTimeHighlight}>{getAlarmTimeString()}</Text>
                </Text>

                {/* Sound player */}
                <View style={styles.soundPlayer}>
                    <TouchableOpacity
                        style={styles.playButton}
                        onPress={() => setIsPlaying(!isPlaying)}
                    >
                        <Ionicons
                            name={isPlaying ? "pause" : "play"}
                            size={24}
                            color="#FFFFFF"
                        />
                    </TouchableOpacity>
                    <View style={styles.soundInfo}>
                        <Text style={styles.soundName}>{selectedSound.name}</Text>
                        <Text style={styles.soundDuration}>{selectedSound.duration}</Text>
                    </View>
                    <TouchableOpacity>
                        <Ionicons name="heart-outline" size={24} color="rgba(255,255,255,0.6)" />
                    </TouchableOpacity>
                    <TouchableOpacity style={{ marginLeft: 16 }}>
                        <Ionicons name="list" size={24} color="rgba(255,255,255,0.6)" />
                    </TouchableOpacity>
                </View>

                {/* Quit button */}
                <TouchableOpacity
                    style={styles.quitButton}
                    onPress={handleQuitTracking}
                >
                    <Text style={styles.quitButtonText}>Quit</Text>
                </TouchableOpacity>
            </View>
        );
    };

    return (
        <LinearGradient
            colors={['#0B1A3D', '#132954', '#1A3568']}
            style={[styles.container, { paddingTop: insets.top }]}
        >
            {screenState === 'setup' && renderSetupScreen()}
            {screenState === 'notes' && renderNotesScreen()}
            {screenState === 'starting' && renderStartingScreen()}
            {screenState === 'tracking' && renderTrackingScreen()}
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    summaryContainer: {
        width: '100%',
        marginTop: spacing.xl,
        marginBottom: spacing.lg,
        padding: spacing.md,
        borderRadius: borderRadius.lg,
        backgroundColor: 'rgba(255, 255, 255, 0.08)',
    },
    summaryTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#FFFFFF',
        marginBottom: spacing.sm,
    },
    summaryGrid: {
        flexDirection: 'row',
        gap: spacing.sm,
    },
    summaryCard: {
        flex: 1,
        alignItems: 'center',
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.md,
        backgroundColor: 'rgba(255, 255, 255, 0.08)',
    },
    summaryValue: {
        fontSize: 22,
        fontWeight: '700',
        color: '#FFFFFF',
    },
    summaryLabel: {
        ...typography.caption,
        color: 'rgba(255, 255, 255, 0.75)',
    },
    summaryFootnote: {
        ...typography.caption,
        color: 'rgba(255, 255, 255, 0.75)',
        marginTop: spacing.sm,
    },
    recentSessionsContainer: {
        width: '100%',
        marginTop: spacing.lg,
    },
    recentSessionsTitle: {
        ...typography.bodySemibold,
        color: '#FFFFFF',
        marginBottom: spacing.sm,
    },
    recentSessionCard: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: spacing.sm,
        borderTopWidth: StyleSheet.hairlineWidth,
        borderTopColor: 'rgba(255, 255, 255, 0.15)',
    },
    recentSessionDate: {
        ...typography.bodySemibold,
        color: '#FFFFFF',
    },
    recentSessionMeta: {
        ...typography.caption,
        color: 'rgba(255, 255, 255, 0.7)',
        marginTop: 2,
    },
    recentSessionDuration: {
        ...typography.bodySemibold,
        color: '#FFFFFF',
    },
    // Setup Screen
    setupContainer: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: spacing.xl,
    },
    backButton: {
        position: 'absolute',
        top: spacing.md,
        left: spacing.md,
        padding: spacing.sm,
    },
    timePicker: {
        alignItems: 'center',
        marginBottom: spacing.xl,
    },
    timePickerFaded: {
        fontSize: 36,
        color: 'rgba(255, 255, 255, 0.3)',
        fontWeight: '300',
    },
    selectedTimeContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        paddingHorizontal: spacing.xl,
        paddingVertical: spacing.md,
        borderRadius: borderRadius.xl,
        marginVertical: spacing.md,
    },
    selectedTime: {
        fontSize: 56,
        color: '#FFFFFF',
        fontWeight: '600',
    },
    selectedTimeColon: {
        fontSize: 56,
        color: '#FFFFFF',
        fontWeight: '300',
        marginHorizontal: 4,
    },
    periodToggle: {
        marginLeft: spacing.md,
    },
    periodText: {
        fontSize: 24,
        color: '#FFFFFF',
        fontWeight: '400',
    },
    timeControls: {
        flexDirection: 'row',
        gap: 100,
        marginTop: spacing.sm,
    },
    timeControl: {
        padding: spacing.sm,
    },
    wakeUpText: {
        fontSize: 16,
        color: '#FFFFFF',
        textAlign: 'center',
        marginTop: spacing.xl,
    },
    wakeUpSubtext: {
        fontSize: 14,
        color: 'rgba(255, 255, 255, 0.6)',
        textAlign: 'center',
        marginTop: 4,
    },
    paginationDots: {
        flexDirection: 'row',
        marginTop: spacing.xl,
        gap: 8,
    },
    dot: {
        width: 8,
        height: 8,
        borderRadius: 4,
    },
    dotActive: {
        backgroundColor: '#FFFFFF',
    },
    dotInactive: {
        backgroundColor: 'rgba(255, 255, 255, 0.3)',
    },
    waveContainer: {
        position: 'absolute',
        bottom: 180,
        left: 0,
        right: 0,
        height: 60,
        overflow: 'hidden',
    },
    wave: {
        width: width * 2,
        height: 60,
        backgroundColor: 'transparent',
        borderTopWidth: 2,
        borderTopColor: 'rgba(0, 150, 255, 0.3)',
        borderRadius: 100,
    },
    startButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#007AFF',
        paddingHorizontal: 40,
        paddingVertical: 16,
        borderRadius: 30,
        marginTop: 60,
        gap: 12,
    },
    startButtonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '600',
    },
    cancelText: {
        color: 'rgba(255, 255, 255, 0.6)',
        fontSize: 16,
        marginTop: spacing.lg,
    },
    // Notes Screen
    notesContainer: {
        flex: 1,
    },
    notesContent: {
        padding: spacing.xl,
        paddingBottom: 100,
    },
    notesTitle: {
        fontSize: 24,
        fontWeight: '700',
        color: '#FFFFFF',
        textAlign: 'center',
        marginBottom: spacing.xl,
    },
    sectionLabel: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFFFFF',
        marginBottom: spacing.md,
        marginTop: spacing.lg,
    },
    moodsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    moodItem: {
        alignItems: 'center',
        marginRight: spacing.md,
        marginBottom: spacing.md,
    },
    moodItemSelected: {},
    moodIcon: {
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 6,
    },
    moodIconSelected: {
        backgroundColor: '#007AFF',
    },
    moodEmoji: {
        fontSize: 28,
    },
    moodLabel: {
        fontSize: 12,
        color: 'rgba(255, 255, 255, 0.7)',
    },
    activitiesGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    activityItem: {
        alignItems: 'center',
        width: (width - 80) / 4,
        marginBottom: spacing.md,
    },
    activityItemSelected: {},
    activityIcon: {
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 6,
    },
    activityIconSelected: {
        backgroundColor: '#007AFF',
    },
    activityEmoji: {
        fontSize: 24,
    },
    activityLabel: {
        fontSize: 11,
        color: 'rgba(255, 255, 255, 0.7)',
        textAlign: 'center',
    },
    activityLabelSelected: {
        color: '#FFFFFF',
    },
    doneButton: {
        backgroundColor: '#007AFF',
        paddingVertical: 16,
        borderRadius: 30,
        alignItems: 'center',
        marginTop: spacing.xl,
    },
    doneButtonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '600',
    },
    // Starting Screen (Good Night)
    startingContainer: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
    },
    moonContainer: {
        marginBottom: spacing.xl,
    },
    moonEmoji: {
        fontSize: 100,
    },
    goodNightText: {
        fontSize: 32,
        fontWeight: '700',
        color: '#FFFFFF',
        marginBottom: spacing.md,
    },
    startingText: {
        fontSize: 16,
        color: 'rgba(255, 255, 255, 0.8)',
    },
    chargerText: {
        fontSize: 14,
        color: 'rgba(255, 255, 255, 0.6)',
        marginTop: 8,
    },
    // Tracking Screen
    trackingContainer: {
        flex: 1,
        padding: spacing.xl,
    },
    trackingHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
    },
    trackingLabel: {
        fontSize: 16,
        color: 'rgba(255, 255, 255, 0.8)',
    },
    ambientNoise: {
        fontSize: 14,
        color: 'rgba(255, 255, 255, 0.5)',
        marginTop: 4,
    },
    noiseValue: {
        color: '#00C853',
    },
    moonEmojiSmall: {
        fontSize: 60,
    },
    currentTimeContainer: {
        alignItems: 'center',
        marginTop: 60,
    },
    currentTime: {
        fontSize: 80,
        fontWeight: '200',
        color: '#FFFFFF',
    },
    currentPeriod: {
        fontSize: 24,
        color: 'rgba(255, 255, 255, 0.6)',
        marginTop: -10,
    },
    alarmInfo: {
        fontSize: 16,
        color: 'rgba(255, 255, 255, 0.6)',
        textAlign: 'center',
        marginTop: spacing.md,
    },
    alarmTimeHighlight: {
        color: '#007AFF',
        textDecorationLine: 'underline',
    },
    soundPlayer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        padding: spacing.md,
        borderRadius: borderRadius.lg,
        marginTop: 60,
    },
    playButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        alignItems: 'center',
        justifyContent: 'center',
    },
    soundInfo: {
        flex: 1,
        marginLeft: spacing.md,
    },
    soundName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    soundDuration: {
        fontSize: 12,
        color: 'rgba(255, 255, 255, 0.5)',
        marginTop: 2,
    },
    quitButton: {
        position: 'absolute',
        bottom: 100,
        alignSelf: 'center',
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        alignItems: 'center',
        justifyContent: 'center',
    },
    quitButtonText: {
        fontSize: 16,
        color: 'rgba(255, 255, 255, 0.8)',
    },
});

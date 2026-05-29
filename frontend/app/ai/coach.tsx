import React, { useState, useRef, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    TextInput,
    ActivityIndicator,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

interface Message {
    id: string;
    role: 'user' | 'coach';
    content: string;
    timestamp: Date;
}


const QUICK_PROMPTS = [
    { icon: '🏃', text: 'How should I structure my training week?' },
    { icon: '😰', text: 'I feel anxious before races' },
    { icon: '💪', text: 'How can I build mental toughness?' },
    { icon: '🩹', text: 'How to stay motivated during injury?' },
    { icon: '😴', text: 'Tips for better recovery sleep' },
    { icon: '🎯', text: 'Setting realistic goals' },
];

export default function AICoachScreen() {
    const insets = useSafeAreaInsets();
    const router = useRouter();
    const scrollRef = useRef<ScrollView>(null);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'coach',
            content: "👋 Hey! I'm your AI performance coach. I'm here to help with training, mental performance, injury recovery, and motivation. What's on your mind?",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const [sending, setSending] = useState(false);

    const buildFallbackReply = (_text: string) => {
        return 'I could not reach the chat service. Please try again shortly.';
    };

    const sendMessage = async (text: string) => {
        if (!text.trim() || sending) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: text.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setSending(true);

        // Scroll to bottom
        setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);

        try {
            const response = await api.post<{ response: string }>('/ai/coach/chat', {
                message: text.trim(),
            }).catch(() => null);

            const coachMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'coach',
                content: response?.response || buildFallbackReply(text.trim()),
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, coachMessage]);
        } catch (error) {
            console.error('Coach chat error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'coach',
                content: buildFallbackReply(text.trim()),
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setSending(false);
            setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
        }
    };

    return (
        <KeyboardAvoidingView
            style={[styles.container, { paddingTop: insets.top }]}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={0}
        >
            {/* Header */}
            <LinearGradient
                colors={[colors.accentGreen, colors.accentTeal]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.header}
            >
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.background} />
                </TouchableOpacity>
                <View style={styles.headerCenter}>
                    <View style={styles.coachAvatar}>
                        <Ionicons name="fitness" size={20} color={colors.accentGreen} />
                    </View>
                    <View>
                        <Text style={styles.headerTitle}>AI Coach</Text>
                        <Text style={styles.headerSubtitle}>Always here to help</Text>
                    </View>
                </View>
                <View style={{ width: 40 }} />
            </LinearGradient>

            {/* Messages */}
            <ScrollView
                ref={scrollRef}
                style={styles.messagesContainer}
                contentContainerStyle={styles.messagesContent}
                showsVerticalScrollIndicator={false}
            >
                {messages.map((message) => (
                    <View
                        key={message.id}
                        style={[
                            styles.messageBubble,
                            message.role === 'user' ? styles.userBubble : styles.coachBubble,
                        ]}
                    >
                        {message.role === 'coach' && (
                            <View style={styles.coachIcon}>
                                <Ionicons name="fitness" size={14} color={colors.accentGreen} />
                            </View>
                        )}
                        <Text
                            style={[
                                styles.messageText,
                                message.role === 'user' ? styles.userText : styles.coachText,
                            ]}
                        >
                            {message.content}
                        </Text>
                    </View>
                ))}

                {sending && (
                    <View style={[styles.messageBubble, styles.coachBubble]}>
                        <View style={styles.coachIcon}>
                            <Ionicons name="fitness" size={14} color={colors.accentGreen} />
                        </View>
                        <ActivityIndicator size="small" color={colors.accentGreen} />
                    </View>
                )}

                {/* Quick Prompts - only show at start */}
                {messages.length === 1 && (
                    <View style={styles.quickPrompts}>
                        <Text style={styles.quickPromptsTitle}>Quick topics</Text>
                        <View style={styles.promptsGrid}>
                            {QUICK_PROMPTS.map((prompt, index) => (
                                <TouchableOpacity
                                    key={index}
                                    style={styles.promptChip}
                                    onPress={() => sendMessage(prompt.text)}
                                >
                                    <Text style={styles.promptIcon}>{prompt.icon}</Text>
                                    <Text style={styles.promptText} numberOfLines={2}>{prompt.text}</Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                    </View>
                )}

                <View style={{ height: 20 }} />
            </ScrollView>

            {/* Input */}
            <View style={[styles.inputContainer, { paddingBottom: insets.bottom + 8 }]}>
                <TextInput
                    style={styles.textInput}
                    placeholder="Ask your coach..."
                    placeholderTextColor={colors.textTertiary}
                    value={input}
                    onChangeText={setInput}
                    onSubmitEditing={() => sendMessage(input)}
                    multiline
                    maxLength={500}
                />
                <TouchableOpacity
                    style={[styles.sendButton, (!input.trim() || sending) && styles.sendButtonDisabled]}
                    onPress={() => sendMessage(input)}
                    disabled={!input.trim() || sending}
                >
                    <Ionicons name="send" size={20} color={colors.background} />
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
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
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.md,
    },
    backButton: {
        padding: spacing.xs,
    },
    headerCenter: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        marginLeft: spacing.sm,
        gap: spacing.sm,
    },
    coachAvatar: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: colors.background,
        alignItems: 'center',
        justifyContent: 'center',
    },
    headerTitle: {
        ...typography.bodySemibold,
        color: colors.background,
    },
    headerSubtitle: {
        ...typography.caption,
        color: 'rgba(255,255,255,0.8)',
    },
    contextCard: {
        margin: spacing.md,
        marginTop: 0,
        padding: spacing.md,
        borderRadius: borderRadius.lg,
        backgroundColor: colors.surface,
        borderWidth: 1,
        borderColor: colors.border,
        gap: spacing.sm,
    },
    contextHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
    },
    contextTitle: {
        ...typography.bodySemibold,
        color: colors.textPrimary,
    },
    contextSummary: {
        ...typography.body,
        color: colors.textPrimary,
        lineHeight: 22,
    },
    contextRecommendation: {
        ...typography.caption,
        color: colors.textSecondary,
    },
    messagesContainer: {
        flex: 1,
    },
    messagesContent: {
        padding: spacing.md,
    },
    messageBubble: {
        maxWidth: '85%',
        padding: spacing.md,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.sm,
    },
    userBubble: {
        alignSelf: 'flex-end',
        backgroundColor: colors.accentGreen,
        borderBottomRightRadius: 4,
    },
    coachBubble: {
        alignSelf: 'flex-start',
        backgroundColor: colors.surface,
        borderBottomLeftRadius: 4,
        borderWidth: 1,
        borderColor: colors.border,
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: spacing.sm,
    },
    coachIcon: {
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: colors.accentGreenLight,
        alignItems: 'center',
        justifyContent: 'center',
    },
    messageText: {
        ...typography.body,
        lineHeight: 22,
        flex: 1,
    },
    userText: {
        color: colors.background,
    },
    coachText: {
        color: colors.textPrimary,
    },
    quickPrompts: {
        marginTop: spacing.lg,
    },
    quickPromptsTitle: {
        ...typography.caption,
        color: colors.textSecondary,
        marginBottom: spacing.sm,
    },
    promptsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    promptChip: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.xs,
        backgroundColor: colors.surface,
        paddingHorizontal: spacing.sm,
        paddingVertical: spacing.sm,
        borderRadius: borderRadius.lg,
        borderWidth: 1,
        borderColor: colors.border,
        maxWidth: '48%',
    },
    promptIcon: {
        fontSize: 16,
    },
    promptText: {
        ...typography.caption,
        color: colors.textPrimary,
        flex: 1,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        padding: spacing.md,
        paddingTop: spacing.sm,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        backgroundColor: colors.background,
        gap: spacing.sm,
    },
    textInput: {
        flex: 1,
        backgroundColor: colors.surface,
        borderRadius: borderRadius.lg,
        borderWidth: 1,
        borderColor: colors.border,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        color: colors.textPrimary,
        ...typography.body,
        maxHeight: 100,
    },
    sendButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: colors.accentGreen,
        alignItems: 'center',
        justifyContent: 'center',
    },
    sendButtonDisabled: {
        opacity: 0.5,
    },
});

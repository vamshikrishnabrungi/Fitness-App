/* eslint-disable react/no-unescaped-entities */
import React from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    Modal,
    Pressable,
} from 'react-native';

interface LogoutModalProps {
    visible: boolean;
    onCancel: () => void;
    onLogout: () => void;
}

export function LogoutModal({ visible, onCancel, onLogout }: LogoutModalProps) {
    return (
        <Modal
            visible={visible}
            transparent
            animationType="fade"
            statusBarTranslucent
        >
            <Pressable style={styles.overlay} onPress={onCancel}>
                <Pressable style={styles.card} onPress={(e) => e.stopPropagation()}>
                    <Text style={styles.title}>Are you sure?</Text>
                    <Text style={styles.description}>
                        You'll need to login again to keep using the application
                    </Text>

                    <View style={styles.buttonRow}>
                        <TouchableOpacity
                            style={styles.cancelButton}
                            onPress={onCancel}
                            activeOpacity={0.7}
                        >
                            <Text style={styles.cancelButtonText}>Cancel</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={styles.logoutButton}
                            onPress={onLogout}
                            activeOpacity={0.7}
                        >
                            <Text style={styles.logoutButtonText}>Log Out</Text>
                        </TouchableOpacity>
                    </View>
                </Pressable>
            </Pressable>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.3)',
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 40,
    },
    card: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        paddingTop: 28,
        paddingHorizontal: 24,
        paddingBottom: 20,
        width: '100%',
        maxWidth: 340,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.15,
        shadowRadius: 20,
        elevation: 10,
    },
    title: {
        fontSize: 20,
        fontWeight: '600',
        color: '#000000',
        marginBottom: 12,
        letterSpacing: -0.3,
    },
    description: {
        fontSize: 15,
        color: '#666666',
        lineHeight: 22,
        marginBottom: 24,
        letterSpacing: -0.2,
    },
    buttonRow: {
        flexDirection: 'row',
        gap: 12,
    },
    cancelButton: {
        flex: 1,
        height: 44,
        borderRadius: 22,
        borderWidth: 1.5,
        borderColor: '#E0E0E0',
        backgroundColor: '#FFFFFF',
        alignItems: 'center',
        justifyContent: 'center',
    },
    cancelButtonText: {
        fontSize: 15,
        fontWeight: '500',
        color: '#000000',
        letterSpacing: -0.2,
    },
    logoutButton: {
        flex: 1,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#000000',
        alignItems: 'center',
        justifyContent: 'center',
    },
    logoutButtonText: {
        fontSize: 15,
        fontWeight: '500',
        color: '#FFFFFF',
        letterSpacing: -0.2,
    },
});

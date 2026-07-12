import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width, height } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  return (
    <View style={styles.container}>
      {/* Dark purple/black gradient background like Nike */}
      <LinearGradient
        colors={['#2D1B4E', '#1a1a2e', '#0f0f1a']}
        style={styles.background}
      >
        {/* Subtle overlay shapes */}
        <View style={styles.shapeContainer}>
          <View style={styles.shape1} />
          <View style={styles.shape2} />
        </View>

        {/* Logo at top left */}
        <View style={[styles.logoContainer, { top: insets.top + 20 }]}>
          <Text style={styles.logo}>Runlete</Text>
        </View>

        {/* Bottom content */}
        <View style={[styles.content, { paddingBottom: insets.bottom + 32 }]}>
          {/* Title */}
          <Text style={styles.title}>Runlete</Text>
          <Text style={styles.subtitle}>
            Strength starts here. Train{'\n'}with us.
          </Text>

          {/* Side by side buttons */}
          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={styles.joinButton}
              onPress={() => router.push('/(auth)/register')}
              activeOpacity={0.8}
            >
              <Text style={styles.joinButtonText}>Join Us</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.signInButton}
              onPress={() => router.push('/(auth)/login')}
              activeOpacity={0.8}
            >
              <Text style={styles.signInButtonText}>Sign In</Text>
            </TouchableOpacity>
          </View>
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  background: {
    flex: 1,
  },
  shapeContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  shape1: {
    position: 'absolute',
    top: height * 0.3,
    left: -50,
    width: width * 0.7,
    height: height * 0.4,
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 200,
    transform: [{ rotate: '-15deg' }],
  },
  shape2: {
    position: 'absolute',
    top: height * 0.4,
    right: -30,
    width: width * 0.5,
    height: height * 0.3,
    backgroundColor: 'rgba(255,255,255,0.015)',
    borderRadius: 150,
    transform: [{ rotate: '10deg' }],
  },
  logoContainer: {
    position: 'absolute',
    left: 24,
  },
  logo: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 17,
    color: 'rgba(255,255,255,0.6)',
    lineHeight: 24,
    marginBottom: 32,
    letterSpacing: -0.2,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  joinButton: {
    flex: 1,
    height: 52,
    backgroundColor: '#FFFFFF',
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  joinButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    letterSpacing: -0.3,
  },
  signInButton: {
    flex: 1,
    height: 52,
    backgroundColor: 'transparent',
    borderRadius: 26,
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  signInButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: -0.3,
  },
});

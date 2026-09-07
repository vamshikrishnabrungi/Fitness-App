import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Modal,
  FlatList,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../src/store/authStore';
import { api, apiErrorMessage } from '../../src/utils/api';
import { countries } from '../../src/data/countries';

type Step = 'email' | 'code';

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loginWithOtp } = useAuthStore();

  const [step, setStep] = useState<Step>('email');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form fields
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [challengeId, setChallengeId] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('India');
  const [countryModalVisible, setCountryModalVisible] = useState(false);
  const [countryQuery, setCountryQuery] = useState('');

  // Resend timer
  const [resendTimer, setResendTimer] = useState(30);

  useEffect(() => {
    if (step === 'code' && resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [step, resendTimer]);

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleContinue = () => {
    const run = async () => {
      if (!validateEmail(email)) {
        setError('Please enter a valid email address');
        return;
      }
      setError('');
      setLoading(true);
      try {
        const normalizedEmail = email.trim().toLowerCase();
        const result = await api.post<{ challenge_id: string }>('/auth/otp/request', { email: normalizedEmail, purpose: 'login' });
        setEmail(normalizedEmail);
        setChallengeId(result.challenge_id);
        setStep('code');
        setResendTimer(30);
      } catch (err: unknown) {
        setError(apiErrorMessage(err, 'Failed to send code'));
      } finally {
        setLoading(false);
      }
    };
    run();
  };

  const handleSignIn = async () => {
    if (!/^\d{6}$/.test(code)) {
      setError('Please enter the 6-digit code');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await loginWithOtp(challengeId, email, code);
      router.replace('/(tabs)');
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Invalid code'));
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (resendTimer > 0 || loading) return;
    setLoading(true);
    setError('');
    try {
      const result = await api.post<{ challenge_id: string }>('/auth/otp/request', { email, purpose: 'login' });
      setChallengeId(result.challenge_id);
      setResendTimer(30);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Failed to resend code'));
    } finally {
      setLoading(false);
    }
  };

  const truncateEmail = (email: string) => {
    if (email.length > 25) {
      return email.substring(0, 22) + '...';
    }
    return email;
  };

  const filteredCountries = countries.filter((country) =>
    country.toLowerCase().includes(countryQuery.trim().toLowerCase())
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          accessibilityLabel={step === 'email' ? 'Close sign in' : 'Back to email'}
          onPress={() => step === 'email' ? router.back() : setStep('email')}
          style={styles.closeButton}
        >
          <Ionicons name="close" size={28} color="#000000" />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={styles.content}
          contentContainerStyle={[styles.contentContainer, { paddingBottom: insets.bottom + 40 }]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Logo */}
          <Text style={styles.logo}>Runlete</Text>

          {step === 'email' ? (
            <>
              {/* Email Step */}
              <Text style={styles.title}>Enter your email to join us or sign in.</Text>

              <Text style={styles.countryRow}>
                <Text style={styles.countryText}>{selectedCountry}</Text>
                {'  '}
                <Text style={styles.changeLink} onPress={() => setCountryModalVisible(true)}>
                  Change
                </Text>
              </Text>

              {/* Email Input */}
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Email*"
                  placeholderTextColor="#999999"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoComplete="email"
                  accessibilityLabel="Email address"
                  returnKeyType="go"
                  onSubmitEditing={handleContinue}
                />
              </View>

              {error ? <Text style={styles.errorText}>{error}</Text> : null}

              {/* Terms */}
              <Text style={styles.termsText}>
                By continuing, I agree to Runlete&apos;s{' '}
                <Text style={styles.link} onPress={() => router.push('/privacy-policy')}>
                  Privacy Policy
                </Text>{' '}
                and{' '}
                <Text style={styles.link} onPress={() => router.push('/terms-of-use')}>
                  Terms of Use
                </Text>.
              </Text>

              {/* Continue Button */}
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityState={{ disabled: !email || loading, busy: loading }}
                style={[styles.continueButton, (!email || loading) && styles.buttonDisabled]}
                onPress={handleContinue}
                disabled={!email || loading}
              >
                {loading ? <ActivityIndicator color="#FFFFFF" size="small" /> : <Text style={styles.buttonText}>Continue</Text>}
              </TouchableOpacity>
            </>
          ) : (
            <>
              {/* Code/Password Step */}
              <Text style={styles.title}>
                Enter the 6-digit code sent to your email.
              </Text>

              <Text style={styles.emailRow}>
                <Text style={styles.emailDisplay}>{truncateEmail(email)}</Text>
                {'  '}
                <Text style={styles.editLink} onPress={() => setStep('email')}>Edit</Text>
              </Text>

              <>
                  {/* OTP Input */}
                  <View style={styles.inputContainer}>
                    <TextInput
                      style={styles.input}
                      placeholder="6-digit code*"
                      placeholderTextColor="#999999"
                      value={code}
                      onChangeText={setCode}
                      keyboardType="number-pad"
                      maxLength={6}
                      accessibilityLabel="Six digit sign-in code"
                      textContentType="oneTimeCode"
                      autoComplete="one-time-code"
                    />
                    <TouchableOpacity accessibilityLabel="Resend code" style={styles.inputIcon} onPress={() => void handleResendCode()} disabled={resendTimer > 0 || loading}>
                      <Ionicons name="refresh-outline" size={20} color="#999999" />
                    </TouchableOpacity>
                  </View>

                  <TouchableOpacity accessibilityRole="button" onPress={() => void handleResendCode()} disabled={resendTimer > 0 || loading}>
                    <Text style={styles.resendText}>
                      {resendTimer > 0 ? `Resend code in ${resendTimer}s` : 'Resend code'}
                    </Text>
                  </TouchableOpacity>
              </>

              {error ? <Text style={styles.errorText}>{error}</Text> : null}

              {/* Sign In Button */}
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityState={{ disabled: loading, busy: loading }}
                style={[styles.signInButton, loading && styles.buttonLoading]}
                onPress={handleSignIn}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.buttonText}>Sign In</Text>
                )}
              </TouchableOpacity>

            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

      <Modal
        visible={countryModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setCountryModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Country</Text>
              <TouchableOpacity onPress={() => setCountryModalVisible(false)}>
                <Ionicons name="close" size={22} color="#000000" />
              </TouchableOpacity>
            </View>
            <View style={styles.searchContainer}>
              <Ionicons name="search-outline" size={18} color="#666666" />
              <TextInput
                style={styles.searchInput}
                placeholder="Search countries"
                placeholderTextColor="#999999"
                value={countryQuery}
                onChangeText={setCountryQuery}
              />
            </View>
            <FlatList
              data={filteredCountries}
              keyExtractor={(item) => item}
              keyboardShouldPersistTaps="handled"
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.countryItem}
                  onPress={() => {
                    setSelectedCountry(item);
                    setCountryModalVisible(false);
                    setCountryQuery('');
                  }}
                >
                  <Text style={styles.countryItemText}>{item}</Text>
                  {item === selectedCountry ? (
                    <Ionicons name="checkmark" size={18} color="#000000" />
                  ) : null}
                </TouchableOpacity>
              )}
            />
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 24,
  },
  logo: {
    fontSize: 28,
    fontWeight: '800',
    color: '#000000',
    letterSpacing: 1,
    marginBottom: 32,
  },
  title: {
    fontSize: 26,
    fontWeight: '400',
    color: '#000000',
    lineHeight: 34,
    marginBottom: 16,
    letterSpacing: -0.5,
  },
  countryRow: {
    marginBottom: 24,
  },
  countryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
  },
  changeLink: {
    fontSize: 14,
    color: '#666666',
    textDecorationLine: 'underline',
  },
  emailRow: {
    marginBottom: 24,
  },
  emailDisplay: {
    fontSize: 14,
    color: '#666666',
  },
  editLink: {
    fontSize: 14,
    color: '#666666',
    textDecorationLine: 'underline',
  },
  inputContainer: {
    borderWidth: 1,
    borderColor: '#CCCCCC',
    borderRadius: 8,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#000000',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  inputIcon: {
    padding: 16,
  },
  termsText: {
    fontSize: 13,
    color: '#666666',
    lineHeight: 20,
    marginTop: 8,
    marginBottom: 24,
  },
  link: {
    textDecorationLine: 'underline',
    color: '#000000',
  },
  resendText: {
    fontSize: 13,
    color: '#666666',
    textAlign: 'right',
    marginBottom: 24,
  },
  forgotPassword: {
    fontSize: 13,
    color: '#666666',
    textDecorationLine: 'underline',
    marginBottom: 24,
  },
  errorText: {
    fontSize: 13,
    color: '#FF3B30',
    marginBottom: 12,
  },
  continueButton: {
    backgroundColor: '#000000',
    borderRadius: 24,
    paddingVertical: 14,
    paddingHorizontal: 32,
    alignSelf: 'flex-end',
  },
  signInButton: {
    backgroundColor: '#000000',
    borderRadius: 24,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  buttonLoading: {
    opacity: 0.7,
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  usePasswordButton: {
    borderWidth: 1.5,
    borderColor: '#CCCCCC',
    borderRadius: 24,
    paddingVertical: 16,
    alignItems: 'center',
  },
  usePasswordText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#000000',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.35)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 24,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 12,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: '#000000',
  },
  countryItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  countryItemText: {
    fontSize: 15,
    color: '#000000',
  },
});

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

type Step = 'email' | 'details';

export default function RegisterScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { register } = useAuthStore();

  const [step, setStep] = useState<Step>('email');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form fields
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [challengeId, setChallengeId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [day, setDay] = useState('');
  const [month, setMonth] = useState('');
  const [year, setYear] = useState('');
  const [agreeToEmails, setAgreeToEmails] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState('India');
  const [countryModalVisible, setCountryModalVisible] = useState(false);
  const [countryQuery, setCountryQuery] = useState('');

  // Resend timer
  const [resendTimer, setResendTimer] = useState(30);

  useEffect(() => {
    if (step === 'details' && resendTimer > 0) {
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
        const result = await api.post<{ challenge_id: string }>('/auth/otp/request', { email: normalizedEmail, purpose: 'register' });
        setEmail(normalizedEmail);
        setChallengeId(result.challenge_id);
        setStep('details');
        setResendTimer(30);
      } catch (err: unknown) {
        setError(apiErrorMessage(err, 'Failed to send code'));
      } finally {
        setLoading(false);
      }
    };
    run();
  };

  const handleCreateAccount = async () => {
    if (!/^\d{6}$/.test(code)) {
      setError('Please enter the verification code');
      return;
    }
    if (!firstName.trim()) {
      setError('Please enter your first name');
      return;
    }
    if (!lastName.trim()) {
      setError('Please enter your last name');
      return;
    }
    const parsedDay = Number(day);
    const parsedMonth = Number(month);
    const parsedYear = Number(year);
    const birthDate = new Date(Date.UTC(parsedYear, parsedMonth - 1, parsedDay));
    const today = new Date();
    if (
      !/^\d{1,2}$/.test(day) ||
      !/^\d{1,2}$/.test(month) ||
      !/^\d{4}$/.test(year) ||
      birthDate.getUTCFullYear() !== parsedYear ||
      birthDate.getUTCMonth() !== parsedMonth - 1 ||
      birthDate.getUTCDate() !== parsedDay ||
      birthDate > today
    ) {
      setError('Please enter a valid date of birth');
      return;
    }
    if (!agreeToTerms) {
      setError('Please agree to the Terms of Use');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const dob = `${year.padStart(4, '0')}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
      await register(email, `${firstName.trim()} ${lastName.trim()}`, code, challengeId, {
        country: selectedCountry,
        date_of_birth: dob,
        marketing_opt_in: agreeToEmails,
      });
      router.replace('/onboarding/goals');
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Registration failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (resendTimer > 0 || loading) return;
    setLoading(true);
    setError('');
    try {
      const result = await api.post<{ challenge_id: string }>('/auth/otp/request', { email, purpose: 'register' });
      setChallengeId(result.challenge_id);
      setResendTimer(30);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Failed to resend code'));
    } finally {
      setLoading(false);
    }
  };

  const filteredCountries = countries.filter((country) =>
    country.toLowerCase().includes(countryQuery.trim().toLowerCase())
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          accessibilityLabel={step === 'email' ? 'Close registration' : 'Back to email'}
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
                style={[styles.continueButton, (!email || loading) && styles.continueButtonDisabled]}
                onPress={handleContinue}
                disabled={!email || loading}
              >
                {loading ? <ActivityIndicator color="#FFFFFF" size="small" /> : <Text style={styles.continueButtonText}>Continue</Text>}
              </TouchableOpacity>
            </>
          ) : (
            <>
              {/* Details Step */}
              <Text style={styles.title}>Now let&apos;s make you a Runlete Member.</Text>

              <Text style={styles.sentCodeText}>
                We&apos;ve sent a code to{'\n'}
                <Text style={styles.emailDisplay}>{email}</Text>
                {'  '}
                <Text style={styles.editLink} onPress={() => setStep('email')}>Edit</Text>
              </Text>

              {/* Code Input */}
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="6-digit code*"
                  placeholderTextColor="#999999"
                  value={code}
                  onChangeText={setCode}
                  keyboardType="number-pad"
                  maxLength={6}
                  accessibilityLabel="Six digit registration code"
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

              {/* Name Inputs */}
              <View style={styles.nameRow}>
                <View style={[styles.inputContainer, styles.halfInput]}>
                  <TextInput
                    style={styles.input}
                    placeholder="First Name*"
                    placeholderTextColor="#999999"
                    value={firstName}
                    onChangeText={setFirstName}
                    autoCapitalize="words"
                  />
                </View>
                <View style={[styles.inputContainer, styles.halfInput]}>
                  <TextInput
                    style={styles.input}
                    placeholder="Last Name*"
                    placeholderTextColor="#999999"
                    value={lastName}
                    onChangeText={setLastName}
                    autoCapitalize="words"
                  />
                </View>
              </View>

              {/* Date of Birth */}
              <Text style={styles.dobLabel}>Date of Birth</Text>
              <View style={styles.dobRow}>
                <View style={[styles.inputContainer, styles.dobInput]}>
                  <TextInput
                    style={styles.input}
                    placeholder="Day*"
                    placeholderTextColor="#999999"
                    value={day}
                    onChangeText={setDay}
                    keyboardType="number-pad"
                    maxLength={2}
                  />
                </View>
                <View style={[styles.inputContainer, styles.dobInput]}>
                  <TextInput
                    style={styles.input}
                    placeholder="Month*"
                    placeholderTextColor="#999999"
                    value={month}
                    onChangeText={setMonth}
                    keyboardType="number-pad"
                    maxLength={2}
                  />
                </View>
                <View style={[styles.inputContainer, styles.dobInput]}>
                  <TextInput
                    style={styles.input}
                    placeholder="Year*"
                    placeholderTextColor="#999999"
                    value={year}
                    onChangeText={setYear}
                    keyboardType="number-pad"
                    maxLength={4}
                  />
                </View>
              </View>
              <Text style={styles.dobHint}>Get a Runlete Member Reward on your birthday.</Text>

              {/* Checkboxes */}
              <TouchableOpacity
                accessibilityRole="checkbox"
                accessibilityState={{ checked: agreeToEmails }}
                style={styles.checkboxRow}
                onPress={() => setAgreeToEmails(!agreeToEmails)}
              >
                <View style={[styles.checkbox, agreeToEmails && styles.checkboxChecked]}>
                  {agreeToEmails && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
                </View>
                <Text style={styles.checkboxText}>
                  Sign up for emails to get updates from Runlete on products, offers and your Member benefits.
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                accessibilityRole="checkbox"
                accessibilityState={{ checked: agreeToTerms }}
                style={styles.checkboxRow}
                onPress={() => setAgreeToTerms(!agreeToTerms)}
              >
                <View style={[styles.checkbox, agreeToTerms && styles.checkboxChecked]}>
                  {agreeToTerms && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
                </View>
                <Text style={styles.checkboxText}>
                  I agree to Runlete&apos;s{' '}
                  <Text style={styles.link} onPress={() => router.push('/privacy-policy')}>
                    Privacy Policy
                  </Text>{' '}
                  and{' '}
                  <Text style={styles.link} onPress={() => router.push('/terms-of-use')}>
                    Terms of Use
                  </Text>.
                </Text>
              </TouchableOpacity>

              {error ? <Text style={styles.errorText}>{error}</Text> : null}

              {/* Create Account Button */}
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityState={{ disabled: loading, busy: loading }}
                style={[styles.createButton, loading && styles.createButtonLoading]}
                onPress={handleCreateAccount}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.createButtonText}>Create Account</Text>
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
  inputContainer: {
    borderWidth: 1,
    borderColor: '#CCCCCC',
    borderRadius: 8,
    marginBottom: 12,
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
  halfInput: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
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
  continueButton: {
    backgroundColor: '#000000',
    borderRadius: 24,
    paddingVertical: 14,
    paddingHorizontal: 32,
    alignSelf: 'flex-end',
    marginTop: 16,
  },
  continueButtonDisabled: {
    opacity: 0.4,
  },
  continueButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  sentCodeText: {
    fontSize: 14,
    color: '#666666',
    lineHeight: 22,
    marginBottom: 24,
  },
  emailDisplay: {
    color: '#000000',
    fontWeight: '500',
  },
  editLink: {
    color: '#666666',
    textDecorationLine: 'underline',
  },
  resendText: {
    fontSize: 13,
    color: '#666666',
    textAlign: 'right',
    marginBottom: 16,
  },
  requirements: {
    marginBottom: 24,
  },
  requirementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  requirementText: {
    fontSize: 12,
    color: '#999999',
  },
  requirementMet: {
    color: '#4CAF50',
  },
  dobLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#000000',
    marginBottom: 12,
  },
  dobRow: {
    flexDirection: 'row',
    gap: 12,
  },
  dobInput: {
    flex: 1,
  },
  dobHint: {
    fontSize: 12,
    color: '#999999',
    marginTop: 4,
    marginBottom: 24,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 16,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderWidth: 1.5,
    borderColor: '#CCCCCC',
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  checkboxChecked: {
    backgroundColor: '#000000',
    borderColor: '#000000',
  },
  checkboxText: {
    flex: 1,
    fontSize: 13,
    color: '#000000',
    lineHeight: 20,
  },
  errorText: {
    fontSize: 13,
    color: '#FF3B30',
    marginBottom: 12,
  },
  createButton: {
    backgroundColor: '#000000',
    borderRadius: 24,
    paddingVertical: 14,
    paddingHorizontal: 32,
    alignSelf: 'flex-end',
    marginTop: 16,
  },
  createButtonLoading: {
    opacity: 0.7,
  },
  createButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF',
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

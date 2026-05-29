/* eslint-disable react/no-unescaped-entities */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
  TouchableWithoutFeedback,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Image
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { GlassCard } from '../../src/components/GlassCard';
import { Badge } from '../../src/components/Badge';
import { ProgressBar } from '../../src/components/ProgressBar';
import { Button } from '../../src/components/Button';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

interface Meal {
  id: string;
  meal_type: string;
  name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber: number;
  date: string;
  status?: string;
  ai_analyzed: boolean;
}

interface DailySummary {
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  total_fiber: number;
  calorie_goal: number;
  protein_goal: number;
  carbs_goal: number;
  fat_goal: number;
  fiber_goal: number;
  bmr?: number;
  tdee?: number;
  goal_type?: 'weight_loss' | 'weight_gain' | 'maintenance';
  meals: Meal[];
  achievements?: {
    current_streak: number;
    longest_streak: number;
    total_meals: number;
    badges: string[];
  };
}

export default function NutritionScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { action } = useLocalSearchParams<{ action?: string }>();
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [summary, setSummary] = useState<DailySummary | null>(null);

  // Date selector state
  const [selectedDate, setSelectedDate] = useState(new Date());

  // Modal State
  const [modalVisible, setModalVisible] = useState(false);
  const [activeMealType, setActiveMealType] = useState<string>('');

  // Review Modal State
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [analyzedData, setAnalyzedData] = useState<any>(null);

  // Date Picker Modal State
  const [datePickerVisible, setDatePickerVisible] = useState(false);
  const [pickerMonth, setPickerMonth] = useState(new Date().getMonth());
  const [pickerYear, setPickerYear] = useState(new Date().getFullYear());

  // Mood Popup State
  const [moodPopupVisible, setMoodPopupVisible] = useState(false);
  const [loggedMealId, setLoggedMealId] = useState<string | undefined>(undefined);

  useEffect(() => {
    fetchDailySummary(selectedDate);
  }, [selectedDate]);

  // Handle scan action from query params (from home screen camera button)
  useEffect(() => {
    if (action === 'scan') {
      // Open the meal options modal with a default meal type
      setActiveMealType('Lunch');
      setModalVisible(true);
    }
  }, [action]);

  const fetchDailySummary = async (date: Date) => {
    setLoading(true);
    try {
      const dateStr = date.toISOString().split('T')[0];
      const data = await api.get<DailySummary>(`/meals/daily-summary?date=${dateStr}`);
      setSummary(data);
    } catch (error) {
      console.error('Error fetching nutrition:', error);
    } finally {
      setLoading(false);
    }
  };

  // Date navigation
  const goToPreviousDay = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() - 1);
    setSelectedDate(newDate);
  };

  const goToNextDay = () => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + 1);
    // Don't allow future dates
    if (newDate <= new Date()) {
      setSelectedDate(newDate);
    }
  };

  const goToToday = () => {
    setSelectedDate(new Date());
  };

  // Calendar helper functions
  const openDatePicker = () => {
    setPickerMonth(selectedDate.getMonth());
    setPickerYear(selectedDate.getFullYear());
    setDatePickerVisible(true);
  };

  const getDaysInMonth = (month: number, year: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (month: number, year: number) => {
    return new Date(year, month, 1).getDay();
  };

  const selectDate = (day: number) => {
    const newDate = new Date(pickerYear, pickerMonth, day);
    // Don't allow future dates
    if (newDate <= new Date()) {
      setSelectedDate(newDate);
      setDatePickerVisible(false);
    }
  };

  const goToPreviousMonth = () => {
    if (pickerMonth === 0) {
      setPickerMonth(11);
      setPickerYear(pickerYear - 1);
    } else {
      setPickerMonth(pickerMonth - 1);
    }
  };

  const goToNextMonth = () => {
    const now = new Date();
    const nextMonth = pickerMonth === 11 ? 0 : pickerMonth + 1;
    const nextYear = pickerMonth === 11 ? pickerYear + 1 : pickerYear;

    // Don't allow navigating past current month
    if (nextYear < now.getFullYear() || (nextYear === now.getFullYear() && nextMonth <= now.getMonth())) {
      setPickerMonth(nextMonth);
      if (pickerMonth === 11) {
        setPickerYear(pickerYear + 1);
      }
    }
  };

  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const formatDateDisplay = (date: Date) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const isToday = selectedDate.toDateString() === new Date().toDateString();

  const handleScanMeal = async () => {
    setModalVisible(false);
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Camera permission is required to scan meals');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.5, // Lower quality for faster upload
        base64: true,
        allowsEditing: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        processImage(result.assets[0].base64);
      }
    } catch (error) {
      console.error('Error scanning meal:', error);
    }
  };

  const handlePickImage = async () => {
    setModalVisible(false);
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Photo library permission is required');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.5,
        base64: true,
        allowsEditing: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        processImage(result.assets[0].base64);
      }
    } catch (error) {
      console.error('Error picking image:', error);
    }
  };

  const processImage = async (base64: string) => {
    setAnalyzing(true);
    try {
      // Call with save=false to review first
      const response = await api.post('/meals/analyze?save=false', {
        meal_type: activeMealType,
        image_base64: base64,
      });

      setAnalyzedData({ ...(response as any), image_base64: base64 });
      setReviewModalVisible(true);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to analyze meal');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmLog = async () => {
    try {
      setLoading(true);
      // Save the confirmed data
      const mealResult = await api.post<{ id?: string }>('/meals/analyze', {
        meal_type: activeMealType,
        name: analyzedData.name,
        calories: parseInt(analyzedData.calories),
        protein: parseFloat(analyzedData.protein),
        carbs: parseFloat(analyzedData.carbs),
        fat: parseFloat(analyzedData.fat),
        image_base64: analyzedData.image_base64,
      });

      setReviewModalVisible(false);
      setAnalyzedData(null);
      await fetchDailySummary(selectedDate);

      // Show mood popup after meal logging
      setLoggedMealId(mealResult?.id);
      setMoodPopupVisible(true);
    } catch (err) {
      Alert.alert('Error', 'Failed to save meal');
    } finally {
      setLoading(false);
    }
  };

  const handleMoodSelect = async (moodValue: number) => {
    try {
      const moodEmojis: Record<number, string> = { 1: '😢', 2: '😔', 3: '😐', 4: '😊', 5: '😄' };
      await api.post('/mood', {
        mood_value: moodValue,
        mood_emoji: moodEmojis[moodValue],
        activities: ['Cooking'],
        trigger: 'meal',
        trigger_id: loggedMealId,
      });
      Alert.alert('Thanks!', 'Your mood has been logged 🎉');
    } catch (error) {
      console.log('Mood logging failed');
    } finally {
      setMoodPopupVisible(false);
      setLoggedMealId(undefined);
    }
  };

  const closeMoodPopup = () => {
    setMoodPopupVisible(false);
    setLoggedMealId(undefined);
  };

  const handleManualEntry = () => {
    setModalVisible(false);
    // Open review modal with empty data
    setAnalyzedData({
      name: '',
      calories: '',
      protein: '',
      carbs: '',
      fat: '',
      foods_identified: []
    });
    setReviewModalVisible(true);
  };

  const openMealOptions = (mealType: string) => {
    setActiveMealType(mealType);
    setModalVisible(true);
  };

  const mealTypes = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

  const getMealsByType = (type: string) => {
    return summary?.meals.filter(m => m.meal_type === type) || [];
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Nutrition</Text>
        <View style={{ width: 44 }} />
      </View>

      {analyzing && (
        <View style={styles.analyzingOverlay}>
          <GlassCard style={styles.analyzingCard}>
            <ActivityIndicator size="large" color={colors.textPrimary} />
            <Text style={styles.analyzingText}>AI Analysis in Progress...</Text>
            <Text style={styles.analyzingSubtext}>Identifying foods & calculating macros</Text>
          </GlassCard>
        </View>
      )}

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Date Selector */}
        <View style={styles.dateSelector}>
          <TouchableOpacity onPress={goToPreviousDay} style={styles.dateArrow}>
            <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <TouchableOpacity onPress={openDatePicker} style={styles.dateDisplay}>
            <View style={styles.dateTextRow}>
              <Ionicons name="calendar-outline" size={18} color={colors.textSecondary} style={{ marginRight: 8 }} />
              <Text style={styles.dateText}>{formatDateDisplay(selectedDate)}</Text>
            </View>
            <Text style={styles.todayHint}>Tap to pick a date</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={goToNextDay}
            style={[styles.dateArrow, isToday && styles.dateArrowDisabled]}
            disabled={isToday}
          >
            <Ionicons
              name="chevron-forward"
              size={24}
              color={isToday ? colors.textTertiary : colors.textPrimary}
            />
          </TouchableOpacity>
        </View>

        {/* Daily Summary */}
        <GlassCard style={styles.summaryCard}>
          <Text style={styles.sectionTitle}>
            {isToday ? "TODAY'S NUTRITION" : formatDateDisplay(selectedDate).toUpperCase() + "'S NUTRITION"}
          </Text>

          <View style={styles.calorieRow}>
            <View style={styles.calorieRing}>
              <View style={styles.ringOuter}>
                <View style={styles.ringInner}>
                  <Text style={styles.calorieValue}>
                    {summary?.total_calories || 0}
                  </Text>
                  <Text style={styles.calorieLabel}>kcal</Text>
                </View>
              </View>
            </View>
            <View style={styles.calorieInfo}>
              <Text style={styles.calorieGoal}>
                Goal: {summary?.calorie_goal || 2000} kcal
              </Text>
              <ProgressBar
                progress={(summary?.total_calories || 0) / (summary?.calorie_goal || 2000) * 100}
                style={styles.calorieProgress}
              />
              <Text style={styles.calorieRemaining}>
                {Math.max(0, (summary?.calorie_goal || 2000) - (summary?.total_calories || 0))} kcal remaining
              </Text>
            </View>
          </View>

          {/* Macros */}
          <View style={styles.macrosGrid}>
            <View style={styles.macroBox}>
              <Text style={styles.macroValue}>{summary?.total_protein || 0}g</Text>
              <Text style={styles.macroLabel}>Protein</Text>
              <ProgressBar
                progress={(summary?.total_protein || 0) / (summary?.protein_goal || 150) * 100}
                height={4}
                style={styles.macroProgress}
              />
            </View>
            <View style={styles.macroBox}>
              <Text style={styles.macroValue}>{summary?.total_carbs || 0}g</Text>
              <Text style={styles.macroLabel}>Carbs</Text>
              <ProgressBar
                progress={(summary?.total_carbs || 0) / (summary?.carbs_goal || 250) * 100}
                height={4}
                style={styles.macroProgress}
              />
            </View>
            <View style={styles.macroBox}>
              <Text style={styles.macroValue}>{summary?.total_fat || 0}g</Text>
              <Text style={styles.macroLabel}>Fat</Text>
              <ProgressBar
                progress={(summary?.total_fat || 0) / (summary?.fat_goal || 65) * 100}
                height={4}
                style={styles.macroProgress}
              />
            </View>
          </View>
        </GlassCard>

        {/* Streak & Achievements Card (from Cal Tracking) */}
        {summary?.achievements && (
          <GlassCard style={styles.streakCard}>
            <View style={styles.streakHeader}>
              <View style={styles.streakInfo}>
                <Text style={styles.streakEmoji}>🔥</Text>
                <View>
                  <Text style={styles.streakValue}>{summary.achievements.current_streak}</Text>
                  <Text style={styles.streakLabel}>Day Streak</Text>
                </View>
              </View>
              <View style={styles.streakStats}>
                <Text style={styles.streakStatLabel}>
                  Longest: {summary.achievements.longest_streak} days
                </Text>
                <Text style={styles.streakStatLabel}>
                  Total Meals: {summary.achievements.total_meals}
                </Text>
              </View>
            </View>
            {summary.achievements.badges.length > 0 && (
              <View style={styles.badgesRow}>
                {summary.achievements.badges.slice(0, 4).map((badge, i) => (
                  <View key={i} style={styles.badgeChip}>
                    <Text style={styles.badgeIcon}>
                      {badge === 'first_meal' ? '🍽️' :
                        badge === 'meal_rookie' ? '🥉' :
                          badge === 'meal_veteran' ? '🥈' :
                            badge === 'week_warrior' ? '⚡' : '🏆'}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </GlassCard>
        )}

        {/* Personalized Metabolic Info (from Cal Tracking) */}
        {summary?.bmr && summary?.tdee && (
          <GlassCard style={styles.metabolicCard}>
            <Text style={styles.sectionTitle}>Your Metabolic Profile</Text>
            <View style={styles.metabolicGrid}>
              <View style={styles.metabolicItem}>
                <Text style={styles.metabolicValue}>{summary.bmr}</Text>
                <Text style={styles.metabolicLabel}>BMR (kcal)</Text>
              </View>
              <View style={styles.metabolicItem}>
                <Text style={styles.metabolicValue}>{summary.tdee}</Text>
                <Text style={styles.metabolicLabel}>TDEE (kcal)</Text>
              </View>
              <View style={styles.metabolicItem}>
                <Text style={styles.metabolicValue}>
                  {summary.goal_type === 'weight_loss' ? '📉' :
                    summary.goal_type === 'weight_gain' ? '📈' : '➡️'}
                </Text>
                <Text style={styles.metabolicLabel}>
                  {summary.goal_type?.replace('_', ' ') || 'Goal'}
                </Text>
              </View>
            </View>
          </GlassCard>
        )}

        {/* Quick Add */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>QUICK ADD</Text>
          <View style={styles.quickAddRow}>
            {mealTypes.map((type) => (
              <TouchableOpacity
                key={type}
                style={styles.quickAddButton}
                onPress={() => openMealOptions(type)}
              >
                <View style={styles.quickAddIcon}>
                  <Ionicons
                    name={
                      type === 'Breakfast' ? 'sunny-outline' :
                        type === 'Lunch' ? 'restaurant-outline' :
                          type === 'Dinner' ? 'moon-outline' :
                            'nutrition-outline'
                    }
                    size={20}
                    color={colors.textSecondary}
                  />
                </View>
                <Text style={styles.quickAddLabel}>{type}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Today's Meals */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>TODAY'S MEALS</Text>

          {mealTypes.map((type) => {
            const meals = getMealsByType(type);
            if (meals.length === 0) return null;

            return (
              <View key={type} style={styles.mealGroup}>
                <Text style={styles.mealGroupTitle}>{type}</Text>
                {meals.map((meal) => (
                  <GlassCard key={meal.id} style={styles.mealCard}>
                    <View style={styles.mealHeader}>
                      <View>
                        <Text style={styles.mealName}>{meal.name}</Text>
                        <Text style={styles.mealTime}>{formatTime(meal.date)}</Text>
                      </View>
                      <View style={styles.mealCalories}>
                        <Text style={styles.mealCalorieValue}>{meal.calories}</Text>
                        <Text style={styles.mealCalorieLabel}>kcal</Text>
                      </View>
                    </View>
                    <View style={styles.mealMacros}>
                      <Text style={styles.mealMacro}>P: {meal.protein}g</Text>
                      <Text style={styles.mealMacro}>C: {meal.carbs}g</Text>
                      <Text style={styles.mealMacro}>F: {meal.fat}g</Text>
                    </View>
                    {meal.status && (
                      <Badge
                        label={meal.status}
                        variant={meal.status === 'Balanced' ? 'outline' : 'filled'}
                        size="sm"
                        style={styles.mealBadge}
                      />
                    )}
                    {meal.ai_analyzed && (
                      <View style={styles.aiTag}>
                        <Ionicons name="sparkles" size={10} color={colors.textTertiary} />
                        <Text style={styles.aiTagText}>AI analyzed</Text>
                      </View>
                    )}
                  </GlassCard>
                ))}
              </View>
            );
          })}

          {(!summary?.meals || summary.meals.length === 0) && (
            <GlassCard style={styles.emptyCard}>
              <Ionicons name="restaurant-outline" size={40} color={colors.textTertiary} />
              <Text style={styles.emptyText}>No meals logged today</Text>
              <Text style={styles.emptySubtext}>Tap a meal type above to add</Text>
            </GlassCard>
          )}
        </View>
      </ScrollView>

      {/* Action Sheet Modal */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableWithoutFeedback onPress={() => setModalVisible(false)}>
          <View style={styles.modalOverlay}>
            <TouchableWithoutFeedback>
              <View style={[styles.modalContent, { paddingBottom: insets.bottom + 20 }]}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Log {activeMealType}</Text>
                  <Text style={styles.modalSubtitle}>Choose an option to track your calories</Text>
                </View>

                <TouchableOpacity style={styles.actionButton} onPress={handleScanMeal}>
                  <View style={[styles.iconContainer, { backgroundColor: '#E8F5E9' }]}>
                    <Ionicons name="camera" size={24} color="#2E7D32" />
                  </View>
                  <View style={styles.actionTextContainer}>
                    <Text style={styles.actionTitle}>Take Photo</Text>
                    <Text style={styles.actionSubtitle}>Snap a picture to analyze nutrition</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
                </TouchableOpacity>

                <TouchableOpacity style={styles.actionButton} onPress={handlePickImage}>
                  <View style={[styles.iconContainer, { backgroundColor: '#E3F2FD' }]}>
                    <Ionicons name="images" size={24} color="#1565C0" />
                  </View>
                  <View style={styles.actionTextContainer}>
                    <Text style={styles.actionTitle}>Upload from Gallery</Text>
                    <Text style={styles.actionSubtitle}>Choose an existing food photo</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
                </TouchableOpacity>

                <TouchableOpacity style={styles.actionButton} onPress={handleManualEntry}>
                  <View style={[styles.iconContainer, { backgroundColor: '#FFF3E0' }]}>
                    <Ionicons name="create" size={24} color="#EF6C00" />
                  </View>
                  <View style={styles.actionTextContainer}>
                    <Text style={styles.actionTitle}>Manual Entry</Text>
                    <Text style={styles.actionSubtitle}>Type in food name or calories</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setModalVisible(false)}
                >
                  <Text style={styles.cancelText}>Cancel</Text>
                </TouchableOpacity>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>

      {/* Review Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={reviewModalVisible}
        onRequestClose={() => setReviewModalVisible(false)}
      >
        <View style={styles.reviewModalContainer}>
          <View style={[styles.reviewModalContent, { paddingTop: insets.top + 20, paddingBottom: insets.bottom + 20 }]}>
            <View style={styles.reviewHeader}>
              <Text style={styles.reviewTitle}>Review Meal</Text>
              <TouchableOpacity onPress={() => setReviewModalVisible(false)}>
                <Ionicons name="close" size={24} color={colors.textPrimary} />
              </TouchableOpacity>
            </View>

            <ScrollView style={{ flex: 1 }} showsVerticalScrollIndicator={false}>
              {analyzedData?.image_base64 && (
                <Image
                  source={{ uri: `data:image/jpeg;base64,${analyzedData.image_base64}` }}
                  style={styles.reviewImage}
                />
              )}

              <Text style={styles.inputLabel}>MEAL NAME</Text>
              <TextInput
                style={styles.input}
                value={analyzedData?.name}
                onChangeText={(t) => setAnalyzedData({ ...analyzedData, name: t })}
                placeholder="Meal Name"
              />

              <View style={styles.macrosRow}>
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Text style={styles.inputLabel}>CALORIES</Text>
                  <TextInput
                    style={styles.input}
                    value={String(analyzedData?.calories || '')}
                    onChangeText={(t) => setAnalyzedData({ ...analyzedData, calories: t })}
                    keyboardType="numeric"
                    placeholder="0"
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.inputLabel}>PROTEIN (g)</Text>
                  <TextInput
                    style={styles.input}
                    value={String(analyzedData?.protein || '')}
                    onChangeText={(t) => setAnalyzedData({ ...analyzedData, protein: t })}
                    keyboardType="numeric"
                    placeholder="0"
                  />
                </View>
              </View>

              <View style={styles.macrosRow}>
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Text style={styles.inputLabel}>CARBS (g)</Text>
                  <TextInput
                    style={styles.input}
                    value={String(analyzedData?.carbs || '')}
                    onChangeText={(t) => setAnalyzedData({ ...analyzedData, carbs: t })}
                    keyboardType="numeric"
                    placeholder="0"
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.inputLabel}>FAT (g)</Text>
                  <TextInput
                    style={styles.input}
                    value={String(analyzedData?.fat || '')}
                    onChangeText={(t) => setAnalyzedData({ ...analyzedData, fat: t })}
                    keyboardType="numeric"
                    placeholder="0"
                  />
                </View>
              </View>

              {analyzedData?.foods_identified && analyzedData.foods_identified.length > 0 && (
                <View style={styles.foodsContainer}>
                  <Text style={styles.foodsLabel}>DETECTED FOODS</Text>
                  {analyzedData.foods_identified.map((food: string, i: number) => (
                    <View key={i} style={styles.foodItem}>
                      <Ionicons name="checkmark-circle" size={16} color={colors.textTertiary} />
                      <Text style={styles.foodText}>{food}</Text>
                    </View>
                  ))}
                </View>
              )}
            </ScrollView>

            <Button
              title="Log Meal"
              onPress={handleConfirmLog}
              loading={loading}
              fullWidth
              size="lg"
              style={{ marginTop: 20 }}
            />
          </View>
        </View>
      </Modal>

      {/* Date Picker Modal */}
      <Modal
        visible={datePickerVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setDatePickerVisible(false)}
      >
        <TouchableWithoutFeedback onPress={() => setDatePickerVisible(false)}>
          <View style={styles.modalOverlay}>
            <TouchableWithoutFeedback>
              <View style={styles.datePickerModal}>
                {/* Month/Year Header */}
                <View style={styles.datePickerHeader}>
                  <TouchableOpacity onPress={goToPreviousMonth} style={styles.monthArrow}>
                    <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
                  </TouchableOpacity>
                  <Text style={styles.monthYearText}>
                    {monthNames[pickerMonth]} {pickerYear}
                  </Text>
                  <TouchableOpacity onPress={goToNextMonth} style={styles.monthArrow}>
                    <Ionicons name="chevron-forward" size={24} color={colors.textPrimary} />
                  </TouchableOpacity>
                </View>

                {/* Day Names */}
                <View style={styles.dayNamesRow}>
                  {dayNames.map((day) => (
                    <Text key={day} style={styles.dayName}>{day}</Text>
                  ))}
                </View>

                {/* Calendar Grid */}
                <View style={styles.calendarGrid}>
                  {/* Empty cells for days before first of month */}
                  {Array.from({ length: getFirstDayOfMonth(pickerMonth, pickerYear) }).map((_, i) => (
                    <View key={`empty-${i}`} style={styles.calendarDay} />
                  ))}

                  {/* Days of month */}
                  {Array.from({ length: getDaysInMonth(pickerMonth, pickerYear) }).map((_, i) => {
                    const day = i + 1;
                    const dateToCheck = new Date(pickerYear, pickerMonth, day);
                    const isFuture = dateToCheck > new Date();
                    const isSelected = selectedDate.getDate() === day &&
                      selectedDate.getMonth() === pickerMonth &&
                      selectedDate.getFullYear() === pickerYear;
                    const isTodayDate = new Date().getDate() === day &&
                      new Date().getMonth() === pickerMonth &&
                      new Date().getFullYear() === pickerYear;

                    return (
                      <TouchableOpacity
                        key={day}
                        style={[
                          styles.calendarDay,
                          isSelected && styles.calendarDaySelected,
                          isTodayDate && !isSelected && styles.calendarDayToday,
                        ]}
                        onPress={() => !isFuture && selectDate(day)}
                        disabled={isFuture}
                      >
                        <Text style={[
                          styles.calendarDayText,
                          isSelected && styles.calendarDayTextSelected,
                          isFuture && styles.calendarDayTextDisabled,
                        ]}>
                          {day}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                {/* Quick Actions */}
                <View style={styles.datePickerActions}>
                  <TouchableOpacity
                    style={styles.todayButton}
                    onPress={() => {
                      setSelectedDate(new Date());
                      setDatePickerVisible(false);
                    }}
                  >
                    <Text style={styles.todayButtonText}>Go to Today</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>

      {/* Mood Popup Modal */}
      <Modal
        visible={moodPopupVisible}
        transparent
        animationType="fade"
        onRequestClose={closeMoodPopup}
      >
        <TouchableWithoutFeedback onPress={closeMoodPopup}>
          <View style={styles.modalOverlay}>
            <TouchableWithoutFeedback>
              <View style={styles.moodPopup}>
                {/* Close Button */}
                <TouchableOpacity style={styles.moodPopupClose} onPress={closeMoodPopup}>
                  <Ionicons name="close" size={24} color={colors.textTertiary} />
                </TouchableOpacity>

                {/* Title */}
                <Text style={styles.moodPopupTitle}>Meal Logged! 🍽️</Text>
                <Text style={styles.moodPopupSubtitle}>How are you feeling?</Text>

                {/* Mood Options */}
                <View style={styles.moodPopupOptions}>
                  {[
                    { value: 1, emoji: '😢', label: 'Terrible' },
                    { value: 2, emoji: '😔', label: 'Bad' },
                    { value: 3, emoji: '😐', label: 'Okay' },
                    { value: 4, emoji: '😊', label: 'Good' },
                    { value: 5, emoji: '😄', label: 'Amazing' },
                  ].map((mood) => (
                    <TouchableOpacity
                      key={mood.value}
                      style={styles.moodPopupButton}
                      onPress={() => handleMoodSelect(mood.value)}
                    >
                      <Text style={styles.moodPopupEmoji}>{mood.emoji}</Text>
                      <Text style={styles.moodPopupLabel}>{mood.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                {/* Skip Text */}
                <TouchableOpacity onPress={closeMoodPopup} style={styles.moodPopupSkip}>
                  <Text style={styles.moodPopupSkipText}>Skip for now</Text>
                </TouchableOpacity>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
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
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
  },
  title: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  // Date Selector Styles
  dateSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    marginBottom: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: 12,
    marginHorizontal: spacing.md,
  },
  dateArrow: {
    padding: spacing.md,
  },
  dateArrowDisabled: {
    opacity: 0.3,
  },
  dateDisplay: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  dateText: {
    ...typography.h4,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  todayHint: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  analyzingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 100,
  },
  analyzingCard: {
    alignItems: 'center',
    paddingVertical: spacing.xxxl,
    paddingHorizontal: spacing.xxxl,
  },
  analyzingText: {
    ...typography.h4,
    color: colors.textPrimary,
    marginTop: spacing.lg,
  },
  analyzingSubtext: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
  },
  summaryCard: {
    marginBottom: spacing.xxl,
  },
  sectionTitle: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  calorieRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  calorieRing: {
    marginRight: spacing.xl,
  },
  ringOuter: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 8,
    borderColor: colors.progressTrack,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ringInner: {
    alignItems: 'center',
  },
  calorieValue: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  calorieLabel: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  calorieInfo: {
    flex: 1,
  },
  calorieGoal: {
    ...typography.bodyMedium,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  calorieProgress: {
    marginBottom: spacing.sm,
  },
  calorieRemaining: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  macrosGrid: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  macroBox: {
    flex: 1,
    backgroundColor: colors.separator,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  macroValue: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  macroLabel: {
    ...typography.caption,
    color: colors.textTertiary,
    marginBottom: spacing.sm,
  },
  macroProgress: {
    width: '100%',
  },
  section: {
    marginBottom: spacing.xxl,
  },
  quickAddRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  quickAddButton: {
    alignItems: 'center',
    flex: 1,
  },
  quickAddIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  quickAddLabel: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  mealGroup: {
    marginBottom: spacing.lg,
  },
  mealGroupTitle: {
    ...typography.captionMedium,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  mealCard: {
    marginBottom: spacing.sm,
  },
  mealHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  mealName: {
    ...typography.body,
    color: colors.textPrimary,
  },
  mealTime: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  mealCalories: {
    alignItems: 'flex-end',
  },
  mealCalorieValue: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  mealCalorieLabel: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  mealMacros: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  mealMacro: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  mealBadge: {
    marginTop: spacing.sm,
  },
  aiTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.sm,
  },
  aiTagText: {
    ...typography.caption,
    color: colors.textTertiary,
    fontSize: 10,
  },
  emptyCard: {
    alignItems: 'center',
    paddingVertical: spacing.xxxl,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  emptySubtext: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing.lg,
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: -2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  modalHeader: {
    marginBottom: spacing.xl,
    alignItems: 'center',
  },
  modalTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  modalSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.separator,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  actionTextContainer: {
    flex: 1,
  },
  actionTitle: {
    ...typography.bodySemibold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  actionSubtitle: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  cancelButton: {
    marginTop: spacing.sm,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  cancelText: {
    ...typography.bodySemibold,
    color: colors.textSecondary,
  },
  // Review Modal
  reviewModalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  reviewModalContent: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  reviewTitle: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  reviewImage: {
    width: '100%',
    height: 200,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.lg,
    resizeMode: 'cover',
  },
  inputLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
  },
  input: {
    backgroundColor: colors.separator,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...typography.body,
    color: colors.textPrimary,
  },
  macrosRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  foodsContainer: {
    marginTop: spacing.lg,
    padding: spacing.md,
    backgroundColor: colors.separator,
    borderRadius: borderRadius.lg,
  },
  foodsLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  foodItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  foodText: {
    ...typography.body,
    color: colors.textPrimary,
  },
  // Streak & Achievements (from Cal Tracking)
  streakCard: {
    marginBottom: spacing.xxl,
    backgroundColor: '#FFF8E1',
    borderColor: '#FFE082',
  },
  streakHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  streakInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  streakEmoji: {
    fontSize: 40,
  },
  streakValue: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  streakLabel: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  streakStats: {
    alignItems: 'flex-end',
  },
  streakStatLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  badgesRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#FFE082',
  },
  badgeChip: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeIcon: {
    fontSize: 24,
  },
  // Metabolic Info
  metabolicCard: {
    marginBottom: spacing.xxl,
  },
  metabolicGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.md,
  },
  metabolicItem: {
    flex: 1,
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.separator,
    borderRadius: borderRadius.md,
    marginHorizontal: spacing.xs,
  },
  metabolicValue: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  metabolicLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    textTransform: 'capitalize',
  },
  // Date Picker Modal Styles
  dateTextRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  datePickerModal: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    width: '90%',
    maxWidth: 360,
  },
  datePickerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  monthArrow: {
    padding: spacing.sm,
  },
  monthYearText: {
    ...typography.h4,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  dayNamesRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.separator,
    paddingBottom: spacing.sm,
  },
  dayName: {
    ...typography.caption,
    color: colors.textSecondary,
    width: 40,
    textAlign: 'center',
    fontWeight: '600',
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
  },
  calendarDay: {
    width: '14.28%',
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  calendarDaySelected: {
    backgroundColor: colors.accentOrange,
    borderRadius: 20,
  },
  calendarDayToday: {
    borderWidth: 2,
    borderColor: colors.accentOrange,
    borderRadius: 20,
  },
  calendarDayText: {
    ...typography.body,
    color: colors.textPrimary,
  },
  calendarDayTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  calendarDayTextDisabled: {
    color: colors.textDisabled,
  },
  datePickerActions: {
    marginTop: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.separator,
    paddingTop: spacing.md,
    alignItems: 'center',
  },
  todayButton: {
    backgroundColor: colors.accentOrange,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  todayButtonText: {
    ...typography.body,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  // Mood Popup Styles
  moodPopup: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    width: '90%',
    maxWidth: 360,
    alignItems: 'center',
  },
  moodPopupClose: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    padding: spacing.sm,
  },
  moodPopupTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
  },
  moodPopupSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.xl,
  },
  moodPopupOptions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: spacing.lg,
  },
  moodPopupButton: {
    alignItems: 'center',
    padding: spacing.sm,
  },
  moodPopupEmoji: {
    fontSize: 40,
    marginBottom: spacing.xs,
  },
  moodPopupLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    fontSize: 11,
  },
  moodPopupSkip: {
    paddingVertical: spacing.sm,
  },
  moodPopupSkipText: {
    ...typography.body,
    color: colors.textTertiary,
  },
});

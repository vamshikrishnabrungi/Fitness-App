import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../../src/components/GlassCard';
import { ProgressBar } from '../../src/components/ProgressBar';
import { Button } from '../../src/components/Button';
import { useAuthStore } from '../../src/store/authStore';
import { api } from '../../src/utils/api';
import { colors, typography, spacing, borderRadius } from '../../src/utils/theme';

interface Client {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  profile?: {
    weight?: number;
    height?: number;
    fitness_level?: string;
  };
  total_workouts: number;
  completed_workouts: number;
  compliance_rate: number;
}

interface SearchUser {
  id: string;
  name: string;
  email: string;
}

type TabType = 'clients' | 'search' | 'workouts' | 'meals' | 'goals';

export default function CoachDashboard() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuthStore();
  const isCoach = user?.mode === 'coach';

  // State
  const [clients, setClients] = useState<Client[]>([]);
  const [searchResults, setSearchResults] = useState<SearchUser[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(isCoach);
  const [activeTab, setActiveTab] = useState<TabType>('clients');

  // Modals
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [clientDetailVisible, setClientDetailVisible] = useState(false);

  // Form data
  const [workoutForm, setWorkoutForm] = useState({
    title: '',
    description: '',
    workout_type: 'strength',
    difficulty: 'intermediate',
    duration: '45',
    exercises: [] as { name: string; sets: number; reps: number }[],
  });

  const [mealForm, setMealForm] = useState({
    title: '',
    description: '',
    meal_type: 'lunch',
    total_calories: '500',
  });

  const [goalForm, setGoalForm] = useState({
    title: '',
    description: '',
    goal_type: 'weight_loss',
    target_value: '',
    unit: 'kg',
    target_date: '',
  });

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const clientsData = await api.get<Client[]>('/coach/clients').catch(() => []);
      setClients(clientsData);
    } catch (error) {
      console.error('Error fetching coach data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      if (isCoach) {
        fetchData();
      } else {
        setLoading(false);
        setClients([]);
        setSearchResults([]);
      }
    }, [isCoach, fetchData])
  );

  // Search users
  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const results = await api.get<SearchUser[]>(`/coach/search-users?query=${encodeURIComponent(query)}`);
      setSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  // Send connection request
  const sendRequest = async (clientId: string) => {
    try {
      await api.post('/coach/send-request', { client_id: clientId });
      Alert.alert('Success', 'Connection request sent!');
      setSearchResults(searchResults.filter(u => u.id !== clientId));
    } catch (error) {
      console.error('Error sending request:', error);
      Alert.alert('Error', 'Failed to send request');
    }
  };

  // Create workout for client
  const createWorkout = async () => {
    if (!selectedClient || !workoutForm.title) {
      Alert.alert('Error', 'Please fill in workout details');
      return;
    }

    try {
      await api.post('/coach/workouts', {
        client_id: selectedClient.id,
        title: workoutForm.title,
        description: workoutForm.description,
        workout_type: workoutForm.workout_type,
        difficulty: workoutForm.difficulty,
        duration: parseInt(workoutForm.duration),
        exercises: workoutForm.exercises,
      });

      Alert.alert('Success', 'Workout assigned!');
      setWorkoutForm({ title: '', description: '', workout_type: 'strength', difficulty: 'intermediate', duration: '45', exercises: [] });
      fetchData();
    } catch (error) {
      console.error('Error creating workout:', error);
      Alert.alert('Error', 'Failed to create workout');
    }
  };

  // Create meal for client
  const createMeal = async () => {
    if (!selectedClient || !mealForm.title) {
      Alert.alert('Error', 'Please fill in meal details');
      return;
    }

    try {
      await api.post('/coach/meals', {
        client_id: selectedClient.id,
        title: mealForm.title,
        description: mealForm.description,
        meal_type: mealForm.meal_type,
        total_calories: parseInt(mealForm.total_calories),
      });

      Alert.alert('Success', 'Meal plan assigned!');
      setMealForm({ title: '', description: '', meal_type: 'lunch', total_calories: '500' });
    } catch (error) {
      console.error('Error creating meal:', error);
      Alert.alert('Error', 'Failed to create meal plan');
    }
  };

  // Create goal for client
  const createGoal = async () => {
    if (!selectedClient || !goalForm.title) {
      Alert.alert('Error', 'Please fill in goal details');
      return;
    }

    try {
      await api.post('/coach/goals', {
        client_id: selectedClient.id,
        title: goalForm.title,
        description: goalForm.description,
        goal_type: goalForm.goal_type,
        target_value: parseFloat(goalForm.target_value) || undefined,
        unit: goalForm.unit,
        target_date: goalForm.target_date || undefined,
      });

      Alert.alert('Success', 'Goal set!');
      setGoalForm({ title: '', description: '', goal_type: 'weight_loss', target_value: '', unit: 'kg', target_date: '' });
    } catch (error) {
      console.error('Error creating goal:', error);
      Alert.alert('Error', 'Failed to create goal');
    }
  };

  // Open client detail
  const openClientDetail = (client: Client) => {
    setSelectedClient(client);
    setClientDetailVisible(true);
  };

  const tabs: { key: TabType; label: string; icon: string }[] = [
    { key: 'clients', label: 'Clients', icon: 'people-outline' },
    { key: 'search', label: 'Add', icon: 'person-add-outline' },
    { key: 'workouts', label: 'Workouts', icon: 'barbell-outline' },
    { key: 'meals', label: 'Meals', icon: 'restaurant-outline' },
    { key: 'goals', label: 'Goals', icon: 'flag-outline' },
  ];

  // Workout types
  const workoutTypes = ['strength', 'cardio', 'hiit', 'flexibility', 'endurance'];
  const difficulties = ['beginner', 'intermediate', 'advanced'];
  const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];
  const goalTypes = ['weight_loss', 'muscle_gain', 'strength', 'endurance', 'flexibility', 'general_fitness'];

  if (!isCoach) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.title}>Coach Dashboard</Text>
          <View style={{ width: 44 }} />
        </View>

        <View style={styles.roleGateContainer}>
          <GlassCard style={styles.roleGateCard}>
            <Ionicons name="shield-checkmark-outline" size={40} color={colors.accentOrange} />
            <Text style={styles.roleGateTitle}>Coach mode required</Text>
            <Text style={styles.roleGateText}>
              Switch your profile to Coach mode to manage clients, assign workouts, and review requests.
            </Text>
            <Button
              title="Open Profile"
              onPress={() => router.push('/profile')}
              variant="primary"
              fullWidth
              style={styles.roleGateButton}
            />
          </GlassCard>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={28} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Coach Dashboard</Text>
        <View style={styles.clientCount}>
          <Text style={styles.clientCountText}>{clients.length}</Text>
        </View>
      </View>

      {/* Tab Navigation */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabsScroll}
        contentContainerStyle={styles.tabsContainer}
      >
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Ionicons
              name={tab.icon as any}
              size={18}
              color={activeTab === tab.key ? '#FFFFFF' : colors.textTertiary}
            />
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        {loading ? (
          <ActivityIndicator size="large" color={colors.accentOrange} style={{ marginTop: 60 }} />
        ) : (
          <>
            {/* Clients Tab */}
            {activeTab === 'clients' && (
              <View>
                <Text style={styles.sectionTitle}>YOUR CLIENTS</Text>

                {clients.length === 0 ? (
                  <GlassCard style={styles.emptyCard}>
                    <Ionicons name="people-outline" size={48} color={colors.textTertiary} />
                    <Text style={styles.emptyText}>No clients yet</Text>
                    <Text style={styles.emptySubtext}>Search and add clients to start coaching</Text>
                    <Button
                      title="Add Client"
                      onPress={() => setActiveTab('search')}
                      variant="primary"
                      style={styles.emptyButton}
                    />
                  </GlassCard>
                ) : (
                  clients.map((client) => (
                    <TouchableOpacity
                      key={client.id}
                      activeOpacity={0.8}
                      onPress={() => openClientDetail(client)}
                    >
                      <GlassCard style={styles.clientCard}>
                        <View style={styles.clientRow}>
                          <View style={styles.clientAvatar}>
                            <Text style={styles.clientInitial}>
                              {client.name?.charAt(0)?.toUpperCase() || 'C'}
                            </Text>
                          </View>
                          <View style={styles.clientInfo}>
                            <Text style={styles.clientName}>{client.name}</Text>
                            <Text style={styles.clientEmail}>{client.email}</Text>
                          </View>
                          <View style={styles.clientStats}>
                            <Text style={styles.complianceValue}>{client.compliance_rate}%</Text>
                            <Text style={styles.complianceLabel}>compliance</Text>
                          </View>
                        </View>
                        <ProgressBar progress={client.compliance_rate} style={styles.clientProgress} />
                      </GlassCard>
                    </TouchableOpacity>
                  ))
                )}
              </View>
            )}

            {/* Search/Add Tab */}
            {activeTab === 'search' && (
              <View>
                <Text style={styles.sectionTitle}>ADD NEW CLIENT</Text>

                <View style={styles.searchContainer}>
                  <Ionicons name="search" size={20} color={colors.textTertiary} />
                  <TextInput
                    style={styles.searchInput}
                    placeholder="Search by name or email..."
                    placeholderTextColor={colors.textTertiary}
                    value={searchQuery}
                    onChangeText={handleSearch}
                  />
                </View>

                {searchResults.length > 0 ? (
                  searchResults.map((user) => (
                    <GlassCard key={user.id} style={styles.searchResultCard}>
                      <View style={styles.searchResultRow}>
                        <View style={styles.searchResultAvatar}>
                          <Ionicons name="person" size={20} color={colors.textTertiary} />
                        </View>
                        <View style={styles.searchResultInfo}>
                          <Text style={styles.searchResultName}>{user.name}</Text>
                          <Text style={styles.searchResultEmail}>{user.email}</Text>
                        </View>
                        <TouchableOpacity
                          style={styles.sendRequestButton}
                          onPress={() => sendRequest(user.id)}
                        >
                          <Ionicons name="add" size={20} color="#FFFFFF" />
                        </TouchableOpacity>
                      </View>
                    </GlassCard>
                  ))
                ) : searchQuery.length >= 2 ? (
                  <Text style={styles.noResultsText}>No users found</Text>
                ) : (
                  <Text style={styles.searchHint}>Enter at least 2 characters to search</Text>
                )}
              </View>
            )}

            {/* Workouts Tab */}
            {activeTab === 'workouts' && (
              <View>
                <Text style={styles.sectionTitle}>ASSIGN WORKOUT</Text>

                {clients.length === 0 ? (
                  <GlassCard style={styles.emptyCard}>
                    <Text style={styles.emptyText}>Add clients first</Text>
                  </GlassCard>
                ) : (
                  <>
                    <Text style={styles.selectLabel}>Select Client</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.clientsScroll}>
                      {clients.map((client) => (
                        <TouchableOpacity
                          key={client.id}
                          style={[
                            styles.clientChip,
                            selectedClient?.id === client.id && styles.clientChipSelected
                          ]}
                          onPress={() => setSelectedClient(client)}
                        >
                          <Text style={[
                            styles.clientChipText,
                            selectedClient?.id === client.id && styles.clientChipTextSelected
                          ]}>
                            {client.name}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>

                    {selectedClient && (
                      <GlassCard style={styles.formCard}>
                        <TextInput
                          style={styles.formInput}
                          placeholder="Workout Title"
                          placeholderTextColor={colors.textTertiary}
                          value={workoutForm.title}
                          onChangeText={(t) => setWorkoutForm({ ...workoutForm, title: t })}
                        />

                        <TextInput
                          style={[styles.formInput, styles.formTextArea]}
                          placeholder="Description"
                          placeholderTextColor={colors.textTertiary}
                          multiline
                          value={workoutForm.description}
                          onChangeText={(t) => setWorkoutForm({ ...workoutForm, description: t })}
                        />

                        <Text style={styles.formLabel}>Type</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                          {workoutTypes.map((type) => (
                            <TouchableOpacity
                              key={type}
                              style={[
                                styles.optionChip,
                                workoutForm.workout_type === type && styles.optionChipSelected
                              ]}
                              onPress={() => setWorkoutForm({ ...workoutForm, workout_type: type })}
                            >
                              <Text style={[
                                styles.optionChipText,
                                workoutForm.workout_type === type && styles.optionChipTextSelected
                              ]}>
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </ScrollView>

                        <Text style={styles.formLabel}>Difficulty</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                          {difficulties.map((diff) => (
                            <TouchableOpacity
                              key={diff}
                              style={[
                                styles.optionChip,
                                workoutForm.difficulty === diff && styles.optionChipSelected
                              ]}
                              onPress={() => setWorkoutForm({ ...workoutForm, difficulty: diff })}
                            >
                              <Text style={[
                                styles.optionChipText,
                                workoutForm.difficulty === diff && styles.optionChipTextSelected
                              ]}>
                                {diff.charAt(0).toUpperCase() + diff.slice(1)}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </ScrollView>

                        <Text style={styles.formLabel}>Duration (minutes)</Text>
                        <TextInput
                          style={styles.formInput}
                          placeholder="45"
                          placeholderTextColor={colors.textTertiary}
                          keyboardType="numeric"
                          value={workoutForm.duration}
                          onChangeText={(t) => setWorkoutForm({ ...workoutForm, duration: t })}
                        />

                        <Button
                          title="Assign Workout"
                          onPress={createWorkout}
                          fullWidth
                          style={styles.formButton}
                        />
                      </GlassCard>
                    )}
                  </>
                )}
              </View>
            )}

            {/* Meals Tab */}
            {activeTab === 'meals' && (
              <View>
                <Text style={styles.sectionTitle}>ASSIGN MEAL PLAN</Text>

                {clients.length === 0 ? (
                  <GlassCard style={styles.emptyCard}>
                    <Text style={styles.emptyText}>Add clients first</Text>
                  </GlassCard>
                ) : (
                  <>
                    <Text style={styles.selectLabel}>Select Client</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.clientsScroll}>
                      {clients.map((client) => (
                        <TouchableOpacity
                          key={client.id}
                          style={[
                            styles.clientChip,
                            selectedClient?.id === client.id && styles.clientChipSelected
                          ]}
                          onPress={() => setSelectedClient(client)}
                        >
                          <Text style={[
                            styles.clientChipText,
                            selectedClient?.id === client.id && styles.clientChipTextSelected
                          ]}>
                            {client.name}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>

                    {selectedClient && (
                      <GlassCard style={styles.formCard}>
                        <TextInput
                          style={styles.formInput}
                          placeholder="Meal Title (e.g., High Protein Lunch)"
                          placeholderTextColor={colors.textTertiary}
                          value={mealForm.title}
                          onChangeText={(t) => setMealForm({ ...mealForm, title: t })}
                        />

                        <TextInput
                          style={[styles.formInput, styles.formTextArea]}
                          placeholder="Description / Instructions"
                          placeholderTextColor={colors.textTertiary}
                          multiline
                          value={mealForm.description}
                          onChangeText={(t) => setMealForm({ ...mealForm, description: t })}
                        />

                        <Text style={styles.formLabel}>Meal Type</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                          {mealTypes.map((type) => (
                            <TouchableOpacity
                              key={type}
                              style={[
                                styles.optionChip,
                                mealForm.meal_type === type && styles.optionChipSelected
                              ]}
                              onPress={() => setMealForm({ ...mealForm, meal_type: type })}
                            >
                              <Text style={[
                                styles.optionChipText,
                                mealForm.meal_type === type && styles.optionChipTextSelected
                              ]}>
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </ScrollView>

                        <Text style={styles.formLabel}>Calories</Text>
                        <TextInput
                          style={styles.formInput}
                          placeholder="500"
                          placeholderTextColor={colors.textTertiary}
                          keyboardType="numeric"
                          value={mealForm.total_calories}
                          onChangeText={(t) => setMealForm({ ...mealForm, total_calories: t })}
                        />

                        <Button
                          title="Assign Meal Plan"
                          onPress={createMeal}
                          fullWidth
                          style={styles.formButton}
                        />
                      </GlassCard>
                    )}
                  </>
                )}
              </View>
            )}

            {/* Goals Tab */}
            {activeTab === 'goals' && (
              <View>
                <Text style={styles.sectionTitle}>SET CLIENT GOALS</Text>

                {clients.length === 0 ? (
                  <GlassCard style={styles.emptyCard}>
                    <Text style={styles.emptyText}>Add clients first</Text>
                  </GlassCard>
                ) : (
                  <>
                    <Text style={styles.selectLabel}>Select Client</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.clientsScroll}>
                      {clients.map((client) => (
                        <TouchableOpacity
                          key={client.id}
                          style={[
                            styles.clientChip,
                            selectedClient?.id === client.id && styles.clientChipSelected
                          ]}
                          onPress={() => setSelectedClient(client)}
                        >
                          <Text style={[
                            styles.clientChipText,
                            selectedClient?.id === client.id && styles.clientChipTextSelected
                          ]}>
                            {client.name}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>

                    {selectedClient && (
                      <GlassCard style={styles.formCard}>
                        <TextInput
                          style={styles.formInput}
                          placeholder="Goal Title (e.g., Lose 5kg)"
                          placeholderTextColor={colors.textTertiary}
                          value={goalForm.title}
                          onChangeText={(t) => setGoalForm({ ...goalForm, title: t })}
                        />

                        <TextInput
                          style={[styles.formInput, styles.formTextArea]}
                          placeholder="Description"
                          placeholderTextColor={colors.textTertiary}
                          multiline
                          value={goalForm.description}
                          onChangeText={(t) => setGoalForm({ ...goalForm, description: t })}
                        />

                        <Text style={styles.formLabel}>Goal Type</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                          {goalTypes.map((type) => (
                            <TouchableOpacity
                              key={type}
                              style={[
                                styles.optionChip,
                                goalForm.goal_type === type && styles.optionChipSelected
                              ]}
                              onPress={() => setGoalForm({ ...goalForm, goal_type: type })}
                            >
                              <Text style={[
                                styles.optionChipText,
                                goalForm.goal_type === type && styles.optionChipTextSelected
                              ]}>
                                {type.replace('_', ' ').charAt(0).toUpperCase() + type.replace('_', ' ').slice(1)}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </ScrollView>

                        <View style={styles.formRow}>
                          <View style={styles.formCol}>
                            <Text style={styles.formLabel}>Target Value</Text>
                            <TextInput
                              style={styles.formInput}
                              placeholder="e.g., 70"
                              placeholderTextColor={colors.textTertiary}
                              keyboardType="numeric"
                              value={goalForm.target_value}
                              onChangeText={(t) => setGoalForm({ ...goalForm, target_value: t })}
                            />
                          </View>
                          <View style={styles.formCol}>
                            <Text style={styles.formLabel}>Unit</Text>
                            <TextInput
                              style={styles.formInput}
                              placeholder="kg"
                              placeholderTextColor={colors.textTertiary}
                              value={goalForm.unit}
                              onChangeText={(t) => setGoalForm({ ...goalForm, unit: t })}
                            />
                          </View>
                        </View>

                        <Button
                          title="Set Goal"
                          onPress={createGoal}
                          fullWidth
                          style={styles.formButton}
                        />
                      </GlassCard>
                    )}
                  </>
                )}
              </View>
            )}
          </>
        )}
      </ScrollView>

      {/* Client Detail Modal */}
      <Modal
        visible={clientDetailVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setClientDetailVisible(false)}
      >
        <View style={[styles.modalContainer, { paddingTop: insets.top }]}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setClientDetailVisible(false)}>
              <Ionicons name="close" size={28} color={colors.textPrimary} />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Client Details</Text>
            <View style={{ width: 28 }} />
          </View>

          {selectedClient && (
            <ScrollView style={styles.modalContent}>
              {/* Client Info */}
              <View style={styles.clientDetailHeader}>
                <View style={styles.clientDetailAvatar}>
                  <Text style={styles.clientDetailInitial}>
                    {selectedClient.name?.charAt(0)?.toUpperCase() || 'C'}
                  </Text>
                </View>
                <Text style={styles.clientDetailName}>{selectedClient.name}</Text>
                <Text style={styles.clientDetailEmail}>{selectedClient.email}</Text>
              </View>

              {/* Stats */}
              <View style={styles.statsRow}>
                <View style={styles.statBox}>
                  <Text style={styles.statValue}>{selectedClient.total_workouts}</Text>
                  <Text style={styles.statLabel}>Workouts</Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statValue}>{selectedClient.completed_workouts}</Text>
                  <Text style={styles.statLabel}>Completed</Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statValueHighlight}>{selectedClient.compliance_rate}%</Text>
                  <Text style={styles.statLabel}>Compliance</Text>
                </View>
              </View>

              {/* Quick Actions */}
              <Text style={styles.actionsTitle}>Quick Actions</Text>
              <View style={styles.actionsGrid}>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => {
                    setClientDetailVisible(false);
                    setActiveTab('workouts');
                  }}
                >
                  <Ionicons name="barbell-outline" size={24} color={colors.accentOrange} />
                  <Text style={styles.actionText}>Assign Workout</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => {
                    setClientDetailVisible(false);
                    setActiveTab('meals');
                  }}
                >
                  <Ionicons name="restaurant-outline" size={24} color={colors.accentTeal} />
                  <Text style={styles.actionText}>Assign Meal</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={() => {
                    setClientDetailVisible(false);
                    setActiveTab('goals');
                  }}
                >
                  <Ionicons name="flag-outline" size={24} color={colors.accentBlue} />
                  <Text style={styles.actionText}>Set Goal</Text>
                </TouchableOpacity>

              </View>
            </ScrollView>
          )}
        </View>
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
  clientCount: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.accentOrange,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clientCountText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  tabsScroll: {
    maxHeight: 50,
  },
  tabsContainer: {
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 20,
    backgroundColor: colors.surface,
    gap: spacing.xs,
  },
  tabActive: {
    backgroundColor: colors.accentOrange,
  },
  tabText: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  tabTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
  },
  sectionTitle: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  emptyCard: {
    alignItems: 'center',
    paddingVertical: spacing.xxxl,
  },
  emptyText: {
    ...typography.h4,
    color: colors.textSecondary,
    marginTop: spacing.lg,
  },
  emptySubtext: {
    ...typography.caption,
    color: colors.textTertiary,
    marginTop: spacing.xs,
    textAlign: 'center',
  },
  emptyButton: {
    marginTop: spacing.xl,
  },
  roleGateContainer: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    justifyContent: 'center',
  },
  roleGateCard: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
  roleGateTitle: {
    ...typography.h4,
    color: colors.textPrimary,
    marginTop: spacing.md,
  },
  roleGateText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  roleGateButton: {
    marginTop: spacing.lg,
  },
  // Client Card
  clientCard: {
    marginBottom: spacing.md,
  },
  clientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  clientAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.accentOrange,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  clientInitial: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
  },
  clientInfo: {
    flex: 1,
  },
  clientName: {
    ...typography.body,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  clientEmail: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  clientStats: {
    alignItems: 'flex-end',
  },
  complianceValue: {
    ...typography.h4,
    color: colors.accentOrange,
  },
  complianceLabel: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  clientProgress: {
    marginTop: spacing.xs,
  },
  // Search
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.lg,
  },
  searchInput: {
    flex: 1,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
    ...typography.body,
    color: colors.textPrimary,
  },
  searchResultCard: {
    marginBottom: spacing.sm,
  },
  searchResultRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchResultAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.separator,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  searchResultInfo: {
    flex: 1,
  },
  searchResultName: {
    ...typography.body,
    color: colors.textPrimary,
  },
  searchResultEmail: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  sendRequestButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.accentOrange,
    alignItems: 'center',
    justifyContent: 'center',
  },
  noResultsText: {
    ...typography.body,
    color: colors.textTertiary,
    textAlign: 'center',
    marginTop: spacing.xl,
  },
  searchHint: {
    ...typography.caption,
    color: colors.textTertiary,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  // Form
  selectLabel: {
    ...typography.captionMedium,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  clientsScroll: {
    marginBottom: spacing.lg,
  },
  clientChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: 20,
    marginRight: spacing.sm,
  },
  clientChipSelected: {
    backgroundColor: colors.accentOrange,
  },
  clientChipText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  clientChipTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  formCard: {
    gap: spacing.md,
  },
  formInput: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...typography.body,
    color: colors.textPrimary,
  },
  formTextArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  formLabel: {
    ...typography.captionMedium,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    marginBottom: spacing.xs,
  },
  optionChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.background,
    borderRadius: 16,
    marginRight: spacing.sm,
  },
  optionChipSelected: {
    backgroundColor: colors.accentOrange,
  },
  optionChipText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  optionChipTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  formRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  formCol: {
    flex: 1,
  },
  formButton: {
    marginTop: spacing.md,
  },
  // Modal
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.separator,
  },
  modalTitle: {
    ...typography.h4,
    color: colors.textPrimary,
  },
  modalContent: {
    flex: 1,
    padding: spacing.lg,
  },
  clientDetailHeader: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  clientDetailAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.accentOrange,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  clientDetailInitial: {
    fontSize: 36,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  clientDetailName: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  clientDetailEmail: {
    ...typography.body,
    color: colors.textTertiary,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: spacing.xl,
  },
  statBox: {
    alignItems: 'center',
  },
  statValue: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  statValueHighlight: {
    ...typography.h3,
    color: colors.accentOrange,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textTertiary,
  },
  actionsTitle: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  actionButton: {
    flexBasis: '48%',
    flexGrow: 1,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    alignItems: 'center',
    gap: spacing.sm,
  },
  actionText: {
    ...typography.caption,
    color: colors.textPrimary,
    fontWeight: '600',
  },
});

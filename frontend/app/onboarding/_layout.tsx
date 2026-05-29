import { Stack } from 'expo-router';

export default function OnboardingLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }} initialRouteName="goals">
      <Stack.Screen name="goals" />
      <Stack.Screen name="experience" />
      <Stack.Screen name="sports" />
      <Stack.Screen name="profile" />
      <Stack.Screen name="schedule" />
      <Stack.Screen name="equipment" />
      <Stack.Screen name="health" />
      <Stack.Screen name="assessment" />
      <Stack.Screen name="generating" />
    </Stack>
  );
}

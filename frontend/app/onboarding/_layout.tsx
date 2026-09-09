import { Stack } from 'expo-router';

export default function OnboardingLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }} initialRouteName="goals">
      <Stack.Screen name="goals" />
      <Stack.Screen name="experience" />
      <Stack.Screen name="schedule" />
      <Stack.Screen name="health" />
      <Stack.Screen name="generating" />
    </Stack>
  );
}

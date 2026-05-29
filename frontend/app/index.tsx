import { Redirect } from 'expo-router';

export default function Index() {
  // Always redirect to welcome - the _layout.tsx will handle auth redirects
  return <Redirect href="/(auth)/welcome" />;
}

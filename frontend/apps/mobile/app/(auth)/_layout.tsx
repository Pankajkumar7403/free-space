// 📍 LOCATION: free-space/frontend/apps/mobile/app/(auth)/_layout.tsx
//
// Auth screens stack navigator.
// Redirects to (main) if user is already authenticated.

import { useEffect } from 'react';
import { Stack, useRouter } from 'expo-router';
import { useAuthStore } from '@/stores/authStore';

export default function AuthLayout() {
  const router          = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading       = useAuthStore((s) => s.isLoading);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/(main)/feed');
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: 'fade',
        contentStyle: { backgroundColor: '#0d0d14' },
      }}
    >
      <Stack.Screen name="login"           />
      <Stack.Screen name="register"        />
      <Stack.Screen name="forgot-password" />
      <Stack.Screen name="verify-email"    />
    </Stack>
  );
}

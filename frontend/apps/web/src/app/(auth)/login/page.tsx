// 📍 LOCATION: free-space/frontend/apps/web/src/app/(auth)/login/page.tsx

import type { Metadata } from 'next';
import { LoginForm } from '@/components/features/auth/LoginForm';

export const metadata: Metadata = {
  title: 'Sign In',
  description: 'Sign in to your Qommunity account.',
};

export default function LoginPage() {
  return <LoginForm />;
}

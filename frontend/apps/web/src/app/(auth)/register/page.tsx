// 📍 LOCATION: free-space/frontend/apps/web/src/app/(auth)/register/page.tsx

import type { Metadata } from 'next';
import { RegisterForm } from '@/components/features/auth/RegisterForm';

export const metadata: Metadata = {
  title: 'Create Account',
  description: 'Join Qommunity — the safe, inclusive social platform for the LGBTQ+ community.',
};

export default function RegisterPage() {
  return <RegisterForm />;
}

// 📍 LOCATION: free-space/frontend/apps/web/src/app/(auth)/forgot-password/page.tsx

import type { Metadata } from 'next';
import { ForgotPasswordForm } from '@/components/features/auth/ForgotPasswordForm';

export const metadata: Metadata = { title: 'Reset Password' };

export default function ForgotPasswordPage() {
  return <ForgotPasswordForm />;
}

// 📍 LOCATION: free-space/frontend/apps/web/src/app/(auth)/verify-email/page.tsx

import type { Metadata } from 'next';
import { VerifyEmailForm } from '@/components/features/auth/VerifyEmailForm';

export const metadata: Metadata = {
  title: 'Verify Email',
};

export default function VerifyEmailPage() {
  return <VerifyEmailForm />;
}

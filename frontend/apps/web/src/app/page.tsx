// 📍 LOCATION: free-space/frontend/apps/web/src/app/page.tsx
//
// Root "/" — middleware handles the redirect to /feed or /login
// based on auth state. This file is a fallback.

import { redirect } from 'next/navigation';

export default function RootPage() {
  redirect('/feed');
}

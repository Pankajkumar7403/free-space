// 📍 LOCATION: free-space/frontend/apps/web/src/app/layout.tsx
//
// Root layout — wraps entire app.
// Server Component: sets HTML lang, fonts, metadata.
// Providers are in src/components/providers/AppProviders.tsx (client boundary).

import type { Metadata, Viewport } from 'next';
import { Sora, DM_Sans, JetBrains_Mono } from 'next/font/google';

import { AppProviders } from '@/components/providers/AppProviders';
import './globals.css';

// ─── Fonts ────────────────────────────────────────────────────────────────────
// Display font: Sora — geometric, distinctive, inclusive feel
const displayFont = Sora({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['300', '400', '500', '600', '700', '800'],
  display: 'swap',
});

// Body font: DM Sans — readable, modern, accessible
const bodyFont = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
});

// Mono font: JetBrains Mono — for code/technical content
const monoFont = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500'],
  display: 'swap',
});

// ─── Metadata ────────────────────────────────────────────────────────────────
export const metadata: Metadata = {
  title: {
    default: 'Qommunity — Your Space, Your Pride',
    template: '%s | Qommunity',
  },
  description:
    'Qommunity is a safe, inclusive social platform built exclusively for the LGBTQ+ community.',
  keywords: ['LGBTQ+', 'queer', 'social media', 'pride', 'community', 'safe space'],
  authors: [{ name: 'Qommunity' }],
  creator: 'Qommunity',

  // Open Graph
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXT_PUBLIC_APP_URL,
    siteName: 'Qommunity',
    title: 'Qommunity — Your Space, Your Pride',
    description: 'A safe, inclusive social platform built for the LGBTQ+ community.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Qommunity — LGBTQ+ Social Platform',
      },
    ],
  },

  // Twitter / X card
  twitter: {
    card: 'summary_large_image',
    title: 'Qommunity — Your Space, Your Pride',
    description: 'A safe, inclusive social platform built for the LGBTQ+ community.',
    images: ['/og-image.png'],
  },

  // PWA manifest
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/favicon-16.png', sizes: '16x16' },
      { url: '/favicon-32.png', sizes: '32x32' },
    ],
    apple: '/apple-touch-icon.png',
  },

  // Privacy-first: no robots indexing of user profiles by default
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
    },
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,            // Allow zoom for accessibility
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)',  color: '#0d0d14' },
  ],
};

// ─── Root layout ─────────────────────────────────────────────────────────────
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning // needed for theme class toggle
      className={`${displayFont.variable} ${bodyFont.variable} ${monoFont.variable}`}
    >
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}

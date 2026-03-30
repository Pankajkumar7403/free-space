// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/layout.tsx
//
// Authenticated app shell layout.
// Wraps: /feed, /explore, /notifications, /[username], /settings, /create
// Contains: left sidebar nav, main content area, right sidebar.

import { redirect } from 'next/navigation';
import { SideNav } from '@/components/features/navigation/SideNav';
import { RightSidebar } from '@/components/features/navigation/RightSidebar';
import { MobileNav } from '@/components/features/navigation/MobileNav';

// This layout is a Server Component.
// Auth check is done in middleware.ts — layout can trust user is authenticated.
export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      {/* Pride accent strip */}
      <div className="h-0.5 pride-gradient w-full fixed top-0 left-0 z-50" aria-hidden="true" />

      <div className="flex min-h-screen pt-0.5">
        {/* Left sidebar — hidden on mobile */}
        <aside
          className="hidden md:flex flex-col w-[72px] lg:w-[244px] fixed left-0 top-0.5 bottom-0 border-r border-border bg-background z-40"
          aria-label="Main navigation"
        >
          <SideNav />
        </aside>

        {/* Main content — offset for sidebars */}
        <main
          className="flex-1 md:ml-[72px] lg:ml-[244px] xl:mr-[320px] min-h-screen"
          id="main-content"
        >
          {children}
        </main>

        {/* Right sidebar — visible only on xl screens */}
        <aside
          className="hidden xl:flex flex-col w-[320px] fixed right-0 top-0.5 bottom-0 border-l border-border bg-background overflow-y-auto scroll-hide px-6 py-8"
          aria-label="Suggested users and trending"
        >
          <RightSidebar />
        </aside>
      </div>

      {/* Mobile bottom navigation */}
      <MobileNav />
    </div>
  );
}

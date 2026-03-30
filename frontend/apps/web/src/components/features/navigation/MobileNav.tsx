// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/navigation/MobileNav.tsx
//
// Bottom tab bar for mobile viewports (< md breakpoint).

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Search, PlusSquare, Bell, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

const TABS = [
  { label: 'Home',    href: '/feed',          icon: Home },
  { label: 'Search',  href: '/explore',        icon: Search },
  { label: 'Create',  href: '/create',         icon: PlusSquare },
  { label: 'Alerts',  href: '/notifications',  icon: Bell },
  { label: 'Profile', href: null,              icon: User }, // dynamic href set below
] as const;

export function MobileNav() {
  const pathname = usePathname();
  const user     = useAuthStore((s) => s.user);

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around border-t border-border bg-background/95 backdrop-blur-sm pb-safe"
      aria-label="Mobile navigation"
    >
      {TABS.map(({ label, icon: Icon, href }) => {
        const resolvedHref = href === null ? `/${user?.username ?? 'profile'}` : href;
        const isActive = pathname === resolvedHref || (href !== null && href !== '/feed' && pathname.startsWith(resolvedHref));

        return (
          <Link
            key={label}
            href={resolvedHref}
            aria-label={label}
            aria-current={isActive ? 'page' : undefined}
            className={cn(
              'flex flex-col items-center justify-center py-3 px-4 gap-0.5 flex-1 transition-colors',
              isActive ? 'text-primary' : 'text-muted-foreground',
            )}
          >
            <Icon
              className={cn('h-6 w-6', isActive && 'stroke-[2.5]')}
              aria-hidden="true"
            />
            <span className="text-[10px] font-medium">{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

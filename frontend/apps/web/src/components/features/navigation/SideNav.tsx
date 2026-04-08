// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/navigation/SideNav.tsx

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home, Search, PlusSquare, Bell, User, Settings,
  Compass, Bookmark, LogOut, Menu,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from '@/components/ui/Toast';
import { Avatar } from '@/components/ui/Avatar';
import { Tooltip } from '@/components/ui/Tooltip';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  exact?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Home',         href: '/feed',          icon: Home,    exact: true },
  { label: 'Search',       href: '/explore',        icon: Search },
  { label: 'Explore',      href: '/explore/trending', icon: Compass },
  { label: 'Create',       href: '/create',         icon: PlusSquare },
  { label: 'Notifications',href: '/notifications',  icon: Bell },
  { label: 'Bookmarks',    href: '/bookmarks',      icon: Bookmark },
];

export function SideNav() {
  const pathname  = usePathname();
  const user      = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const { toast } = useToast();

  const handleLogout = async () => {
    try {
      await fetch('/api/users/logout', { method: 'POST' });
      clearAuth();
    } catch {
      toast({ title: 'Logout failed', description: 'Please try again.', variant: 'error' });
    }
  };

  return (
    <div className="flex flex-col h-full py-6 px-3 lg:px-4 gap-1">
      {/* Logo */}
      <Link
        href="/feed"
        className="flex items-center gap-3 px-3 py-2 mb-4 rounded-xl hover:bg-muted transition-colors group"
        aria-label="Qommunity home"
      >
        <span className="text-2xl font-display font-bold text-primary shrink-0">Q</span>
        <span className="hidden lg:block text-xl font-display font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
          ommunity
        </span>
      </Link>

      {/* Nav items */}
      <nav className="flex-1 flex flex-col gap-0.5" aria-label="Primary navigation">
        {NAV_ITEMS.map(({ label, href, icon: Icon, exact }) => {
          const isActive = exact ? pathname === href : pathname.startsWith(href);
          return (
            <Tooltip key={href} content={label} side="right" delayDuration={500}>
              <Link
                href={href}
                aria-label={label}
                aria-current={isActive ? 'page' : undefined}
                className={cn(
                  'flex items-center gap-4 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-150',
                  'hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                <Icon
                  className={cn('h-5 w-5 shrink-0', isActive && 'stroke-[2.5]')}
                  aria-hidden="true"
                />
                <span className="hidden lg:block">{label}</span>
              </Link>
            </Tooltip>
          );
        })}
      </nav>

      {/* Bottom: profile + settings + logout */}
      <div className="flex flex-col gap-0.5 mt-auto border-t border-border pt-4">
        {user && (
          <Link
            href={`/${user.username}`}
            className={cn(
              'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all hover:bg-muted',
              pathname === `/${user.username}` ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <Avatar
              src={user.avatar_url}
              alt={user.display_name}
              size="sm"
              className="shrink-0"
            />
            <div className="hidden lg:block min-w-0">
              <p className="font-semibold text-foreground truncate text-xs">{user.display_name}</p>
              <p className="text-xs text-muted-foreground truncate">@{user.username}</p>
            </div>
          </Link>
        )}

        <Tooltip content="Settings" side="right" delayDuration={500}>
          <Link
            href="/settings"
            className="flex items-center gap-4 rounded-xl px-3 py-3 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
          >
            <Settings className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span className="hidden lg:block">Settings</span>
          </Link>
        </Tooltip>

        <Tooltip content="Sign out" side="right" delayDuration={500}>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-4 rounded-xl px-3 py-3 text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-all"
            aria-label="Sign out"
          >
            <LogOut className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span className="hidden lg:block">Sign out</span>
          </button>
        </Tooltip>
      </div>
    </div>
  );
}

// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/profile/UserSearch.tsx
//
// UserSearch — debounced user search input with results list.
// Used in: explore page, followers/following modals.
// Debounce at 300ms — only fires API call when user stops typing.

'use client';

import { useState, useCallback, useRef } from 'react';
import Link from 'next/link';
import { Search, Loader2, X } from 'lucide-react';

import { useUserSearch, flattenUserPages } from '@/hooks';
import type { UserSummary } from '@qommunity/types';
import { cn } from '@/lib/utils';
import { Avatar } from '@/components/ui/Avatar';
import { Skeleton } from '@/components/ui/Skeleton';

interface UserSearchProps {
  /** Placeholder text for the search input */
  placeholder?: string;
  /** Called when a user result is clicked — useful for modals */
  onSelect?: (user: UserSummary) => void;
  className?: string;
}

export function UserSearch({
  placeholder = 'Search people...',
  onSelect,
  className,
}: UserSearchProps) {
  const [inputValue, setInputValue]     = useState('');
  const [debouncedQuery, setDebounced]  = useState('');
  const debounceTimer                   = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleChange = useCallback((value: string) => {
    setInputValue(value);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => setDebounced(value.trim()), 300);
  }, []);

  const handleClear = () => {
    setInputValue('');
    setDebounced('');
  };

  const { data, isLoading, isFetchingNextPage } = useUserSearch(debouncedQuery);
  const users = flattenUserPages(data);
  const showResults = debouncedQuery.length > 0;

  return (
    <div className={cn('relative w-full', className)}>
      {/* Input */}
      <div className="relative">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
          aria-hidden="true"
        />
        <input
          type="search"
          value={inputValue}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={placeholder}
          className={cn(
            'w-full h-10 rounded-xl border border-input bg-muted/50',
            'pl-9 pr-9 py-2 text-sm',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            'placeholder:text-muted-foreground',
            'transition-colors duration-150',
          )}
          aria-label={placeholder}
          aria-autocomplete="list"
          aria-expanded={showResults}
          role="combobox"
        />
        {inputValue && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Results */}
      {showResults && (
        <div
          className="mt-1 rounded-xl border border-border bg-background shadow-lg overflow-hidden"
          role="listbox"
          aria-label="Search results"
        >
          {isLoading ? (
            <div className="p-2 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-2 py-1.5">
                  <Skeleton className="h-9 w-9 rounded-full flex-shrink-0" />
                  <div className="space-y-1 flex-1">
                    <Skeleton className="h-3.5 w-24" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
              ))}
            </div>
          ) : users.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-muted-foreground">
              No users found for &quot;{debouncedQuery}&quot;
            </div>
          ) : (
            <ul className="py-1 max-h-64 overflow-y-auto scroll-hide">
              {users.map((user) => (
                <UserSearchResult
                  key={user.id}
                  user={user}
                  onSelect={onSelect}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Single search result row ─────────────────────────────────────────────────
function UserSearchResult({
  user,
  onSelect,
}: {
  user: UserSummary;
  onSelect?: (user: UserSummary) => void;
}) {
  const showPronouns =
    user.pronouns &&
    (user.pronouns_visibility === 'public' ||
      (user.pronouns_visibility === 'followers_only' && user.is_following));

  const content = (
    <div className="flex items-center gap-3 px-3 py-2 hover:bg-muted rounded-lg transition-colors cursor-pointer">
      <Avatar
        src={user.avatar_url}
        alt={user.display_name}
        size="sm"
        className="flex-shrink-0"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1 text-sm font-medium truncate">
          {user.display_name}
          {showPronouns && (
            <span className="text-xs text-muted-foreground font-normal">
              {user.pronouns}
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground">@{user.username}</p>
      </div>
    </div>
  );

  if (onSelect) {
    return (
      <li role="option" aria-selected={false}>
        <button className="w-full text-left" onClick={() => onSelect(user)}>
          {content}
        </button>
      </li>
    );
  }

  return (
    <li role="option" aria-selected={false}>
      <Link href={`/${user.username}`}>{content}</Link>
    </li>
  );
}
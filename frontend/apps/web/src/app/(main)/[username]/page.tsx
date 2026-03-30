// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/[username]/page.tsx
//
// Profile page — /[username]
// Server Component that fetches the initial user data on the server.
// Client components (ProfileHeader, ProfilePostsGrid) handle interactivity.
//
// SEO:
//   - generateMetadata builds per-user OG tags from server-fetched data
//   - IMPORTANT: identity fields (pronouns, orientation) are NEVER in OG tags
//     (outing prevention — they must not appear in search engine snippets)

import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ProfileHeader, ProfileHeaderSkeleton } from '@/components/features/profile/ProfileHeader';
import { ProfilePostsGrid } from '@/components/features/profile/ProfilePostsGrid';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Suspense } from 'react';
import { Grid3x3, Bookmark, Heart } from 'lucide-react';

interface ProfilePageProps {
  params: Promise<{ username: string }>;
}

// ── OG metadata — identity fields intentionally excluded ─────────────────────
export async function generateMetadata(
  { params }: ProfilePageProps,
): Promise<Metadata> {
  const { username } = await params;

  const API = process.env.API_INTERNAL_URL ?? 'http://localhost:8000/api/v1';

  try {
    const res = await fetch(`${API}/users/${username}/`, {
      next: { revalidate: 60 },
    });

    if (!res.ok) return { title: 'User not found' };

    const user = await res.json() as { display_name: string; bio?: string; avatar_url?: string };

    return {
      title: `${user.display_name} (@${username})`,
      description: user.bio ?? `View ${user.display_name}'s profile on Qommunity.`,
      openGraph: {
        title:       `${user.display_name} (@${username}) on Qommunity`,
        description: user.bio ?? `View ${user.display_name}'s profile on Qommunity.`,
        // NOTE: avatar_url deliberately omitted — identity fields must not leak
        // into OG image previews that could appear in search results or link previews
        // without the user's explicit consent.
      },
    };
  } catch {
    return { title: username };
  }
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default async function ProfilePage({ params }: ProfilePageProps) {
  const { username } = await params;

  const API = process.env.API_INTERNAL_URL ?? 'http://localhost:8000/api/v1';

  // Fetch user on the server for fast initial paint
  let user = null;
  try {
    const res = await fetch(`${API}/users/${username}/`, {
      next: { revalidate: 60 },
    });
    if (res.status === 404) notFound();
    if (res.ok) user = await res.json();
  } catch {
    // Client will retry via useProfile hook
  }

  if (!user) notFound();

  const isPrivateAndNotFollowing =
    user.account_privacy === 'private' && !user.is_following;

  return (
    <div className="max-w-[935px] mx-auto">
      {/* Profile header with all identity/stats/follow button */}
      <ProfileHeader user={user} isOwnProfile={false} />

      {/* Content tabs */}
      <div className="border-t border-border mt-2">
        <Tabs defaultValue="posts">
          <TabsList className="w-full justify-center">
            <TabsTrigger value="posts" className="flex-1 max-w-[200px] gap-2">
              <Grid3x3 className="h-4 w-4" aria-hidden="true" />
              Posts
            </TabsTrigger>
            <TabsTrigger value="liked" className="flex-1 max-w-[200px] gap-2">
              <Heart className="h-4 w-4" aria-hidden="true" />
              Liked
            </TabsTrigger>
            <TabsTrigger value="saved" className="flex-1 max-w-[200px] gap-2">
              <Bookmark className="h-4 w-4" aria-hidden="true" />
              Saved
            </TabsTrigger>
          </TabsList>

          <TabsContent value="posts">
            <ProfilePostsGrid
              username={username}
              isPrivate={isPrivateAndNotFollowing}
            />
          </TabsContent>

          <TabsContent value="liked">
            <div className="py-16 text-center text-sm text-muted-foreground">
              Liked posts — coming soon
            </div>
          </TabsContent>

          <TabsContent value="saved">
            <div className="py-16 text-center text-sm text-muted-foreground">
              Saved posts — only visible to you
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
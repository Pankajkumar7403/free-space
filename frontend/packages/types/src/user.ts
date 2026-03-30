// 📍 LOCATION: free-space/frontend/packages/types/src/user.ts
//
// User types — mirror backend apps/users/models.py exactly
// Field names match snake_case API responses.

// ─── LGBTQ+ identity enums — mirror backend choices ──────────────────────────
export const PRONOUNS = [
    'he/him',
    'she/her',
    'they/them',
    'he/they',
    'she/they',
    'ze/zir',
    'xe/xem',
    'prefer_not_to_say',
    'other',
  ] as const;
  export type Pronouns = (typeof PRONOUNS)[number];
  
  export const GENDER_IDENTITY = [
    'man',
    'woman',
    'non_binary',
    'genderqueer',
    'genderfluid',
    'agender',
    'two_spirit',
    'prefer_not_to_say',
    'other',
  ] as const;
  export type GenderIdentity = (typeof GENDER_IDENTITY)[number];
  
  export const SEXUAL_ORIENTATION = [
    'gay',
    'lesbian',
    'bisexual',
    'pansexual',
    'queer',
    'asexual',
    'aromantic',
    'straight',
    'prefer_not_to_say',
    'other',
  ] as const;
  export type SexualOrientation = (typeof SEXUAL_ORIENTATION)[number];
  
  // ─── Visibility — who can see a field ────────────────────────────────────────
  export const VISIBILITY = ['public', 'followers_only', 'private'] as const;
  export type Visibility = (typeof VISIBILITY)[number];
  
  export const ACCOUNT_PRIVACY = ['public', 'followers_only', 'close_friends', 'private'] as const;
  export type AccountPrivacy = (typeof ACCOUNT_PRIVACY)[number];
  
  // ─── Core User interface ──────────────────────────────────────────────────────
  export interface User {
    id: string;                            // UUID
    username: string;
    email: string;
    display_name: string;
    bio: string | null;
    avatar_url: string | null;
    website: string | null;
  
    // LGBTQ+ identity fields — visibility controlled per-field
    pronouns: Pronouns | null;
    pronouns_visibility: Visibility;
    gender_identity: GenderIdentity | null;
    gender_identity_visibility: Visibility;
    sexual_orientation: SexualOrientation | null;
    sexual_orientation_visibility: Visibility;
  
    // Privacy & safety
    account_privacy: AccountPrivacy;
    is_verified: boolean;
    is_active: boolean;
  
    // Social stats (denormalised for display)
    followers_count: number;
    following_count: number;
    posts_count: number;
  
    // Relationship state (present when fetching another user's profile)
    is_following?: boolean;
    is_followed_by?: boolean;
    is_blocked?: boolean;
    is_muted?: boolean;
    follow_request_sent?: boolean;
  
    // Timestamps
    created_at: string; // ISO 8601 UTC
    updated_at: string;
  }
  
  // ─── Authenticated user (own profile — includes private fields) ────────────────
  export type AuthenticatedUser = User & {
    email: string;
    email_verified: boolean;
    notification_preferences: NotificationPreferences;
  };
  
  // ─── Notification preferences ────────────────────────────────────────────────
  export interface NotificationPreferences {
    likes_in_app: boolean;
    likes_push: boolean;
    comments_in_app: boolean;
    comments_push: boolean;
    follows_in_app: boolean;
    follows_push: boolean;
    mentions_in_app: boolean;
    mentions_push: boolean;
  }
  
  // ─── Slim user (used in lists, PostCard avatar, comment author) ───────────────
  export interface UserSummary {
    id: string;
    username: string;
    display_name: string;
    avatar_url: string | null;
    pronouns: Pronouns | null;
    pronouns_visibility: Visibility;
    is_verified: boolean;
    is_following?: boolean;
  }
  
  // ─── Follow model ─────────────────────────────────────────────────────────────
  export interface Follow {
    id: string;
    follower: UserSummary;
    following: UserSummary;
    created_at: string;
  }
  
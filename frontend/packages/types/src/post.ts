// 📍 LOCATION: free-space/frontend/packages/types/src/post.ts
//
// Post & Media types — mirror backend apps/posts/models.py + apps/media/models.py

import type { UserSummary } from './user';

// ─── Post visibility — mirror backend choices ─────────────────────────────────
export const POST_VISIBILITY = ['public', 'followers_only', 'close_friends', 'private'] as const;
export type PostVisibility = (typeof POST_VISIBILITY)[number];

// ─── Media types ──────────────────────────────────────────────────────────────
export const MEDIA_TYPE = ['image', 'video'] as const;
export type MediaType = (typeof MEDIA_TYPE)[number];

export const MEDIA_STATUS = ['pending', 'processing', 'ready', 'failed'] as const;
export type MediaStatus = (typeof MEDIA_STATUS)[number];

export interface Media {
  id: string;
  file_type: MediaType;
  original_url: string;
  processed_url: string | null;  // null while processing
  thumbnail_url: string | null;  // null while processing
  status: MediaStatus;
  width: number | null;
  height: number | null;
  duration_seconds: number | null; // video only
  created_at: string;
}

// ─── Hashtag ──────────────────────────────────────────────────────────────────
export interface Hashtag {
  id: string;
  name: string;           // without the # prefix
  post_count: number;
  trending_score: number; // Redis sorted set score
}

// ─── Core Post ────────────────────────────────────────────────────────────────
export interface Post {
  id: string;
  author: UserSummary;

  content: string | null;       // text content (nullable for media-only posts)
  media: Media[];               // ordered list, max 10
  hashtags: Hashtag[];

  visibility: PostVisibility;
  is_anonymous: boolean;        // anonymous posting feature
  allow_comments: boolean;
  location: string | null;

  // Engagement counts (from Redis — denormalised for display)
  likes_count: number;
  comments_count: number;

  // Viewer state (present when authenticated)
  is_liked: boolean;
  is_bookmarked: boolean;

  created_at: string;
  updated_at: string;
  edited_at: string | null;     // null if never edited
}

// ─── Create/update DTOs (what the frontend sends to the API) ─────────────────
export interface CreatePostPayload {
  content?: string;
  media_ids?: string[];         // IDs from upload endpoint
  hashtags?: string[];          // without # prefix
  visibility: PostVisibility;
  is_anonymous?: boolean;
  allow_comments?: boolean;
  location?: string;
}

export interface UpdatePostPayload {
  content?: string;
  visibility?: PostVisibility;
  allow_comments?: boolean;
}

// ─── S3 Upload flow ───────────────────────────────────────────────────────────
export interface PresignedUploadUrl {
  media_id: string;    // created media record ID
  upload_url: string;  // presigned S3 URL
  fields: Record<string, string>; // extra fields for S3 POST
  cdn_url: string;     // final CDN URL after upload completes
  expires_in: number;  // seconds until presigned URL expires
}

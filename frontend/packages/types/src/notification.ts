// 📍 LOCATION: free-space/frontend/packages/types/src/notification.ts
//
// Notification types — mirror backend apps/notifications/models.py

import type { UserSummary } from './user';

export const NOTIFICATION_VERB = [
  'liked_post',
  'liked_comment',
  'commented_on_post',
  'replied_to_comment',
  'followed_you',
  'follow_request',
  'follow_request_accepted',
  'mentioned_in_post',
  'mentioned_in_comment',
  'post_approved',             // for close_friends posts
] as const;
export type NotificationVerb = (typeof NOTIFICATION_VERB)[number];

export interface Notification {
  id: string;
  recipient_id: string;
  actor: UserSummary;          // who triggered the notification
  verb: NotificationVerb;
  target_id: string | null;    // post ID, comment ID, etc.
  target_type: 'post' | 'comment' | 'user' | null;
  is_read: boolean;
  created_at: string;
}

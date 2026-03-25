// 📍 LOCATION: free-space/frontend/packages/types/src/comment.ts
//
// Comment types — mirror backend apps/comments/models.py

import type { UserSummary } from './user';

export interface Comment {
  id: string;
  post_id: string;
  author: UserSummary;

  content: string;
  parent_id: string | null;   // null = top-level comment
  depth: number;              // 0 = top-level, max 3 levels
  is_pinned: boolean;         // pinned by post author

  likes_count: number;
  replies_count: number;
  is_liked: boolean;          // viewer's like state

  is_hidden: boolean;         // hidden by author/post owner
  is_deleted: boolean;        // soft deleted — shows "deleted comment" placeholder

  created_at: string;
  updated_at: string;
}

export interface CreateCommentPayload {
  post_id: string;
  content: string;
  parent_id?: string;         // for replies
}

export interface UpdateCommentPayload {
  content: string;
}

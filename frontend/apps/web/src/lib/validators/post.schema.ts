// 📍 LOCATION: free-space/frontend/packages/validators/src/post.schema.ts
//
// Post & comment Zod schemas — mirror backend apps/posts/validators.py

import { z } from 'zod';
import { POST_VISIBILITY } from '@qommunity/types';

// ─── Create post ──────────────────────────────────────────────────────────────
export const createPostSchema = z
  .object({
    content: z.string().max(2200, 'Post content must be 2200 characters or fewer').optional(),
    media_ids: z.array(z.string().uuid()).max(10, 'Maximum 10 media items per post').optional(),
    hashtags: z
      .array(
        z
          .string()
          .min(1)
          .max(50)
          .regex(/^[a-zA-Z0-9_]+$/, 'Hashtags can only contain letters, numbers, and underscores'),
      )
      .max(30, 'Maximum 30 hashtags per post')
      .optional(),
    visibility: z.enum(POST_VISIBILITY),
    is_anonymous: z.boolean().default(false),
    allow_comments: z.boolean().default(true),
    location: z.string().max(100, 'Location name too long').optional(),
  })
  .refine((data) => data.content || (data.media_ids && data.media_ids.length > 0), {
    message: 'Post must have content or media',
    path: ['content'],
  });

export type CreatePostFormValues = z.infer<typeof createPostSchema>;

// ─── Update post ──────────────────────────────────────────────────────────────
export const updatePostSchema = z.object({
  content: z.string().max(2200).optional(),
  visibility: z.enum(POST_VISIBILITY).optional(),
  allow_comments: z.boolean().optional(),
});

export type UpdatePostFormValues = z.infer<typeof updatePostSchema>;

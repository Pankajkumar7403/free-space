// 📍 LOCATION: free-space/frontend/packages/validators/src/comment.schema.ts

import { z } from 'zod';

export const createCommentSchema = z.object({
  content: z
    .string()
    .min(1, 'Comment cannot be empty')
    .max(500, 'Comment must be 500 characters or fewer'),
  parent_id: z.string().uuid().optional(),
});

export type CreateCommentFormValues = z.infer<typeof createCommentSchema>;

export const updateCommentSchema = z.object({
  content: z
    .string()
    .min(1, 'Comment cannot be empty')
    .max(500, 'Comment must be 500 characters or fewer'),
});

export type UpdateCommentFormValues = z.infer<typeof updateCommentSchema>;

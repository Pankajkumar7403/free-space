// 📍 LOCATION: free-space/frontend/packages/validators/src/profile.schema.ts

import { z } from 'zod';
import { PRONOUNS, GENDER_IDENTITY, SEXUAL_ORIENTATION, VISIBILITY, ACCOUNT_PRIVACY } from '@qommunity/types';

export const updateProfileSchema = z.object({
  display_name: z.string().min(1).max(60).optional(),
  bio: z.string().max(500, 'Bio must be 500 characters or fewer').optional(),
  website: z.string().url('Please enter a valid URL').optional().or(z.literal('')),

  // LGBTQ+ identity — each field has its own visibility toggle
  pronouns: z.enum(PRONOUNS).optional().nullable(),
  pronouns_visibility: z.enum(VISIBILITY).optional(),
  gender_identity: z.enum(GENDER_IDENTITY).optional().nullable(),
  gender_identity_visibility: z.enum(VISIBILITY).optional(),
  sexual_orientation: z.enum(SEXUAL_ORIENTATION).optional().nullable(),
  sexual_orientation_visibility: z.enum(VISIBILITY).optional(),

  account_privacy: z.enum(ACCOUNT_PRIVACY).optional(),
});

export type UpdateProfileFormValues = z.infer<typeof updateProfileSchema>;

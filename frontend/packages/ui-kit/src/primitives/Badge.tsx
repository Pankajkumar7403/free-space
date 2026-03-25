// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/primitives/Badge.tsx
//
// Badge — used for: verified checkmark, pronoun display, post visibility labels,
// notification unread count, trending tags.

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../lib/cn';

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors select-none',
  {
    variants: {
      variant: {
        default:     'border-transparent bg-primary text-primary-foreground',
        secondary:   'border-transparent bg-secondary/10 text-secondary',
        outline:     'border-border text-foreground bg-transparent',
        muted:       'border-transparent bg-muted text-muted-foreground',
        success:     'border-transparent bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
        warning:     'border-transparent bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
        destructive: 'border-transparent bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        // Pride gradient badge — used on community spaces
        pride:       'border-transparent text-white pride-gradient',
        // Visibility badges for posts
        public:       'border-transparent bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
        followers:    'border-transparent bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
        close_friends:'border-transparent bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
        private:      'border-transparent bg-gray-100 text-gray-600 dark:bg-gray-900/30 dark:text-gray-400',
        anonymous:    'border-transparent bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      },
      size: {
        sm:  'px-2 py-px text-[10px]',
        md:  'px-2.5 py-0.5 text-xs',
        lg:  'px-3 py-1 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)} {...props} />
  );
}

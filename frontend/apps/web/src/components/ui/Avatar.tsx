// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/Avatar.tsx
//
// Avatar with pride-gradient ring option and fallback initials.

import * as React from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';

const SIZE_MAP = {
  xs:  { px: 24,  className: 'h-6 w-6 text-[9px]'  },
  sm:  { px: 32,  className: 'h-8 w-8 text-xs'      },
  md:  { px: 40,  className: 'h-10 w-10 text-sm'    },
  lg:  { px: 56,  className: 'h-14 w-14 text-base'  },
  xl:  { px: 80,  className: 'h-20 w-20 text-xl'    },
  '2xl':{ px: 112, className: 'h-28 w-28 text-2xl'  },
} as const;

export type AvatarSize = keyof typeof SIZE_MAP;

interface AvatarProps {
  src?: string | null;
  alt: string;
  size?: AvatarSize;
  prideRing?: boolean;  // shows pride gradient ring (for own profile)
  className?: string;
}

export function Avatar({ src, alt, size = 'md', prideRing = false, className }: AvatarProps) {
  const { px, className: sizeClass } = SIZE_MAP[size];
  const initials = getInitials(alt);

  return (
    <div
      className={cn('relative shrink-0', className)}
      style={prideRing ? { padding: 2 } : undefined}
    >
      {prideRing && (
        <div
          className="absolute inset-0 rounded-full pride-gradient"
          aria-hidden="true"
          style={{ padding: 2 }}
        />
      )}

      <div
        className={cn(
          'relative rounded-full overflow-hidden bg-muted ring-2 ring-background',
          sizeClass,
          prideRing && 'ring-[3px]',
        )}
      >
        {src ? (
          <Image
            src={src}
            alt={alt}
            width={px}
            height={px}
            className="object-cover w-full h-full"
            sizes={`${px}px`}
            // Blur placeholder while loading
            placeholder="blur"
            blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2U1ZTdlYiIvPjwvc3ZnPg=="
          />
        ) : (
          // Fallback: initials on gradient background
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/20 to-accent/20">
            <span className="font-semibold text-primary select-none">{initials}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return (parts[0]?.[0] ?? '').toUpperCase();
  return ((parts[0]?.[0] ?? '') + (parts[parts.length - 1]?.[0] ?? '')).toUpperCase();
}

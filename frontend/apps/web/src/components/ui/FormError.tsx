// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/FormError.tsx

import * as React from 'react';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FormErrorProps extends React.HTMLAttributes<HTMLDivElement> {}

export function FormError({ className, children, ...props }: FormErrorProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/5 px-3 py-2.5 text-sm text-destructive',
        className,
      )}
      {...props}
    >
      <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

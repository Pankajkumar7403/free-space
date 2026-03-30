// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/Separator.tsx

import { cn } from '@/lib/utils';

interface SeparatorProps {
  label?: string;
  className?: string;
}

export function Separator({ label, className }: SeparatorProps) {
  if (!label) {
    return <hr className={cn('border-border', className)} />;
  }

  return (
    <div className={cn('relative flex items-center gap-3', className)}>
      <div className="h-px flex-1 bg-border" aria-hidden="true" />
      <span className="text-xs text-muted-foreground whitespace-nowrap select-none">
        {label}
      </span>
      <div className="h-px flex-1 bg-border" aria-hidden="true" />
    </div>
  );
}

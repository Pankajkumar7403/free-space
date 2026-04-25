// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/primitives/Switch.tsx
//
// Switch — used in notification preferences, privacy settings, identity field visibility.

'use client';

import * as React from 'react';
import * as SwitchPrimitive from '@radix-ui/react-switch';
import { cn } from '@/lib/utils';

interface SwitchProps extends React.ComponentPropsWithoutRef<typeof SwitchPrimitive.Root> {
  /** Label shown beside the switch */
  label?: string;
  description?: string;
}

const Switch = React.forwardRef<React.ElementRef<typeof SwitchPrimitive.Root>, SwitchProps>(
  ({ className, label, description, id, ...props }, ref) => {
    const switchId = id ?? React.useId();

    if (label) {
      return (
        <div className="flex items-center justify-between gap-4 py-1">
          <div className="space-y-0.5">
            <label
              htmlFor={switchId}
              className="text-sm font-medium leading-none cursor-pointer select-none"
            >
              {label}
            </label>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          <SwitchRoot ref={ref} id={switchId} className={className} {...props} />
        </div>
      );
    }

    return <SwitchRoot ref={ref} id={switchId} className={className} {...props} />;
  },
);
Switch.displayName = 'Switch';

const SwitchRoot = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitive.Root
    ref={ref}
    className={cn(
      'peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent',
      'transition-colors duration-200',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
      'disabled:cursor-not-allowed disabled:opacity-50',
      'data-[state=checked]:bg-primary data-[state=unchecked]:bg-input',
      className,
    )}
    {...props}
  >
    <SwitchPrimitive.Thumb
      className={cn(
        'pointer-events-none block h-5 w-5 rounded-full bg-background shadow-md ring-0',
        'transition-transform duration-200',
        'data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0',
      )}
    />
  </SwitchPrimitive.Root>
));
SwitchRoot.displayName = SwitchPrimitive.Root.displayName;

export { Switch };

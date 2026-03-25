// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/Toast.tsx
//
// Lightweight toast system built on Radix UI Toast primitive.
// Usage: const { toast } = useToast();
//        toast({ title: "Post shared!", variant: "success" });

'use client';

import * as React from 'react';
import * as ToastPrimitive from '@radix-ui/react-toast';
import { cva, type VariantProps } from 'class-variance-authority';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────
export type ToastVariant = 'default' | 'success' | 'error' | 'info';

export interface ToastOptions {
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastItem extends ToastOptions {
  id: string;
}

// ─── Context ──────────────────────────────────────────────────────────────────
const ToastContext = React.createContext<{
  toast: (options: ToastOptions) => void;
} | null>(null);

// ─── Variants ────────────────────────────────────────────────────────────────
const toastVariants = cva(
  'group pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-xl border p-4 pr-8 shadow-lg transition-all',
  {
    variants: {
      variant: {
        default: 'border-border bg-background text-foreground',
        success: 'border-green-200 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950 dark:text-green-100',
        error:   'border-red-200 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100',
        info:    'border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-100',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

const ICONS: Record<ToastVariant, React.ReactNode> = {
  default: null,
  success: <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" aria-hidden="true" />,
  error:   <AlertCircle  className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5"   aria-hidden="true" />,
  info:    <Info         className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5"  aria-hidden="true" />,
};

// ─── Provider ─────────────────────────────────────────────────────────────────
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([]);

  const toast = React.useCallback((options: ToastOptions) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev, { ...options, id }]);
  }, []);

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}

        {toasts.map((t) => (
          <ToastPrimitive.Root
            key={t.id}
            duration={t.duration ?? 4000}
            onOpenChange={(open) => { if (!open) dismiss(t.id); }}
            className={cn(
              toastVariants({ variant: t.variant ?? 'default' }),
              // Animate in from right
              'data-[state=open]:animate-slide-up data-[state=closed]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full',
            )}
            aria-label={t.title}
          >
            {/* Icon */}
            {ICONS[t.variant ?? 'default']}

            {/* Content */}
            <div className="flex-1 space-y-0.5">
              <ToastPrimitive.Title className="text-sm font-semibold leading-tight">
                {t.title}
              </ToastPrimitive.Title>
              {t.description && (
                <ToastPrimitive.Description className="text-xs opacity-80">
                  {t.description}
                </ToastPrimitive.Description>
              )}
            </div>

            {/* Close button */}
            <ToastPrimitive.Close
              className="absolute right-2 top-2 rounded-md p-1 text-current opacity-40 hover:opacity-100 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Close notification"
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" />
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        ))}

        {/* Viewport — where toasts render in the DOM */}
        <ToastPrimitive.Viewport
          className={cn(
            'fixed bottom-0 right-0 z-[var(--z-toast)] flex max-h-screen w-full flex-col-reverse gap-2 p-4',
            'sm:max-w-[420px]',
          )}
        />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');
  return ctx;
}

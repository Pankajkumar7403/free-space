// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/FullScreenLoader.tsx
//
// Shown while AuthProvider restores the session on mount.
// Keeps brand presence — not a blank white screen.

export function FullScreenLoader() {
    return (
      <div
        className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background gap-4"
        role="status"
        aria-label="Loading Qommunity"
      >
        {/* Animated pride ring */}
        <div className="relative h-14 w-14">
          <div className="absolute inset-0 rounded-full pride-gradient animate-spin [animation-duration:2s]" />
          <div className="absolute inset-[3px] rounded-full bg-background flex items-center justify-center">
            <span className="text-xl font-display font-bold text-primary select-none" aria-hidden="true">
              Q
            </span>
          </div>
        </div>
        <p className="text-sm text-muted-foreground animate-pulse">Loading your space…</p>
      </div>
    );
  }
  
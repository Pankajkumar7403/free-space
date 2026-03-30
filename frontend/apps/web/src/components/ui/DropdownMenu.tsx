// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/DropdownMenu.tsx
//
// Re-exports the DropdownMenu from ui-kit.
// Having a local re-export lets us add web-specific overrides later.

'use client';

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
} from '@qommunity/ui-kit/primitives';
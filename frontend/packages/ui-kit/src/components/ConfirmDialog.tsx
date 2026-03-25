// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/components/ConfirmDialog.tsx
//
// ConfirmDialog — used for: delete post, unfollow user, block user, leave community.
// Prevents accidental destructive actions.

'use client';

import * as React from 'react';
import { Loader2 } from 'lucide-react';
import {
  Modal, ModalContent, ModalHeader, ModalFooter,
  ModalTitle, ModalDescription, ModalClose,
} from '../primitives/Modal';
import { cn } from '../lib/cn';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Makes the confirm button destructive (red) */
  destructive?: boolean;
  onConfirm: () => void | Promise<void>;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel  = 'Cancel',
  destructive  = false,
  onConfirm,
}: ConfirmDialogProps) {
  const [isLoading, setIsLoading] = React.useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent size="sm" hideClose>
        <ModalHeader>
          <ModalTitle>{title}</ModalTitle>
          <ModalDescription>{description}</ModalDescription>
        </ModalHeader>

        <ModalFooter>
          <ModalClose asChild>
            <button
              className="rounded-lg px-4 py-2 text-sm font-medium bg-muted hover:bg-muted/80 transition-colors"
              disabled={isLoading}
            >
              {cancelLabel}
            </button>
          </ModalClose>

          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-all',
              'disabled:opacity-50 disabled:pointer-events-none',
              destructive
                ? 'bg-destructive hover:bg-destructive/90'
                : 'bg-primary hover:bg-primary/90',
            )}
          >
            {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />}
            {confirmLabel}
          </button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

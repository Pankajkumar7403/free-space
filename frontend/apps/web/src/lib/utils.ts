// 📍 LOCATION: free-space/frontend/apps/web/src/lib/utils.ts
//
// Utility functions shared across all web components.

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * cn — merge Tailwind classes safely.
 * Resolves conflicts (e.g. "p-4 p-6" → "p-6") and
 * conditionally applies classes via clsx.
 *
 * Usage: cn("base-class", isActive && "active-class", { "conditional": bool })
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number for display (e.g. 1234 → "1.2K", 1_200_000 → "1.2M")
 * Used for likes counts, follower counts, etc.
 */
export function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 10_000)    return `${Math.floor(n / 1000)}K`;
  if (n >= 1_000)     return `${(n / 1000).toFixed(1)}K`;
  return n.toString();
}

/**
 * Format an ISO timestamp to a relative time string.
 * e.g. "2 hours ago", "3 days ago", "just now"
 */
export function formatRelativeTime(isoString: string): string {
  const date   = new Date(isoString);
  const now    = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffS  = Math.floor(diffMs / 1000);
  const diffM  = Math.floor(diffS / 60);
  const diffH  = Math.floor(diffM / 60);
  const diffD  = Math.floor(diffH / 24);
  const diffW  = Math.floor(diffD / 7);

  if (diffS < 60)  return 'just now';
  if (diffM < 60)  return `${diffM}m`;
  if (diffH < 24)  return `${diffH}h`;
  if (diffD < 7)   return `${diffD}d`;
  if (diffW < 52)  return `${diffW}w`;
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

/**
 * Truncate text with ellipsis at word boundary.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).replace(/\s+\S*$/, '') + '…';
}

/**
 * Generate a blur data URL placeholder for images while loading.
 * Uses a tiny SVG as the blur placeholder — no external dependency.
 */
export function getBlurDataUrl(width = 8, height = 8): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <filter id="blur"><feGaussianBlur stdDeviation="1"/></filter>
    <rect width="100%" height="100%" fill="#e5e7eb" filter="url(#blur)"/>
  </svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`;
}

/**
 * Extract hashtags from post content string.
 * Returns array of tag names without the # prefix.
 */
export function extractHashtags(content: string): string[] {
  const matches = content.match(/#([a-zA-Z0-9_]+)/g) ?? [];
  return [...new Set(matches.map((tag) => tag.slice(1).toLowerCase()))];
}

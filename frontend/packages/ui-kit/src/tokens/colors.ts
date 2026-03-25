// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/tokens/colors.ts
//
// Design tokens — single source of truth for all colours.
// Web uses CSS variables (defined in globals.css).
// Mobile uses these direct values (NativeWind maps CSS vars differently).

export const colors = {
    // ─── Brand palette ──────────────────────────────────────────────────────────
    brand: {
      50:  '#f5f3ff',
      100: '#ede9fe',
      200: '#ddd6fe',
      300: '#c4b5fd',
      400: '#a78bfa',
      500: '#8b5cf6',
      600: '#7c3aed',  // primary
      700: '#6d28d9',
      800: '#5b21b6',
      900: '#4c1d95',
      950: '#2e1065',
    },
  
    // ─── Pride flag colours ──────────────────────────────────────────────────────
    pride: {
      red:    '#E40303',
      orange: '#FF8C00',
      yellow: '#FFED00',
      green:  '#008026',
      blue:   '#004DFF',
      violet: '#750787',
      // Trans flag
      transPink:  '#F5A9B8',
      transBlue:  '#55CDFC',
      transWhite: '#FFFFFF',
      // Non-binary flag
      nbYellow:   '#FCF434',
      nbWhite:    '#FFFFFF',
      nbPurple:   '#9C59D1',
      nbBlack:    '#2C2C2C',
    },
  
    // ─── Neutrals ────────────────────────────────────────────────────────────────
    gray: {
      50:  '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
      950: '#030712',
    },
  
    // ─── Semantic ────────────────────────────────────────────────────────────────
    success: { light: '#dcfce7', DEFAULT: '#16a34a', dark: '#14532d' },
    warning: { light: '#fef9c3', DEFAULT: '#ca8a04', dark: '#713f12' },
    error:   { light: '#fee2e2', DEFAULT: '#dc2626', dark: '#7f1d1d' },
    info:    { light: '#dbeafe', DEFAULT: '#2563eb', dark: '#1e3a8a' },
  
    // ─── Light mode surface palette ─────────────────────────────────────────────
    light: {
      background:   '#ffffff',
      surface:      '#ffffff',
      surfaceRaised:'#f9fafb',
      border:       '#e5e7eb',
      text:         '#111827',
      textMuted:    '#6b7280',
      textSubtle:   '#9ca3af',
    },
  
    // ─── Dark mode surface palette ───────────────────────────────────────────────
    dark: {
      background:   '#0d0d14',
      surface:      '#16162a',
      surfaceRaised:'#1e1e38',
      border:       '#2a2a4a',
      text:         '#f1f0ff',
      textMuted:    '#7b7a9d',
      textSubtle:   '#4a4a6a',
    },
  } as const;
  
  export type ColorToken = typeof colors;
  
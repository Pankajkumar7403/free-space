// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/tokens/spacing.ts

export const spacing = {
    0:    0,
    0.5:  2,
    1:    4,
    1.5:  6,
    2:    8,
    2.5:  10,
    3:    12,
    3.5:  14,
    4:    16,
    5:    20,
    6:    24,
    7:    28,
    8:    32,
    9:    36,
    10:   40,
    11:   44,
    12:   48,
    14:   56,
    16:   64,
    20:   80,
    24:   96,
    28:   112,
    32:   128,
  } as const;
  
  export const borderRadius = {
    none:  0,
    sm:    4,
    md:    6,
    lg:    8,
    xl:    12,
    '2xl': 16,
    '3xl': 20,
    full:  9999,
  } as const;
  
  export const shadows = {
    sm:  { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2,  elevation: 1 },
    md:  { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.08, shadowRadius: 8,  elevation: 4 },
    lg:  { shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.12, shadowRadius: 16, elevation: 8 },
    xl:  { shadowColor: '#000', shadowOffset: { width: 0, height: 16 }, shadowOpacity: 0.16, shadowRadius: 24, elevation: 16 },
    // Brand shadow — used on primary buttons
    brand: { shadowColor: '#7c3aed', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 12, elevation: 8 },
  } as const;
  
  export const typography = {
    // Font families (must match app.json/fonts loaded in _layout.tsx)
    fontFamily: {
      display: 'Sora_700Bold',
      displayMedium: 'Sora_600SemiBold',
      body: 'DMSans_400Regular',
      bodyMedium: 'DMSans_500Medium',
    },
    // Font sizes (px on web, sp on mobile — same scale)
    fontSize: {
      '2xs': 10,
      xs:    12,
      sm:    13,
      base:  15,
      md:    16,
      lg:    18,
      xl:    20,
      '2xl': 22,
      '3xl': 28,
      '4xl': 36,
      '5xl': 48,
    },
    // Line heights
    lineHeight: {
      tight:  1.25,
      snug:   1.375,
      normal: 1.5,
      relaxed:1.625,
    },
    // Letter spacing
    letterSpacing: {
      tight:  -0.5,
      normal: 0,
      wide:   0.5,
      wider:  1,
    },
  } as const;
  
  export const zIndex = {
    base:     0,
    raised:   10,
    dropdown: 20,
    sticky:   30,
    overlay:  40,
    modal:    50,
    toast:    60,
    tooltip:  70,
  } as const;
  
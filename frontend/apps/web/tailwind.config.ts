// 📍 LOCATION: free-space/frontend/apps/web/tailwind.config.ts
import type { Config } from 'tailwindcss';
import baseConfig from '@qommunity/config/tailwind';

const config: Config = {
  // Extend the shared base config
  ...baseConfig,
  // Web-specific content paths
  content: [
    './src/**/*.{ts,tsx}',
    '../../packages/ui-kit/src/**/*.{ts,tsx}',
  ],
};

export default config;

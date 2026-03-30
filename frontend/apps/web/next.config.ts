// 📍 LOCATION: free-space/frontend/apps/web/next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Turbopack (stable in Next 15)
  experimental: {
    // Enable React Server Components optimisations
    optimizePackageImports: ['lucide-react', 'framer-motion', '@radix-ui/react-icons'],
  },

  images: {
    remotePatterns: [
      // AWS S3 / MinIO (local dev)
      {
        protocol: 'https',
        hostname: '*.s3.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: '*.s3.*.amazonaws.com',
      },
      // CloudFront CDN
      {
        protocol: 'https',
        hostname: '*.cloudfront.net',
      },
      // Cloudflare CDN
      {
        protocol: 'https',
        hostname: '*.cloudflare.com',
      },
      // Local MinIO for development
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '9000',
      },
    ],
    // Serve modern formats — avif first, then webp
    formats: ['image/avif', 'image/webp'],
    // Match backend's max image size
    deviceSizes: [375, 640, 750, 828, 1080, 1200, 1920],
    imageSizes: [48, 64, 96, 128, 256],
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(self)',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // unsafe-eval needed for Next.js dev
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https: http://localhost:9000",
              "connect-src 'self' https: ws: wss: http://localhost:*",
              "media-src 'self' https: blob:",
              "frame-ancestors 'none'",
            ].join('; '),
          },
        ],
      },
    ];
  },

  // Redirect bare domain to www in production (optional)
  async redirects() {
    return [];
  },

  // Bundle only what ships to the browser
  transpilePackages: [
    '@qommunity/types',
    '@qommunity/api-client',
    '@qommunity/validators',
    '@qommunity/ui-kit',
    '@qommunity/hooks',
  ],
};

export default nextConfig;

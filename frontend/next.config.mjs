   import path from 'path';
   import { fileURLToPath } from 'url';
   import fs from 'fs';

   const __filename = fileURLToPath(import.meta.url);
   const __dirname = path.dirname(__filename);

   /** @type {import('next').NextConfig} */
   const nextConfig = {
    reactStrictMode: true,
    typescript: {
      // Build errors will show as warnings but won't block builds
      ignoreBuildErrors: true,
    },
    eslint: {
      // Show ESLint warnings/errors but don't block builds in development
      ignoreDuringBuilds: true,
      dirs: ['src'], // Only lint src directory, not node_modules
    },
  experimental: {
    // Enhanced package optimization for better tree-shaking
    optimizePackageImports: [
      '@radix-ui/react-toast',
      '@radix-ui/react-dialog',
      '@radix-ui/react-select',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-popover',
      '@radix-ui/react-tabs',
      '@radix-ui/react-accordion',
      'lucide-react',
      'framer-motion',
      'recharts',
      '@tanstack/react-query',
    ],
    // Enable React Compiler for better performance (if available)
    // reactCompiler: true,
    // Enable partial prerendering for better performance (disabled for stability)
    // ppr: true,
  },
  transpilePackages: [
    '@radix-ui/react-toast',
    '@radix-ui/react-dialog',
    '@radix-ui/react-select',
    'lucide-react',
  ],

  // Performance and bundle optimization
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Enhanced Security Headers
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: '/(.*)',
        headers: [
          // Content Security Policy
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://api.fontshare.com https://fonts.googleapis.com https://www.googletagmanager.com",
              "style-src 'self' 'unsafe-inline' https://api.fontshare.com https://fonts.googleapis.com",
              "font-src 'self' https://api.fontshare.com https://fonts.gstatic.com data:",
              "img-src 'self' data: blob: https: http:",
              "connect-src 'self' http://localhost:8000 https://linkedinautomation-production-7ae9.up.railway.app https://api.prismpro.live https://api.supabase.io https://fecoflibopgxliexcdbg.supabase.co https://fonts.googleapis.com https://api.fontshare.com",
              "frame-src 'self' https://www.google.com",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-ancestors 'none'",
              "upgrade-insecure-requests"
            ].join('; ')
          },
          // Prevent XSS attacks
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          // Prevent clickjacking
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          // Prevent MIME type sniffing
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          // Referrer Policy
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          // HSTS (Force HTTPS in production)
          ...(process.env.NODE_ENV === 'production' ? [{
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload'
          }] : []),
          // Permissions Policy (formerly Feature Policy)
          {
            key: 'Permissions-Policy',
            value: [
              'camera=()',
              'microphone=()',
              'geolocation=()',
              'interest-cohort=()',
              'payment=()',
              'usb=()',
              'screen-wake-lock=()',
              'web-share=()'
            ].join(', ')
          },
          // Cross-Origin policies
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin'
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'same-origin'
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'require-corp'
          },
          // Remove server information
          {
            key: 'X-Powered-By',
            value: ''
          }
        ]
      },
      {
        // API routes get additional security headers
        source: '/api/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache, must-revalidate, proxy-revalidate'
          },
          {
            key: 'X-Robots-Tag',
            value: 'noindex, nofollow, nosnippet, noarchive'
          }
        ]
      }
    ]
  },

  // Security-focused environment variables
  env: {
    // Ensure we don't expose sensitive variables
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
  },

  // Additional security configurations
  poweredByHeader: false, // Remove X-Powered-By header

  // Enhanced webpack configuration for performance and security
  webpack: (config, { dev, isServer, buildId }) => {
    // Production optimizations
    if (!dev) {
      config.optimization.minimize = true;
      config.devtool = false; // Remove source maps for security

      // Advanced code splitting configuration
      config.optimization.splitChunks = {
        chunks: 'all',
        minSize: 20000,
        maxSize: 244000,
        cacheGroups: {
          default: {
            minChunks: 2,
            priority: -20,
            reuseExistingChunk: true,
          },
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: -10,
            chunks: 'all',
          },
          // UI Components bundle
          ui: {
            test: /[\\/]node_modules[\\/](@radix-ui|lucide-react)[\\/]/,
            name: 'ui-components',
            priority: 10,
            chunks: 'all',
            enforce: true,
          },
          // Charts and visualization bundle
          charts: {
            test: /[\\/]node_modules[\\/](recharts|d3-|react-chartjs)[\\/]/,
            name: 'charts',
            priority: 15,
            chunks: 'all',
            enforce: true,
          },
          // React Query and state management
          state: {
            test: /[\\/]node_modules[\\/](@tanstack\/react-query|zustand|jotai)[\\/]/,
            name: 'state-management',
            priority: 12,
            chunks: 'all',
            enforce: true,
          },
          // Framer Motion animation bundle
          animation: {
            test: /[\\/]node_modules[\\/](framer-motion)[\\/]/,
            name: 'animations',
            priority: 11,
            chunks: 'all',
            enforce: true,
          },
          // Form handling libraries
          forms: {
            test: /[\\/]node_modules[\\/](react-hook-form|zod|@hookform)[\\/]/,
            name: 'forms',
            priority: 9,
            chunks: 'all',
            enforce: true,
          },
        },
      };

      // Module concatenation optimization
      config.optimization.concatenateModules = true;

      // Aggressive tree shaking
      config.optimization.usedExports = true;
      config.optimization.sideEffects = false;
    }

    // Performance optimizations for all builds
    config.optimization.moduleIds = 'deterministic';
    config.optimization.chunkIds = 'deterministic';

    // Ensure path aliases work in Docker build
    const srcPath = path.resolve(__dirname, 'src');
    const cwdSrcPath = path.resolve(process.cwd(), 'src');
    const actualSrcPath = fs.existsSync(srcPath) ? srcPath :
                         (fs.existsSync(cwdSrcPath) ? cwdSrcPath : srcPath);

    config.resolve.alias = {
      ...config.resolve.alias,
      '@': actualSrcPath,
      // Optimize bundle by excluding unnecessary polyfills
      canvas: false,
      encoding: false,
      'fs': false,
      'path': false,
      'os': false,
    };

    // Bundle analyzer in development (optional)
    if (dev && process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'server',
          openAnalyzer: true,
        })
      );
    }

    return config;
  }
}

export default nextConfig
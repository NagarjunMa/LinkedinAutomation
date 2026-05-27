/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'cobertura'],
      include: [
        'src/hooks/use-tailor-apply.ts',
        'src/hooks/use-export-pdf.ts',
        'src/hooks/use-resume.ts',
        'src/hooks/use-jd-analyze.ts',
        'src/hooks/use-credits.ts',
        'src/app/lib/api/resume-v2.ts',
        'src/app/lib/api/jd.ts',
        'src/app/lib/api/exports.ts',
        'src/app/lib/api/credits.ts',
        'src/components/tailor/**',
        'src/components/jd/diff-view.tsx',
        'src/components/resume/bullet-highlight.tsx',
        'src/components/resume/rewrite-modal.tsx',
        'src/components/resume/resume-upload-dropzone.tsx',
        'src/components/resume/ats-tab.tsx',
      ],
      thresholds: {
        lines: 80,
        functions: 72,
        branches: 75,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

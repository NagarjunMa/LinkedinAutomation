// Design constants for the new Resume Evaluation UI
// Based on Google AI Studio generated design

export const COLORS = {
  // Primary brand colors
  primary: '#3b3b3b',        // Main text and elements
  background: '#f0eff2',     // Main background
  accent: '#ff7a30',         // Orange accent color

  // Surface colors
  surface: '#ffffff',        // Card backgrounds
  surfaceSecondary: '#e5e4e9', // Secondary surface (resume viewer bg)

  // Text colors
  textPrimary: '#3b3b3b',
  textSecondary: '#3b3b3b/70',
  textMuted: '#3b3b3b/40',
  textXsMuted: '#3b3b3b/30',

  // Status colors
  success: '#10b981',        // Emerald
  warning: '#f59e0b',        // Amber
  error: '#ef4444',          // Red

  // Interactive states
  hover: '#000000',          // Black for hover states
  border: '#3b3b3b/5',       // Subtle borders
  borderHover: '#3b3b3b/20', // Hover borders
} as const;

export const TYPOGRAPHY = {
  // Font families
  fontFamily: {
    inter: ['Inter', 'sans-serif'],
    mono: ['ui-monospace', 'SFMono-Regular', 'Monaco', 'Consolas', 'monospace'],
  },

  // Font sizes (in rem and classes)
  fontSize: {
    // Micro text (9px - 10px)
    micro: 'text-[9px]',
    microSm: 'text-[10px]',

    // Small text (11px - 12px)
    xs: 'text-[11px]',
    sm: 'text-xs',

    // Base sizes
    base: 'text-sm',
    lg: 'text-lg',
    xl: 'text-xl',
    '2xl': 'text-2xl',
    '3xl': 'text-3xl',
    '4xl': 'text-4xl',
  },

  // Font weights
  fontWeight: {
    medium: 'font-medium',
    bold: 'font-bold',
    black: 'font-black', // Key for the ultra-bold aesthetic
  },

  // Letter spacing
  tracking: {
    tight: 'tracking-tight',
    tighter: 'tracking-tighter',
    wide: 'tracking-wide',
    wider: 'tracking-wider',
    widest: 'tracking-widest',
    ultraWide: 'tracking-[0.2em]', // Custom ultra-wide spacing
  },
} as const;

export const SPACING = {
  // Border radius (rounded corners)
  borderRadius: {
    sm: 'rounded-lg',
    md: 'rounded-2xl',
    lg: 'rounded-3xl',
    xl: 'rounded-[40px]',  // Custom large radius
  },

  // Padding scales
  padding: {
    card: 'p-10',      // Large card padding
    cardSm: 'p-6',     // Medium card padding
    section: 'p-8',    // Section padding
    button: 'px-8 py-4', // Button padding
  },

  // Gap scales
  gap: {
    xs: 'gap-2',
    sm: 'gap-3',
    md: 'gap-6',
    lg: 'gap-8',
    xl: 'gap-12',
  },
} as const;

export const ANIMATIONS = {
  // Transition classes
  transition: {
    default: 'transition-all',
    colors: 'transition-colors',
    transform: 'transition-transform',
    shadow: 'transition-shadow',
  },

  // Duration
  duration: {
    fast: 'duration-200',
    medium: 'duration-300',
    slow: 'duration-500',
    slower: 'duration-700',
    slowest: 'duration-1000',
  },

  // Transform effects
  transform: {
    scale: 'hover:scale-110',
    scaleDown: 'active:scale-95',
    rotate: 'group-hover:rotate-6',
    rotateReverse: 'group-hover:-rotate-6',
    translateX: 'group-hover:translate-x-1',
  },

  // Backdrop effects
  backdrop: {
    blur: 'backdrop-blur-md',
    blurSm: 'backdrop-blur-sm',
  },
} as const;

export const COMPONENTS = {
  // Button variants
  button: {
    primary: `
      px-8 py-4 bg-[#3b3b3b] text-white rounded-2xl
      font-black text-xs uppercase tracking-widest
      shadow-xl hover:bg-black transition-all active:scale-95
    `,
    secondary: `
      px-8 py-4 bg-white/80 backdrop-blur-md
      border border-white shadow-sm rounded-2xl
      font-black text-xs uppercase tracking-widest text-[#3b3b3b]
      hover:bg-white transition-all
    `,
  },

  // Card variants
  card: {
    primary: `
      bg-white p-10 rounded-[40px] border border-[#3b3b3b]/5
      shadow-sm hover:shadow-xl transition-all
    `,
    surface: `
      bg-[#f0eff2]/50 border border-[#3b3b3b]/5 rounded-3xl
    `,
    interactive: `
      bg-white border border-[#3b3b3b]/5 rounded-[40px]
      group cursor-pointer hover:border-[#3b3b3b]/20
      transition-all shadow-sm hover:shadow-xl
    `,
  },

  // Badge variants
  badge: {
    status: `
      px-3 py-1 text-[10px] font-black uppercase tracking-widest
      rounded-full border
    `,
    active: `
      px-3 py-1 bg-orange-50 text-orange-600 text-[10px]
      font-black uppercase tracking-widest rounded-full
      border border-orange-100
    `,
  },
} as const;

import { ResumeEvaluation } from '@/app/lib/api/types';

// Mock data structure for development
// Mock data structure for development
// Mock data structure for development
// MOCK_FEEDBACK removed

// File type definitions for resume uploads
export const RESUME_FILE_TYPES = {
  PDF: 'application/pdf',
  DOC: 'application/msword',
  DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
} as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// SVG noise pattern for grain effect
export const NOISE_PATTERN = `data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E`;
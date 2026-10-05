/** @type {import('tailwindcss').Config} */
import animate from 'tailwindcss-animate';

export default {
    darkMode: ['class'],
    content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
  	extend: {
  		fontFamily: {
  			// ── Prism Pro brand typography ──────────────────────────────────────
  			// Display / headings: Fraunces (premium editorial serif)
  			'display': ['var(--font-fraunces)', 'Georgia', 'serif'],
  			'serif': ['var(--font-fraunces)', 'Georgia', 'serif'],
  			// Body / UI: Humane (editorial minimalist sans) — primary body + nav
  			'sans': ['var(--font-geist-sans)', 'var(--font-ibm-plex-sans)', 'Inter', 'system-ui', 'sans-serif'],
  			'body': ['var(--font-geist-sans)', 'var(--font-ibm-plex-sans)', 'Inter', 'system-ui', 'sans-serif'],
  			// Humane direct reference
  			'humane': ['var(--font-humane)', 'Inter', 'sans-serif'],
  			// ── Legacy font families kept for backward compat ────────────────────
  			'absans': ['Absans', 'sans-serif'],
  			'urbanist': ['var(--font-urbanist)', 'Urbanist', 'sans-serif'],
  			'clash': ['Clash Display', 'sans-serif'],
  			'heading': ['var(--font-fraunces)', 'Clash Display', 'Georgia', 'serif'],
  			'title': ['var(--font-fraunces)', 'Clash Display', 'Georgia', 'serif'],
  			'stardom': ['Stardom', 'sans-serif'],
  			'app-title': ['Stardom', 'var(--font-fraunces)', 'serif'],
  			'adieu': ['Adieu', 'sans-serif'],
  			'inter': ['Inter', 'var(--font-ibm-plex-sans)', 'sans-serif'],
  			'ibm': ['var(--font-ibm-plex-sans)', 'Inter', 'sans-serif'],
  			'mono': ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Monaco', 'Consolas', 'monospace'],
  		},
		colors: {
			// ── Prism Pro earth-tone design tokens ──────────────────────────────
			// These map to CSS vars in globals.css; all shadcn components pick them up.
			'terracotta': {
				DEFAULT: 'hsl(18 52% 48%)',
				light:   'hsl(18 52% 62%)',
				dark:    'hsl(18 52% 34%)',
			},
			'sage': {
				DEFAULT: 'hsl(140 14% 58%)',
				light:   'hsl(140 14% 72%)',
				dark:    'hsl(140 14% 40%)',
			},
			'sand': {
				50:  'hsl(40 20% 97%)',
				100: 'hsl(40 15% 93%)',
				200: 'hsl(38 12% 86%)',
				300: 'hsl(36 10% 76%)',
			},
			'charcoal': {
				DEFAULT: 'hsl(30 8% 18%)',
				soft:    'hsl(30 6% 28%)',
				muted:   'hsl(30 5% 40%)',
			},
			'gold': {
				DEFAULT: 'hsl(42 45% 65%)',
				dark:    'hsl(42 45% 45%)',
			},
			'rust': {
				DEFAULT: 'hsl(10 62% 38%)',
				light:   'hsl(10 62% 52%)',
			},

			// ── Unified app-wide theme colors ───────────────────────────────────
			'app-bg': 'var(--app-bg)',
			'app-text': 'var(--app-text)',
			'app-card': 'var(--app-card)',
			'app-card-border': 'var(--app-card-border)',
			'app-muted': 'var(--app-muted)',
			'app-accent': 'var(--app-accent)',

			// ── Resume evaluation specific colors (unchanged) ────────────────────
			'resume-primary': '#3b3b3b',
			'resume-bg': '#f0eff2',
			'resume-surface': '#ffffff',
			'resume-surface-secondary': '#e5e4e9',
			'resume-accent': '#ff7a30',
			'resume-text': {
				DEFAULT: '#3b3b3b',
				secondary: 'rgb(59 59 59 / 0.7)',
				muted: 'rgb(59 59 59 / 0.4)',
				'xs-muted': 'rgb(59 59 59 / 0.3)',
			},
			'resume-border': {
				DEFAULT: 'rgb(59 59 59 / 0.05)',
				hover: 'rgb(59 59 59 / 0.2)',
			},

			// ── shadcn/ui semantic colors — map to CSS vars ──────────────────────
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		backgroundImage: {
  			// ── Earth-tone gradients ─────────────────────────────────────────────
  			'gradient-warm':       'linear-gradient(135deg, hsl(18 52% 48%) 0%, hsl(42 45% 65%) 100%)',
  			'gradient-terracotta': 'linear-gradient(135deg, hsl(18 52% 42%), hsl(18 52% 58%))',
  			'gradient-sage':       'linear-gradient(135deg, hsl(140 14% 50%), hsl(140 14% 65%))',
  			'gradient-glow':       'radial-gradient(circle at 30% 40%, hsl(18 52% 48% / 0.15) 0%, transparent 60%)',
  			'gradient-card':       'linear-gradient(to bottom right, hsl(18 52% 48% / 0.08), hsl(42 45% 65% / 0.04))',
  			// Legacy orange gradients kept for backward compat
  			'gradient-orange':     'linear-gradient(135deg, hsl(18 52% 48%), hsl(18 52% 58%))',
  			'gradient-gold':       'linear-gradient(135deg, hsl(42 45% 58%), hsl(42 45% 70%))',
  		},
  		boxShadow: {
            // Preserve the v3 small-shadow scale used by shared controls.
            sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  			// ── Earth-tone glow shadows ──────────────────────────────────────────
  			'glow-terracotta': '0 0 20px hsl(18 52% 48% / 0.28)',
  			'glow-gold':       '0 0 20px hsl(42 45% 60% / 0.28)',
  			'card-elevated':   '0 8px 32px hsl(30 8% 10% / 0.18)',
  			'card-subtle':     '0 4px 16px hsl(30 8% 10% / 0.10)',
  			// Legacy aliases
  			'glow-orange':     '0 0 20px hsl(18 52% 48% / 0.28)',
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)',
  			'3xl': '1.875rem',
  			'4xl': '2.5rem',
  		},
  		letterSpacing: {
  			'ultra-wide': '0.2em',
  			// ── Editorial tracking utilities ─────────────────────────────────────
  			'editorial': '0.18em',    // eyebrow / metadata
  			'nav': '0.15em',          // nav links / wordmark
  			'cta': '0.12em',          // CTA buttons
  			'scroll': '0.2em',        // SCROLL DOWN indicator
  			'tight-display': '-0.02em', // display H1 hero
  			'tight-h2': '-0.01em',    // display H2 section
  			'tight-h3': '-0.005em',   // H3 sub-headlines
  		},
  		fontSize: {
  			'micro': '9px',
  			'micro-sm': '10px',
  			'11px': '11px',
  		},
        blur: { sm: '4px' },
        backdropBlur: {
            sm: '4px',
  			'xs': '2px',
  		}
  	}
  },
  plugins: [animate],
}

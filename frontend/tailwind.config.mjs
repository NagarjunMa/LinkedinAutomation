/** @type {import('tailwindcss').Config} */
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
  			'absans': ['Absans', 'sans-serif'], // Primary application font
  			'sans': ['Absans', 'sans-serif'], // Default sans-serif
  			'urbanist': ['var(--font-urbanist)', 'Urbanist', 'sans-serif'],
  			'clash': ['Clash Display', 'sans-serif'],
  			'heading': ['Clash Display', 'sans-serif'],
  			'title': ['Clash Display', 'sans-serif'], // All page titles
  			'stardom': ['Stardom', 'sans-serif'],
  			'app-title': ['Stardom', 'sans-serif'], // JOBFLOW PRO application name
  			'adieu': ['Adieu', 'sans-serif'], // Backup for Adieu if files available
  			// Resume evaluation specific fonts
  			'inter': ['Inter', 'sans-serif'], // For resume evaluation UI
  			'mono': ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Monaco', 'Consolas', 'monospace'],
            'serif': ['Playfair Display', 'serif'],
  		},
		colors: {
			// Unified application theme colors
			'app-bg': 'var(--app-bg)',
			'app-text': 'var(--app-text)',
			'app-card': 'var(--app-card)',
			'app-card-border': 'var(--app-card-border)',
			'app-muted': 'var(--app-muted)',
			'app-accent': 'var(--app-accent)',

			// Resume evaluation specific colors
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

			// Keep existing accent colors for special purposes
			accent: {
				600: '#e64a19', // Darker orange
				500: '#ff5722', // Primary orange
				400: '#ff6b3d', // Lighter orange
				300: '#ff7f57', // Lightest orange
			},
  			// Keep existing shadcn colors for compatibility
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
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
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
  			'gradient-warm': 'linear-gradient(135deg, #ff5722 0%, #f59e0b 100%)',
  			'gradient-glow': 'radial-gradient(circle at 30% 40%, rgba(255, 87, 34, 0.15) 0%, transparent 60%)',
  			'gradient-card': 'linear-gradient(to bottom right, rgba(255, 87, 34, 0.1), rgba(245, 158, 11, 0.05))',
  			'gradient-orange': 'linear-gradient(135deg, #ff5722, #ff6b3d)',
  			'gradient-gold': 'linear-gradient(135deg, #f59e0b, #fbbf24)',
  		},
  		boxShadow: {
  			'glow-orange': '0 0 20px rgba(255, 87, 34, 0.3)',
  			'glow-gold': '0 0 20px rgba(245, 158, 11, 0.3)',
  			'card-elevated': '0 8px 32px rgba(0, 0, 0, 0.4)',
  			'card-subtle': '0 4px 16px rgba(0, 0, 0, 0.2)',
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)',
  			// Resume evaluation specific radius
  			'3xl': '1.875rem', // 30px
  			'4xl': '2.5rem',   // 40px - for cards
  		},
  		letterSpacing: {
  			'ultra-wide': '0.2em', // For ultra-wide tracking
  		},
  		fontSize: {
  			'micro': '9px',
  			'micro-sm': '10px',
  			'11px': '11px',
  		},
  		backdropBlur: {
  			'xs': '2px',
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
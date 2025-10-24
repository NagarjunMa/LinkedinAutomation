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
  		},
		colors: {
			// Premium theme colors - responsive to theme using CSS variables
			primary: {
				950: 'var(--primary-950)',
				900: 'var(--primary-900)',
				800: 'var(--primary-800)',
				700: 'var(--primary-700)',
				600: 'var(--primary-600)',
				500: 'var(--primary-500)',
				400: 'var(--primary-400)',
			},
			// Orange accent colors - same for both themes
			accent: {
				600: '#e64a19', // Darker orange
				500: '#ff5722', // Primary orange
				400: '#ff6b3d', // Lighter orange
				300: '#ff7f57', // Lightest orange
			},
			// Gold/yellow highlights - same for both themes
			gold: {
				600: '#d97706', // Deep gold
				500: '#f59e0b', // Standard gold
				400: '#fbbf24', // Bright gold
				300: '#fcd34d', // Light gold
			},
			// Neutral text colors - responsive to theme using CSS variables
			cream: {
				50: 'var(--cream-50)',
				100: 'var(--cream-100)',
				200: 'var(--cream-200)',
				300: 'var(--cream-300)',
				400: 'var(--cream-400)',
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
  			sm: 'calc(var(--radius) - 4px)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
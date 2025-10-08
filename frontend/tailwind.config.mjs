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
  			'anton': ['var(--font-anton)', 'Anton', 'sans-serif'],
  			'asset': ['var(--font-asset)', 'Asap', 'sans-serif'],
  		},
  		colors: {
  			// Premium dark theme colors
  			primary: {
  				950: '#0f0e0d', // Deepest background
  				900: '#1a1412', // Main background
  				800: '#2d2520', // Card backgrounds
  				700: '#3d342d', // Elevated cards
  				600: '#4d443d', // Borders and dividers
  				500: '#5d544d', // Hover states
  				400: '#6d645d', // Active states
  			},
  			// Orange accent colors
  			accent: {
  				600: '#e64a19', // Darker orange
  				500: '#ff5722', // Primary orange
  				400: '#ff6b3d', // Lighter orange
  				300: '#ff7f57', // Lightest orange
  			},
  			// Gold/yellow highlights
  			gold: {
  				600: '#d97706', // Deep gold
  				500: '#f59e0b', // Standard gold
  				400: '#fbbf24', // Bright gold
  				300: '#fcd34d', // Light gold
  			},
  			// Neutral text colors
  			cream: {
  				50: '#fafaf9',  // Primary text
  				100: '#f5f5f4', // Secondary text
  				200: '#e7e5e4', // Tertiary text
  				300: '#d6d3d1', // Muted text
  				400: '#a8a29e', // Disabled text
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
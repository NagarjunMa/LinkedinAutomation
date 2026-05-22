import type { Metadata } from "next"
import localFont from "next/font/local"
import { Urbanist, Inter, Playfair_Display, JetBrains_Mono, Fraunces, IBM_Plex_Sans } from "next/font/google"
import { GeistSans } from "geist/font/sans"
import "./globals.css"
import { Providers } from "@/components/ui/providers"
import { AuthProvider } from "@/contexts/auth-context"
import { ThemeProvider } from "@/contexts/theme-context"
import ErrorBoundary, { PageErrorFallback } from "@/components/error-boundary"

// ── Humane variable typeface — editorial display / UI font ─────────────────
// Loaded via next/font/local for optimal performance (no FOUT/FOIT).
// Variable font file covers wght 100–900 from a single file.
const humane = localFont({
  src: "../../public/fonts/HUMANE Typeface/Variable-TT/Humane-VF.ttf",
  variable: "--font-humane",
  display: "swap",
  weight: "100 900",
})

const urbanist = Urbanist({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-urbanist"
})

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter"
})

const playfair = Playfair_Display({
  subsets: ["latin"],
  style: ['normal', 'italic'],
  variable: "--font-playfair"
})

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono"
})

// ── Prism Pro brand typography ─────────────────────────────────────────────
// Display / headings: Fraunces (premium editorial optical-size serif)
const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "900"],
  style: ["normal", "italic"],
  variable: "--font-fraunces",
  display: "swap",
})

// Body / UI: IBM Plex Sans (professional, legible, neutral)
const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-ibm-plex-sans",
  display: "swap",
})

export const metadata: Metadata = {
  title: {
    default: "Prism Pro — Recruiter-Grade Resume Prep",
    template: "%s | Prism Pro"
  },
  description: "Recruiter-grade resume tailoring and JD matching for experienced engineers and product professionals. Used by SWEs, Data Scientists, and PMs targeting roles in the US and India.",
  keywords: [
    "resume tailoring",
    "ATS optimization",
    "JD matching",
    "resume scoring",
    "recruiter resume review",
    "software engineer resume",
    "data scientist resume",
    "product manager resume",
    "resume builder USA India",
    "ATS resume checker"
  ],
  authors: [{ name: "Prism Pro Team" }],
  creator: "Prism Pro",
  publisher: "Prism Pro",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://prismpro.live'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://prismpro.live',
    title: 'Prism Pro — Recruiter-Grade Resume Prep',
    description: 'Recruiter-grade resume tailoring and JD matching for experienced engineers and product professionals. Used by SWEs, Data Scientists, and PMs targeting roles in the US and India.',
    siteName: 'Prism Pro',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Prism Pro — Recruiter-Grade Resume Prep',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Prism Pro — Recruiter-Grade Resume Prep',
    description: 'Bullet-level resume critique, JD-driven tailoring, and country-aware PDF export for experienced engineers and PMs.',
    images: ['/og-image.jpg'],
    creator: '@prismpro',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Clash Display Font - All Titles */}
        <link rel="preconnect" href="https://api.fontshare.com" />
        <link href="https://api.fontshare.com/v2/css?f[]=clash-display@200,300,400,500,600,700&display=swap" rel="stylesheet" />

        {/* Stardom Font - Application Name "PRISM PRO" */}
        <link href="https://api.fontshare.com/v2/css?f[]=stardom@400,500,600,700&display=swap" rel="stylesheet" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              "name": "Prism Pro",
              "description": "Recruiter-grade resume tailoring platform. Professionals use Prism Pro to evaluate and tailor their resumes to job descriptions, prepare for ATS systems, and export polished, country-aware PDF resumes.",
              "url": "https://prismpro.live",
              "applicationCategory": "BusinessApplication",
              "operatingSystem": "Web Browser",
              "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "description": "Freemium — 20 free credits per month; top-up credits available"
              },
              "author": {
                "@type": "Organization",
                "name": "Prism Pro"
              }
            })
          }}
        />
      </head>
      <body className={`${GeistSans.variable} ${humane.variable} ${fraunces.variable} ${ibmPlexSans.variable} ${urbanist.variable} ${inter.variable} ${playfair.variable} ${jetbrains.variable}`}>
        <ErrorBoundary fallback={PageErrorFallback}>
          <ThemeProvider>
            <AuthProvider>
              <Providers>
                {children}
              </Providers>
            </AuthProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
} 

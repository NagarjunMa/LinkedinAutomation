import type { Metadata } from "next"
import localFont from "next/font/local"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import "./globals.css"
import { Providers } from "@/components/ui/providers"
import { AuthProvider } from "@/contexts/auth-context"
import { ThemeProvider } from "@/contexts/theme-context"
import ErrorBoundary, { PageErrorFallback } from "@/components/error-boundary"
import { getConfiguredAppOrigin } from "@/lib/url"

// ── Humane variable typeface — editorial display / UI font ─────────────────
// Loaded via next/font/local for optimal performance (no FOUT/FOIT).
// Variable font file covers wght 100–900 from a single file.
const humane = localFont({
  src: "../../public/fonts/HUMANE Typeface/Variable-TT/Humane-VF.ttf",
  variable: "--font-humane",
  display: "swap",
  weight: "100 900",
})

const appOrigin = getConfiguredAppOrigin()

export const metadata: Metadata = {
  title: {
    default: "Prism Pro — Truthful Resume Tailoring for Technical Professionals",
    template: "%s | Prism Pro"
  },
  description: "Tailor your resume to real job descriptions without generic AI bullets or unsupported claims. Prism Pro helps engineers, data scientists, and PMs review, edit, and export ATS-aware resumes.",
  keywords: [
    "resume tailoring for software engineers",
    "job description resume tailoring",
    "ATS resume checker",
    "AI resume review",
    "truthful resume rewriting",
    "software engineer resume review",
    "data scientist resume review",
    "product manager resume tailoring",
    "resume diff editor",
    "US India resume templates"
  ],
  authors: [{ name: "Prism Pro Team" }],
  creator: "Prism Pro",
  publisher: "Prism Pro",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(appOrigin),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: appOrigin,
    title: 'Prism Pro — Truthful Resume Tailoring for Technical Professionals',
    description: 'Upload your resume, paste a job description, review every suggested change, and export an ATS-aware PDF without unsupported claims.',
    siteName: 'Prism Pro',
  },
  twitter: {
    card: 'summary',
    title: 'Prism Pro — Truthful Resume Tailoring',
    description: 'JD-specific resume edits with diff review, truth checks, ATS-aware export, and saved company-specific versions.',
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
              "description": "Truthful resume tailoring workspace for technical professionals. Prism Pro helps users evaluate resumes, tailor them to job descriptions, review every AI-suggested change, avoid unsupported claims, and export ATS-aware PDFs.",
              "url": appOrigin,
              "applicationCategory": "BusinessApplication",
              "operatingSystem": "Web Browser",
              "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "description": "Freemium — 90 free credits per month during launch"
              },
              "author": {
                "@type": "Organization",
                "name": "Prism Pro"
              }
            })
          }}
        />
      </head>
      <body className={`${GeistSans.variable} ${GeistMono.variable} ${humane.variable}`}>
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

import type { Metadata } from "next"
import { Urbanist, Inter, Playfair_Display, JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { Providers } from "@/components/ui/providers"
import { AuthProvider } from "@/contexts/auth-context"
import { ThemeProvider } from "@/contexts/theme-context"
import ErrorBoundary, { PageErrorFallback } from "@/components/error-boundary"


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

export const metadata: Metadata = {
  title: {
    default: "Prism Pro - AI-Powered LinkedIn Job Automation for Students",
    template: "%s | Prism Pro"
  },
  description: "Streamline your job search with Prism Pro. Extract jobs from URLs, track applications, and get smart job matching. Perfect for students and recent graduates.",
  keywords: [
    "LinkedIn automation",
    "job search automation",
    "AI job matching",
    "student job search",
    "LinkedIn job extraction",
    "application tracking",
    "career automation",
    "job hunting tools",
    "graduate job search",
    "LinkedIn tools"
  ],
  authors: [{ name: "Prism Pro Team" }],
  creator: "Prism Pro",
  publisher: "Prism Pro",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://jobflowpro.com'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://jobflowpro.com',
    title: 'Prism Pro - AI-Powered LinkedIn Job Automation',
    description: 'Streamline your job search with Prism Pro. Perfect for students and recent graduates.',
    siteName: 'Prism Pro',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Prism Pro - AI-Powered Job Search Automation',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Prism Pro - AI-Powered LinkedIn Job Automation',
    description: 'Streamline your job search with Prism Pro.',
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
              "description": "AI-powered LinkedIn job search automation for students and recent graduates",
              "url": "https://prismpro.live",
              "applicationCategory": "BusinessApplication",
              "operatingSystem": "Web Browser",
              "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "description": "Free for students"
              },
              "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.9",
                "ratingCount": "1000"
              },
              "author": {
                "@type": "Organization",
                "name": "Prism Pro"
              }
            })
          }}
        />
      </head>
      <body className={`${urbanist.className} ${urbanist.variable} ${inter.variable} ${playfair.variable} ${jetbrains.variable}`}>
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

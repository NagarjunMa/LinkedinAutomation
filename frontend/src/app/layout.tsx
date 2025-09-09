import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "@/components/ui/providers"
import { AuthProvider } from "@/contexts/auth-context"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: {
    default: "JobFlow Pro - AI-Powered LinkedIn Job Automation for Students",
    template: "%s | JobFlow Pro"
  },
  description: "Streamline your job search with AI-powered LinkedIn automation. Extract jobs from URLs, track applications, and get smart job matching. Perfect for students and recent graduates.",
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
  authors: [{ name: "JobFlow Pro Team" }],
  creator: "JobFlow Pro",
  publisher: "JobFlow Pro",
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
    title: 'JobFlow Pro - AI-Powered LinkedIn Job Automation',
    description: 'Streamline your job search with AI-powered LinkedIn automation. Perfect for students and recent graduates.',
    siteName: 'JobFlow Pro',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'JobFlow Pro - AI-Powered Job Search Automation',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'JobFlow Pro - AI-Powered LinkedIn Job Automation',
    description: 'Streamline your job search with AI-powered LinkedIn automation.',
    images: ['/og-image.jpg'],
    creator: '@jobflowpro',
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
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              "name": "JobFlow Pro",
              "description": "AI-powered LinkedIn job search automation for students and recent graduates",
              "url": "https://jobflowpro.com",
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
                "name": "JobFlow Pro"
              }
            })
          }}
        />
      </head>
      <body className={inter.className}>
        <AuthProvider>
          <Providers>
            {children}
          </Providers>
        </AuthProvider>
      </body>
    </html>
  )
} 

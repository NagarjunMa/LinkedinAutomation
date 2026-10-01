import type { Metadata } from "next"
import { headers } from "next/headers"
import localFont from "next/font/local"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import "./globals.css"
import { Providers } from "@/components/ui/providers"
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
    default: "PrismPro — Career Evidence Coach for Technical Candidates",
    template: "%s | PrismPro"
  },
  description: "Uncover the work your resume and LinkedIn miss. PrismPro turns confirmed career evidence into truthful, role-aligned application and interview material.",
  keywords: [
    "career evidence coach",
    "career story for software engineers",
    "truthful AI resume help",
    "evidence grounded resume",
    "LinkedIn profile review for engineers",
    "technical interview story builder",
    "career evidence interview",
    "role aligned resume",
    "resume and LinkedIn consistency",
    "technical career positioning"
  ],
  authors: [{ name: "PrismPro Team" }],
  creator: "PrismPro",
  publisher: "PrismPro",
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
    title: 'Make the Work Behind Your Resume Visible | PrismPro',
    description: 'A career-evidence coach that interviews before it writes and uses only candidate-confirmed facts.',
    siteName: 'PrismPro',
    images: [
      {
        url: '/opengraph-image',
        width: 1200,
        height: 630,
        alt: 'PrismPro — Make the work behind your resume visible',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Make the Work Behind Your Resume Visible | PrismPro',
    description: 'A career-evidence coach that interviews before it writes and uses only candidate-confirmed facts.',
    images: ['/opengraph-image'],
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

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Reading request headers makes every page dynamic, so the Proxy's nonce
  // can be applied to Next.js scripts and this structured-data block.
  const nonce = (await headers()).get('x-nonce') ?? undefined
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          id="prismpro-structured-data"
          nonce={nonce}
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              "name": "PrismPro",
              "description": "Career-evidence coach in development for technical candidates. PrismPro is designed to uncover truthful work evidence and prepare role-aligned resume, LinkedIn, and interview material from candidate-confirmed facts.",
              "url": appOrigin,
              "applicationCategory": "BusinessApplication",
              "operatingSystem": "Web Browser",
              "author": {
                "@type": "Organization",
                "name": "PrismPro"
              }
            }).replace(/</g, '\\u003c')
          }}
        />
      </head>
      <body className={`${GeistSans.variable} ${GeistMono.variable} ${humane.variable}`}>
        <ErrorBoundary fallback={PageErrorFallback}>
          <ThemeProvider>
            <Providers nonce={nonce}>{children}</Providers>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
} 

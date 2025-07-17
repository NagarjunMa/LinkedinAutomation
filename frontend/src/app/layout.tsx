import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "@/components/ui/providers"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "LinkedIn Job Search Dashboard",
  description: "Automated LinkedIn Job Search and Application Dashboard",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
} 

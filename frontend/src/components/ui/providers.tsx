"use client"

import { ThemeProvider } from "next-themes"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { TooltipProvider } from "@/components/ui/tooltip"
import { useState } from "react"

export function Providers({ children, nonce }: { children: React.ReactNode; nonce?: string }) {
    // Create a new QueryClient instance for each app instance
    const [queryClient] = useState(
        () => new QueryClient({
            defaultOptions: {
                queries: {
                    staleTime: 60 * 1000, // 1 minute
                    retry: 2,
                    refetchOnWindowFocus: false,
                },
            },
        })
    )

    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider
                nonce={nonce}
                attribute="class"
                defaultTheme="dark"
                enableSystem={true}
                storageKey="prism-theme"
            >
                <TooltipProvider>
                    {children}
                </TooltipProvider>
            </ThemeProvider>
        </QueryClientProvider>
    )
}

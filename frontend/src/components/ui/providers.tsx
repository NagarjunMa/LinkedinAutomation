"use client"

import { ThemeProvider } from "next-themes"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

export function Providers({ children }: { children: React.ReactNode }) {
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
                attribute="class"
                defaultTheme="system"
                enableSystem={true}
                storageKey="jobflow-theme"
            >
                {children}
            </ThemeProvider>
        </QueryClientProvider>
    )
} 
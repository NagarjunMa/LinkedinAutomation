// app/providers.tsx
'use client'

import { ChakraProvider } from '@chakra-ui/react'
import { ColorModeProvider } from '@/components/ui/color-mode'
import { defaultSystem } from '@chakra-ui/react'


export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ChakraProvider value={defaultSystem}>
            <ColorModeProvider>{children}</ColorModeProvider>
        </ChakraProvider>
    )
}
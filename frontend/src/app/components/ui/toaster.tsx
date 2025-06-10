"use client"

import * as React from "react"
import { ToastProvider, ToastViewport } from "@radix-ui/react-toast"

export function Toaster({ children }: { children?: React.ReactNode }) {
    return (
        <ToastProvider>
            {children}
            <ToastViewport className="fixed bottom-0 right-0 flex flex-col p-4 gap-2 z-50" />
        </ToastProvider>
    )
}
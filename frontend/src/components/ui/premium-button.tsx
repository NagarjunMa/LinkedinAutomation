"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface PremiumButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    variant?: "primary" | "secondary";
}

export const PremiumButton = React.forwardRef<HTMLButtonElement, PremiumButtonProps>(
    ({ className, children, variant: _variant = "primary", ...props }, ref) => {
        return (
            <button
                ref={ref}
                className={cn(
                    "premium-button relative overflow-hidden inline-block transition-all duration-200 z-10 cursor-pointer text-sm font-bold uppercase tracking-widest rounded-lg px-8 py-3.5",
                    // Theme colors using our CSS variables
                    "text-app-text bg-app-card border border-app-text/10",
                    // Hover state text color change handled by CSS class .premium-button:hover
                    "hover:border-app-text",
                    // Shadows
                    "shadow-lg shadow-black/5 hover:shadow-xl hover:shadow-black/10",
                    className
                )}
                {...props}
            >
                {children}
            </button>
        );
    }
);

PremiumButton.displayName = "PremiumButton";

"use client";

import { useEffect, useRef, useState } from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { Menu, X } from "lucide-react"
import { SophisticatedSidebar, SidebarProvider, useSidebar } from "./sophisticated-sidebar"
import { SophisticatedHeader } from "./sophisticated-header"
import { AnimatePresence } from 'framer-motion';

interface SophisticatedLayoutProps {
    children: React.ReactNode
    notificationCount?: number
    showHeader?: boolean
}

// Inner component to consume the context
const LayoutContent = ({ children, notificationCount, showHeader }: SophisticatedLayoutProps) => {
    const { isCollapsed } = useSidebar();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const desktopNavigation = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!sidebarOpen) return;
        const desktop = window.matchMedia("(min-width: 64rem)");
        const closeOnDesktop = () => {
            if (desktop.matches) setSidebarOpen(false);
        };
        desktop.addEventListener("change", closeOnDesktop);
        closeOnDesktop();
        return () => desktop.removeEventListener("change", closeOnDesktop);
    }, [sidebarOpen]);

    return (
        <div className="min-h-screen bg-app-bg text-app-text transition-colors duration-300">
            <div ref={desktopNavigation} className="hidden lg:block">
                <SophisticatedSidebar />
            </div>

            {/* CSS keeps sidebar spacing desktop-only, including before hydration. */}
            <main
                className={`@container ml-0 min-w-0 flex-1 min-h-screen flex flex-col transition-[margin-left] [transition-duration:600ms] [transition-timing-function:cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none ${isCollapsed ? 'lg:ml-20' : 'lg:ml-[280px]'}`}
            >
                {showHeader && (
                    <DialogPrimitive.Root open={sidebarOpen} onOpenChange={setSidebarOpen}>
                        <SophisticatedHeader
                            notificationCount={notificationCount}
                            navigationControl={
                                <DialogPrimitive.Trigger asChild>
                                    <button type="button" aria-label="Open navigation" className="inline-flex size-11 shrink-0 items-center justify-center rounded-sm text-app-text/70 hover:bg-app-text/5 hover:text-app-text focus-visible:outline-2 focus-visible:outline-offset-2 lg:hidden">
                                        <Menu aria-hidden="true" className="size-5" />
                                    </button>
                                </DialogPrimitive.Trigger>
                            }
                        />
                        <DialogPrimitive.Portal>
                            <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />
                            <DialogPrimitive.Content
                                aria-describedby={undefined}
                                className="fixed inset-y-0 left-0 z-50 w-70 max-w-full bg-app-bg shadow-xl"
                                onCloseAutoFocus={event => {
                                    const desktopHome = desktopNavigation.current?.querySelector('a');
                                    if (desktopHome?.getClientRects().length) {
                                        event.preventDefault();
                                        desktopHome.focus({ preventScroll: true });
                                    }
                                }}
                            >
                                <DialogPrimitive.Title className="sr-only">Workspace navigation</DialogPrimitive.Title>
                                <DialogPrimitive.Close asChild>
                                    <button type="button" aria-label="Close navigation" className="absolute top-6 right-3 z-10 inline-flex size-11 items-center justify-center rounded-sm text-app-text/70 hover:bg-app-text/5 hover:text-app-text focus-visible:outline-2">
                                        <X aria-hidden="true" className="size-5" />
                                    </button>
                                </DialogPrimitive.Close>
                                <SophisticatedSidebar onClose={() => setSidebarOpen(false)} />
                            </DialogPrimitive.Content>
                        </DialogPrimitive.Portal>
                    </DialogPrimitive.Root>
                )}

                <div className="p-8 md:p-12 overflow-y-auto w-full">
                    <AnimatePresence mode="wait">
                        {children}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
};

export function SophisticatedLayout(props: SophisticatedLayoutProps) {
    return (
        <SidebarProvider>
            <LayoutContent {...props} />
        </SidebarProvider>
    )
}

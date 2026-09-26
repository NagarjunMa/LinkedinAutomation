"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Sun, Moon } from 'lucide-react';
import Link from 'next/link';
import { useTheme } from '@/contexts/theme-context';
import { useHydratedReducedMotion } from '@/hooks/use-hydrated-reduced-motion';

export const Navigation: React.FC = () => {
  const { isDark, toggleTheme } = useTheme();
  const reduceMotion = useHydratedReducedMotion();

  return (
    <>
      {/* Top dark band — full-width charcoal strip */}
      <div
        className="fixed top-0 left-0 right-0 z-[101] h-[14px]"
        style={{ backgroundColor: '#1a1a1a' }}
      />

      {/* Nav — sits below dark band, on bg color */}
      <nav className="fixed top-[14px] left-0 right-0 z-[100] transition-colors duration-300 border-b border-foreground/[0.08]">
        <div
          className="transition-colors duration-300"
          style={{ backgroundColor: 'hsl(var(--background) / 0.95)' }}
        >
          <div className="max-w-[1400px] mx-auto px-4 py-7 flex items-center justify-between sm:px-8">

            {/* Left: wordmark */}
            <Link href="/" className="flex min-h-11 items-center gap-3">
              {/* Abstract glyph — thin circle-cross icon */}
              <span
                className="w-5 h-5 border border-foreground/40 rounded-full flex items-center justify-center shrink-0"
                aria-hidden="true"
              >
                <span className="w-[1px] h-3 bg-foreground/40 absolute" />
              </span>
              <span
                className="text-foreground uppercase font-humane"
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontVariationSettings: '"wght" 600',
                  letterSpacing: '0.04em',
                  lineHeight: 1,
                }}
              >
                PRISM PRO.
              </span>
            </Link>

            {/* Center: nav links */}
            <div className="hidden lg:flex items-center gap-9">
              {[
                { label: 'HOW IT WORKS', href: '/#how-it-works' },
                { label: "WHAT YOU'LL GET", href: '/#experience' },
                { label: 'PRINCIPLES', href: '/#principles' },
                { label: 'FAQ', href: '/#faq' },
              ].map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="flex min-h-11 items-center text-foreground/90 hover:text-foreground transition-colors duration-200 uppercase font-humane"
                  style={{ fontSize: '22px', fontWeight: 600, fontVariationSettings: '"wght" 600', letterSpacing: '0.14em', lineHeight: 1 }}
                >
                  {item.label}
                </Link>
              ))}
            </div>

            {/* Right: pre-launch CTA + theme toggle. Authentication stays closed. */}
            <div className="flex items-center gap-2 sm:gap-5">
              <button
                onClick={toggleTheme}
                className="flex h-11 w-11 items-center justify-center text-foreground/50 hover:text-foreground transition-colors duration-200"
                aria-label="Toggle theme"
              >
                <AnimatePresence mode="wait">
                  {isDark ? (
                    <motion.div
                      key="sun"
                      initial={reduceMotion ? false : { rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: reduceMotion ? 0 : 90, opacity: 0 }}
                      transition={{ duration: reduceMotion ? 0 : 0.2 }}
                    >
                      <Sun size={16} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="moon"
                      initial={reduceMotion ? false : { rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: reduceMotion ? 0 : 90, opacity: 0 }}
                      transition={{ duration: reduceMotion ? 0 : 0.2 }}
                    >
                      <Moon size={16} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>

              <Link
                href="/#early-access"
                className="inline-flex min-h-11 items-center gap-2 border border-foreground/30 px-3 text-foreground/90 transition-colors duration-200 hover:border-foreground hover:text-foreground sm:px-4"
                style={{ fontFamily: 'var(--font-geist-sans), sans-serif', fontSize: '13px', fontWeight: 700, letterSpacing: '0.14em', lineHeight: 1 }}
              >
                <span className="uppercase"><span className="hidden sm:inline">JOIN THE </span>PREVIEW</span>
                <ArrowRight size={14} aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </nav>
    </>
  );
};

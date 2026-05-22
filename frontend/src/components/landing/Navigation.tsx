"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import Link from 'next/link';
import { useTheme } from '@/contexts/theme-context';

const smoothScrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId);
  if (element) {
    const headerOffset = 80;
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
  }
};

export const Navigation: React.FC = () => {
  const { isDark, toggleTheme } = useTheme();

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
          style={{ backgroundColor: isDark ? 'hsl(0 0% 5% / 0.95)' : 'hsl(40 14% 91% / 0.95)' }}
        >
          <div className="max-w-[1400px] mx-auto px-8 py-7 flex items-center justify-between">

            {/* Left: wordmark */}
            <Link href="/" className="flex items-center gap-3">
              {/* Abstract glyph — thin circle-cross icon */}
              <span
                className="w-5 h-5 border border-foreground/40 rounded-full flex items-center justify-center shrink-0"
                aria-hidden="true"
              >
                <span className="w-[1px] h-3 bg-foreground/40 absolute" />
              </span>
              <span
                className="text-foreground uppercase font-humane"
                style={{ fontSize: '18px', fontWeight: 600, letterSpacing: '0.12em', lineHeight: 1 }}
              >
                PRISM PRO.
              </span>
            </Link>

            {/* Center: nav links */}
            <div className="hidden md:flex items-center gap-12">
              {[
                { label: 'PRODUCT', action: () => smoothScrollToSection('how-it-works') },
                { label: 'DOCS', href: '/docs' },
                { label: 'PRICING', action: () => smoothScrollToSection('pricing') },
              ].map((item) =>
                item.href ? (
                  <Link
                    key={item.label}
                    href={item.href}
                    className="text-foreground/55 hover:text-foreground transition-colors duration-200 uppercase font-humane"
                    style={{ fontSize: '14px', fontWeight: 500, letterSpacing: '0.18em', lineHeight: 1 }}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <button
                    key={item.label}
                    onClick={item.action}
                    className="text-foreground/55 hover:text-foreground transition-colors duration-200 uppercase font-humane"
                    style={{ fontSize: '14px', fontWeight: 500, letterSpacing: '0.18em', lineHeight: 1 }}
                  >
                    {item.label}
                  </button>
                )
              )}
            </div>

            {/* Right: sign in + theme toggle */}
            <div className="flex items-center gap-5">
              <button
                onClick={toggleTheme}
                className="p-1.5 text-foreground/50 hover:text-foreground transition-colors duration-200"
                aria-label="Toggle theme"
              >
                <AnimatePresence mode="wait">
                  {isDark ? (
                    <motion.div
                      key="sun"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Sun size={16} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="moon"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Moon size={16} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>

              <Link href="/login">
                <span
                  className="text-foreground/55 hover:text-foreground transition-colors duration-200 uppercase font-humane"
                  style={{ fontSize: '14px', fontWeight: 500, letterSpacing: '0.18em', lineHeight: 1 }}
                >
                  SIGN IN
                </span>
              </Link>
            </div>
          </div>
        </div>
      </nav>
    </>
  );
};

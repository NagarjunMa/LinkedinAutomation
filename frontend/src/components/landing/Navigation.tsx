"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import Link from 'next/link';
import { StyledButton } from './StyledButton';
import { useTheme } from '@/contexts/theme-context';

const smoothScrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId);
  if (element) {
    const headerOffset = 80;
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
};

export const Navigation: React.FC = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <nav className={`fixed top-0 left-0 right-0 z-[100] border-b ${isDark ? 'border-white/10 bg-[#1c1914]/80' : 'border-black/10 bg-[#f7f5f2]/80'} backdrop-blur-md transition-colors duration-300`}>
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Wordmark */}
        <Link href="/" className="flex items-center gap-0">
          <span className="font-bold tracking-tight text-xl text-foreground" style={{ fontFamily: 'var(--font-fraunces), serif' }}>
            Prism <span className="italic font-normal opacity-80">Pro</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-10 text-xs font-medium tracking-widest uppercase opacity-60">
          <button
            onClick={() => smoothScrollToSection('how-it-works')}
            className="hover:opacity-100 transition-opacity"
          >
            Product
          </button>
          <Link
            href="/docs"
            className="hover:opacity-100 transition-opacity"
          >
            Docs
          </Link>
          <button
            onClick={() => smoothScrollToSection('pricing')}
            className="hover:opacity-100 transition-opacity"
          >
            Pricing
          </button>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-full border ${isDark ? 'border-white/20 hover:bg-white/10' : 'border-black/20 hover:bg-black/10'} transition-all`}
            aria-label="Toggle Theme"
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
                  <Sun size={18} />
                </motion.div>
              ) : (
                <motion.div
                  key="moon"
                  initial={{ rotate: -90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  exit={{ rotate: 90, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <Moon size={18} />
                </motion.div>
              )}
            </AnimatePresence>
          </button>
          <Link href="/login">
            <StyledButton isDark={isDark}>Sign In</StyledButton>
          </Link>
        </div>
      </div>
    </nav>
  );
};

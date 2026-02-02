"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Sun, Moon } from 'lucide-react';
import Link from 'next/link';
import { StyledButton } from './StyledButton';
import { useTheme } from '@/contexts/theme-context';

const smoothScrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId);
  if (element) {
    const headerOffset = 80; // Account for fixed header height
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
    <nav className={`fixed top-0 left-0 right-0 z-[100] border-b ${isDark ? 'border-[#f0eff2]/10 bg-[#3b3b3b]/80' : 'border-[#3b3b3b]/10 bg-[#f0eff2]/80'} backdrop-blur-md transition-colors duration-300`}>
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className={`w-8 h-8 ${isDark ? 'bg-[#f0eff2]' : 'bg-[#3b3b3b]'} flex items-center justify-center rounded-sm transition-colors`}>
            <Cpu className={isDark ? 'text-[#3b3b3b]' : 'text-[#f0eff2]'} size={18} />
          </div>
          <span className="font-extrabold tracking-tighter text-xl text-foreground">
            PRISM <span className="font-serif italic lowercase font-medium opacity-70">pro</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-10 text-xs font-medium tracking-widest uppercase opacity-60">
          <button
            onClick={() => smoothScrollToSection('prevention')}
            className="hover:opacity-100 transition-opacity"
          >
            Prevention
          </button>
          <button
            onClick={() => smoothScrollToSection('system')}
            className="hover:opacity-100 transition-opacity"
          >
            The System
          </button>
          <button
            onClick={() => smoothScrollToSection('accountability')}
            className="hover:opacity-100 transition-opacity"
          >
            Accountability
          </button>
          <Link
            href="https://www.prismpro.live/privacy"
            className="hover:opacity-100 transition-opacity"
          >
            Privacy Policy
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-full border ${isDark ? 'border-[#f0eff2]/20 hover:bg-[#f0eff2]/10' : 'border-[#3b3b3b]/20 hover:bg-[#3b3b3b]/10'} transition-all`}
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
            <StyledButton isDark={isDark}>Login</StyledButton>
          </Link>
        </div>
      </div>
    </nav>
  );
};
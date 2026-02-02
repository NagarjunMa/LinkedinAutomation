"use client";

import React from 'react';
import { motion, useInView } from 'framer-motion';
import {
  ArrowRight,
  Zap,
  LayoutGrid,
  FileSearch,
  Cpu
} from 'lucide-react';
import Link from 'next/link';

// Import our landing page components
import { Navigation } from '@/components/landing/Navigation';
import { StyledButton } from '@/components/landing/StyledButton';
import { SectionHeader } from '@/components/landing/SectionHeader';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { useTheme } from '@/contexts/theme-context';

/**
 * ANIMATION VARIANTS
 */
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.17, 0.55, 0.55, 1] as any }
  }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.1
    }
  }
};

export default function LandingPage() {
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="relative min-h-screen selection:bg-current selection:text-transparent transition-colors duration-300 scroll-smooth">
      <div className="grain-overlay"></div>

      <Navigation />

      {/* HERO SECTION */}
      <section id="hero" className="relative pt-40 pb-32 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="flex flex-col items-center text-center"
          >
            <motion.div
              variants={fadeInUp}
              className={`mb-6 inline-flex items-center gap-2 px-3 py-1 rounded-full border ${isDark ? 'border-[#f0eff2]/10 bg-white/5' : 'border-[#3b3b3b]/10 bg-black/5'
                } text-[10px] font-bold tracking-[0.2em] opacity-60 uppercase`}
            >
              <Zap size={12} className="opacity-100" /> Built for Senior Engineering Roles
            </motion.div>

            <motion.h1
              variants={fadeInUp}
              className="text-5xl md:text-8xl font-bold tracking-tight mb-8 max-w-5xl leading-[0.95]"
            >
              Your job search is a numbers game. <br />
              <span className="opacity-40">You're playing without a scoreboard.</span>
            </motion.h1>

            <motion.p
              variants={fadeInUp}
              className="opacity-70 text-lg md:text-xl max-w-2xl mb-12 font-light leading-relaxed"
            >
              Engineering isn't about effort; it's about systems. Stop drowning in chaotic spreadsheets and "quick-apply" loops.
            </motion.p>

            <motion.div
              variants={fadeInUp}
              className="flex flex-col sm:flex-row items-center gap-6"
            >
              <Link href="/login">
                <StyledButton isDark={isDark}>
                  Initialize System <ArrowRight size={16} />
                </StyledButton>
              </Link>
              <button
                className={`text-xs font-bold tracking-widest uppercase py-4 px-8 border ${isDark ? 'border-[#f0eff2]/10 hover:bg-white/5' : 'border-[#3b3b3b]/10 hover:bg-black/5'
                  } transition-colors rounded-full`}
              >
                View Documentation
              </button>
            </motion.div>

            <motion.div
              variants={fadeInUp}
              className={`mt-24 w-full max-w-6xl aspect-[16/8] ${isDark ? 'bg-black/20' : 'bg-white/40'
                } rounded-sm border ${isDark ? 'border-white/5' : 'border-black/5'
                } relative overflow-hidden group shadow-2xl transition-all`}
            >
              <div
                className={`absolute inset-0 bg-gradient-to-t ${isDark ? 'from-[#0a0a0a] via-transparent to-transparent' : 'from-[#f0eff2] via-transparent to-transparent'
                  } z-10`}
              ></div>
              <img
                src="/landingpage.jpg"
                alt="Prism Pro Engineering Dashboard"
                className={`w-full h-full object-cover transition-all duration-1000 group-hover:scale-105 ${isDark ? 'opacity-80' : 'opacity-100'
                  }`}
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
                <div
                  className={`p-6 rounded-full ${isDark ? 'bg-white/5' : 'bg-black/5'
                    } backdrop-blur-md border ${isDark ? 'border-white/10' : 'border-black/10'
                    }`}
                >
                  <LayoutGrid className={isDark ? 'text-white' : 'text-black'} size={48} />
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* THE MIRROR OF PAIN / PROBLEM SECTION */}
      <section
        id="prevention"
        className={`py-32 px-6 ${isDark ? 'bg-black/10' : 'bg-white/10'
          } border-y ${isDark ? 'border-[#f0eff2]/5' : 'border-[#3b3b3b]/5'
          } scroll-mt-20 transition-colors duration-300`}
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-24 items-center">
            <SectionHeader
              label="The Mirror of Pain"
              title="Spreadsheets are where applications go to die."
              subtitle="The average senior engineer loses 40% of their interview opportunities due to poor follow-up and missing context."
            />
            <div className="space-y-8">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className={`flex gap-6 p-6 border ${isDark ? 'border-white/10 bg-white/5' : 'border-black/10 bg-black/5'
                  } rounded-sm`}
              >
                <div
                  className={`shrink-0 w-12 h-12 flex items-center justify-center border ${isDark
                    ? 'border-red-400/30 bg-red-400/10 text-red-400'
                    : 'border-red-600/30 bg-red-600/10 text-red-600'
                    } rounded-sm`}
                >
                  <FileSearch size={20} />
                </div>
                <div>
                  <h4 className="font-bold mb-2">The Context Gap</h4>
                  <p className="text-sm opacity-60 leading-relaxed">
                    Snapshot job requirements before they disappear.
                  </p>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* BENTO GRID FEATURES */}
      <section id="system" className="py-32 px-6 scroll-mt-20">
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            label="Systemic Solutions"
            title="A technical stack for the human element."
            subtitle="Implement an accountability layer for your engineering job search."
          />
          <BentoGrid isDark={isDark} />
        </div>
      </section>

      {/* ACCOUNTABILITY / CTA SECTION */}
      <section
        id="accountability"
        className={`py-32 px-6 ${isDark ? 'bg-[#f0eff2] text-[#0a0a0a]' : 'bg-[#0a0a0a] text-[#f0eff2]'
          } scroll-mt-20 transition-colors duration-300`}
      >
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
          <SectionHeader
            label="Commitment Required"
            title="Stop wasting your seniority on volume."
            subtitle="Prism Pro is an exclusive system for engineers who treat their career like an engineering problem."
          />
          <div className="mt-8">
            <Link href="/login">
              <StyledButton isDark={!isDark}>
                Request System Access <ArrowRight size={20} />
              </StyledButton>
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer
        className={`py-20 px-6 border-t ${isDark ? 'border-[#f0eff2]/5' : 'border-[#3b3b3b]/5'
          } transition-colors duration-300`}
      >
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="max-w-sm">
            <div className="flex items-center gap-2 mb-6">
              <div
                className={`w-8 h-8 ${isDark ? 'bg-white/10' : 'bg-black/10'
                  } flex items-center justify-center rounded-sm`}
              >
                <Cpu size={18} />
              </div>
              <span className="font-bold tracking-tighter text-xl">
                PRISM<span className="opacity-40 font-light text-sm">PRO</span>
              </span>
            </div>
            <p className="opacity-50 text-sm leading-relaxed mb-8">
              High-precision career management for the top 1% of engineers.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-16">
            <div>
              <h5 className="text-[10px] font-bold tracking-[0.2em] uppercase mb-6 opacity-100">
                System
              </h5>
              <ul className="text-sm opacity-50 space-y-4">
                <li className="hover:opacity-100 transition-opacity cursor-pointer">Protocol</li>
                <li className="hover:opacity-100 transition-opacity cursor-pointer">Security</li>
                <li><Link href="https://www.prismpro.live/privacy" className="opacity-100 hover:text-primary transition-colors cursor-pointer">Privacy Policy</Link></li>
                <li><Link href="https://www.prismpro.live/terms" className="opacity-100 hover:text-primary transition-colors cursor-pointer">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
        </div>
        <div
          className={`max-w-7xl mx-auto mt-20 pt-8 border-t ${isDark ? 'border-white/5' : 'border-black/5'
            } flex flex-col md:flex-row justify-between items-center gap-4`}
        >
          <p className="text-[10px] opacity-40 tracking-widest uppercase">
            © 2026 Prism Pro Engineering. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
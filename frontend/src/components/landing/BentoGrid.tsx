"use client";

import React from 'react';
import { motion, useInView } from 'framer-motion';
import {
  Camera,
  Target,
  Users,
  Cpu,
  Database,
  Link2
} from 'lucide-react';

interface BentoGridProps {
  isDark: boolean;
}

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
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

export const BentoGrid: React.FC<BentoGridProps> = ({ isDark }) => {
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });

  return (
    <motion.div
      ref={ref}
      variants={staggerContainer}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-[240px]"
    >
      <motion.div
        variants={fadeInUp}
        className="md:col-span-8 bento-card p-8 rounded-sm flex flex-col justify-between group"
      >
        <div>
          <Camera className="mb-4 group-hover:opacity-60 transition-opacity" size={24} />
          <h3 className="text-xl font-bold mb-2">URL Persistence Engine</h3>
          <p className="opacity-70 max-w-md text-sm leading-relaxed">
            Automatically snapshot job requirements and listing data before they disappear. Your context is archived instantly.
          </p>
        </div>
        <div className="flex items-center gap-2 opacity-50 text-[10px] tracking-[0.2em] uppercase font-bold">
          <Link2 size={12} /> Live Link Capture Active
        </div>
      </motion.div>

      <motion.div
        variants={fadeInUp}
        className={`md:col-span-4 bento-card p-8 rounded-sm flex flex-col justify-between group ${
          isDark ? 'bg-gradient-to-br from-white/5 to-transparent' : 'bg-gradient-to-br from-black/5 to-transparent'
        }`}
      >
        <div>
          <Target className="mb-4 group-hover:scale-110 transition-transform" size={24} />
          <h3 className="text-xl font-bold mb-2">Harvard Audit</h3>
          <p className="opacity-70 text-sm leading-relaxed">
            Single-call AI analysis against engineering leadership standards.
          </p>
        </div>
        <div className={`h-2 w-full ${isDark ? 'bg-[#f0eff2]/10' : 'bg-[#3b3b3b]/10'} rounded-full overflow-hidden`}>
          <div className={`h-full w-[94%] ${isDark ? 'bg-[#f0eff2]' : 'bg-[#3b3b3b]'}`}></div>
        </div>
      </motion.div>

      <motion.div
        variants={fadeInUp}
        className="md:col-span-4 bento-card p-8 rounded-sm flex flex-col justify-between group"
      >
        <div>
          <Users className="opacity-50 mb-4" size={24} />
          <h3 className="text-xl font-bold mb-2">Network Parser</h3>
          <p className="opacity-70 text-sm leading-relaxed">
            Convert LinkedIn profiles into tailored referral requests with one paste.
          </p>
        </div>
      </motion.div>

      <motion.div
        variants={fadeInUp}
        className={`md:col-span-8 bento-card p-8 rounded-sm flex flex-col justify-between group ${
          isDark ? 'bg-white/5' : 'bg-black/5'
        }`}
      >
        <div className="flex justify-between items-start">
          <div className="max-w-md">
            <Cpu className="mb-4" size={24} />
            <h3 className="text-xl font-bold mb-2">Recursive Context Profiling</h3>
            <p className="opacity-70 text-sm leading-relaxed">
              The system that remembers your 4+ years of distributed systems engineering and masters degree.
            </p>
          </div>
          <Database className="opacity-20 hidden lg:block" size={80} />
        </div>
        <div className="flex gap-4">
          <div
            className={`px-3 py-1 ${
              isDark ? 'bg-white/10' : 'bg-black/10'
            } text-[10px] rounded-full uppercase tracking-tighter`}
          >
            Distributed Systems
          </div>
          <div
            className={`px-3 py-1 ${
              isDark ? 'bg-white/10' : 'bg-black/10'
            } text-[10px] rounded-full uppercase tracking-tighter`}
          >
            React Specialist
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
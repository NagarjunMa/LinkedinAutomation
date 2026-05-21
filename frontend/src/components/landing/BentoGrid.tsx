"use client";

import React from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';
import {
  ScanText,
  Target,
  FileStack,
  Coins,
  FileDiff,
  Globe
} from 'lucide-react';

interface BentoGridProps {
  isDark: boolean;
}

export const BentoGrid: React.FC<BentoGridProps> = ({ isDark }) => {
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });
  const reduce = useReducedMotion();

  const fadeInUp = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } }
      };

  const staggerContainer = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.12, delayChildren: 0.1 } }
      };

  // Hover props: subtle scale + transition; skipped when reduced motion is requested
  const cardHover = reduce ? {} : { scale: 1.02 };
  const cardHoverTransition = { duration: 0.2, ease: 'easeOut' };

  const borderClass = isDark ? 'border-white/10' : 'border-black/10';
  const subtleClass = isDark ? 'bg-white/5' : 'bg-black/5';
  const pillClass = isDark ? 'bg-white/10 text-white/70' : 'bg-black/10 text-black/70';

  return (
    <motion.div
      ref={ref}
      variants={staggerContainer}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-[240px]"
    >
      {/* Card 1: ATS Simulator — wide */}
      <motion.div
        variants={fadeInUp}
        whileHover={cardHover}
        transition={cardHoverTransition}
        className="md:col-span-8 bento-card p-8 rounded-sm flex flex-col justify-between group"
      >
        <div>
          <ScanText className="mb-4 group-hover:opacity-60 transition-opacity text-primary" size={24} />
          <h3 className="text-xl font-bold mb-2">ATS Raw-Text Simulator</h3>
          <p className="opacity-70 max-w-md text-sm leading-relaxed">
            See your resume as a parser sees it — tables, columns, and special characters called out before they cost you a screen.
          </p>
        </div>
        <div className={`font-mono text-[10px] opacity-40 leading-relaxed border-l-2 border-primary/30 pl-3`}>
          {'Name: John Doe  |  [TABLE STRIPPED]  |  Skills: [COLUMN LOST]'}
        </div>
      </motion.div>

      {/* Card 2: Senior Recruiter Critique — narrow */}
      <motion.div
        variants={fadeInUp}
        whileHover={cardHover}
        transition={cardHoverTransition}
        className={`md:col-span-4 bento-card p-8 rounded-sm flex flex-col justify-between group ${subtleClass}`}
      >
        <div>
          <Target className="mb-4 group-hover:scale-110 transition-transform text-primary" size={24} />
          <h3 className="text-xl font-bold mb-2">Senior-Recruiter Panel</h3>
          <p className="opacity-70 text-sm leading-relaxed">
            Bullet-level severity flags: Strong, Weak, Vague Impact. Actionable rewrites, not five-paragraph rubrics.
          </p>
        </div>
        <div className={`h-2 w-full bg-muted rounded-full overflow-hidden`}>
          <div className={`h-full w-[82%] bg-primary`}></div>
        </div>
      </motion.div>

      {/* Card 3: JD Diff View — narrow */}
      <motion.div
        variants={fadeInUp}
        whileHover={cardHover}
        transition={cardHoverTransition}
        className="md:col-span-4 bento-card p-8 rounded-sm flex flex-col justify-between group"
      >
        <div>
          <FileDiff className="opacity-70 mb-4 text-primary" size={24} />
          <h3 className="text-xl font-bold mb-2">JD Diff &amp; Accept</h3>
          <p className="opacity-70 text-sm leading-relaxed">
            Paste any job description. AI proposes bullet rewrites and skill reorders in a diff view — accept each change individually or all at once.
          </p>
        </div>
      </motion.div>

      {/* Card 4: Country-Aware Export — wide */}
      <motion.div
        variants={fadeInUp}
        whileHover={cardHover}
        transition={cardHoverTransition}
        className={`md:col-span-8 bento-card p-8 rounded-sm flex flex-col justify-between group ${subtleClass}`}
      >
        <div className="flex justify-between items-start">
          <div className="max-w-md">
            <Globe className="mb-4 text-primary" size={24} />
            <h3 className="text-xl font-bold mb-2">Country-Aware PDF Export</h3>
            <p className="opacity-70 text-sm leading-relaxed">
              Six templates (SWE · DS · PM) × (USA · India) rendered to recruiter-standard PDFs. US 1-page compact or India extended CV — export the format that fits the market.
            </p>
          </div>
          <FileStack className={`opacity-20 hidden lg:block`} size={80} />
        </div>
        <div className="flex gap-3 flex-wrap">
          {['SWE – USA', 'DS – USA', 'PM – USA', 'SWE – India', 'DS – India', 'PM – India'].map((label) => (
            <span key={label} className={`px-3 py-1 ${pillClass} text-[10px] rounded-full uppercase tracking-tighter`}>
              {label}
            </span>
          ))}
        </div>
      </motion.div>

      {/* Card 5: Hallucination Guard — narrow */}
      <motion.div
        variants={fadeInUp}
        whileHover={cardHover}
        transition={cardHoverTransition}
        className={`md:col-span-6 bento-card p-8 rounded-sm flex flex-col justify-between group border ${borderClass}`}
      >
        <div>
          <span className={`inline-block mb-4 px-2 py-1 text-[10px] rounded font-bold tracking-widest uppercase ${pillClass}`}>
            No hallucination
          </span>
          <h3 className="text-xl font-bold mb-2">Placeholder-Hybrid Rewrites</h3>
          <p className="opacity-70 text-sm leading-relaxed">
            Hard numbers that AI can't verify are preserved as <code className="text-xs bg-muted px-1 py-0.5 rounded">[X%]</code> or <code className="text-xs bg-muted px-1 py-0.5 rounded">[N users]</code> — you fill them in. Verbs, structure, and framing are rewritten. The result reads like a recruiter wrote it, not a language model.
          </p>
        </div>
      </motion.div>

      {/* Card 6: Credits — narrow */}
      <motion.div
        variants={fadeInUp}
        whileHover={cardHover}
        transition={cardHoverTransition}
        className={`md:col-span-6 bento-card p-8 rounded-sm flex flex-col justify-between group border ${borderClass}`}
      >
        <div>
          <Coins className="mb-4 text-primary" size={24} />
          <h3 className="text-xl font-bold mb-2">Transparent Credit System</h3>
          <p className="opacity-70 text-sm leading-relaxed">
            20 free credits every month — enough to evaluate and tailor your resume twice. Top up when you need more. No subscription lock-in, no hidden AI usage fees.
          </p>
        </div>
        <div className={`flex items-center gap-3`}>
          <div className={`flex-1 h-2 rounded-full ${isDark ? 'bg-white/10' : 'bg-black/10'} overflow-hidden`}>
            <div className="h-full w-[60%] bg-primary rounded-full"></div>
          </div>
          <span className="text-[10px] opacity-50 font-bold tracking-widest uppercase">12 / 20 used</span>
        </div>
      </motion.div>
    </motion.div>
  );
};

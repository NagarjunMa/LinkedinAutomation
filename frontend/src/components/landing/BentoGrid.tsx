"use client";

import React from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';

interface BentoGridProps {
  isDark: boolean;
}

const humaneStyle = (
  size: number,
  weight: number = 400,
  tracking: string = '0'
): React.CSSProperties => ({
  fontFamily: 'var(--font-humane), sans-serif',
  fontSize: `${size}px`,
  fontWeight: weight,
  letterSpacing: tracking,
  lineHeight: 1.4,
});

const frauncesStyle = (
  size: string,
  weight: number = 500
): React.CSSProperties => ({
  fontFamily: 'var(--font-fraunces), Georgia, serif',
  fontSize: size,
  fontWeight: weight,
  letterSpacing: '-0.005em',
  lineHeight: 1.15,
});

const CARDS = [
  {
    num: '01',
    title: 'ATS Raw-Text Simulator',
    desc: 'See your resume as a parser sees it — tables, columns, and special characters called out before they cost you a screen.',
    span: 'md:col-span-2',
    detail: 'Name: John Doe  |  [TABLE STRIPPED]  |  Skills: [COLUMN LOST]',
    mono: true,
  },
  {
    num: '02',
    title: 'Senior-Recruiter Panel',
    desc: 'Bullet-level severity flags: Strong, Weak, Vague Impact. Actionable rewrites, not five-paragraph rubrics.',
    span: 'md:col-span-1',
    bar: 82,
  },
  {
    num: '03',
    title: 'JD Diff & Accept',
    desc: 'Paste any job description. AI proposes bullet rewrites in a diff view — accept each change individually or all at once.',
    span: 'md:col-span-1',
  },
  {
    num: '04',
    title: 'Country-Aware PDF Export',
    desc: 'Six templates (SWE · DS · PM) × (USA · India) rendered to recruiter-standard PDFs.',
    span: 'md:col-span-2',
    pills: ['SWE – USA', 'DS – USA', 'PM – USA', 'SWE – India', 'DS – India', 'PM – India'],
  },
  {
    num: '05',
    title: 'Placeholder-Hybrid Rewrites',
    desc: 'Hard numbers are preserved as [X%] or [N users] — you fill them in. Verbs, structure, and framing are rewritten.',
    span: 'md:col-span-1',
    tag: 'NO HALLUCINATION',
  },
  {
    num: '06',
    title: 'Transparent Credit System',
    desc: '20 free credits every month — enough to evaluate and tailor your resume twice. Top up when you need more.',
    span: 'md:col-span-1',
    creditBar: 60,
  },
];

export const BentoGrid: React.FC<BentoGridProps> = ({ isDark: _isDark }) => {
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });
  const reduce = useReducedMotion();

  const fadeInUp = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 16 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } }
      };

  const staggerContainer = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.05 } }
      };

  return (
    <motion.div
      ref={ref}
      variants={staggerContainer}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      className="grid grid-cols-1 md:grid-cols-3 gap-0 border-l border-t border-foreground/10 auto-rows-[260px]"
    >
      {CARDS.map((card) => (
        <motion.div
          key={card.num}
          variants={fadeInUp}
          className={`${card.span} border-r border-b border-foreground/10 p-8 flex flex-col justify-between group hover:bg-foreground/[0.025] transition-colors duration-200`}
        >
          {/* Card header */}
          <div>
            <div className="flex items-start justify-between mb-5">
              <span
                className="text-foreground/25"
                style={humaneStyle(11, 500, '0.18em')}
              >
                {card.num}.
              </span>
              {card.tag && (
                <span
                  className="px-2 py-1 border border-foreground/15 text-foreground/40 uppercase"
                  style={humaneStyle(10, 500, '0.15em')}
                >
                  {card.tag}
                </span>
              )}
            </div>

            <h3
              className="text-foreground mb-3 font-normal"
              style={frauncesStyle('clamp(18px, 1.6vw, 22px)')}
            >
              {card.title}
            </h3>

            <p
              className="text-foreground/50 leading-relaxed"
              style={humaneStyle(14, 400, '0')}
            >
              {card.desc}
            </p>
          </div>

          {/* Card footer — contextual detail */}
          <div>
            {card.mono && (
              <div
                className="text-foreground/30 leading-relaxed border-l border-foreground/15 pl-3"
                style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', letterSpacing: '0' }}
              >
                {card.detail}
              </div>
            )}

            {card.bar !== undefined && (
              <div className="space-y-2">
                <div className="h-[2px] w-full bg-foreground/10 overflow-hidden">
                  <div
                    className="h-full bg-foreground/50 transition-all duration-700"
                    style={{ width: `${card.bar}%` }}
                  />
                </div>
                <span
                  className="text-foreground/30 uppercase"
                  style={humaneStyle(10, 500, '0.15em')}
                >
                  RECRUITER SCORE — {card.bar}%
                </span>
              </div>
            )}

            {card.pills && (
              <div className="flex gap-2 flex-wrap">
                {card.pills.map((label) => (
                  <span
                    key={label}
                    className="px-3 py-1 border border-foreground/10 text-foreground/40 uppercase"
                    style={humaneStyle(10, 500, '0.08em')}
                  >
                    {label}
                  </span>
                ))}
              </div>
            )}

            {card.creditBar !== undefined && (
              <div className="space-y-2">
                <div className="h-[2px] w-full bg-foreground/10 overflow-hidden">
                  <div
                    className="h-full bg-foreground/40 transition-all duration-700"
                    style={{ width: `${card.creditBar}%` }}
                  />
                </div>
                <span
                  className="text-foreground/30 uppercase"
                  style={humaneStyle(10, 500, '0.15em')}
                >
                  12 / 20 CREDITS USED
                </span>
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
};

"use client";

import React from 'react';
import { motion, type Variants, useInView } from 'framer-motion';

import { useHydratedReducedMotion } from '@/hooks/use-hydrated-reduced-motion';

interface BentoGridProps {
  isDark: boolean;
}

const humaneStyle = (
  size: number,
  weight: number = 400,
  tracking: string = '0'
): React.CSSProperties => ({
  fontFamily: 'var(--font-geist-sans), system-ui, sans-serif',
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
    title: 'Career Evidence Coach',
    desc: 'A chaptered conversation that asks one useful question at a time, based on your career stage and the evidence still missing.',
    span: 'md:col-span-2',
    detail: 'What part of the service did you personally design, and what constraint shaped that decision?',
    mono: true,
  },
  {
    num: '02',
    title: 'Evidence Notebook',
    desc: 'Review each proposed claim, its source, support level, and privacy state before it can be used.',
    span: 'md:col-span-1',
    status: 'CONFIRM · EDIT · PRIVATE',
  },
  {
    num: '03',
    title: 'Coverage Report',
    desc: 'See communication, evidence, experience, knowledge, and positioning gaps as separate findings—not one magic score.',
    span: 'md:col-span-1',
    pills: ['Communication', 'Evidence', 'Experience', 'Knowledge', 'Positioning'],
  },
  {
    num: '04',
    title: 'Target Role Views',
    desc: 'Project one confirmed career history toward different roles without deleting breadth or creating contradictions.',
    span: 'md:col-span-2',
    pills: ['Role requirements', 'Strongest proof', 'Open questions', 'Level alignment'],
  },
  {
    num: '05',
    title: 'LinkedIn PDF Review',
    desc: 'Compare a user-uploaded profile snapshot with confirmed evidence and the active target—without live account access.',
    span: 'md:col-span-1',
    tag: 'NO SCRAPING',
  },
  {
    num: '06',
    title: 'Grounded Career Artifacts',
    desc: 'Prepare resume changes, LinkedIn copy, interview stories, and a hiring-manager brief using confirmed non-private evidence only.',
    span: 'md:col-span-1',
    status: 'EVIDENCE-LINKED',
  },
];

export const BentoGrid: React.FC<BentoGridProps> = ({ isDark: _isDark }) => {
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });
  const reduce = useHydratedReducedMotion();

  const fadeInUp: Variants = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 16 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } }
      };

  const staggerContainer: Variants = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.05 } }
      };

  return (
    <figure ref={ref}>
      <div className="mb-4 flex items-center justify-between gap-4 border-y border-foreground/10 py-3">
        <span
          className="uppercase text-foreground/70"
          style={humaneStyle(10, 700, '0.18em')}
        >
          Planned concept preview
        </span>
        <span className="text-foreground/70" style={humaneStyle(10, 500, '0.08em')}>
          NOT A PRODUCTION SCREENSHOT
        </span>
      </div>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="grid auto-rows-[260px] grid-cols-1 gap-0 border-l border-t border-foreground/10 md:grid-cols-3"
      >
        {CARDS.map((card) => (
          <motion.div
            key={card.num}
            variants={fadeInUp}
            className={`${card.span} group flex flex-col justify-between border-b border-r border-foreground/10 p-8 transition-colors duration-200 hover:bg-foreground/[0.025]`}
          >
          {/* Card header */}
          <div>
            <div className="flex items-start justify-between mb-5">
              <span
                className="text-foreground/70"
                style={humaneStyle(11, 500, '0.18em')}
              >
                {card.num}.
              </span>
              {card.tag && (
                <span
                  className="px-2 py-1 border border-foreground/15 text-foreground/70 uppercase"
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
              className="text-foreground/70 leading-relaxed"
              style={humaneStyle(14, 400, '0')}
            >
              {card.desc}
            </p>
          </div>

          {/* Card footer — contextual detail */}
          <div>
            {card.mono && (
              <div
                className="text-foreground/70 leading-relaxed border-l border-foreground/15 pl-3"
                style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', letterSpacing: '0' }}
              >
                {card.detail}
              </div>
            )}

            {card.pills && (
              <div className="flex gap-2 flex-wrap">
                {card.pills.map((label) => (
                  <span
                    key={label}
                    className="px-3 py-1 border border-foreground/10 text-foreground/70 uppercase"
                    style={humaneStyle(10, 500, '0.08em')}
                  >
                    {label}
                  </span>
                ))}
              </div>
            )}

            {card.status && (
              <div className="flex items-center gap-3">
                <span className="h-2 w-2 rounded-full bg-foreground/35" />
                <span
                  className="text-foreground/70 uppercase"
                  style={humaneStyle(10, 500, '0.15em')}
                >
                  {card.status}
                </span>
              </div>
            )}
          </div>
          </motion.div>
        ))}
      </motion.div>
      <figcaption className="mt-4 text-sm leading-relaxed text-foreground/70">
        Planned experience shown for illustration. Public product access is not yet available.
      </figcaption>
    </figure>
  );
};

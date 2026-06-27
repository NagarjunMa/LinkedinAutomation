"use client";

import React from 'react';
import { motion, type Variants, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  Upload,
  ScanText,
  FileDiff,
  Download,
  CheckCircle
} from 'lucide-react';
import Link from 'next/link';

import { Navigation } from '@/components/landing/Navigation';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { useTheme } from '@/contexts/theme-context';

// ── Motion variants respecting prefers-reduced-motion ─────────────────────
function useMotionVariants() {
  const reduce = useReducedMotion();

  const fadeIn: Variants = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { duration: 0.7, ease: [0.17, 0.55, 0.55, 1] as [number, number, number, number] }
        }
      };

  const fadeInUp: Variants = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 20 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.7, ease: [0.17, 0.55, 0.55, 1] as [number, number, number, number] }
        }
      };

  const staggerContainer: Variants = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: 0.12, delayChildren: 0.05 }
        }
      };

  const scrollReveal: Variants = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 16 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
      };

  return { fadeIn, fadeInUp, staggerContainer, scrollReveal, reduce };
}

// ── Data ───────────────────────────────────────────────────────────────────
const STEPS = [
  {
    icon: Upload,
    step: '01',
    title: 'Upload your resume',
    desc: 'PDF or DOCX. Prism Pro turns your existing resume into structured content you can evaluate, tailor, and reuse.'
  },
  {
    icon: ScanText,
    step: '02',
    title: 'See what weakens the first scan',
    desc: 'Review score explanations, ATS parseability, missing evidence, noisy bullets, and the highest-impact actions before applying.'
  },
  {
    icon: FileDiff,
    step: '03',
    title: 'Tailor against the real JD',
    desc: 'Paste a job description and compare suggested changes against the role requirements before anything is applied.'
  },
  {
    icon: Download,
    step: '04',
    title: 'Save the application version',
    desc: 'Keep a company-specific resume record, then export an ATS-aware PDF when you are ready to submit.'
  }
];

const PROBLEMS = [
  {
    stat: 'ATS',
    label: 'parsers flatten the resume before anyone sees it',
    detail: 'Tables, columns, headers, special characters, and missing dates can change what systems actually read.'
  },
  {
    stat: 'SCAN',
    label: 'strong experience gets buried under noisy bullets',
    detail: 'A recruiter should not have to hunt through every project to understand your fit for the role.'
  },
  {
    stat: 'FIT',
    label: 'a strong general resume can still miss the job',
    detail: 'Each JD asks for a different mix of evidence, keywords, seniority signals, and project context.'
  }
];

const FEATURES = [
  {
    title: 'Transparent score explanations',
    desc: 'Scores are broken into readable reasons and top actions, so you know what to fix before sending the resume.'
  },
  {
    title: 'ATS raw-text simulator',
    desc: 'Preview the text an ATS-style parser sees, including formatting issues that can hide otherwise strong experience.'
  },
  {
    title: 'Diff-based tailoring control',
    desc: 'Accept, edit, reset, regenerate, or reject every suggested pointer. The final resume changes only when you approve it.'
  },
  {
    title: 'Truth-checked rewrite signals',
    desc: 'Unsupported numbers and JD skills are blocked or surfaced as review signals instead of quietly becoming fake achievements.'
  },
  {
    title: 'One-page fit guardrails',
    desc: 'For US-style resumes, Prism Pro helps prioritize the highest-signal bullets so tailoring does not create a noisy two-page resume.'
  },
  {
    title: 'Company-specific resume library',
    desc: 'Every accepted JD-tailored version is saved with company, role, source JD, accepted changes, and resume JSON for interview review.'
  }
];

const FAQS = [
  {
    q: 'How is this different from Rezi or Teal?',
    a: "Prism Pro is built around truthful JD-specific editing, not one-click resume generation. You see why a pointer helps, what requirement it maps to, and exactly what will change before you apply it."
  },
  {
    q: 'Does Prism Pro write fake achievements?',
    a: "It is designed to avoid unsupported claims. Rewrites are checked for invented numbers and unsupported JD skills, and every proposed change remains editable before it becomes part of a saved resume."
  },
  {
    q: 'Can I edit or reject the AI suggestions?',
    a: "Yes. Suggested pointers can be selected, cleared, edited, reset, regenerated, or switched between alternatives. Prism Pro keeps you in control of the final version."
  },
  {
    q: 'Will it always create a one-page resume?',
    a: "For US-style resumes, the workflow prioritizes one-page fit when the source content supports it. If the original resume has much more content, Prism Pro focuses on reducing noise while preserving the strongest role evidence."
  },
  {
    q: 'How are credits priced?',
    a: "Every account receives 90 free credits per month during the freemium launch. A JD tailor-and-export workflow costs 3 credits: 2 to tailor and 1 to export."
  },
  {
    q: 'Why save tailored resumes?',
    a: "Every application creates a different version. The library lets you revisit the exact company-specific resume, source JD, and accepted changes before recruiter screens or interviews."
  },
  {
    q: 'Is my resume data stored securely?',
    a: "Resume data is stored in user-scoped records and private storage. The launch checklist includes Supabase Row-Level Security and storage policy audits before public release."
  }
];

// ── Sans typography helper ─────────────────────────────────────────────────
// NOTE: Humane is reserved for the wordmark + Navbar only (see Navigation.tsx).
// All other UI labels use IBM Plex Sans for legibility.
const humaneStyle = (
  size: number,
  weight: number = 400,
  tracking: string = '0'
): React.CSSProperties => ({
  fontFamily: 'var(--font-geist-sans), system-ui, sans-serif',
  fontSize: `${size}px`,
  fontWeight: weight,
  letterSpacing: tracking,
  lineHeight: 1,
});

const frauncesStyle = (
  size: string,
  weight: number = 400,
  tracking: string = '-0.02em'
): React.CSSProperties => ({
  fontFamily: 'var(--font-fraunces), Georgia, serif',
  fontSize: size,
  fontWeight: weight,
  letterSpacing: tracking,
  lineHeight: 1.02,
});

// ── Shared split-section heading column ────────────────────────────────────
interface SplitHeadingProps {
  number: string;
  label: string;
  title: React.ReactNode;
  subtitle: string;
}

const SplitHeading: React.FC<SplitHeadingProps> = ({ number, label, title, subtitle }) => (
  <div className="lg:sticky lg:top-32 self-start">
    <div
      className="mb-8 uppercase text-foreground/85"
      style={humaneStyle(16, 700, '0.2em')}
    >
      {number} / {label}
    </div>
    <h2
      className="text-foreground font-normal mb-8 leading-[0.95]"
      style={{
        fontFamily: 'var(--font-fraunces), Georgia, serif',
        fontSize: 'clamp(36px, 4.5vw, 72px)',
        letterSpacing: '-0.02em',
        lineHeight: 0.95,
        fontWeight: 400,
      }}
    >
      {title}
    </h2>
    <p
      className="text-foreground/85 max-w-md"
      style={{ fontSize: '21px', lineHeight: 1.55, fontWeight: 400 }}
    >
      {subtitle}
    </p>
  </div>
);

// ── Page ───────────────────────────────────────────────────────────────────
export default function LandingPage() {
  const { isDark } = useTheme();
  const { fadeIn, fadeInUp, staggerContainer, scrollReveal } = useMotionVariants();

  const viewport = { once: true, margin: '-80px' } as const;
  const borderFaint = isDark ? 'border-foreground/10' : 'border-foreground/10';

  return (
    <div className="relative min-h-screen bg-background text-foreground">

      {/* ─── NAV (includes top dark band) ──────────────────────────────── */}
      <Navigation />

      {/* ─── HERO ────────────────────────────────────────────────────────── */}
      {/* Push down below fixed nav: 14px band + ~74px nav = 88px */}
      <section id="hero" className="relative pt-[88px] min-h-screen bg-background">

        {/* Asymmetric two-column grid */}
        <div className="max-w-[1400px] mx-auto px-8 grid grid-cols-1 lg:grid-cols-[1fr_1fr] min-h-[calc(100vh-88px)]">

          {/* LEFT column — eyebrow + body copy + CTAs */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="flex flex-col justify-center lg:border-r border-foreground/10 py-16 pr-0 lg:pr-20"
          >
            {/* Eyebrow — with horizontal rules for emphasis */}
            <motion.div
              variants={fadeInUp}
              className="flex items-center gap-3 mb-8"
            >
              <div className="w-10 h-[1px] bg-foreground/60" aria-hidden="true" />
              <span
                className="text-foreground uppercase"
                style={{ fontFamily: 'var(--font-geist-sans), system-ui, sans-serif', fontSize: '22px', fontWeight: 700, letterSpacing: '0.22em', lineHeight: 1 }}
              >
                TRUTHFUL TAILORING — 2026
              </span>
              <div className="w-10 h-[1px] bg-foreground/60" aria-hidden="true" />
            </motion.div>

            {/* Body copy — IBM Plex Sans for paragraph readability */}
            <motion.p
              variants={fadeInUp}
              className="text-foreground leading-relaxed mb-12"
              style={{ fontFamily: 'var(--font-geist-sans), system-ui, sans-serif', fontSize: '24px', fontWeight: 400, lineHeight: '1.5', maxWidth: '600px' }}
            >
              Upload your resume, paste a job description, and review every suggested change before it becomes your final resume.{' '}
              <span
                className="text-foreground uppercase"
                style={{ fontFamily: 'var(--font-geist-sans), system-ui, sans-serif', fontSize: '26px', fontWeight: 700, letterSpacing: '0.05em' }}
              >
                Truthful,
              </span>{' '}
              JD-specific resume prep for technical professionals.
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              variants={fadeInUp}
              className="flex flex-col sm:flex-row items-start gap-4 mb-16"
            >
              <Link href="/login">
                <button
                  className="inline-flex items-center gap-2 px-7 py-3.5 bg-foreground text-background uppercase transition-opacity hover:opacity-85"
                  style={humaneStyle(17, 700, '0.14em')}
                >
                  Tailor My Resume Free <ArrowRight size={16} />
                </button>
              </Link>
              <button
                onClick={() => {
                  const el = document.getElementById('how-it-works');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}
                className="inline-flex items-center gap-2 px-7 py-3.5 border border-foreground/40 text-foreground uppercase transition-colors hover:border-foreground"
                style={humaneStyle(17, 700, '0.14em')}
              >
                See How It Works
              </button>
            </motion.div>

            {/* Scroll down indicator — bottom left */}
            <motion.div
              variants={fadeIn}
              className="hidden lg:flex items-center gap-3"
            >
              <div className="w-10 h-[1px] bg-foreground/50" />
              <span
                className="text-foreground/75 uppercase"
                style={humaneStyle(16, 700, '0.2em')}
              >
                SCROLL DOWN
              </span>
            </motion.div>
          </motion.div>

          {/* RIGHT column — massive serif headline */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="flex flex-col justify-center py-16 pl-0 lg:pl-20"
          >
            {/* Display H1 — massive Humane, single line, left-aligned, condensed */}
            <motion.h1
              variants={fadeInUp}
              className="text-foreground uppercase leading-[0.9] mb-8 whitespace-nowrap"
              style={{
                fontFamily: 'var(--font-humane), sans-serif',
                fontSize: 'clamp(96px, 14vw, 220px)',
                letterSpacing: '0.04em',
                fontWeight: 500,
                fontVariationSettings: '"wght" 500',
              }}
            >
              PRISM PRO.
            </motion.h1>

            {/* Tagline */}
            <motion.p
              variants={fadeInUp}
              className="text-foreground/85 mb-10 max-w-xl"
              style={{
                fontFamily: 'var(--font-geist-sans), system-ui, sans-serif',
                fontSize: 'clamp(20px, 1.6vw, 26px)',
                fontWeight: 400,
                lineHeight: 1.4,
                letterSpacing: '-0.005em',
              }}
            >
              Recruiter-grade resume tailoring for engineers, data scientists, and PMs who refuse generic AI bullets.
            </motion.p>

            {/* Decorative circle — editorial accent */}
            <motion.div
              variants={fadeInUp}
              aria-hidden="true"
              className="w-24 h-24 rounded-full border border-foreground/20"
            />
          </motion.div>
        </div>
      </section>

      {/* ─── SOCIAL PROOF STRIP — infinite marquee ───────────────────────── */}
      <section className={`py-10 border-y ${borderFaint} overflow-hidden`}>
        <div className="flex items-center gap-16">
          <span
            className="shrink-0 pl-8 text-foreground/35 uppercase whitespace-nowrap"
            style={humaneStyle(15, 700, '0.2em')}
          >
            BUILT FOR
          </span>

          {/* Marquee — duplicates list twice; CSS keyframe translates -50% */}
          <div className="flex-1 overflow-hidden relative">
            <div
              className="flex gap-12 whitespace-nowrap pr-12"
              style={{
                animation: 'marquee 30s linear infinite',
                width: 'max-content',
              }}
            >
              {[...Array(2)].flatMap((_, dupIdx) =>
                ['Software Engineers', 'Data Scientists', 'Product Managers', 'ML Engineers', 'Backend Engineers', 'Cloud Engineers', 'Platform Engineers', 'Technical PMs', 'Career Switchers'].map((name) => (
                  <span
                    key={`${dupIdx}-${name}`}
                    className="text-foreground/40 uppercase shrink-0"
                    style={humaneStyle(20, 700, '0.08em')}
                  >
                    {name}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Keyframe scoped via JSX style block */}
        <style jsx>{`
          @keyframes marquee {
            0%   { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
        `}</style>
      </section>

      {/* ─── 01 / PROBLEM STATEMENT ─────────────────────────────────────── */}
      <section
        id="problem"
        className={`border-t ${borderFaint} py-32 scroll-mt-20`}
      >
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-16 lg:gap-24">

            {/* LEFT — sticky heading */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
            >
              <SplitHeading
                number="01"
                label="PROBLEM"
                title={<>The problem is not<br />your <em className="font-normal not-italic">experience.</em></>}
                subtitle="It is what survives the first scan. Prism Pro focuses on the parts that decide whether your resume gets read: parseability, signal, and role fit."
              />
            </motion.div>

            {/* RIGHT — 3 stat cards, vertical stack with hairline separators */}
            <div className="divide-y divide-foreground/10 border border-foreground/10">
              {PROBLEMS.map(({ stat, label, detail }, i) => (
                <motion.div
                  key={stat}
                  initial="hidden"
                  whileInView="visible"
                  variants={scrollReveal}
                  viewport={viewport}
                  style={{ transitionDelay: `${i * 80}ms` }}
                  className="p-10 hover:bg-foreground/[0.025] transition-colors"
                >
                  <div
                    className="mb-4 text-foreground font-normal leading-none"
                    style={frauncesStyle('clamp(40px, 4vw, 64px)', 400, '-0.02em')}
                  >
                    {stat}
                  </div>
                  <h4
                    className="font-normal mb-3 text-foreground leading-snug"
                    style={frauncesStyle('clamp(17px, 1.5vw, 21px)', 500, '-0.005em')}
                  >
                    {label}
                  </h4>
                  <p
                    className="text-foreground/85 leading-relaxed"
                    style={humaneStyle(19, 500, '0')}
                  >
                    {detail}
                  </p>
                </motion.div>
              ))}
            </div>

          </div>
        </div>
      </section>

      {/* ─── 02 / WORKFLOW ──────────────────────────────────────────────── */}
      <section id="how-it-works" className={`border-t ${borderFaint} py-32 scroll-mt-20`}>
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-16 lg:gap-24">

            {/* LEFT — sticky heading */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
            >
              <SplitHeading
                number="02"
                label="WORKFLOW"
                title={<>Four steps from<br />resume to<br /><em className="font-normal not-italic">application-ready.</em></>}
                subtitle="Every step is built for professionals who want targeted edits, proof-aware suggestions, and a saved record for each application."
              />
            </motion.div>

            {/* RIGHT — vertical stack of 4 steps */}
            <div className="divide-y divide-foreground/10 border border-foreground/10">
              {STEPS.map(({ icon: Icon, step, title, desc }, i) => (
                <motion.div
                  key={step}
                  initial="hidden"
                  whileInView="visible"
                  variants={scrollReveal}
                  viewport={viewport}
                  style={{ transitionDelay: `${i * 80}ms` }}
                  className="p-8 flex items-start gap-6 group hover:bg-foreground/[0.025] transition-colors"
                >
                  <div className="shrink-0 w-10 h-10 border border-foreground/15 flex items-center justify-center group-hover:border-foreground/30 transition-colors mt-0.5">
                    <Icon size={18} className="text-foreground/60" strokeWidth={1.25} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <h4
                        className="text-foreground font-normal"
                        style={frauncesStyle('clamp(17px, 1.5vw, 21px)', 500, '-0.005em')}
                      >
                        {title}
                      </h4>
                      <span
                        className="text-foreground/10 font-normal ml-4 shrink-0"
                        style={frauncesStyle('clamp(22px, 2.5vw, 36px)', 400, '-0.02em')}
                      >
                        {step}
                      </span>
                    </div>
                    <p
                      className="text-foreground/85 leading-relaxed"
                      style={humaneStyle(19, 500, '0')}
                    >
                      {desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>

          </div>
        </div>
      </section>

      {/* ─── 03 / FEATURES (BENTO) ──────────────────────────────────────── */}
      <section id="features" className={`border-t ${borderFaint} py-32 scroll-mt-20`}>
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-16 lg:gap-24">

            {/* LEFT — sticky heading */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
            >
              <SplitHeading
                number="03"
                label="FEATURES"
                title={<>Every tool built to keep your resume<br /><em className="font-normal italic">specific</em> and honest.</>}
                subtitle="Not a one-click generator. Each feature helps you decide what belongs on this resume for this job."
              />
            </motion.div>

            {/* RIGHT — BentoGrid constrained to right column */}
            <div>
              <BentoGrid isDark={isDark} />
            </div>

          </div>
        </div>
      </section>

      {/* ─── 04 / CAPABILITIES ──────────────────────────────────────────── */}
      <section className={`border-t ${borderFaint} py-32`}>
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-16 lg:gap-24">

            {/* LEFT — sticky heading */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
            >
              <SplitHeading
                number="04"
                label="CAPABILITIES"
                title={<>Six signals.<br />One<br /><em className="font-normal italic">deliberate</em><br />workflow.</>}
                subtitle="Evaluation, ATS view, JD fit, truth checks, page discipline, and saved versions work together so the final resume is intentional."
              />
            </motion.div>

            {/* RIGHT — 2-col grid of feature blocks */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-0 border border-foreground/10">
              {FEATURES.map(({ title, desc }, i) => (
                <motion.div
                  key={title}
                  initial="hidden"
                  whileInView="visible"
                  variants={scrollReveal}
                  viewport={viewport}
                  style={{ transitionDelay: `${i * 60}ms` }}
                  className={`p-8 hover:bg-foreground/[0.025] transition-colors border-foreground/10
                    ${i % 2 === 0 ? 'sm:border-r' : ''}
                    ${i < FEATURES.length - 2 ? 'border-b' : ''}
                    ${FEATURES.length % 2 !== 0 && i === FEATURES.length - 1 ? 'sm:col-span-2 sm:border-r-0' : ''}
                  `}
                >
                  <span
                    className="block mb-5 text-foreground/25"
                    style={humaneStyle(15, 700, '0.2em')}
                  >
                    {String(i + 1).padStart(2, '0')}.
                  </span>
                  <h4
                    className="text-foreground mb-3 font-normal"
                    style={frauncesStyle('clamp(17px, 1.5vw, 21px)', 500, '-0.005em')}
                  >
                    {title}
                  </h4>
                  <p
                    className="text-foreground/85 leading-relaxed"
                    style={humaneStyle(19, 500, '0')}
                  >
                    {desc}
                  </p>
                </motion.div>
              ))}
            </div>

          </div>
        </div>
      </section>

      {/* ─── 05 / PRICING ───────────────────────────────────────────────── */}
      <section
        id="pricing"
        className={`border-t ${borderFaint} py-32 scroll-mt-20`}
      >
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-16 lg:gap-24">

            {/* LEFT — sticky heading */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
            >
              <SplitHeading
                number="05"
                label="PRICING"
                title={<>Freemium +<br />credits. <em className="font-normal italic">No</em><br />surprises.</>}
                subtitle="Start free with a monthly allowance built for real job-search volume."
              />
            </motion.div>

            {/* RIGHT — 2 pricing cards, side-by-side on sm+, stacked on mobile */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-0 border border-foreground/10 self-start">

              {/* Free tier */}
              <motion.div
                initial="hidden"
                whileInView="visible"
                variants={scrollReveal}
                viewport={viewport}
                className="p-10 border-b sm:border-b-0 sm:border-r border-foreground/10"
              >
                <div
                  className="uppercase text-foreground/80 mb-6"
                  style={humaneStyle(15, 700, '0.2em')}
                >
                  FREE
                </div>
                <div
                  className="text-foreground font-normal mb-1 leading-none"
                  style={frauncesStyle('clamp(36px, 4vw, 56px)', 400, '-0.02em')}
                >
                  90 credits
                </div>
                <div
                  className="text-foreground/80 mb-8"
                  style={humaneStyle(19, 500, '0')}
                >
                  per month, always
                </div>
                <ul className="space-y-3">
                  {[
                    'About 30 JD tailor-and-export workflows',
                    'ATS raw-text simulator',
                    'All 6 PDF export templates',
                    'JD diff with per-change accept'
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-3">
                      <CheckCircle size={13} className="text-foreground/40 shrink-0" strokeWidth={1.5} />
                      <span
                        className="text-foreground/60"
                        style={humaneStyle(19, 500, '0')}
                      >
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              </motion.div>

              {/* Freemium launch */}
              <motion.div
                initial="hidden"
                whileInView="visible"
                variants={scrollReveal}
                viewport={viewport}
                className="p-10 bg-foreground/[0.03]"
              >
                <div
                  className="uppercase text-foreground/80 mb-6"
                  style={humaneStyle(15, 700, '0.2em')}
                >
                  LAUNCH
                </div>
                <div
                  className="text-foreground font-normal mb-1 leading-none"
                  style={frauncesStyle('clamp(36px, 4vw, 56px)', 400, '-0.02em')}
                >
                  Freemium first
                </div>
                <div
                  className="text-foreground/80 mb-8"
                  style={humaneStyle(19, 500, '0')}
                >
                  paid plans are on hold
                </div>
                <p
                  className="text-foreground/85 leading-relaxed mb-8"
                  style={humaneStyle(19, 500, '0')}
                >
                  We are keeping launch freemium-only while we validate resume quality, layout fit, and JD-tailoring accuracy with real users.
                </p>
                <Link href="/login">
                  <button
                    className="inline-flex items-center gap-2 px-6 py-3 bg-foreground text-background uppercase transition-opacity hover:opacity-80"
                    style={humaneStyle(16, 700, '0.14em')}
                  >
                    Get Started Free <ArrowRight size={13} />
                  </button>
                </Link>
              </motion.div>

            </div>

          </div>
        </div>
      </section>

      {/* ─── 06 / FAQ ───────────────────────────────────────────────────── */}
      <section
        id="faq"
        className={`border-t ${borderFaint} py-32 scroll-mt-20`}
      >
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-16 lg:gap-24">

            {/* LEFT — sticky heading */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
            >
              <SplitHeading
                number="06"
                label="FAQ"
                title={<>Straight<br /><em className="font-normal italic">answers.</em></>}
                subtitle="Questions we get from engineers who have tried every other resume tool."
              />
            </motion.div>

            {/* RIGHT — single-column FAQ list, 1px bottom-border each */}
            <div>
              {FAQS.map(({ q, a }, i) => (
                <motion.div
                  key={q}
                  initial="hidden"
                  whileInView="visible"
                  variants={scrollReveal}
                  viewport={viewport}
                  style={{ transitionDelay: `${i * 60}ms` }}
                  className={`py-8 ${i < FAQS.length - 1 ? `border-b ${borderFaint}` : ''}`}
                >
                  <h4
                    className="text-foreground mb-4 font-normal"
                    style={frauncesStyle('clamp(17px, 1.6vw, 22px)', 500, '-0.005em')}
                  >
                    {q}
                  </h4>
                  <p
                    className="text-foreground/85 leading-relaxed"
                    style={humaneStyle(19, 500, '0')}
                  >
                    {a}
                  </p>
                </motion.div>
              ))}
            </div>

          </div>
        </div>
      </section>

      {/* ─── FINAL CTA ──────────────────────────────────────────────────── */}
      <section className={`py-40 px-8 border-t ${borderFaint} bg-foreground/[0.02]`}>
        <motion.div
          initial="hidden"
          whileInView="visible"
          variants={scrollReveal}
          viewport={viewport}
          className="max-w-[1400px] mx-auto flex flex-col items-center text-center"
        >
          <h2
            className="text-foreground font-normal mb-8 leading-[0.95]"
            style={{
              fontFamily: 'var(--font-fraunces), Georgia, serif',
              fontSize: 'clamp(40px, 6vw, 88px)',
              letterSpacing: '-0.01em',
              fontWeight: 400,
            }}
          >
            Make every application version<br />
            <em className="font-normal opacity-60">intentional.</em>
          </h2>
          <p
            className="text-foreground/50 mb-12 max-w-md leading-relaxed"
            style={humaneStyle(20, 500, '0')}
          >
            Upload your resume, tailor it to a real JD, and keep only the changes you trust.
          </p>
          <Link href="/login">
            <button
              className="inline-flex items-center gap-2 px-8 py-4 bg-foreground text-background uppercase transition-opacity hover:opacity-80 mb-8"
              style={humaneStyle(16, 700, '0.14em')}
            >
              Start Free <ArrowRight size={14} />
            </button>
          </Link>
          <span
            className="text-foreground/30 uppercase"
            style={humaneStyle(15, 700, '0.2em')}
          >
            PRISM PRO. — TRUTHFUL RESUME TAILORING
          </span>
        </motion.div>
      </section>

      {/* ─── BOTTOM DARK BAND ────────────────────────────────────────────── */}
      <div className="h-[14px] w-full" style={{ backgroundColor: '#1a1a1a' }} />

      {/* ─── FOOTER ─────────────────────────────────────────────────────── */}
      <footer className={`py-16 px-8 border-t ${borderFaint}`}>
        <div className="max-w-[1400px] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
            {/* Wordmark column */}
            <div className="md:col-span-1">
              <span
                className="block mb-4 uppercase text-foreground"
                style={humaneStyle(16, 600, '0.15em')}
              >
                PRISM PRO.
              </span>
              <p
                className="text-foreground/80 leading-relaxed"
                style={humaneStyle(16, 500, '0.01em')}
              >
                Truthful JD-specific resume tailoring for technical professionals. Built for focused applications, ATS-aware exports, and interview-ready version history.
              </p>
            </div>

            {/* Product */}
            <div>
              <h5
                className="uppercase text-foreground mb-5"
                style={humaneStyle(15, 700, '0.2em')}
              >
                PRODUCT
              </h5>
              <ul className="space-y-3">
                {[
                  { label: 'How It Works', action: () => { const el = document.getElementById('how-it-works'); if (el) el.scrollIntoView({ behavior: 'smooth' }); } },
                  { label: 'Features', action: () => { const el = document.getElementById('features'); if (el) el.scrollIntoView({ behavior: 'smooth' }); } },
                  { label: 'Pricing', action: () => { const el = document.getElementById('pricing'); if (el) el.scrollIntoView({ behavior: 'smooth' }); } },
                ].map(({ label, action }) => (
                  <li key={label}>
                    <button
                      onClick={action}
                      className="text-foreground/75 hover:text-foreground transition-colors"
                      style={humaneStyle(16, 500, '0.01em')}
                    >
                      {label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h5
                className="uppercase text-foreground mb-5"
                style={humaneStyle(15, 700, '0.2em')}
              >
                RESOURCES
              </h5>
              <ul className="space-y-3">
                <li>
                  <Link href="/docs" className="text-foreground/75 hover:text-foreground transition-colors" style={humaneStyle(16, 500, '0.01em')}>
                    Docs
                  </Link>
                </li>
                <li>
                  <button
                    onClick={() => { const el = document.getElementById('faq'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}
                    className="text-foreground/75 hover:text-foreground transition-colors"
                    style={humaneStyle(16, 500, '0.01em')}
                  >
                    FAQ
                  </button>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h5
                className="uppercase text-foreground mb-5"
                style={humaneStyle(15, 700, '0.2em')}
              >
                LEGAL
              </h5>
              <ul className="space-y-3">
                <li>
                  <Link href="/privacy-policy" className="text-foreground/75 hover:text-foreground transition-colors" style={humaneStyle(16, 500, '0.01em')}>
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="text-foreground/75 hover:text-foreground transition-colors" style={humaneStyle(16, 500, '0.01em')}>
                    Terms of Service
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom row */}
          <div className={`pt-8 border-t ${borderFaint} flex flex-col md:flex-row justify-between items-center gap-4`}>
            <span
              className="text-foreground/30 uppercase"
              style={humaneStyle(15, 700, '0.2em')}
            >
              &copy; 2026 PRISM PRO. ALL RIGHTS RESERVED.
            </span>
            <span
              className="text-foreground/30 uppercase"
              style={humaneStyle(15, 700, '0.2em')}
            >
              PRISMPRO.LIVE
            </span>
            {/* Locale switch placeholder */}
            <span
              className="text-foreground/20 uppercase cursor-default"
              style={humaneStyle(15, 700, '0.2em')}
            >
              EN / IN
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

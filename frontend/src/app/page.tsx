"use client";

import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
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

  const fadeIn = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { duration: 0.7, ease: [0.17, 0.55, 0.55, 1] as [number, number, number, number] }
        }
      };

  const fadeInUp = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 20 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.7, ease: [0.17, 0.55, 0.55, 1] as [number, number, number, number] }
        }
      };

  const staggerContainer = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: 0.12, delayChildren: 0.05 }
        }
      };

  const scrollReveal = reduce
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
    desc: 'PDF or DOCX. We extract every bullet, skill, and section without losing structure.'
  },
  {
    icon: ScanText,
    step: '02',
    title: 'Senior-recruiter critique',
    desc: 'Bullet-level severity flags — Strong, Weak, Vague Impact — the same lens a hiring manager uses in 7 seconds.'
  },
  {
    icon: FileDiff,
    step: '03',
    title: 'JD-driven tailoring',
    desc: 'Paste any job description. Review a diff of AI-proposed rewrites and accept changes one by one.'
  },
  {
    icon: Download,
    step: '04',
    title: 'Recruiter-grade PDF export',
    desc: 'Six templates (SWE · DS · PM) × (USA · India). Export the format that matches the market.'
  }
];

const PROBLEMS = [
  {
    stat: '75%',
    label: 'of resumes are rejected before a human reads them',
    detail: 'ATS systems filter on keyword match and parse quality, not on your actual experience.'
  },
  {
    stat: '7 sec',
    label: 'is how long a recruiter spends on first pass',
    detail: 'Weak opening bullets and buried impact metrics cost you before the conversation starts.'
  },
  {
    stat: '1 size',
    label: 'does not fit all — US and India formats differ',
    detail: 'US recruiters expect a tight 1-page resume. Indian hiring teams expect a longer structured CV.'
  }
];

const FEATURES = [
  {
    title: 'Bullet-level severity scoring',
    desc: 'Each bullet is flagged Strong, Weak, or Vague Impact — no five-paragraph rubric, just the same signal a senior recruiter marks on paper.'
  },
  {
    title: 'ATS raw-text simulator',
    desc: 'See your resume as an ATS parser sees it. Tables, multi-column layouts, and special characters are called out before they cost you a screen.'
  },
  {
    title: 'JD diff with per-change accept',
    desc: 'Paste a job description and review a structured diff. Accept rewrites bullet by bullet or all at once — you stay in control.'
  },
  {
    title: 'Placeholder-hybrid rewrites',
    desc: "Numbers you can't verify appear as [X%] or [N users]. Verbs, structure, and framing are rewritten. The output reads like a recruiter wrote it."
  },
  {
    title: 'Country + role templates',
    desc: 'Six export templates — SWE, DS, PM in USA and India formats — rendered to PDF via Puppeteer to match recruiter expectations in each market.'
  },
  {
    title: 'Transparent credit system',
    desc: '20 free credits per month covers two full evaluation-and-tailor cycles. Top up as needed, no subscription lock-in.'
  }
];

const FAQS = [
  {
    q: 'How is this different from Rezi or Teal?',
    a: "Most resume tools score your resume against a rubric and produce generic AI-written bullets. Prism Pro surfaces bullet-level severity flags the same way a senior recruiter would mark your resume by hand, then proposes rewrites in a diff view so you accept or reject every change."
  },
  {
    q: 'Will the AI hallucinate my experience or invent metrics?',
    a: "No. Hard numbers that the AI cannot verify are replaced with typed placeholders like [X%] or [$Y]. Only verb choice, sentence structure, and framing are rewritten. Every proposed change is shown in a diff view before it is applied."
  },
  {
    q: 'Which ATS systems does it test against?',
    a: "The simulator tests against the core parser behaviours shared by Workday, Greenhouse, Lever, and iCIMS: multi-column rejection, table parsing, header/footer stripping, and special-character handling."
  },
  {
    q: 'Why do you have different templates for the USA and India?',
    a: "US hiring conventions expect a one-page, tightly scoped resume. Indian hiring teams typically expect a 2-3 page structured CV with education placed prominently and a profile summary at the top."
  },
  {
    q: 'How are credits priced?',
    a: "Every account starts with 20 free credits per month. One full evaluation-and-tailor cycle costs 10 credits. Top-up packs are available; pricing is shown in the dashboard."
  },
  {
    q: 'Is my resume data stored securely?',
    a: "All documents are stored in Supabase with Row-Level Security — your data is only accessible to your account. You can delete your data at any time from the account settings."
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
  fontFamily: 'var(--font-ibm-plex-sans), system-ui, sans-serif',
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
  const { fadeIn, fadeInUp, staggerContainer, scrollReveal, reduce } = useMotionVariants();

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
                style={{ fontFamily: 'var(--font-ibm-plex-sans), system-ui, sans-serif', fontSize: '22px', fontWeight: 700, letterSpacing: '0.22em', lineHeight: 1 }}
              >
                RECRUITER-GRADE — 2026
              </span>
              <div className="w-10 h-[1px] bg-foreground/60" aria-hidden="true" />
            </motion.div>

            {/* Body copy — IBM Plex Sans for paragraph readability */}
            <motion.p
              variants={fadeInUp}
              className="text-foreground leading-relaxed mb-12"
              style={{ fontFamily: 'var(--font-ibm-plex-sans), system-ui, sans-serif', fontSize: '24px', fontWeight: 400, lineHeight: '1.5', maxWidth: '600px' }}
            >
              Bullet-level resume critique. JD-driven tailoring.{' '}
              <span
                className="text-foreground uppercase"
                style={{ fontFamily: 'var(--font-ibm-plex-sans), system-ui, sans-serif', fontSize: '26px', fontWeight: 700, letterSpacing: '0.05em' }}
              >
                Recruiter&#8209;grade
              </span>{' '}
              PDF export for USA and India markets.
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
                  Polish Your Resume <ArrowRight size={16} />
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
            {/* Display H1 — massive Fraunces, two lines, left-aligned */}
            <motion.h1
              variants={fadeInUp}
              className="text-foreground font-normal leading-[0.95] mb-10"
              style={{
                fontFamily: 'var(--font-fraunces), Georgia, serif',
                fontSize: 'clamp(64px, 11vw, 180px)',
                letterSpacing: '-0.02em',
                fontWeight: 400,
              }}
            >
              PRISM
              <br />
              PRO.
            </motion.h1>

            {/* Decorative circle — editorial accent */}
            <motion.div
              variants={fadeInUp}
              aria-hidden="true"
              className="w-24 h-24 rounded-full border border-foreground/20"
            />
          </motion.div>
        </div>
      </section>

      {/* ─── SOCIAL PROOF STRIP ──────────────────────────────────────────── */}
      {/* REPLACE: add real company logos when available */}
      <section className={`py-10 px-8 border-y ${borderFaint}`}>
        <div className="max-w-[1400px] mx-auto">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <span
              className="text-foreground/35 uppercase"
              style={humaneStyle(15, 700, '0.2em')}
            >
              USED BY ENGINEERS FROM
            </span>
            <div className="flex flex-wrap items-center gap-10">
              {['Stripe', 'Razorpay', 'Flipkart', 'Spotify', 'Amazon', 'Thoughtworks'].map((name) => (
                <span
                  key={name}
                  className="text-foreground/25 uppercase"
                  style={humaneStyle(18, 700, '0.06em')}
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>
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
                subtitle="It is how your experience is presented. Three structural failures cause most rejections before a hiring manager ever reads your name."
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
                title={<>Four steps from<br />upload to<br /><em className="font-normal not-italic">recruiter-ready.</em></>}
                subtitle="Every step is designed for experienced professionals who know what their resume needs — and want to act on it fast."
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
                title={<>Every tool built around what recruiters<br /><em className="font-normal italic">actually</em> look for.</>}
                subtitle="Not a generic AI wrapper. Each feature maps directly to a documented hiring-team behaviour or ATS failure mode."
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
                title={<>Six tools.<br />One<br /><em className="font-normal italic">coherent</em><br />workflow.</>}
                subtitle="Each capability addresses a specific, documented point of failure in the application process."
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
                subtitle="Start for free. Pay only when you need more evaluations or exports."
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
                  20 credits
                </div>
                <div
                  className="text-foreground/80 mb-8"
                  style={humaneStyle(19, 500, '0')}
                >
                  per month, always
                </div>
                <ul className="space-y-3">
                  {[
                    '2 full evaluation-and-tailor cycles',
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

              {/* Credit top-up */}
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
                  TOP-UP
                </div>
                <div
                  className="text-foreground font-normal mb-1 leading-none"
                  style={frauncesStyle('clamp(36px, 4vw, 56px)', 400, '-0.02em')}
                >
                  Buy credits
                </div>
                <div
                  className="text-foreground/80 mb-8"
                  style={humaneStyle(19, 500, '0')}
                >
                  when you need them — no subscription
                </div>
                <p
                  className="text-foreground/85 leading-relaxed mb-8"
                  style={humaneStyle(19, 500, '0')}
                >
                  {/* REPLACE: Add real pricing tiers when Stripe integration ships */}
                  Credit pack pricing will be shown in-dashboard. Top-ups are one-time purchases — no recurring charge, no lock-in.
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
            Your resume reviewed by a<br />
            <em className="font-normal opacity-60">senior recruiter in minutes.</em>
          </h2>
          <p
            className="text-foreground/50 mb-12 max-w-md leading-relaxed"
            style={humaneStyle(20, 500, '0')}
          >
            Join engineers and product professionals who prep smarter, not longer.
          </p>
          <Link href="/login">
            <button
              className="inline-flex items-center gap-2 px-8 py-4 bg-foreground text-background uppercase transition-opacity hover:opacity-80 mb-8"
              style={humaneStyle(16, 700, '0.14em')}
            >
              Polish Your Resume <ArrowRight size={14} />
            </button>
          </Link>
          <span
            className="text-foreground/30 uppercase"
            style={humaneStyle(15, 700, '0.2em')}
          >
            PRISM PRO. — RECRUITER-GRADE RESUME PREP
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
                Recruiter-grade resume tailoring for experienced engineers and product professionals. Built for USA and India markets.
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

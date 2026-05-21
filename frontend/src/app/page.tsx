"use client";

import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  Upload,
  ScanText,
  FileDiff,
  Download,
  ChevronDown,
  BookOpen,
  CheckCircle
} from 'lucide-react';
import Link from 'next/link';

import { Navigation } from '@/components/landing/Navigation';
import { StyledButton } from '@/components/landing/StyledButton';
import { SectionHeader } from '@/components/landing/SectionHeader';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { useTheme } from '@/contexts/theme-context';

// Build animation variants respecting prefers-reduced-motion.
// When reduced motion is requested every variant resolves to a no-op so
// the page is fully accessible without forking every JSX element.
function useMotionVariants() {
  const reduce = useReducedMotion();

  const fadeInUp = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 24 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.6, ease: [0.17, 0.55, 0.55, 1] as [number, number, number, number] }
        }
      };

  const staggerContainer = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: 0.15, delayChildren: 0.1 }
        }
      };

  const scrollReveal = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } }
      };

  return { fadeInUp, staggerContainer, scrollReveal, reduce };
}

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
    detail: 'US recruiters expect a tight 1-page resume. Indian hiring teams expect a longer structured CV. Most tools ignore this.'
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
    desc: 'Numbers you can\'t verify appear as [X%] or [N users]. Verbs, structure, and framing are rewritten. The output reads like a recruiter wrote it.'
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
    a: 'Most resume tools score your resume against a rubric and produce generic AI-written bullets. Prism Pro surfaces bullet-level severity flags the same way a senior recruiter would mark your resume by hand, then proposes rewrites in a diff view so you accept or reject every change. The output does not read machine-generated because numbers that can\'t be verified are preserved as placeholders — you fill them in.'
  },
  {
    q: 'Will the AI hallucinate my experience or invent metrics?',
    a: 'No. Hard numbers (percentages, team sizes, revenue figures) that the AI cannot verify are replaced with typed placeholders like [X%] or [$Y]. Only verb choice, sentence structure, and framing are rewritten. Every proposed change is shown in a diff view before it is applied.'
  },
  {
    q: 'Which ATS systems does it test against?',
    a: 'The simulator tests against the core parser behaviours shared by Workday, Greenhouse, Lever, and iCIMS: multi-column rejection, table parsing, header/footer stripping, and special-character handling. It generates a raw-text preview so you can read what the parser actually extracts.'
  },
  {
    q: 'Why do you have different templates for the USA and India?',
    a: 'US hiring conventions expect a one-page, tightly scoped resume. Indian hiring teams and MNC Indian offices typically expect a 2-3 page structured CV with education placed prominently and a profile summary at the top. Using the wrong format in the wrong market creates friction before anyone reads your content.'
  },
  {
    q: 'How are credits priced?',
    a: 'Every account starts with 20 free credits per month. One full evaluation-and-tailor cycle (upload → critique → JD tailor → export) costs 10 credits. Top-up packs are available; pricing is shown in the dashboard once the credit system ships in the next release.'
  },
  {
    q: 'Is my resume data stored securely?',
    a: 'All documents are stored in Supabase with Row-Level Security — your data is only accessible to your account. Google OAuth authentication is fully verified by Google under their Limited Use Policy. You can delete your data at any time from the account settings.'
  }
];

export default function LandingPage() {
  const { isDark } = useTheme();
  const { fadeInUp, staggerContainer, scrollReveal, reduce } = useMotionVariants();

  const borderFaint = isDark ? 'border-white/8' : 'border-black/8';
  const surfaceFaint = isDark ? 'bg-white/5' : 'bg-black/5';

  // Viewport config for scroll-reveal sections
  const viewport = { once: true, margin: '-100px' } as const;

  return (
    <div className="relative min-h-screen transition-colors duration-300 scroll-smooth bg-background text-foreground">
      <div className="grain-overlay" />

      <Navigation />

      {/* ─── HERO ────────────────────────────────────────────────────────── */}
      <section id="hero" className="relative pt-44 pb-32 px-6">
        {/* Ambient radial gradient — slow drift, stays behind content */}
        {!reduce && (
          <motion.div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 2 }}
          >
            <motion.div
              className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] rounded-full"
              style={{
                background: isDark
                  ? 'radial-gradient(ellipse at center, hsl(18 50% 56% / 0.07) 0%, transparent 70%)'
                  : 'radial-gradient(ellipse at center, hsl(18 52% 48% / 0.06) 0%, transparent 70%)'
              }}
              animate={{ y: [0, -18, 0], x: [0, 10, 0] }}
              transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
            />
          </motion.div>
        )}
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="flex flex-col items-center text-center"
          >
            {/* Badge */}
            <motion.div
              variants={fadeInUp}
              className={`mb-8 inline-flex items-center gap-2 px-4 py-1.5 rounded-full border ${borderFaint} ${surfaceFaint} text-[11px] font-semibold tracking-[0.15em] opacity-70 uppercase`}
            >
              Hand-tuned by senior recruiters · AI-powered, human-validated
            </motion.div>

            {/* H1 — Fraunces serif display */}
            <motion.h1
              variants={fadeInUp}
              className="text-5xl md:text-7xl font-bold tracking-tight mb-7 max-w-4xl leading-[1.05]"
              style={{ fontFamily: 'var(--font-fraunces), serif' }}
            >
              Recruiter-Grade<br />
              <span className="italic font-normal opacity-60">Resume Prep</span>
            </motion.h1>

            {/* Subhead */}
            <motion.p
              variants={fadeInUp}
              className="opacity-65 text-lg md:text-xl max-w-xl mb-12 leading-relaxed"
            >
              Paste a job description. See bullet-level rewrites in a diff view. Export a PDF template recruiters in the USA or India actually expect.
            </motion.p>

            {/* CTAs */}
            <motion.div
              variants={fadeInUp}
              className="flex flex-col sm:flex-row items-center gap-5"
            >
              <motion.div whileTap={reduce ? {} : { scale: 0.97 }} transition={{ duration: 0.1 }}>
                <Link href="/login">
                  <StyledButton isDark={isDark}>
                    Polish Your Resume <ArrowRight size={15} />
                  </StyledButton>
                </Link>
              </motion.div>
              <motion.div whileTap={reduce ? {} : { scale: 0.97 }} transition={{ duration: 0.1 }}>
                <button
                  onClick={() => {
                    const el = document.getElementById('how-it-works');
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  <StyledButton variant="secondary" isDark={isDark} className="min-w-[150px]">
                    <div className="flex items-center gap-2">
                      <ChevronDown className="w-4 h-4" />
                      <span>See How It Works</span>
                    </div>
                  </StyledButton>
                </button>
              </motion.div>
            </motion.div>

            {/* Hero product screenshot */}
            <motion.div
              variants={fadeInUp}
              className={`mt-20 w-full max-w-5xl aspect-[16/9] bg-muted rounded-sm border ${borderFaint} relative overflow-hidden group shadow-xl`}
            >
              <div className={`absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10`} />
              {/* <Image src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=1600&q=80" alt="Prism Pro resume evaluation interface" className="w-full h-full object-cover" /> */}
              <div className="absolute inset-0 flex items-center justify-center z-20">
                <div className={`px-6 py-3 rounded-sm border ${borderFaint} ${surfaceFaint} backdrop-blur-sm`}>
                  <span className="text-xs font-mono opacity-50 tracking-widest uppercase">[ dashboard preview coming soon ]</span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ─── SOCIAL PROOF STRIP ──────────────────────────────────────────── */}
      {/* <!-- REPLACE THIS SECTION when real logos or review data is available --> */}
      <section className={`py-10 px-6 border-y ${borderFaint} ${surfaceFaint}`}>
        <div className="max-w-5xl mx-auto text-center">
          <p className="text-[11px] font-semibold tracking-[0.2em] uppercase opacity-40 mb-6">
            Used by engineers from
          </p>
          <div className="flex flex-wrap items-center justify-center gap-10 opacity-30">
            {['Stripe', 'Razorpay', 'Flipkart', 'Spotify', 'Amazon Web Services', 'Thoughtworks'].map((name) => (
              <span key={name} className="text-sm font-semibold tracking-wide">{name}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PROBLEM STATEMENT ──────────────────────────────────────────── */}
      <section
        id="problem"
        className={`py-32 px-6 border-b ${borderFaint} scroll-mt-20`}
      >
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            label="Why most resumes fail"
            title="The problem is not your experience."
            subtitle="It is how your experience is presented. Three structural failures cause most rejections before a hiring manager ever reads your name."
          />
          <div className="grid md:grid-cols-3 gap-8 mt-8">
            {PROBLEMS.map(({ stat, label, detail }) => (
              <motion.div
                key={stat}
                initial="hidden"
                whileInView="visible"
                variants={scrollReveal}
                viewport={viewport}
                className={`p-8 border ${borderFaint} rounded-sm`}
              >
                <div
                  className="text-5xl font-bold mb-4 text-primary"
                  style={{ fontFamily: 'var(--font-fraunces), serif' }}
                >
                  {stat}
                </div>
                <h4 className="font-semibold mb-3 leading-snug">{label}</h4>
                <p className="text-sm opacity-60 leading-relaxed">{detail}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ───────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-32 px-6 scroll-mt-20">
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            label="The workflow"
            title="Four steps from upload to recruiter-ready."
            subtitle="Every step is designed for experienced professionals who know what their resume needs — and want to act on it fast."
          />
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8">
            {STEPS.map(({ icon: Icon, step, title, desc }) => (
              <motion.div
                key={step}
                initial="hidden"
                whileInView="visible"
                variants={scrollReveal}
                viewport={viewport}
                className={`p-7 border ${borderFaint} rounded-sm flex flex-col gap-5 group hover:border-primary/30 transition-colors`}
              >
                <div className="flex items-start justify-between">
                  <div className={`w-11 h-11 flex items-center justify-center border ${borderFaint} rounded-sm group-hover:border-primary/30 transition-colors`}>
                    <Icon size={20} className="text-primary" />
                  </div>
                  <span
                    className="text-4xl font-bold opacity-10"
                    style={{ fontFamily: 'var(--font-fraunces), serif' }}
                  >
                    {step}
                  </span>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">{title}</h4>
                  <p className="text-sm opacity-60 leading-relaxed">{desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FEATURE DEEP DIVE (BENTO) ──────────────────────────────────── */}
      <section id="features" className={`py-32 px-6 border-t ${borderFaint} scroll-mt-20`}>
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            label="Feature detail"
            title="Every tool is built around what recruiters actually look for."
            subtitle="Not a generic AI wrapper. Each feature maps directly to a documented hiring-team behaviour or ATS failure mode."
          />
          <BentoGrid isDark={isDark} />
        </div>
      </section>

      {/* ─── FEATURE LIST ───────────────────────────────────────────────── */}
      <section className={`py-20 px-6 border-t ${borderFaint}`}>
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 lg:grid-cols-3 gap-x-12 gap-y-10">
          {FEATURES.map(({ title, desc }) => (
            <motion.div
              key={title}
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
              className="flex gap-4"
            >
              <CheckCircle size={20} className="shrink-0 mt-1 text-primary opacity-80" />
              <div>
                <h4 className="font-semibold mb-1.5">{title}</h4>
                <p className="text-sm opacity-60 leading-relaxed">{desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── PRICING TEASER ─────────────────────────────────────────────── */}
      <section
        id="pricing"
        className={`py-32 px-6 border-t ${borderFaint} scroll-mt-20`}
      >
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            label="Pricing"
            title="Freemium + credits. No surprises."
            subtitle="Start for free. Pay only when you need more evaluations or exports."
          />
          <div className="grid md:grid-cols-2 gap-8 max-w-3xl">
            {/* Free tier */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              variants={scrollReveal}
              viewport={viewport}
              className={`p-8 border ${borderFaint} rounded-sm`}
            >
              <div className="text-xs font-bold tracking-[0.2em] uppercase opacity-50 mb-4">Free</div>
              <div
                className="text-4xl font-bold mb-1"
                style={{ fontFamily: 'var(--font-fraunces), serif' }}
              >
                20 credits
              </div>
              <div className="text-sm opacity-50 mb-6">per month, always</div>
              <ul className="space-y-3 text-sm opacity-70">
                {[
                  '2 full evaluation-and-tailor cycles',
                  'ATS raw-text simulator',
                  'All 6 PDF export templates',
                  'JD diff with per-change accept'
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3">
                    <CheckCircle size={14} className="text-primary shrink-0" />
                    {item}
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
              className={`p-8 border border-primary/30 bg-primary/5 rounded-sm`}
            >
              <div className="text-xs font-bold tracking-[0.2em] uppercase text-primary/70 mb-4">Top-up</div>
              <div
                className="text-4xl font-bold mb-1"
                style={{ fontFamily: 'var(--font-fraunces), serif' }}
              >
                Buy credits
              </div>
              <div className="text-sm opacity-50 mb-6">when you need them — no subscription</div>
              <p className="text-sm opacity-60 leading-relaxed">
                {/* REPLACE: Add real pricing tiers when Stripe integration ships */}
                Credit pack pricing will be shown in-dashboard. Top-ups are one-time purchases — no recurring charge, no lock-in.
              </p>
              <div className="mt-6">
                <motion.div whileTap={reduce ? {} : { scale: 0.97 }} transition={{ duration: 0.1 }}>
                  <Link href="/login">
                    <StyledButton isDark={isDark}>
                      Get Started Free <ArrowRight size={14} />
                    </StyledButton>
                  </Link>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── FAQ ────────────────────────────────────────────────────────── */}
      <section
        id="faq"
        className={`py-32 px-6 border-t ${borderFaint} scroll-mt-20`}
      >
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            label="FAQ"
            title="Straight answers."
            subtitle="Questions we get from engineers who have tried every other resume tool."
          />
          <div className="grid md:grid-cols-2 gap-x-16 gap-y-12 max-w-5xl">
            {FAQS.map(({ q, a }) => (
              <motion.div
                key={q}
                initial="hidden"
                whileInView="visible"
                variants={scrollReveal}
                viewport={viewport}
              >
                <h4 className="font-semibold mb-3">{q}</h4>
                <p className="text-sm opacity-60 leading-relaxed">{a}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FINAL CTA ──────────────────────────────────────────────────── */}
      <section
        className={`py-32 px-6 border-t ${borderFaint}`}
      >
        <motion.div
          initial="hidden"
          whileInView="visible"
          variants={scrollReveal}
          viewport={viewport}
          className="max-w-3xl mx-auto flex flex-col items-center text-center"
        >
          <h2
            className="text-4xl md:text-5xl font-bold tracking-tight mb-6 leading-tight"
            style={{ fontFamily: 'var(--font-fraunces), serif' }}
          >
            Your resume reviewed by a<br />
            <span className="italic font-normal opacity-60">senior recruiter in minutes.</span>
          </h2>
          <p className="opacity-60 mb-10 leading-relaxed max-w-lg">
            Join engineers and product professionals who prep smarter, not longer.
          </p>
          <motion.div whileTap={reduce ? {} : { scale: 0.97 }} transition={{ duration: 0.1 }}>
            <Link href="/login">
              <StyledButton isDark={isDark}>
                Polish Your Resume <ArrowRight size={16} />
              </StyledButton>
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* ─── FOOTER ─────────────────────────────────────────────────────── */}
      <footer
        className={`py-16 px-6 border-t ${borderFaint}`}
      >
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="max-w-sm">
            {/* Wordmark */}
            <div className="mb-5">
              <span
                className="font-bold tracking-tight text-xl text-foreground"
                style={{ fontFamily: 'var(--font-fraunces), serif' }}
              >
                Prism <span className="italic font-normal opacity-70">Pro</span>
              </span>
            </div>
            <p className="opacity-45 text-sm leading-relaxed">
              Recruiter-grade resume tailoring for experienced engineers and product professionals. Built for USA and India markets.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-14">
            <div>
              <h5 className="text-[10px] font-bold tracking-[0.2em] uppercase mb-5 opacity-100">Product</h5>
              <ul className="text-sm opacity-50 space-y-3">
                <li className="hover:opacity-100 transition-opacity">
                  <button onClick={() => { const el = document.getElementById('how-it-works'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}>
                    How It Works
                  </button>
                </li>
                <li className="hover:opacity-100 transition-opacity">
                  <button onClick={() => { const el = document.getElementById('features'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}>
                    Features
                  </button>
                </li>
                <li className="hover:opacity-100 transition-opacity">
                  <button onClick={() => { const el = document.getElementById('pricing'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}>
                    Pricing
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h5 className="text-[10px] font-bold tracking-[0.2em] uppercase mb-5 opacity-100">Resources</h5>
              <ul className="text-sm opacity-50 space-y-3">
                <li className="hover:opacity-100 transition-opacity">
                  <Link href="/docs" className="flex items-center gap-1.5">
                    <BookOpen size={12} /> Docs
                  </Link>
                </li>
                <li className="hover:opacity-100 transition-opacity">
                  <button onClick={() => { const el = document.getElementById('faq'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}>
                    FAQ
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h5 className="text-[10px] font-bold tracking-[0.2em] uppercase mb-5 opacity-100">Legal</h5>
              <ul className="text-sm opacity-50 space-y-3">
                <li className="hover:opacity-100 transition-opacity">
                  <Link href="/privacy-policy">Privacy Policy</Link>
                </li>
                <li className="hover:opacity-100 transition-opacity">
                  <Link href="/terms">Terms of Service</Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className={`max-w-7xl mx-auto mt-16 pt-8 border-t ${borderFaint} flex flex-col md:flex-row justify-between items-center gap-4`}>
          <p className="text-[10px] opacity-35 tracking-widest uppercase">
            &copy; 2026 Prism Pro. All rights reserved.
          </p>
          <p className="text-[10px] opacity-35 tracking-widest uppercase">
            prismpro.live
          </p>
        </div>
      </footer>
    </div>
  );
}

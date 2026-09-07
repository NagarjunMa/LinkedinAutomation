"use client";

import React, { useEffect, useRef } from 'react';
import { motion, MotionConfig, type Variants } from 'framer-motion';
import {
  BookOpenCheck,
  Check,
  FileText,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
  Target,
  UserRoundCheck,
} from 'lucide-react';
import Link from 'next/link';

import { Navigation } from '@/components/landing/Navigation';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { WaitlistForm } from '@/components/landing/WaitlistForm';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useTheme } from '@/contexts/theme-context';
import { trackPublicPreviewEvent } from '@/lib/public-preview-analytics';
import { useHydratedReducedMotion } from '@/hooks/use-hydrated-reduced-motion';

/*
 * Prism Pro landing direction
 * Purpose: introduce the in-development Career Evidence Coach and collect early interest.
 * Audience: students, new graduates, engineers, technical leaders, and career switchers.
 * Aesthetic: refined editorial minimalism — warm paper, ink, oversized condensed type,
 * asymmetric layouts, fine rules, and restrained motion.
 * Typography: Humane for the wordmark/display moments, editorial serif for section titles,
 * and a highly legible sans for body copy.
 * Motion: one staggered hero entrance, quiet scroll reveals, and reduced-motion parity.
 * Spatial system: generous whitespace with sticky editorial headings and structured proof panels.
 */

function useMotionVariants() {
  const reduce = useHydratedReducedMotion();

  const fadeIn: Variants = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { duration: 0.7, ease: [0.17, 0.55, 0.55, 1] },
        },
      };

  const fadeInUp: Variants = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 22 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.7, ease: [0.17, 0.55, 0.55, 1] },
        },
      };

  const staggerContainer: Variants = reduce
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: 0.12, delayChildren: 0.05 },
        },
      };

  const scrollReveal: Variants = reduce
    ? { hidden: { opacity: 1, y: 0 }, visible: { opacity: 1, y: 0 } }
    : {
        hidden: { opacity: 0, y: 16 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.55, ease: 'easeOut' },
        },
      };

  return { fadeIn, fadeInUp, staggerContainer, scrollReveal };
}

const STAGES = [
  'Students',
  'New graduates',
  'Early-career engineers',
  'Experienced ICs',
  'Technical leaders',
  'Career switchers',
  'Returning professionals',
];

const PROBLEMS = [
  {
    marker: 'HIDDEN',
    title: 'Your documents capture only part of the work.',
    detail:
      'Ownership, decisions, constraints, recovery, and impact often surface only when someone asks the right follow-up question.',
  },
  {
    marker: 'GENERIC',
    title: 'Polished AI language can erase the person behind it.',
    detail:
      'When every candidate sounds strategic, scalable, and high-impact, credible technical evidence becomes harder to see.',
  },
  {
    marker: 'SPLIT',
    title: 'Resume, LinkedIn, and interview stories drift apart.',
    detail:
      'A strong application needs one truthful evidence history, expressed differently for each role and each career artifact.',
  },
];

const STEPS = [
  {
    icon: FileText,
    step: '01',
    title: 'Bring what already exists',
    desc: 'Start with a resume, an optional LinkedIn profile PDF, and a short introduction. Your documents are source material—not unquestioned truth.',
  },
  {
    icon: MessagesSquare,
    step: '02',
    title: 'Talk through the work behind the bullets',
    desc: 'Prism Pro will ask one focused question at a time about ownership, technical decisions, constraints, outcomes, and proof.',
  },
  {
    icon: UserRoundCheck,
    step: '03',
    title: 'Decide what is true and usable',
    desc: 'Confirm, edit, reject, mark private, or leave evidence unavailable. The model cannot approve its own assumptions.',
  },
  {
    icon: Target,
    step: '04',
    title: 'Create a role-specific view',
    desc: 'Turn confirmed evidence into a focused resume, LinkedIn recommendations, interview stories, and an honest map of what is still missing.',
  },
];

const CAPABILITIES = [
  {
    title: 'A coach that interviews before it writes',
    desc: 'The planned conversational flow learns your target, stage, history, and evidence before suggesting career material.',
  },
  {
    title: 'One evidence history, many career views',
    desc: 'Keep the complete story once, then create different role views without rewriting your history into contradictions.',
  },
  {
    title: 'Questions that adapt to your career stage',
    desc: 'A student project, an early-career delivery, and a staff-level decision require different evidence—not the same questionnaire.',
  },
  {
    title: 'Gaps explained without a magic score',
    desc: 'Separate communication, evidence, experience, knowledge, positioning, and document limitations instead of hiding them in one number.',
  },
  {
    title: 'Candidate control over every factual claim',
    desc: 'Private, rejected, contradicted, or unavailable evidence stays out of generated material. Unknown metrics stay unknown.',
  },
  {
    title: 'LinkedIn review without LinkedIn automation',
    desc: 'Upload your own profile PDF for review. Prism Pro will not request credentials, scrape the live profile, or post on your behalf.',
  },
];

const RESEARCH_SIGNALS = [
  {
    label: 'SIGNAL 01',
    title: 'Generic polish is not differentiation.',
    body: 'Candidate and recruiter discovery repeatedly points to the same concern: polished resumes can still feel interchangeable when ownership and proof are missing.',
  },
  {
    label: 'SIGNAL 02',
    title: 'The strongest evidence often starts as a conversation.',
    body: 'Projects and roles contain decisions, trade-offs, failures, and recovery stories that rarely survive the first resume draft.',
  },
  {
    label: 'SIGNAL 03',
    title: 'Broad careers need focus, not erasure.',
    body: 'Experienced candidates need a clear target lane while preserving the complete history that supports interviews and future role changes.',
  },
  {
    label: 'SIGNAL 04',
    title: 'Credibility comes from boundaries.',
    body: 'Strong claims are easier to trust when personal ownership, team contribution, measurement, uncertainty, and source evidence are visible.',
  },
];

const BOUNDARIES = [
  'Invent metrics, technologies, employers, ownership, or outcomes.',
  'Ask for LinkedIn credentials, scrape a live profile, or publish changes.',
  'Reduce your career to an unexplained resume or ATS success score.',
  'Promise profile views, interviews, offers, or employment outcomes.',
];

const FAQS = [
  {
    q: 'What is Prism Pro becoming?',
    a: 'Prism Pro is becoming a career-evidence coach for technical candidates. It is designed to uncover truthful work evidence, help you confirm what may be used, and create role-aligned resume, LinkedIn, and interview material from that confirmed evidence.',
  },
  {
    q: 'Can I create an account or enter the dashboard today?',
    a: 'Not yet. Prism Pro is currently in product development, and public account creation and dashboard access are intentionally closed. This site is a preview of the product direction.',
  },
  {
    q: 'Who is it being built for?',
    a: 'The first experience is being designed for students, new graduates, engineers, technical professionals, career switchers, and returning professionals. The questions and evidence priorities will adapt to career stage and target role.',
  },
  {
    q: 'Do I need a finished resume to use it?',
    a: 'No. A resume will be recommended because it gives the interview useful context, but it will not be required. A short introduction and a target role can start the evidence conversation.',
  },
  {
    q: 'How will the LinkedIn review work?',
    a: 'You will be able to upload the PDF generated from your own LinkedIn profile. Prism Pro will compare that snapshot with confirmed evidence and a target role, then prepare copy-ready recommendations for you to review. It will not access or edit your live account.',
  },
  {
    q: 'Will Prism Pro generate achievements for me?',
    a: 'It may help express approved facts more clearly, but it is not designed to manufacture achievements. Evidence starts as proposed, and factual career material can use only evidence that you have confirmed and kept non-private.',
  },
  {
    q: 'Will it guarantee that I pass an ATS or get interviews?',
    a: 'No. Prism Pro can help with truthful communication, role alignment, defensibility, and document parseability. Hiring outcomes also depend on role fit, market conditions, timing, application channel, and employer decisions.',
  },
  {
    q: 'What happens when I join the private preview?',
    a: 'You will join the research and early-access list. No application account will be created. We may contact you about product interviews, prototype feedback, or private-preview availability.',
  },
];

const labelStyle = (
  size: number,
  weight: number = 500,
  tracking: string = '0',
): React.CSSProperties => ({
  fontFamily: 'var(--font-geist-sans), sans-serif',
  fontSize: `${size}px`,
  fontWeight: weight,
  letterSpacing: tracking,
  lineHeight: 1.2,
});

const serifStyle = (
  size: string,
  weight: number = 400,
  tracking: string = '-0.02em',
): React.CSSProperties => ({
  fontFamily: 'var(--font-fraunces), Georgia, serif',
  fontSize: size,
  fontWeight: weight,
  letterSpacing: tracking,
  lineHeight: 1.02,
});

interface SplitHeadingProps {
  number: string;
  label: string;
  title: React.ReactNode;
  subtitle: string;
}

const SplitHeading: React.FC<SplitHeadingProps> = ({ number, label, title, subtitle }) => (
  <div className="self-start lg:sticky lg:top-32">
    <div className="mb-8 uppercase text-foreground/75" style={labelStyle(13, 700, '0.2em')}>
      {number} / {label}
    </div>
    <h2
      className="mb-8 font-normal text-foreground"
      style={serifStyle('clamp(38px, 4.5vw, 72px)', 400)}
    >
      {title}
    </h2>
    <p className="max-w-md text-foreground/75" style={{ fontSize: '20px', lineHeight: 1.6 }}>
      {subtitle}
    </p>
  </div>
);

export default function LandingPage() {
  const { isDark } = useTheme();
  const { fadeIn, fadeInUp, staggerContainer, scrollReveal } = useMotionVariants();
  const reportedScrollDepths = useRef(new Set<number>());
  const viewport = { once: true, margin: '-80px' } as const;
  const borderFaint = 'border-foreground/10';

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    let scheduled = false;
    const thresholds = [25, 50, 75, 100] as const;

    const reportScrollDepth = () => {
      scheduled = false;
      const scrollableHeight = document.documentElement.scrollHeight;
      if (scrollableHeight <= 0) return;

      const depth = Math.min(
        100,
        Math.round(((window.scrollY + window.innerHeight) / scrollableHeight) * 100),
      );
      thresholds.forEach((threshold) => {
        if (depth >= threshold && !reportedScrollDepths.current.has(threshold)) {
          reportedScrollDepths.current.add(threshold);
          trackPublicPreviewEvent({
            event_name: 'scroll_depth',
            scroll_depth: threshold,
          });
        }
      });
    };

    const onScroll = () => {
      if (scheduled) return;
      scheduled = true;
      window.requestAnimationFrame(reportScrollDepth);
    };

    reportScrollDepth();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Framer's media-query read can differ between SSR and hydration. Motion
  // reduction is applied through useHydratedReducedMotion after hydration.
  return (
    <MotionConfig reducedMotion="never">
      <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <Navigation />

      <main>
        <section id="hero" className="relative min-h-screen pt-[88px]">
          <div className="pointer-events-none absolute inset-0 opacity-[0.16] [background-image:radial-gradient(circle_at_1px_1px,currentColor_1px,transparent_0)] [background-size:28px_28px]" aria-hidden="true" />
          <div className="relative mx-auto grid min-h-[calc(100vh-88px)] max-w-[1400px] grid-cols-1 px-6 sm:px-8 lg:grid-cols-[0.92fr_1.08fr]">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
              className="order-2 flex flex-col justify-center border-foreground/10 py-12 lg:order-1 lg:border-r lg:py-16 lg:pr-20"
            >
              <motion.div variants={fadeInUp} className="mb-9 flex flex-wrap items-center gap-3">
                <Badge
                  variant="outline"
                  className="rounded-none border-foreground/25 px-3 py-1.5 uppercase text-foreground"
                  style={labelStyle(11, 700, '0.18em')}
                >
                  Private preview in development
                </Badge>
                <span className="text-foreground/70" style={labelStyle(12, 600, '0.08em')}>
                  PUBLIC ACCESS CLOSED
                </span>
              </motion.div>

              <motion.p
                variants={fadeInUp}
                className="mb-10 max-w-[620px] text-foreground"
                style={{ fontSize: 'clamp(21px, 1.8vw, 28px)', lineHeight: 1.5 }}
              >
                Prism Pro is the career-evidence coach for technical candidates. It uncovers
                the work your resume and LinkedIn miss, lets you verify every fact, and prepares
                role-aligned career material without inventing experience.
              </motion.p>

              <motion.div variants={fadeInUp} className="mb-7 max-w-[640px]">
                <WaitlistForm compact formLabel="Join the PrismPro private preview from the hero" />
              </motion.div>

              <motion.div variants={fadeInUp} className="mb-8">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => scrollTo('how-it-works')}
                  className="h-auto min-h-12 rounded-none border-foreground/35 bg-transparent px-7 py-3.5 text-foreground shadow-none hover:bg-foreground/5 hover:text-foreground"
                  style={labelStyle(13, 700, '0.13em')}
                >
                  See how it will work
                </Button>
              </motion.div>

              <motion.div variants={fadeIn} className="flex items-center gap-3 text-foreground/70">
                <ShieldCheck size={16} strokeWidth={1.5} aria-hidden="true" />
                <span style={labelStyle(12, 600, '0.04em')}>
                  No account or dashboard access yet. Join the waitlist to help shape the private preview.
                </span>
              </motion.div>
            </motion.div>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
              className="order-1 flex flex-col justify-center py-12 lg:order-2 lg:py-16 lg:pl-20"
            >
              <motion.span variants={fadeInUp} className="mb-5 uppercase text-foreground/70" style={labelStyle(12, 700, '0.22em')}>
                Career evidence, before career copy
              </motion.span>
              <motion.h1
                variants={fadeInUp}
                className="mb-8 uppercase text-foreground"
                style={{
                  fontFamily: 'var(--font-humane), sans-serif',
                  fontSize: 'clamp(76px, 10.5vw, 168px)',
                  fontWeight: 540,
                  fontVariationSettings: '"wght" 540',
                  letterSpacing: '0.02em',
                  lineHeight: 0.77,
                }}
              >
                MAKE THE WORK<br />BEHIND YOUR<br />RESUME VISIBLE.
              </motion.h1>
              <motion.p
                variants={fadeInUp}
                className="max-w-xl border-l border-foreground/25 pl-5 text-foreground/70"
                style={{ fontSize: 'clamp(17px, 1.4vw, 21px)', lineHeight: 1.55 }}
              >
                One confirmed evidence history. Many truthful views for your resume,
                LinkedIn profile, target roles, and interviews.
              </motion.p>
            </motion.div>
          </div>
        </section>

        <section aria-label="People Prism Pro is being designed for" className={`overflow-hidden border-y ${borderFaint} py-8`}>
          <div className="flex items-center gap-10">
            <span className="shrink-0 pl-8 uppercase text-foreground/70" style={labelStyle(11, 700, '0.2em')}>
              DESIGNED FOR
            </span>
            <div className="overflow-hidden">
              <div className="flex w-max gap-12 whitespace-nowrap pr-12 motion-safe:animate-[marquee_32s_linear_infinite]">
                {[...STAGES, ...STAGES].map((stage, index) => (
                  <span key={`${stage}-${index}`} className="uppercase text-foreground/70" style={labelStyle(15, 700, '0.08em')}>
                    {stage}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="product-vision" className={`scroll-mt-24 border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="01"
                  label="THE GAP"
                  title={<>Your experience is not the same as what your application <em className="font-normal">shows.</em></>}
                  subtitle="Prism Pro is being built to close the communication gap without crossing the truth boundary."
                />
              </motion.div>

              <div className="divide-y divide-foreground/10 border border-foreground/10">
                {PROBLEMS.map(({ marker, title, detail }, index) => (
                  <motion.div
                    key={marker}
                    initial="hidden"
                    whileInView="visible"
                    variants={scrollReveal}
                    viewport={viewport}
                    transition={{ delay: index * 0.08 }}
                    className="p-8 transition-colors hover:bg-foreground/[0.025] sm:p-10"
                  >
                    <span className="mb-5 block text-foreground/70" style={labelStyle(11, 700, '0.2em')}>{marker}</span>
                    <h3 className="mb-4 max-w-2xl text-foreground" style={serifStyle('clamp(25px, 2.8vw, 40px)', 400)}>{title}</h3>
                    <p className="max-w-2xl text-foreground/70" style={{ fontSize: '18px', lineHeight: 1.7 }}>{detail}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="how-it-works" className={`scroll-mt-24 border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="02"
                  label="PLANNED EXPERIENCE"
                  title={<>From scattered details to a <em className="font-normal">defensible story.</em></>}
                  subtitle="The product will interview before it writes, and the candidate—not the model—will decide what becomes career evidence."
                />
              </motion.div>

              <div className="divide-y divide-foreground/10 border border-foreground/10">
                {STEPS.map(({ icon: Icon, step, title, desc }, index) => (
                  <motion.div
                    key={step}
                    initial="hidden"
                    whileInView="visible"
                    variants={scrollReveal}
                    viewport={viewport}
                    transition={{ delay: index * 0.08 }}
                    className="group flex items-start gap-5 p-7 transition-colors hover:bg-foreground/[0.025] sm:gap-7 sm:p-9"
                  >
                    <div className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center border border-foreground/20 group-hover:border-foreground/40">
                      <Icon size={19} strokeWidth={1.35} aria-hidden="true" />
                    </div>
                    <div className="flex-1">
                      <div className="mb-3 flex items-start justify-between gap-5">
                        <h3 className="text-foreground" style={serifStyle('clamp(21px, 2vw, 29px)', 400)}>{title}</h3>
                        <span className="text-foreground/70" style={serifStyle('32px', 400)}>{step}</span>
                      </div>
                      <p className="text-foreground/70" style={{ fontSize: '18px', lineHeight: 1.7 }}>{desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="experience" className={`scroll-mt-24 border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="03"
                  label="PRODUCT PREVIEW"
                  title={<>A workspace for the evidence behind the <em className="font-normal">document.</em></>}
                  subtitle="These concept panels show the planned experience. They are product direction—not a claim that public access is already available."
                />
              </motion.div>
              <BentoGrid isDark={isDark} />
            </div>
          </div>
        </section>

        <section id="principles" className={`scroll-mt-24 border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="04"
                  label="PRODUCT PRINCIPLES"
                  title={<>Useful AI needs a clear line it will <em className="font-normal">not cross.</em></>}
                  subtitle="The differentiator is not more generated text. It is better evidence, explicit candidate control, and transparent boundaries."
                />
              </motion.div>

              <div className="grid grid-cols-1 border-l border-t border-foreground/10 sm:grid-cols-2">
                {CAPABILITIES.map(({ title, desc }, index) => (
                  <motion.div
                    key={title}
                    initial="hidden"
                    whileInView="visible"
                    variants={scrollReveal}
                    viewport={viewport}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-r border-foreground/10 p-8 transition-colors hover:bg-foreground/[0.025]"
                  >
                    <span className="mb-6 block text-foreground/70" style={labelStyle(11, 700, '0.2em')}>
                      {String(index + 1).padStart(2, '0')}.
                    </span>
                    <h3 className="mb-4 text-foreground" style={serifStyle('clamp(21px, 1.9vw, 27px)', 400)}>{title}</h3>
                    <p className="text-foreground/70" style={{ fontSize: '17px', lineHeight: 1.7 }}>{desc}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="research" className={`scroll-mt-24 border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="05"
                  label="WHAT SHAPED IT"
                  title={<>Built from observed problems, not invented <em className="font-normal">proof.</em></>}
                  subtitle="Prism Pro is being shaped by qualitative candidate and recruiter discovery. These are directional research signals, not customer results or hiring statistics."
                />
              </motion.div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {RESEARCH_SIGNALS.map(({ label, title, body }, index) => (
                  <motion.div key={label} initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport} transition={{ delay: index * 0.06 }}>
                    <Card className="h-full rounded-none border-foreground/10 bg-card/35 p-8 shadow-none transition-transform duration-300 hover:-translate-y-1">
                      <span className="mb-8 block text-foreground/70" style={labelStyle(11, 700, '0.2em')}>{label}</span>
                      <h3 className="mb-5 text-foreground" style={serifStyle('clamp(23px, 2.2vw, 31px)', 400)}>{title}</h3>
                      <p className="text-foreground/70" style={{ fontSize: '17px', lineHeight: 1.7 }}>{body}</p>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className={`border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="06"
                  label="THE BOUNDARY"
                  title={<>Career support without career <em className="font-normal">fiction.</em></>}
                  subtitle="Some product limits are features. They protect your credibility, your privacy, and the value of the work you actually did."
                />
              </motion.div>

              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport} className="border border-foreground/10">
                <div className="border-b border-foreground/10 p-8 sm:p-10">
                  <span className="mb-5 block uppercase text-foreground/70" style={labelStyle(11, 700, '0.2em')}>PRISM PRO WILL NOT</span>
                  <h3 className="max-w-2xl text-foreground" style={serifStyle('clamp(32px, 4vw, 58px)', 400)}>
                    Manufacture confidence where evidence is missing.
                  </h3>
                </div>
                <ul className="divide-y divide-foreground/10">
                  {BOUNDARIES.map((boundary) => (
                    <li key={boundary} className="flex items-start gap-4 p-6 sm:px-10">
                      <Check size={17} className="mt-1 shrink-0 text-foreground/45" strokeWidth={1.5} aria-hidden="true" />
                      <span className="text-foreground/75" style={{ fontSize: '18px', lineHeight: 1.6 }}>{boundary}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            </div>
          </div>
        </section>

        <section id="faq" className={`scroll-mt-24 border-t ${borderFaint} py-28 lg:py-32`}>
          <div className="mx-auto max-w-[1400px] px-6 sm:px-8">
            <div className="grid grid-cols-1 gap-16 lg:grid-cols-[420px_1fr] lg:gap-24">
              <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport}>
                <SplitHeading
                  number="07"
                  label="FAQ"
                  title={<>The product is early. The answers should still be <em className="font-normal">clear.</em></>}
                  subtitle="What Prism Pro is becoming, what is deliberately unavailable today, and what the product will never promise."
                />
              </motion.div>

              <div className="divide-y divide-foreground/10 border-y border-foreground/10">
                {FAQS.map(({ q, a }, index) => (
                  <motion.details
                    key={q}
                    initial="hidden"
                    whileInView="visible"
                    variants={scrollReveal}
                    viewport={viewport}
                    transition={{ delay: index * 0.04 }}
                    className="group py-7"
                  >
                    <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-6 text-foreground marker:content-none">
                      <span style={serifStyle('clamp(20px, 1.8vw, 26px)', 400)}>{q}</span>
                      <span className="relative h-5 w-5 shrink-0" aria-hidden="true">
                        <span className="absolute left-0 top-1/2 h-px w-5 bg-foreground/50" />
                        <span className="absolute left-1/2 top-0 h-5 w-px bg-foreground/50 transition-transform group-open:rotate-90" />
                      </span>
                    </summary>
                    <p className="max-w-3xl pb-2 pt-5 text-foreground/70" style={{ fontSize: '17px', lineHeight: 1.75 }}>{a}</p>
                  </motion.details>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="early-access" className={`relative scroll-mt-24 border-t ${borderFaint} bg-foreground/[0.025] px-6 py-32 sm:px-8 lg:py-40`}>
          <div className="pointer-events-none absolute inset-0 opacity-[0.12] [background-image:linear-gradient(to_right,currentColor_1px,transparent_1px),linear-gradient(to_bottom,currentColor_1px,transparent_1px)] [background-size:48px_48px]" aria-hidden="true" />
          <motion.div initial="hidden" whileInView="visible" variants={scrollReveal} viewport={viewport} className="relative mx-auto max-w-[1100px] text-center">
            <Badge variant="outline" className="mb-8 rounded-none border-foreground/25 px-3 py-1.5 uppercase text-foreground" style={labelStyle(11, 700, '0.18em')}>
              Private preview
            </Badge>
            <h2 className="mb-8 text-foreground" style={serifStyle('clamp(46px, 7vw, 104px)', 400, '-0.025em')}>
              Your career is bigger than the document trying to explain it.
            </h2>
            <p className="mx-auto mb-10 max-w-2xl text-foreground/70" style={{ fontSize: 'clamp(18px, 1.8vw, 23px)', lineHeight: 1.6 }}>
              Tell us your target role, career stage, and the part of your experience that is hardest to communicate. We will use that context to shape the private preview.
            </p>
            <div className="mx-auto max-w-3xl border border-foreground/15 bg-background/75 p-6 backdrop-blur-sm sm:p-9">
              <WaitlistForm formLabel="Join the PrismPro private preview from the final call to action" />
            </div>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-foreground/70" style={labelStyle(11, 650, '0.08em')}>
              <span className="inline-flex items-center gap-2"><Sparkles size={14} aria-hidden="true" /> PRODUCT PREVIEW</span>
              <span className="inline-flex items-center gap-2"><BookOpenCheck size={14} aria-hidden="true" /> RESEARCH-LED</span>
              <span className="inline-flex items-center gap-2"><ShieldCheck size={14} aria-hidden="true" /> TRUTH-FIRST</span>
            </div>
          </motion.div>
        </section>
      </main>

      <div className="h-[14px] w-full bg-[#1a1a1a]" />

      <footer className={`border-t ${borderFaint} px-6 py-16 sm:px-8`}>
        <div className="mx-auto max-w-[1400px]">
          <div className="mb-16 grid grid-cols-1 gap-12 md:grid-cols-4">
            <div className="md:col-span-2">
              <span className="mb-4 block uppercase text-foreground" style={{ fontFamily: 'var(--font-humane), sans-serif', fontSize: '36px', fontWeight: 600, letterSpacing: '0.05em', lineHeight: 1 }}>
                PRISM PRO.
              </span>
              <p className="max-w-lg text-foreground/70" style={{ fontSize: '16px', lineHeight: 1.7 }}>
                A career-evidence coach in development for technical candidates. One confirmed evidence history for truthful, role-aligned resumes, LinkedIn recommendations, and interview narratives.
              </p>
              <a href="mailto:support@prismpro.live" className="mt-5 inline-block text-foreground/80 underline decoration-foreground/25 underline-offset-4 hover:text-foreground" style={labelStyle(14, 600, '0.03em')}>
                support@prismpro.live
              </a>
            </div>

            <div>
              <h3 className="mb-5 uppercase text-foreground" style={labelStyle(11, 700, '0.2em')}>EXPLORE</h3>
              <ul className="space-y-3">
                {[
                  ['Product vision', 'product-vision'],
                  ['Planned experience', 'how-it-works'],
                  ['Product principles', 'principles'],
                  ['FAQ', 'faq'],
                ].map(([label, id]) => (
                  <li key={id}>
                    <button onClick={() => scrollTo(id)} className="text-foreground/70 transition-colors hover:text-foreground" style={labelStyle(14, 500, '0.02em')}>
                      {label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="mb-5 uppercase text-foreground" style={labelStyle(11, 700, '0.2em')}>LEGAL</h3>
              <ul className="space-y-3">
                <li><Link href="/privacy-policy" className="text-foreground/70 transition-colors hover:text-foreground" style={labelStyle(14, 500, '0.02em')}>Privacy Policy</Link></li>
                <li><Link href="/terms" className="text-foreground/70 transition-colors hover:text-foreground" style={labelStyle(14, 500, '0.02em')}>Terms of Service</Link></li>
              </ul>
            </div>
          </div>

          <div className={`flex flex-col items-start justify-between gap-4 border-t ${borderFaint} pt-8 sm:flex-row sm:items-center`}>
            <span className="uppercase text-foreground/70" style={labelStyle(10, 700, '0.18em')}>© 2026 PRISM PRO. ALL RIGHTS RESERVED.</span>
            <span className="uppercase text-foreground/70" style={labelStyle(10, 700, '0.18em')}>PRISMPRO.LIVE · PRODUCT IN DEVELOPMENT</span>
          </div>
        </div>
      </footer>

      <style jsx global>{`
        @keyframes marquee {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }

        @media (prefers-reduced-motion: reduce) {
          html { scroll-behavior: auto; }
        }
      `}</style>
      </div>
    </MotionConfig>
  );
}

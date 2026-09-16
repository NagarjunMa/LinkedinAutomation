"use client";

import React, { useState } from 'react';
import { Navigation } from '@/components/landing/Navigation';
import { useTheme } from '@/contexts/theme-context';
import {
    FileText,
    Wand2,
    Zap,
    Coins,
    Download,
    HelpCircle,
    Shield,
    ChevronDown,
    ChevronUp,
    ExternalLink,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const sections = [
    {
        id: 'getting-started',
        icon: <Zap className="w-5 h-5 text-amber-500" />,
        title: 'Getting Started',
        summary: 'Create an account, set up your profile, and upload your first resume in under five minutes.',
        content: (
            <div className="space-y-4">
                <p>
                    Prism Pro is a resume intelligence platform for experienced engineers and product professionals. No browser extension is required — everything runs in the browser.
                </p>
                <ol className="list-decimal pl-5 space-y-3">
                    <li>
                        <strong>Sign in with Google.</strong> Prism Pro uses Google OAuth (verified). We request only your name and email — no Gmail read access at login.
                    </li>
                    <li>
                        <strong>Complete your profile.</strong> Navigate to <strong>Profile</strong> and fill in your target role, target location (USA / India), career level, and a short professional summary. This context powers the AI rewrite engine.
                    </li>
                    <li>
                        <strong>Upload your resume.</strong> Go to <strong>Resume</strong> and upload a PDF or DOCX. Review the extracted content before requesting an evaluation.
                    </li>
                    <li>
                        <strong>Run your first evaluation.</strong> Click <em>Evaluate</em> to review content findings and suggested next steps. Open <em>Document checks</em> for separate text-extraction and formatting diagnostics.
                    </li>
                </ol>
                <p className="text-sm font-medium mt-4">
                    New users receive <strong>90 free monthly credits</strong> on signup. See the Credits section for details.
                </p>
            </div>
        ),
    },
    {
        id: 'resume-polish',
        icon: <FileText className="w-5 h-5 text-sky-500" />,
        title: 'Resume Polish',
        summary: 'Review content findings, inspect document checks, and consider truthful rewrites.',
        content: (
            <div className="space-y-4">
                <p>
                    Resume Polish offers model-assisted content feedback. It is not a hiring assessment; review each suggestion against work you actually did.
                </p>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">What is evaluated</h4>
                <ul className="list-disc pl-5 space-y-2">
                    <li>
                        <strong>Document checks:</strong> Inspect extracted text and format findings. A layout warning is a reason to check reading order, not proof that an employer will reject the file.
                    </li>
                    <li>
                        <strong>Clarity and relevance:</strong> Review how clearly the resume communicates your contribution and target role.
                    </li>
                    <li>
                        <strong>Bullet-point content:</strong> Clarify your action, method, ownership, and supported outcome. STAR, CAR, and XYZ are optional structures; do not invent a metric to fit one.
                    </li>
                    <li>
                        <strong>Evidence gaps:</strong> Check whether a suggestion needs clarification or additional experience. Missing terminology does not prove a missing skill.
                    </li>
                </ul>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">How to use rewrites</h4>
                <ol className="list-decimal pl-5 space-y-2">
                    <li>After evaluation, click a bullet to review a suggested rewrite.</li>
                    <li>Accept a rewrite only if its skills, ownership, and outcomes reflect your actual experience.</li>
                    <li>Download the updated resume as PDF once you are satisfied.</li>
                </ol>
                <p className="text-sm italic mt-4 text-muted-foreground">
                    Each evaluation costs 1 credit. Rewrite attempts on a previously evaluated resume do not cost additional credits within the same session.
                </p>
            </div>
        ),
    },
    {
        id: 'jd-tailoring',
        icon: <Wand2 className="w-5 h-5 text-violet-500" />,
        title: 'JD Tailoring',
        summary: 'Compare job requirements with your resume and review proposed changes.',
        content: (
            <div className="space-y-4">
                <p>
                    JD Tailoring compares your resume against a specific job description and produces a targeted variant optimised for that role.
                </p>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Steps</h4>
                <ol className="list-decimal pl-5 space-y-2">
                    <li>Go to <strong>Tailor</strong> in the sidebar.</li>
                    <li>Select the resume version you want to tailor (your most recent evaluation is pre-selected).</li>
                    <li>Paste the full job description text into the JD input field.</li>
                    <li>Click <em>Analyse</em>. The AI extracts required skills, seniority signals, and company-specific language.</li>
                    <li>Review requirements found and not found in the uploaded resume. These are model-assisted findings, not verified skills or hiring probabilities.</li>
                    <li>Review proposed changes, select those you can defend, and apply your selection.</li>
                    <li>Export the tailored version as a new resume revision.</li>
                </ol>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Tips</h4>
                <ul className="list-disc pl-5 space-y-2">
                    <li>Use the full JD text, not just the "Requirements" section — job titles, team descriptions, and tech-stack mentions also inform the AI.</li>
                    <li>Only add job-description terms when your actual experience supports them. Do not insert a skill, technology, or outcome merely because it appears in the job description.</li>
                    <li>Each JD analysis costs 1 credit. Generating rewrites from the same analysis is free within the session.</li>
                </ul>
            </div>
        ),
    },
    {
        id: 'ats-simulator',
        icon: <Shield className="w-5 h-5 text-green-500" />,
        title: 'Document checks',
        summary: 'Inspect PrismPro text extraction and formatting diagnostics separately from content feedback.',
        content: (
            <div className="space-y-4">
                <p>
                    This is PrismPro&apos;s document diagnostic, not a replica of any ATS. It does not measure candidate quality, hiring probability, or future score improvements. Different systems may extract or display the same file differently.
                </p>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">What to inspect</h4>
                <ul className="list-disc pl-5 space-y-2">
                    <li>Whether extracted text preserves the intended reading order</li>
                    <li>Whether contact details, roles, dates, and bullet text are present</li>
                    <li>Whether the exported file stays readable without clipping or overflow</li>
                    <li>Any reported format issue, checked against the original file rather than treated as universal ATS behavior</li>
                </ul>
                <p className="text-sm mt-4">
                    After evaluation, open the Document checks tab. Its parseability value is an internal document heuristic, not an ATS success percentage.
                </p>
            </div>
        ),
    },
    {
        id: 'credits',
        icon: <Coins className="w-5 h-5 text-yellow-500" />,
        title: 'Credits',
        summary: 'Understand how credits work, what they cost, and how to manage your usage.',
        content: (
            <div className="space-y-4">
                <p>
                    Prism Pro uses a credit system to keep costs transparent. You always know exactly how many operations you have remaining.
                </p>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Credit usage</h4>
                <ul className="list-disc pl-5 space-y-2">
                    <li><strong>1 credit:</strong> Resume evaluation (content feedback and document checks)</li>
                    <li><strong>1 credit:</strong> JD analysis (requirement comparison and tailoring suggestions)</li>
                    <li><strong>Free:</strong> Viewing past evaluations, accepting / rejecting rewrites within an existing session, downloading PDFs of already-evaluated resumes</li>
                </ul>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Checking your balance</h4>
                <p>
                    Your current credit balance is always visible in the sidebar. Go to <strong>Credits</strong> for your monthly allowance and usage details.
                </p>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Free tier</h4>
                <p>
                    New accounts receive <strong>90 free credits every month</strong>. That covers about 30 JD tailor-and-export workflows during the freemium launch.
                </p>
            </div>
        ),
    },
    {
        id: 'export',
        icon: <Download className="w-5 h-5 text-rose-500" />,
        title: 'Export Templates',
        summary: 'Download a PDF and check its text, layout, and reading order before submitting.',
        content: (
            <div className="space-y-4">
                <p>
                    After reviewing proposed changes, export a PDF and inspect it before submitting. No template guarantees acceptance or identical parsing across employers&apos; systems.
                </p>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Export options</h4>
                <ul className="list-disc pl-5 space-y-2">
                    <li>
                        <strong>Standard PDF (US):</strong> A US-oriented presentation option. Check the exported document against the employer&apos;s file requirements.
                    </li>
                    <li>
                        <strong>Standard PDF (India / A4):</strong> An India-oriented presentation option. Check page layout and reading order rather than assuming compatibility with a hiring portal.
                    </li>
                </ul>
                <h4 className="font-bold text-sm uppercase tracking-wider mt-6 mb-2">Resume versioning</h4>
                <p>
                    Every export creates a new version record under your resume. You can download any past version at any time from the Resume Revision Ledger in your Profile.
                </p>
                <p className="text-sm italic text-muted-foreground mt-4">
                    Exports are free — no credits are consumed when downloading a previously evaluated resume.
                </p>
            </div>
        ),
    },
    {
        id: 'faq',
        icon: <HelpCircle className="w-5 h-5 text-slate-500" />,
        title: 'FAQ',
        summary: 'Answers to the most common questions from engineers and product professionals.',
        content: (
            <div className="space-y-6">
                <FaqItem q="Is Prism Pro a job board or job search tool?">
                    No. Prism Pro is a resume intelligence platform. We do not aggregate jobs, connect to LinkedIn, or automate job applications. Our focus is on helping you prepare a recruiter-grade resume before you apply.
                </FaqItem>
                <FaqItem q="Which file formats are supported for upload?">
                    PDF and DOCX. Inspect the extracted text and exported document; file support does not guarantee identical results in an employer&apos;s system.
                </FaqItem>
                <FaqItem q="Does Prism Pro store my resume permanently?">
                    Your resumes are stored securely in your account and are only accessible to you. You can delete any resume version at any time from your Profile page. See our <a href="/privacy-policy" className="underline underline-offset-2">Privacy Policy</a> for full details.
                </FaqItem>
                <FaqItem q="What does document parseability tell me?">
                    It summarizes PrismPro&apos;s own extraction and formatting checks. It is not validated against an employer&apos;s ATS and does not predict screening, interviews, or employment. Inspect individual findings instead of treating the value as a candidate-quality score.
                </FaqItem>
                <FaqItem q="Does sign-in with Google give Prism Pro access to my Gmail?">
                    No. Prism Pro requests only your name and email address during sign-in. We do not request Gmail read access. This is confirmed by Google's OAuth verification process — our app has passed Google's review for Limited Use compliance.
                </FaqItem>
                <FaqItem q="What is the difference between Resume Polish and JD Tailoring?">
                    Resume Polish offers content feedback and document diagnostics. JD Tailoring compares the uploaded resume with a specific job description and proposes changes. Both require your review; neither establishes the truth of a claim or predicts a hiring outcome.
                </FaqItem>
                <FaqItem q="I ran out of credits. What can I do?">
                    Credits refresh monthly during the freemium launch. If you believe your balance is incorrect, contact <a href="mailto:support@prismpro.live" className="underline underline-offset-2">support@prismpro.live</a>.
                </FaqItem>
            </div>
        ),
    },
];

// ---------------------------------------------------------------------------
// Accordion item
// ---------------------------------------------------------------------------

function FaqItem({ q, children }: { q: string; children: React.ReactNode }) {
    return (
        <div>
            <p className="font-bold text-sm mb-1">{q}</p>
            <p className="text-sm opacity-75 leading-relaxed">{children}</p>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Collapsible section card
// ---------------------------------------------------------------------------

function SectionCard({
    section,
    isDark,
}: {
    section: typeof sections[number];
    isDark: boolean;
}) {
    const [open, setOpen] = useState(false);

    return (
        <div
            className={`rounded-2xl border ${
                isDark ? 'bg-white/5 border-white/10' : 'bg-white border-black/5 shadow-sm'
            } transition-all duration-300`}
        >
            <button
                onClick={() => setOpen((v) => !v)}
                className="w-full text-left p-6 md:p-8 flex items-start gap-4"
                aria-expanded={open}
            >
                <div
                    className={`mt-0.5 p-3 rounded-xl shrink-0 ${
                        isDark ? 'bg-white/10' : 'bg-gray-100'
                    }`}
                >
                    {section.icon}
                </div>
                <div className="flex-1 min-w-0">
                    <h2 className="text-xl font-bold mb-1">{section.title}</h2>
                    <p className="text-sm opacity-60">{section.summary}</p>
                </div>
                <div className="shrink-0 mt-1 opacity-40">
                    {open ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
            </button>

            {open && (
                <div className={`px-6 md:px-8 pb-8 pt-0 text-sm leading-relaxed opacity-80 border-t ${isDark ? 'border-white/5' : 'border-black/5'}`}>
                    <div className="pt-6">{section.content}</div>
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Documentation() {
    const { isDark } = useTheme();

    return (
        <div
            className={`min-h-screen ${
                isDark ? 'bg-[#0a0a0a] text-[#f0eff2]' : 'bg-[#f0eff2] text-[#0a0a0a]'
            } transition-colors duration-300 font-sans`}
        >
            <Navigation />

            <main className="max-w-4xl mx-auto px-6 pt-32 pb-20">
                {/* Hero */}
                <div className="text-center mb-16">
                    <p className="text-xs font-bold uppercase tracking-[0.2em] opacity-40 mb-4">
                        Prism Pro Documentation
                    </p>
                    <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">
                        How to use Prism Pro
                    </h1>
                    <p className="text-lg opacity-60 max-w-2xl mx-auto">
                        A practical guide to reviewing resume content, document diagnostics, and job requirements — without promises about hiring outcomes.
                    </p>
                </div>

                {/* Section index */}
                <nav
                    className={`p-5 rounded-xl mb-12 text-sm border ${
                        isDark ? 'bg-white/5 border-white/10' : 'bg-white border-black/5 shadow-sm'
                    }`}
                    aria-label="On this page"
                >
                    <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-3">On this page</p>
                    <ul className="flex flex-wrap gap-x-6 gap-y-2">
                        {sections.map((s) => (
                            <li key={s.id}>
                                <a
                                    href={`#${s.id}`}
                                    className="opacity-60 hover:opacity-100 transition-opacity flex items-center gap-1"
                                >
                                    {s.title}
                                </a>
                            </li>
                        ))}
                    </ul>
                </nav>

                {/* Section cards */}
                <div className="space-y-4">
                    {sections.map((section) => (
                        <div key={section.id} id={section.id}>
                            <SectionCard section={section} isDark={isDark} />
                        </div>
                    ))}
                </div>

                {/* Support CTA */}
                <div
                    className={`mt-16 p-8 rounded-2xl border text-center ${
                        isDark ? 'bg-white/5 border-white/10' : 'bg-white border-black/5 shadow-sm'
                    }`}
                >
                    <div className="flex justify-center mb-4">
                        <Shield className="w-8 h-8 opacity-30" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Google OAuth Verified</h3>
                    <p className="opacity-60 text-sm mb-4 max-w-md mx-auto">
                        Prism Pro has passed Google&apos;s OAuth App Verification. We comply with Google&apos;s Limited Use Policy — your data is never shared with third parties.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <a
                            href="/privacy-policy"
                            className={`inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-medium rounded-lg border transition-all duration-200 ${
                                isDark
                                    ? 'border-white/20 hover:bg-white/10'
                                    : 'border-black/10 hover:bg-black/5'
                            }`}
                        >
                            Privacy Policy <ExternalLink className="w-3 h-3" />
                        </a>
                        <a
                            href="mailto:support@prismpro.live"
                            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200"
                        >
                            Contact Support
                        </a>
                    </div>
                </div>
            </main>

            <footer
                className={`py-12 px-6 border-t ${
                    isDark ? 'border-[#f0eff2]/5' : 'border-[#3b3b3b]/5'
                }`}
            >
                <div className="max-w-7xl mx-auto text-center opacity-40 text-sm">
                    <p>&copy; {new Date().getFullYear()} Prism Pro. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}

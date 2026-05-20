"use client";

import React from 'react';
import { Navigation } from '@/components/landing/Navigation';
import { useTheme } from '@/contexts/theme-context';
import {
    FileText,
    Briefcase,
    Share2,
    Zap
} from 'lucide-react';

export default function Documentation() {
    const { isDark } = useTheme();

    const sections = [
        {
            id: "getting-started",
            icon: <Zap className="w-6 h-6 text-yellow-500" />,
            title: "Getting Started",
            content: (
                <div className="space-y-4">
                    <p>Welcome to Prism Pro! To get the most out of our platform, follow these initial steps:</p>
                    <ol className="list-decimal pl-5 space-y-2">
                        <li><strong>Install the Extension:</strong> Download our Chrome Extension to enable one-click job saving from LinkedIn.</li>
                        <li><strong>Create an Account:</strong> Sign up using your Google account or email address.</li>
                        <li><strong>Complete Your Profile:</strong> Go to Settings &gt; Profile to upload your resume and set your job preferences.</li>
                    </ol>
                </div>
            )
        },
        {
            id: "job-tracking",
            icon: <Briefcase className="w-6 h-6 text-blue-500" />,
            title: "Job Tracking",
            content: (
                <div className="space-y-4">
                    <p>Track your job search progress with our powerful application tracker.</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong>Dashboard View:</strong> See all your applications in a Kanban board or List view.</li>
                        <li><strong>Status Updates:</strong> Drag and drop applications to change their status (e.g., Applied -&gt; Interview).</li>
                        <li><strong>Smart Extraction:</strong> Use the extension on any LinkedIn job post to automatically extract details like Salary, Location, and Recruiter info.</li>
                    </ul>
                </div>
            )
        },
        {
            id: "resume-ai",
            icon: <FileText className="w-6 h-6 text-green-500" />,
            title: "AI Resume Builder",
            content: (
                <div className="space-y-4">
                    <p>Optimize your resume for every application using our AI tools.</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong>Resume Evaluation:</strong> Upload your resume and a job description to get a compatibility score (0-100%).</li>
                        <li><strong>Keyword Analysis:</strong> See exactly which keywords you're missing from the job description.</li>
                        <li><strong>Tailoring:</strong> Let our AI rewrite your bullet points to better match the target role.</li>
                    </ul>
                </div>
            )
        },
        {
            id: "networking",
            icon: <Share2 className="w-6 h-6 text-purple-500" />,
            title: "Networking & Referrals",
            content: (
                <div className="space-y-4">
                    <p>Leverage your network to land more interviews.</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong>Referral Templates:</strong> Use our pre-written, AI-customized templates to ask for referrals.</li>
                        <li><strong>Contact Management:</strong> Keep track of who you've reached out to and set follow-up reminders.</li>
                    </ul>
                </div>
            )
        }
    ];

    return (
        <div className={`min-h-screen ${isDark ? 'bg-[#0a0a0a] text-[#f0eff2]' : 'bg-[#f0eff2] text-[#0a0a0a]'} transition-colors duration-300 font-sans`}>
            <Navigation />

            <main className="max-w-6xl mx-auto px-6 pt-32 pb-20">
                <div className="text-center mb-16">
                    <h1 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight">
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
                            Documentation
                        </span>
                    </h1>
                    <p className="text-xl opacity-60 max-w-2xl mx-auto">
                        Everything you need to know to land your dream job with Prism Pro.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {sections.map((section) => (
                        <div
                            key={section.id}
                            className={`p-8 rounded-2xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-white border-black/5 shadow-sm'} hover:border-primary/50 transition-all duration-300`}
                        >
                            <div className="flex items-center gap-4 mb-6">
                                <div className={`p-3 rounded-xl ${isDark ? 'bg-white/10' : 'bg-gray-100'}`}>
                                    {section.icon}
                                </div>
                                <h2 className="text-2xl font-bold">{section.title}</h2>
                            </div>
                            <div className="opacity-80 leading-relaxed">
                                {section.content}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-20 p-8 rounded-2xl bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-500/20 text-center">
                    <h3 className="text-2xl font-bold mb-4">Still have questions?</h3>
                    <p className="opacity-70 mb-6">Our support team is always ready to help you with any specific issues.</p>
                    <a
                        href="mailto:support@prismpro.live"
                        className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-all duration-200 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground"
                    >
                        Contact Support
                    </a>
                </div>
            </main>

            <footer className={`py-12 px-6 border-t ${isDark ? 'border-[#f0eff2]/5' : 'border-[#3b3b3b]/5'}`}>
                <div className="max-w-7xl mx-auto text-center opacity-40 text-sm">
                    <p>&copy; {new Date().getFullYear()} Prism Pro. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}

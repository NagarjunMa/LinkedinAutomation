"use client";

import React from 'react';
import { Navigation } from '@/components/landing/Navigation';
import { useTheme } from '@/contexts/theme-context';

export default function PrivacyPolicy() {
    const { isDark } = useTheme();

    return (
        <div className={`min-h-screen ${isDark ? 'bg-[#0a0a0a] text-[#f0eff2]' : 'bg-[#f0eff2] text-[#0a0a0a]'} transition-colors duration-300 font-sans`}>
            <Navigation />

            <main className="max-w-4xl mx-auto px-6 pt-32 pb-20">
                <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">PRIVACY POLICY</h1>
                <p className="opacity-60 mb-12">Last updated February 02, 2026</p>

                <div className="prose max-w-none prose-lg opacity-80 space-y-8">
                    <p>
                        This Privacy Notice for Prism Pro ("we," "us," or "our"), describes how and why we might access, collect, store, use, and/or share ("process") your personal information when you use our services ("Services"), including when you:
                    </p>
                    <ul className="list-disc pl-6 space-y-2">
                        <li>Visit our website at <a href="https://www.prismpro.live" className="underline hover:text-blue-500">https://www.prismpro.live</a> or any website of ours that links to this Privacy Notice</li>
                        <li>Use Prism Pro. Prism Pro is an AI-powered LinkedIn automation and job search management platform. Students and job seekers use Prism Pro to extract job listings, track applications, and tailor resumes.</li>
                        <li>Engage with us in other related ways, including any marketing or events</li>
                    </ul>

                    <p>
                        Questions or concerns? Reading this Privacy Notice will help you understand your privacy rights and choices. We are responsible for making decisions about how your personal information is processed. If you do not agree with our policies and practices, please do not use our Services. If you still have any questions or concerns, please contact us at <a href="mailto:nagarjunmallesh@gmail.com" className="underline hover:text-blue-500">nagarjunmallesh@gmail.com</a>.
                    </p>

                    <hr className={`border-t ${isDark ? 'border-white/10' : 'border-black/10'} my-12`} />

                    <h2 className="text-2xl font-bold mt-12 mb-6 text-xl uppercase tracking-widest">Summary of Key Points</h2>

                    <div className="space-y-6 text-sm md:text-base">
                        <p><strong>What personal information do we process?</strong> When you visit, use, or navigate our Services, we may process personal information depending on how you interact with us and the Services, the choices you make, and the products and features you use.</p>

                        <p><strong>Do we process any sensitive personal information?</strong> We do not strictly process sensitive personal information unless included in the resumes or job applications you upload or track (e.g., if you choose to include racial or ethnic origin in your documents), but we do not require it.</p>

                        <p><strong>Do we collect any information from third parties?</strong> Yes, we collect information from LinkedIn (via our extension/automation tools) and Google (via OAuth) to provide our core services.</p>

                        <p><strong>How do we process your information?</strong> We process your information to provide, improve, and administer our Services, communicate with you, for security and fraud prevention, and to comply with law. We may also process your information for other purposes with your consent.</p>

                        <p><strong>How do we keep your information safe?</strong> We have adequate organizational and technical processes and procedures in place to protect your personal information.</p>
                    </div>

                    <h2 className="text-2xl font-bold mt-16 mb-6 uppercase tracking-widest">1. What Information Do We Collect?</h2>

                    <h3 className="text-xl font-bold mt-8 mb-4">Personal information you disclose to us</h3>
                    <p>The personal information that we collect depends on the context of your interactions with us and the Services, the choices you make, and the products and features you use. The personal information we collect may include the following:</p>
                    <ul className="list-disc pl-6 space-y-2">
                        <li>Names</li>
                        <li>Email addresses</li>
                        <li>Job titles</li>
                        <li>Passwords (stored securely via authentication providers)</li>
                        <li>Professional information including resumes, cover letters, LinkedIn profile links, employment history, education, skills, and certifications.</li>
                        <li>Job application data: Information about jobs you save, status of applications, and notes you add.</li>
                    </ul>

                    <h3 className="text-xl font-bold mt-8 mb-4">Social Media Login Data</h3>
                    <p>We provide you with the option to register with us using your existing social media account details, like your Google account. If you choose to register in this way, we will collect certain profile information about you from the social media provider.</p>

                    <h2 className="text-2xl font-bold mt-16 mb-6 uppercase tracking-widest">2. How Do We Process Your Information?</h2>
                    <p>We process your personal information for a variety of reasons, depending on how you interact with our Services, including:</p>
                    <ul className="list-disc pl-6 space-y-2">
                        <li><strong>To facilitate account creation and authentication:</strong> We process your information so you can create and log in to your account.</li>
                        <li><strong>To deliver specific services:</strong> Identifying relevant jobs, tailoring resumes using AI, and tracking application status.</li>
                        <li><strong>To protect our Services:</strong> We may process your information as part of our efforts to keep our Services safe and secure.</li>
                        <li><strong>Personalize recommendations:</strong> Tailor job and candidate recommendations match results.</li>
                    </ul>

                    <h2 className="text-2xl font-bold mt-16 mb-6 uppercase tracking-widest">3. Google API Services User Data Policy</h2>
                    <p>
                        Our use of information received from Google APIs will adhere to the <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-500">Google API Services User Data Policy</a>, including the Limited Use requirements.
                    </p>

                    <h2 className="text-2xl font-bold mt-16 mb-6 uppercase tracking-widest">4. Do We Offer Artificial Intelligence-Based Products?</h2>
                    <p>As part of our Services, we offer products, features, or tools powered by artificial intelligence, machine learning, or similar technologies (collectively, "AI Products").</p>
                    <p className="mt-4">
                        We provide the AI Products through third-party service providers, potentially including OpenAI and others. Your input (such as resume content) and output (such as tailored suggestions) will be shared with and processed by these AI Service Providers found to enable your use of our AI Products. We do not use your personal data to train public AI models without your explicit consent.
                    </p>

                    <h2 className="text-2xl font-bold mt-16 mb-6 uppercase tracking-widest">5. How Can You Contact Us?</h2>
                    <p>If you have questions or comments about this notice, you may email us at <a href="mailto:nagarjunmallesh@gmail.com" className="underline hover:text-blue-500">nagarjunmallesh@gmail.com</a>.</p>
                </div>
            </main>

            <footer className={`py-12 px-6 border-t ${isDark ? 'border-[#f0eff2]/5' : 'border-[#3b3b3b]/5'}`}>
                <div className="max-w-7xl mx-auto text-center opacity-40 text-sm">
                    <p>&copy; 2026 Prism Pro. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}

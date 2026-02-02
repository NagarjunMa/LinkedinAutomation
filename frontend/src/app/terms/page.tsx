import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function TermsOfService() {
    return (
        <div className="min-h-screen bg-background text-foreground py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <Link href="/">
                        <Button variant="ghost" className="gap-2 pl-0 hover:pl-2 transition-all">
                            <ArrowLeft className="h-4 w-4" />
                            Back to Home
                        </Button>
                    </Link>
                </div>

                <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
                <div className="prose prose-gray dark:prose-invert max-w-none space-y-6">
                    <p className="text-lg text-muted-foreground">Last updated: {new Date().toLocaleDateString()}</p>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
                        <p>
                            By accessing and using Prism Pro ("the Service"), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our Service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
                        <p>
                            Prism Pro is an automated job application management and resume optimization platform. We provide tools to help users organize their job search, evaluate resumes, and track applications.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
                        <p>
                            You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">4. Acceptable Use</h2>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>You agree not to misuse our services or help anyone else do so.</li>
                            <li>You will not use the Service for any illegal or unauthorized purpose.</li>
                            <li>You will not attempt to bypass any security measures of the Service.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">5. Disclaimer of Warranties</h2>
                        <p>
                            The Service is provided "as is" and "as available" without any warranties of any kind, either express or implied, including but not limited to fitness for a particular purpose and non-infringement.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">6. Limitation of Liability</h2>
                        <p>
                            In no event shall Prism Pro be liable for any indirect, incidental, special, consequential, or punitive damages arising out of your use of or inability to use the Service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">7. Changes to Terms</h2>
                        <p>
                            We reserve the right to modify these terms at any time. We will notify users of any significant changes. Your continued use of the Service after such changes constitutes your acceptance of the new Terms of Service.
                        </p>
                    </section>
                </div>
            </div>
        </div>
    );
}

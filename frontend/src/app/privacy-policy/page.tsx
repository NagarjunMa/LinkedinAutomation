"use client";

import React from 'react';

import { Navigation } from '@/components/landing/Navigation';
import { useTheme } from '@/contexts/theme-context';
import { getConfiguredAppOrigin } from '@/lib/url';

export default function PrivacyPolicy() {
  const { isDark } = useTheme();
  const appOrigin = getConfiguredAppOrigin();

  return (
    <div className={`min-h-screen ${isDark ? 'bg-[#0a0a0a] text-[#f0eff2]' : 'bg-[#f0eff2] text-[#0a0a0a]'} font-sans transition-colors duration-300`}>
      <Navigation />

      <main className="mx-auto max-w-4xl px-6 pb-20 pt-36">
        <p className="mb-4 text-sm font-bold uppercase tracking-[0.18em] opacity-55">
          Public preview
        </p>
        <h1 className="mb-4 text-4xl font-bold tracking-tight md:text-5xl">Privacy Policy</h1>
        <p className="mb-12 opacity-60">Last updated September 6, 2026</p>

        <div className="max-w-none space-y-10 text-base leading-7 opacity-85 md:text-lg">
          <section className="space-y-4">
            <h2 className="text-2xl font-bold">What this notice covers</h2>
            <p>
              This notice explains how PrismPro processes information submitted through the
              private-preview waitlist at{' '}
              <a href={appOrigin} className="underline underline-offset-4">{appOrigin}</a>.
              Public account creation, authentication, and product access are currently closed.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">Information we collect</h2>
            <p>The waitlist asks for:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Your email address, which is required.</li>
              <li>Your career stage, target role, and communication challenge, which are optional.</li>
              <li>The version and time of your consent to private-preview contact.</li>
              <li>
                Content-free landing-page events, such as form location, validation category,
                and scroll-depth threshold. These events do not include your email address or
                free-text responses.
              </li>
            </ul>
            <p>
              Our server may temporarily process network and request metadata, such as an IP
              address and request identifier, to enforce rate limits, investigate abuse, and keep
              the service reliable. This metadata is not stored in your waitlist record.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">How we use it</h2>
            <ul className="list-disc space-y-2 pl-6">
              <li>To maintain the research and private-preview list.</li>
              <li>To contact you about interviews, prototype feedback, or preview availability.</li>
              <li>To understand which career communication problems the first experience should address.</li>
              <li>To prevent duplicate, fraudulent, or abusive submissions.</li>
              <li>To measure whether the public preview and waitlist flow are working.</li>
            </ul>
            <p>
              Joining the list does not create an account. We do not sell waitlist information,
              use it for advertising profiles, or use it to train generalized AI models.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">Storage, access, and retention</h2>
            <p>
              Waitlist entries are stored in our application database. The table is not available
              for direct browser writes and is restricted from anonymous and authenticated
              Supabase Data API roles. Access is limited to the server-side application and
              authorized operators who need it for the purposes above.
            </p>
            <p>
              Each waitlist entry receives a 180-day retention deadline. We review and delete
              expired entries unless you separately join a later pilot, ask us to retain your
              information, or applicable law requires retention.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">Service providers</h2>
            <p>
              We may use infrastructure providers to host the website, API, and database. They
              process information for us under their service terms and only as needed to operate
              the preview. The waitlist does not request LinkedIn credentials or access a live
              LinkedIn account.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">Your choices</h2>
            <p>
              You can ask to access, correct, export, or delete your waitlist information, or
              withdraw contact consent, by emailing{' '}
              <a href="mailto:support@prismpro.live" className="underline underline-offset-4">
                support@prismpro.live
              </a>
              . We may need to verify that you control the submitted email address before acting
              on the request.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">Updates and contact</h2>
            <p>
              We may revise this notice as the preview changes. The date above identifies the
              current version. Questions can be sent to{' '}
              <a href="mailto:support@prismpro.live" className="underline underline-offset-4">
                support@prismpro.live
              </a>
              .
            </p>
          </section>
        </div>
      </main>

      <footer className={`border-t px-6 py-12 ${isDark ? 'border-[#f0eff2]/5' : 'border-[#3b3b3b]/5'}`}>
        <div className="mx-auto max-w-7xl text-center text-sm opacity-40">
          <p>&copy; 2026 PrismPro. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

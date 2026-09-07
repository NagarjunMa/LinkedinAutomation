import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-background px-4 py-12 text-foreground sm:px-6 lg:px-8">
      <main className="mx-auto max-w-4xl">
        <div className="mb-8">
          <Button asChild variant="ghost" className="gap-2 pl-0 transition-all hover:pl-2">
            <Link href="/">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Back to home
            </Link>
          </Button>
        </div>

        <p className="mb-4 text-sm font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Public preview
        </p>
        <h1 className="mb-4 text-4xl font-bold">Terms of Service</h1>
        <p className="mb-12 text-lg text-muted-foreground">Last updated September 6, 2026</p>

        <div className="max-w-none space-y-10 text-base leading-7 md:text-lg">
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold">1. Preview website</h2>
            <p>
              PrismPro is an in-development career-evidence coach for technical candidates. This
              public website describes the planned product direction and provides a private-preview
              waitlist. It does not provide a public account, dashboard, or production product.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold">2. Waitlist participation</h2>
            <p>
              Joining the waitlist gives us permission to contact you about PrismPro research and
              early access. It does not guarantee admission, a launch date, continued availability,
              or any particular feature. You may withdraw at any time by contacting us.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold">3. Truthful product claims</h2>
            <p>
              Product concepts shown on this site are clearly labelled as planned experiences.
              PrismPro does not guarantee ATS performance, recruiter attention, interviews,
              offers, or employment outcomes.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold">4. Acceptable use</h2>
            <ul className="list-disc space-y-2 pl-6">
              <li>Do not submit information you do not have permission to provide.</li>
              <li>Do not attempt to bypass rate limits or preview access controls.</li>
              <li>Do not interfere with the website, API, database, or other visitors.</li>
              <li>Do not use the preview for unlawful, fraudulent, or abusive activity.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold">5. Availability and disclaimer</h2>
            <p>
              The preview website is provided on an “as is” and “as available” basis. We may
              change, suspend, or discontinue preview content or waitlist access. To the extent
              permitted by law, PrismPro disclaims implied warranties relating to this preview.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-2xl font-semibold">6. Contact</h2>
            <p>
              Questions about these terms can be sent to{' '}
              <a href="mailto:support@prismpro.live" className="underline underline-offset-4">
                support@prismpro.live
              </a>
              . See the{' '}
              <Link href="/privacy-policy" className="underline underline-offset-4">
                Privacy Policy
              </Link>{' '}
              for waitlist data practices.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}

"use client";
import { useMemo } from 'react';
import { BulletHighlight } from './bullet-highlight';
import type { ResumeDocumentJSON, BulletFlag } from '@/app/lib/api';

export interface ResumeRendererProps {
  doc: ResumeDocumentJSON;
  flags?: BulletFlag[];
  onBulletClick: (bulletId: string) => void;
}

export function ResumeRenderer({ doc, flags = [], onBulletClick }: ResumeRendererProps) {
  const flagByBullet = useMemo(() => {
    const m = new Map<string, BulletFlag>();
    for (const f of flags) m.set(f.bullet_id, f);
    return m;
  }, [flags]);

  return (
    <article className="bg-white text-black rounded-lg p-8 shadow-sm font-serif">
      <header className="text-center border-b pb-4 mb-4">
        <h1 className="text-xl font-bold">{doc.contact.name}</h1>
        <p className="text-xs opacity-70">
          {[doc.contact.email, doc.contact.phone, ...doc.contact.links]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </header>

      {doc.summary && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-1">Summary</h2>
          <p className="text-sm">{doc.summary}</p>
        </section>
      )}

      {doc.experience.length > 0 && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-2">Experience</h2>
          {doc.experience.map((exp, i) => (
            <div key={i} className="mb-3">
              <div className="flex justify-between text-sm font-semibold">
                <span>{exp.role} — {exp.company}</span>
                <span className="opacity-70">{exp.dates}</span>
              </div>
              <ul className="ml-4 mt-1">
                {exp.bullets.map((b) => (
                  <BulletHighlight
                    key={b.id}
                    bullet={b}
                    flag={flagByBullet.get(b.id)}
                    onClick={onBulletClick}
                  />
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {doc.projects.length > 0 && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-2">Projects</h2>
          {doc.projects.map((p, i) => (
            <div key={i} className="mb-2">
              <p className="text-sm font-semibold">{p.name}</p>
              <ul className="ml-4">
                {p.bullets.map((b) => (
                  <BulletHighlight
                    key={b.id}
                    bullet={b}
                    flag={flagByBullet.get(b.id)}
                    onClick={onBulletClick}
                  />
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {doc.education.length > 0 && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-2">Education</h2>
          {doc.education.map((e, i) => (
            <div key={i} className="text-sm">
              <span className="font-semibold">{e.school}</span>
              {e.degree && <span> — {e.degree}</span>}
              {e.dates && <span className="opacity-70"> ({e.dates})</span>}
            </div>
          ))}
        </section>
      )}

      {(doc.skills.hard.length > 0 || doc.skills.soft.length > 0) && (
        <section>
          <h2 className="text-sm font-bold uppercase tracking-wide mb-1">Skills</h2>
          <p className="text-sm">{doc.skills.hard.join(' · ')}</p>
          {doc.skills.soft.length > 0 && (
            <p className="text-xs opacity-70 mt-1">{doc.skills.soft.join(' · ')}</p>
          )}
        </section>
      )}
    </article>
  );
}

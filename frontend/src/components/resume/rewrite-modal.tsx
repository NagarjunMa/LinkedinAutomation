// frontend/src/components/resume/rewrite-modal.tsx
"use client";
import { useEffect, useState } from 'react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useRewriteBullet } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import type { Bullet, BulletFlag, RewriteResult } from '@/app/lib/api';

const NO_FINDINGS: BulletFlag[] = [];
const MAX_REWRITE_FINDINGS = 20;
const BRACKETED_TEXT = /\[[^\]\r\n]+\]/g;
const METRIC_PLACEHOLDER = /^\[(?:[NXYZ](?:%|\s[^\]\r\n]+)?|\$[A-Z](?:\s[^\]\r\n]+)?)\]$/;

export interface RewriteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  bullet: Bullet | null;
  targetRole: string;
  country: string;
  jdContext?: string;
  versionId?: string;
  findings?: BulletFlag[];
  onAccept: (bulletId: string, newText: string) => void;
}

function fillPlaceholders(template: string, values: Record<string, string>): string {
  let out = template;
  for (const [token, val] of Object.entries(values)) {
    if (val.trim()) out = out.split(token).join(val.trim());
  }
  return out;
}

export function RewriteModal(props: RewriteModalProps) {
  const { open, onOpenChange, resumeId, bullet, targetRole, country, jdContext, onAccept,
    versionId, findings = NO_FINDINGS } = props;
  const [result, setResult] = useState<RewriteResult | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const rewrite = useRewriteBullet();
  const { toast } = useToast();

  useEffect(() => {
    let active = true;
    setResult(null);
    setValues({});
    if (!open || !bullet) return;
    rewrite.mutate(
      { resumeId, bulletId: bullet.id, targetRole, country, jdContext, versionId,
        findings: findings.slice(0, MAX_REWRITE_FINDINGS) },
      {
        onSuccess: (data) => {
          if (!active) return;
          setResult(data);
          setValues(Object.fromEntries(data.placeholders.map((p) => [p.token, ''])));
        },
        onError: (e: any) => {
          if (!active) return;
          if (e?.status === 422) {
            toast({
              title: 'Rewrite rejected',
              description: 'AI tried to invent a number. Please try again.',
              variant: 'destructive',
            });
          } else {
            toast({ title: 'Rewrite failed', description: e?.message, variant: 'destructive' });
          }
          onOpenChange(false);
        },
      },
    );
    return () => { active = false; };
  }, [open, bullet?.id, resumeId, targetRole, country, jdContext, versionId, findings]);

  if (!bullet) return null;
  const filled = result ? fillPlaceholders(result.rewritten, values) : '';
  const blank = Boolean(result && !filled.trim());
  const sourceBrackets = new Set(bullet.text.match(BRACKETED_TEXT) ?? []);
  const unresolved = (filled.match(BRACKETED_TEXT) ?? []).some(
    (token) => METRIC_PLACEHOLDER.test(token) || !sourceBrackets.has(token),
  );
  const incomplete = unresolved || result?.placeholders.some((p) => !values[p.token]?.trim() || filled.includes(p.token));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[calc(100dvh-2rem)] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Rewrite bullet</DialogTitle>
          <DialogDescription>
            Review the suggested rewrite, fill any placeholders, and accept it only when it reflects your actual experience.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {findings.length > 0 && (
            <section aria-label="Why this bullet was flagged" className="space-y-2">
              <h3 className="font-semibold">Why this bullet was flagged</h3>
              {findings.map((finding, index) => <div key={`${finding.category}-${index}`}>
                <p className="text-xs capitalize opacity-70">{finding.severity} · {finding.category}</p>
                <p className="text-sm">{finding.reason}</p>
              </div>)}
            </section>
          )}
          <div>
            <Label className="text-xs uppercase opacity-70">Original</Label>
            <p className="text-sm bg-app-text/5 p-2 rounded">{bullet.text}</p>
          </div>

          {rewrite.isPending && <p className="text-sm opacity-60">Rewriting…</p>}

          {result && (
            <>
              <div>
                <Label className="text-xs uppercase opacity-70">Suggested</Label>
                <p className="text-sm bg-app-accent/10 p-2 rounded">{filled}</p>
              </div>

              {result.placeholders.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs uppercase opacity-70">Fill in</Label>
                  {result.placeholders.map((p) => (
                    <div key={p.token} className="flex items-center gap-2">
                      <code className="text-xs bg-app-text/5 px-1 rounded">{p.token}</code>
                      <input
                        aria-label={p.what}
                        data-testid={`placeholder-${p.token}`}
                        className="flex-1 border rounded px-2 py-1 text-sm"
                        placeholder={p.what}
                        value={values[p.token] || ''}
                        onChange={(e) => setValues({ ...values, [p.token]: e.target.value })}
                      />
                    </div>
                  ))}
                </div>
              )}

              {result.applied_changes.length > 0 && (
                <ul className="text-xs opacity-70 list-disc ml-5">
                  {result.applied_changes.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              )}
            </>
          )}
        </div>

        {blank && <p className="text-sm" role="status">The suggestion is empty. Cancel and request another suggestion.</p>}
        {!blank && incomplete && <p className="text-sm" role="status">Complete every bracketed field before accepting. If a field is missing, cancel and request another suggestion.</p>}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            disabled={!result || rewrite.isPending || incomplete || blank}
            onClick={() => {
              if (!result || rewrite.isPending || incomplete || blank) return;
              onAccept(bullet.id, filled);
              onOpenChange(false);
            }}
          >
            Accept
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

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
import type { Bullet, RewriteResult } from '@/app/lib/api';

export interface RewriteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  bullet: Bullet | null;
  targetRole: string;
  country: string;
  jdContext?: string;
  onAccept: (bulletId: string, newText: string) => void;
}

function fillPlaceholders(template: string, values: Record<string, string>): string {
  let out = template;
  for (const [token, val] of Object.entries(values)) {
    if (val) out = out.split(token).join(val);
  }
  return out;
}

export function RewriteModal(props: RewriteModalProps) {
  const { open, onOpenChange, resumeId, bullet, targetRole, country, jdContext, onAccept } = props;
  const [result, setResult] = useState<RewriteResult | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const rewrite = useRewriteBullet();
  const { toast } = useToast();

  useEffect(() => {
    if (!open || !bullet) { setResult(null); setValues({}); return; }
    rewrite.mutate(
      { resumeId, bulletId: bullet.id, targetRole, country, jdContext },
      {
        onSuccess: (data) => {
          setResult(data);
          setValues(Object.fromEntries(data.placeholders.map((p) => [p.token, ''])));
        },
        onError: (e: any) => {
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
  }, [open, bullet?.id]);

  if (!bullet) return null;
  const filled = result ? fillPlaceholders(result.rewritten, values) : '';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Rewrite bullet</DialogTitle>
          <DialogDescription>
            Review the suggested rewrite, fill any placeholders, and accept it only when it reflects your actual experience.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
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

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            disabled={!result}
            onClick={() => {
              if (!result) return;
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

// frontend/src/components/jd/diff-view.tsx
"use client";
import { useMemo, useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChangeCard } from './change-card';
import { useCreateVersion } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import type { DiffPlan, ChangeItem } from '@/app/lib/api';

type Selection = {
  bullets: Record<string, boolean>;
  skillsReorder: boolean;
  summaryRewrite: boolean;
};

export interface DiffViewProps {
  resumeId: string;
  plan: DiffPlan;
  onApplied: (versionId: string) => void;
  /** When provided the internal Apply button is hidden; the parent drives Apply. */
  onAcceptedChangesChange?: (items: ChangeItem[]) => void;
}

export function DiffView({ resumeId, plan, onApplied, onAcceptedChangesChange }: DiffViewProps) {
  const { toast } = useToast();
  const createVersion = useCreateVersion();
  const initial: Selection = useMemo(() => ({
    bullets: Object.fromEntries(plan.bullets.map((b) => [b.bullet_id, true])),
    skillsReorder: !!plan.skills_reorder,
    summaryRewrite: !!plan.summary_rewrite,
  }), [plan]);
  const [sel, setSel] = useState<Selection>(initial);

  const buildChangeSet = (): ChangeItem[] => {
    const out: ChangeItem[] = [];
    for (const b of plan.bullets) {
      if (sel.bullets[b.bullet_id]) {
        out.push({ type: 'bullet_update', bullet_id: b.bullet_id, new_text: b.new });
      }
    }
    if (sel.skillsReorder && plan.skills_reorder) {
      out.push({ type: 'skills_reorder', new_skills_order: plan.skills_reorder.new_order });
    }
    if (sel.summaryRewrite && plan.summary_rewrite) {
      out.push({ type: 'summary_update', new_summary: plan.summary_rewrite.new });
    }
    return out;
  };

  const acceptedCount =
    Object.values(sel.bullets).filter(Boolean).length +
    (sel.skillsReorder ? 1 : 0) +
    (sel.summaryRewrite ? 1 : 0);

  // Notify parent whenever the accepted change set changes
  useEffect(() => {
    onAcceptedChangesChange?.(buildChangeSet());
  }, [sel]);

  const onApply = async () => {
    const cs = buildChangeSet();
    if (cs.length === 0) {
      toast({ title: 'Select at least one change', variant: 'destructive' });
      return;
    }
    try {
      const res = await createVersion.mutateAsync({ resumeId, body: { change_set: cs } });
      toast({ title: 'Version saved', description: `Version ${res.version_id.slice(0, 8)}` });
      onApplied(res.version_id);
    } catch (e: any) {
      toast({ title: 'Save failed', description: e?.message, variant: 'destructive' });
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row justify-between items-center">
        <CardTitle>Proposed changes</CardTitle>
        {!onAcceptedChangesChange && (
          <Button
            onClick={onApply}
            disabled={acceptedCount === 0 || createVersion.isPending}
            data-testid="apply-changes"
          >
            {createVersion.isPending ? 'Saving…' : `Apply ${acceptedCount}`}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {plan.bullets.map((b) => (
          <ChangeCard
            key={b.bullet_id}
            testId={`change-bullet-${b.bullet_id}`}
            title="Bullet rewrite"
            reason={b.reason}
            before={b.old}
            after={b.new}
            accepted={!!sel.bullets[b.bullet_id]}
            onToggle={(v) =>
              setSel((s) => ({ ...s, bullets: { ...s.bullets, [b.bullet_id]: v } }))
            }
          />
        ))}
        {plan.skills_reorder && (
          <ChangeCard
            testId="change-skills"
            title="Skills reorder"
            reason={plan.skills_reorder.rationale}
            before={null}
            after={plan.skills_reorder.new_order.join(' · ')}
            accepted={sel.skillsReorder}
            onToggle={(v) => setSel((s) => ({ ...s, skillsReorder: v }))}
          />
        )}
        {plan.summary_rewrite && (
          <ChangeCard
            testId="change-summary"
            title="Summary rewrite"
            reason={plan.summary_rewrite.reason}
            before={plan.summary_rewrite.old}
            after={plan.summary_rewrite.new}
            accepted={sel.summaryRewrite}
            onToggle={(v) => setSel((s) => ({ ...s, summaryRewrite: v }))}
          />
        )}
      </CardContent>
    </Card>
  );
}

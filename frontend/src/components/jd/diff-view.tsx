// frontend/src/components/jd/diff-view.tsx
"use client";
import { useMemo, useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChangeCard } from './change-card';
import { useCreateVersion } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import { jdApi } from '@/app/lib/api';
import type { BulletOption, DiffPlan, ChangeItem } from '@/app/lib/api';

type Selection = {
  bullets: Record<string, boolean>;
  skillsReorder: boolean;
  summaryRewrite: boolean;
};

type PointerState = {
  options: BulletOption[];
  selectedOptionId: string;
  text: string;
};

export interface DiffViewProps {
  resumeId: string;
  jdEvaluationId?: string;
  plan: DiffPlan;
  onApplied: (versionId: string) => void;
  /** When provided the internal Apply button is hidden; the parent drives Apply. */
  onAcceptedChangesChange?: (items: ChangeItem[]) => void;
}

function defaultOptions(diff: DiffPlan['bullets'][number]): BulletOption[] {
  return diff.options && diff.options.length > 0
    ? diff.options
    : [{
        option_id: 'recommended',
        text: diff.new,
        reason: diff.reason,
        placeholders: diff.placeholders,
      }];
}

function buildPointerState(plan: DiffPlan): Record<string, PointerState> {
  return Object.fromEntries(plan.bullets.map((bullet) => {
    const options = defaultOptions(bullet);
    const selected = options[0];
    return [
      bullet.bullet_id,
      {
        options,
        selectedOptionId: selected.option_id,
        text: selected.text,
      },
    ];
  }));
}

export function DiffView({ resumeId, jdEvaluationId, plan, onApplied, onAcceptedChangesChange }: DiffViewProps) {
  const { toast } = useToast();
  const createVersion = useCreateVersion();
  const initial: Selection = useMemo(() => ({
    bullets: Object.fromEntries(plan.bullets.map((b) => [b.bullet_id, true])),
    skillsReorder: !!plan.skills_reorder,
    summaryRewrite: !!plan.summary_rewrite,
  }), [plan]);
  const [sel, setSel] = useState<Selection>(initial);
  const [pointerState, setPointerState] = useState<Record<string, PointerState>>(
    () => buildPointerState(plan)
  );
  const [regeneratingBulletId, setRegeneratingBulletId] = useState<string | null>(null);

  useEffect(() => {
    setSel(initial);
    setPointerState(buildPointerState(plan));
  }, [initial, plan]);

  const buildChangeSet = (): ChangeItem[] => {
    const out: ChangeItem[] = [];
    for (const b of plan.bullets) {
      if (sel.bullets[b.bullet_id]) {
        out.push({
          type: 'bullet_update',
          bullet_id: b.bullet_id,
          new_text: pointerState[b.bullet_id]?.text || b.new,
        });
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
  const fitByBulletId = useMemo(
    () => Object.fromEntries((plan.bullet_fit || []).map((item) => [item.bullet_id, item])),
    [plan.bullet_fit]
  );

  // Notify parent whenever the accepted change set changes
  useEffect(() => {
    onAcceptedChangesChange?.(buildChangeSet());
  }, [sel, pointerState]);

  const setAll = (accepted: boolean) => {
    setSel((current) => ({
      ...current,
      bullets: Object.fromEntries(Object.keys(current.bullets).map((id) => [id, accepted])),
      skillsReorder: plan.skills_reorder ? accepted : false,
      summaryRewrite: plan.summary_rewrite ? accepted : false,
    }));
  };

  const resetAll = () => {
    setSel(initial);
    setPointerState(buildPointerState(plan));
  };

  const selectOption = (bulletId: string, optionId: string) => {
    setPointerState((current) => {
      const state = current[bulletId];
      const option = state?.options.find((item) => item.option_id === optionId);
      if (!state || !option) return current;
      return {
        ...current,
        [bulletId]: {
          ...state,
          selectedOptionId: optionId,
          text: option.text,
        },
      };
    });
  };

  const editPointerText = (bulletId: string, text: string) => {
    setPointerState((current) => ({
      ...current,
      [bulletId]: {
        ...current[bulletId],
        text,
      },
    }));
  };

  const resetPointer = (bulletId: string) => {
    const bullet = plan.bullets.find((item) => item.bullet_id === bulletId);
    if (!bullet) return;
    const options = defaultOptions(bullet);
    setPointerState((current) => ({
      ...current,
      [bulletId]: {
        options,
        selectedOptionId: options[0].option_id,
        text: options[0].text,
      },
    }));
  };

  const regeneratePointer = async (bulletId: string) => {
    if (!jdEvaluationId) return;
    try {
      setRegeneratingBulletId(bulletId);
      const regenerated = await jdApi.regenerateBulletOptions(jdEvaluationId, bulletId);
      const options = defaultOptions(regenerated);
      setPointerState((current) => ({
        ...current,
        [bulletId]: {
          options,
          selectedOptionId: options[0].option_id,
          text: options[0].text,
        },
      }));
      toast({ title: 'Pointer regenerated', description: 'Three new options are ready.' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Regenerate failed';
      toast({ title: 'Regenerate failed', description: message, variant: 'destructive' });
    } finally {
      setRegeneratingBulletId(null);
    }
  };

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
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => setAll(true)}>
            Select all
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => setAll(false)}>
            Clear all
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={resetAll}>
            Reset all
          </Button>
          {!onAcceptedChangesChange && (
            <Button
              onClick={onApply}
              disabled={acceptedCount === 0 || createVersion.isPending}
              data-testid="apply-changes"
            >
              {createVersion.isPending ? 'Saving...' : `Apply ${acceptedCount}`}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {plan.content_budget && (
          <div className="rounded-sm border bg-muted/30 p-3 text-xs text-muted-foreground">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold uppercase tracking-wide text-foreground">
                Resume fit target: {plan.content_budget.target_max_pages} page{plan.content_budget.target_max_pages === 1 ? '' : 's'}
              </span>
              <span className="uppercase">
                {plan.content_budget.current_bullet_count}/{plan.content_budget.recommended_bullet_budget} bullet budget · {plan.content_budget.page_fit_risk} risk
              </span>
            </div>
            <p className="mt-1">{plan.content_budget.guidance}</p>
          </div>
        )}
        {plan.bullets.map((b) => {
          const state = pointerState[b.bullet_id];
          const selectedOption = state?.options.find((option) => option.option_id === state.selectedOptionId);
          return (
            <ChangeCard
              key={b.bullet_id}
              testId={`change-bullet-${b.bullet_id}`}
              title="Bullet rewrite"
              reason={selectedOption?.reason || b.reason}
              before={b.old}
              after={state?.text || b.new}
              accepted={!!sel.bullets[b.bullet_id]}
              options={state?.options}
              selectedOptionId={state?.selectedOptionId}
              editedText={state?.text || b.new}
              regenerating={regeneratingBulletId === b.bullet_id}
              fitSignal={fitByBulletId[b.bullet_id]}
              onToggle={(v) =>
                setSel((s) => ({ ...s, bullets: { ...s.bullets, [b.bullet_id]: v } }))
              }
              onOptionChange={(optionId) => selectOption(b.bullet_id, optionId)}
              onTextChange={(text) => editPointerText(b.bullet_id, text)}
              onReset={() => resetPointer(b.bullet_id)}
              onRegenerate={jdEvaluationId ? () => regeneratePointer(b.bullet_id) : undefined}
            />
          );
        })}
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

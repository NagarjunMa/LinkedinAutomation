// frontend/src/components/jd/change-card.tsx
"use client";
import { RefreshCw, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import type { BulletFitSignal, BulletOption } from '@/app/lib/api';

export interface ChangeCardProps {
  title: string;
  reason: string;
  before: string | null;
  after: string;
  accepted: boolean;
  onToggle: (accepted: boolean) => void;
  options?: BulletOption[];
  selectedOptionId?: string;
  editedText?: string;
  regenerating?: boolean;
  onOptionChange?: (optionId: string) => void;
  onTextChange?: (text: string) => void;
  onReset?: () => void;
  onRegenerate?: () => void;
  fitSignal?: BulletFitSignal;
  testId?: string;
}

function signalTone(value?: 'low' | 'medium' | 'high') {
  if (value === 'high') return 'border-red-500/30 bg-red-500/10 text-red-700';
  if (value === 'medium') return 'border-amber-500/30 bg-amber-500/10 text-amber-700';
  return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700';
}

export function ChangeCard(props: ChangeCardProps) {
  const editable = props.onTextChange && props.editedText !== undefined;
  const fitTone = props.fitSignal?.recommendation === 'keep'
    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700'
    : props.fitSignal?.recommendation === 'rewrite'
      ? 'border-amber-500/30 bg-amber-500/10 text-amber-700'
      : 'border-red-500/30 bg-red-500/10 text-red-700';
  return (
    <div
      data-testid={props.testId}
      className="border rounded p-3 flex gap-3 items-start"
    >
      <Checkbox
        checked={props.accepted}
        onCheckedChange={(v) => props.onToggle(Boolean(v))}
        aria-label="Accept change"
      />
      <div className="flex-1 space-y-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs uppercase opacity-70">{props.title}</p>
            {props.fitSignal && (
              <span className={`rounded-sm border px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${fitTone}`}>
                {props.fitSignal.recommendation.replace('_', ' ')} · {props.fitSignal.relevance_score}
              </span>
            )}
          </div>
          {(props.options?.length || props.onRegenerate || props.onReset) && (
            <div className="flex flex-wrap items-center gap-2">
              {props.options && props.options.length > 0 && (
                <select
                  className="h-8 rounded border border-input bg-background px-2 text-xs"
                  value={props.selectedOptionId}
                  onChange={(event) => props.onOptionChange?.(event.target.value)}
                  aria-label="Pointer option"
                >
                  {props.options.map((option) => (
                    <option key={option.option_id} value={option.option_id}>
                      {option.option_id}
                    </option>
                  ))}
                </select>
              )}
              {props.onReset && (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={props.onReset}
                  aria-label="Reset pointer"
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
              )}
              {props.onRegenerate && (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={props.onRegenerate}
                  disabled={props.regenerating}
                  aria-label="Regenerate pointer"
                >
                  <RefreshCw className={props.regenerating ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
                </Button>
              )}
            </div>
          )}
        </div>
        {props.before && (
          <p className="text-sm bg-red-500/10 p-2 rounded line-through opacity-70">
            {props.before}
          </p>
        )}
        {editable ? (
          <Textarea
            value={props.editedText}
            onChange={(event) => props.onTextChange?.(event.target.value)}
            className="min-h-[88px] bg-emerald-500/10"
            aria-label="Generated pointer text"
          />
        ) : (
          <p className="text-sm bg-emerald-500/10 p-2 rounded">{props.after}</p>
        )}
        <div className="space-y-1">
          <p className="text-xs opacity-60">{props.reason}</p>
          {props.fitSignal && (
            <div className="space-y-2 rounded-sm border border-border/70 bg-muted/30 p-3 text-xs">
              <p className="font-medium text-foreground">
                {props.fitSignal.why_stronger || props.fitSignal.rationale}
              </p>
              <div className="flex flex-wrap gap-2">
                <span className={`rounded-sm border px-2 py-1 font-semibold uppercase tracking-wide ${signalTone(props.fitSignal.page_cost)}`}>
                  Page cost: {props.fitSignal.page_cost || 'low'}
                </span>
                <span className={`rounded-sm border px-2 py-1 font-semibold uppercase tracking-wide ${signalTone(props.fitSignal.truth_risk)}`}>
                  Truth risk: {props.fitSignal.truth_risk || 'low'}
                </span>
                {props.fitSignal.matched_requirements.length > 0 && (
                  <span className="rounded-sm border border-blue-500/30 bg-blue-500/10 px-2 py-1 font-semibold uppercase tracking-wide text-blue-700">
                    Matches: {props.fitSignal.matched_requirements.join(', ')}
                  </span>
                )}
              </div>
              {props.fitSignal.matched_jd_phrases && props.fitSignal.matched_jd_phrases.length > 0 && (
                <div>
                  <p className="font-semibold uppercase tracking-wide text-muted-foreground">JD evidence</p>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-muted-foreground">
                    {props.fitSignal.matched_jd_phrases.slice(0, 2).map((phrase, index) => (
                      <li key={`${phrase}-${index}`}>{phrase}</li>
                    ))}
                  </ul>
                </div>
              )}
              {props.fitSignal.source_resume_evidence && props.fitSignal.source_resume_evidence.length > 0 && (
                <div>
                  <p className="font-semibold uppercase tracking-wide text-muted-foreground">Resume evidence</p>
                  <p className="mt-1 text-muted-foreground">{props.fitSignal.source_resume_evidence[0]}</p>
                </div>
              )}
              {props.fitSignal.noise_flags.length > 0 && (
                <p className="text-muted-foreground">
                  Flags: {props.fitSignal.noise_flags.join(', ')}.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// frontend/src/components/jd/change-card.tsx
"use client";
import { RefreshCw, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import type { BulletOption } from '@/app/lib/api';

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
  testId?: string;
}

export function ChangeCard(props: ChangeCardProps) {
  const editable = props.onTextChange && props.editedText !== undefined;
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
          <p className="text-xs uppercase opacity-70">{props.title}</p>
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
        <p className="text-xs opacity-60">{props.reason}</p>
      </div>
    </div>
  );
}

// frontend/src/components/jd/change-card.tsx
"use client";
import { Checkbox } from '@/components/ui/checkbox';

export interface ChangeCardProps {
  title: string;
  reason: string;
  before: string | null;
  after: string;
  accepted: boolean;
  onToggle: (accepted: boolean) => void;
  testId?: string;
}

export function ChangeCard(props: ChangeCardProps) {
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
        <p className="text-xs uppercase opacity-70">{props.title}</p>
        {props.before && (
          <p className="text-sm bg-red-500/10 p-2 rounded line-through opacity-70">
            {props.before}
          </p>
        )}
        <p className="text-sm bg-emerald-500/10 p-2 rounded">{props.after}</p>
        <p className="text-xs opacity-60">{props.reason}</p>
      </div>
    </div>
  );
}

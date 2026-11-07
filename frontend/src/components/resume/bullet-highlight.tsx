"use client";
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { Bullet, BulletFlag, Severity } from '@/app/lib/api';

const DOT: Record<Severity, string> = {
  critical: 'bg-red-500',
  warning: 'bg-amber-500',
  info: 'bg-blue-500',
};

export interface BulletHighlightProps {
  bullet: Bullet;
  flags?: BulletFlag[];
  onClick: (bulletId: string) => void;
}

export function BulletHighlight({ bullet, flags: findings = [], onClick }: BulletHighlightProps) {
  const flag = findings.find((f) => f.severity === 'critical')
    ?? findings.find((f) => f.severity === 'warning') ?? findings[0];
  const dot = flag ? DOT[flag.severity] : 'bg-transparent';
  return (
    <li
      data-testid={`bullet-${bullet.id}`}
      data-severity={flag?.severity ?? 'none'}
    >
      <Tooltip>
        <TooltipTrigger asChild>
          <button type="button" onClick={() => onClick(bullet.id)}
            className="flex gap-2 items-start py-1 hover:bg-app-text/5 rounded px-1 text-left w-full focus-visible:outline-2">
            <span className={`mt-2 w-2 h-2 rounded-full shrink-0 ${dot}`} aria-hidden />
            <span className="text-sm">{bullet.text}</span>
          </button>
        </TooltipTrigger>
        {flag && (
          <TooltipContent>
            <p className="text-xs max-w-xs">
              {findings.map((finding, index) => <span key={index} className="block">
                <strong className="capitalize">{finding.severity}</strong> — {finding.reason}
              </span>)}
            </p>
          </TooltipContent>
        )}
      </Tooltip>
    </li>
  );
}

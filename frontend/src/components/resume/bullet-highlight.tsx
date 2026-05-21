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
  flag?: BulletFlag;
  onClick: (bulletId: string) => void;
}

export function BulletHighlight({ bullet, flag, onClick }: BulletHighlightProps) {
  const dot = flag ? DOT[flag.severity] : 'bg-transparent';
  return (
    <li
      data-testid={`bullet-${bullet.id}`}
      data-severity={flag?.severity ?? 'none'}
      className="flex gap-2 items-start py-1 cursor-pointer hover:bg-app-text/5 rounded px-1"
      onClick={() => onClick(bullet.id)}
    >
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={`mt-2 w-2 h-2 rounded-full shrink-0 ${dot}`} aria-hidden />
        </TooltipTrigger>
        {flag && (
          <TooltipContent>
            <p className="text-xs max-w-xs">
              <strong className="capitalize">{flag.severity}</strong> — {flag.reason}
            </p>
          </TooltipContent>
        )}
      </Tooltip>
      <span className="text-sm">{bullet.text}</span>
    </li>
  );
}

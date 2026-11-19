"use client";
import Link from 'next/link';
import { Coins } from 'lucide-react';
import { useCreditsBalance } from '@/hooks/use-credits';

export function CreditsBalanceBadge() {
  const { data, isLoading } = useCreditsBalance();
  const balance = data?.balance ?? 0;
  const low = !isLoading && balance < 3;
  return (
    <Link
      href="/dashboard/credits"
      data-testid="credits-badge"
      className={`flex min-h-11 min-w-11 items-center justify-center gap-1 whitespace-nowrap rounded border px-2 text-xs focus-visible:outline-2 focus-visible:outline-offset-2 ${
        low ? 'border-amber-500 text-amber-500' : 'border-app-text/20'
      }`}
    >
      <Coins aria-hidden="true" className="size-3 shrink-0" />
      {isLoading ? '…' : balance}
    </Link>
  );
}

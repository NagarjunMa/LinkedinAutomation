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
      className={`flex items-center gap-1 text-xs px-2 py-1 rounded border ${
        low ? 'border-amber-500 text-amber-500' : 'border-app-text/20'
      }`}
    >
      <Coins className="w-3 h-3" />
      {isLoading ? '…' : balance}
    </Link>
  );
}

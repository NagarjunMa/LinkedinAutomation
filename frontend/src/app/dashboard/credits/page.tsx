"use client";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreditsBalance } from '@/hooks/use-credits';

export default function CreditsPage() {
  const { data, isLoading, error } = useCreditsBalance();

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Credits</h1>
      </header>
      <Card>
        <CardHeader><CardTitle>Balance</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <p className="text-sm opacity-60">Loading…</p>}
          {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}
          {data && (
            <p className="text-4xl font-bold" data-testid="credits-balance">{data.balance}</p>
          )}
          <p className="text-xs opacity-60 mt-2">
            90 free credits refresh every month. Evaluate: 1 credit · Tailor: 2 credits · Apply: 0 credits · Export: 1 credit
          </p>
        </CardContent>
      </Card>
      <p className="text-xs opacity-60">
        Credits refresh monthly during the freemium launch.
      </p>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { tokens } from '@/lib/api';

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    tokens
      .portfolio()
      .then(setHoldings)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold">Portfolio</h1>
      <p className="text-sm text-forest-400">Simulated holdings · Devnet only</p>

      {error && (
        <p className="mt-4 text-sm text-red-400">
          {error}{' '}
          <Link href="/auth/login" className="text-gold-400 underline">
            Log in
          </Link>
        </p>
      )}

      <div className="mt-6 space-y-3">
        {holdings.length === 0 && !error && (
          <p className="text-forest-500">No holdings yet. Trade on the launchpad.</p>
        )}
        {holdings.map((h) => (
          <Link
            key={h.token_id}
            href={`/token/${h.mint}`}
            className="flex items-center justify-between rounded-xl border border-forest-800 bg-forest-900/40 px-4 py-3 hover:border-forest-600"
          >
            <div>
              <p className="font-medium">{h.name}</p>
              <p className="text-xs text-gold-400">${h.symbol}</p>
            </div>
            <div className="text-right text-sm">
              <p>{(h.amount / 10 ** h.decimals).toLocaleString(undefined, { maximumFractionDigits: 4 })}</p>
              <p className="text-xs text-forest-500">
                ≈ {(h.estimated_value_lamports / 1e9).toFixed(6)} SOL
              </p>
            </div>
          </Link>
        ))}
      </div>

      <p className="mt-8 text-center text-[10px] text-forest-600">
        All values are simulated. Not withdrawable as real money.
      </p>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { tokens } from '@/lib/api';

export default function LaunchpadPage() {
  const [list, setList] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    tokens
      .list()
      .then(setList)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Launchpad</h1>
          <p className="text-sm text-forest-400">Solana Devnet · Simulated bonding curve</p>
        </div>
        <Link
          href="/launchpad/create"
          className="rounded-xl bg-gold-500 px-4 py-2 text-sm font-semibold text-forest-950 hover:bg-gold-400"
        >
          Create token
        </Link>
      </div>

      {error && (
        <p className="mt-4 text-sm text-red-400">{error}</p>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {list.length === 0 && !error && (
          <p className="text-forest-500 col-span-2">No tokens yet. Be the first to launch.</p>
        )}
        {list.map((t) => (
          <Link
            key={t.id}
            href={`/token/${t.mint_address}`}
            className="rounded-2xl border border-forest-800 bg-forest-900/40 p-5 transition hover:border-forest-600"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">{t.name}</h3>
                <p className="text-sm text-gold-400">${t.symbol}</p>
              </div>
              <span className="rounded bg-forest-800 px-2 py-0.5 text-[10px] uppercase text-forest-400">
                {t.network}
              </span>
            </div>
            <p className="mt-3 text-xs text-forest-500">
              Spot ≈ {t.spot_price_sol?.toFixed(10)} SOL
            </p>
            <p className="mt-1 text-[10px] text-forest-600">{t.label}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { tokens } from '@/lib/api';

export default function TokenPage() {
  const { mint } = useParams<{ mint: string }>();
  const [token, setToken] = useState<any>(null);
  const [solAmount, setSolAmount] = useState('0.1');
  const [quote, setQuote] = useState<any>(null);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    if (mint) tokens.getByMint(mint).then(setToken).catch((e) => setErr(e.message));
  }, [mint]);

  async function getQuote() {
    if (!token) return;
    setErr('');
    try {
      const lamports = Math.round(parseFloat(solAmount) * 1e9);
      const q = await tokens.quote(token.id, { side: 'buy', sol_lamports: lamports });
      setQuote(q);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function executeBuy() {
    if (!token) return;
    setMsg('');
    setErr('');
    try {
      const lamports = Math.round(parseFloat(solAmount) * 1e9);
      const order = await tokens.trade(token.id, {
        side: 'buy',
        sol_lamports: lamports,
      });
      setMsg(`Simulated buy filled: ${order.token_amount} tokens`);
      const updated = await tokens.getByMint(mint);
      setToken(updated);
      setQuote(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  if (!token && !err) {
    return <div className="px-4 py-16 text-center text-forest-400">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-8">
      {token && (
        <>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold">{token.name}</h1>
              <p className="text-gold-400">${token.symbol}</p>
            </div>
            <span className="rounded bg-forest-800 px-2 py-1 text-[10px] uppercase text-forest-400">
              {token.network}
            </span>
          </div>
          <p className="mt-2 text-xs text-forest-500 break-all">{token.mint_address}</p>
          <p className="mt-1 text-[10px] text-forest-600">{token.label}</p>

          <div className="mt-6 rounded-xl border border-forest-800 bg-forest-900/50 p-4">
            <p className="text-xs text-forest-400">Spot price</p>
            <p className="text-xl font-semibold">{token.spot_price_sol?.toFixed(12)} SOL</p>
          </div>

          <div className="mt-6 rounded-xl border border-forest-800 p-4">
            <h2 className="font-semibold text-gold-400">Simulated Buy</h2>
            <p className="text-xs text-forest-500">Bonding-curve simulator · not on-chain</p>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={solAmount}
              onChange={(e) => setSolAmount(e.target.value)}
              className="mt-3 w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2 text-sm outline-none focus:border-gold-500"
              placeholder="SOL amount"
            />
            <div className="mt-3 flex gap-2">
              <button
                onClick={getQuote}
                className="flex-1 rounded-lg border border-forest-600 py-2 text-sm hover:bg-forest-900"
              >
                Quote
              </button>
              <button
                onClick={executeBuy}
                className="flex-1 rounded-lg bg-gold-500 py-2 text-sm font-semibold text-forest-950 hover:bg-gold-400"
              >
                Buy (sim)
              </button>
            </div>
            {quote && (
              <div className="mt-3 rounded-lg bg-forest-950 p-3 text-xs text-forest-300">
                <p>Tokens out: {quote.token_amount}</p>
                <p>Price impact: {quote.price_impact_bps} bps</p>
                <p>Price: {quote.price_per_token?.toFixed(12)} SOL</p>
              </div>
            )}
          </div>

          {msg && <p className="mt-4 text-sm text-green-400">{msg}</p>}
          {err && <p className="mt-4 text-sm text-red-400">{err}</p>}
        </>
      )}
      {!token && err && <p className="text-red-400">{err}</p>}
    </div>
  );
}

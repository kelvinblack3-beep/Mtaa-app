'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { tokens } from '@/lib/api';

export default function CreateTokenPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [symbol, setSymbol] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const t = await tokens.create({ name, symbol, description });
      router.push(`/token/${t.mint_address}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-8">
      <h1 className="text-2xl font-bold">Create token</h1>
      <p className="mt-1 text-sm text-forest-400">
        Solana Devnet · Mint address is simulated until independently verified
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {error && (
          <div className="rounded-lg border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}
        <div>
          <label className="mb-1 block text-xs uppercase text-forest-400">Name</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2.5 text-sm outline-none focus:border-gold-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase text-forest-400">Symbol</label>
          <input
            required
            maxLength={10}
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2.5 text-sm outline-none focus:border-gold-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase text-forest-400">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2.5 text-sm outline-none focus:border-gold-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-gold-500 py-3 text-sm font-semibold text-forest-950 hover:bg-gold-400 disabled:opacity-50"
        >
          {loading ? 'Creating…' : 'Launch on Devnet'}
        </button>
      </form>
    </div>
  );
}

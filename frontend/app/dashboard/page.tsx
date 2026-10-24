'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { auth, wallet } from '@/lib/api';

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [balance, setBalance] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const me = await auth.me();
        setUser(me);
        const bal = await wallet.balance();
        setBalance(bal);
      } catch {
        setError('Please log in to view your dashboard.');
      }
    })();
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-forest-300">{error}</p>
        <Link href="/auth/login" className="mt-4 inline-block text-gold-400 hover:underline">
          Log in
        </Link>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center text-forest-400">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-2xl font-bold">
        Habari, {user.display_name || user.username}
      </h1>
      <p className="text-sm text-forest-400">@{user.username} · {user.role}</p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-forest-800 bg-forest-900/50 p-6">
          <p className="text-xs uppercase tracking-wide text-forest-400">KSh Balance</p>
          <p className="mt-1 text-3xl font-bold text-gold-400">
            {balance ? `KES ${balance.balance_kes}` : '—'}
          </p>
          <Link href="/wallet" className="mt-3 inline-block text-sm text-forest-300 hover:text-white">
            Manage wallet →
          </Link>
        </div>
        <div className="rounded-2xl border border-forest-800 bg-forest-900/50 p-6">
          <p className="text-xs uppercase tracking-wide text-forest-400">Quick actions</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/wallet"
              className="rounded-lg bg-forest-800 px-3 py-1.5 text-sm hover:bg-forest-700"
            >
              Deposit
            </Link>
            <Link
              href="/launchpad"
              className="rounded-lg bg-forest-800 px-3 py-1.5 text-sm hover:bg-forest-700"
            >
              Launchpad
            </Link>
            <Link
              href="/portfolio"
              className="rounded-lg bg-forest-800 px-3 py-1.5 text-sm hover:bg-forest-700"
            >
              Portfolio
            </Link>
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-forest-800 bg-forest-950 p-4 text-xs text-forest-500">
        All balances and trades on this platform are simulated or restricted to Solana
        devnet. This is not real money.
      </div>
    </div>
  );
}

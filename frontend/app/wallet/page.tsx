'use client';

import { useEffect, useState } from 'react';
import { wallet } from '@/lib/api';

export default function WalletPage() {
  const [balance, setBalance] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [amount, setAmount] = useState('');
  const [recipient, setRecipient] = useState('');
  const [transferAmount, setTransferAmount] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  async function refresh() {
    try {
      const bal = await wallet.balance();
      setBalance(bal);
      const hist = await wallet.history();
      setHistory(hist);
    } catch {
      setErr('Please log in to view wallet.');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function doDeposit(e: React.FormEvent) {
    e.preventDefault();
    setMsg('');
    setErr('');
    setLoading(true);
    try {
      const res = await wallet.deposit(parseFloat(amount));
      setMsg(`Deposit ${res.status}: KES ${res.amount_kes} (ref ${res.external_reference})`);
      setAmount('');
      await refresh();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function doTransfer(e: React.FormEvent) {
    e.preventDefault();
    setMsg('');
    setErr('');
    setLoading(true);
    try {
      const res = await wallet.transfer(recipient, parseFloat(transferAmount));
      setMsg(`Transferred KES ${res.amount_kes} to @${res.recipient} (${res.reference})`);
      setRecipient('');
      setTransferAmount('');
      await refresh();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold">Wallet</h1>
      <p className="text-sm text-forest-400">KSh · Double-entry ledger · Simulation</p>

      <div className="mt-6 rounded-2xl border border-forest-800 bg-gradient-to-br from-forest-900 to-forest-950 p-6">
        <p className="text-xs uppercase tracking-wide text-forest-400">Available balance</p>
        <p className="mt-1 text-4xl font-bold text-gold-400">
          {balance ? `KES ${balance.balance_kes}` : '—'}
        </p>
        <p className="mt-1 text-xs text-forest-500">
          {balance ? `${balance.balance_cents} cents` : ''}
        </p>
      </div>

      {msg && (
        <div className="mt-4 rounded-lg border border-forest-600 bg-forest-900 px-3 py-2 text-sm text-forest-200">
          {msg}
        </div>
      )}
      {err && (
        <div className="mt-4 rounded-lg border border-red-800 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {err}
        </div>
      )}

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <form onSubmit={doDeposit} className="rounded-xl border border-forest-800 p-4">
          <h2 className="font-semibold text-gold-400">Simulate deposit</h2>
          <p className="mt-1 text-xs text-forest-500">Local simulator · not real M-Pesa</p>
          <input
            type="number"
            step="0.01"
            min="1"
            required
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Amount (KES)"
            className="mt-3 w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2 text-sm outline-none focus:border-gold-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="mt-3 w-full rounded-lg bg-forest-700 py-2 text-sm font-medium hover:bg-forest-600 disabled:opacity-50"
          >
            Deposit
          </button>
        </form>

        <form onSubmit={doTransfer} className="rounded-xl border border-forest-800 p-4">
          <h2 className="font-semibold text-gold-400">Transfer</h2>
          <p className="mt-1 text-xs text-forest-500">Free · username or phone</p>
          <input
            required
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="Recipient username"
            className="mt-3 w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2 text-sm outline-none focus:border-gold-500"
          />
          <input
            type="number"
            step="0.01"
            min="0.01"
            required
            value={transferAmount}
            onChange={(e) => setTransferAmount(e.target.value)}
            placeholder="Amount (KES)"
            className="mt-2 w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2 text-sm outline-none focus:border-gold-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="mt-3 w-full rounded-lg bg-gold-500 py-2 text-sm font-semibold text-forest-950 hover:bg-gold-400 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>

      <div className="mt-10">
        <h2 className="font-semibold">History</h2>
        {history.length === 0 ? (
          <p className="mt-3 text-sm text-forest-500">No transactions yet.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {history.map((h) => (
              <li
                key={h.reference + h.side}
                className="flex items-center justify-between rounded-lg border border-forest-800 px-3 py-2 text-sm"
              >
                <div>
                  <p className="font-medium">{h.description}</p>
                  <p className="text-xs text-forest-500">
                    {h.entry_type} · {h.reference}
                  </p>
                </div>
                <span
                  className={
                    h.side === 'credit' ? 'text-green-400' : 'text-red-400'
                  }
                >
                  {h.side === 'credit' ? '+' : '−'}KES {h.amount_kes}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

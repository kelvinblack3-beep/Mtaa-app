'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { auth } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username_or_email, setIdent] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await auth.login({ username_or_email, password });
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <h1 className="text-2xl font-bold">Welcome back</h1>
      <p className="mt-1 text-sm text-forest-400">Log in to your Mtaa account</p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {error && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-forest-400">
            Username or email
          </label>
          <input
            required
            value={username_or_email}
            onChange={(e) => setIdent(e.target.value)}
            className="w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2.5 text-sm outline-none focus:border-gold-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-forest-400">
            Password
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2.5 text-sm outline-none focus:border-gold-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-gold-500 py-3 text-sm font-semibold text-forest-950 hover:bg-gold-400 disabled:opacity-50"
        >
          {loading ? 'Signing in…' : 'Log in'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-forest-400">
        No account?{' '}
        <Link href="/auth/register" className="text-gold-400 hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}

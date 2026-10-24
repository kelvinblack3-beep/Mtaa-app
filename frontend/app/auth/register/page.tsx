'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { auth } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    phone: '',
    display_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await auth.register(form);
      await auth.login({
        username_or_email: form.username,
        password: form.password,
      });
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <h1 className="text-2xl font-bold">Create account</h1>
      <p className="mt-1 text-sm text-forest-400">Join Mtaa — testnet only</p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {error && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}
        {['username', 'email', 'password', 'phone', 'display_name'].map((field) => (
          <div key={field}>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-forest-400">
              {field.replace('_', ' ')}
              {field === 'phone' || field === 'display_name' ? ' (optional)' : ''}
            </label>
            <input
              type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
              required={field !== 'phone' && field !== 'display_name'}
              value={(form as any)[field]}
              onChange={(e) => setForm({ ...form, [field]: e.target.value })}
              className="w-full rounded-lg border border-forest-700 bg-forest-900 px-3 py-2.5 text-sm outline-none focus:border-gold-500"
              placeholder={
                field === 'phone' ? '+2547...' : field === 'username' ? 'johndoe' : ''
              }
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-gold-500 py-3 text-sm font-semibold text-forest-950 hover:bg-gold-400 disabled:opacity-50"
        >
          {loading ? 'Creating…' : 'Create account'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-forest-400">
        Already have an account?{' '}
        <Link href="/auth/login" className="text-gold-400 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

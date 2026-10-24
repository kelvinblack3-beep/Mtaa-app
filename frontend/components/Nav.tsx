'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const links = [
  { href: '/', label: 'Home' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/wallet', label: 'Wallet' },
  { href: '/launchpad', label: 'Launchpad' },
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/community', label: 'Community' },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-forest-800 bg-forest-950/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-700 text-sm font-bold text-gold-400">
            M
          </span>
          <span className="text-lg font-semibold tracking-tight">Mtaa</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={clsx(
                'rounded-lg px-3 py-1.5 text-sm font-medium transition',
                pathname === l.href || pathname.startsWith(l.href + '/')
                  ? 'bg-forest-800 text-gold-400'
                  : 'text-forest-300 hover:bg-forest-900 hover:text-white'
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            href="/auth/login"
            className="rounded-lg px-3 py-1.5 text-sm text-forest-300 hover:text-white"
          >
            Log in
          </Link>
          <Link
            href="/auth/register"
            className="rounded-lg bg-gold-500 px-3 py-1.5 text-sm font-medium text-forest-950 hover:bg-gold-400"
          >
            Sign up
          </Link>
        </div>
      </div>

      {/* Mobile nav */}
      <nav className="flex gap-1 overflow-x-auto border-t border-forest-900 px-2 py-2 md:hidden">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={clsx(
              'whitespace-nowrap rounded-lg px-3 py-1 text-xs font-medium',
              pathname === l.href
                ? 'bg-forest-800 text-gold-400'
                : 'text-forest-400'
            )}
          >
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}

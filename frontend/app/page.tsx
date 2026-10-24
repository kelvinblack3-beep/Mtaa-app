import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      {/* Hero */}
      <section className="text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-forest-700 bg-forest-900 px-3 py-1 text-xs text-gold-400">
          <span className="h-1.5 w-1.5 rounded-full bg-gold-400" />
          Testnet · Simulation Only
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Your neighbourhood
          <br />
          <span className="text-gold-400">fintech community</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-forest-300">
          KSh wallet, free internal transfers, M-Pesa simulation, and a Solana
          devnet token launchpad — built for Kenya.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/auth/register"
            className="rounded-xl bg-gold-500 px-6 py-3 text-sm font-semibold text-forest-950 hover:bg-gold-400"
          >
            Get started
          </Link>
          <Link
            href="/launchpad"
            className="rounded-xl border border-forest-600 px-6 py-3 text-sm font-medium text-white hover:bg-forest-900"
          >
            Explore launchpad
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[
          {
            title: 'KSh Wallet',
            desc: 'Double-entry ledger, free P2P transfers, simulated M-Pesa deposits.',
            href: '/wallet',
          },
          {
            title: 'Token Launchpad',
            desc: 'Create SPL tokens on Solana devnet with a simulated bonding curve.',
            href: '/launchpad',
          },
          {
            title: 'Community',
            desc: 'Feeds, communities, creator profiles, and moderation tools.',
            href: '/community',
          },
        ].map((f) => (
          <Link
            key={f.title}
            href={f.href}
            className="rounded-2xl border border-forest-800 bg-forest-900/50 p-6 transition hover:border-forest-600"
          >
            <h3 className="text-lg font-semibold text-gold-400">{f.title}</h3>
            <p className="mt-2 text-sm text-forest-300">{f.desc}</p>
          </Link>
        ))}
      </section>

      <section className="mt-16 rounded-2xl border border-forest-800 bg-forest-900/30 p-6 text-center">
        <p className="text-sm text-forest-400">
          <strong className="text-gold-400">Safety notice:</strong> Mtaa is a
          prototype. It does not custody real money, process live M-Pesa, or
          trade on Solana mainnet. All financial activity is simulated or
          restricted to test networks.
        </p>
      </section>
    </div>
  );
}

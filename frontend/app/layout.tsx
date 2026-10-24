import type { Metadata } from 'next';
import './globals.css';
import { Nav } from '@/components/Nav';

export const metadata: Metadata = {
  title: 'Mtaa — Kenyan Fintech & Community',
  description: 'Mobile-first KSh wallet, community, and Solana devnet token launchpad. Testnet only.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <Nav />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-forest-800 py-6 text-center text-sm text-forest-400">
          <p>Mtaa · Testnet / Simulation Only · No real money</p>
          <p className="mt-1 text-xs">Solana Devnet · M-Pesa Sandbox</p>
        </footer>
      </body>
    </html>
  );
}

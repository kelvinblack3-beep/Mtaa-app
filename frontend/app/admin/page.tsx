export default function AdminPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold">Admin</h1>
      <p className="text-sm text-forest-400">Protected · Role required</p>
      <div className="mt-8 rounded-2xl border border-forest-800 bg-forest-900/40 p-6 text-sm text-forest-300">
        <p>
          Administration views for user status, ledger history, payment simulations,
          token review, moderation and audit logs are enforced server-side via role
          checks. Connect authenticated admin sessions to populate this panel.
        </p>
      </div>
    </div>
  );
}

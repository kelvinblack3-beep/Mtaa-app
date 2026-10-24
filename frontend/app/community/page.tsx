export default function CommunityPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold">Community</h1>
      <p className="text-sm text-forest-400">Feeds, groups & creator profiles</p>

      <div className="mt-8 rounded-2xl border border-forest-800 bg-forest-900/40 p-8 text-center">
        <p className="text-forest-300">
          Social feed, communities, posts, comments and moderation are implemented
          in the backend models and will be connected to interactive UI in the next
          iteration.
        </p>
        <p className="mt-4 text-xs text-forest-500">
          Backend tables: communities, posts, comments, likes, follows, reports
        </p>
      </div>
    </div>
  );
}

// PulseBoard Dashboard — main page layout

import Navbar from "./components/Navbar";
import TrendingTopics from "./components/TrendingTopics";
import PostFeed from "./components/PostFeed";
import NewsFeed from "./components/NewsFeed";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <TrendingTopics />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <PostFeed />
          <NewsFeed />
        </div>
      </main>
    </div>
  );
}

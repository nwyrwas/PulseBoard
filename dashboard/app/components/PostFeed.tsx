// Displays recent Hacker News stories with score and comment count

"use client";

import useSWR from "swr";

const fetcher = (url) => fetch(url).then((res) => res.json());

export default function PostFeed() {
  const { data, error, isLoading } = useSWR(
    "http://localhost:8000/hn/stories?limit=10",
    fetcher,
    { refreshInterval: 60000 }
  );

  if (isLoading) return <div className="text-gray-400 p-4">Loading stories...</div>;
  if (error) return <div className="text-red-400 p-4">Failed to load stories</div>;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Hacker News Stories</h2>
      <div className="space-y-4">
        {data?.map((story) => (
          <div key={story.story_id} className="border-b border-gray-700 pb-3">
            <a
              href={story.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              {story.title}
            </a>
            <div className="flex gap-4 mt-1 text-sm text-gray-400">
              <span>Score: {story.score}</span>
              <span>Comments: {story.num_comments}</span>
              <span>By: {story.author}</span>
              <span>Sentiment: {story.sentiment_label}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

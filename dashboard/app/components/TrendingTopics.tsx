"use client";

import useSWR from "swr";

// SWR needs a "fetcher" function — this just wraps fetch() and returns JSON
const fetcher = (url) => fetch(url).then((res) => res.json());

export default function TrendingTopics() {
  const { data, error, isLoading } = useSWR(
    "http://localhost:8000/trending",
    fetcher,
    { refreshInterval: 60000 } // re-fetch every 60 seconds
  );

  if (isLoading) return <div className="text-gray-400 p-4">Loading trends...</div>;
  if (error) return <div className="text-red-400 p-4">Failed to load trends</div>;

  // Find the max mention count for scaling the bars
  const maxCount = data?.length ? Math.max(...data.map((t) => t.mention_count)) : 1;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Trending Topics</h2>
      <div className="space-y-3">
        {data?.map((topic) => (
          <div key={topic.topic} className="flex items-center gap-4">
            <span className="text-gray-400 font-mono w-6">#{topic.topic_rank}</span>
            <div className="flex-1">
              <div className="flex justify-between mb-1">
                <span className="text-white font-medium capitalize">{topic.topic}</span>
                <span className="text-gray-400 text-sm">{topic.mention_count} mentions</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(topic.mention_count / maxCount) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

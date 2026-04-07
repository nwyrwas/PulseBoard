// Displays recent news headlines with source and published time

"use client";

import useSWR from "swr";

const fetcher = (url) => fetch(url).then((res) => res.json());

export default function NewsFeed() {
  const { data, error, isLoading } = useSWR(
    "http://localhost:8000/news/articles?limit=10",
    fetcher,
    { refreshInterval: 60000 }
  );

  if (isLoading) return <div className="text-gray-400 p-4">Loading articles...</div>;
  if (error) return <div className="text-red-400 p-4">Failed to load articles</div>;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">News Headlines</h2>
      <div className="space-y-4">
        {data?.map((article) => (
          <div key={article.article_id} className="border-b border-gray-700 pb-3">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              {article.title}
            </a>
            <div className="flex gap-4 mt-1 text-sm text-gray-400">
              <span>Source: {article.source_name}</span>
              <span>
                Published: {new Date(article.published_at).toLocaleDateString()}
              </span>
              <span>
                Sentiment: {article.sentiment_label}
              </span>
              <span className="capitalize">Topic: {article.topic}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

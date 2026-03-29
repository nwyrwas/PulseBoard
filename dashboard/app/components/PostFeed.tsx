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


  // target="_blank" - causes the user when clicking on a link to open a new tab to open the link
  // rel="noopener noreferrer" - removes window.opener so the new tab can go back to the original page
    // tab-napping
    // security measure so that the reference cant redirect the original page to a phishing site
    // noreferrer stops the browser from sending the referer head to the destination site so they do not know where the user came from.

  // Security best practice for any link that opens in a new tab.
    // Prevents the new tab from accessing the original page through window.opener, protecting against tab-napping attacks.
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

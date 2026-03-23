"""
hn_fetcher.py
-------------
Fetches top stories from the Hacker News API (no auth required).
This is PulseBoard's Hacker News ingestion layer.

API docs: https://github.com/HackerNews/API

Usage:
    python ingest/hn_fetcher.py
"""

import requests
from datetime import datetime, timezone

# Hacker News API base URL — free, no keys needed
HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


def fetch_top_story_ids(limit=10):
    """
    Fetch the IDs of the current top stories on Hacker News.

    The API returns up to 500 story IDs ranked by score.
    We slice to our desired limit.
    """
    url = f"{HN_BASE_URL}/topstories.json"
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request failed
    story_ids = response.json()
    return story_ids[:limit]


def fetch_story_details(story_id):
    """
    Fetch the full details for a single story by its ID.

    Returns a clean dict with only the fields we care about.
    """
    url = f"{HN_BASE_URL}/item/{story_id}.json"
    response = requests.get(url)
    response.raise_for_status()
    item = response.json()

    # Some items can be None (deleted stories), skip those
    if item is None:
        return None

    # Convert Unix timestamp to readable datetime
    created_dt = datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc)

    return {
        "story_id": item.get("id"),
        "title": item.get("title", ""),
        "score": item.get("score", 0),
        "num_comments": item.get("descendants", 0),
        "url": item.get("url", ""),
        "created_utc": created_dt.isoformat(),
        "author": item.get("by", ""),
        "source": "hackernews",
    }


def fetch_top_stories(limit=10):
    """
    Fetch top stories with full details.

    This is the main function other parts of the pipeline will call.
    """
    story_ids = fetch_top_story_ids(limit=limit)
    stories = []

    for story_id in story_ids:
        story = fetch_story_details(story_id)
        if story is not None:
            stories.append(story)

    return stories


if __name__ == "__main__":
    # --- Configuration ---
    STORY_LIMIT = 10

    print(f"Fetching top {STORY_LIMIT} stories from Hacker News...\n")

    stories = fetch_top_stories(limit=STORY_LIMIT)

    print(f"{'='*60}")
    print(f"  Hacker News — Top {STORY_LIMIT} stories")
    print(f"{'='*60}")

    for i, story in enumerate(stories, 1):
        print(f"\n  [{i}] {story['title']}")
        print(f"      Score: {story['score']} | Comments: {story['num_comments']}")
        print(f"      URL: {story['url']}")
        print(f"      Author: {story['author']}")
        print(f"      Posted: {story['created_utc']}")

    print(f"\n✅ Successfully fetched {len(stories)} stories!")

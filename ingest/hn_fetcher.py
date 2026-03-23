"""
hn_fetcher.py
-------------
Fetches top stories from the Hacker News API and upserts them
into PostgreSQL (raw.hn_stories table).

API docs: https://github.com/HackerNews/API

Usage:
    python ingest/hn_fetcher.py
"""

import requests
import psycopg2
from datetime import datetime, timezone

# Hacker News API base URL — free, no keys needed
HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"

# PostgreSQL connection config
DB_CONFIG = {
    "dbname": "pulseboard",
    "user": "nickwyrwas",
    "host": "localhost",
    "port": 5432,
}


def fetch_top_story_ids(limit=10):
    """
    Fetch the IDs of the current top stories on Hacker News.

    The API returns up to 500 story IDs ranked by score.
    We slice to our desired limit.
    """
    url = f"{HN_BASE_URL}/topstories.json"
    response = requests.get(url)
    response.raise_for_status()
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

    if item is None:
        return None

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


def upsert_stories(stories):
    """
    Insert stories into raw.hn_stories, skipping any that already exist.

    Uses INSERT ... ON CONFLICT DO NOTHING to make this idempotent —
    safe to run multiple times without creating duplicates.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO raw.hn_stories (story_id, title, score, num_comments, url, author, created_utc, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (story_id) DO NOTHING;
    """

    inserted = 0
    for story in stories:
        cur.execute(insert_query, (
            story["story_id"],
            story["title"],
            story["score"],
            story["num_comments"],
            story["url"],
            story["author"],
            story["created_utc"],
            story["source"],
        ))
        # rowcount is 1 if inserted, 0 if skipped (duplicate)
        inserted += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return inserted


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

    # Save to database
    print(f"\nSaving to PostgreSQL...")
    inserted = upsert_stories(stories)
    print(f"✅ Done! Inserted {inserted} new stories ({len(stories) - inserted} already existed)")

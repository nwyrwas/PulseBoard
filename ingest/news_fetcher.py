"""
news_fetcher.py
---------------
Fetches top headlines from NewsAPI.org by topic and upserts them
into PostgreSQL (raw.news_articles table).

API docs: https://newsapi.org/docs

Usage:
    python ingest/news_fetcher.py
"""

import os
import hashlib
import requests
import psycopg2
from dotenv import load_dotenv
from sentiment import analyze_sentiment

# Load API key from .env
load_dotenv()

NEWS_API_URL = "https://newsapi.org/v2/everything"

# PostgreSQL connection config
DB_CONFIG = {
    "dbname": "pulseboard",
    "user": "nickwyrwas",
    "host": "localhost",
    "port": 5432,
}


def make_article_id(url):
    """
    Create a unique ID for an article by hashing its URL.

    We use MD5 here — not for security, just for a short, consistent hash.
    The same URL will always produce the same ID, which is what we need
    for our upsert to detect duplicates.
    """
    return hashlib.md5(url.encode()).hexdigest()


def fetch_articles(topic, limit=10):
    """
    Search NewsAPI for articles matching a topic keyword.

    Args:
        topic: Search keyword (e.g. "technology", "politics", "sports")
        limit: Number of articles to fetch (max 100 on free tier)

    Returns:
        List of dicts with article data
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY not found in .env file!")

    params = {
        "q": topic,
        "pageSize": limit,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": api_key,
    }

    response = requests.get(NEWS_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")

    articles = []
    for article in data.get("articles", []):
        # Skip articles with missing URLs (can't create a unique ID without one)
        if not article.get("url"):
            continue

        article_data = {
            "article_id": make_article_id(article["url"]),
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article["url"],
            "source_name": article.get("source", {}).get("name", ""),
            "published_at": article.get("publishedAt"),
            "topic": topic,
        }

        sentiment = analyze_sentiment(article_data["title"])
        article_data["sentiment_score"] = sentiment["score"]
        article_data["sentiment_label"] = sentiment["label"]

        articles.append(article_data)


    return articles


def upsert_articles(articles):
    """
    Insert articles into raw.news_articles, skipping duplicates.

    Same upsert pattern as hn_fetcher.py — ON CONFLICT DO NOTHING.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO raw.news_articles (article_id, title, description, url, source_name, published_at, topic, sentiment_score, sentiment_label)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (article_id) DO NOTHING;
    """

    inserted = 0
    for article in articles:
        cur.execute(insert_query, (
            article["article_id"],
            article["title"],
            article["description"],
            article["url"],
            article["source_name"],
            article["published_at"],
            article["topic"],
            article["sentiment_score"],
            article["sentiment_label"]
        ))
        inserted += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return inserted


if __name__ == "__main__":
    # --- Configuration ---
    TOPICS = ["technology", "business"]
    ARTICLE_LIMIT = 5

    for topic in TOPICS:
        print(f"\n{'='*60}")
        print(f"  NewsAPI — '{topic}' (top {ARTICLE_LIMIT} articles)")
        print(f"{'='*60}")

        articles = fetch_articles(topic, limit=ARTICLE_LIMIT)

        for i, article in enumerate(articles, 1):
            print(f"\n  [{i}] {article['title']}")
            print(f"      Source: {article['source_name']}")
            print(f"      URL: {article['url']}")
            print(f"      Published: {article['published_at']}")
            print(f"      Sentiment: {article['sentiment_label']} ({article['sentiment_score']})")

        # Save to database
        inserted = upsert_articles(articles)
        print(f"\n  ✅ Inserted {inserted} new articles ({len(articles) - inserted} already existed)")

    print(f"\nDone!")

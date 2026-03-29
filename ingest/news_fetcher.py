"""
news_fetcher.py
---------------
Fetches top headlines from NewsAPI.org by topic and upserts them
into PostgreSQL (raw.news_articles table).

API docs: https://newsapi.org/docs

Usage:
    python ingest/news_fetcher.py
"""
# os is going to be used to access the .env file and the environment variables stored in it.
    # without having to hardcode any API keys or secret variables into the code.
# hashlib would be used for hashing variables
import os
import hashlib
import requests
import psycopg2
from dotenv import load_dotenv

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

    # used to give each article its own unique ID
    # url.encode() - converts the URL string into bytes, due to hashlib working with bytes
    # hashlib.md5 - runs the md5 hashing algorithm on the bytes generated.
    # .hexdigest() - helps convert the raw hash output into a readable hex string

    # Chose md5 due to it being fast and producing consistent fixed-length output. I would choose something more secure if protecting passwords.
    
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

        articles.append({
            "article_id": make_article_id(article["url"]),
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article["url"],

            # article.get("source", {}) - gets the source field. If it doesnt exist it returns a empty dictionary
            # .get("name", "") - would try to get the name of what was retrieved in the previous step. if not present returns an empty string.
            # Coding it this way if the fields are missing allows us to avoid an unexpected crash if fields are missing.
            "source_name": article.get("source", {}).get("name", ""),
            "published_at": article.get("publishedAt"),
            "topic": topic,
        })

    return articles


def upsert_articles(articles):
    """
    Insert articles into raw.news_articles, skipping duplicates.

    Same upsert pattern as hn_fetcher.py — ON CONFLICT DO NOTHING.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO raw.news_articles (article_id, title, description, url, source_name, published_at, topic)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
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

        # Save to database
        inserted = upsert_articles(articles)
        print(f"\n  ✅ Inserted {inserted} new articles ({len(articles) - inserted} already existed)")

    print(f"\nDone!")

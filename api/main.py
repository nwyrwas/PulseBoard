from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="PulseBoard API")

# CORS middleware — allows the Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # we'll lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    """Create a database connection."""
    return psycopg2.connect(
        dbname="pulseboard",
        host="localhost",
        port=5432,
        cursor_factory=RealDictCursor,  # returns rows as dictionaries
    )

@app.get("/trending")
def get_trending(hours: int = Query(default=168, description="Hours to look back")):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM raw.mart_trending_topics;")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.get("/hn/stories")
def get_hn_stories(limit: int = Query(default=20, description="Number of stories")):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM raw.hn_stories ORDER BY created_utc DESC LIMIT %s;",
        (limit,)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.get("/news/articles")
def get_news_articles(
    topic: str = Query(default=None, description="Filter by topic"),
    limit: int = Query(default=20, description="Number of articles"),
):
    conn = get_connection()
    cur = conn.cursor()
    if topic:
        cur.execute(
            "SELECT * FROM raw.news_articles WHERE topic = %s ORDER BY published_at DESC LIMIT %s;",
            (topic, limit)
        )
    else:
        cur.execute(
            "SELECT * FROM raw.news_articles ORDER BY published_at DESC LIMIT %s;",
            (limit,)
        )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

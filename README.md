# PulseBoard

A full-stack data pipeline and live dashboard that ingests stories from Hacker News and headlines from NewsAPI, transforms and scores them, stores everything in PostgreSQL, and serves it through a real-time Next.js dashboard.

PulseBoard is designed as a hands-on learning project that covers every layer of a modern data engineering stack — from raw data ingestion to orchestration, transformation, API development, and frontend visualization.

## Project Goals

- Build an end-to-end data pipeline that runs automatically on a schedule
- Ingest data from multiple sources (Hacker News, NewsAPI) and store it reliably
- Transform raw data into clean, analytics-ready tables using dbt
- Serve processed data through a FastAPI REST API
- Visualize trending topics, stories, and headlines on a live Next.js dashboard
- Learn industry-standard tools used by data and platform engineering teams

## Architecture

```
┌──────────────┐     ┌──────────────┐
│  Hacker News │     │   NewsAPI    │
│     API      │     │              │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────────────────────────┐
│         Ingestion Layer          │
│  hn_fetcher.py  news_fetcher.py  │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│      PostgreSQL (raw schema)     │
│  hn_stories  │  news_articles    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│     dbt Transformations          │
│  staging → marts → trending      │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│    Airflow Orchestration         │
│  Scheduled hourly DAG            │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│         FastAPI REST API         │
│  /trending  /stories  /articles  │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│     Next.js + Tailwind CSS       │
│       Live Dashboard             │
└──────────────────────────────────┘
```

## Tech Stack

| Layer             | Technology                          |
|-------------------|-------------------------------------|
| Ingestion         | Python 3.11+, requests              |
| Storage           | PostgreSQL 14                       |
| Transformation    | dbt (data build tool)               |
| Orchestration     | Apache Airflow                      |
| API               | FastAPI, psycopg2                   |
| Frontend          | Next.js 14, Tailwind CSS, SWR       |
| Streaming (opt.)  | Apache Kafka via Docker              |
| Config            | python-dotenv, .env files           |

## Project Phases

### ✅ Phase 1 — Data Ingestion
- Connected to the Hacker News API (no auth required)
- Built `ingest/hn_fetcher.py` to fetch top stories with titles, scores, comment counts, URLs, and timestamps
- Tested on live data

### ✅ Phase 2 — PostgreSQL Storage
- Created a `pulseboard` database with a `raw` schema
- Designed `raw.hn_stories` and `raw.news_articles` tables with proper types and constraints
- Implemented upserts (`INSERT ... ON CONFLICT DO NOTHING`) for idempotent, re-runnable ingestion
- Built `ingest/news_fetcher.py` to fetch headlines from NewsAPI by topic
- Both fetchers write directly to PostgreSQL

### 🔲 Phase 3 — dbt Transformations
- Initialize a dbt project for SQL-based data transformations
- Build a staging layer (`stg_hn_stories`, `stg_news_articles`) to clean and standardize raw data
- Build a marts layer (`mart_trending_topics`) that joins both sources and ranks topics by mention volume
- Add dbt tests for basic data quality checks

### 🔲 Phase 4 — Airflow Orchestration
- Set up Apache Airflow locally
- Create a DAG that runs the full pipeline in order: fetch → transform
- Schedule the pipeline to run every hour
- Monitor pipeline runs through the Airflow web UI

### 🔲 Phase 5 — FastAPI REST API
- Build a FastAPI app with endpoints for trending topics, stories, and articles
- Add CORS middleware for frontend access
- Use psycopg2 connection pooling for efficient database access

### 🔲 Phase 6 — Next.js Dashboard
- Scaffold a Next.js 14 app with Tailwind CSS
- Build components: TrendingTopics, PostFeed, NewsFeed
- Auto-refresh data every 60 seconds using SWR or React Query
- Dark mode UI with a clean, modern design

### 🔲 Phase 7 (Optional) — Kafka Streaming
- Set up a local Kafka broker with Docker Compose
- Create a producer/consumer for real-time story ingestion
- Compare tradeoffs of streaming vs scheduled batch processing

## Project Structure

```
PulseBoard/
├── .env                  # API keys and secrets (not committed)
├── .gitignore
├── README.md
├── ingest/
│   ├── hn_fetcher.py     # Hacker News ingestion script
│   └── news_fetcher.py   # NewsAPI ingestion script
├── dbt/                  # (Phase 3) dbt project
├── dags/                 # (Phase 4) Airflow DAGs
├── api/                  # (Phase 5) FastAPI app
└── dashboard/            # (Phase 6) Next.js frontend
```

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- A free API key from [NewsAPI](https://newsapi.org/register)

### Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/nwyrwas/PulseBoard.git
   cd PulseBoard
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install requests psycopg2-binary python-dotenv
   ```

3. **Create the database**
   ```bash
   createdb pulseboard
   ```

4. **Create the tables**
   ```bash
   psql -d pulseboard -c "
   CREATE SCHEMA IF NOT EXISTS raw;

   CREATE TABLE IF NOT EXISTS raw.hn_stories (
       story_id     INTEGER PRIMARY KEY,
       title        TEXT NOT NULL,
       score        INTEGER DEFAULT 0,
       num_comments INTEGER DEFAULT 0,
       url          TEXT,
       author       TEXT,
       created_utc  TIMESTAMPTZ NOT NULL,
       source       TEXT DEFAULT 'hackernews',
       ingested_at  TIMESTAMPTZ DEFAULT NOW()
   );

   CREATE TABLE IF NOT EXISTS raw.news_articles (
       article_id   TEXT PRIMARY KEY,
       title        TEXT NOT NULL,
       description  TEXT,
       url          TEXT NOT NULL,
       source_name  TEXT,
       published_at TIMESTAMPTZ,
       topic        TEXT,
       ingested_at  TIMESTAMPTZ DEFAULT NOW()
   );
   "
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your NewsAPI key
   ```

6. **Run the fetchers**
   ```bash
   python ingest/hn_fetcher.py
   python ingest/news_fetcher.py
   ```

## Author

**Nick Wyrwas**
- GitHub: [@nwyrwas](https://github.com/nwyrwas)

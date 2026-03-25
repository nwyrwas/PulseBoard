# PulseBoard

A full-stack data pipeline and live dashboard that ingests stories from Hacker News and headlines from NewsAPI, transforms and scores them with dbt, stores everything in PostgreSQL, and serves it through a real-time Next.js dashboard — orchestrated by Apache Airflow.

## Tech Stack

| Layer             | Technology                                    |
|-------------------|-----------------------------------------------|
| Ingestion         | Python 3.13, requests, python-dotenv          |
| Storage           | PostgreSQL 14                                 |
| Transformation    | dbt 1.11 (data build tool)                    |
| Orchestration     | Apache Airflow                                |
| API               | FastAPI, psycopg2                             |
| Frontend          | Next.js 14, Tailwind CSS, SWR                 |
| Streaming (opt.)  | Apache Kafka via Docker                       |

---

## Context

### The Problem

Tracking what's trending across tech communities and news outlets means checking multiple sources manually — Hacker News, various news sites, social media. There's no single view that aggregates, ranks, and refreshes this data automatically.

### Constraints

- API keys must never be hardcoded or committed to version control
- Pipeline must be idempotent — safe to re-run without creating duplicate data
- Data transformations must be version-controlled SQL, not ad-hoc scripts
- Must use free-tier APIs to keep the project accessible for learning
- Each phase must be independently functional before moving to the next

### Stakes

Portfolio project demonstrating end-to-end data engineering: API ingestion, relational database design, SQL transformations with dbt, pipeline orchestration with Airflow, REST API development with FastAPI, and a live frontend with Next.js.

### My Role

**Title:** Full-Stack Developer & Data Engineer

**Team:** Personal Project

**Ownership:** End-to-end ownership: data pipeline architecture, database schema design, dbt modeling, API development, frontend dashboard, and deployment.

---

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

---

## Approach & Key Decisions

### Hacker News API over Reddit API for data ingestion

Reddit's API required OAuth app registration, which was blocked by persistent rate-limiting and reCAPTCHA issues during setup. The Hacker News API is completely open — no authentication, no API keys, no sign-up — and provides the same core data (titles, scores, comment counts, URLs, timestamps). This let us start building immediately without being blocked by external dependencies.

### Upserts (INSERT ... ON CONFLICT) for idempotent ingestion

Data pipelines run repeatedly on a schedule. Without upserts, re-running a fetcher would either crash on duplicate primary keys or insert duplicate rows. Using `INSERT ... ON CONFLICT DO NOTHING` makes every pipeline run safe to repeat — a core principle of reliable data engineering.

### Separate raw, staging, and marts layers in dbt

Raw data stays untouched in the `raw` schema exactly as it arrived from the API. Staging models clean and standardize it (casting types, filtering nulls). Marts models join sources and build business-ready analytics tables. This layered approach means upstream changes don't break downstream consumers, and each layer can be tested independently.

### dbt over raw SQL scripts for transformations

dbt provides dependency management (via `ref()`), built-in testing, and version-controlled SQL. Writing raw SQL scripts would work, but you'd have to manually manage execution order, handle errors yourself, and lose the ability to test data quality assertions like `unique` and `not_null`.

### python-dotenv for all secrets management

Every API key and database credential lives in a `.env` file that is git-ignored. The `.env.example` file documents what variables are needed without exposing actual values. This prevents accidental credential exposure in version control.

---

## Phase Details

### Phase 1 — Data Ingestion ✅

**What was built:** Two Python ingestion scripts that pull data from external APIs — `hn_fetcher.py` for Hacker News top stories and `news_fetcher.py` for NewsAPI headlines by topic.

**Key implementation details:**
- Hacker News API returns a list of story IDs, then each story's details are fetched individually via `requests`
- NewsAPI searches articles by keyword (e.g., "technology", "business") and returns structured JSON
- Article IDs are generated by MD5-hashing the URL, providing a consistent unique identifier for deduplication
- All timestamps are converted to timezone-aware UTC format

> **Challenge:** Reddit's API registration page was completely blocked — reCAPTCHA wouldn't validate and Reddit rate-limited the IP after multiple attempts across browsers.
>
> **Solution:** Pivoted to the Hacker News API, which requires zero authentication and provides equivalent data for our pipeline. This decision removed an external dependency and simplified the ingestion layer.

---

### Phase 2 — PostgreSQL Storage ✅

**What was built:** A `pulseboard` PostgreSQL database with a `raw` schema containing two tables — `raw.hn_stories` and `raw.news_articles` — with proper types, constraints, and upsert logic.

**Key implementation details:**
- `story_id` (INTEGER) and `article_id` (TEXT) serve as primary keys for natural deduplication
- `TIMESTAMPTZ` used for all time columns to preserve timezone information across the pipeline
- `ingested_at` column auto-populates with `NOW()` to track when each row was fetched
- Both fetchers use `INSERT ... ON CONFLICT DO NOTHING` for safe, repeatable execution
- `psycopg2` handles all database connections with explicit commit/close patterns

> **Challenge:** Needed a way to handle duplicate data when the pipeline runs on a schedule — the same HN story could be in the top 10 for hours.
>
> **Solution:** Implemented PostgreSQL upserts with `ON CONFLICT DO NOTHING` on the primary key. The pipeline tracks how many rows were actually inserted vs skipped, giving visibility into data freshness.

---

### Phase 3 — dbt Transformations ✅

**What was built:** A dbt project with a staging layer (cleaning raw data) and a marts layer (joining sources and ranking trending topics), plus schema tests for data quality.

**Key implementation details:**
- `stg_hn_stories` and `stg_news_articles` — staging models that pass through columns, cast `created_utc`/`published_at` to `DATE` for day-level grouping, and filter null titles
- `mart_trending_topics` — a marts model using CTEs, `UNION ALL`, and `RANK()` window functions to combine both sources and rank topics by mention count
- `ref()` used for all model dependencies so dbt automatically determines execution order
- Schema tests enforce `unique` and `not_null` on primary keys and titles across both staging models

> **Challenge:** dbt crashed on startup with a `mashumaro.exceptions.UnserializableField` error — a compatibility issue between dbt's dependencies and Python 3.14.
>
> **Solution:** Recreated the virtual environment with Python 3.13, which has stable support for dbt 1.11 and all its dependencies. Kept all existing project code compatible.

> **Challenge:** The `mart_trending_topics` model returned data for Hacker News but not for news articles, even though articles existed in the database.
>
> **Solution:** The articles' `published_at` timestamps had aged past the 24-hour filter window. Widened the time window to 7 days during development. In production (Phase 4), the hourly Airflow schedule will keep fresh data flowing within the 24-hour window.

---

### Phase 4 — Airflow Orchestration 🔲

**Planned:** Set up Apache Airflow locally and create a DAG that runs the full pipeline (fetch → transform) on an hourly schedule.

- Configure Airflow standalone mode
- Build a DAG with tasks: `fetch_hn_stories` → `fetch_news_articles` → `run_dbt_models`
- Schedule hourly with monitoring via the Airflow web UI

---

### Phase 5 — FastAPI REST API 🔲

**Planned:** Build a FastAPI app that serves transformed data through REST endpoints.

- `GET /trending?hours=24` — top trending topics from `mart_trending_topics`
- `GET /hn/stories?limit=20` — recent Hacker News stories
- `GET /news/articles?topic=tech&limit=20` — recent headlines
- CORS middleware for frontend access
- psycopg2 connection pooling for efficient database usage

---

### Phase 6 — Next.js Dashboard 🔲

**Planned:** Build a live dashboard with Next.js 14 and Tailwind CSS that visualizes the pipeline output.

- TrendingTopics component polling every 60 seconds
- PostFeed and NewsFeed components for stories and headlines
- SWR or React Query for data fetching with auto-refresh
- Dark mode UI with clean, modern design

---

### Phase 7 (Optional) — Kafka Streaming 🔲

**Planned:** Add real-time streaming as an alternative to scheduled batch processing.

- Local Kafka broker via Docker Compose
- Producer streaming HN stories to a `pulseBoard.reddit` topic
- Consumer writing to PostgreSQL in real time
- Analysis of Kafka vs Airflow scheduling tradeoffs

---

## Project Structure

```
PulseBoard/
├── .env                  # API keys and secrets (not committed)
├── .env.example          # Template showing required env vars
├── .gitignore
├── README.md
├── ingest/
│   ├── hn_fetcher.py     # Hacker News ingestion script
│   └── news_fetcher.py   # NewsAPI ingestion script
├── pulseBoard/           # dbt project
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       │   ├── schema.yml
│       │   ├── stg_hn_stories.sql
│       │   └── stg_news_articles.sql
│       └── marts/
│           └── mart_trending_topics.sql
├── dags/                 # (Phase 4) Airflow DAGs
├── api/                  # (Phase 5) FastAPI app
└── dashboard/            # (Phase 6) Next.js frontend
```

---

## Getting Started

### Prerequisites
- Python 3.13+
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
   python3.13 -m venv venv
   source venv/bin/activate
   pip install requests psycopg2-binary python-dotenv dbt-postgres
   ```

3. **Create the database and tables**
   ```bash
   createdb pulseboard
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

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your NewsAPI key
   ```

5. **Run the pipeline**
   ```bash
   python ingest/hn_fetcher.py
   python ingest/news_fetcher.py
   dbt run --project-dir pulseBoard
   dbt test --project-dir pulseBoard
   ```

6. **Verify results**
   ```bash
   psql -d pulseboard -c "SELECT * FROM raw.mart_trending_topics;"
   ```

---

## Author

**Nick Wyrwas**
- GitHub: [@nwyrwas](https://github.com/nwyrwas)

---

## Project Links

[View on GitHub](https://github.com/nwyrwas/PulseBoard)

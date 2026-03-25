SELECT
    article_id,
    title,
    description,
    url,
    source_name,
    topic,
    ingested_at,
    published_at,
    published_at::date AS published_date

FROM raw.news_articles
WHERE title IS NOT NULL
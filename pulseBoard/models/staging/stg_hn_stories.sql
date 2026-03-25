SELECT
    story_id,
    title,
    score,
    num_comments,
    url,
    author,
    created_utc,
    created_utc::date AS posted_date,
    source,
    ingested_at

FROM raw.hn_stories
WHERE title IS NOT NULL
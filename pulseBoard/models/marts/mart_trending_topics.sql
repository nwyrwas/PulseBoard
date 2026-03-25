WITH hn_topics AS (
    SELECT
        source AS topic,
        title,
        created_utc as published_at

    FROM {{ ref('stg_hn_stories') }}
    WHERE created_utc > NOW() - INTERVAL '7 days'
),

news_topics AS (
    SELECT
        topic,
        title,
        published_at

    FROM {{ ref('stg_news_articles') }}
    WHERE published_at > NOW() - INTERVAL '7 days'
),

combined AS (
    SELECT * FROM hn_topics
    UNION ALL
    SELECT * FROM news_topics
),

topic_counts AS (
    SELECT
        topic,
        COUNT(*) as mention_count

    FROM combined
    GROUP BY topic
)

SELECT
    topic,
    mention_count,
    RANK() OVER (ORDER BY mention_count DESC) as topic_rank

FROM topic_counts
ORDER BY topic_rank
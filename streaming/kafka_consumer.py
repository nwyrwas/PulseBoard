# streaming/kafka_consumer.py
# Kafka consumer that reads HN stories from a topic and writes to PostgreSQL

import json
import psycopg2
from datetime import datetime, timezone
from confluent_kafka import Consumer, KafkaException

KAFKA_BROKER = "localhost:9092"
TOPIC = "pulseboard.hn_stories"

consumer = Consumer({
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "pulseboard-consumer",
    "auto.offset.reset": "earliest",  # start from the beginning of the topic
})


def save_to_postgres(story):
    """Upsert a story into PostgreSQL."""
    conn = psycopg2.connect(dbname="pulseboard", host="localhost", port=5432)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO raw.hn_stories (story_id, title, score, num_comments, url, author, created_utc, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'hackernews')
        ON CONFLICT (story_id) DO NOTHING;
    """, (
        story["story_id"],
        story["title"],
        story["score"],
        story["num_comments"],
        story["url"],
        story["author"],
        datetime.fromtimestamp(story["created_utc"], tz=timezone.utc),
    ))
    conn.commit()
    cur.close()
    conn.close()


def consume_stories():
    consumer.subscribe([TOPIC])
    print(f"Listening for messages on '{TOPIC}'...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            msg = consumer.poll(1.0)  # wait up to 1 second for a message

            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            story = json.loads(msg.value().decode("utf-8"))
            print(f"  Received: {story['title']}")
            save_to_postgres(story)
            print(f"  Saved to PostgreSQL!")

    except KeyboardInterrupt:
        print("\nShutting down consumer...")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_stories()

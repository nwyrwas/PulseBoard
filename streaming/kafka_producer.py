# kafka producer that streams Hacker News stories to a topic

import json
import requests
from confluent_kafka import Producer

KAFKA_BROKER = "localhost:9092"
TOPIC = "pulseboard.hn_stories"

HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_STORY_DETAIL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
STORY_LIMIT = 10

producer = Producer ({"bootstrap.servers": KAFKA_BROKER})

def deliver_report(err, msg):
    """ Callback - called once per message to confirm delivery."""

    if err:
        print(f" Delivery failed: {err}")
    else:
        print(f" Delivered to {msg.topic()} [{msg.partition()}]")

def produce_stories():
    print(f"Fetching top {STORY_LIMIT} stories from Hacker News...")
    response = requests.get(HN_TOP_STORIES)
    story_ids = response.json()[:STORY_LIMIT]

    for story_id in story_ids:
        detail_url = HN_STORY_DETAIL.format(story_id)
        data = requests.get(detail_url).json()

        if data is None:
            continue

        story_data = {
            "story_id": data.get("id"),
            "title": data.get("title"),
            "score": data.get("score", 0),
            "num_comments": data.get("descendants", 0),
            "url": data.get("url", ""),
            "author": data.get("by", ""),
            "created_utc": data.get("time", 0),
        }

        print(f"  Producing: {story_data['title']}")
        producer.produce(
            TOPIC,
            value=json.dumps(story_data),
            callback=deliver_report,
        )

    # Wait for all messages to be delivered
    producer.flush()
    print("Done! All messages sent to Kafka.")


if __name__ == "__main__":
    produce_stories()
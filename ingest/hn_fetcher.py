"""
hn_fetcher.py
-------------
Fetches top stories from the Hacker News API and upserts them
into PostgreSQL (raw.hn_stories table).

API docs: https://github.com/HackerNews/API

Usage:
    python ingest/hn_fetcher.py
"""
# The imports
# Requests - lets you make HTTP calls
# psycopg2 - this lets you connect and talk to PostgreSQL Database. Without it there is no way to write data to Postgres.
# Datetime lets you manipulate dates and times. Timezone lets you make timestamps timezone-aware.
import requests
import psycopg2
from datetime import datetime, timezone

# Hacker News API base URL
HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"

# PostgreSQL connection config
# This holds my database connection settings
DB_CONFIG = {
    "dbname": "pulseboard", #Name of the database

    # If a user clones this repo and runs it will fail due to their username not being nickwyrwas
    # Created a .env.example to document variables are needed without exposing real values.
    "user": "nickwyrwas", #PostgreSQL username


    "host": "localhost", # Database would be running on the same machine as the script
    "port": 5432, # Default port for PostgreSQL
}


def fetch_top_story_ids(limit=10):
    """
    Fetch the IDs of the current top stories on Hacker News.

    The API returns up to 500 story IDs ranked by score.
    We slice to our desired limit.
    """
    url = f"{HN_BASE_URL}/topstories.json" # a format string that builds the full URL but inserting the base URL constant.
    response = requests.get(url) # Makes a HTTP GET Request from the URL Variable.
    response.raise_for_status() # If the api returns an error, this would allow the program to raise a python exception immediately.
    story_ids = response.json() # Parses raw JSON data into python list of integer

    # Have python return only the first 10 IDs from the list
    # :limit means that its from the start but not including index 10 (indicies 0-9)
    return story_ids[:limit]

def fetch_story_details(story_id):
    """
    Fetch the full details for a single story by its ID.

    Returns a clean dict with only the fields we care about.
    """

    # Fetches the story details and builds the URL for a specific story.
    # Example: If the story ID is "38234567" the URL becomes HTTPS://hacker-news.firebaseio.com/v0/item/38234567.json
    url = f"{HN_BASE_URL}/item/{story_id}.json"
    response = requests.get(url)
    response.raise_for_status()
    item = response.json()

    # Utilized this statement due to HN API returning a null story ID
    # Primarily because there will be story IDs that no longer exists or was deleted.
    # Without this check, calling item.get("id") on None would throw an AttributeError and crash the script.
    # Returning None is used to guard against unexpected data before touching it.
    if item is None:
        return None

    #item.get() isi a method on a dictionary that returns a value or second argument if the key does not exist
    # If the API response has no "time field" with a value of 0. Which would represent lets say January 1, 1970 instead of a crash.

    # the datetime.fromtimestamp(..., tz=timezone.utc)
        # Allows us to convert Unix integers into a proper timezone aware datetime object
        # the part that is tz=timezone.utc is what would make it timezone aware.
    created_dt = datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc)

    return {
        "story_id": item.get("id"),
        "title": item.get("title", ""),
        "score": item.get("score", 0),

        #item.get("decendants", 0)
            # HN calls comment count "descendants" in their API
            # And calling the variable "num_comments" allows this to be more readable in the database.
        "num_comments": item.get("descendants", 0),
        
        "url": item.get("url", ""),

        #Created_dt.isoformat()
            #Converts the datetime object into a string
                # Example: "2026-03-16T14:32:00+00:00"
        # This is the format you want since PostgreSQL timestamptz column expects this.
        "created_utc": created_dt.isoformat(),

        "author": item.get("by", ""),

        # Source being hackernews is hardcoded
            # So that when data from both sources ends up in the same pipeline.
                # I can tell where the data came from
        "source": "hackernews",
    }


# Why separate the functions?:
    # This allows us to be able to call each function having them do their primary function.
        # Making them independent, testable and reusable. 
        # If I wanted to fetch lets say only 1 story's details somewhere else in the codebase.
            # I can call fetch_story_details directly without draggin in other logic.
def fetch_top_stories(limit=10):
    """
    Fetch top stories with full details.

    This is the main function other parts of the pipeline will call.
    """

    # This is an orchestor function, which calls fetch_top_story_ids and Fetch_story_details
        # Which combines their results
    
    # Calls fetch_top_story_ids  to get the list of IDs
        # Then loops through each one in fetch_story_details
        # If the story is not None the check skips any stories that returned Null from the API
            # By doing this we are able to build a list of clean story dictionaries and return it
    story_ids = fetch_top_story_ids(limit=limit)
    stories = []

    for story_id in story_ids:
        story = fetch_story_details(story_id)
        if story is not None:
            stories.append(story)

    return stories


# Primary function for data getting written into PostgreSQL
def upsert_stories(stories):
    """
    Insert stories into raw.hn_stories, skipping any that already exist.

    Uses INSERT ... ON CONFLICT DO NOTHING to make this idempotent —
    safe to run multiple times without creating duplicates.
    """

    # This allows us to unpack the dictionary as keyword arguments
        # instead of having to re-write all the information needed from DB_CONFIG.
    conn = psycopg2.connect(**DB_CONFIG)

    # Using conn.cursor() is an interface that helps with executing SQL Queries. 
    cur = conn.cursor()

    # Used %s as placeholders, due to hardcoding f-strings or concatenation would cause SQL injection vulnerabilities
    # ON CONFLICT (story_id) DO NOTHING:
        # This is the upsert where if there is a story_id that already exists in the table
        # PostgreSQL will ignore it instead of throwing an error.
        # Steering away from duplicates and keeping the data clean.
    insert_query = """
        INSERT INTO raw.hn_stories (story_id, title, score, num_comments, url, author, created_utc, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (story_id) DO NOTHING;
    """

    inserted = 0
    for story in stories:
        cur.execute(insert_query, (
            story["story_id"],
            story["title"],
            story["score"],
            story["num_comments"],
            story["url"],
            story["author"],
            story["created_utc"],
            story["source"],
        ))
        # rowcount is 1 if inserted, 0 if skipped (duplicate)
        inserted += cur.rowcount

    # Nothing is saved to db until you commit
    conn.commit()

    # Always want to ensure database connections are clean. 
    # Want to ensure that we do not leave them open as it wastes resourses.
    cur.close()
    conn.close()

    return inserted


# Sets a special variable called __name__ to the string __main__ when you execute the file directly.
# So when we use Airflow when it runs a module called fetch_top_stories() from another script
    # __name__ is set to hn_fetcher instead

# This is beneficial because then we know our functions are reusable and Airflow can import and call fetch_top_stories()
    # Without having to trigger all of the print statments
        # Where the print output should mainly be for the developers instead of the automated pipeline.
        # Used for testing and debugging.
if __name__ == "__main__":
    # --- Configuration ---
    STORY_LIMIT = 10

    print(f"Fetching top {STORY_LIMIT} stories from Hacker News...\n")

    stories = fetch_top_stories(limit=STORY_LIMIT)

    print(f"{'='*60}")
    print(f"  Hacker News — Top {STORY_LIMIT} stories")
    print(f"{'='*60}")

    for i, story in enumerate(stories, 1):
        print(f"\n  [{i}] {story['title']}")
        print(f"      Score: {story['score']} | Comments: {story['num_comments']}")
        print(f"      URL: {story['url']}")
        print(f"      Author: {story['author']}")
        print(f"      Posted: {story['created_utc']}")

    # Save to database
    print(f"\nSaving to PostgreSQL...")
    inserted = upsert_stories(stories)
    print(f"✅ Done! Inserted {inserted} new stories ({len(stories) - inserted} already existed)")

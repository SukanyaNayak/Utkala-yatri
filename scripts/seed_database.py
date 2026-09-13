"""
Seed MongoDB Atlas with the demo dataset in data/*.json.

Run from the project root (with your venv activated):
    python scripts/seed_database.py

This script connects to MongoDB directly (it does NOT go through
services/mongodb_service.py, since that module's connect_db() is
decorated with @st.cache_resource and is meant to run inside a live
Streamlit app, not a standalone script).

Behavior:
- Upserts each record by its "slug" field (or a composite key for
  collections without one), so re-running this script is always safe
  and never creates duplicates.
- Creates the indexes requested for Part 2:
    places.name, places.city, places.category, places.slug (unique)
    hotels.city
    festivals.month
    reviews.place_id
  (the "reviews" collection has no seed data yet — this just prepares
  the index ahead of time for a later week.)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

# Allow running this script directly from the project root
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import MONGODB_URI, MONGODB_DB_NAME  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def upsert_records(collection, records: list[dict], key_field: str = "slug") -> tuple[int, int]:
    """
    Upsert each record into `collection`, matched on `key_field`.
    Returns (inserted_count, updated_count).
    """
    inserted = 0
    updated = 0
    for record in records:
        key_value = record.get(key_field)
        if not key_value:
            print(f"  ⚠ Skipping record with no '{key_field}': {record}")
            continue

        result = collection.update_one(
            {key_field: key_value},
            {"$set": record},
            upsert=True,
        )
        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    return inserted, updated


def main() -> int:
    if not MONGODB_URI:
        print(
            "ERROR: MONGODB_URI is not set. Copy .env.example to .env and "
            "fill in your MongoDB Atlas connection string before seeding."
        )
        return 1

    print(f"Connecting to MongoDB Atlas (db: {MONGODB_DB_NAME}) ...")
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except PyMongoError as exc:
        print(f"ERROR: Could not connect to MongoDB Atlas: {exc}")
        return 1

    db = client[MONGODB_DB_NAME]
    print("Connected.\n")

    # ----------------------------------------------------------------
    # Seed each collection
    # ----------------------------------------------------------------
    datasets = [
        ("places.json", "places"),
        ("hotels.json", "hotels"),
        ("routes.json", "routes"),
        ("festivals.json", "festivals"),
        ("emergency.json", "emergency"),
    ]

    for filename, collection_name in datasets:
        print(f"Seeding '{collection_name}' from {filename} ...")
        records = load_json(filename)
        inserted, updated = upsert_records(db[collection_name], records)
        skipped = len(records) - inserted - updated
        print(f"  -> {inserted} inserted, {updated} updated, {skipped} unchanged "
              f"(total records in file: {len(records)})\n")

    # ----------------------------------------------------------------
    # Create indexes
    # ----------------------------------------------------------------
    print("Creating indexes ...")

    db["places"].create_index([("name", ASCENDING)])
    db["places"].create_index([("city", ASCENDING)])
    db["places"].create_index([("category", ASCENDING)])
    db["places"].create_index([("slug", ASCENDING)], unique=True)
    print("  -> places: name, city, category, slug (unique)")

    db["hotels"].create_index([("city", ASCENDING)])
    print("  -> hotels: city")

    db["festivals"].create_index([("month", ASCENDING)])
    print("  -> festivals: month")

    # reviews has no seed data yet, but we prepare the index for later weeks
    db["reviews"].create_index([("place_id", ASCENDING)])
    print("  -> reviews: place_id (collection will be empty until reviews are added)")

    print("\nSeeding complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

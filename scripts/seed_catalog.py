
"""Seed places, hotels, emergency collections from cleaned data files.

Run AFTER build_dataset.py:   python scripts/seed_catalog.py
Safe to re-run — upserts by id, never duplicates.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pymongo import ASCENDING, MongoClient
from pymongo.operations import IndexModel, UpdateOne

from utils.config import MONGODB_URI, MONGODB_DB_NAME


def load(fname: str) -> list[dict]:
    path = ROOT / "data" / fname
    if not path.exists():
        print(f"⚠️  {fname} not found — run scripts/build_dataset.py first")
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return next(iter(raw.values())) if isinstance(raw, dict) else raw


def seed(col, docs: list[dict], id_field: str, label: str) -> None:
    if not docs:
        return
    col.create_indexes([
        IndexModel([(id_field, ASCENDING)], unique=True),
        IndexModel([("location", "2dsphere")]),
        IndexModel([("name", ASCENDING)]),
    ])
    ops = [UpdateOne({id_field: d[id_field]}, {"$set": d}, upsert=True) for d in docs]
    res = col.bulk_write(ops)
    print(f"✅ {label:<10} upserted {len(docs):>4} (matched={res.matched_count})")


def main() -> None:
    if not MONGODB_URI:
        sys.exit("❌ MONGODB_URI is not set — check your .env")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[MONGODB_DB_NAME or "utkalayatri"]

    seed(db["places"], load("places.json"), "place_id", "places")
    seed(db["hotels"], load("hotels.json"), "hotel_id", "hotels")

    emergency = load("emergency.json")   # free-form schema → derive stable ids
    for i, e in enumerate(emergency):
        if "emergency_id" not in e:
            base = f"{e.get('type') or e.get('service') or e.get('name') or 'svc'}-{e.get('city') or i}"
            e["emergency_id"] = base.lower().replace(" ", "-")
    db["emergency"].delete_many({})      # emergency.json is the full source of truth
    seed(db["emergency"], emergency, "emergency_id", "emergency")


if __name__ == "__main__":
    main()
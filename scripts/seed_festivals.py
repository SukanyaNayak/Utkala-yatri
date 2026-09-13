"""Seed the `festivals` collection from data/festivals.json (upsert by festival_id).

Usage (from project root):
    python scripts/seed_festivals.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # allow `utils` imports when run as a script

from pymongo import ASCENDING, MongoClient
from pymongo.operations import IndexModel, UpdateOne

from utils.config import MONGODB_URI, MONGODB_DB_NAME  # same source as the app

REQUIRED = ["festival_id", "name", "category", "city", "location",
            "typical_window", "description"]


def validate(festivals: list[dict]) -> None:
    errors = []
    for i, f in enumerate(festivals):
        for key in REQUIRED:
            if key not in f:
                errors.append(f"[{i}] missing `{key}`")
        lng, lat = f.get("location", {}).get("coordinates", [None, None])
        if not (-180 <= (lng or 0) <= 180 and -90 <= (lat or 0) <= 90):
            errors.append(f"[{i}] bad coordinates — GeoJSON order is [lng, lat]!")
        for m in f.get("typical_window", {}).get("months", []):
            if m not in range(1, 13):
                errors.append(f"[{i}] month {m} out of range 1–12")
    if errors:
        sys.exit("❌ Validation failed:\n" + "\n".join(errors))


def main() -> None:
    if not MONGODB_URI:
        sys.exit("❌ MONGODB_URI is not set — check your .env")

    raw = json.loads((ROOT / "data" / "festivals.json").read_text(encoding="utf-8"))
    if isinstance(raw, dict):          # tolerate {"festivals": [...]} wrappers
        raw = next(iter(raw.values()))
    validate(raw)

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")       # fail fast instead of hanging
    db_name = MONGODB_DB_NAME or "utkalayatri"
    col = client[db_name]["festivals"]

    col.create_indexes([
        IndexModel([("festival_id", ASCENDING)], unique=True),
        IndexModel([("location", "2dsphere")]),
        IndexModel([("tags", ASCENDING)]),
    ])

    ops = [UpdateOne({"festival_id": f["festival_id"]}, {"$set": f}, upsert=True)
           for f in raw]
    res = col.bulk_write(ops)
    print(f"✅ Upserted {len(raw)} festivals into db '{db_name}' "
          f"(matched={res.matched_count}, modified={res.modified_count})")


if __name__ == "__main__":
    main()
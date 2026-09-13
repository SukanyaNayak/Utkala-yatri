"""Quick health report of the UtkalaYatri database.

Shows collections, document counts, indexes, and a sample document per
collection. Run from project root:
    python scripts/db_overview.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pymongo import MongoClient

from utils.config import MONGODB_URI, MONGODB_DB_NAME

EXPECTED = {
    "festivals": ("festival_id", 17),    # (id field, ~expected count)
    "places":    ("place_id", 200),
    "hotels":    ("hotel_id", 250),
    "emergency": ("emergency_id", 10),
}


def main() -> None:
    if not MONGODB_URI:
        sys.exit("❌ MONGODB_URI is not set — check your .env")

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        sys.exit(f"❌ Cannot reach MongoDB Atlas: {exc}")

    db = client[MONGODB_DB_NAME or "utkalayatri"]
    print(f"Database: {db.name}\n" + "=" * 50)

    names = sorted(db.list_collection_names())
    if not names:
        print("  (no collections yet — run the seed scripts)")
    for name in names:
        col = db[name]
        count = col.count_documents({})
        id_field, expected = EXPECTED.get(name, ("id", None))
        idx = ", ".join(sorted(col.index_information()))
        flag = ""
        if expected is not None:
            flag = "✅" if count >= expected * 0.5 else "⚠️ count looks low"
        print(f"\n📁 {name}  —  {count} documents  {flag}")
        print(f"   indexes: {idx}")
        sample = col.find_one({}, {"_id": 0})
        if sample:
            keys = ", ".join(list(sample.keys())[:8])
            print(f"   fields:  {keys} …")

    missing = [n for n in EXPECTED if n not in names]
    print("\n" + "=" * 50)
    if missing:
        print(f"❌ Missing collections: {', '.join(missing)}")
        print("   → run: python scripts/seed_festivals.py && python scripts/seed_catalog.py")
    else:
        print("✅ All expected collections present.")
    print(f"\nApp must show the SAME db name — sidebar says: "
          f"'Connected to MongoDB Atlas (db: {db.name})' if in sync.")


if __name__ == "__main__":
    main()
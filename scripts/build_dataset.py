"""Clean + merge raw CSVs -> canonical JSON, ready for seeding.

Pipeline:  fetch_*.py -> data/raw/*.csv
           build_dataset.py (THIS) -> data/places.json, data/hotels.json
           seed_catalog.py -> MongoDB

Raw files are never modified. Run from project root:
    python scripts/build_dataset.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data"

# Odisha bounding box (+ margin) — rows outside are dropped
LAT_MIN, LAT_MAX = 17.5, 22.8
LON_MIN, LON_MAX = 81.0, 87.8

# Highest priority first — on duplicates, earlier source wins & fills gaps
PLACE_SOURCES = [
    ("curated",  ["curated_places.csv", "curated_places (1).csv"]),
    ("wikidata", ["wikidata_places.csv"]),
    ("osm",      ["osm_places.csv"]),
]
HOTEL_SOURCES = [
    ("curated",  ["curated_hotels.csv"]),
    ("osm",      ["osm_hotels.csv"]),
]

# raw column-name variants -> canonical field
COLMAP: dict[str, list[str]] = {
    "name": ["name", "title", "label", "itemlabel", "name_en", "place_name"],
    "lat": ["lat", "latitude", "y", "coord_lat"],
    "lon": ["lon", "lng", "long", "longitude", "x", "coord_lon"],
    "category": ["category", "type", "tourism", "amenity", "historic",
                 "leisure", "natural", "place_type", "class", "kind",
                 "wikidata_class"],
    "city": ["city", "town", "village", "address_city", "location"],
    "district": ["district", "county", "state_district"],
    "image": ["image", "image_url", "photo", "thumbnail", "picture",
              "wikidata_image"],
    "website": ["website", "url", "official_website", "contact_website"],
    "phone": ["phone", "telephone", "contact_phone"],
    "address": ["address", "addr_street", "street"],
    "rating": ["rating", "stars", "star_rating"],
    "price": ["price", "price_level", "avg_cost", "cost_per_night", "rate",
              "price_range_inr", "price_range"],          # ← added
    "description": ["description", "desc", "summary", "details", "abstract",
                    "description_en", "wikidata_description", "itemdescription",
                    "notes"],                              # ← added (last = lowest priority)
    "tags": ["tags"],                                      # ← new
    "best_time": ["best_time_to_visit", "best_time"],      # ← new
}

CATEGORY_BUCKETS = {
    "heritage": {"temple", "hindu_temple", "pilgrimage","heritage", "monument", "fort",
                 "fortification", "palace", "historic", "memorial", "ruins",
                 "cave", "buddhist_temple", "archaeological"},
    "beach":    {"beach", "sea", "coast"},
    "nature":   {"waterfall", "lake", "river", "hill", "mountain", "peak",
                 "spring", "garden", "park", "viewpoint", "island",
                 "nature_reserve"},
    "wildlife": {"national_park", "wildlife_sanctuary", "tiger_reserve",
                 "sanctuary", "zoo"},
    "museum":   {"museum", "gallery", "artwork", "aquarium"},
}


def resolve(names: list[str]) -> Path | None:
    for n in names:
        if (RAW / n).exists():
            return RAW / n
    return None


def norm_text(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = re.sub(r"[^\w\s]", " ", s).lower()
    return re.sub(r"\s+", " ", s).strip()


def slugify(*parts) -> str:
    s = norm_text("-".join(p for p in parts if p))
    return re.sub(r"\s+", "-", s)[:60] or "item"


def bucket(category: str) -> str:
    c = norm_text(category).replace(" ", "_").replace("-", "_")
    for name, keys in CATEGORY_BUCKETS.items():
        if c in keys:
            return name
    for name, keys in CATEGORY_BUCKETS.items():   # substring fallback
        if any(k in c for k in keys):
            return name
    return "other"


def load_source(source: str, path: Path) -> list[dict]:
    df = pd.read_csv(path, encoding="utf-8-sig")
    cols = {c.lower().strip(): c for c in df.columns}
    rename = {}
    for canon, variants in COLMAP.items():
        for v in variants:
            if v in cols and canon not in rename:
                rename[cols[v]] = canon
    df = df.rename(columns=rename)
    unknown = [c for c in df.columns if c not in COLMAP]
    if unknown:
        print(f"   ⚠️ {path.name}: unmapped columns {unknown} (ignored — tell Claude)")

    kept, reasons = [], Counter()
    for _, row in df.iterrows():
        try:
            lat, lon = float(row.get("lat")), float(row.get("lon"))
        except (TypeError, ValueError):
            reasons["bad/missing lat-lon"] += 1
            continue
        name = str(row.get("name") or "").strip()
        if not name or name.lower() == "nan":
            reasons["missing name"] += 1
            continue
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            reasons["outside Odisha box"] += 1
            print(f"      ↳ outside box: {name!r} lat={lat} lon={lon}")
            continue
        rec = {"name": name, "lat": round(lat, 6), "lon": round(lon, 6),
               "source": source}
        for f in ("description", "category", "city", "district", "image",
                  "website", "phone", "address", "price", "rating",
                  "tags", "best_time"):
            val = row.get(f)
            if val is not None and str(val).strip() not in ("", "nan", "None"):
                rec[f] = str(val).strip()
        kept.append(rec)
    print(f"   {source:<9} {len(df):>4} rows -> {len(kept):>4} kept, "
          f"{sum(reasons.values())} dropped")
    for reason, n in reasons.items():
        print(f"      ↳ {n}x {reason}")
    return kept
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))  # FIX: was (…, lon2)
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def name_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, norm_text(a), norm_text(b)).ratio()


def dedupe(records: list[dict], label: str,
           radius_km: float = 0.3, sim_threshold: float = 0.55) -> list[dict]:
    """Same POI = within radius AND similar name. Records arrive in priority
    order; lower-priority fields only fill gaps (never overwrite)."""
    out: list[dict] = []
    merged = 0
    for rec in records:
        match = None
        for keep in out:
            if (haversine_km(rec["lat"], rec["lon"], keep["lat"], keep["lon"]) <= radius_km
                    and name_sim(rec["name"], keep["name"]) >= sim_threshold):
                match = keep
                break
        if match:
            merged += 1
            for k, v in rec.items():
                if k not in match and k != "source":
                    match[k] = v
        else:
            out.append(rec)
    print(f"   {label}: {len(records)} in -> {len(out)} unique ({merged} duplicates merged)")
    return out


def finalize(records: list[dict], id_field: str) -> None:
    used: set[str] = set()
    for r in records:
        base = slugify(r["name"], r.get("city", ""))
        rid, n = base, 2
        while rid in used:
            rid, n = f"{base}-{n}", n + 1
        used.add(rid)
        r[id_field] = rid
        if r.get("category"):
            r["category_raw"] = r["category"]
            r["category"] = bucket(r["category"])
        else:
            r["category"] = "other"
        # parse "a; b; c" style tag strings into a clean list,
        # then merge with bucketed category + source (deduped, order kept)
        tags = r.get("tags")
        if isinstance(tags, str):
            r["tags"] = [t.strip() for t in re.split(r"[;,|]", tags) if t.strip()]
        r.setdefault("tags", [])
        r["tags"] = list(dict.fromkeys([*r["tags"], r["category"], r["source"]]))
        # GeoJSON, same as festivals — enables 2dsphere queries. [lng, lat]!
        r["location"] = {"type": "Point", "coordinates": [r["lon"], r["lat"]]}
def main() -> None:
    print("Loading raw sources…")
    places: list[dict] = []
    for source, names in PLACE_SOURCES:
        path = resolve(names)
        if path:
            places.extend(load_source(source, path))
        else:
            print(f"   ⚠️ missing: {names[0]}")

    hotels: list[dict] = []
    for source, names in HOTEL_SOURCES:
        path = resolve(names)
        if path:
            hotels.extend(load_source(source, path))
        else:
            print(f"   ⚠️ missing: {names[0]}")

    print("Deduplicating (proximity + name similarity)…")
    places = dedupe(places, "places")
    hotels = dedupe(hotels, "hotels", radius_km=0.15)  # hotels cluster tighter
    for h in hotels:
        h["category"] = "hotel"

    finalize(places, "place_id")
    finalize(hotels, "hotel_id")

    (OUT / "places.json").write_text(
        json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "hotels.json").write_text(
        json.dumps(hotels, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ data/places.json : {len(places)} places  "
          f"{dict(Counter(p['category'] for p in places))}")
    print(f"✅ data/hotels.json : {len(hotels)} hotels  "
          f"{dict(Counter(h['source'] for h in hotels))}")


if __name__ == "__main__":
    main()
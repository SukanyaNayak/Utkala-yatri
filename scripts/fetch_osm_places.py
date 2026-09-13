"""
Fetch real tourism/heritage points-of-interest and hotels for Odisha
from OpenStreetMap, using the free public Overpass API.

This is the "OpenStreetMap" source in the data pipeline:

    Official Odisha Tourism + OpenStreetMap + curated data
        -> Pandas (clean/validate)
        -> MongoDB Atlas

Run from the project root (with your venv activated):
    python scripts/fetch_osm_places.py

Output:
    data/raw/osm_places.csv
    data/raw/osm_hotels.csv

Notes:
- Overpass is a shared, rate-limited public service — be considerate
  (this script makes 2 requests total: one for places, one for hotels).
- Coordinates and tags come directly from OpenStreetMap contributors.
  They are reasonably reliable for location, but names/categories
  should still be spot-checked before treating them as fully verified —
  build_dataset.py marks OSM rows with source="openstreetmap" and
  source_verified=False for exactly this reason.
- No API key is required.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import requests

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",  # fallback mirror
]

# Overpass's fair-use policy filters out requests with generic/default
# User-Agents (which is what caused the "406 Not Acceptable" error) —
# sending a descriptive one fixes it.
HEADERS = {
    "User-Agent": "UtkalaYatri-Hackathon-MVP/1.0 (student project; contact: set-your-email-here)"
}

# Rough bounding box covering Odisha: (south, west, north, east)
ODISHA_BBOX = (17.7, 81.3, 22.6, 87.5)

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Tags that broadly capture tourist attractions / heritage sites
PLACES_QUERY = f"""
[out:json][timeout:60];
(
  node["tourism"~"attraction|museum|viewpoint|zoo|theme_park"]({ODISHA_BBOX[0]},{ODISHA_BBOX[1]},{ODISHA_BBOX[2]},{ODISHA_BBOX[3]});
  node["historic"]({ODISHA_BBOX[0]},{ODISHA_BBOX[1]},{ODISHA_BBOX[2]},{ODISHA_BBOX[3]});
  node["natural"="beach"]({ODISHA_BBOX[0]},{ODISHA_BBOX[1]},{ODISHA_BBOX[2]},{ODISHA_BBOX[3]});
);
out center;
"""

HOTELS_QUERY = f"""
[out:json][timeout:60];
(
  node["tourism"="hotel"]({ODISHA_BBOX[0]},{ODISHA_BBOX[1]},{ODISHA_BBOX[2]},{ODISHA_BBOX[3]});
  node["tourism"="guest_house"]({ODISHA_BBOX[0]},{ODISHA_BBOX[1]},{ODISHA_BBOX[2]},{ODISHA_BBOX[3]});
);
out center;
"""


def run_overpass_query(query: str) -> list[dict]:
    """
    POST a query to Overpass, trying each mirror in OVERPASS_URLS in turn.
    Raises the last error if every mirror fails.
    """
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            response = requests.post(url, data={"data": query}, headers=HEADERS, timeout=90)
            response.raise_for_status()
            return response.json().get("elements", [])
        except requests.RequestException as exc:
            print(f"  (mirror {url} failed: {exc} — trying next mirror if available)")
            last_error = exc
            continue
    raise last_error


def category_from_tags(tags: dict) -> str:
    """Best-effort category label derived from OSM tags."""
    if "historic" in tags:
        return f"Historic ({tags['historic']})"
    if tags.get("natural") == "beach":
        return "Beach"
    if "tourism" in tags:
        return tags["tourism"].replace("_", " ").title()
    return "Unknown"


def fetch_places() -> int:
    print("Querying Overpass API for tourist attractions / heritage sites in Odisha ...")
    elements = run_overpass_query(PLACES_QUERY)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "osm_places.csv"

    rows_written = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["osm_id", "name", "city", "category", "description",
                      "latitude", "longitude", "source", "source_verified"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue  # skip unnamed nodes — not useful for a travel app

            w.writerow({
                "osm_id": el.get("id"),
                "name": name,
                "city": tags.get("addr:city", ""),  # often blank on OSM — filled in later by build_dataset.py
                "category": category_from_tags(tags),
                "description": tags.get("description", ""),
                "latitude": el.get("lat"),
                "longitude": el.get("lon"),
                "source": "openstreetmap",
                "source_verified": False,  # community-sourced — treat as needing a manual glance, not guaranteed
            })
            rows_written += 1

    print(f"  -> wrote {rows_written} rows to {out_path}")
    return rows_written


def fetch_hotels() -> int:
    print("Querying Overpass API for hotels / guest houses in Odisha ...")
    elements = run_overpass_query(HOTELS_QUERY)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "osm_hotels.csv"

    rows_written = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["osm_id", "name", "city", "category", "latitude", "longitude",
                      "source", "source_verified"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue

            w.writerow({
                "osm_id": el.get("id"),
                "name": name,
                "city": tags.get("addr:city", ""),
                "category": tags.get("tourism", "").replace("_", " ").title(),
                "latitude": el.get("lat"),
                "longitude": el.get("lon"),
                "source": "openstreetmap",
                "source_verified": False,
            })
            rows_written += 1

    print(f"  -> wrote {rows_written} rows to {out_path}")
    return rows_written


def main() -> int:
    try:
        places_count = fetch_places()
        hotels_count = fetch_hotels()
    except requests.RequestException as exc:
        print(f"ERROR: Could not reach Overpass API: {exc}")
        print("Check your internet connection, or try again later — "
              "overpass-api.de is a shared public service and occasionally busy.")
        return 1

    print(f"\nDone. {places_count} places, {hotels_count} hotels/guest houses fetched from OpenStreetMap.")
    print("Next: run scripts/build_dataset.py to clean, validate, and merge with curated data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
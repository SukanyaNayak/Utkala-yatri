"""
Fetch real tourist attractions / heritage sites for Odisha from Wikidata,
using the free public Wikidata Query Service (SPARQL).

This is a second "other verified/open dataset" source in the pipeline,
alongside OpenStreetMap:

    Official Odisha Tourism + OpenStreetMap + Wikidata + curated data
        -> Pandas (clean/validate)
        -> MongoDB Atlas

Run from the project root (with your venv activated):
    python scripts/fetch_wikidata_places.py

Output:
    data/raw/wikidata_places.csv

How it works:
- Wikidata models "administrative territorial entity" (P131) as a chain —
  a temple is located in a village, which is in a district, which is in
  Odisha (Q22048). The query below follows that chain (P131+) so it picks
  up items nested at any depth under Odisha, not just direct children.
- Results are restricted to a fixed list of tourist-relevant types
  (tourist attraction, museum, Hindu temple, palace, archaeological site,
  fortification, waterfall, beach, national park) via VALUES — without
  this filter the query would also return unrelated things like villages,
  schools, and companies located in Odisha.
- Only items with a coordinate (P625) are kept, since a place with no
  location isn't useful for a map-based travel app.

Notes:
- No API key is required, but Wikidata's usage policy asks for a
  descriptive User-Agent identifying your project — see REQUEST_HEADERS
  below (this is exactly what caused a 406 error on the OSM/Overpass
  fetcher, so it's set correctly here from the start).
- Wikidata is community-edited, same caveat as OpenStreetMap: coordinates
  are generally reliable, but treat names/categories as needing a glance,
  not gospel. Rows are tagged source="wikidata", source_verified=False.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import requests

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# Wikidata usage policy asks for a descriptive User-Agent identifying the
# project/tool making the request (not a generic default).
REQUEST_HEADERS = {
    "User-Agent": "UtkalaYatri-Hackathon-MVP/1.0 (student project; Odisha travel app)",
    "Accept": "application/sparql-results+json",
}

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

ODISHA_QID = "wd:Q22048"

# Tourist-relevant "instance of" (P31) types to include. Not exhaustive —
# add more Wikidata QIDs here later if you find categories being missed.
#
# IMPORTANT: these are queried ONE AT A TIME (see fetch_places below), not
# combined into a single VALUES clause. Combining a transitive property
# path (P131+, which walks the whole administrative hierarchy) with a
# multi-value type filter in one query is exactly what caused a
# "504 Gateway Timeout" in testing — Wikidata's public endpoint has a
# fairly tight time budget, and that combination is too expensive for it.
# Nine small, targeted queries reliably finish; one big combined query
# often doesn't.
TYPE_QIDS = {
    "wd:Q570116": "tourist attraction",
    "wd:Q33506": "museum",
    "wd:Q1370598": "Hindu temple",
    "wd:Q16560": "palace",
    "wd:Q839954": "archaeological site",
    "wd:Q57821": "fortification",
    "wd:Q34038": "waterfall",
    "wd:Q40080": "beach",
    "wd:Q46169": "national park",
}

# Wikidata returns coordinates as a WKT string like "Point(85.8245 20.2961)"
# — longitude first, then latitude.
COORD_PATTERN = re.compile(r"Point\(([-\d.]+)\s+([-\d.]+)\)")


def build_query_for_type(type_qid: str) -> str:
    return f"""
SELECT ?item ?itemLabel ?itemDescription ?locLabel ?coord WHERE {{
  ?item wdt:P31 {type_qid}.
  ?item wdt:P131+ {ODISHA_QID}.
  ?item wdt:P625 ?coord.
  OPTIONAL {{ ?item wdt:P131 ?loc. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 300
"""


def run_sparql_query(query: str) -> list[dict]:
    response = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers=REQUEST_HEADERS,
        timeout=90,
    )
    response.raise_for_status()
    return response.json().get("results", {}).get("bindings", [])


def parse_coord(coord_wkt: str) -> tuple[float, float] | tuple[None, None]:
    match = COORD_PATTERN.search(coord_wkt)
    if not match:
        return None, None
    lon, lat = match.groups()
    return float(lat), float(lon)


def fetch_places() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "wikidata_places.csv"

    seen_qids = set()  # an item can match more than one type — dedupe across all queries
    rows_written = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["wikidata_id", "name", "city", "category", "description",
                      "latitude", "longitude", "source", "source_verified"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for type_qid, type_label in TYPE_QIDS.items():
            print(f"Querying Wikidata for '{type_label}' in Odisha ...")
            try:
                bindings = run_sparql_query(build_query_for_type(type_qid))
            except requests.RequestException as exc:
                # Don't let one slow/timing-out type kill the whole run —
                # skip it and keep going with the rest.
                print(f"  (skipping '{type_label}': {exc})")
                continue

            type_rows = 0
            for b in bindings:
                item_uri = b.get("item", {}).get("value", "")
                qid = item_uri.rsplit("/", 1)[-1] if item_uri else ""
                if not qid or qid in seen_qids:
                    continue

                name = b.get("itemLabel", {}).get("value", "")
                if not name or name == qid:
                    continue  # no usable label — skip rather than write a bare QID as the name

                coord_wkt = b.get("coord", {}).get("value", "")
                lat, lon = parse_coord(coord_wkt)
                if lat is None or lon is None:
                    continue

                seen_qids.add(qid)

                w.writerow({
                    "wikidata_id": qid,
                    "name": name,
                    "city": b.get("locLabel", {}).get("value", ""),
                    "category": type_label,
                    "description": b.get("itemDescription", {}).get("value", ""),
                    "latitude": lat,
                    "longitude": lon,
                    "source": "wikidata",
                    "source_verified": False,  # community-edited — see module docstring
                })
                rows_written += 1
                type_rows += 1

            print(f"  -> {type_rows} rows")
            time.sleep(1)  # be considerate to the shared public endpoint between requests

    print(f"\nWrote {rows_written} total rows to {out_path}")
    return rows_written


def main() -> int:
    count = fetch_places()

    if count == 0:
        print("\nNo rows were written. If every type above showed a timeout/error, "
              "the Wikidata endpoint may be temporarily overloaded — try again shortly.")
        return 1

    print(f"\nDone. {count} places fetched from Wikidata.")
    print("Next: run scripts/build_dataset.py to clean, validate, and merge with your other sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
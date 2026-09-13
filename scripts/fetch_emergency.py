"""Fetch real emergency facilities in Odisha from OpenStreetMap (Overpass)
-> data/emergency.json

Covers: hospitals, clinics, police, fire stations.
Run from project root:
    python scripts/fetch_emergency.py
"""
import json
import re
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "emergency.json"

BBOX = "17.5,81.0,22.8,87.8"          # Odisha bounding box (S, W, N, E)
AMENITIES = ["hospital", "police", "fire_station", "clinic"]
TYPE_MAP = {"hospital": "hospital", "clinic": "hospital",
            "police": "police", "fire_station": "fire"}

OVERPASS_URLS = ["https://overpass-api.de/api/interpreter",
                 "https://overpass.kumi.systems/api/interpreter",
                 "https://overpass.private.coffee/api/interpreter"]

# Overpass rejects the default python-requests User-Agent with 406
HEADERS = {"User-Agent": "UtkalaYatri-hackathon/1.0 (student tourism project)"}

QUERY = f"""
[out:json][timeout:90];
(
  node["amenity"~"^({'|'.join(AMENITIES)})$"]({BBOX});
  way["amenity"~"^({'|'.join(AMENITIES)})$"]({BBOX});
);
out center tags;
"""


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s).lower()).strip()


def first_phone(raw: str) -> str | None:
    """OSM phones can be '0674 2391234;+91 94370 21234' — take the first."""
    if not raw:
        return None
    part = re.split(r"[;,/]", raw)[0]
    digits = re.sub(r"[^\d+]", "", part)
    return digits if len(re.sub(r"\D", "", digits)) >= 6 else None


def run_overpass() -> list[dict]:
    last_err = None
    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                print(f"Querying Overpass ({url.split('/')[2]}) "
                      f"attempt {attempt + 1}…")
                r = requests.post(url, data={"data": QUERY},
                                  headers=HEADERS, timeout=120)
                if r.status_code == 429:
                    print("   ⏳ rate-limited — waiting 45s…")
                    time.sleep(45)
                    continue
                r.raise_for_status()
                return r.json().get("elements", [])
            except Exception as exc:
                last_err = exc
                print(f"   ⚠️ failed: {exc}")
                time.sleep(10)
    raise SystemExit(f"❌ All Overpass endpoints failed: {last_err}")


def main() -> None:
    elements = run_overpass()
    print(f"   {len(elements)} raw OSM elements")

    seen, out = set(), []
    skipped = {"no_name": 0, "no_coords": 0, "dup": 0}
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            skipped["no_coords"] += 1
            continue
        name = (tags.get("name") or tags.get("operator") or "").strip()
        if not name:
            skipped["no_name"] += 1
            continue
        key = (norm_text(name), round(lat, 3), round(lon, 3))
        if key in seen:
            skipped["dup"] += 1
            continue
        seen.add(key)

        addr = ", ".join(tags[k] for k in
                         ("addr:full", "addr:street", "addr:suburb", "addr:city")
                         if tags.get(k)) or None
        etype = TYPE_MAP.get(tags.get("amenity"), "hospital")
        out.append({
            "name": name,
            "type": etype,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "phone": first_phone(tags.get("phone")
                                 or tags.get("contact:phone")
                                 or tags.get("emergency:phone")),
            "address": addr,
            "source": "osm",
        })

    out.sort(key=lambda e: (e["type"], norm_text(e["name"])))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    from collections import Counter
    with_phone = sum(1 for e in out if e["phone"])
    print(f"✅ {OUT}: {len(out)} facilities  {dict(Counter(e['type'] for e in out))}")
    print(f"   phone coverage: {with_phone}/{len(out)}")
    print(f"   skipped: {skipped}")


if __name__ == "__main__":
    main()
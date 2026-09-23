"""Interactively add a place to data/places.json.
Run:  python scripts/add_place.py
Then: python scripts/seed_catalog.py   (hotspot if campus DNS misbehaves)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "places.json"


def ask(prompt: str, required: bool = True) -> str:
    while True:
        v = input(prompt).strip()
        if v or not required:
            return v
        print("  ⚠️ required")


def main() -> None:
    places = json.loads(FILE.read_text(encoding="utf-8"))
    name = ask("Place name: ")
    if any(p["name"].lower() == name.lower() for p in places):
        sys.exit("❌ A place with this name already exists.")

    city = ask("City/town (optional): ", required=False)
    district = ask("District (optional): ", required=False)
    try:
        lat = float(ask("Latitude  (e.g. 20.24): "))
        lon = float(ask("Longitude (e.g. 85.43): "))
    except ValueError:
        sys.exit("❌ Coordinates must be numbers.")
    if not (17.5 <= lat <= 22.8 and 81.0 <= lon <= 87.8):
        sys.exit("❌ Coordinates look outside Odisha — double-check them.")
    category = (ask("Category [heritage/beach/nature/wildlife/museum/other]: ")
                or "other").lower()
    description = ask("Description (1-2 sentences): ")
    best_time = ask("Best time to visit (optional): ", required=False)
    insider_tip = ask("Insider tip (optional): ", required=False)
    image = ask("Image URL (optional, direct upload.wikimedia.org link): ",
                required=False)
    hidden = input("Hidden gem? [y/N]: ").strip().lower() == "y"

    # unique slug id
    slug = re.sub(r"\s+", "-", re.sub(r"[^\w\s]", "", name.lower())).strip()[:60]
    if any(p.get("place_id") == slug for p in places):
        slug += "-2"

    p = {
        "place_id": slug,
        "name": name,
        "city": city, "district": district,
        "lat": round(lat, 6), "lon": round(lon, 6),
        "location": {"type": "Point", "coordinates": [lon, lat]},  # [lng, lat]!
        "category": category,
        "description": description,
        "source": "curated",                       # → Trip Planner & selectboxes
        "tags": [category, "curated"] + (["hidden-gem"] if hidden else []),
    }
    if best_time:
        p["best_time"] = best_time
    if insider_tip:
        p["insider_tip"] = insider_tip
    if image:
        p["image"] = image

    places.append(p)
    FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"\n✅ Added '{name}' to data/places.json")
    print("Next:  python scripts/seed_catalog.py")


if __name__ == "__main__":
    main()
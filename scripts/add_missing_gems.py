"""Append missing flagship hidden gems to data/places.json.
⚠️ Coordinates are city-area approximations — verify on Google Maps before demo."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "places.json"

NEW_GEMS = [
    {"name": "Mangalajodi Wetlands", "city": "Mangalajodi", "district": "Khordha",
     "category": "wildlife", "category_raw": "wetland", "source": "curated",
     "lat": 20.077, "lon": 85.393,
     "description": "A wetland village on Chilika's northern edge where former bird "
                    "poachers now work as protectors and boat guides — one of India's "
                    "best community-conservation stories. Winter dawns bring thousands "
                    "of migratory waders within a canoe's length.",
     "insider_tip": "Book the dawn boat through the village ecotourism counter; "
                    "Nov–Feb is peak birding season.",
     "best_time": "November to February",
     "tags": ["hidden-gem", "birding", "eco", "wetland", "curated"]},
    {"name": "Deomali Peak", "city": "Deomali", "district": "Koraput",
     "category": "nature", "category_raw": "mountain", "source": "curated",
     "lat": 18.756, "lon": 82.724,
     "description": "Odisha's highest peak (around 1,672 m) — a roll of green hills "
                    "and tribal villages in Koraput. The drive up is as much the "
                    "attraction as the summit panorama.",
     "insider_tip": "Time it for sunset; combine with Koraput's Parab festival (Nov–Dec).",
     "best_time": "October to February",
     "tags": ["hidden-gem", "peak", "tribal", "nature", "curated"]},
    {"name": "Hirakud Dam", "city": "Sambalpur", "district": "Sambalpur",
     "category": "nature", "category_raw": "dam", "source": "curated",
     "lat": 21.528, "lon": 83.869,
     "description": "One of the world's longest earthen dams (about 26 km) holding "
                    "back the Mahanadi near Sambalpur. The dyke-top drive and the "
                    "Gandhi Minar tower views are quintessentially Odia.",
     "insider_tip": "Sunset from Gandhi Minar; monsoon-season water releases are dramatic.",
     "best_time": "October to February",
     "tags": ["hidden-gem", "dam", "sunset", "nature", "curated"]},
]


def main() -> None:
    places = json.loads(FILE.read_text(encoding="utf-8"))
    added = 0
    for g in NEW_GEMS:
        if any(g["name"].lower() == p.get("name", "").lower() for p in places):
            print(f"⏭️  already present: {g['name']}")
            continue
        g["place_id"] = g["name"].lower().replace(" ", "-")
        g["location"] = {"type": "Point", "coordinates": [g["lon"], g["lat"]]}
        places.append(g)
        added += 1
        print(f"✅ added: {g['name']}")
    if added:
        FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"{added} gem(s) appended.")


if __name__ == "__main__":
    main()
"""Remove wrong/misleading images from data/places.json (human-curated blacklist).
Run → review output → python scripts/seed_catalog.py"""
import json
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "data" / "places.json"

# Places whose Commons match was wrong or misleading (from the fetch log review)
PRUNE = [
    "kings palace", "white palace", "jai stambha", "divis beach",
    "science park", "ore terminal", "buddhist museum", "the surgical world",
    "audi services", "fireman statue", "snake park", "dhyan chand",
    "mahatma gandhi", "gajapati narayana deva", "ratnagiri",   # got Maharashtra fort
    "nehru museum", "waterfalls", "model beach", "zoo", "district memorial",
    "hippopotamus zone", "nocturnal house", "aviary in zoo",
    "alluri seetharamaraju", "kanika palace", "maa bhagabati temple",
    "banpur", "satpada",          # monkey photo — weak; delete line if you disagree
    "talasari",                   # motorboats — weak; delete line if you disagree
    "gopabandhu park",            # road photo, not the park
]

places = json.loads(FILE.read_text(encoding="utf-8"))
pruned = 0
for p in places:
    if p.get("image") and any(k in p.get("name", "").lower() for k in PRUNE):
        for field in ("image", "image_credit", "image_source", "image_confidence"):
            p.pop(field, None)
        pruned += 1
        print(f"✂️  {p['name']}")

FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
print(f"\nPruned {pruned}. Remaining with images: "
      f"{sum(1 for p in places if p.get('image'))} / {len(places)}")
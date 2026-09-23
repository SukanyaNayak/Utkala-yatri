"""Mark the curated offbeat set as true hidden gems."""
import json
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "data" / "places.json"

GEMS = [   # edit freely — this list IS the editorial decision
    "mangalajodi", "deomali", "hirakud", "daringbadi", "chandipur",
    "bhitarkanika", "taptapani", "chandrabhaga", "ratnagiri", "lalitgiri",
    "hirapur", "sisupalgarh", "phurlijharan", "badaghagara", "sanaghagara",
    "gandahati", "joranda", "panchalingeswar", "barabati",
]

places = json.loads(FILE.read_text(encoding="utf-8"))
n = 0
for p in places:
    if any(k in p.get("name", "").lower() for k in GEMS) \
            and "hidden-gem" not in p.get("tags", []):
        p["tags"] = [*p.get("tags", []), "hidden-gem"]
        n += 1
        print(f"💎 {p['name']}")
FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
print(f"{n} places tagged.")
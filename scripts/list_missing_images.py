"""Show which places lack images, sorted by demo importance.
Also prints a ready-to-search Commons query per place."""
import json
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "data" / "places.json"
GEM_TAGS = {"hidden-gem", "hidden_gem", "offbeat", "gem"}

places = json.loads(FILE.read_text(encoding="utf-8"))
missing = [p for p in places if not p.get("image")]


def rank(p: dict) -> int:
    """0 = must-have (curated/gems), 1 = notable, 2 = long tail."""
    if p.get("source") == "curated" or p.get("description_source") == "hand_curated":
        return 0
    if any(t in GEM_TAGS for t in map(str.lower, p.get("tags", []))):
        return 0
    if (p.get("description") or "").strip():          # has any story
        return 1
    return 2


missing.sort(key=rank)
groups = {0: "🔴 MUST HAVE (curated + gems — judge will see these)",
          1: "🟡 Notable (has a description)",
          2: "⚪ Long tail (gradient placeholder is fine)"}

for level in (0, 1, 2):
    group = [p for p in missing if rank(p) == level]
    print(f"\n{groups[level]} — {len(group)} place(s)")
    for p in group:
        query = f"{p['name']} {p.get('city', '')}".strip()
        print(f"  • {p['name']} ({p.get('city', '')})"
              f"   → search: {query}")

print(f"\nTotal missing: {len(missing)} / {len(places)}")
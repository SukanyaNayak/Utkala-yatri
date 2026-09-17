"""Search Wikimedia Commons for real photos per place -> data/places.json.

One API call per place (search includes imageinfo URLs). Mismatch guard:
a result is 'strong' only if its title shares a distinctive word with the
place name — weak matches are saved with image_confidence:'low' so YOU can
review. Everything prints for human review, as always.

    python scripts/fetch_commons_images.py --limit 80
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "places.json"

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "UtkalaYatri-hackathon/1.0 (student tourism project)"}

GENERIC = {"falls", "waterfall", "waterfalls", "temple", "park", "beach",
           "hill", "hills", "view", "point", "national", "odisha", "india",
           "sanctuary", "lake", "fort", "museum", "cave", "caves", "site",
           "ancient", "prehistoric", "upper", "lower", "zone", "house"}


def _get(params: dict) -> dict:
    for attempt in range(4):
        r = requests.get(API, params=params, headers=HEADERS, timeout=20)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 0) or 0) or 30 * (attempt + 1)
            print(f"    ⏳ 429 — waiting {wait}s…")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise requests.HTTPError("429 persisted")


def distinctive_tokens(name: str) -> set[str]:
    words = re.findall(r"[a-z]{4,}", name.lower())
    return {w for w in words if w not in GENERIC}


def search_image(name: str, city: str) -> dict | None:
    """Return {url, file_title, confidence} or None."""
    data = _get({
        "action": "query", "format": "json",
        "generator": "search",
        "gsrsearch": f"{name} {city} filetype:bitmap".strip(),
        "gsrnamespace": 6, "gsrlimit": 3,
        "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 640,
    })
    pages = (data.get("query") or {}).get("pages") or {}
    hits = sorted(pages.values(), key=lambda p: p.get("index", 99))
    tokens = distinctive_tokens(name)

    for h in hits:
        infos = h.get("imageinfo") or []
        if not infos or not str(infos[0].get("mime", "")).startswith("image/"):
            continue
        title = h.get("title", "")
        url = infos[0].get("thumburl") or infos[0].get("url")
        if not url:
            continue
        t = title.lower()
        confidence = "strong" if (tokens & set(re.findall(r"[a-z]{4,}", t))) \
                     else "low"
        return {"url": url, "file_title": title, "confidence": confidence}
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=80)
    args = ap.parse_args()

    places = json.loads(FILE.read_text(encoding="utf-8"))
    targets = [p for p in places if not p.get("image")][: args.limit]
    print(f"Searching Commons for {len(targets)} place(s)…")

    got = 0
    for i, p in enumerate(targets, 1):
        try:
            hit = search_image(p["name"], p.get("city", ""))
        except Exception as exc:
            print(f"  [{i}] {p['name']}: FAILED {str(exc)[:100]}")
            hit = None
        if hit:
            p["image"] = hit["url"]
            p["image_credit"] = hit["file_title"]
            p["image_source"] = "wikimedia_commons"
            p["image_confidence"] = hit["confidence"]
            got += 1
            flag = "✅" if hit["confidence"] == "strong" else "⚠️ check"
            print(f"  [{i}] {p['name']}: {flag} {hit['file_title'][:60]}")
        else:
            print(f"  [{i}] {p['name']}: nothing on Commons")
        time.sleep(2)                      # always pace — success or fail

    FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"\n✅ {got} images added. Review the ⚠️ lines above:")
    print("   wrong photo → delete that entry's image/image_credit/… fields,")
    print("   then: python scripts/seed_catalog.py")


if __name__ == "__main__":
    main()
"""Fetch real Wikipedia intros + article images for places -> data/places.json.

- Skips hand_curated entries (your written stories win) unless --overwrite-ai
  also given (then only ai_enriched ones get replaced).
- Always tries to fill a missing image for any place.
- Truncates to first 2-3 sentences (~380 chars).
- License: Wikipedia text is CC BY-SA 4.0 — attribution is REQUIRED:
  add the credit line (below) to README and app footer.

    python scripts/enrich_places_wiki.py
    python scripts/enrich_places_wiki.py --limit 30
"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "places.json"

SEARCH_API = "https://en.wikipedia.org/w/api.php"
SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
HEADERS = {"User-Agent": "UtkalaYatri-hackathon/1.0 (student tourism project)"}


def _get(url: str, params: dict | None = None) -> requests.Response:
    """GET with 429 backoff (respects Retry-After). Raises on final failure."""
    for attempt in range(4):
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 0) or 0) or 30 * (attempt + 1)
            print(f"    ⏳ 429 — waiting {wait}s…")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    raise requests.HTTPError("429 persisted after 4 attempts")


def find_title(name: str, city: str) -> str | None:
    r = _get(SEARCH_API, params={
        "action": "query", "format": "json", "list": "search",
        "srlimit": 1, "maxlag": 5,                       # be a good citizen
        "srsearch": f"{name} {city} Odisha",
    })
    hits = r.json().get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def get_summary(title: str) -> dict | None:
    r = _get(SUMMARY_API + requests.utils.quote(title, safe=""))
    return r.json() if r.status_code == 200 else None

def first_sentences(text: str, max_chars: int = 380) -> str:
    out, count = "", 0
    for part in text.split(". "):
        out += (". " if out else "") + part.strip()
        count += 1
        if count >= 3 or len(out) >= max_chars:
            break
    return out + ("." if not out.endswith(".") else "")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--overwrite-ai", action="store_true",
                    help="also replace ai_enriched descriptions")
    args = ap.parse_args()

    places = json.loads(FILE.read_text(encoding="utf-8"))
    def _target(p: dict) -> bool:
        if p.get("description_source") == "hand_curated":
            return not p.get("image")                 # flagship: image only
        if not p.get("image"):
            return True
        if not (p.get("description") or "").strip():
            return True
        return bool(args.overwrite_ai
                    and p.get("description_source") == "ai_enriched")

    targets = [p for p in places if _target(p)][: args.limit]
    print(f"Fetching Wikipedia data for {len(targets)} place(s)…")
    got_desc = got_img = 0
    for i, p in enumerate(targets, 1):
        try:
            title = find_title(p["name"], p.get("city", ""))
            if not title:
                print(f"  [{i}] {p['name']}: no article — skipped")
                time.sleep(1)
                continue
            s = get_summary(title)
            time.sleep(1)                      # polite: ~1 req/s

            # image (works for every place with an article photo)
            img = ((s or {}).get("originalimage") or {}).get("source")
            if img and not p.get("image"):
                p["image"] = img
                got_img += 1

            # description: real sourced text replaces only AI-voiced/empty
            extract = (s or {}).get("extract", "")
            if (extract and p.get("description_source") == "ai_enriched"
                    and args.overwrite_ai) or (extract and not (p.get("description") or "").strip()):
                p["description"] = first_sentences(extract)
                p["description_source"] = "wikipedia"
                p["description_license"] = "CC BY-SA 4.0"
                got_desc += 1
            print(f"  [{i}] {p['name']} → wiki: '{title}'"
                  f"{' | img ✅' if img else ''}")
        except Exception as exc:
            print(f"  [{i}] {p['name']}: FAILED {str(exc)[:100]}")
            time.sleep(2)   

    FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"\n✅ descriptions from Wikipedia: {got_desc}, images added: {got_img}")
    print("   Review the title mappings above (wrong match? delete that line),")
    print("   then: python scripts/seed_catalog.py")


if __name__ == "__main__":
    main()
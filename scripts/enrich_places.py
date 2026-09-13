"""Fill missing descriptions + best_time for places via Gemini (BUILD TIME).

Scope-controlled: by default only enriches 'gem-ish' places without a
description. Reviews happen in git — nothing touches MongoDB until you
re-run seed_catalog.py.

    python scripts/enrich_places.py                # gems subset, cap 60
    python scripts/enrich_places.py --limit 100    # more per run
    python scripts/enrich_places.py --all          # every description-less place

Honesty rule baked into the prompt: the model may only phrase what's
inferable from name/category/region — no invented heights, dates or history.
"""
import time
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

FILE = ROOT / "data" / "places.json"
GEM_TAGS = {"hidden-gem", "hidden_gem", "offbeat", "lesser-known", "gem"}

PROMPT = """You write 'hidden gem' blurbs for an Odisha (India) travel app.
Place record:
{record}

Return ONLY JSON: {{"description": "...", "best_time": "..."}}
Description rules (2-3 sentences, max 45 words):
- Sentence 1: what the place is, from the category/name/region only.
- Sentence 2: the hidden-gem angle as EXPECTATION-SETTING, not facts —
  e.g. "far from the tourist circuit", "you'll likely share it with locals",
  "facilities are basic — plan ahead". These are safe for any such place.
- Sentence 3 (optional): a practical caution like checking road/access locally.
- NEVER invent specifics: no heights, lengths, dates, history, or superlatives.
best_time: short phrase from general Odisha climate, e.g. "October to February"."""

def is_gemish(p: dict) -> bool:
    tags = {str(t).lower() for t in p.get("tags", [])}
    return bool(tags & GEM_TAGS) or p.get("category") in ("nature", "wildlife")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true",
                    help="re-enrich entries previously written by AI")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--model", default=None,
                    help="override model, e.g. gemini-2.5-flash-lite (higher free-tier RPM)")
    args = ap.parse_args()

    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = args.model or os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

    places = json.loads(FILE.read_text(encoding="utf-8"))
    def _target(p: dict) -> bool:
        if args.redo:
            return p.get("description_source") == "ai_enriched"
        return (not (p.get("description") or "").strip()
                and (args.all or is_gemish(p)))

    targets = [p for p in places if _target(p)][: args.limit]
    print(f"Enriching {len(targets)} place(s) with {model} …")
    done, min_gap = 0, 5          # ~12 requests/min — inside free-tier limits

    for i, p in enumerate(targets, 1):
        record = {k: p.get(k) for k in
                  ("name", "category", "category_raw", "city", "district")}
        patch = None
        for attempt in range(4):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=PROMPT.format(record=json.dumps(record, ensure_ascii=False)),
                    config={"response_mime_type": "application/json",
                            "temperature": 0.4})
                patch = json.loads(resp.text)
                break
            except Exception as exc:
                msg = str(exc)
                print(f"  [{i}] {p['name']}: {msg[:300]}")     # full error, visible
                if "404" in msg or "NOT_FOUND" in msg:
                    sys.exit("\n❌ Model not found. Run `python scripts/list_models.py` "
                             "and pass a live name via --model "
                             "(aliases like gemini-flash-lite-latest are safest).")
                if "429" in msg:
                    wait = 60 * (attempt + 1)
                    print(f"  [{i}] ⏳ quota — waiting {wait}s…")
                    time.sleep(wait)
                elif "503" in msg or "UNAVAILABLE" in msg:
                    wait = 15 * (attempt + 1)
                    print(f"  [{i}] ⏳ 503 — waiting {wait}s…")
                    time.sleep(wait)
                else:
                    break
        if not patch:
            continue

        desc = (patch.get("description") or "").strip()
        if desc:
            p["description"] = desc
            p["description_source"] = "ai_enriched"
        bt = (patch.get("best_time") or "").strip()
        if bt and not p.get("best_time"):
            p["best_time"] = bt
        done += 1
        print(f"  [{i}/{len(targets)}] {p['name']}: ✅ {desc[:60]}…")
        time.sleep(min_gap)                          # polite pacing

    if done:
        FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"\n✅ {done} places updated in data/places.json")
        print("   → review with `git diff data/places.json`, then re-seed:")
        print("     python scripts/seed_catalog.py")
    else:
        print("Nothing enriched.")


if __name__ == "__main__":
    main()
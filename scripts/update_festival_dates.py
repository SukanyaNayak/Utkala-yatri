"""Compute lunar festival dates and merge into data/festivals.json.

Usage:  python scripts/update_festival_dates.py --years 2026 2027
Adds entries as  "approximate": true, "source": "computed".
Verify on drikpanchang.com, then edit to  "approximate": false, "source": "verified".
"""
import argparse, json
from datetime import timedelta
from pathlib import Path
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.panchang import LUNAR_RULES, compute_dates

FILE = Path(__file__).resolve().parents[1] / "data" / "festivals.json"


def self_test(data: list[dict]) -> None:
    """Compare calculator against dates you already verified for 2025."""
    print("— self-test vs verified known_dates —")
    for fest in data:
        verified = next((d for d in fest.get("known_dates", [])
                         if d["year"] == 2025 and not d.get("approximate")), None)
        if not verified or fest["festival_id"] not in LUNAR_RULES:
            continue
        got = compute_dates(fest["festival_id"], 2025)
        ok = bool(got) and got[0]["date"].isoformat() == verified["start"]
        print(f"  {'✅' if ok else '⚠️ '}{fest['festival_id']}: "
              f"computed={got[0]['date'] if got else '—'} verified={verified['start']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    years = ap.parse_args().years

    data = json.loads(FILE.read_text(encoding="utf-8"))
    self_test(data)

    for fest in data:
        fid = fest["festival_id"]
        if fid not in LUNAR_RULES:
            continue  # solar/fixed festivals (Raja Parba, Konark) stay window-based
        for year in years:
            if any(d["year"] == year and not d.get("approximate")
                   for d in fest.get("known_dates", [])):
                continue  # already verified — never overwrite
            out = compute_dates(fid, year)
            if not out:
                print(f"  ❓ no match for {fid} {year} — check manually")
                continue
            start = out[0]["date"]
            fest.setdefault("known_dates", []).append({
                "year": year, "start": start.isoformat(),
                "end": (start + timedelta(days=fest.get("duration_days", 1) - 1)).isoformat(),
                "approximate": True, "source": "computed", "rule": out[0]["rule"],
            })
            print(f"  🧮 {fid} {year} → {start}  (verify then flip flag)")

    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
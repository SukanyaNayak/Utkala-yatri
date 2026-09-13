"""Festival queries. Primary: MongoDB. Fallback: data/festivals.json (offline-safe).

Date priority: verified dates > computed dates > typical month window.
"""
import calendar
import json
from datetime import date, timedelta
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "festivals.json"


def _collection():
    try:
        from services.mongodb_service import get_collection
        return get_collection("festivals")
    except Exception:
        return None


def _load_file() -> list[dict]:
    if not hasattr(_load_file, "_cache"):
        _load_file._cache = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return _load_file._cache


def get_all_festivals() -> list[dict]:
    col = _collection()
    if col is not None:
        try:
            docs = list(col.find({}, {"_id": 0}))
            if docs:
                return docs
        except Exception:
            pass
    return _load_file()


def _known_range(f: dict, year: int):
    """Best date entry for `year`, preferring verified over approximate.

    Returns (start, end, is_approximate, source) or None.
    """
    best = None
    for d in f.get("known_dates", []):
        if d.get("year") != year:
            continue
        if best is None or (best.get("approximate") and not d.get("approximate")):
            best = d
    if best:
        return (date.fromisoformat(best["start"]),
                date.fromisoformat(best.get("end") or best["start"]),
                bool(best.get("approximate")),
                best.get("source", "manual"))
    return None


def _next_occurrence(f: dict, today: date):
    for year in (today.year, today.year + 1):
        hit = _known_range(f, year)
        if hit and hit[1] >= today:
            return hit
    months = f.get("typical_window", {}).get("months", [])
    if months:
        candidates = [date(today.year if m >= today.month else today.year + 1, m, 15)
                      for m in months]
        best = min(candidates)
        if best >= today:
            return best, best, True, "window"
    return None


def get_upcoming_festivals(days_ahead: int = 60, limit: int = 8) -> list[dict]:
    today, horizon, out = date.today(), date.today() + timedelta(days=days_ahead), []
    for f in get_all_festivals():
        occ = _next_occurrence(f, today)
        if occ and occ[0] <= horizon:
            start, end, approx, source = occ
            out.append({**f,
                        "next_start": start.isoformat(),
                        "next_end": end.isoformat(),
                        "dates_approximate": approx,
                        "date_source": source})
    out.sort(key=lambda x: x["next_start"])
    return out[:limit]


def get_festivals_during(start: date, end: date) -> list[dict]:
    """Festivals overlapping a trip window (trip-planner callout).

    Attaches uniform display fields so pages can treat results like
    get_upcoming_festivals output:
      - next_start / next_end : ISO dates (known-date matches only)
      - typical_months        : overlapping month numbers (window matches)
      - date_confidence       : 'known' | 'typical_month'
    """
    months = set()
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.add(m)
        m += 1
        if m == 13:
            m, y = 1, y + 1

    exact, approx = [], []
    for f in get_all_festivals():
        hit = None
        for d in f.get("known_dates", []):
            d_start = date.fromisoformat(d["start"])
            d_end = date.fromisoformat(d.get("end") or d["start"])
            if d_start <= end and d_end >= start:
                hit = d
                break
        if hit:
            exact.append({**f,
                          "next_start": hit["start"],
                          "next_end": hit.get("end") or hit["start"],
                          "date_confidence": "known"})
        elif months & set(f.get("typical_window", {}).get("months", [])):
            approx.append({**f,
                           "typical_months": sorted(months & set(f["typical_window"]["months"])),
                           "date_confidence": "typical_month"})
    return exact + approx
def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def get_festivals_near(lat: float, lon: float, radius_km: float = 100, limit: int = 10) -> list[dict]:
    hits = []
    for f in get_all_festivals():
        flon, flat = f["location"]["coordinates"]  # GeoJSON: [lng, lat]
        d = _haversine_km(lat, lon, flat, flon)
        if d <= radius_km:
            hits.append({**f, "distance_km": round(d, 1)})
    hits.sort(key=lambda x: x["distance_km"])
    return hits[:limit]


def search_festivals(query: str) -> list[dict]:
    q = (query or "").strip().lower()
    if not q:
        return []
    out = []
    for f in get_all_festivals():
        hay = " ".join([*f.get("name", {}).values(), *f.get("description", {}).values(),
                        f.get("city", ""), f.get("district", ""), *f.get("tags", [])]).lower()
        if q in hay:
            out.append(f)
    return out


def build_gemini_context(lang: str = "en", limit: int = 40) -> str:
    """Compact text block to inject into the chatbot's prompt."""
    lines = []
    for f in get_all_festivals()[:limit]:
        name = f["name"].get(lang) or f["name"]["en"]
        desc = f["description"].get(lang) or f["description"]["en"]
        months = "/".join(calendar.month_abbr[m] for m in f.get("typical_window", {}).get("months", []))
        dates = "; ".join(
            f"{d['start']}–{d.get('end', d['start'])}" + (" (approx)" if d.get("approximate") else "")
            for d in f.get("known_dates", [])) or "varies with lunar calendar"
        lines.append(f"- {name} ({f['city']}) | months: {months} | dates: {dates} | {desc}")
    return "\n".join(lines)
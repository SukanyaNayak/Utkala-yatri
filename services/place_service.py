"""Place queries. Primary: MongoDB (places). Fallback: data/places.json.

Same structure as festival_service.py — MongoDB first, file fallback so
the demo never dies if Atlas is unreachable.
"""
from __future__ import annotations

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "places.json"

CATEGORY_META = {   # emoji + hex color per bucket (used by map + cards)
    "heritage": ("🏛️", "#8e44ad"),
    "beach":    ("🏖️", "#e67e22"),
    "nature":   ("🌿", "#27ae60"),
    "wildlife": ("🐅", "#16a085"),
    "museum":   ("🖼️", "#2980b9"),
    "hotel":    ("🏨", "#c0392b"),
    "other":    ("📍", "#7f8c8d"),
}


def category_meta(category: str) -> tuple[str, str]:
    return CATEGORY_META.get(category, CATEGORY_META["other"])


def _collection():
    try:
        from services.mongodb_service import get_collection
        return get_collection("places")
    except Exception:
        return None


def _load_file() -> list[dict]:
    if not hasattr(_load_file, "_cache"):
        _load_file._cache = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return _load_file._cache


def get_all_places() -> list[dict]:
    col = _collection()
    if col is not None:
        try:
            docs = list(col.find({}, {"_id": 0}))
            if docs:
                return docs
        except Exception:
            pass
    return _load_file()


def get_place(place_id: str) -> dict | None:
    if not place_id:
        return None
    for p in get_all_places():
        if p.get("place_id") == place_id:
            return p
    return None


def get_categories() -> list[str]:
    return sorted({p.get("category", "other") for p in get_all_places()})


def search_places(query: str = "", category: str = "All",
                  limit: int = 500) -> list[dict]:
    q = (query or "").strip().lower()
    out = []
    for p in get_all_places():
        if category != "All" and p.get("category") != category:
            continue
        if q:
            hay = " ".join([p.get("name", ""), p.get("description", ""),
                            p.get("city", ""), p.get("district", ""),
                            " ".join(p.get("tags", []))]).lower()
            if q not in hay:
                continue
        out.append(p)
    return out[:limit]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def get_nearby_places(lat: float, lon: float, radius_km: float = 50,
                      limit: int = 8, exclude_id: str | None = None,
                      category: str | None = None) -> list[dict]:
    hits = []
    for p in get_all_places():
        if exclude_id and p.get("place_id") == exclude_id:
            continue
        if category and p.get("category") != category:
            continue
        d = _haversine_km(lat, lon, p["lat"], p["lon"])
        if d <= radius_km:
            hits.append({**p, "distance_km": round(d, 1)})
    hits.sort(key=lambda x: x["distance_km"])
    return hits[:limit]


def build_places_context(limit: int = 25) -> str:
    """Compact text block for the chatbot prompt (curated places first)."""
    places = sorted(get_all_places(),
                    key=lambda p: 0 if p.get("source") == "curated" else 1)
    lines = []
    for p in places[:limit]:
        desc = (p.get("description") or "")[:120]
        lines.append(f"- {p['name']} ({p.get('city', '')}) | "
                     f"{p.get('category', '')} | {desc}")
    return "\n".join(lines)
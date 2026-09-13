"""Hotel + emergency lookups. MongoDB primary, JSON file fallback.

Same contract as place_service / festival_service:
  - records carry lat/lon floats AND location GeoJSON
  - every function degrades gracefully (empty list, never raises)
"""
from __future__ import annotations

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOTELS_FILE = ROOT / "data" / "hotels.json"
EMERGENCY_FILE = ROOT / "data" / "emergency.json"


def _collection(name: str):
    try:
        from services.mongodb_service import get_collection
        return get_collection(name)
    except Exception:
        return None


def _load_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    if not hasattr(_load_file, "_cache"):
        _load_file._cache = {}
    if path.name not in _load_file._cache:
        _load_file._cache[path.name] = json.loads(
            path.read_text(encoding="utf-8"))
    return _load_file._cache[path.name]


def _get_all(name: str, fallback: list[dict]) -> list[dict]:
    col = _collection(name)
    if col is not None:
        try:
            docs = list(col.find({}, {"_id": 0}))
            if docs:
                return docs
        except Exception:
            pass
    return fallback


# ---------------- hotels ----------------

def get_all_hotels() -> list[dict]:
    return _get_all("hotels", _load_file(HOTELS_FILE))


def get_hotels_near(lat: float, lon: float, radius_km: float = 25,
                    limit: int = 12) -> list[dict]:
    hits = []
    for h in get_all_hotels():
        if h.get("lat") is None or h.get("lon") is None:
            continue
        d = _haversine_km(lat, lon, h["lat"], h["lon"])
        if d <= radius_km:
            hits.append({**h, "distance_km": round(d, 1)})
    hits.sort(key=lambda x: x["distance_km"])
    return hits[:limit]


def price_band(price_range: str) -> str:
    """'3500-6500' / 'Premium' / '₹₹₹' → one of budget/mid/premium/unknown."""
    s = str(price_range or "").lower()
    if any(k in s for k in ("budget", "₹", "1000", "1500", "2000", "2500")):
        return "budget"
    if any(k in s for k in ("premium", "luxury", "8000", "10000", "12000")):
        return "premium"
    if any(k in s for k in ("mid", "3000", "3500", "4000", "5000", "6000", "7000")):
        return "mid"
    return "unknown"


# ---------------- emergency ----------------

def get_all_emergency() -> list[dict]:
    data = _get_all("emergency", _load_file(EMERGENCY_FILE))
    out = []
    for e in data:
        lat, lon = e.get("lat"), e.get("lon")
        out.append({**e,
                    "lat": float(lat) if lat not in (None, "") else None,
                    "lon": float(lon) if lon not in (None, "") else None})
    return out


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def get_emergency_near(lat: float, lon: float, limit: int = 6) -> list[dict]:
    items = [e for e in get_all_emergency() if e.get("lat") is not None]
    for e in items:
        e["distance_km"] = round(_haversine_km(lat, lon, e["lat"], e["lon"]), 1)
    items.sort(key=lambda x: x["distance_km"])
    return items[:limit]
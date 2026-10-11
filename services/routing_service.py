"""Road routing — provider configurable: OSRM (default, keyless) or OpenRouteService.

Public API:
    get_route_between(p1, p2) -> {distance_km, duration_min, geometry, provider}
        Never returns None — falls back to a straight-line road-factor estimate.
    order_stops(start, stops) -> nearest-neighbour ordering for a day plan.

geometry follows folium's [lat, lon] convention.
"""
from __future__ import annotations

import os
from math import asin, cos, radians, sin, sqrt

import requests
from services.cache_compat import cache_data

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# Road-distance inflation factor for the offline fallback estimate
ROAD_FACTOR, EST_AVG_KMH = 1.25, 40


def provider() -> str:
    p = os.getenv("ROUTING_PROVIDER", "osrm").lower()
    if p == "ors":
        key = os.getenv("OPENROUTESERVICE_API_KEY", "")
        if key and "your_ors" not in key:
            return "ors"
    return "osrm"          # key missing/placeholder -> public OSRM


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))

@cache_data

def _fetch(lat1, lon1, lat2, lon2) -> dict | None:
    prov = provider()
    try:
        if prov == "ors":
            r = requests.post(
                ORS_URL,
                headers={"Authorization": os.environ["OPENROUTESERVICE_API_KEY"]},
                json={"coordinates": [[lon1, lat1], [lon2, lat2]]},
                timeout=10)
            r.raise_for_status()
            seg = r.json()["routes"][0]
            dist, dur = seg["summary"]["distance"] / 1000, seg["summary"]["duration"] / 60
            geom = [[c[1], c[0]] for c in seg["geometry"]["coordinates"]]
        else:
            r = requests.get(
                f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}",
                params={"overview": "full", "geometries": "geojson"}, timeout=10)
            r.raise_for_status()
            route = r.json()["routes"][0]
            dist, dur = route["distance"] / 1000, route["duration"] / 60
            geom = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
        return {"distance_km": round(dist, 1), "duration_min": max(1, int(dur)),
                "geometry": geom, "provider": prov}
    except Exception as exc:
        print(f"routing [{prov}] failed:", exc)
        return None


def get_route_between(p1: dict, p2: dict) -> dict:
    """Route between two place dicts — graceful straight-line fallback."""
    res = _fetch(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
    if res:
        return res
    d = _haversine_km(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
    road = d * ROAD_FACTOR
    return {"distance_km": round(road, 1),
            "duration_min": max(1, int(road / EST_AVG_KMH * 60)),
            "geometry": [[p1["lat"], p1["lon"]], [p2["lat"], p2["lon"]]],
            "provider": "estimate"}


def order_stops(start: dict, stops: list[dict]) -> list[dict]:
    """Greedy nearest-neighbour ordering — good enough for <=8 stops."""
    remaining, ordered, cur = list(stops), [], start
    while remaining:
        nxt = min(remaining, key=lambda s: _haversine_km(
            cur["lat"], cur["lon"], s["lat"], s["lon"]))
        ordered.append(nxt)
        remaining.remove(nxt)
        cur = nxt
    return ordered
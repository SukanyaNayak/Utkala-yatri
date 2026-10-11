from fastapi import APIRouter, Query

from services.festival_service import (
    get_all_festivals,
    get_festivals_during,
    get_festivals_near,
    get_upcoming_festivals,
    search_festivals,
)

from backend.schemas import DuringRequest

router = APIRouter()


@router.get("")
def all_festivals():
    return get_all_festivals()


@router.get("/upcoming")
def upcoming(days_ahead: int = 60, limit: int = 8):
    return get_upcoming_festivals(days_ahead=days_ahead, limit=limit)


@router.get("/search")
def search(q: str = Query(min_length=1)):
    return search_festivals(q)


@router.get("/near")
def near(lat: float, lon: float, radius_km: float = 100, limit: int = 10):
    return get_festivals_near(lat, lon, radius_km=radius_km, limit=limit)


@router.post("/during")
def during(body: DuringRequest):
    from datetime import date
    return get_festivals_during(date.fromisoformat(body.start),
                                date.fromisoformat(body.end))
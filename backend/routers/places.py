from fastapi import APIRouter, HTTPException, Query

from services import place_service, review_service, translate_service

router = APIRouter()


@router.get("")
def list_places(query: str = "", category: str = "All", limit: int = 500):
    return place_service.search_places(query=query, category=category, limit=limit)


@router.get("/categories")
def categories():
    return place_service.get_categories()


@router.get("/near")
def near(lat: float, lon: float, radius_km: float = 50, limit: int = 8,
         category: str | None = None):
    return place_service.get_nearby_places(lat, lon, radius_km=radius_km,
                                           limit=limit, category=category)


@router.get("/{place_id}/review-summary")
def review(place_id: str):
    place = place_service.get_place(place_id)
    if not place:
        raise HTTPException(404, "Place not found")
    return {"summary": review_service.summary(place)}


@router.get("/{place_id}")
def get_place(place_id: str):
    place = place_service.get_place(place_id)
    if not place:
        raise HTTPException(404, "Place not found")
    return place
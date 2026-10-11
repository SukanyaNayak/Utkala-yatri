from fastapi import APIRouter

from services import hotel_service

router = APIRouter()


@router.get("/near")
def near(lat: float, lon: float, radius_km: float = 25, limit: int = 40,
         band: str = "All"):
    hits = hotel_service.get_hotels_near(lat, lon, radius_km=radius_km,
                                         limit=limit)
    if band != "All":
        hits = [h for h in hits
                if hotel_service.price_band(
                    h.get("price") or h.get("price_range_inr") or "") == band]
    return hits
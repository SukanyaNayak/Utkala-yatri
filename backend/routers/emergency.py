from fastapi import APIRouter

from services import hotel_service

router = APIRouter()


@router.get("/near")
def near(lat: float, lon: float, limit: int = 6):
    return hotel_service.get_emergency_near(lat, lon, limit=limit)


@router.get("")
def all_facilities():
    return hotel_service.get_all_emergency()
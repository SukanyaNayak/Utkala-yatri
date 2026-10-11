from fastapi import APIRouter

from services.routing_service import get_route_between, order_stops

from backend.schemas import OrderRequest, RouteRequest

router = APIRouter()


@router.post("/route")
def route(body: RouteRequest):
    a = {"lat": body.origin.lat, "lon": body.origin.lon}
    b = {"lat": body.destination.lat, "lon": body.destination.lon}
    return get_route_between(a, b)


@router.post("/order")
def order(body: OrderRequest):
    start = {"lat": body.origin.lat, "lon": body.origin.lon}
    stops = [{"name": s.name, "lat": s.lat, "lon": s.lon} for s in body.stops]
    return order_stops(start, stops)
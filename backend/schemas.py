from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    history: list[ChatMessage]          # newest message LAST
    lang: str = "auto"


class PlaceRef(BaseModel):
    name: str = ""
    lat: float
    lon: float


class RouteRequest(BaseModel):
    origin: PlaceRef
    destination: PlaceRef


class OrderRequest(BaseModel):
    origin: PlaceRef
    stops: list[PlaceRef] = Field(min_length=1)


class DuringRequest(BaseModel):
    start: str          # ISO date, e.g. "2026-10-01"
    end: str
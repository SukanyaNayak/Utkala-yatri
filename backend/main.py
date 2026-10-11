"""UtkalaYatri FastAPI backend — wraps the existing services/ layer."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                      # services/ imports
os.environ.setdefault("UTKALAYATRI_BACKEND", "1")  # BEFORE any service import

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import chat, emergency, festivals, hotels, landmark, places, planner, voice
app = FastAPI(title="UtkalaYatri API", version="1.0.0",
              description="AI travel companion for Odisha — grounded in a curated database.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Phase B: replace with your Vercel/Netlify URL
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(places.router,    prefix="/api/places",    tags=["places"])
app.include_router(festivals.router, prefix="/api/festivals", tags=["festivals"])
app.include_router(hotels.router,    prefix="/api/hotels",    tags=["hotels"])
app.include_router(emergency.router, prefix="/api/emergency", tags=["emergency"])
app.include_router(planner.router,   prefix="/api/planner",   tags=["planner"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["chat"])
app.include_router(landmark.router,  prefix="/api/landmark",  tags=["landmark"])
app.include_router(voice.router,     prefix="/api/voice",     tags=["voice"])


@app.get("/api/health", tags=["health"])
def health():
    from services.mongodb_service import test_connection
    ok, msg = test_connection()
    return {"mongo": ok, "detail": msg}
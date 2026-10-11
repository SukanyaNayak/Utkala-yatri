"""Landmark recognition: photo -> a place in OUR database (never open-ended).

The model must pick from candidate place_ids we provide — no free-form
answers that could hallucinate a place we don't have.
"""
from __future__ import annotations

from services import gemini_service, place_service

_SYSTEM = "You are a precise landmark recognition engine for Odisha, India."


def _candidates(limit: int = 60) -> list[dict]:
    """Curated places first — they have the richest, most reliable data."""
    places = sorted(place_service.get_all_places(),
                    key=lambda p: 0 if p.get("source") == "curated" else 1)
    return [{"place_id": p["place_id"], "name": p["name"],
             "city": p.get("city", "")} for p in places[:limit]]


def identify(image_bytes: bytes, mime: str = "image/jpeg") -> dict | None:
    """Returns {matched_place_id, confidence, best_guess, seen} or None."""
    cands = _candidates()
    listing = "\n".join(f"- {c['place_id']} | {c['name']} | {c['city']}"
                        for c in cands)
    prompt = f"""Identify the landmark shown in this image.

Candidate places from our database:
{listing}

Return ONLY JSON:
{{"matched_place_id": "<id from the list, or null>",
  "confidence": "high|medium|low",
  "best_guess": "<name if unsure or not in the list>",
  "seen": "<one sentence: what is visible in the photo>"}}

Rules: match only if the image plausibly shows that exact place.
Ordinary buildings, streets or people -> matched_place_id must be null."""
    raw = gemini_service.ask_with_image(image_bytes, mime, prompt,
                                        system=_SYSTEM, temperature=0.1)
    return gemini_service._extract_json(raw)
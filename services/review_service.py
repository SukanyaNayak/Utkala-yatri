"""'What visitors say' — AI digest generated from place ATTRIBUTES.

Honesty contract: clearly a synthesis of the place's data fields, never
invented quotes, reviewer names or star ratings. Works under both
Streamlit and FastAPI (no Streamlit touchpoints).
"""
from __future__ import annotations

from services import gemini_service

_SYSTEM = ("You summarize what travelers typically value about a place, "
           "from its attributes only. You never invent quotes, names or ratings.")


def summary(place: dict) -> str:
    facts = "\n".join(
        f"- {k}: {place[k]}" for k in
        ("name", "category", "city", "description", "best_time", "tags")
        if place.get(k))
    return gemini_service.ask(
        f"Place attributes:\n{facts}\n\n"
        "Write 'What visitors say' as exactly 3 short bullets:\n"
        "- What travelers typically appreciate here\n"
        "- What to watch out for / practical reality\n"
        "- Who this place is best for\n\n"
        "Frame from the attributes above (category, description, season, "
        "tags). No fabricated quotes, names, dates or star ratings. "
        "Max 70 words total.",
        system=_SYSTEM, temperature=0.5)
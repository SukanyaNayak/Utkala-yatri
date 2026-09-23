"""On-demand UI-content translation via Gemini, cached in session_state.

Honesty rule: translated content is labeled as AI-translated and is never
written back to the database.
"""
from __future__ import annotations

import streamlit as st

from services import gemini_service

_LANG_NAMES = {"hi": "Hindi (Devanagari)", "or": "Odia (Odia script)"}


@st.cache_data(show_spinner=False, ttl=86400)   # one day per text+lang
def _translate(text: str, lang: str) -> str:
    resp = gemini_service.ask(
        f"Translate the following tourism description into {lang}. "
        "Keep place names unchanged. Output ONLY the translation.\n\n" + text,
        system="You are a precise translator for travel content.",
        temperature=0.2)
    return resp or ""


def localized_text(text: str, lang: str = "en") -> tuple[str, bool]:
    """Returns (text, was_translated). Falls back to English on any failure."""
    if lang == "en" or not text:
        return text, False
    translated = _translate(text, _LANG_NAMES.get(lang, lang))
    if not translated:
        return text, False
    return translated, True
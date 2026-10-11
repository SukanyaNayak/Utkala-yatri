"""On-demand UI-content translation via Gemini.

Manual dict cache instead of st.cache_data: gemini_service.ask() calls
st.toast() on errors, and a Streamlit element inside a @st.cache_data
function breaks cache replay. A plain dict also lets us skip caching
empty (failed) results, so transient failures retry on the next rerun.
"""
from __future__ import annotations

from services import gemini_service

_LANG_NAMES = {"hi": "Hindi (Devanagari)", "or": "Odia (Odia script)"}
_CACHE: dict[tuple[str, str], str] = {}
_MAX_CACHE = 2000


def _translate(text: str, lang: str) -> str:
    key = (text, lang)
    if key in _CACHE:
        return _CACHE[key]
    resp = gemini_service.ask(
        f"Translate the following tourism description into {lang}. "
        "Keep place names unchanged. Output ONLY the translation.\n\n" + text,
        system="You are a precise translator for travel content.",
        temperature=0.2)
    result = resp or ""
    if result and len(_CACHE) < _MAX_CACHE:   # never cache failed/empty results
        _CACHE[key] = result
    return result


def localized_text(text: str, lang: str = "en") -> tuple[str, bool]:
    """Returns (text, was_translated). Falls back to English on any failure."""
    if lang == "en" or not text:
        return text, False
    translated = _translate(text, _LANG_NAMES.get(lang, lang))
    if not translated:
        return text, False
    return translated, True
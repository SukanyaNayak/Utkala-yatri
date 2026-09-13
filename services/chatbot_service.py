"""Chatbot brain: assembles the system prompt from app data + generates replies.

Free of Streamlit UI logic — portable to a FastAPI backend unchanged.
"""
from __future__ import annotations

from datetime import date

from services import gemini_service
from services.festival_service import build_gemini_context, get_upcoming_festivals
from services.place_service import build_places_context

LANG_INSTRUCTIONS = {
    "auto": "Reply in the same language the visitor used (English, Hindi, or Odia).",
    "en": "Reply in English.",
    "hi": "Reply in Hindi (Devanagari script).",
    "or": "Reply in Odia (Odia script).",
}

MAX_HISTORY_MESSAGES = 12   # keep prompt size bounded


def build_system_prompt(lang: str = "auto") -> str:
    today = date.today().isoformat()

    upcoming = get_upcoming_festivals(days_ahead=45, limit=5)
    upcoming_lines = "\n".join(
        f"- {f['name']['en']} ({f['city']}): {f['next_start']} to {f['next_end']}"
        + (" (dates approximate)" if f.get("dates_approximate") else "")
        for f in upcoming
    ) or "- (none in the next 45 days)"

    return f"""You are UtkalaYatri, a friendly AI travel guide for Odisha, India.
Today's date: {today}.

Festivals coming up (from our verified database):
{upcoming_lines}

Festival reference:
{build_gemini_context(lang='en')}

Places reference (curated places first):
{build_places_context(limit=25)}

Rules:
1. Base factual claims about places and festivals ONLY on the reference data above. If something is not covered there, say you are not certain instead of inventing it.
2. Never state exact dates for lunar-calendar festivals unless the dates above are not marked approximate — otherwise say dates shift yearly with the lunar calendar.
3. {LANG_INSTRUCTIONS.get(lang, LANG_INSTRUCTIONS['auto'])}
4. Be concise and practical: short paragraphs, bullets for lists, 2-3 concrete suggestions rather than exhaustive lists.
5. For hotels, transport or prices beyond the data above, give general guidance and advise verifying current details.
6. When planning itineraries, remember the distances in the data are straight-line; road travel in Odisha takes noticeably longer.
"""


def get_reply(history: list[dict], lang: str = "auto") -> str:
    """Generate the next assistant message.

    history: [{'role': 'user'|'assistant', 'content': str}, ...]
             INCLUDING the newest user message as the last item.
    Returns "" if Gemini is unreachable (caller shows a fallback).
    """
    recent = history[-MAX_HISTORY_MESSAGES:]
    convo = "\n\n".join(
        f"{'Visitor' if m['role'] == 'user' else 'UtkalaYatri'}: "
        f"{m['content'][:600]}"
        for m in recent
    )
    prompt = (f"Conversation so far:\n{convo}\n\n"
              "Reply to the Visitor's last message as UtkalaYatri:")
    return gemini_service.ask(prompt, system=build_system_prompt(lang))
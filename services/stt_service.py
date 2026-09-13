"""Speech-to-text: WAV recording -> text, via Gemini. Cached + demo-safe."""
from __future__ import annotations

import streamlit as st

from services import gemini_service

_UNINTELLIGIBLE = "[unintelligible]"

_TRANSCRIBE_PROMPT = (
    "Transcribe the spoken words exactly, in the language spoken. "
    "Output ONLY the transcription — no comments, no punctuation fixes. "
    f"If the audio is silent or unintelligible, output exactly: {_UNINTELLIGIBLE}"
)


@st.cache_data(show_spinner=False)
def transcribe(audio_bytes: bytes) -> str:
    """Return the transcribed text, or "" if it couldn't be heard."""
    if not audio_bytes:
        return ""
    text = gemini_service.ask_with_audio(
        audio_bytes, mime_type="audio/wav",
        prompt=_TRANSCRIBE_PROMPT,
        system="You are a precise speech-to-text engine.")
    if not text or _UNINTELLIGIBLE in text.lower():
        return ""
    return text
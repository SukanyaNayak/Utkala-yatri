"""Text-to-speech for chatbot replies — multi-engine, demo-safe.

Engines:
  en/hi -> gTTS (Google Translate voices), edge-tts as backup
  or    -> edge-tts (Microsoft) IF an Odia voice exists, else graceful
           "no audio" note (Odia stays text-first)

Successes are cached; failures are NEVER cached, so a transient network
blip doesn't permanently mute a message.
"""
from __future__ import annotations

import asyncio
import io
import re

import streamlit as st


def detect_lang(text: str, chosen: str = "auto") -> str:
    """Explicit choice wins; else detect by script (Odia, Devanagari)."""
    if chosen in ("en", "hi", "or"):
        return chosen
    if any("\u0B00" <= ch <= "\u0B7F" for ch in text):
        return "or"
    if any("\u0900" <= ch <= "\u097F" for ch in text):
        return "hi"
    return "en"


def clean_for_speech(text: str, max_chars: int = 900) -> str:
    """Strip markdown/symbol noise so speech sounds natural and synthesis
    is fast and reliable."""
    t = re.sub(r"```.*?```", " ", text, flags=re.S)          # code blocks
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)           # [label](url) -> label
    t = re.sub(r"[*_#`>|]", " ", t)                          # markdown symbols
    t = re.sub(r"^\s*[-•]\s+", "", t, flags=re.M)            # bullet dashes
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_chars]


def _vget(v, key: str) -> str:
    """edge-tts voices are dicts in some versions, objects in others."""
    return v.get(key, "") if isinstance(v, dict) else getattr(v, key, "")


# ---------- engine 1: gTTS (raises on failure -> never cached) ----------
@st.cache_data(show_spinner=False)
def _gtts_bytes(text: str, lang: str) -> bytes:
    from gtts import gTTS
    from gtts.lang import tts_langs
    if lang not in tts_langs():
        raise ValueError(f"gTTS has no voice for '{lang}'")
    buf = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


# ---------- engine 2: edge-tts (Microsoft neural voices) ----------
@st.cache_data(show_spinner=False, ttl=3600)
def _edge_voices() -> list[dict]:
    """Fetch the Microsoft voice list. Raises on failure (never cached)."""
    import edge_tts
    voices = asyncio.run(edge_tts.list_voices())
    return [v if isinstance(v, dict) else vars(v) for v in voices]


def _edge_voice_for(lang: str) -> str | None:
    """Pick a Microsoft voice for this language (Indian locale preferred).
    NOT cached — only the voice LIST is cached, so failures retry."""
    try:
        voices = _edge_voices()
    except Exception as exc:
        print("edge-tts voice lookup failed:", exc)
        return None
    prefix = {"or": "or-", "hi": "hi-in", "en": "en-in"}.get(lang, f"{lang}-")
    candidates = [v for v in voices
                  if str(v.get("Locale", "")).lower().startswith(prefix)]
    if not candidates:
        print(f"edge-tts: no '{lang}' voice found in Microsoft list")
        return None
    for v in candidates:                       # prefer a female voice if present
        if str(v.get("Gender", "")).lower() == "female":
            return v.get("ShortName")
    return candidates[0].get("ShortName")

@st.cache_data(show_spinner=False)
def _edge_bytes(text: str, voice: str) -> bytes:
    import edge_tts

    async def run() -> bytes:
        buf = io.BytesIO()
        com = edge_tts.Communicate(text, voice)
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    return asyncio.run(run())


def synthesize(text: str, lang: str) -> bytes | None:
    """MP3 bytes, or None when no engine can speak this (UI shows a note)."""
    text = clean_for_speech(text)
    if not text:
        return None

    engines = ["edge"] if lang == "or" else ["gtts", "edge"]
    for engine in engines:
        try:
            if engine == "gtts":
                return _gtts_bytes(text, lang)
            voice = _edge_voice_for(lang)
            if voice:
                return _edge_bytes(text, voice)
            print(f"edge-tts: no voice for '{lang}'")
        except Exception as exc:
            print(f"TTS [{engine}/{lang}] failed (not cached):", exc)
    return None
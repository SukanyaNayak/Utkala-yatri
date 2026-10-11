"""Thin Gemini wrapper — the ONLY file that talks to Google GenAI.

Works under BOTH Streamlit and FastAPI (via services.cache_compat):
Streamlit mode uses st.secrets/st.cache; backend mode uses env/lru_cache
and logs instead of toasting.

Model name comes from GEMINI_MODEL (.env / Streamlit secrets) — never
hard-coded, so models can be swapped without touching code.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from services.cache_compat import cache_resource

logger = logging.getLogger("utkalayatri")

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:                                   # Streamlit-only touchpoints (secrets/toast)
    import streamlit as st
except Exception:                      # backend mode: no Streamlit runtime
    st = None

_SECRETS_FILE = Path(".streamlit/secrets.toml")
DEFAULT_MODEL = "gemini-flash-latest"   # alias — survives model retirement


def _get_setting(key: str, fallback: str = "") -> str:
    """Streamlit secrets (Cloud) first, then environment (.env)."""
    if st is not None and _SECRETS_FILE.exists():
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    return os.getenv(key, fallback)


def model_name() -> str:
    return _get_setting("GEMINI_MODEL", DEFAULT_MODEL)


_CLIENT_ERROR: str | None = None


@cache_resource
def _client():
    global _CLIENT_ERROR
    _CLIENT_ERROR = None
    api_key = _get_setting("GEMINI_API_KEY")
    if not api_key:
        _CLIENT_ERROR = "GEMINI_API_KEY not found — add it to .env."
        return None
    try:
        from google import genai
    except ImportError:
        _CLIENT_ERROR = ("Python package 'google-genai' is not installed — "
                         "run: pip install google-genai")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        _CLIENT_ERROR = f"Gemini client init failed: {exc}"
        return None


def is_configured() -> bool:
    return _client() is not None


def config_error() -> str | None:
    """Reason Gemini is unavailable (None = everything fine)."""
    _client()  # ensure an attempt was made
    return _CLIENT_ERROR


# Tried in order when the primary model fails with 5xx errors
FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash",
                   "gemini-flash-lite-latest"]


def _generate(client, model: str, prompt: str, config: dict) -> str:
    resp = client.models.generate_content(
        model=model, contents=prompt, config=config)
    return (resp.text or "").strip()


def _model_chain() -> list[str]:
    """Primary model first, then fallbacks (de-duplicated)."""
    return [model_name()] + [m for m in FALLBACK_MODELS if m != model_name()]


def ask(prompt: str, system: str | None = None,
        temperature: float = 0.7, retries: int = 2) -> str:
    """Free-form generation with retry + model fallback. "" on failure."""
    client = _client()
    if client is None:
        return ""
    config: dict = {"temperature": temperature}
    if system:
        config["system_instruction"] = system

    last_err: Exception | None = None
    for model in _model_chain():
        for attempt in range(retries + 1):
            try:
                return _generate(client, model, prompt, config)
            except Exception as exc:
                last_err = exc
                transient = ("503" in str(exc) or "429" in str(exc)
                             or "UNAVAILABLE" in str(exc))
                if transient and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))   # 1.5s, then 3s
                    continue
                break   # non-transient, or retries exhausted -> next model

    logger.warning("Gemini unavailable — empty reply (last error: %s)",
                   str(last_err)[:300])
    return ""


def ask_json(prompt: str, system: str | None = None,
             temperature: float = 0.4, retries: int = 2) -> Optional[dict]:
    """Forced-JSON generation with retry + model fallback. None on failure."""
    client = _client()
    if client is None:
        return None
    config: dict = {"temperature": temperature,
                    "response_mime_type": "application/json"}
    if system:
        config["system_instruction"] = system

    last_err: Exception | None = None
    for model in _model_chain():
        for attempt in range(retries + 1):
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt, config=config)
                return json.loads(resp.text)
            except Exception as exc:
                last_err = exc
                transient = ("503" in str(exc) or "429" in str(exc)
                             or "UNAVAILABLE" in str(exc))
                if transient and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break

    logger.warning("Gemini JSON request failed (last error: %s)",
                   str(last_err)[:300])
    return None


def ask_with_audio(audio_bytes: bytes, mime_type: str = "audio/wav",
                   prompt: str = "Transcribe the spoken words exactly.",
                   system: str | None = None, retries: int = 2) -> str:
    """Send audio + prompt to the multimodal model. "" on failure."""
    client = _client()
    if client is None or not audio_bytes:
        return ""
    config: dict = {"temperature": 0.0}
    if system:
        config["system_instruction"] = system
    try:
        from google.genai import types
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    except Exception as exc:
        logger.warning("Audio part error: %s", exc)
        return ""

    last_err: Exception | None = None
    for model in _model_chain():
        for attempt in range(retries + 1):
            try:
                resp = client.models.generate_content(
                    model=model, contents=[prompt, audio_part], config=config)
                return (resp.text or "").strip()
            except Exception as exc:
                last_err = exc
                transient = ("503" in str(exc) or "429" in str(exc)
                             or "UNAVAILABLE" in str(exc))
                if transient and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
    logger.warning("Gemini audio error (all attempts failed): %s",
                   str(last_err)[:300])
    return ""


def _extract_json(raw: str) -> dict | None:
    """Best-effort JSON extraction from a model reply (handles ``` fences)."""
    if not raw:
        return None
    import re
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def ask_with_image(image_bytes: bytes, mime_type: str, prompt: str,
                   system: str | None = None, temperature: float = 0.2,
                   retries: int = 2) -> str:
    """Send an image + prompt to the multimodal model. "" on failure."""
    client = _client()
    if client is None or not image_bytes:
        return ""
    config: dict = {"temperature": temperature}
    if system:
        config["system_instruction"] = system
    try:
        from google.genai import types
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    except Exception as exc:
        logger.warning("Image part error: %s", exc)
        return ""

    last_err: Exception | None = None
    for model in _model_chain():
        for attempt in range(retries + 1):
            try:
                resp = client.models.generate_content(
                    model=model, contents=[prompt, part], config=config)
                return (resp.text or "").strip()
            except Exception as exc:
                last_err = exc
                transient = ("503" in str(exc) or "429" in str(exc)
                             or "UNAVAILABLE" in str(exc))
                if transient and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
    logger.warning("Gemini image error (all attempts failed): %s",
                   str(last_err)[:300])
    return ""


LANG_INSTRUCTIONS = {
    "en": "Reply only in English.",
    "hi": "Reply only in Hindi, using Devanagari script.",
    "or": ("Reply only in Odia, using Odia script (ଓଡ଼ିଆ). "
           "Do not switch to Hindi, Bengali, or English."),
    "auto": ("Reply in the same language and script the user wrote in — "
             "English, Hindi (Devanagari), or Odia (Odia script)."),
}


def yatri_system_prompt(lang: str = "auto") -> str:
    """System instruction for the Yatri AI chat assistant, language-aware."""
    base = (
        "You are Yatri AI, a friendly travel assistant for Odisha, India. "
        "Answer questions about places, culture, food, festivals, and travel "
        "logistics in Odisha using the information provided to you. "
    )
    return base + LANG_INSTRUCTIONS.get(lang, LANG_INSTRUCTIONS["auto"])
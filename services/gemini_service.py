"""Thin Gemini wrapper — the ONLY file that talks to Google GenAI.

Public API:
    is_configured()       -> bool  (GEMINI_API_KEY present?)
    ask(prompt, ...)      -> str   (never raises; "" on failure)
    ask_json(prompt, ...) -> dict | None  (JSON-mode response)

Model name comes from GEMINI_MODEL (.env / Streamlit secrets) — never
hard-coded here, so you can swap models without touching code.

Migration note: st.toast is the only Streamlit touchpoint; replace with
logging when this moves into FastAPI.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

_SECRETS_FILE = Path(".streamlit/secrets.toml")
DEFAULT_MODEL = "gemini-2.0-flash"   # fallback only — set GEMINI_MODEL in .env


def _get_setting(key: str, fallback: str = "") -> str:
    """Streamlit secrets (Cloud) first, then environment (.env)."""
    if _SECRETS_FILE.exists():
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    return os.getenv(key, fallback)


def model_name() -> str:
    return _get_setting("GEMINI_MODEL", DEFAULT_MODEL)


_CLIENT_ERROR: str | None = None


@st.cache_resource(show_spinner=False)
def _client():
    global _CLIENT_ERROR
    _CLIENT_ERROR = None
    api_key = _get_setting("GEMINI_API_KEY")
    if not api_key:
        _CLIENT_ERROR = ("GEMINI_API_KEY not found — add it to .env "
                         "and restart Streamlit.")
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
FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest"]


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

    st.toast("Gemini unavailable — no AI note for now.", icon="⚠️")
    print("Gemini error (all attempts failed):", last_err)
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

    st.toast("Gemini JSON request failed — see terminal.", icon="⚠️")
    print("Gemini JSON error (all attempts failed):", last_err)
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
        print("Audio part error:", exc)
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
    print("Gemini audio error (all attempts failed):", last_err)
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
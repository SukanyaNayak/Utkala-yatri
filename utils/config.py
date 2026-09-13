"""
Central configuration for UtkalaYatri.

Loads environment variables (via python-dotenv) and exposes them as
constants so the rest of the app never touches os.environ directly.
Keeping this separate from the UI also means the same config module
can be reused as-is by a future FastAPI backend.
"""

import os

from dotenv import load_dotenv

# Load variables from a local .env file if present (no-op in production
# environments where env vars are already set, e.g. Streamlit Cloud secrets).
load_dotenv()


# --------------------------------------------------------------------------
# App metadata
# --------------------------------------------------------------------------
APP_NAME = "UtkalaYatri"
APP_TAGLINE = "AI Travel Companion for Odisha"
APP_ICON = "🧭"


# --------------------------------------------------------------------------
# Environment / secrets
# --------------------------------------------------------------------------
# NOTE: values are intentionally left as None/empty when unset rather than
# raising errors here — Week 1 scaffold has no features that require them
# yet. Services that need a given key should validate it themselves before
# use (e.g. mongodb_service.py checks MONGODB_URI before connecting).

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "utkalayatri")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")

# Generic app environment flag: "development" | "production"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV != "production"

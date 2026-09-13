"""
MongoDB Atlas service layer.

This module is the ONLY place in the app that should import pymongo.
Keeping all database access here (rather than scattered across
Streamlit pages) makes it trivial to lift this file into a future
FastAPI backend with little change.

Public API:
    connect_db()        -> cached MongoClient (or None if unreachable)
    get_collection(name) -> a pymongo Collection from the app database
    test_connection()   -> fresh (bool, message) health check, safe to
                            call repeatedly (e.g. from the sidebar)

Credential resolution order (Streamlit secrets compatibility):
    1. st.secrets["MONGODB_URI"] / st.secrets["MONGODB_DB_NAME"]
       (used automatically on Streamlit Cloud via .streamlit/secrets.toml)
    2. Environment variables loaded from .env by utils/config.py
       (used for local development)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from utils.config import MONGODB_URI, MONGODB_DB_NAME

# Streamlit renders a visible "No secrets found" warning in the app the
# moment anything touches st.secrets and no secrets.toml exists on disk —
# this happens even inside a try/except, since Streamlit draws it as a
# side effect before the exception reaches our code. So we only touch
# st.secrets at all when a secrets.toml file actually exists locally
# (e.g. on Streamlit Cloud, or if you add one yourself).
_SECRETS_FILE = Path(".streamlit/secrets.toml")


def _resolve_credential(env_value: str, secret_key: str) -> str:
    """
    Resolve a config value, preferring Streamlit secrets when a
    secrets.toml file is actually present (e.g. on Streamlit Cloud),
    and falling back to the value already loaded from .env by
    utils/config.py (local development — the common case).
    """
    if _SECRETS_FILE.exists():
        try:
            if secret_key in st.secrets:
                return st.secrets[secret_key]
        except Exception:
            pass
    return env_value

def _get_uri() -> str:
    return _resolve_credential(MONGODB_URI, "MONGODB_URI")


def _get_db_name() -> str:
    return _resolve_credential(MONGODB_DB_NAME, "MONGODB_DB_NAME") or "utkalayatri"


@st.cache_resource(show_spinner=False)
def connect_db() -> Optional[MongoClient]:
    """
    Create (and cache) a MongoClient for the app's lifetime.

    Streamlit's cache_resource keeps this connection alive across
    reruns and user sessions instead of reconnecting on every script
    run. Returns None (never raises) if the URI is missing or the
    connection/ping fails, so callers can handle the failure
    gracefully in the UI.
    """
    uri = _get_uri()
    if not uri:
        return None

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")  # fail fast if unreachable
        return client
    except PyMongoError:
        return None


def get_collection(collection_name: str) -> Optional[Collection]:
    """
    Return a pymongo Collection handle from the app database.

    Returns None if the database is not currently reachable — callers
    should check for None before using the result (e.g. skip a query
    and show a friendly message instead of crashing the page).
    """
    client = connect_db()
    if client is None:
        return None
    db = client[_get_db_name()]
    return db[collection_name]


def test_connection() -> tuple[bool, str]:
    """
    Run a fresh connectivity check (not cached) and return a
    human-readable status message.

    Safe to call on every page load / sidebar render — it reuses the
    cached client but re-pings each time, so a status indicator
    reflects the *current* connection state rather than a stale one.
    """
    uri = _get_uri()
    if not uri:
        return False, (
            "MONGODB_URI is not set. Copy .env.example to .env (local) or "
            "add it to Streamlit secrets (deployed) and fill in your "
            "MongoDB Atlas connection string."
        )

    client = connect_db()
    if client is None:
        return False, "Could not connect to MongoDB Atlas. Check your URI, network access list, and credentials."

    try:
        client.admin.command("ping")
        return True, f"Connected to MongoDB Atlas (db: {_get_db_name()})"
    except PyMongoError as exc:
        return False, f"MongoDB connection lost: {exc}"

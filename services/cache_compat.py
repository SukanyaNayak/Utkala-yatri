"""Cache decorators that work under BOTH Streamlit and plain FastAPI.

Streamlit mode (default): delegates to st.cache_resource / st.cache_data.
Backend mode   (UTKALAYATRI_BACKEND=1, set by backend/main.py):
                plain functools.lru_cache — no Streamlit dependency.
"""
from __future__ import annotations

import functools
import os

if os.getenv("UTKALAYATRI_BACKEND") == "1":
    def cache_resource(fn):
        return functools.lru_cache(maxsize=1)(fn)

    def cache_data(fn=None, *, ttl=None):
        # lru_cache has no TTL; route/tts results are stable enough for MVP
        def deco(f):
            return functools.lru_cache(maxsize=256)(f)
        return deco(fn) if fn else deco
else:
    import streamlit as st

    def cache_resource(fn):
        return st.cache_resource(show_spinner=False)(fn)

    def cache_data(fn=None, *, ttl=None):
        if fn is None:
            return lambda f: st.cache_data(show_spinner=False, ttl=ttl)(f)
        return st.cache_data(show_spinner=False)(fn)
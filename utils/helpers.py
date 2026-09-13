"""
Reusable UI helper functions shared across Streamlit pages.

These helpers only touch st.session_state and st.markdown/CSS — no
business logic. Anything that talks to MongoDB, Gemini, or maps
belongs in services/, not here.
"""

from __future__ import annotations

import streamlit as st

from utils.config import APP_NAME
from services.mongodb_service import test_connection


def init_session_state() -> None:
    """
    Initialize all session_state keys used across the app.

    Call this once, early, from app.py (and it is safe to call again
    from any page — keys are only set if they don't already exist).
    Centralizing this avoids KeyError surprises when new pages are
    added in later weeks.
    """
    defaults = {
        "user_name": "",
        "chat_history": [],          # list of {"role": ..., "content": ...}
        "current_itinerary": None,   # will hold generated itinerary data later
        "selected_destinations": [], # places the user has picked/saved
        "map_center": [20.2961, 85.8245],  # default: Bhubaneswar, Odisha
        "page_visits": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.session_state["page_visits"] += 1


def load_custom_css() -> None:
    """Inject basic custom CSS for a consistent, branded look."""
    st.markdown(
        """
        <style>
        /* Tighten default top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Simple card-like look for st.info / st.expander headers */
        div[data-testid="stExpander"] {
            border-radius: 10px;
        }

        /* Footer styling */
        .uy-footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(128, 128, 128, 0.3);
            text-align: center;
            font-size: 0.85rem;
            opacity: 0.7;
        }

        /* Sidebar heading spacing */
        section[data-testid="stSidebar"] h2 {
            margin-bottom: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=30, show_spinner=False)
def _cached_connection_status() -> tuple[bool, str]:
    """
    Wraps mongodb_service.test_connection() with a short TTL cache so
    the sidebar doesn't ping Atlas on every single widget interaction —
    only at most once every 30 seconds.
    """
    return test_connection()


def render_db_status(sidebar: bool = True) -> None:
    """
    Render a small MongoDB Atlas connection status indicator.

    Pass sidebar=False to render inline in the main page body instead
    of the sidebar.
    """
    target = st.sidebar if sidebar else st

    connected, message = _cached_connection_status()

    if connected:
        target.success("🟢 MongoDB: Connected", icon="✅")
    else:
        target.error("🔴 MongoDB: Not connected", icon="⚠️")

    with target.expander("Connection details", expanded=False):
        st.caption(message)


def render_footer() -> None:
    """Render a simple footer at the bottom of a page."""
    st.markdown(
        f"""
        <div class="uy-footer">
            Built with ❤️ for Odisha · {APP_NAME} · Hackathon MVP (Week 1 scaffold)
        </div>
        """,
        unsafe_allow_html=True,
    )

"""
UtkalaYatri — AI Travel Companion for Odisha
Main Streamlit application entry point.

This file is intentionally thin: it only handles page config,
navigation, session_state bootstrap, and layout/CSS. All business
logic lives in services/ and utils/ so it can be reused later when
this project migrates to a React + FastAPI stack.
"""

import streamlit as st

from utils.config import APP_NAME, APP_TAGLINE, APP_ICON
from utils.helpers import init_session_state, load_custom_css, render_footer, render_db_status


# --------------------------------------------------------------------------
# Page configuration (must be the first Streamlit command executed)
# --------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Session state bootstrap
# --------------------------------------------------------------------------
init_session_state()

# --------------------------------------------------------------------------
# Custom CSS
# --------------------------------------------------------------------------
load_custom_css()

# --------------------------------------------------------------------------
# Sidebar navigation
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.divider()

    st.markdown("### Navigation")
    st.page_link("app.py", label="Home", icon="🏠")

    # NOTE: As pages/ fills up in later weeks (e.g. pages/1_Itinerary.py,
    # pages/2_Chat_Assistant.py, pages/3_Map_Explorer.py), Streamlit's
    # multipage app system will auto-detect them and this sidebar section
    # can either rely on the default page list or add explicit st.page_link
    # entries here.

    st.divider()
    st.markdown("### Status")
    st.info("MVP scaffold — Week 2", icon="🚧")
    render_db_status(sidebar=True)

# --------------------------------------------------------------------------
# Home page content
# --------------------------------------------------------------------------
st.title(f"{APP_ICON} {APP_NAME}")
st.subheader(APP_TAGLINE)

st.markdown(
    """
Welcome to **UtkalaYatri**, your upcoming AI-powered travel companion for
exploring **Odisha** — its temples, beaches, wildlife sanctuaries, tribal
heritage, and hidden gems.

This is currently a **project scaffold** built for a hackathon MVP. Core
features are being added incrementally over the following weeks.
"""
)

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🗺️ Smart Itineraries")
    st.write("Personalized day-by-day travel plans across Odisha (coming soon).")
with col2:
    st.markdown("### 💬 AI Travel Chat")
    st.write("Ask questions about places, culture, food, and travel logistics (coming soon).")
with col3:
    st.markdown("### 📍 Interactive Maps")
    st.write("Explore destinations visually with route planning (coming soon).")

st.divider()

with st.expander("ℹ️ About this build"):
    st.write(
        "This scaffold sets up the folder structure, navigation, "
        "session state, and styling for UtkalaYatri. Business logic is "
        "kept separate from the UI layer (in `services/` and `utils/`) "
        "to make a future migration to React + FastAPI straightforward."
    )

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
render_footer()

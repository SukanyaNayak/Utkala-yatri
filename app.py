"""UtkalaYatri — app entry: config, CSS, global language, navigation, DB status.

Thin by design: all business logic lives in services/ and utils/.
"""
import streamlit as st

from utils.config import APP_NAME, APP_ICON
from utils.helpers import init_session_state, load_custom_css, render_db_status
from utils.i18n import t, language_picker

# Page configuration (must be the first Streamlit command)
st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide",
                   initial_sidebar_state="expanded")

init_session_state()
load_custom_css()
language_picker()          # THE single global language control (sidebar)

# Navigation — labels are live t() calls, so the sidebar relabels
# instantly when the language changes. Filenames no longer matter.
PAGE_DEFS = [
    ("pages/0_Home.py",            "nav_home",      "🏠", True),
    ("pages/1_Explore_Places.py",  "nav_explore",   "🗺️", False),
    ("pages/2_AI_Travel_Chat.py",  "nav_chat",      "🤖", False),
    ("pages/3_Trip_Planner.py",    "nav_planner",   "📅", False),
    ("pages/4_Festivals.py",       "nav_festivals", "🎪", False),
    ("pages/5_Nearby_Hotels.py",   "nav_hotels",    "🏨", False),
    ("pages/6_Emergency.py",       "nav_emergency", "🚨", False),
    ("pages/7_Hidden_Gems.py",     "nav_gems",      "💎", False),
    ("pages/8_Landmark_Scan.py",   "nav_landmark",  "📷", False),
]
pages = [st.Page(path, title=t(key), icon=icon, default=dflt)
         for path, key, icon, dflt in PAGE_DEFS]

with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.divider()
    render_db_status(sidebar=True)

st.navigation(pages).run()
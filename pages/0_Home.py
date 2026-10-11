"""UtkalaYatri home page."""
import streamlit as st
from utils.helpers import render_footer
from utils.i18n import t

st.title(f"🛕 UtkalaYatri")
st.subheader(t("app_tagline"))

st.markdown("""
Welcome to **UtkalaYatri**, your AI-powered travel companion for **Odisha** —
its temples, beaches, wildlife sanctuaries, tribal heritage, and hidden gems.
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"### {t('nav_explore')}")
    st.write("231 places, photos, click-to-select map and AI insights.")
with col2:
    st.markdown(f"### {t('nav_chat')}")
    st.write("Ask anything — type or 🎙️ speak; hear the reply in English or Hindi.")
with col3:
    st.markdown(f"### {t('nav_planner')}")
    st.write("Multi-stop plans with real road routing, costs and festival alerts.")

st.divider()
st.caption("Data: OpenStreetMap contributors · Wikipedia/Wikimedia Commons "
           "contributors (CC BY-SA) · AI-assisted content is provenance-tagged.")
render_footer()
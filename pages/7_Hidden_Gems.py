"""Hidden Gems — the lesser-known Odisha: offbeat places only."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from services import place_service
from services.translate_service import localized_text
from utils.i18n import t, tf, language_picker, content_lang



ss = st.session_state
GEM_TAGS = {"hidden-gem", "hidden_gem", "offbeat", "lesser-known", "gem"}

st.title(t("gems_title"))
st.caption(t("gems_caption"))

places = place_service.get_all_places()


def is_gem(p: dict) -> bool:
    if p.get("is_hidden_gem"):
        return True
    tags = {str(tag).lower() for tag in p.get("tags", [])}
    return bool(tags & GEM_TAGS)


gems = [p for p in places if is_gem(p)]
# a gem without a story isn't a gem card — drop it (quality over quantity)
gems = [p for p in gems if (p.get("description") or "").strip()]
# curated stories first — they're the real gems
gems.sort(key=lambda p: 0 if p.get("source") == "curated" else 1)
st.markdown(f"**{tf('gems_count', n=len(gems))}**")
query = st.text_input(t("filter_gems"), placeholder=t("gems_search_ph"))

if query:
    q = query.lower()
    gems = [p for p in gems if q in " ".join(
        [p.get("name", ""), p.get("description", ""), p.get("city", ""),
         " ".join(p.get("tags", []))]).lower()]

# ---- map ----
m = folium.Map(location=[20.1, 84.5], zoom_start=7, tiles="OpenStreetMap")
for p in gems:
    folium.Marker([p["lat"], p["lon"]],
                  tooltip=f"💎 {p['name']}",
                  popup=folium.Popup(
                      f"<div style='width:210px'><b>{p['name']}</b><br>"
                      f"{(p.get('description') or '')[:140]}</div>",
                      max_width=240),
                  icon=folium.DivIcon(html="<div style='font-size:20px'>💎</div>")
                  ).add_to(m)
st_folium(m, height=380, use_container_width=True)

# ---- cards, 2-wide with more story room ----
for i in range(0, len(gems), 2):
    row = st.columns(2)
    for col, p in zip(row, gems[i:i + 2]):
        with col, st.container(border=True):
            st.markdown(f"### 💎 {p['name']}")
            st.markdown(place_service.image_html(p), unsafe_allow_html=True)
            st.caption(f"{p.get('city') or p.get('district') or 'Odisha'} · "
                       f"{p.get('category', '')}")
            if p.get("description"):
                text, was_translated = localized_text(p["description"],
                                                      ss.get("lang", "en"))
                st.write(text)
                if was_translated:
                    st.caption("🌐 AI-translated")
            if p.get("insider_tip"):
                st.info(f"🗝️ {p['insider_tip']}")
            if p.get("best_time"):
                st.info(f"🗓️ Best time: **{p['best_time']}**")
            if p.get("tags"):
                st.caption(" ".join(f"`#{tag}`" for tag in p["tags"][:6]))
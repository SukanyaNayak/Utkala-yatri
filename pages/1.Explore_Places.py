"""Place Explorer - search, interactive map, click-to-select, details view."""
from services.translate_service import localized_text
import folium
import streamlit as st
from streamlit_folium import st_folium

from services import gemini_service, place_service
from utils.i18n import t, language_picker

st.set_page_config(
    page_title="Explore Places - UtkalaYatri",
    page_icon="🗺️",
    layout="wide",
)

language_picker()   # must come AFTER st.set_page_config

ODISHA_CENTER = [20.35, 85.30]
PAGE_SIZE = 24

ss = st.session_state
ss.setdefault("selected_place_id", None)
ss.setdefault("_last_click", None)


def chip(text: str, color: str) -> str:
    return (f"<span style='background:{color}22;color:{color};"
            f"border:1px solid {color}55;border-radius:12px;padding:2px 10px;"
            f"font-size:12px;margin:0 4px 4px 0;display:inline-block'>{text}</span>")


def render_details(place: dict) -> None:
    emoji, color = place_service.category_meta(place.get("category"))
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"### {emoji} {place['name']}")
            st.caption(
                f"{place.get('city') or place.get('district') or 'Odisha'} - "
                f"{place.get('category', 'other')}"
            )
            if place.get("best_time"):
                st.info(f"🗓️ {t('best_time')}: **{place['best_time']}**")
            if place.get("insider_tip"):
                st.info(f"🗝️ **{t('insider_tip')}:** {place['insider_tip']}")
            if place.get("description"):
                text, was_translated = localized_text(
                    place["description"], ss.get("lang", "en"))
                st.write(text)
                if was_translated:
                    st.caption("🌐 AI-translated")
            if place.get("tags"):
                clean_tags = [
                    tag for tag in place.get("tags", [])
                    if tag not in ("curated", "osm", "wikidata")
                ]
                st.markdown(
                    "".join(chip(f"#{tag}", color) for tag in clean_tags[:8]),
                    unsafe_allow_html=True,
                )
            if place.get("website"):
                st.markdown(f"[Open website]({place['website']})")

            # --- AI Insights ---
            ai_key = f"ai_{place['place_id']}"
            if st.button(t("ai_insights"), type="primary"):
                if not gemini_service.is_configured():
                    st.warning(gemini_service.config_error()
                               or "Gemini unavailable.")
                else:
                    with st.spinner("UtkalaYatri AI is thinking..."):
                        facts = "\n".join(
                            f"- {k}: {place[k]}" for k in
                            ("name", "city", "district", "category",
                             "description", "best_time") if place.get(k))
                        ss[ai_key] = gemini_service.ask(
                            f"Place facts:\n{facts}\n\nWrite a short guide note:\n"
                            "1) a vivid 2-sentence intro,\n"
                            "2) two practical tips as bullets.\n"
                            "Under 80 words total. Use ONLY the facts above.",
                            system="You are UtkalaYatri, a friendly Odisha travel "
                                   "guide. Accurate and concise.")
            if ss.get(ai_key):
                st.success(ss[ai_key])

        with right:
            img = place.get("image")
            shown = False
            if img:
                try:
                    st.image(img, use_container_width=True)
                    shown = True
                except Exception:
                    pass
            if not shown:
                st.markdown(
                    f"<div style='text-align:center;font-size:84px;"
                    f"padding:20px'>{emoji}</div>",
                    unsafe_allow_html=True,
                )
            st.metric("Coordinates", f"{place['lat']:.4f}, {place['lon']:.4f}")


st.title(t("explore_title"))
all_places = place_service.get_all_places()
st.caption(
    f"{len(all_places)} places across Odisha - search, click the map, or open a card."
)

c1, c2 = st.columns([2, 1])
query = c1.text_input(
    t("search"),
    placeholder="temple, beach, Chilika, waterfall...",
    label_visibility="collapsed",
)
cats = ["All"] + place_service.get_categories()
counts = {
    category: sum(1 for place in all_places
                  if place.get("category", "other") == category)
    for category in cats
}
category = c2.selectbox(
    t("category"),
    cats,
    format_func=lambda value: (
        f"All ({len(all_places)})" if value == "All"
        else f"{value} ({counts.get(value, 0)})"
    ),
    label_visibility="collapsed",
)

places = place_service.search_places(query=query, category=category)
selected = place_service.get_place(ss["selected_place_id"] or "")
if selected:
    render_details(selected)
    st.divider()

map_view = folium.Map(location=ODISHA_CENTER, zoom_start=7, tiles="OpenStreetMap")
for place in places:
    emoji, color = place_service.category_meta(place.get("category"))
    is_selected = place["place_id"] == ss["selected_place_id"]
    description = place.get("description") or ""
    popup_html = (
        f"<div style='width:220px'><b>{emoji} {place['name']}</b><br>"
        f"<span style='color:#666'>{place.get('city', '')} - "
        f"{place.get('category', '')}</span><br>"
        f"{description[:120]}{'...' if len(description) > 120 else ''}</div>"
    )
    folium.CircleMarker(
        [place["lat"], place["lon"]],
        radius=10 if is_selected else 6,
        color=color,
        fill=True,
        fill_opacity=0.9,
        tooltip=f"{emoji} {place['name']}",
        popup=folium.Popup(popup_html, max_width=240),
    ).add_to(map_view)

map_output = st_folium(map_view, height=440, use_container_width=True)
clicked = map_output.get("last_clicked")
if clicked and clicked != ss["_last_click"]:
    ss["_last_click"] = clicked
    nearby = place_service.get_nearby_places(
        clicked["lat"], clicked["lng"], radius_km=5, limit=1
    )
    if nearby:
        ss["selected_place_id"] = nearby[0]["place_id"]
        st.rerun()

st.subheader(f"{t('explore_title')} - {len(places)} {t('results')}")
if not places:
    st.info("No places match - try a different search or category.")

show_all = st.toggle(
    f"Show all {len(places)} results",
    value=bool(ss.get("show_all")),
    disabled=len(places) <= PAGE_SIZE,
)
ss["show_all"] = show_all
shown = places if show_all else places[:PAGE_SIZE]

cols = st.columns(3)
for index, place in enumerate(shown):
    emoji, _ = place_service.category_meta(place.get("category"))
    with cols[index % 3], st.container(border=True):
        st.markdown(f"**{emoji} {place['name'][:42]}**")
        st.caption(
            f"{place.get('city') or place.get('district') or 'Odisha'} - "
            f"{place.get('category', 'other')}"
        )
        description = place.get("description") or ""
        if description:
            if len(shown) <= 30:                     # safe: ≤30 Gemini calls, cached
                text, was_translated = localized_text(description, ss.get("lang", "en"))
                st.write(text[:110] + ("..." if len(text) > 110 else ""))
                if was_translated:
                    st.caption("🌐")
            else:                                    # "Show all" mode: keep English
                st.write(description[:110] + ("..." if len(description) > 110 else ""))
        if st.button(t("view_details"), key=f"view_{place['place_id']}"):
            ss["selected_place_id"] = place["place_id"]
            st.rerun()
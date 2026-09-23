"""Nearby Hotels — pick a place, see hotels ranked by distance on map + cards."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from services import hotel_service, place_service
from utils.i18n import t, language_picker

st.set_page_config(page_title="Nearby Hotels · UtkalaYatri", page_icon="🏨",
                   layout="wide")
language_picker()

st.title(t("hotels_title"))
st.caption("Real hotels across Odisha, ranked by distance from anywhere you're "
           "exploring.")

places = place_service.get_all_places()
curated = [p for p in places if p.get("source") == "curated"] or places
label = lambda p: f"{p['name']} ({p.get('city', '')})"

c1, c2, c3 = st.columns([2, 1, 1])
base = c1.selectbox(t("hotels_near"), curated, format_func=label)
radius = c2.slider(t("radius"), 5, 100, 25, step=5)
band = c3.selectbox("Price band", ["All", "budget", "mid", "premium"])

hotels = hotel_service.get_hotels_near(base["lat"], base["lon"],
                                       radius_km=radius, limit=40)
if band != "All":
    hotels = [h for h in hotels
              if hotel_service.price_band(
                  h.get("price") or h.get("price_range_inr") or "") == band]

st.success(f"📍 **{base['name']}** — {len(hotels)} hotel(s) within {radius} km")

# ---- map ----
m = folium.Map(location=[base["lat"], base["lon"]], zoom_start=10)
folium.Marker([base["lat"], base["lon"]], tooltip=f"📍 {base['name']}",
              icon=folium.Icon(color="blue", icon="camera")).add_to(m)
for h in hotels:
    if h.get("lat") is None:
        continue
    folium.CircleMarker([h["lat"], h["lon"]], radius=6, color="#c0392b",
                        fill=True, fill_opacity=0.9,
                        tooltip=f"🏨 {h['name']} · {h['distance_km']} km",
                        popup=folium.Popup(
                            f"<div style='width:200px'><b>{h['name']}</b><br>"
                            f"{h.get('price') or h.get('price_range_inr') or ''}"
                            f"{' · ⭐' + str(h['rating']) if h.get('rating') else ''}"
                            f"</div>", max_width=220)).add_to(m)
st_folium(m, height=380, use_container_width=True)

# ---- cards ----
cols = st.columns(3)
for i, h in enumerate(hotels[:24]):
    with cols[i % 3], st.container(border=True):
        price = h.get("price") or h.get("price_range_inr") or "Price N/A"
        st.markdown(f"**🏨 {h['name'][:40]}**")
        if h.get("image"):
            try:
                st.image(h["image"], use_container_width=True)
            except Exception:
                pass
        st.caption(f"{h.get('city') or 'Odisha'} · {h['distance_km']} km from "
                   f"{base['name'][:20]}")
        st.write(f"💰 {price}"
                 + (f"  ·  ⭐ {h['rating']}" if h.get("rating") else ""))
        notes = h.get("description") or h.get("notes")
        if notes:
            st.write(notes[:100] + ("…" if len(notes) > 100 else ""))
        if h.get("tags"):
            st.caption(" ".join(f"`#{tag}`" for tag in h["tags"][:4]))

if not hotels:
    st.info("No hotels in this radius — widen the search or pick another place.")
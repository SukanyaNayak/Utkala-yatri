"""Emergency Services — helplines + nearest facilities, always one tap away."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from services import hotel_service, place_service

st.set_page_config(page_title="Emergency · UtkalaYatri", page_icon="🚨",
                   layout="wide")

st.title("🚨 Emergency Services")
st.markdown("### National helplines — work anywhere in India")
hc = st.columns(4)
helplines = [("112", "🆘 All-in-one emergency"), ("100", "👮 Police"),
             ("108", "🚑 Ambulance"), ("101", "🔥 Fire")]
for col, (num, lab) in zip(hc, helplines):
    col.markdown(f"[**📞 {num}**](tel:{num})  \n{lab}")

st.divider()
st.markdown("### Facilities near you")
places = place_service.get_all_places()
curated = [p for p in places if p.get("source") == "curated"] or places
base = st.selectbox("Show facilities near", curated,
                    format_func=lambda p: f"{p['name']} ({p.get('city', '')})")

nearby = hotel_service.get_emergency_near(base["lat"], base["lon"])
TYPE_STYLE = {"police": ("👮", "#3498db"), "hospital": ("🏥", "#e74c3c"),
              "fire": ("🔥", "#e67e22"), "pharmacy": ("💊", "#27ae60")}

if nearby:
    m = folium.Map(location=[base["lat"], base["lon"]], zoom_start=11)
    folium.Marker([base["lat"], base["lon"]], tooltip=f"📍 {base['name']}",
                  icon=folium.Icon(color="blue")).add_to(m)
    cols = st.columns(3)
    for i, e in enumerate(nearby):
        emoji, color = TYPE_STYLE.get(str(e.get("type", "")).lower(),
                                      ("🆘", "#7f8c8d"))
        with cols[i % 3], st.container(border=True):
            st.markdown(f"**{emoji} {e.get('name', 'Facility')}**")
            st.caption(f"{e.get('type', 'service').title()} · "
                       f"{e.get('distance_km', '?')} km away")
            if e.get("phone"):
                st.markdown(f"[📞 Call {e['phone']}](tel:{e['phone']})")
            if e.get("address"):
                st.caption(e["address"][:70])
        if e.get("lat") is not None:
            folium.Marker([e["lat"], e["lon"]], tooltip=f"{emoji} {e.get('name')}",
                          icon=folium.Icon(color=color)).add_to(m)
    st_folium(m, height=360, use_container_width=True)
else:
    st.warning("No facility coordinates in the data yet — the national "
               "helplines above work everywhere. "
               "*(Add lat/lon to emergency.json to enable the map.)*")

st.info("💾 Save this page before you travel. In an emergency call **112** — "
        "it routes to police, medical and fire services across Odisha.")
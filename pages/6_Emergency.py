"""Emergency Services — helplines + nearest facilities, always one tap away."""
import folium
import streamlit as st
from streamlit_folium import st_folium

from services import hotel_service, place_service
from utils.i18n import t, tf, language_picker



st.title(t("emergency_title"))
st.markdown(f"### {t('helplines_header')}")

HELPLINES = [("112", "help_all", "🆘"), ("100", "help_police", "👮"),
             ("108", "help_ambulance", "🚑"), ("101", "help_fire", "🔥")]
hc = st.columns(4)
for col, (num, key, emoji) in zip(hc, HELPLINES):
    col.markdown(f"[**📞 {num}**](tel:{num})  \n{emoji} {t(key)}")

st.divider()
st.markdown(f"### {t('facilities_header')}")
places = place_service.get_all_places()
curated = [p for p in places if p.get("source") == "curated"] or places
base = st.selectbox(t("show_near"), curated,
                    format_func=lambda p: f"{p['name']} ({p.get('city', '')})")

nearby = hotel_service.get_emergency_near(base["lat"], base["lon"])
TYPE_STYLE = {"police": ("type_police", "#3498db"),
              "hospital": ("type_hospital", "#e74c3c"),
              "fire": ("type_fire", "#e67e22"),
              "pharmacy": ("type_pharmacy", "#27ae60")}

if nearby:
    m = folium.Map(location=[base["lat"], base["lon"]], zoom_start=11)
    folium.Marker([base["lat"], base["lon"]], tooltip=f"📍 {base['name']}",
                  icon=folium.Icon(color="blue")).add_to(m)
    cols = st.columns(3)
    for i, e in enumerate(nearby):
        key, color = TYPE_STYLE.get(str(e.get("type", "")).lower(),
                                    ("type_hospital", "#7f8c8d"))
        with cols[i % 3], st.container(border=True):
            st.markdown(f"**🏥 {e.get('name', 'Facility')}**")
            st.caption(f"{t(key)} · " + tf("km_away", km=e.get("distance_km", "?")))
            if e.get("phone"):
                st.markdown(f"[{t('call')} {e['phone']}](tel:{e['phone']})")
            if e.get("address"):
                st.caption(e["address"][:70])
        if e.get("lat") is not None:
            folium.Marker([e["lat"], e["lon"]],
                          tooltip=f"{e.get('name')}",
                          icon=folium.Icon(color=color)).add_to(m)
    st_folium(m, height=360, use_container_width=True)
    st.caption(t("osm_note"))
else:
    st.warning(t("no_coords"))

st.info(t("save_info"))
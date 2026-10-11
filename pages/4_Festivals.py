"""Festivals of Odisha — upcoming strip, filters, map, multilingual cards."""
import calendar
from datetime import date

import folium
import streamlit as st
from streamlit_folium import st_folium

from services.festival_service import (
    get_all_festivals,
    get_upcoming_festivals,
    search_festivals,
)
from utils.i18n import t, tf, language_picker, content_lang



ss = st.session_state

CATEGORY_COLORS = {"religious": "#e74c3c", "cultural": "#8e44ad",
                   "art": "#2980b9", "tribal": "#27ae60", "fair": "#f39c12"}
CROWD_LABEL = {"very_high": "crowd_very_high", "high": "crowd_high",
               "medium": "crowd_medium"}
DATE_BADGE = {"verified": "✅", "computed": "🧮"}   # else 📅 typical window


def badge_for(f: dict) -> str:
    return DATE_BADGE.get(f.get("date_source", "manual"), "📅")


def chip(text: str, color: str) -> str:
    return (f"<span style='background:{color}22;color:{color};"
            f"border:1px solid {color}55;border-radius:12px;padding:2px 10px;"
            f"font-size:12px;margin:0 4px 4px 0;display:inline-block'>{text}</span>")


def loc(f: dict, field: str) -> str:
    """Native festival text in the global content language, English fallback."""
    block = f.get(field) or {}
    lang = content_lang()
    return block.get(lang) or block.get("en", "")


def crowd(level: str) -> str:
    return t(CROWD_LABEL.get(level, "crowd_medium")) if level in CROWD_LABEL \
        else "👥"


st.title(t("festivals_title"))
st.caption(t("fest_caption"))
all_fest = get_all_festivals()

# ---- quick stats ----
this_month = date.today().month
m1, m2, m3 = st.columns(3)
m1.metric(t("metric_festivals"), len(all_fest))
m2.metric(t("metric_this_month"),
          sum(1 for f in all_fest
              if this_month in f.get("typical_window", {}).get("months", [])))
m3.metric(t("metric_gems"),
          sum(1 for f in all_fest if f.get("is_hidden_gem")))

# ---- upcoming strip ----
upcoming = get_upcoming_festivals(days_ahead=90, limit=6)
if upcoming:
    st.subheader(t("upcoming_90"))
    cols = st.columns(min(3, len(upcoming)))
    for i, f in enumerate(upcoming):
        with cols[i % len(cols)], st.container(border=True):
            st.markdown(f"**{loc(f, 'name')}**")
            approx = " *(approx.)*" if f.get("dates_approximate") else ""
            st.caption(f"{f['city']} · {f['next_start']} → {f['next_end']}  "
                       f"{badge_for(f)}{approx}")

st.divider()
st.subheader(t("all_festivals"))

# ---- filters ----
c1, c2, c3 = st.columns([1, 1, 2])
month_sel = c1.selectbox(
    t("month"),
    [t("month_all")] + [f"{i:02d} · {calendar.month_name[i]}"
                        for i in range(1, 13)])
cat_sel = c2.selectbox(
    t("category"),
    [t("month_all")] + sorted({f.get("category", "other")
                               for f in all_fest}))
query = c3.text_input(t("search"), label_visibility="collapsed",
                      placeholder=t("fest_search_ph"))

festivals = search_festivals(query) if query else list(all_fest)
if month_sel != t("month_all"):
    mnum = int(month_sel[:2])
    festivals = [f for f in festivals
                 if mnum in f.get("typical_window", {}).get("months", [])]
if cat_sel != t("month_all"):
    festivals = [f for f in festivals if f.get("category") == cat_sel]

st.caption(tf("fest_results", n=len(festivals)))

# ---- map ----
m = folium.Map(location=[20.35, 85.30], zoom_start=7, tiles="OpenStreetMap")
for f in festivals:
    coords = (f.get("location") or {}).get("coordinates")
    if not coords:
        continue
    lng, lat = coords                      # GeoJSON order: [lng, lat]
    color = CATEGORY_COLORS.get(f.get("category"), "#3388ff")
    popup_html = (f"<div style='width:240px;font-family:sans-serif'>"
                  f"<b>{loc(f, 'name')}</b><br>"
                  f"<span style='color:#666'>{f.get('city', '')} · "
                  f"{f.get('category', '')}</span><br>"
                  f"{loc(f, 'description')[:140]}</div>")
    folium.CircleMarker([lat, lng], radius=8, color=color, fill=True,
                        fill_opacity=0.85, tooltip=loc(f, "name"),
                        popup=folium.Popup(popup_html, max_width=260)).add_to(m)
st_folium(m, height=420, use_container_width=True)

# ---- cards ----
if not festivals:
    st.info(t("no_fest_match"))
for i in range(0, len(festivals), 2):
    row = st.columns(2)
    for col, f in zip(row, festivals[i:i + 2]):
        color = CATEGORY_COLORS.get(f.get("category"), "#3388ff")
        with col, st.container(border=True):
            head = (f"### {loc(f, 'name')}"
                    + (" 💎" if f.get("is_hidden_gem") else ""))
            st.markdown(head)
            months = "/".join(calendar.month_abbr[mn]
                              for mn in f.get("typical_window", {}).get("months", []))
            st.caption(f"{f.get('city')}, {f.get('district', '')} · "
                       f"`{f.get('category', '')}` · "
                       f"~{f.get('duration_days', '?')} {t('days_short')} · "
                       f"{crowd(f.get('crowd_level', ''))} · 📆 {months}")
            st.write(loc(f, "description"))
            tips = f.get("travel_tips") or {}
            tip = tips.get(content_lang()) or tips.get("en")
            if tip:
                st.info(f"💡 {tip}")
            if f.get("known_dates"):
                with st.expander(t("date_history")):
                    for d in sorted(f["known_dates"],
                                    key=lambda x: x.get("year", 0)):
                        flag = (t("verified") if not d.get("approximate")
                                else t("approximate"))
                        src = (f" · source: {d['source']}"
                               if d.get("source") else "")
                        st.markdown(f"- **{d.get('year')}**: {d['start']} → "
                                    f"{d.get('end', d['start'])} — {flag}{src}")
                    if f.get("official_source"):
                        st.caption(f"[official source]({f['official_source']})")
            if f.get("tags"):
                st.markdown("".join(chip(f"#{tag}", color)
                                    for tag in f["tags"][:6]),
                            unsafe_allow_html=True)

st.caption(t("fest_planner_hint"))
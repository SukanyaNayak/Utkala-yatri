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

st.set_page_config(page_title="Festivals · UtkalaYatri", page_icon="🎪",
                   layout="wide")

ss = st.session_state
ss.setdefault("fest_lang", "en")

CATEGORY_COLORS = {"religious": "#e74c3c", "cultural": "#8e44ad",
                   "art": "#2980b9", "tribal": "#27ae60", "fair": "#f39c12"}
CROWD_LABEL = {"very_high": "👥👥👥 very high", "high": "👥👥 high",
               "medium": "👥 moderate"}
LANG_LABELS = {"en": "English", "hi": "हिन्दी", "or": "ଓଡ଼ିଆ"}
DATE_BADGE = {"verified": "✅", "computed": "🧮"}   # else 📅 typical window


def badge_for(f: dict) -> str:
    return DATE_BADGE.get(f.get("date_source", "manual"), "📅")


def chip(text: str, color: str) -> str:
    return (f"<span style='background:{color}22;color:{color};"
            f"border:1px solid {color}55;border-radius:12px;padding:2px 10px;"
            f"font-size:12px;margin:0 4px 4px 0;display:inline-block'>{text}</span>")


def loc(f: dict, field: str) -> str:
    """Localized text field with English fallback."""
    block = f.get(field) or {}
    return block.get(ss["fest_lang"]) or block.get("en", "")


st.title("🎪 Festivals of Odisha")
all_fest = get_all_festivals()

# ---- language + quick stats ----
this_month = date.today().month
lc1, lc2, lc3, lc4 = st.columns([1, 1, 1, 2])
ss["fest_lang"] = lc1.selectbox("Language", list(LANG_LABELS),
                                format_func=lambda k: LANG_LABELS[k],
                                label_visibility="collapsed")
lc2.metric("Festivals", len(all_fest))
lc3.metric("In this month",
           sum(1 for f in all_fest
               if this_month in f.get("typical_window", {}).get("months", [])))
lc4.metric("Hidden gems 💎",
           sum(1 for f in all_fest if f.get("is_hidden_gem")))

# ---- upcoming strip ----
upcoming = get_upcoming_festivals(days_ahead=90, limit=6)
if upcoming:
    st.subheader("🗓️ Coming up in the next 90 days")
    cols = st.columns(min(3, len(upcoming)))
    for i, f in enumerate(upcoming):
        with cols[i % len(cols)], st.container(border=True):
            st.markdown(f"**{loc(f, 'name')}**")
            approx = " *(approx.)*" if f.get("dates_approximate") else ""
            st.caption(f"{f['city']} · {f['next_start']} → {f['next_end']}  "
                       f"{badge_for(f)}{approx}")

st.divider()
st.subheader("All festivals")

# ---- filters ----
c1, c2, c3 = st.columns([1, 1, 2])
month_sel = c1.selectbox(
    "Month",
    ["All"] + [f"{i:02d} · {calendar.month_name[i]}" for i in range(1, 13)])
cat_sel = c2.selectbox(
    "Category",
    ["All"] + sorted({f.get("category", "other") for f in all_fest}))
query = c3.text_input("Search", label_visibility="collapsed",
                      placeholder="Search festival, city or tag…")

festivals = search_festivals(query) if query else list(all_fest)
if month_sel != "All":
    mnum = int(month_sel[:2])
    festivals = [f for f in festivals
                 if mnum in f.get("typical_window", {}).get("months", [])]
if cat_sel != "All":
    festivals = [f for f in festivals if f.get("category") == cat_sel]

st.caption(f"{len(festivals)} festival(s)")

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
    st.info("No festivals match — try another month, category or search.")
for i in range(0, len(festivals), 2):
    row = st.columns(2)
    for col, f in zip(row, festivals[i:i + 2]):
        color = CATEGORY_COLORS.get(f.get("category"), "#3388ff")
        with col, st.container(border=True):
            head = f"### {loc(f, 'name')}" + (" 💎" if f.get("is_hidden_gem") else "")
            st.markdown(head)
            months = "/".join(calendar.month_abbr[mn]
                              for mn in f.get("typical_window", {}).get("months", []))
            st.caption(f"{f.get('city')}, {f.get('district', '')} · "
                       f"`{f.get('category', '')}` · ~{f.get('duration_days', '?')} day(s) · "
                       f"{CROWD_LABEL.get(f.get('crowd_level'), '')} · 📆 {months}")
            st.write(loc(f, "description"))
            tips = f.get("travel_tips") or {}
            tip = tips.get(ss["fest_lang"]) or tips.get("en")
            if tip:
                st.info(f"💡 {tip}")
            if f.get("known_dates"):
                with st.expander("📅 Date history & trust"):
                    for d in sorted(f["known_dates"],
                                    key=lambda x: x.get("year", 0)):
                        flag = ("✅ verified" if not d.get("approximate")
                                else "🧮 approximate")
                        src = (f" · source: {d['source']}"
                               if d.get("source") else "")
                        st.markdown(f"- **{d.get('year')}**: {d['start']} → "
                                    f"{d.get('end', d['start'])} — {flag}{src}")
                    if f.get("official_source"):
                        st.caption(f"[official source]({f['official_source']})")
            if f.get("tags"):
                st.markdown("".join(chip(f"#{t}", color)
                                    for t in f["tags"][:6]),
                            unsafe_allow_html=True)

st.caption("Planning a trip? The 📅 Trip Planner automatically flags festivals "
           "happening during your travel dates.")
"""Trip Planner — pick stops + dates -> routed day-wise plan, map, costs,
and the festival callout."""
from datetime import date, timedelta
from math import ceil
import calendar
from datetime import date, timedelta
import folium
import streamlit as st
from streamlit_folium import st_folium

from services import chatbot_service, gemini_service, place_service
from services.festival_service import get_festivals_during
from services.routing_service import get_route_between, order_stops

st.set_page_config(page_title="Trip Planner · UtkalaYatri", page_icon="📅",
                   layout="wide")
ss = st.session_state
ss.setdefault("plan_ai", {})

LEG_COLORS = ["#e74c3c", "#2980b9", "#27ae60", "#8e44ad", "#f39c12", "#16a085"]
RATE_PER_KM = {"🛵 Bike": 2.5, "🚗 Car": 8.0}

st.title("📅 AI Trip Planner")
st.caption("Pick your stops and dates — UtkalaYatri sequences them, draws real "
           "road routes, estimates costs, and flags festivals along the way.")

places = place_service.get_all_places()
curated = [p for p in places if p.get("source") == "curated"] or places
label = lambda p: f"{p['name']} ({p.get('city', '')})"

c1, c2 = st.columns([1, 2])
start_place = c1.selectbox("🏁 Starting from", curated, format_func=label)
stops = c2.multiselect("📍 Destinations (2–6 works best)", curated,
                       format_func=label,
                       default=[p for p in curated if p["name"] == "Konark Sun Temple"][:2])

c3, c4, c5 = st.columns(3)
trip_start = c3.date_input("🗓️ Trip starts", value=date.today() + timedelta(days=1),
                           min_value=date.today())
days = c4.slider("Days", 1, 7, 3)
mode = c5.radio("Travel mode", list(RATE_PER_KM), horizontal=True)

if len(stops) < 1:
    st.info("Select at least one destination to build a plan.")
    st.stop()

trip_end = trip_start + timedelta(days=days - 1)
ordered = order_stops(start_place, stops)

# ---- legs ----
route_points = [start_place] + ordered
legs = [get_route_between(route_points[i], route_points[i + 1])
        for i in range(len(route_points) - 1)]
total_km = sum(l["distance_km"] for l in legs)
total_min = sum(l["duration_min"] for l in legs)
live_routing = any(l["provider"] != "estimate" for l in legs)

# ---- festival callout (the demo moment) ----
during = get_festivals_during(trip_start, trip_end)
if during:
    def fest_label(f: dict) -> str:
        name = f["name"]["en"]
        if f.get("date_confidence") == "known":
            start_d = date.fromisoformat(f["next_start"])
            when = (f["next_start"] if start_d >= trip_start
                    else f"ongoing since {f['next_start']}")
            return f"**{name}** ({f['city']}, {when})"
        mnames = " / ".join(calendar.month_name[m]
                            for m in f.get("typical_months", []))
        return f"**{name}** ({f['city']}, typically {mnames or 'varies'})"
    st.success("🎪 **Happening during your trip:** "
               + " · ".join(fest_label(f) for f in during[:4]))
else:
    st.info("No major festivals fall inside your dates — the Festivals page "
            "shows what's coming up next.")
# ---- map ----
m = folium.Map(location=[ordered[0]["lat"], ordered[0]["lon"]], zoom_start=8)
folium.Marker([start_place["lat"], start_place["lon"]],
              tooltip=f"🏁 {start_place['name']}",
              icon=folium.Icon(color="green", icon="flag")).add_to(m)
for i, (p, leg) in enumerate(zip(ordered, legs)):
    folium.Marker([p["lat"], p["lon"]],
                  tooltip=f"{i + 1}. {p['name']}",
                  icon=folium.DivIcon(html=f"<div style='font-size:18px'>"
                                       f"<b>{i + 1}️⃣</b></div>")).add_to(m)
    folium.PolyLine(leg["geometry"], color=LEG_COLORS[i % len(LEG_COLORS)],
                    weight=4, opacity=0.85,
                    dash_array="6" if leg["provider"] == "estimate" else None,
                    tooltip=f"{leg['distance_km']} km · ~{leg['duration_min']} min"
                            + (" (estimate)" if leg["provider"] == "estimate" else "")
                    ).add_to(m)
st_folium(m, height=400, use_container_width=True)

# ---- day-wise itinerary ----
st.subheader(f"🧭 Your {days}-day plan — {total_km:.0f} km, ~{total_min // 60} h {total_min % 60:02d} m on the road"
             + ("" if live_routing else " *(straight-line estimates — routing service unreachable)*"))
per_day = ceil(len(ordered) / days)
day_stops = [ordered[i:i + per_day] for i in range(0, len(ordered), per_day)]
leg_by_stop = {ordered[i]["place_id"]: legs[i] for i in range(len(ordered))}

for d, group in enumerate(day_stops[:days], 1):
    with st.container(border=True):
        st.markdown(f"**Day {d}**")
        for j, p in enumerate(group):
            emoji, _ = place_service.category_meta(p.get("category"))
            leg = leg_by_stop.get(p["place_id"])
            travel = (f" · 🚗 {leg['distance_km']} km, ~{leg['duration_min']} min from previous"
                      if leg else "")
            st.markdown(f"- {emoji} **{p['name']}**{travel}")
            if p.get("best_time"):
                st.caption(f"   ⏰ Best time: {p['best_time']}")

# ---- cost calculator ----
st.subheader("💰 Estimated trip cost")
cc1, cc2, cc3, cc4 = st.columns(4)
travelers = cc1.number_input("Travellers", 1, 10, 2)
stay = cc2.number_input("Stay / night (₹)", 500, 20000, 1500, step=250)
food_day = cc3.number_input("Food / person / day (₹)", 100, 5000, 600, step=50)
misc_day = cc4.number_input("Misc / day (₹)", 0, 5000, 500, step=50)

travel_cost = total_km * RATE_PER_KM[mode]
nights = max(0, days - 1)
total = travel_cost + nights * stay + travelers * days * (food_day + misc_day)

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"{mode} fuel/fare", f"₹{travel_cost:,.0f}", f"{total_km:.0f} km")
k2.metric("Stay", f"₹{nights * stay:,.0f}", f"{nights} night(s)")
k3.metric("Food + misc", f"₹{travelers * days * (food_day + misc_day):,.0f}",
          f"{travelers} × {days} d")
k4.metric("Total", f"₹{total:,.0f}", "estimate")

# ---- optional AI polish ----
plan_key = f"{trip_start}_{days}_{len(ordered)}_{mode}"
if gemini_service.is_configured() and st.button("✨ Ask AI to refine this plan"):
    with st.spinner("UtkalaYatri AI is reviewing your plan…"):
        summary = "\n".join(
            f"Day {d}: " + ", ".join(p["name"] for p in group)
            for d, group in enumerate(day_stops[:days], 1))
        fest = "; ".join(f["name"]["en"] for f in during[:4]) or "none"
        ss["plan_ai"][plan_key] = gemini_service.ask(
            f"Trip plan for Odisha ({trip_start} to {trip_end}, {mode}):\n{summary}\n"
            f"Road total ~{total_km:.0f} km. Festivals during trip: {fest}.\n\n"
            "Give: 1) one ordering/timing fix if any, 2) one food or local tip, "
            "3) one caution (crowds/traffic/weather). Max 90 words, bullets.",
            system=chatbot_service.build_system_prompt("en"))
if ss["plan_ai"].get(plan_key):
    st.info(ss["plan_ai"][plan_key])
// src/pages/Hotels.tsx  (v2 — themed to match the new Explore & Festivals look)
//
// Same treatment the Festivals page got — but YOUR logic is untouched:
//   • API calls are exactly yours: api.places() → api.hotels(lat, lon, radius),
//     hotels reload live when you change the base place or the radius slider.
//   • PageHero banner on top (same component as Festivals/Planner/Chat).
//   • The place select + radius slider now sit ON the hero photo, Explore
//     style: one white pill bar + green "Find hotels →" button that scrolls
//     to the list. Stacks into a rounded card on mobile.
//   • Map and hotel cards wear the theme: rounded-3xl cream borders,
//     font-script headings, sage/orange pills, lightbulb tip boxes and a
//     themed empty state.
//
// i18n: your existing keys (nav-hotels area) still work — radius, state,
// price_na, no_hotels. New hotels_* keys below all use defaultValue
// fallbacks, so nothing breaks if you don't touch the locale files.
// (Optional: copy hotels-i18n-keys.txt into en/hi/or.json for translations.)
//
// ⚠ ONE THING TO CHECK (same as Festivals v7): your PageHero must render
//   {children}. If TypeScript says "Property 'children' does not exist",
//   copy PageHero-v7.tsx (same download folder) over
//   src/components/PageHero.tsx.
export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { useTranslation } from "react-i18next";
import {
  FaMapMarkerAlt,
  FaMapMarkedAlt,
  FaHotel,
  FaRupeeSign,
  FaStar,
  FaRegLightbulb,
  FaChevronDown,
  FaBed,
} from "react-icons/fa";
import { api } from "../api/client";
import type { Place } from "../api/client";
import PageHero from "../components/PageHero"; // same import line as your Chat.tsx

type Hotel = {
  hotel_id: string;
  name: string;
  city?: string;
  price?: string;
  price_range_inr?: string;
  rating?: number;
  notes?: string;
  description?: string;
  lat: number;
  lon: number;
  distance_km: number;
};

export default function Hotels() {
  const { t } = useTranslation();

  const [places, setPlaces] = useState<Place[]>([]);
  const [base, setBase] = useState<Place | null>(null);
  const [radius, setRadius] = useState(25);
  const [hotels, setHotels] = useState<Hotel[]>([]);

  useEffect(() => {
    api
      .places()
      .then((p) => {
        setPlaces(p);
        setBase(p[0] ?? null);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (base) api.hotels(base.lat, base.lon, radius).then(setHotels).catch(console.error);
  }, [base, radius]);

  // the hero button just jumps to the list — filtering is already live
  function scrollToResults() {
    document.getElementById("hotel-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="pb-4">
      {/* ── hero banner — place select + radius slider sit ON the photo ── */}
      <PageHero
        title={t("hotels_title", { defaultValue: "Hotels & Stays" })}
        tagline={t("hotels_tag", { defaultValue: "STAY • NEARBY • COMFY" })}
        desc={t("hotels_desc", {
          defaultValue: "Pick a base place and a radius — we'll show the hotels around it on the map and in a tidy list.",
        })}
        quote={t("hotels_quote", { defaultValue: "Rest Well, Travel Far" })}
      >
        {/* controls ON the hero photo — same look as the Explore/Festivals
            bar: white pill, borderless select, slider, green button */}
        <div
          role="search"
          className="flex flex-col gap-2 rounded-[2rem] bg-white p-2 pl-5 shadow-[0_10px_30px_rgba(0,0,0,0.28)] sm:flex-row sm:items-center sm:rounded-full"
        >
          {/* base place */}
          <div className="relative min-w-0 flex-1">
            <FaMapMarkerAlt className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-sm text-[#C4A882]" />
            <select
              aria-label={t("hotels_base", { defaultValue: "Base place" })}
              value={base?.place_id ?? ""}
              onChange={(e) => setBase(places.find((p) => p.place_id === e.target.value) ?? null)}
              className="h-11 w-full min-w-0 cursor-pointer appearance-none rounded-full bg-transparent pl-8 pr-9 text-sm font-semibold text-[#3E2A1B] focus:outline-none focus:ring-2 focus:ring-forest/40"
            >
              {places.map((p) => (
                <option key={p.place_id} value={p.place_id}>
                  {p.name} ({p.city})
                </option>
              ))}
            </select>
            <FaChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#6B5D4F]" />
          </div>

          {/* radius slider */}
          <div className="flex items-center gap-2 rounded-full bg-[#FFF7EF] px-4 py-2 sm:bg-transparent sm:px-0 sm:py-0">
            <span className="shrink-0 text-xs font-semibold text-[#B08968]">
              {t("radius", { defaultValue: "Radius" })}
            </span>
            <input
              type="range"
              min={5}
              max={100}
              step={5}
              value={radius}
              onChange={(e) => setRadius(+e.target.value)}
              className="w-28 cursor-pointer accent-forest sm:w-24"
            />
            <span className="shrink-0 rounded-full bg-sage px-2.5 py-0.5 text-[10px] font-bold text-forest">
              {radius} km
            </span>
          </div>

          {/* hotels reload live — this button jumps to the list */}
          <button
            onClick={scrollToResults}
            className="flex h-11 shrink-0 items-center justify-center gap-2 rounded-full bg-forest px-7 text-sm font-bold text-white shadow-sm transition-colors hover:bg-[#2C4634] active:scale-95"
          >
            {t("hotels_find", { defaultValue: "Find hotels" })} <span aria-hidden>→</span>
          </button>
        </div>
      </PageHero>

      {/* ── results summary strip ──────────────────────────────────────── */}
      {base && (
        <div className="mt-6 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-2xl bg-sage px-4 py-3 text-sm font-semibold text-forest">
          <FaMapMarkerAlt className="shrink-0" />
          <b>{base.name}</b>
          <span className="font-normal opacity-70">·</span>
          <span>
            {t("hotels_found", {
              n: hotels.length,
              r: radius,
              defaultValue: "{{n}} hotels within {{r}} km",
            })}
          </span>
        </div>
      )}

      {/* ── map ────────────────────────────────────────────────────────── */}
      <div className="mt-6">
        <h2 className="flex items-center gap-2 font-script text-3xl text-forest">
          <FaMapMarkedAlt className="text-xl" /> {t("hotels_on_map", { defaultValue: "On the map" })}
        </h2>
        {base && (
          <MapContainer
            center={[base.lat, base.lon]}
            zoom={10}
            className="z-0 mt-3 h-80 rounded-3xl border border-[#F0E2D0] bg-[#FFF7EF] shadow-sm"
          >
            <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {/* base place = deep green dot */}
            <CircleMarker
              center={[base.lat, base.lon]}
              radius={9}
              pathOptions={{ color: "#35543F", fillColor: "#35543F", fillOpacity: 0.9 }}
            />
            {hotels.map((h) => (
              <CircleMarker
                key={h.hotel_id}
                center={[h.lat, h.lon]}
                radius={6}
                pathOptions={{ color: "#D35400", fillColor: "#E8A268", fillOpacity: 0.9 }}
              >
                <Popup>
                  <b>{h.name}</b>
                  <br />
                  {h.price ?? h.price_range_inr ?? t("price_na", { defaultValue: "Price N/A" })}
                  <br />
                  {Number(h.distance_km).toFixed(1)} km
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        )}
      </div>

      {/* ── nearby stays (theme cards) ─────────────────────────────────── */}
      <div id="hotel-list" className="mt-6 scroll-mt-4">
        <h2 className="flex items-center gap-2 font-script text-3xl text-forest">
          <FaHotel className="text-lg" /> {t("hotels_list", { defaultValue: "Nearby stays" })}
        </h2>
        {hotels.length > 24 && (
          <p className="mt-1 text-xs text-[#B08968]">
            {t("hotels_showing", {
              n: 24,
              total: hotels.length,
              defaultValue: "Showing the first {{n}} of {{total}} stays — shrink the radius to narrow it down.",
            })}
          </p>
        )}

        {hotels.length > 0 ? (
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {hotels.slice(0, 24).map((h) => (
              <div key={h.hotel_id} className="flex flex-col rounded-3xl border border-[#F0E2D0] bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-script text-xl leading-tight text-[#3E2A1B]">{h.name.slice(0, 40)}</h3>
                  <span className="shrink-0 rounded-full bg-sage px-2.5 py-0.5 text-[10px] font-bold text-forest">
                    ~{Number(h.distance_km).toFixed(1)} km
                  </span>
                </div>
                <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-[#6B5D4F]">
                  <span className="flex items-center gap-1">
                    <FaMapMarkerAlt className="text-terracotta" /> {h.city ?? t("state", { defaultValue: "Odisha" })}
                  </span>
                  {h.rating ? (
                    <span className="flex items-center gap-1">
                      <FaStar className="text-[#E8A23B]" /> {h.rating}
                    </span>
                  ) : null}
                </p>
                <p className="mt-2 flex items-center gap-1.5 text-sm font-semibold text-[#3E2A1B]">
                  <FaRupeeSign className="text-xs text-forest" />
                  {h.price ?? h.price_range_inr ?? t("price_na", { defaultValue: "Price N/A" })}
                </p>
                {(h.notes ?? h.description) && (
                  <p className="mt-2.5 flex items-start gap-2 rounded-2xl bg-[#FFF7EF] px-3 py-2 text-xs text-[#6B5D4F]">
                    <FaRegLightbulb className="mt-0.5 shrink-0 text-terracotta" />
                    <span>{(h.notes ?? h.description)!.slice(0, 100)}…</span>
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : base ? (
          <div className="mt-3 flex min-h-[160px] flex-col items-center justify-center rounded-3xl border border-dashed border-[#EAD9C6] bg-white/60 p-8 text-center">
            <FaBed className="mb-2 text-3xl text-[#C4A882]" />
            <p className="text-sm text-[#B08968]">
              {t("no_hotels", { defaultValue: "No hotels found in this radius. Try widening it." })}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

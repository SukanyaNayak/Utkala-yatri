// src/pages/Emergency.tsx  (v4 — theme + SSR-SAFE lazy Leaflet map)
//
// ROOT CAUSE FOUND (reproduced on an identical Next.js + React 19 stack):
//   import { MapContainer } from "react-leaflet"  →  imports leaflet
//   → leaflet touches `window` while the module is being evaluated
//   → Next.js pre-renders the page on the SERVER, where window does
//     not exist → "ReferenceError: window is not defined" → the page
//     (or the lazy chunk) crashes → blank page / map fallback.
//   (This is why it "worked for 1 second": the HTML arrived, then the
//   hydration/flight data failed and React gave up.)
//
// WHAT v4 CHANGES vs v3 — only HOW the map is created:
//   • NO static react-leaflet / leaflet import anywhere. Leaflet is
//     loaded lazily inside useEffect with `await import("leaflet")`,
//     so the module is evaluated ONLY in the browser. SSR can never
//     crash, on every Next.js version and every router setup.
//   • The map is drawn with raw Leaflet (L.circleMarker) — the same
//     approach your own MapView uses ("default-icon bug avoided").
//     No marker PNGs needed, so no broken default icons either.
//   • StrictMode-safe: the effect cleans up with map.remove(), which
//     releases the container ("Map container is already initialized"
//     can never happen).
//   • If the Leaflet chunk fails to load, a small 🗺️ box appears and
//     the facility list below still works — the page can NEVER go blank.
//   • All your logic is untouched: api.places() → api.emergency(lat,lon).
//   • The helplines, hero, select and facility cards are IDENTICAL to v3.
export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { useEffect, useRef, useState } from "react";
import type { Map as LeafletMap } from "leaflet"; // type-only import: erased at build, SSR-safe
import "leaflet/dist/leaflet.css"; // pure CSS — safe on the server
import { useTranslation } from "react-i18next";
import {
  FaMapMarkerAlt,
  FaMapMarkedAlt,
  FaPhoneAlt,
  FaChevronDown,
  FaShieldAlt,
} from "react-icons/fa";
import { api } from "../api/client";
import type { Place } from "../api/client";
import PageHero from "../components/PageHero"; // same import line as your Chat.tsx

type Facility = {
  name: string;
  type: string;
  lat: number;
  lon: number;
  phone?: string;
  address?: string;
  distance_km?: number;
};

// [number, emoji, i18n key, english fallback]
const HELPLINES: [string, string, string, string][] = [
  ["112", "🆘", "help_all", "All emergency"],
  ["100", "👮", "help_police", "Police"],
  ["108", "🚑", "help_ambulance", "Ambulance"],
  ["101", "🔥", "help_fire", "Fire"],
];

const TYPES: Record<string, string> = { hospital: "🏥", police: "👮", fire: "🔥", pharmacy: "💊" };

/** Escape a string before putting it inside a Leaflet popup (HTML string). */
function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
}

export default function Emergency() {
  const { t } = useTranslation();

  const [places, setPlaces] = useState<Place[]>([]);
  const [base, setBase] = useState<Place | null>(null);
  const [nearby, setNearby] = useState<Facility[]>([]);
  const [mapFailed, setMapFailed] = useState(false);
  const mapElRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    api
      .places()
      .then((p) => {
        // guard: a non-list response must never reach the render code
        const list = Array.isArray(p) ? p : [];
        if (!Array.isArray(p)) console.error("places API did not return a list:", p);
        setPlaces(list);
        setBase(list[0] ?? null);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!base) return;
    api
      .emergency(base.lat, base.lon)
      .then((data) => {
        if (Array.isArray(data)) {
          setNearby(data);
        } else {
          // most likely your backend has no working /emergency route and the
          // api client returned the error body — check the Network tab (F12)
          console.error("emergency API did not return a list:", data);
          setNearby([]);
        }
      })
      .catch(console.error);
  }, [base]);

  // ── the map: raw Leaflet, loaded lazily, browser-only ──────────────────
  useEffect(() => {
    if (!base) return;

    const lat = Number(base.lat);
    const lon = Number(base.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;

    let map: LeafletMap | null = null;
    let cancelled = false;

    (async () => {
      try {
        const L = await import("leaflet"); // ← evaluated in the browser ONLY
        if (cancelled) return;
        const el = mapElRef.current;
        // _leaflet_id is set by Leaflet on the container; if it is still
        // there, a map already lives on this div — do not double-init
        const anyEl = el as (HTMLDivElement & { _leaflet_id?: number }) | null;
        if (!anyEl || anyEl._leaflet_id != null) return;

        map = L.map(anyEl, { scrollWheelZoom: false });

        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(map);

        // base place — deep green dot
        L.circleMarker([lat, lon], {
          radius: 9,
          color: "#ffffff",
          weight: 2.5,
          fillColor: "#35543F",
          fillOpacity: 0.95,
        })
          .addTo(map)
          .bindPopup(`<b>📍 ${esc(base.name)}</b><br>${esc(base.city ?? "")}`);

        // facilities — terracotta dots (no marker images needed)
        const pts: [number, number][] = [[lat, lon]];
        for (const f of nearby) {
          const flat = Number(f.lat);
          const flon = Number(f.lon);
          if (!Number.isFinite(flat) || !Number.isFinite(flon)) continue; // skip bad coordinates
          pts.push([flat, flon]);
          const popup =
            `<b>${TYPES[f.type] ?? "🆘"} ${esc(f.name)}</b>` +
            (f.address ? `<br>${esc(f.address)}` : "") +
            (f.phone ? `<br><a href="tel:${esc(f.phone)}">📞 ${esc(f.phone)}</a>` : "");
          L.circleMarker([flat, flon], {
            radius: 7,
            color: "#ffffff",
            weight: 1.5,
            fillColor: "#D35400",
            fillOpacity: 0.92,
          })
            .addTo(map)
            .bindPopup(popup);
        }

        // frame base + facilities (or just center on the base)
        if (pts.length > 1) {
          map.fitBounds(L.latLngBounds(pts), { padding: [30, 30], maxZoom: 12 });
        } else {
          map.setView([lat, lon], 11);
        }
      } catch (err) {
        console.error("Map failed to load:", err); // ← the real cause, always in the console
        if (!cancelled) setMapFailed(true);
      }
    })();

    // cleanup: StrictMode double-mount safe — remove() releases the container
    return () => {
      cancelled = true;
      map?.remove();
      map = null;
    };
    // re-run when the place or the facilities change
  }, [base, nearby]);

  // the hero button just jumps to the facilities — loading is already live
  function scrollToResults() {
    document.getElementById("facility-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="pb-4">
      {/* ── hero banner — base-place select sits ON the photo ──────────── */}
      <PageHero
        title={t("emergency_title", { defaultValue: "Emergency & Help" })}
        tagline={t("emergency_tag", { defaultValue: "HELP • 24×7 • SAFE" })}
        desc={t("emergency_desc", {
          defaultValue:
            "Tap a helpline to call instantly, or find hospitals, police stations, fire stations and pharmacies near your base place.",
        })}
        quote={t("emergency_quote", { defaultValue: "Help Is Always Near" })}
      >
        {/* select ON the hero photo — same white pill as Explore/Festivals */}
        <div
          role="search"
          className="flex flex-col gap-2 rounded-[2rem] bg-white p-2 pl-5 shadow-[0_10px_30px_rgba(0,0,0,0.28)] sm:flex-row sm:items-center sm:rounded-full"
        >
          <div className="relative min-w-0 flex-1">
            <FaMapMarkerAlt className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-sm text-[#C4A882]" />
            <select
              aria-label={t("emergency_base", { defaultValue: "Base place" })}
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

          {/* facilities reload live — this button jumps to the list */}
          <button
            onClick={scrollToResults}
            className="flex h-11 shrink-0 items-center justify-center gap-2 rounded-full bg-forest px-7 text-sm font-bold text-white shadow-sm transition-colors hover:bg-[#2C4634] active:scale-95"
          >
            {t("emergency_find", { defaultValue: "Find nearby" })} <span aria-hidden>→</span>
          </button>
        </div>
      </PageHero>

      {/* ── helplines (tap to call) ────────────────────────────────────── */}
      <div className="mt-6">
        <h2 className="flex items-center gap-2 font-script text-3xl text-forest">
          <FaPhoneAlt className="text-lg" /> {t("helplines_header", { defaultValue: "Helplines" })}
        </h2>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {HELPLINES.map(([num, emoji, key, def]) => (
            <a
              key={num}
              href={`tel:${num}`}
              className="rounded-3xl border border-[#F0E2D0] bg-white p-4 text-center shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md active:scale-95"
            >
              <div className="text-2xl" aria-hidden>
                {emoji}
              </div>
              <div className="mt-1 text-2xl font-bold leading-none text-terracotta">{num}</div>
              <div className="mt-2 inline-block rounded-full bg-sage px-2.5 py-0.5 text-[10px] font-bold text-forest">
                {t(key, { defaultValue: def })}
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* ── nearby facilities ──────────────────────────────────────────── */}
      <div id="facility-list" className="mt-6 scroll-mt-4">
        <h2 className="flex items-center gap-2 font-script text-3xl text-forest">
          <FaMapMarkedAlt className="text-xl" /> {t("facilities_header", { defaultValue: "Nearby facilities" })}
        </h2>

        {base && (
          <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-2xl bg-sage px-4 py-3 text-sm font-semibold text-forest">
            <FaMapMarkerAlt className="shrink-0" />
            <span>
              {t("emergency_found", {
                n: nearby.length,
                place: base.name,
                defaultValue: "{{n}} facilities near {{place}}",
              })}
            </span>
          </div>
        )}

        {/* the map container — Leaflet draws into it after mount. If the
            Leaflet chunk ever fails, the small note below still appears
            and the facility list keeps working. The page can NEVER go blank. */}
        {base && !mapFailed && <div ref={mapElRef} className="z-0 mt-3 h-80 rounded-3xl border border-[#F0E2D0] bg-[#FFF7EF] shadow-sm" />}

        {mapFailed && (
          <div className="mt-3 flex min-h-[160px] flex-col items-center justify-center rounded-3xl border border-dashed border-[#EAD9C6] bg-white/60 p-8 text-center">
            <span className="mb-2 text-3xl" aria-hidden>
              🗺️
            </span>
            <p className="text-sm text-[#B08968]">
              {t("emergency_map_fail", {
                defaultValue: "The map could not load, but the facility list below still works.",
              })}
            </p>
          </div>
        )}

        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {nearby.slice(0, 12).map((f) => (
            <div key={f.name + f.lat} className="flex flex-col rounded-3xl border border-[#F0E2D0] bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-script text-xl leading-tight text-[#3E2A1B]">{f.name}</h3>
                {f.distance_km != null && (
                  <span className="shrink-0 rounded-full bg-sage px-2.5 py-0.5 text-[10px] font-bold text-forest">
                    ~{Number(f.distance_km).toFixed(1)} km
                  </span>
                )}
              </div>
              <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-[#6B5D4F]">
                <span>
                  {TYPES[f.type] ?? "🆘"} {f.type}
                </span>
              </p>
              {f.phone && (
                <a
                  href={`tel:${f.phone}`}
                  className="mt-2 flex items-center gap-1.5 text-sm font-semibold text-terracotta hover:underline"
                >
                  <FaPhoneAlt className="text-xs" /> {f.phone}
                </a>
              )}
            </div>
          ))}
        </div>

        <p className="mt-3 text-xs text-[#B08968]">{t("osm_note", { defaultValue: "Facility data © OpenStreetMap contributors" })}</p>

        <div className="mt-4 flex items-start gap-2 rounded-2xl bg-sage px-4 py-3 text-sm font-semibold text-forest">
          <FaShieldAlt className="mt-0.5 shrink-0" />
          <span>{t("save_info", { defaultValue: "Save these numbers in your phone before your trip." })}</span>
        </div>
      </div>
    </div>
  );
}

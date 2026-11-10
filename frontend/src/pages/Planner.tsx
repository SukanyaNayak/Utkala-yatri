// src/pages/Planner.tsx  (v3 — fills empty days with nearby suggested places)
// Trip Planner — restyled to match the new Explore & Chat theme.
// What changed in v3:
//   • Pick 1 place for 3 days? → it now SUGGESTS nearby places to fill
//     Day 2 and Day 3 (marked with an orange "Suggested" badge)
//   • Day cards now split evenly — 3 days always shows Day 1, 2, 3
//   • "Get best routes" now ALWAYS rebuilds the plan with your current
//     settings (before, it only scrolled if a plan already existed)
export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  FaMapMarkerAlt,
  FaSearch,
  FaCalendarAlt,
  FaCompass,
  FaChevronRight,
  FaRoute,
  FaWallet,
  FaCloudSun,
  FaBookmark,
  FaTimes,
} from "react-icons/fa";
import PageHero from "../components/PageHero"; // same import line as your Chat.tsx

/* ── built-in stop list (used when the backend is not running) ────────── */
type Stop = { id: string; name: string; city: string; lat: number; lon: number; best_time: string };

const STOPS: Stop[] = [
  { id: "konark",      name: "Konark Sun Temple",      city: "Konark",      lat: 19.8876, lon: 86.0945, best_time: "October – March" },
  { id: "jagannath",   name: "Jagannath Temple",       city: "Puri",        lat: 19.8050, lon: 85.8217, best_time: "October – February" },
  { id: "chilika",     name: "Chilika Lake",           city: "Chilika",     lat: 19.7000, lon: 85.3000, best_time: "November – February" },
  { id: "lingaraj",    name: "Lingaraj Temple",        city: "Bhubaneswar", lat: 20.2380, lon: 85.8340, best_time: "October – February" },
  { id: "udaigiri",    name: "Udayagiri Caves",        city: "Bhubaneswar", lat: 20.2400, lon: 85.7830, best_time: "October – March" },
  { id: "nandankanan", name: "Nandankanan Zoo",        city: "Bhubaneswar", lat: 20.3950, lon: 85.8190, best_time: "October – March" },
  { id: "dhauli",      name: "Dhauli Shanti Stupa",    city: "Bhubaneswar", lat: 20.1930, lon: 85.8380, best_time: "October – February" },
  { id: "pipli",       name: "Pipli Applique Village", city: "Pipli",       lat: 20.1230, lon: 85.8430, best_time: "October – February" },
];

const ORIGIN_CITIES = [
  { name: "Bhubaneswar", lat: 20.2961, lon: 85.8245 },
  { name: "Cuttack",     lat: 20.4625, lon: 85.8830 },
  { name: "Puri",        lat: 19.8135, lon: 85.8312 },
  { name: "Berhampur",   lat: 19.3151, lon: 84.7941 },
  { name: "Sambalpur",   lat: 21.4669, lon: 83.9813 },
  { name: "Rourkela",    lat: 22.2604, lon: 84.8536 },
  { name: "Balasore",    lat: 21.4942, lon: 86.9335 },
];

type Mode = "car" | "bus" | "bike" | "train";
const MODES: Mode[] = ["car", "bus", "bike", "train"];
const PER_KM: Record<Mode, number> = { car: 9, bike: 5, bus: 4, train: 6 }; // ₹ per km
const COST = { stayPerNight: 1800, foodPerDay: 700 }; // ₹

/** A stop inside a built plan — auto:true means the planner suggested it. */
type PlanStop = Stop & { auto?: boolean };

interface PlanResult {
  origin: string;
  ordered: PlanStop[];
  totalKm: number;
  days: PlanStop[][];
  nDays: number;
  mode: Mode;
  date: string;
  costs: { travel: number; stay: number; food: number; total: number };
}

/** Straight-line distance between two points, in km. */
function haversineKm(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const la1 = (a.lat * Math.PI) / 180;
  const la2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** Greedy route: from the start city, always hop to the nearest unvisited stop. */
function bestOrder(origin: { lat: number; lon: number }, list: Stop[]): Stop[] {
  const left = [...list];
  const out: Stop[] = [];
  let cur = origin;
  while (left.length > 0) {
    let best = 0;
    for (let i = 1; i < left.length; i++) {
      if (haversineKm(cur, left[i]) < haversineKm(cur, left[best])) best = i;
    }
    cur = left[best];
    out.push(left.splice(best, 1)[0]);
  }
  return out;
}

/** When there are more days than picked places, suggest the nearest
 *  un-picked places so every day has something to visit. */
function fillWithNearby(planned: Stop[], pool: Stop[], need: number): PlanStop[] {
  const added: PlanStop[] = [];
  const plannedPts = [...planned];
  const left = pool.filter((s) => !planned.some((p) => p.id === s.id));
  while (added.length < need && left.length > 0) {
    let bi = 0;
    let bd = Infinity;
    for (let i = 0; i < left.length; i++) {
      // distance from this candidate to the closest already-planned place
      let d = Infinity;
      for (const p of plannedPts) {
        const dd = haversineKm(p, left[i]);
        if (dd < d) d = dd;
      }
      if (d < bd) {
        bd = d;
        bi = i;
      }
    }
    const chosen = left.splice(bi, 1)[0];
    added.push({ ...chosen, auto: true });
    plannedPts.push(chosen); // so the next suggestion grows outward
  }
  return added;
}

/** Try to load your real places from the backend; fall back to the built-in list. */
async function loadStops(): Promise<Stop[]> {
  try {
    const res = await fetch("/api/places");
    const data = await res.json();
    const list: any[] = Array.isArray(data) ? data : data.places ?? [];
    const fromApi: Stop[] = list.map((p, i) => ({
      id: String(p.id ?? p._id ?? i),
      name: String(p.name ?? "Place"),
      city: String(p.city ?? ""),
      lat: Number(p.lat ?? p.latitude ?? 0),
      lon: Number(p.lon ?? p.lng ?? p.longitude ?? 0),
      best_time: String(p.best_time ?? "All year"),
    }));
    const seen = new Set(fromApi.map((s) => s.name.toLowerCase()));
    return [...fromApi, ...STOPS.filter((s) => !seen.has(s.name.toLowerCase()))];
  } catch {
    return STOPS; // backend off → built-in list
  }
}

/** Small forest-green circle with the step number. */
function StepBadge({ n }: { n: number }) {
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-forest text-xs font-bold text-white">
      {n}
    </span>
  );
}

export default function Planner() {
  const { t } = useTranslation();

  const [stops, setStops] = useState<Stop[]>(STOPS);
  const [origin, setOrigin] = useState(ORIGIN_CITIES[0].name);
  const [originQuery, setOriginQuery] = useState("");
  const [destIds, setDestIds] = useState<string[]>([]);
  const [qInput, setQInput] = useState("");
  const [date, setDate] = useState("");
  const [days, setDays] = useState(3);
  const [mode, setMode] = useState<Mode>("car");
  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showTimes, setShowTimes] = useState(false);

  // load your real places once when the page opens
  useEffect(() => {
    loadStops().then(setStops);
  }, []);

  const originCity = ORIGIN_CITIES.find((c) => c.name === origin) ?? ORIGIN_CITIES[0];
  const filteredOrigins = ORIGIN_CITIES.filter((c) =>
    c.name.toLowerCase().includes(originQuery.toLowerCase())
  );
  // if what you typed matches no city, show all 7 cities so you can just pick one
  const originSuggestions = originQuery && filteredOrigins.length > 0 ? filteredOrigins : ORIGIN_CITIES;

  const selectedPlaces = useMemo(
    () => destIds.map((id) => stops.find((p) => p.id === id)!).filter(Boolean),
    [destIds, stops]
  );

  const destMatches = useMemo(() => {
    const needle = qInput.trim().toLowerCase();
    if (!needle) return [];
    return stops
      .filter(
        (p) =>
          !destIds.includes(p.id) &&
          (p.name.toLowerCase().includes(needle) || p.city.toLowerCase().includes(needle))
      )
      .slice(0, 6);
  }, [qInput, destIds, stops]);

  // places shown in the "Best time to visit" panel
  const timesList = selectedPlaces.length > 0 ? selectedPlaces : stops.slice(0, 6);

  function addDest(id: string) {
    setDestIds((ids) => (ids.includes(id) ? ids : [...ids, id]));
    setPlan(null);
    setSaved(false);
  }

  function removeDest(id: string) {
    setDestIds((ids) => ids.filter((x) => x !== id));
    setPlan(null);
    setSaved(false);
  }

  function generate() {
    if (selectedPlaces.length === 0) return;
    setBusy(true);
    setSaved(false);

    // ── ROUTING SLOT ─────────────────────────────────────────────────
    // If your old Planner.tsx ordered the stops its own way (or asked your
    // backend for a route), paste that code here and use its result as
    // `route0`. The default below simply hops to the nearest next stop.
    const route0: PlanStop[] = bestOrder(originCity, selectedPlaces);
    // ─────────────────────────────────────────────────────────────────

    // More days than places? → suggest nearby places to fill the empty
    // days (target: up to 2 places per day, maximum 6 suggestions).
    const need = Math.min(6, Math.max(0, days * 2 - route0.length));
    const suggestions: PlanStop[] = need > 0 ? fillWithNearby(route0, stops, need) : [];

    // route again with the suggestions included so the order stays sensible
    const ordered: PlanStop[] = bestOrder(originCity, [
      ...route0,
      ...suggestions,
    ]) as PlanStop[];

    const pts = [originCity, ...ordered];
    let totalKm = 0;
    for (let i = 1; i < pts.length; i++) {
      totalKm += Math.round(haversineKm(pts[i - 1], pts[i]) * 1.22); // ×1.22 ≈ real roads
    }

    // spread the stops across the days as evenly as possible
    // (3 days + 6 stops → 2 per day; 3 days + 4 stops → 2/1/1)
    const n = ordered.length;
    const chunkCount = Math.max(1, Math.min(days, n));
    const base = Math.floor(n / chunkCount);
    const extra = n % chunkCount;
    const daySplit: PlanStop[][] = [];
    let idx = 0;
    for (let d = 0; d < chunkCount; d++) {
      const size = base + (d < extra ? 1 : 0);
      daySplit.push(ordered.slice(idx, idx + size));
      idx += size;
    }

    const nights = Math.max(1, days - 1);
    const costs = {
      travel: Math.round(totalKm * PER_KM[mode]),
      stay: nights * COST.stayPerNight,
      food: days * COST.foodPerDay,
      total: 0,
    };
    costs.total = costs.travel + costs.stay + costs.food;

    setPlan({ origin: originCity.name, ordered, totalKm, days: daySplit, nDays: days, mode, date, costs });
    setBusy(false);
  }

  function savePlan() {
    if (!plan) return;
    try {
      localStorage.setItem("uy_plan", JSON.stringify(plan));
      setSaved(true);
    } catch {
      /* storage full or private mode — ignore */
    }
  }

  function scrollToId(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ── the 4 strip buttons ─────────────────────────────────────────────
  function handleRoutes() {
    if (selectedPlaces.length > 0) {
      generate(); // ALWAYS rebuild with the current settings, then jump to it
      setTimeout(() => scrollToId("uy-plan"), 150);
    } else {
      scrollToId("uy-steps"); // nothing selected yet → show the form
    }
  }

  function handleCosts() {
    if (plan) scrollToId("uy-costs");
    else scrollToId("uy-steps");
  }

  function handleSave() {
    if (plan) savePlan();
    else scrollToId("uy-steps");
  }

  const FEATURES = [
    { icon: <FaRoute />, title: t("planner_feat_route"), sub: t("planner_feat_route_sub"), onClick: handleRoutes },
    { icon: <FaWallet />, title: t("planner_feat_cost"), sub: t("planner_feat_cost_sub"), onClick: handleCosts },
    { icon: <FaCloudSun />, title: t("planner_feat_time"), sub: t("planner_feat_time_sub"), onClick: () => setShowTimes((s) => !s) },
    {
      icon: <FaBookmark />,
      title: saved ? t("planner_saved") : t("planner_feat_save"),
      sub: t("planner_feat_save_sub"),
      onClick: handleSave,
    },
  ];

  return (
    <div className="pb-4">
      <PageHero title={t("planner_title")} tagline={t("planner_tag")} desc={t("planner_desc")} quote={t("planner_quote")} />

      {/* ── 5-step planner card ─────────────────────────────────────────── */}
      <div id="uy-steps" className="mt-6 rounded-3xl border border-[#F0E2D0] bg-white p-4 shadow-sm sm:p-6">
        {/* Step 1 — starting point */}
        <div className="flex items-start gap-3">
          <StepBadge n={1} />
          <div className="min-w-0 flex-1">
            <label className="flex items-center gap-1.5 text-sm font-bold text-[#3E2A1B]">
              <FaMapMarkerAlt className="text-forest" /> {t("planner_step1")}
            </label>
            <div className="relative mt-2">
              <FaMapMarkerAlt className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-[#B08968]" />
              <input
                value={originQuery || origin}
                onChange={(e) => {
                  setOriginQuery(e.target.value);
                  setOrigin(e.target.value);
                }}
                onFocus={() => setOriginQuery("")}
                placeholder={t("planner_origin_ph")}
                className="h-12 w-full rounded-2xl border border-[#EAD9C6] bg-[#FFF7EF]/60 pl-10 pr-10 text-sm text-[#3E2A1B] placeholder:text-[#C4A882] focus:outline-none focus:ring-2 focus:ring-forest/40"
              />
              {originQuery || origin ? (
                <button
                  onClick={() => {
                    setOrigin(ORIGIN_CITIES[0].name);
                    setOriginQuery("");
                  }}
                  aria-label="clear"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#C4A882] hover:text-[#D35400]"
                >
                  <FaTimes />
                </button>
              ) : null}
            </div>
            {originQuery ? (
              <ul className="mt-1 overflow-hidden rounded-2xl border border-[#EAD9C6] bg-white shadow-sm">
                {originSuggestions.map((c) => (
                  <li key={c.name}>
                    <button
                      onClick={() => {
                        setOrigin(c.name);
                        setOriginQuery("");
                      }}
                      className="w-full px-4 py-2.5 text-left text-sm text-[#3E2A1B] hover:bg-[#FFF7EF]"
                    >
                      {c.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>

        <div className="my-4 h-px bg-[#F0E2D0]" />

        {/* Step 2 — add destinations */}
        <div className="flex items-start gap-3">
          <StepBadge n={2} />
          <div className="min-w-0 flex-1">
            <label className="flex items-center gap-1.5 text-sm font-bold text-[#3E2A1B]">
              <FaSearch className="text-forest" /> {t("planner_step2")}
            </label>
            <div className="relative mt-2">
              <FaSearch className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-[#C4A882]" />
              <input
                value={qInput}
                onChange={(e) => setQInput(e.target.value)}
                placeholder={t("planner_add_dest")}
                className="h-12 w-full rounded-2xl border border-[#EAD9C6] bg-[#FFF7EF]/60 pl-10 pr-4 text-sm text-[#3E2A1B] placeholder:text-[#C4A882] focus:outline-none focus:ring-2 focus:ring-forest/40"
              />
            </div>
            {destMatches.length > 0 ? (
              <ul className="mt-1 overflow-hidden rounded-2xl border border-[#EAD9C6] bg-white shadow-sm">
                {destMatches.map((p) => (
                  <li key={p.id}>
                    <button
                      onClick={() => {
                        addDest(p.id);
                        setQInput("");
                      }}
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-[#FFF7EF]"
                    >
                      <span className="font-semibold text-[#3E2A1B]">{p.name}</span>
                      <span className="text-xs text-[#B08968]"> · {p.city}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            {selectedPlaces.length > 0 ? (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {selectedPlaces.map((p) => (
                  <span
                    key={p.id}
                    className="inline-flex h-8 items-center gap-2 rounded-full bg-sage px-3 text-xs font-semibold text-forest"
                  >
                    {p.name}
                    <button onClick={() => removeDest(p.id)} aria-label="clear" className="hover:text-[#D35400]">
                      <FaTimes />
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        {/* Steps 3-4-5 — dates, days, travel mode */}
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-[#F0E2D0] bg-[#FFF7EF]/50 p-4">
            <label className="flex items-center gap-2 text-sm font-bold text-[#3E2A1B]">
              <StepBadge n={3} /> <FaCalendarAlt className="text-forest" /> {t("planner_step3")}
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="mt-3 h-10 w-full rounded-xl border border-[#EAD9C6] bg-white px-3 text-sm text-[#3E2A1B] focus:outline-none focus:ring-2 focus:ring-forest/40"
            />
          </div>

          <div className="rounded-2xl border border-[#F0E2D0] bg-[#FFF7EF]/50 p-4">
            <label className="flex items-center gap-2 text-sm font-bold text-[#3E2A1B]">
              <StepBadge n={4} /> {t("planner_step4")}
            </label>
            <div className="mt-3 flex h-10 items-center justify-between rounded-xl border border-[#EAD9C6] bg-white px-2">
              <button
                onClick={() => setDays((d) => Math.max(1, d - 1))}
                className="h-8 w-9 rounded-lg font-bold text-forest hover:bg-sage"
                aria-label="minus"
              >
                −
              </button>
              <span className="text-lg font-bold text-[#3E2A1B]">{days}</span>
              <button
                onClick={() => setDays((d) => Math.min(7, d + 1))}
                className="h-8 w-9 rounded-lg font-bold text-forest hover:bg-sage"
                aria-label="plus"
              >
                +
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-[#F0E2D0] bg-[#FFF7EF]/50 p-4">
            <label className="flex items-center gap-2 text-sm font-bold text-[#3E2A1B]">
              <StepBadge n={5} /> {t("planner_step5")}
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as Mode)}
              className="mt-3 h-10 w-full rounded-xl border border-[#EAD9C6] bg-white px-3 text-sm text-[#3E2A1B] focus:outline-none focus:ring-2 focus:ring-forest/40"
            >
              {MODES.map((m) => (
                <option key={m} value={m}>
                  {t(`planner_mode_${m}`)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Build My Plan */}
        <div className="mt-5 flex flex-col items-center gap-2">
          <button
            onClick={generate}
            disabled={selectedPlaces.length === 0 || busy}
            className="flex h-14 w-full items-center justify-center gap-3 rounded-full bg-forest text-base font-bold text-white shadow-sm transition-all hover:bg-[#2C4634] active:scale-[0.99] disabled:opacity-40 sm:w-auto sm:px-12"
          >
            <FaCompass className={`text-lg ${busy ? "animate-spin" : ""}`} />
            {t("planner_build")}
            <FaChevronRight className="text-sm opacity-80" />
          </button>
          {selectedPlaces.length === 0 && !busy ? (
            <p className="text-xs text-[#B08968]">{t("planner_empty")}</p>
          ) : null}
        </div>
      </div>

      {/* ── feature strip — now REAL buttons ────────────────────────────── */}
      <div className="mt-5 grid grid-cols-2 gap-2 rounded-3xl bg-sage p-4 sm:grid-cols-4 sm:p-5">
        {FEATURES.map((f, i) => (
          <button
            key={i}
            onClick={f.onClick}
            className="flex items-center gap-3 rounded-2xl p-2 text-left transition-colors hover:bg-white/70"
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-forest text-sm text-white">
              {f.icon}
            </span>
            <span>
              <span className="block text-xs font-bold text-[#3E2A1B] sm:text-sm">{f.title}</span>
              <span className="hidden text-xs text-[#6B7A5E] sm:block">{f.sub}</span>
            </span>
          </button>
        ))}
      </div>

      {/* ── best-time panel (opens when you click "Best time to visit") ── */}
      {showTimes ? (
        <div className="mt-3 rounded-3xl border border-[#EAD9C6] bg-white p-4">
          <p className="font-script text-2xl text-forest">{t("planner_feat_time")}</p>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {timesList.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between gap-2 rounded-2xl bg-[#FFF7EF] px-3 py-2 text-sm"
              >
                <span className="font-semibold text-[#3E2A1B]">{s.name}</span>
                <span className="text-xs font-semibold text-forest">{s.best_time}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* ── result ──────────────────────────────────────────────────────── */}
      {plan ? (
        <div id="uy-plan" className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-script text-3xl text-forest">{t("planner_your_plan")}</h2>
            <button
              onClick={savePlan}
              className={`flex h-10 items-center gap-2 rounded-full border px-4 text-sm font-bold transition-colors ${
                saved
                  ? "border-forest bg-forest text-white"
                  : "border-forest/40 bg-white text-forest hover:bg-sage"
              }`}
            >
              <FaBookmark /> {saved ? t("planner_saved") : t("planner_save")}
            </button>
          </div>

          <p className="text-xs font-semibold text-[#B08968]">
            {plan.origin} → {plan.ordered.length} {t("planner_destinations").toLowerCase()} ·{" "}
            {plan.nDays} {t("planner_days").toLowerCase()} · {t(`planner_mode_${plan.mode}`)}
            {plan.date ? ` · ${plan.date.split("-").reverse().join("-")}` : ""}
          </p>

          {/* how many of the stops were auto-suggested */}
          {plan.ordered.some((s) => s.auto) ? (
            <p className="text-xs font-semibold text-[#D35400]">
              + {plan.ordered.filter((s) => s.auto).length} {t("planner_suggested")}
            </p>
          ) : null}

          <div id="uy-costs" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-2xl border border-[#F0E2D0] bg-white p-3.5">
              <p className="text-[10px] font-bold uppercase tracking-wide text-[#B08968]">
                {t("planner_total_km")}
              </p>
              <p className="mt-1 text-xl font-bold text-[#3E2A1B]">
                ~{plan.totalKm} <span className="text-sm font-semibold text-[#B08968]">km</span>
              </p>
            </div>
            {(["travel", "stay", "food"] as const).map((k) => (
              <div key={k} className="rounded-2xl border border-[#F0E2D0] bg-white p-3.5">
                <p className="text-[10px] font-bold uppercase tracking-wide text-[#B08968]">
                  {t(`planner_cost_${k}`)}
                </p>
                <p className="mt-1 text-xl font-bold text-[#3E2A1B]">₹{plan.costs[k].toLocaleString("en-IN")}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between rounded-2xl bg-forest p-4 text-white">
            <span className="font-semibold">{t("planner_est_cost")}</span>
            <span className="text-2xl font-extrabold">₹{plan.costs.total.toLocaleString("en-IN")}</span>
          </div>

          <div className="space-y-3">
            {plan.days.map((dayPlaces, di) => (
              <div key={di} className="rounded-2xl border border-[#F0E2D0] bg-white p-4">
                <p className="flex h-8 w-fit items-center rounded-full bg-forest px-3.5 text-xs font-bold text-white">
                  {t("planner_day")} {di + 1}
                </p>
                <ol className="mt-3 space-y-2.5">
                  {dayPlaces.map((p, pi) => (
                    <li key={p.id} className="flex items-center gap-2.5 text-sm text-[#3E2A1B]">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sage text-[11px] font-bold text-forest">
                        {pi + 1}
                      </span>
                      <span className="font-semibold">{p.name}</span>
                      <span className="truncate text-xs text-[#B08968]">· {p.city}</span>
                      {p.auto ? (
                        <span className="ml-auto shrink-0 rounded-full bg-[#FCE9CB] px-2 py-0.5 text-[10px] font-bold text-[#B45309]">
                          {t("planner_suggested")}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-6 flex min-h-[220px] flex-col items-center justify-center rounded-3xl border border-dashed border-[#EAD9C6] bg-white/60 p-8 text-center">
          <span className="mb-3 text-4xl" aria-hidden>
            🗺️
          </span>
          <p className="max-w-xs text-sm text-[#B08968]">{t("planner_empty")}</p>
        </div>
      )}
    </div>
  );
}
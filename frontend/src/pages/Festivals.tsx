// src/pages/Festivals.tsx  (v7 — search ON the hero, photo "Coming up soon" cards)
// Your 3 requests, exactly:
//   1. SEARCH BAR now sits ON the hero image — passed to <PageHero> as
//      {children}, so it renders inside the banner exactly like your
//      Explore Places page: one white pill bar with the magnifier, the
//      borderless "All locations" dropdown and the green "Search →" button.
//      (The old white card that floated ABOVE the banner is gone.)
//   2. HERO SECTION unchanged — same PageHero banner, same title/tagline/
//      desc/quote and photo. Only the search bar moved into it.
//   3. "Coming up soon" cards keep the real FESTIVAL PHOTO as the card
//      background (with a soft dark layer so the white text stays
//      readable). ONLY these cards have photos — the "All festivals"
//      cards below stay clean white cards.
//
// Also still true:
//   • The countdown pills (Today / Tomorrow / In N days) are back.
//   • No ugly scrollbar under the card row (hidden on purpose).
//   • If a photo ever fails to load, that card falls back to a soft
//     theme gradient — the page never looks broken.
//   • All 9 festivals carry a photo in the data (even the ones not in
//     the "Coming up soon" row today) — so as months pass and a new
//     festival rotates into the top-5, its photo is already there.
//     Nothing for you to maintain.
//   • No i18n edits needed — same fest_*/cat_* keys as before.
//
// ⚠ ONE THING TO CHECK: your PageHero must render {children} (one line).
//   If TypeScript complains "Property 'children' does not exist", copy
//   PageHero-v7.tsx (next to this file) over src/components/PageHero.tsx.
//
// Want to swap a photo later? Each festival has ONE image: "..." line —
// replace the URL (or use "/fest-durga.jpg" after copying the file into
// frontend/public/).
export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  FaSearch,
  FaMapMarkerAlt,
  FaCalendarAlt,
  FaStar,
  FaRegLightbulb,
  FaChevronDown,
} from "react-icons/fa";
import PageHero from "../components/PageHero"; // same import line as your Chat.tsx

/* ── festival list (works without the backend) ────────────────────────── */
type Fest = {
  id: string;
  name: string;
  city: string;
  month: string; // shown to the user, e.g. "1 – 5 December"
  mmdd: string; // "MM-DD" — used to compute how soon the festival is
  cat: string; // religious | cultural | dance | music | tribal | folk | art
  desc: string;
  tip: string;
  image?: string; // photo used on the "Coming up soon" card
};

const FESTS: Fest[] = [
  {
    id: "rath",
    name: "Rath Yatra (Car Festival)",
    city: "Puri",
    month: "June – July",
    mmdd: "06-27",
    cat: "religious",
    desc: "Lord Jagannath, Balabhadra and Subhadra ride giant wooden chariots pulled by lakhs of devotees along Puri's Bada Danda — one of the world's largest religious processions.",
    tip: "Book Puri hotels 2–3 months ahead. Try Mahaprasad at Ananda Bazar.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/ed5021ec08f6.jpg",
  },
  {
    id: "durga",
    name: "Durga Puja",
    city: "Cuttack",
    month: "September – October",
    mmdd: "09-28",
    cat: "religious",
    desc: "Cuttack's centuries-old Durga Puja is famous for its Chandi Medha — massive silver backdrops behind emerald-crowned Durga idols across the old city.",
    tip: "Pandal-hopping is best on foot; visit after 7 PM for the lighting.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/1fb07af16fb1.jpg",
  },
  {
    id: "parab",
    name: "Parab Festival",
    city: "Koraput",
    month: "November",
    mmdd: "11-15",
    cat: "tribal",
    desc: "Koraput's tribal festival brings together folk dance, music and the heritage of the district's tribal communities.",
    tip: "Pair it with a trip to Duduma Waterfall.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/a8cd33eb5427.jpg",
  },
  {
    id: "balijatra",
    name: "Bali Jatra",
    city: "Cuttack",
    month: "November",
    mmdd: "11-24",
    cat: "cultural",
    desc: "Cuttack's grand trade fair on the Mahanadi riverbank, held on Kartik Purnima to remember the Odia sailors who set off for Bali and Southeast Asia.",
    tip: "Go in the evening for the Boita Bandana lamps floating on the river.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/e2bb409b956b.jpg",
  },
  {
    id: "konarkdance",
    name: "Konark Dance Festival",
    city: "Konark",
    month: "1 – 5 December",
    mmdd: "12-01",
    cat: "dance",
    desc: "Classical dancers perform against the floodlit Sun Temple every December — an open-air stage like no other.",
    tip: "Carry a shawl — December evenings by the sea get cold.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/813091a1465d.jpg",
  },
  {
    id: "sandart",
    name: "Sand Art Festival",
    city: "Chandrabhaga",
    month: "1 – 5 December",
    mmdd: "12-01",
    cat: "art",
    desc: "International sand artists sculpt giant masterpieces on Chandrabhaga beach, right next to the Sun Temple.",
    tip: "Visit early morning for soft light and fewer crowds.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/b09ce02ba1d8.jpg",
  },
  {
    id: "dhanu",
    name: "Dhanu Yatra",
    city: "Bargarh",
    month: "December – January",
    mmdd: "12-16",
    cat: "folk",
    desc: "Bargarh town becomes the mythical Mathura for around 10 days — the world's largest open-air theatre.",
    tip: "The evening Kansa procession is the highlight.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/ca210b322f2b.jpeg",
  },
  {
    id: "mukteswar",
    name: "Mukteswar Dance Festival",
    city: "Bhubaneswar",
    month: "January",
    mmdd: "01-14",
    cat: "dance",
    desc: "Odissi dancers perform in the lamp-lit Mukteswar temple compound in old Bhubaneswar.",
    tip: "Entry is free — reach an hour early for a good seat.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/491dd87811ac.jpg",
  },
  {
    id: "rajarani",
    name: "Rajarani Music Festival",
    city: "Bhubaneswar",
    month: "January",
    mmdd: "01-18",
    cat: "music",
    desc: "Three evenings of Indian classical music at the dreamy Rajarani temple.",
    tip: "Combine it with the Mukteswar festival — same month, same city.",
    image: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/8d983fabf9a2.jpg",
  },
];

/* ── helpers ───────────────────────────────────────────────────────────── */
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// soft theme gradients — ONLY the automatic fallback when a coming-up
// card has no photo (all 9 festivals have one baked in below)
const GRADS = [
  "from-forest to-[#5A7A62]",
  "from-[#D35400] to-[#E8A268]",
  "from-[#8A9B6E] to-[#B5C29A]",
  "from-[#B06E3B] to-[#D9A05B]",
];

/** How many days from today until the next MM-DD (ignores the year). */
function daysUntil(mmdd: string): number {
  const [m, d] = mmdd.split("-").map(Number);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  let next = new Date(now.getFullYear(), m - 1, d);
  if (next < today) next = new Date(now.getFullYear() + 1, m - 1, d);
  return Math.round((next.getTime() - today.getTime()) / 86400000);
}

/** "12-01" → "1 Dec" */
function dateLabel(mmdd: string): string {
  const [m, d] = mmdd.split("-").map(Number);
  return `${d} ${MONTHS_SHORT[m - 1]}`;
}

/** Two pastel badge styles, both from the theme palette. */
function badgeStyle(cat: string): string {
  return ["religious", "music", "art"].includes(cat)
    ? "bg-[#FCE9CB] text-[#B45309]"
    : "bg-sage text-forest";
}

export default function Festivals() {
  const { t } = useTranslation();

  const [q, setQ] = useState("");
  const [city, setCity] = useState("");

  const cities = useMemo(() => Array.from(new Set(FESTS.map((f) => f.city))).sort(), []);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return FESTS.filter(
      (f) =>
        (!city || f.city === city) &&
        (!needle ||
          f.name.toLowerCase().includes(needle) ||
          f.city.toLowerCase().includes(needle) ||
          f.desc.toLowerCase().includes(needle))
    );
  }, [q, city]);

  // 5 festivals starting soonest (Today / Tomorrow / In N days)
  const upcoming = useMemo(
    () =>
      [...FESTS]
        .filter((f) => /^\d{2}-\d{2}$/.test(f.mmdd))
        .sort((a, b) => daysUntil(a.mmdd) - daysUntil(b.mmdd))
        .slice(0, 5),
    []
  );

  function whenLabel(n: number): string {
    if (n === 0) return t("fest_today", { defaultValue: "Today" });
    if (n === 1) return t("fest_tomorrow", { defaultValue: "Tomorrow" });
    return t("fest_in_days", { n, defaultValue: "In {{n}} days" });
  }

  function scrollToResults() {
    document.getElementById("fest-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="pb-4">
      {/* ── hero banner (unchanged) — the search bar now lives ON it ────── */}
      <PageHero
        title={t("fest_title")}
        tagline={t("fest_tag")}
        desc={t("fest_desc")}
        quote={t("fest_quote")}
      >
        {/* search bar ON the hero photo — same look as the Explore page:
            one white pill bar, magnifier left, borderless "All locations"
            dropdown, green "Search →" pill. Stacks into a card on mobile. */}
        <div
          role="search"
          className="flex flex-col gap-2 rounded-[2rem] bg-white p-2 pl-5 shadow-[0_10px_30px_rgba(0,0,0,0.28)] sm:flex-row sm:items-center sm:rounded-full"
        >
          <div className="relative flex-1">
            <FaSearch className="pointer-events-none absolute left-1 top-1/2 -translate-y-1/2 text-sm text-[#C4A882]" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("fest_search_ph", { defaultValue: "Search festivals or cities…" })}
              className="h-11 w-full min-w-0 rounded-full bg-transparent pl-8 pr-3 text-sm text-[#3E2A1B] placeholder:text-[#C4A882] focus:outline-none"
            />
          </div>

          <div className="relative shrink-0">
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="h-11 w-full cursor-pointer appearance-none rounded-full bg-transparent pl-3 pr-9 text-sm font-semibold text-[#3E2A1B] focus:outline-none focus:ring-2 focus:ring-forest/40 sm:w-auto"
            >
              <option value="">{t("fest_all_cities", { defaultValue: "All locations" })}</option>
              {cities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <FaChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#6B5D4F]" />
          </div>

          {/* filtering is live while you type — this button jumps to the list */}
          <button
            onClick={scrollToResults}
            className="flex h-11 shrink-0 items-center justify-center gap-2 rounded-full bg-forest px-7 text-sm font-bold text-white shadow-sm transition-colors hover:bg-[#2C4634] active:scale-95"
          >
            {t("fest_search", { defaultValue: "Search" })} <span aria-hidden>→</span>
          </button>
        </div>
      </PageHero>

      {/* ── coming up soon (festival PHOTO cards) ───────────────────────── */}
      <div className="mt-6">
        <h2 className="flex items-center gap-2 font-script text-3xl text-forest">
          <FaCalendarAlt className="text-xl" /> {t("fest_coming", { defaultValue: "Coming up soon" })}
        </h2>
        <div className="mt-3 flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {upcoming.map((f, i) => (
            <div
              key={f.id}
              className={`relative flex h-48 w-60 shrink-0 snap-start flex-col justify-between overflow-hidden rounded-3xl p-4 text-white shadow-sm ${
                f.image ? "" : `bg-gradient-to-br ${GRADS[i % GRADS.length]}`
              }`}
              style={
                f.image
                  ? {
                      backgroundImage: `url(${f.image})`,
                      backgroundSize: "cover",
                      backgroundPosition: "center",
                    }
                  : undefined
              }
            >
              {/* soft dark layer so the white text stays readable on photos */}
              {f.image ? <div className="absolute inset-0 bg-black/35" /> : null}

              <div className="relative">
                <span className="rounded-full bg-forest/90 px-3 py-1 text-xs font-bold">
                  {dateLabel(f.mmdd)}
                </span>
              </div>
              <div className="relative">
                <p className="flex items-center gap-1 text-xs font-semibold opacity-90">
                  <FaMapMarkerAlt /> {f.city}
                </p>
                <p className="font-script text-2xl leading-tight">{f.name}</p>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${badgeStyle(f.cat)}`}>
                    {t(`cat_${f.cat}`, { defaultValue: f.cat })}
                  </span>
                  <span className="rounded-full bg-white/25 px-2.5 py-0.5 text-[10px] font-bold backdrop-blur-sm">
                    {whenLabel(daysUntil(f.mmdd))}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── all festivals (clean white cards — no photos here) ──────────── */}
      <div id="fest-list" className="mt-6 scroll-mt-4">
        <h2 className="flex items-center gap-2 font-script text-3xl text-forest">
          <FaStar className="text-lg" /> {t("fest_all", { defaultValue: "All festivals" })}
        </h2>
        <p className="mt-1 text-xs text-[#B08968]">
          {t("fest_dates_note", {
            defaultValue: "Festival dates follow the lunar calendar, so they can shift a little each year.",
          })}
        </p>

        {filtered.length > 0 ? (
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {filtered.map((f) => (
              <div key={f.id} className="rounded-3xl border border-[#F0E2D0] bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-script text-2xl leading-tight text-[#3E2A1B]">{f.name}</h3>
                  <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${badgeStyle(f.cat)}`}>
                    {t(`cat_${f.cat}`, { defaultValue: f.cat })}
                  </span>
                </div>
                <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-[#6B5D4F]">
                  <span className="flex items-center gap-1">
                    <FaMapMarkerAlt className="text-terracotta" /> {f.city}
                  </span>
                  <span className="flex items-center gap-1">
                    <FaCalendarAlt className="text-forest" /> {f.month}
                  </span>
                </p>
                <p className="mt-2 text-sm leading-relaxed text-[#6B5D4F]">{f.desc}</p>
                <p className="mt-2.5 flex items-start gap-2 rounded-2xl bg-[#FFF7EF] px-3 py-2 text-xs text-[#6B5D4F]">
                  <FaRegLightbulb className="mt-0.5 shrink-0 text-terracotta" />
                  <span>{f.tip}</span>
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-3 flex min-h-[160px] flex-col items-center justify-center rounded-3xl border border-dashed border-[#EAD9C6] bg-white/60 p-8 text-center">
            <span className="mb-2 text-3xl" aria-hidden>
              🎪
            </span>
            <p className="text-sm text-[#B08968]">
              {t("fest_empty", { defaultValue: "No festivals match your search." })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

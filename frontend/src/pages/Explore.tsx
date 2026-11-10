import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from 'react-leaflet'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import type { Place } from '../api/client'
import { FaSearch, FaArrowRight, FaMapMarkerAlt, FaRegClock, FaPaw, FaWater, FaMountain, FaGopuram, FaUniversity, FaCompass, FaSlidersH } from 'react-icons/fa'
import { useLocalized } from '../api/useLocalized'
import PageHero from '../components/PageHero'

const COLORS: Record<string, string> = {
  heritage: '#8e44ad', beach: '#e67e22', nature: '#27ae60',
  wildlife: '#16a085', museum: '#2980b9', other: '#7f8c8d',
}

const MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

// Turns a best_time string (e.g. "October - February") into quarter numbers 0-3.
// If no month name is recognised it returns true (treated as "all year", never filtered out).
function inQuarter(bestTime: string | undefined, quarter: number) {
  if (!bestTime) return true
  const s = bestTime.toLowerCase()
  const found = MONTHS.map((m, i) => (s.includes(m) ? i : -1)).filter(i => i >= 0)
  if (found.length === 0) return true
  return found.some(m => Math.floor(m / 3) === quarter)
}

const CATS: { key: string; icon: any }[] = [
  { key: 'All', icon: FaCompass },
  { key: 'heritage', icon: FaGopuram },
  { key: 'beach', icon: FaWater },
  { key: 'nature', icon: FaMountain },
  { key: 'wildlife', icon: FaPaw },
  { key: 'museum', icon: FaUniversity },
  { key: 'other', icon: FaMapMarkerAlt },
]

export default function Explore() {
  const { t } = useTranslation()
  const [places, setPlaces] = useState<Place[]>([])
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('All')
  const [sel, setSel] = useState<Place | null>(null)
  const [qInput, setQInput] = useState('')          // what's currently typed in the box
  const [city, setCity] = useState('All')           // the "All Locations" dropdown
  const [timeQ, setTimeQ] = useState<number[]>([])  // checked quarters 0-3
  const [favs, setFavs] = useState<string[]>(() => JSON.parse(localStorage.getItem('uy_favs') ?? '[]'))

  const toggleFav = (id: string) => {
    const next = favs.includes(id) ? favs.filter(f => f !== id) : [...favs, id]
    setFavs(next)
    localStorage.setItem('uy_favs', JSON.stringify(next))
  }

  // details-panel description: AI-translated per the UI language
  const [selDesc, selTr] = useLocalized(sel?.description)

  // 1. Load the grid (refetches on search/category change)
  useEffect(() => {
    api.places(q, cat).then(setPlaces).catch(console.error)
  }, [q, cat])

  // 2. Landmark handoff: open the saved place's details after first fetch
  useEffect(() => {
    if (places.length === 0) return            // wait until the first fetch lands
    const saved = localStorage.getItem('selected_place_id')
    if (!saved) return
    const fromList = places.find(p => p.place_id === saved)
    if (fromList) setSel(fromList)             // use the fetched object (no extra call)
    else api.place(saved).then(setSel).catch(console.error)
    localStorage.removeItem('selected_place_id')
  }, [places])

  // City and season filters are "frontend-only": just pick from the places we already have
  const cities = ['All', ...Array.from(new Set(places.map(p => p.city).filter(Boolean)))]
  const shown = places
    .filter(p => city === 'All' || p.city === city)
    .filter(p => timeQ.length === 0 || timeQ.some(qt => inQuarter(p.best_time, qt)))

  return (
    <div>
      {/* ── Hero banner (shared PageHero) + Explore's pill search bar ── */}
      <PageHero title={t('explore_title')} tagline={t('explore_tag')} desc={t('explore_desc')} quote={t('explore_quote')}>
        <form onSubmit={e => { e.preventDefault(); setQ(qInput) }}
          className="flex max-w-3xl flex-wrap items-center gap-2 rounded-full bg-white p-2 pl-5 shadow-xl">
          <FaSearch className="shrink-0 text-gray-400" />
          <input
            value={qInput}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQInput(e.target.value)}
            placeholder={t('search_ph')}
            className="min-w-[8rem] flex-1 bg-transparent text-sm text-[#3E2A1B] outline-none"
          />
          <select
            value={city}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCity(e.target.value)}
            className="rounded-full border border-gray-200 p-2 text-sm text-[#3E2A1B]"
          >
            {cities.map(c => <option key={c} value={c}>{c === 'All' ? t('all_locations') : c}</option>)}
          </select>
          <button type="submit"
            className="flex items-center gap-2 rounded-full bg-forest px-6 py-2.5 text-sm font-semibold text-white hover:opacity-90">
            {t('search')} <FaArrowRight size={13} />
          </button>
        </form>
      </PageHero>

      {/* ── Category chips ── */}
      <div className="flex flex-wrap justify-center gap-3 py-6 sm:gap-4">
        {CATS.map(c => (
          <button key={c.key} onClick={() => setCat(c.key)}
            className={`flex w-20 flex-col items-center gap-1 rounded-2xl py-3 text-xs font-semibold transition sm:w-24
              ${cat === c.key ? 'bg-forest text-white shadow-lg' : 'bg-white text-[#3E2A1B] shadow hover:-translate-y-0.5'}`}>
            <c.icon size={22} />
            {c.key === 'All' ? t('cat_all') : t(`cat_${c.key}`)}
          </button>
        ))}
      </div>

      {/* ── Left filter sidebar + right content ── */}
      <div className="flex flex-col gap-6 px-4 pb-10 lg:flex-row">
        <aside className="w-full shrink-0 self-start rounded-2xl bg-sage p-5 lg:w-56">
          <h3 className="mb-3 flex items-center gap-2 font-script text-2xl text-forest">
            <FaSlidersH size={15} /> {t('filter')}
          </h3>
          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#3E2A1B]">{t('best_time')}</p>
          {['Jan - Mar', 'Apr - Jun', 'Jul - Sep', 'Oct - Dec'].map((label, i) => (
            <label key={label} className="flex items-center gap-2 py-1 text-sm text-[#3E2A1B]">
              <input
                type="checkbox"
                checked={timeQ.includes(i)}
                onChange={() => setTimeQ(timeQ.includes(i) ? timeQ.filter(x => x !== i) : [...timeQ, i])}
              />
              {label}
            </label>
          ))}
        </aside>

        <section className="min-w-0 flex-1">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-script text-4xl text-forest">🌿 {t('popular_places')}</h2>
            <button onClick={() => { setCat('All'); setCity('All'); setTimeQ([]) }}
              className="text-sm font-semibold text-forest hover:underline">
              {t('view_all')} →
            </button>
          </div>

          {sel && (
            <div className="card mb-4 grid md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <button onClick={() => setSel(null)} className="text-terracotta mb-2">
                  ← {t('nav_explore')}
                </button>
                <h2 className="text-2xl font-bold">{sel.name}</h2>
                <p className="text-sm text-gray-500 mb-2">{sel.city} · {sel.category}</p>
                {sel.best_time && (
                  <div className="bg-blue-50 text-blue-800 rounded p-2 mb-2">
                    🗓️ {t('best_time')}: <b>{sel.best_time}</b>
                  </div>
                )}
                <p>
                  {selDesc}
                  {selTr && <span className="text-xs text-gray-400"> 🌐</span>}
                </p>
                {sel.insider_tip && (
                  <div className="bg-amber-50 rounded p-2 mt-2">
                    🗝️ <b>{t('insider_tip')}:</b> {sel.insider_tip}
                  </div>
                )}
              </div>
              {sel.image ? (
                <img src={sel.image} className="rounded-lg object-cover h-56 w-full" alt={sel.name} />
              ) : (
                <div className="rounded-lg flex items-center justify-center text-6xl h-56"
                  style={{ background: `${COLORS[sel.category] ?? '#888'}33` }}>
                  🏛️
                </div>
              )}
            </div>
          )}

          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {shown.slice(0, 24).map(p => (
              <ExploreCard key={p.place_id} p={p}
                fav={favs.includes(p.place_id)}
                onFav={() => toggleFav(p.place_id)}
                onOpen={() => setSel(p)} />
            ))}
          </div>
        </section>
      </div>

      <MapContainer center={[20.35, 85.30]} zoom={7} className="z-0 mb-4 h-96 w-full rounded-2xl">
        <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ClickPick onPick={(lat, lng) => api.nearby(lat, lng, 5).then(n => n[0] && setSel(n[0]))} />
        {shown.map(p => (
          <CircleMarker
            key={p.place_id}
            center={[p.lat, p.lon]}
            radius={6}
            pathOptions={{ color: COLORS[p.category] ?? '#3388ff', fillOpacity: 0.9 }}
            eventHandlers={{ click: () => setSel(p) }}
          >
            <Popup>
              <b>{p.name}</b><br />{(p.description ?? '').slice(0, 120)}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}

function ClickPick({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: e => onPick(e.latlng.lat, e.latlng.lng) })
  return null
}

// The reference-style "photo card": the whole card is the photo,
// text floats on a dark gradient at the bottom
function ExploreCard({ p, fav, onFav, onOpen }: {
  p: Place; fav: boolean; onFav: () => void; onOpen: () => void
}) {
  const { t } = useTranslation()
  return (
    <div onClick={onOpen} className="group relative h-60 cursor-pointer overflow-hidden rounded-2xl shadow-md">
      {p.image ? (
        <img src={p.image} alt={p.name} loading="lazy"
          className="absolute inset-0 h-full w-full object-cover transition duration-300 group-hover:scale-105" />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-6xl"
          style={{ background: `linear-gradient(135deg, ${(COLORS[p.category] ?? '#888')}33, ${(COLORS[p.category] ?? '#888')}77)` }}>
          🏛️
        </div>
      )}

      {/* Darken from the bottom up so white text stays readable */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/15 to-black/25" />

      <span className="absolute left-3 top-3 rounded-full bg-black/45 px-3 py-1 text-xs font-semibold text-white backdrop-blur-sm">
        {t(`cat_${p.category}`)}
      </span>
      <button
        onClick={e => { e.stopPropagation(); onFav() }}
        className="absolute right-3 top-3 text-xl leading-none text-white drop-shadow"
        aria-label="favourite"
      >
        {fav ? '❤️' : '🤍'}
      </button>

      <div className="absolute inset-x-0 bottom-0 p-3 text-white">
        <div className="flex items-center gap-1.5 font-bold">
          <FaMapMarkerAlt className="shrink-0 text-sm" />
          <span className="truncate">{p.name}</span>
        </div>
        <div className="mt-0.5 flex items-center gap-1.5 text-xs text-white/85">
          <FaRegClock className="shrink-0" />
          <span className="truncate">{p.city}</span>
        </div>
      </div>
    </div>
  )
}
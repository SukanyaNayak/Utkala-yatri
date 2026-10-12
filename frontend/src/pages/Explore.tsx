import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from 'react-leaflet'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import type { Place } from '../api/client'

const COLORS: Record<string, string> = {
  heritage: '#8e44ad', beach: '#e67e22', nature: '#27ae60',
  wildlife: '#16a085', museum: '#2980b9', other: '#7f8c8d',
}

export default function Explore() {
  const { t } = useTranslation()
  const [places, setPlaces] = useState<Place[]>([])
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('All')
  const [sel, setSel] = useState<Place | null>(null)

  useEffect(() => {
    api.places(q, cat).then(setPlaces).catch(console.error)
  }, [q, cat])

  const desc = (p: Place) => p.description ?? ''

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">🗺️ {t('nav_explore')}</h1>
      <div className="flex gap-3 mb-4">
        <input
          value={q}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQ(e.target.value)}
          placeholder={t('search')}
          className="flex-1 rounded-lg border p-2 bg-white"
        />
        <select
          value={cat}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCat(e.target.value)}
          className="rounded-lg border p-2 bg-white"
        >
          {['All', 'heritage', 'beach', 'nature', 'wildlife', 'museum', 'other']
            .map(c => <option key={c}>{c}</option>)}
        </select>
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
            <p>{desc(sel)}</p>
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

      <MapContainer center={[20.35, 85.30]} zoom={7} className="h-96 rounded-xl mb-4 z-0">
        <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ClickPick onPick={(lat, lng) => api.nearby(lat, lng, 5).then(n => n[0] && setSel(n[0]))} />
        {places.map(p => (
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

      <div className="grid md:grid-cols-3 gap-4">
        {places.slice(0, 24).map(p => (
          <div key={p.place_id} className="card">
            <b>{p.name}</b>
            <p className="text-sm text-gray-500 mb-1">{p.city} · {p.category}</p>
            <p className="text-sm">{desc(p).slice(0, 110)}…</p>
            <button onClick={() => setSel(p)} className="btn-primary mt-2 text-sm">
              {t('view_details')}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function ClickPick({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: e => onPick(e.latlng.lat, e.latlng.lng) })
  return null
}
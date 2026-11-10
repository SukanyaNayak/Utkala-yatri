// src/components/PlaceCard.tsx
import { useTranslation } from 'react-i18next'
import { useLocalized } from '../api/useLocalized'
import type { Place } from '../api/client'

const COLORS: Record<string, string> = {
  heritage: '#8e44ad', beach: '#e67e22', nature: '#27ae60',
  wildlife: '#16a085', museum: '#2980b9', other: '#7f8c8d',
}

export default function PlaceCard({ p, onView, full = false }:
  { p: Place; onView: () => void; full?: boolean }) {
  const { t } = useTranslation()
  const [d, tr] = useLocalized(p.description)

  return (
    <div className="card overflow-hidden p-0">           {/* p-0 so the image bleeds to edges */}
      {/* photo or category-tinted gradient header */}
      {p.image ? (
        <img src={p.image} alt={p.name} loading="lazy"
          className="w-full h-44 object-cover" />
      ) : (
        <div className="w-full h-44 flex items-center justify-center text-6xl"
          style={{ background: `linear-gradient(135deg, ${(COLORS[p.category] ?? '#888')}33, ${(COLORS[p.category] ?? '#888')}77)` }}>
          💎
        </div>
      )}

      <div className="p-4">
        <b>{p.name}</b>
        <p className="text-sm text-gray-500 mb-1">{p.city} · {p.category}</p>
        <p className="text-sm">
          {full ? d : d.slice(0, 110)}{(d.length > 110) ? '…' : ''}
        </p>
        {p.insider_tip && (
          <div className="bg-amber-50 rounded p-2 mt-2 text-sm">🗝️ {p.insider_tip}</div>
        )}
        {p.best_time && (
          <div className="bg-blue-50 text-blue-800 rounded p-2 mt-2 text-sm">
            🗓️ {t('best_time')}: <b>{p.best_time}</b>
          </div>
        )}
        <button onClick={onView} className="btn-primary mt-2 text-sm">{t('view_details')}</button>
        {tr && <span className="text-xs text-gray-400">🌐</span>}
      </div>
    </div>
  )
}
export interface Place {
  place_id: string; name: string; city?: string; district?: string;
  category: string; description?: string; best_time?: string;
  insider_tip?: string; image?: string; tags?: string[];
  lat: number; lon: number;
  distance_km?: number; lang_names?: Record<string, string>;
}
export interface Festival {
  festival_id: string; name: Record<string, string>; city: string;
  category: string; description: Record<string, string>;
  next_start?: string; next_end?: string; dates_approximate?: boolean;
  date_confidence?: string; typical_months?: number[];
  travel_tips?: Record<string, string>; is_hidden_gem?: boolean;
  location?: { coordinates: [number, number] };
}
export interface RouteResult {
  distance_km: number; duration_min: number;
  geometry: [number, number][]; provider: string;
}

const j = async (r: Response) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); }

// Baked at build time from frontend/.env.production (VITE_API_URL).
// Empty in dev → calls stay relative → Vite's dev proxy serves them (unchanged).
const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

export const api = {
  places: (q = '', category = 'All') =>
    fetch(`${API_BASE}/api/places?query=${encodeURIComponent(q)}&category=${category}`).then(j) as Promise<Place[]>,
  place: (id: string) => fetch(`${API_BASE}/api/places/${id}`).then(j) as Promise<Place>,
  nearby: (lat: number, lon: number, radius_km = 50) =>
    fetch(`${API_BASE}/api/places/near?lat=${lat}&lon=${lon}&radius_km=${radius_km}`).then(j) as Promise<Place[]>,
  reviewSummary: (id: string) =>
    fetch(`${API_BASE}/api/places/${id}/review-summary`).then(j) as Promise<{ summary: string }>,
  festivals: () => fetch(`${API_BASE}/api/festivals`).then(j) as Promise<Festival[]>,
  upcoming: (days = 90) =>
    fetch(`${API_BASE}/api/festivals/upcoming?days_ahead=${days}`).then(j) as Promise<Festival[]>,
  hotels: (lat: number, lon: number, radius_km = 25, band = 'All') =>
    fetch(`${API_BASE}/api/hotels/near?lat=${lat}&lon=${lon}&radius_km=${radius_km}&band=${band}`).then(j),
  emergency: (lat: number, lon: number) =>
    fetch(`${API_BASE}/api/emergency/near?lat=${lat}&lon=${lon}`).then(j),
  route: (origin: { lat: number; lon: number }, dest: { lat: number; lon: number }) =>
    fetch(`${API_BASE}/api/planner/route`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest }) }).then(j) as Promise<RouteResult>,
  chat: async (history: { role: string; content: string }[], lang: string) => {
    const r = await fetch(`${API_BASE}/api/chat`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ history, lang }) })
    return (await j(r)) as { reply: string }
  },
  transcribe: async (blob: Blob) => {
    const fd = new FormData(); fd.append('file', blob, 'q.wav')
    const r = await fetch(`${API_BASE}/api/voice/transcribe`, { method: 'POST', body: fd })
    return (await j(r)) as { text: string }
  },
  ttsUrl: (text: string, lang: string) =>
    `${API_BASE}/api/voice/tts?text=${encodeURIComponent(text)}&lang=${lang}`,
  landmark: async (file: File) => {
    const fd = new FormData(); fd.append('file', file)
    const r = await fetch(`${API_BASE}/api/landmark`, { method: 'POST', body: fd })
    return (await j(r)) as { matched_place_id: string | null; confidence: string; best_guess?: string; seen: string }
  },
  translate: async (text: string, lang: string) => {
    const r = await fetch(`${API_BASE}/api/translate?text=${encodeURIComponent(text)}&lang=${lang}`)
    return (await j(r)) as { text: string; was_translated: boolean }
  },
}
// src/App.tsx
import { Routes, Route, NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import Explore from './pages/Explore'
import Chat from './pages/Chat'
import Home from './pages/Home'
import Planner from './pages/Planner'
import Festivals from './pages/Festivals'
import Hotels from './pages/Hotels'
import Emergency from './pages/Emergency'
import Gems from './pages/Gems'
import Landmark from './pages/Landmark'
// Planner, Festivals, Hotels, Emergency, Gems, Landmark — phase B part 2

const NAV = [
  { to: '/', key: 'nav_home', icon: '🏠' },
  { to: '/explore', key: 'nav_explore', icon: '🗺️' },
  { to: '/chat', key: 'nav_chat', icon: '🤖' },
  { to: '/planner', key: 'nav_planner', icon: '📅' },
  { to: '/festivals', key: 'nav_festivals', icon: '🎪' },
  { to: '/hotels', key: 'nav_hotels', icon: '🏨' },
  { to: '/emergency', key: 'nav_emergency', icon: '🚨' },
  { to: '/gems', key: 'nav_gems', icon: '💎' },
  { to: '/landmark', key: 'nav_landmark', icon: '📷' },
]

const LANGS = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'or', label: 'ଓଡ଼ିଆ' },
]

export default function App() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 bg-cream p-4 hidden md:block">
        <div className="text-xl font-bold mb-4">🛕 UtkalaYatri</div>
        <nav>
          {NAV.map(n => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }: { isActive: boolean }) =>
                `block px-3 py-2 rounded-lg mb-1 ${
                  isActive ? 'bg-terracotta text-white' : 'hover:bg-cream-dark'
                }`}
            >
              {n.icon} {t(n.key)}
            </NavLink>
          ))}
        </nav>
        <LanguagePicker />
      </aside>

      <div className="flex-1">
        {/* mobile top bar */}
        <div className="md:hidden flex items-center justify-between p-3 bg-cream">
          <span className="font-bold">🛕 UtkalaYatri</span>
          <button onClick={() => setOpen(!open)} className="btn-primary">☰</button>
        </div>
        {open && (
          <nav className="md:hidden p-3 bg-cream">
            {NAV.map(n => (
              <NavLink key={n.to} to={n.to} onClick={() => setOpen(false)}
                className="block px-3 py-2">
                {n.icon} {t(n.key)}
              </NavLink>
            ))}
            <LanguagePicker />
          </nav>
        )}

        <main className="p-6 max-w-6xl mx-auto">
          <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/explore" element={<Explore />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/planner" element={<Planner />} />
              <Route path="/festivals" element={<Festivals />} />
              <Route path="/hotels" element={<Hotels />} />
              <Route path="/emergency" element={<Emergency />} />
              <Route path="/gems" element={<Gems />} />
              <Route path="/landmark" element={<Landmark />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function LanguagePicker() {
  const { i18n } = useTranslation()
  return (
    <div className="mt-6">
      <select
        value={i18n.language}
        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
          i18n.changeLanguage(e.target.value)
          localStorage.setItem('lang', e.target.value)
        }}
        className="w-full rounded-lg border p-2 bg-white"
      >
        {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
      </select>
    </div>
  )
}
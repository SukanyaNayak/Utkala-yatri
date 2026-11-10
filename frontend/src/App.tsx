import { useEffect, useState } from 'react'
import { Routes, Route, NavLink, Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Home from './pages/Home'
import Explore from './pages/Explore'
import Chat from './pages/Chat'
import Planner from './pages/Planner'
import Festivals from './pages/Festivals'
import Hotels from './pages/Hotels'
import Emergency from './pages/Emergency'
import Gems from './pages/Gems'
import Landmark from './pages/Landmark'

const NAV = [
  { to: '/', key: 'nav_home' },
  { to: '/explore', key: 'nav_explore' },
  { to: '/chat', key: 'nav_chat' },
  { to: '/planner', key: 'nav_planner' },
  { to: '/festivals', key: 'nav_festivals' },
  { to: '/hotels', key: 'nav_hotels' },
  { to: '/emergency', key: 'nav_emergency' },
  { to: '/gems', key: 'nav_gems' },
  { to: '/landmark', key: 'nav_landmark' },
]
const LANGS = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'or', label: 'ଓଡ଼ିଆ' },
]

function LanguagePicker() {
  const { i18n } = useTranslation()
  return (
    <select
      aria-label="Language"
      value={i18n.language?.slice(0, 2)}
      onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
        i18n.changeLanguage(e.target.value)
        localStorage.setItem('lang', e.target.value)
      }}
      className="rounded-lg border border-[#3E2A1B]/30 px-2 py-2 bg-white text-[#3E2A1B] text-sm shadow-sm">
      {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
    </select>
  )
}

export default function App() {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)   // top-bar menu dropdown
  const location = useLocation()
  const isHome = location.pathname === '/'

  const lang = i18n.language?.slice(0, 2)
  // script-appropriate font for the whole app (classes defined in index.css)
  const fontClass = lang === 'or' ? 'font-odia' : lang === 'hi' ? 'font-deva' : ''

  // keep <html lang> in sync so browsers pick correct glyphs
  useEffect(() => {
    if (lang) document.documentElement.lang = lang
  }, [lang])

  // tab title follows page + language
  useEffect(() => {
    const current = NAV.find(n => n.to === location.pathname)
    document.title = current
      ? `${t(current.key)} · ${t('app_name')}`
      : t('app_name')
  }, [location.pathname, i18n.language, t])

  // auto-close the menu after navigation
  useEffect(() => { setOpen(false) }, [location.pathname])

  return (
    <div className={`min-h-screen ${fontClass}`}>
      {/* ═══ TOP BAR (replaces the sidebar) ═══ */}
      {/* z-[1100] keeps it above Leaflet map panes on the Explore page */}
      <header className={`z-[1100] border-b ${isHome
  ? 'absolute top-0 inset-x-0 bg-transparent border-transparent text-white'
  : 'sticky top-0 bg-cream border-black/5'}`}>
        <div className="flex items-center gap-3 px-4 py-2">
          <Link to="/" aria-label="Home" className="mr-auto flex items-center">
            <img src="/logo.png" alt="Utkala Yatri" className="h-11 w-auto rounded-xl bg-white/85 p-0.5 shadow" />
          </Link>
         
          <LanguagePicker />

          <div className="relative">
            <button
              onClick={() => setOpen(!open)}
              aria-label="Menu"
              aria-expanded={open}
              className="btn-primary px-3">
              {open ? '✕' : '☰'}
            </button>

            {open && (
              <>
                {/* click-away layer */}
                <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                <nav className="absolute right-0 top-full mt-2 z-50 w-72 max-h-[80vh] overflow-y-auto
                rounded-xl bg-white shadow-xl border p-2 text-[#3E2A1B]">
                  {NAV.map(n => (
                    <NavLink key={n.to} to={n.to} end={n.to === '/'}
                      className={({ isActive }: { isActive: boolean }) =>
                      `block px-3 py-2 rounded-lg font-medium ${
                       isActive ? 'bg-[#D35400] text-white' : 'text-[#3E2A1B] hover:bg-cream-dark'}`}>
                      {t(n.key)}
                    </NavLink>
                ))}
                </nav>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="p-4 md:p-6 max-w-6xl mx-auto">
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
  )
}
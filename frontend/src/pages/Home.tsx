// Home.tsx — SIGN-IN BUILT IN (v6 — click canary + top-of-stack chip)
// ==========================================================
// Copy these contents over frontend/src/pages/Home.tsx (whole file).
//
// V6 CHANGE — "still the signin doesnot show anything": I rebuilt this page
//   in a REAL headless browser on my side and clicked through everything —
//   the chip opens the card, Sign Up creates the account, the chip flips to
//   the signed-in name, Sign out flips it back. Zero errors. The code path
//   is proven, so what's left is environment-side, and v6 arms two probes:
//   (1) the chip now sits at z-[9998] — ABOVE any invisible layer your app
//   might stretch over the top bar (a fixed transparent navbar shows the
//   chip through it but EATS its clicks — the classic "looks fine, click
//   dead" bug); (2) a TEMPORARY click canary: clicking Sign In pops a small
//   alert and logs "[ut] Sign In chip clicked" to the console.
//   • Alert shows AND the card opens → all working; tell me and the next
//     version removes the canary.
//   • Alert shows but NO card → tell me (very unlikely).
//   • NOTHING at all → the click never reaches the button: hard-refresh
//     first (Ctrl+Shift+R), then check whether OTHER buttons still work
//     (☰ menu, the 8 round tiles) and send an F12 → Console screenshot.
//
// V5 CHANGE — "the sign in button not working": two likely causes, both
//   fixed here. (1) The overlay used position:fixed INSIDE the page tree —
//   if any parent element uses transform / filter / backdrop-filter,
//   browsers trap fixed elements inside it and the overlay can end up
//   invisible (the click "works", nothing appears). It now mounts straight
//   on <body> via createPortal with z-[9999], so it always covers the
//   whole screen, above every navbar. The chip also got z-40 +
//   pointer-events-auto so no stray layer can swallow its click.
//   (2) If the card DOES open but "Sign In" rejects you: accounts are
//   per-browser (localStorage, no server) — you must create one via the
//   Sign Up tab first; the form now says so explicitly when this device
//   has no saved accounts. And hard-refresh once after pasting
//   (Ctrl+Shift+R) so no stale bundle runs.
//
// V4 CHANGE — "fix it adjust the button": your app's LOGO tile also lives at
//   the top-left, and the chip at left-3 landed UNDER it (only "…n In" was
//   visible). The chip now sits just RIGHT of the logo — left-24 ≈ 96px
//   from the edge, measured off your screenshot (the logo tile ends ≈76px)
//   — same top row, so it reads:  [logo] [Sign In] …… [ଓଡ଼ିଆ pill] [☰]
//
// V3 CHANGE — "here its double remove it": your app's navbar ALREADY has its
//   own language pill (ଓଡ଼ିଆ / English / हिन्दी) plus the ☰ menu button at
//   the top-right, and v2 added a SECOND language select right on top of
//   them. That select and its setLang code are now GONE from this file —
//   your navbar pill stays the one and only language control, untouched.
//
// V2 recap — the ENTIRE sign-in setup lives INSIDE this file (account
//   store, chip, full-screen overlay page): no `../SignIn` import, no
//   second file to copy. If you created frontend/src/SignIn.tsx while
//   troubleshooting, delete it or leave it — nothing imports it.
//
// WHAT'S INSIDE (all in this one file):
//   • orange Sign In chip in the hero's top-left row, just right of the
//     app logo (home page only).
//   • Sign In / Sign Up tabs, show-password toggle, inline validation
//     errors (English defaults; your auth_* i18n keys translate them).
//   • signed in, the chip flips to "name + Sign out" by itself; the
//     session survives refreshes and syncs across tabs.
//   • accounts live in localStorage ("ut_users" + "ut_user"), passwords
//     stored only as a simple hash. Demo-grade by design: per-browser,
//     no server. Real shared accounts → README section 6 backend set.
//
// ── your earlier changelog, kept ──
// quick-links strip now shows ALL 8 destinations in the
// same order as the nav menu (Home itself excluded — you're on it):
//   Explore Places → AI Travel Chat → Trip Planner → Festivals → Nearby Hotels
//   → Emergency → Hidden Gems → Landmark Scan
// Everything else (random api.places() hero photo, HERO_IMAGE export,
// tile routes, grid) is untouched.

export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { FaMapMarkedAlt, FaHotel, FaRoute, FaTheaterMasks, FaLifeRing, FaGem, FaComments, FaMonument } from 'react-icons/fa'
import { FaEye, FaEyeSlash, FaSignInAlt, FaSignOutAlt, FaTimes, FaUserCircle, FaUserPlus } from 'react-icons/fa'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useEffect, useState } from 'react'
// portal the sign-in overlay onto <body> — see the V5 note up top
import { createPortal } from 'react-dom'
import { api } from '../api/client'

const TILES = [
  { to: '/explore',   key: 'nav_explore',   Icon: FaMapMarkedAlt,  bg: 'bg-[#D35400]' },
  { to: '/chat',      key: 'nav_chat',      Icon: FaComments,      bg: 'bg-teal-600' },
  { to: '/planner',   key: 'nav_planner',   Icon: FaRoute,         bg: 'bg-sky-600' },
  { to: '/festivals', key: 'nav_festivals', Icon: FaTheaterMasks,  bg: 'bg-purple-600' },
  { to: '/hotels',    key: 'nav_hotels',    Icon: FaHotel,         bg: 'bg-green-600' },
  { to: '/emergency', key: 'nav_emergency', Icon: FaLifeRing,      bg: 'bg-red-600' },
  { to: '/gems',      key: 'nav_gems',      Icon: FaGem,           bg: 'bg-amber-500' },
  { to: '/landmark',  key: 'nav_landmark',  Icon: FaMonument,      bg: 'bg-pink-600' },
]

// ═══════════════════════════════════════════════════════════════════════════
//  THE SIGN-IN SETUP — all local to this file, imports nothing new
// ═══════════════════════════════════════════════════════════════════════════

interface Account {
  name: string
  email: string
  hash: string // djb2 of the password — demo-grade, see the header note
}

type StoredUser = { name: string; email: string }

function lsGet(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null // private mode / storage disabled
  }
}

function lsSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* private mode */
  }
}

/** djb2 — a plain demo hash so the raw password never sits on disk. */
function demoHash(s: string): string {
  let h = 5381
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0
  return String(h)
}

function readAccounts(): Account[] {
  try {
    const raw = lsGet('ut_users')
    return raw ? (JSON.parse(raw) as Account[]) : []
  } catch {
    return []
  }
}

function readUser(): StoredUser | null {
  try {
    const raw = lsGet('ut_user')
    return raw ? (JSON.parse(raw) as StoredUser) : null
  } catch {
    return null
  }
}

/** tell every mounted chip that the session changed */
function announce(): void {
  try {
    window.dispatchEvent(new Event('ut-auth'))
  } catch {
    /* very old browser — the chip just won't auto-refresh */
  }
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/** Returns an i18n error key, or null on success (session is set). */
function signUp(name: string, email: string, pass: string): string | null {
  if (!name.trim()) return 'auth_err_name'
  if (!EMAIL_RE.test(email)) return 'auth_err_email'
  if (pass.length < 8) return 'auth_err_password'
  const accounts = readAccounts()
  if (accounts.some((a) => a.email.toLowerCase() === email.toLowerCase()))
    return 'auth_err_exists'
  accounts.push({ name: name.trim(), email: email.trim(), hash: demoHash(pass) })
  lsSet('ut_users', JSON.stringify(accounts))
  lsSet('ut_user', JSON.stringify({ name: name.trim(), email: email.trim() }))
  announce()
  return null
}

/** Returns an i18n error key, or null on success (session is set). */
function signIn(email: string, pass: string): string | null {
  if (!EMAIL_RE.test(email)) return 'auth_err_email'
  const account = readAccounts().find(
    (a) => a.email.toLowerCase() === email.toLowerCase(),
  )
  if (!account || account.hash !== demoHash(pass)) return 'auth_err_invalid'
  lsSet('ut_user', JSON.stringify({ name: account.name, email: account.email }))
  announce()
  return null
}

function signOut(): void {
  try {
    localStorage.removeItem('ut_user')
  } catch {
    /* private mode */
  }
  announce()
}

/** The chip subscribes here (plus the native storage event). */
function useSignedIn(): StoredUser | null {
  const [user, setUser] = useState<StoredUser | null>(() => readUser())
  useEffect(() => {
    const sync = () => setUser(readUser())
    window.addEventListener('ut-auth', sync)
    window.addEventListener('storage', sync) // another tab signed in/out
    return () => {
      window.removeEventListener('ut-auth', sync)
      window.removeEventListener('storage', sync)
    }
  }, [])
  return user
}

/** The shared form — used by the overlay below. */
function AuthForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation()
  const [tab, setTab] = useState<'in' | 'up'>('in')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [pass, setPass] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [errKey, setErrKey] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const switchTab = (next: 'in' | 'up') => {
    setTab(next)
    setErrKey(null)
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    // a tick so the "Signing in…" state paints before the (instant) store call
    setTimeout(() => {
      const err = tab === 'in' ? signIn(email, pass) : signUp(name, email, pass)
      setBusy(false)
      if (err) setErrKey(err)
      else onDone()
    }, 50)
  }

  const field =
    'w-full rounded-lg border border-[#EAD9C6] bg-white px-3 py-2.5 text-sm text-[#3E2C1C] outline-none placeholder:text-[#B9A08A] focus:border-[#D35400]'

  return (
    <div className="w-full max-w-sm">
      <div className="mb-5 text-center">
        <div className="text-4xl" aria-hidden>
          🛕
        </div>
        <h1 className="mt-2 font-[family-name:var(--font-display)] text-2xl font-bold text-[#5C2E0D]">
          {t('app_name', { defaultValue: 'Utkala Yatri' })}
        </h1>
        <p className="mt-1 text-sm font-semibold text-[#8A5A2B]">
          {tab === 'in'
            ? t('auth_welcome_back', { defaultValue: 'Welcome Back!' })
            : t('auth_create_account', { defaultValue: 'Create your account' })}
        </p>
      </div>

      {/* sign in / create account tabs */}
      <div className="mb-4 grid grid-cols-2 gap-1 rounded-xl bg-[#FFF3E4] p-1">
        <button
          type="button"
          onClick={() => switchTab('in')}
          className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition ${
            tab === 'in'
              ? 'bg-[#D35400] text-white shadow'
              : 'text-[#8A5A2B] hover:bg-white/60'
          }`}
        >
          <FaSignInAlt aria-hidden />
          {t('auth_signin', { defaultValue: 'Sign In' })}
        </button>
        <button
          type="button"
          onClick={() => switchTab('up')}
          className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition ${
            tab === 'up'
              ? 'bg-[#D35400] text-white shadow'
              : 'text-[#8A5A2B] hover:bg-white/60'
          }`}
        >
          <FaUserPlus aria-hidden />
          {t('auth_signup', { defaultValue: 'Sign Up' })}
        </button>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-3">
        {tab === 'up' && (
          <label className="block">
            <span className="mb-1 block text-xs font-bold text-[#8A5A2B]">
              {t('auth_name', { defaultValue: 'Full name' })}
            </span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              autoComplete="name"
              placeholder={t('auth_name', { defaultValue: 'Full name' })}
              className={field}
            />
          </label>
        )}

        <label className="block">
          <span className="mb-1 block text-xs font-bold text-[#8A5A2B]">
            {t('auth_email', { defaultValue: 'Email' })}
          </span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus={tab === 'in'}
            autoComplete="email"
            placeholder="you@example.com"
            className={field}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-bold text-[#8A5A2B]">
            {t('auth_password', { defaultValue: 'Password' })}
          </span>
          <span className="relative block">
            <input
              type={showPw ? 'text' : 'password'}
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              autoComplete={tab === 'in' ? 'current-password' : 'new-password'}
              placeholder={tab === 'up' ? t('auth_password_hint', { defaultValue: 'At least 8 characters' }) : '••••••••'}
              className={`${field} pr-10`}
            />
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              aria-label={showPw ? 'Hide password' : 'Show password'}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[#B9A08A] hover:text-[#8A5A2B]"
            >
              {showPw ? <FaEyeSlash aria-hidden /> : <FaEye aria-hidden />}
            </button>
          </span>
        </label>

        {errKey && (
          <p
            role="alert"
            className="rounded-lg bg-red-50 px-3 py-2 text-sm font-semibold text-[#C0392B]"
          >
            {t(errKey, { defaultValue: 'Something went wrong. Please try again.' })}
          </p>
        )}

        {/* sign-in failed and this device has no saved accounts → say so,
            instead of leaving "Invalid email or password" unexplained */}
        {tab === 'in' && errKey === 'auth_err_invalid' && readAccounts().length === 0 && (
          <p className="rounded-lg bg-[#FFF3E4] px-3 py-2 text-xs font-semibold text-[#8A5A2B]">
            {t('auth_no_accounts_hint', {
              defaultValue:
                'No accounts exist on this device yet — switch to the Sign Up tab and create one first.',
            })}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="mt-1 w-full rounded-lg bg-[#D35400] px-4 py-2.5 text-sm font-bold text-white shadow transition hover:bg-[#B84700] disabled:opacity-60"
        >
          {busy
            ? tab === 'in'
              ? t('auth_signing_in', { defaultValue: 'Signing in…' })
              : t('auth_creating', { defaultValue: 'Creating account…' })
            : tab === 'in'
              ? t('auth_signin', { defaultValue: 'Sign In' })
              : t('auth_signup', { defaultValue: 'Sign Up' })}
        </button>
      </form>

      <p className="mt-4 text-center text-xs text-[#8A5A2B]">
        {tab === 'in' ? (
          <>
            {t('auth_no_account', { defaultValue: 'New to Utkala Yatri?' })}{' '}
            <button
              type="button"
              onClick={() => switchTab('up')}
              className="font-bold text-[#D35400] underline underline-offset-2"
            >
              {t('auth_signup', { defaultValue: 'Sign Up' })}
            </button>
          </>
        ) : (
          <>
            {t('auth_have_account', { defaultValue: 'Already have an account?' })}{' '}
            <button
              type="button"
              onClick={() => switchTab('in')}
              className="font-bold text-[#D35400] underline underline-offset-2"
            >
              {t('auth_signin', { defaultValue: 'Sign In' })}
            </button>
          </>
        )}
      </p>
    </div>
  )
}

/** The sign-in page, opening as a full-screen overlay over the hero. */
function SignInOverlay({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation()

  // ESC closes · body scroll locked while open
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [onClose])

  return (
    <div className="pointer-events-auto fixed inset-0 z-[9999]" role="dialog" aria-modal="true">
      <button
        type="button"
        aria-label={t('common_close', { defaultValue: 'Close' })}
        onClick={onClose}
        className="absolute inset-0 h-full w-full cursor-default bg-black/55"
      />
      <div
        onClick={(e) => e.stopPropagation()}
        className="absolute left-1/2 top-1/2 max-h-[92vh] w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl bg-[#FFF7EF] p-6 shadow-2xl"
      >
        <button
          type="button"
          onClick={onClose}
          aria-label={t('common_close', { defaultValue: 'Close' })}
          className="absolute right-3 top-3 rounded-lg p-2 text-[#8A5A2B] transition hover:bg-[#FFF3E4]"
        >
          <FaTimes aria-hidden />
        </button>
        <div className="flex justify-center">
          <AuthForm onDone={onClose} />
        </div>
      </div>
    </div>
  )
}

/**
 * The orange Sign In chip — top-left row of the hero, just right of the
 * app logo. Signed in, it becomes "name + Sign out". Clicking it opens
 * the overlay, which mounts on <body> through createPortal so no
 * transformed ancestor can trap or hide it. Defined right here in
 * Home.tsx, so it exists on the home page only — no other page can
 * render it.
 */
function SignInButton() {
  const { t } = useTranslation()
  const user = useSignedIn()
  const [open, setOpen] = useState(false)

  return (
    <>
      {user ? (
        <button
          type="button"
          onClick={signOut}
          title={t('auth_signout', { defaultValue: 'Sign out' })}
          className="flex h-10 items-center gap-2 rounded-lg bg-white px-3 text-sm font-bold text-[#C0392B] shadow-lg transition hover:bg-[#FFF3E4]"
        >
          <FaUserCircle aria-hidden />
          <span className="hidden max-w-[10rem] truncate sm:inline">
            {user.name}
          </span>
          <FaSignOutAlt aria-hidden />
        </button>
      ) : (
        <button
          type="button"
          onClick={() => {
            // TEMP v6 canary — proves the click reaches this button; the next
            // version removes it once the card is confirmed opening.
            console.log('[ut] Sign In chip clicked')
            window.alert(
              'Sign In clicked ✓ — the button works. The sign-in card should now be open.',
            )
            setOpen(true)
          }}
          className="flex h-10 items-center gap-2 rounded-lg bg-[#D35400] px-4 text-sm font-bold text-white shadow-lg transition hover:bg-[#B84700]"
        >
          <FaUserCircle aria-hidden />
          {t('auth_signin', { defaultValue: 'Sign In' })}
        </button>
      )}

      {/* portal → <body>: position:fixed can be trapped (made invisible) by
          transformed ancestors — mounting on <body> ends that class of bug.
          React context (i18n) still flows through the React tree. */}
      {open &&
        (typeof document === 'undefined'
          ? null
          : createPortal(<SignInOverlay onClose={() => setOpen(false)} />, document.body))}
    </>
  )
}

// ═══════════════ end of the sign-in setup ═══════════════

export default function Home() {
  const { t } = useTranslation()
  const [heroImg, setHeroImg] = useState<string | null>(null)

  // Option C: random place photo on every visit
  useEffect(() => {
    api.places().then(places => {
      const withImg = places.filter(p => p.image)
      if (withImg.length) {
        const pick = withImg[Math.floor(Math.random() * withImg.length)]
        setHeroImg(pick.image ?? null)
      }
    }).catch(() => {})
  }, [])

  return (
    <div className="-m-6">
      {/* ═══════════ HERO ═══════════ */}
      <section className="relative h-screen overflow-hidden mx-[calc(50%_-_50vw)]">
        {heroImg && (
          <img src={heroImg} alt="Odisha" className="absolute inset-0 w-full h-full object-cover" />
        )}
        <div className={`absolute inset-0 ${heroImg
          ? 'bg-gradient-to-b from-black/40 via-black/20 to-black/70'
          : 'bg-gradient-to-b from-[#F2B33D] via-[#E85D2A] to-[#7A2E1D]'}`} />

        {/* Sign In chip — top-left ROW, just right of the app logo: left-24
            (96px) clears the logo tile (≈76px wide, measured off your
            screenshot) and stays far from the ଓଡ଼ିଆ pill + ☰ at the
            top-right. z-[9998]: beats ANY invisible layer stretched over
            the top bar (a fixed transparent navbar lets the chip show
            through but eats its clicks). Home page only — setup is local. */}
        <header className="pointer-events-auto absolute left-24 top-3 z-[9998] sm:top-4">
          <SignInButton />
        </header>

        {/* title block */}
        <div className="absolute inset-x-0 top-[7%] flex flex-col items-center text-center px-4">

          <h1 className="text-white text-5xl md:text-7xl font-bold tracking-wide drop-shadow-lg">
            {t('app_name')}
          </h1>
          <p className="text-white/90 text-lg md:text-xl font-semibold tracking-[0.3em] mt-2 drop-shadow">
            {t('hero_tagline')}
          </p>
          <p className="hero-title text-white mt-3 drop-shadow-lg">{t('hero_title')}</p>
          <div className="flex gap-3 mt-6">
            <Link to="/explore" className="btn-primary">{t('hero_cta_explore')}</Link>
            <Link to="/chat" className="rounded-lg px-4 py-2 font-semibold bg-white/20 text-white border border-white/60 hover:bg-white/30 transition">
              🎙️ {t('hero_cta_ai')}
            </Link>
          </div>
        </div>

        {/* ═══ OPTIONS ON THE IMAGE ═══ — all 8 tiles, nav-menu order */}
        <div className="absolute inset-x-0 bottom-4 px-4">
          <div className="max-w-4xl mx-auto grid grid-cols-4 md:grid-cols-8 gap-4 md:gap-6 rounded-2xl bg-black/25 py-4 backdrop-blur-sm px-2">
            {TILES.map(tile => (
              <Link key={tile.key} to={tile.to} className="flex flex-col items-center group">
                <div className={`w-16 h-16 rounded-full ${tile.bg} text-white text-2xl flex items-center justify-center
                  shadow-lg group-hover:scale-110 group-hover:shadow-xl transition-transform`}>
                  <tile.Icon size={26} />
                </div>
                <span className="mt-2 text-xs sm:text-sm font-semibold text-white text-center drop-shadow">
                  {t(tile.key)}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
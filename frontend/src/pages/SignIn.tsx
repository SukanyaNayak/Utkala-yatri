// frontend/src/SignIn.tsx — THE WHOLE SIGN-IN SETUP IN ONE FILE (v2, backend edition)
// ====================================================================
// Copy this file's contents over frontend/src/SignIn.tsx (replace the
// whole file). Nothing else changes in your project — the exports are
// identical to v1, so the <SignInButton /> line in Home.tsx stays as-is.
//
// WHAT CHANGED vs v1 (localStorage-only demo)
//   • signUp / signIn now call the REAL backend:
//       POST {API}/api/auth/signup  and  POST {API}/api/auth/login
//     Accounts are stored server-side in MongoDB (auth_backend.py +
//     MONGODB_URI on Render). Any visitor on any device/browser shares
//     the same account list — a redeploy no longer wipes anything.
//   • A successful call stores the JWT in localStorage ("utk_token")
//     and the display profile in "ut_user" (same key as v1, so the chip
//     behaviour is unchanged). The token lets a future "/me" or saved-
//     itinerary endpoint identify the user.
//   • Errors still surface as the SAME i18n keys (auth_err_exists,
//     auth_err_invalid, auth_err_name…) — they just come from the
//     backend now, so en/hi/or translations keep working untouched.
//   • The tiny offline fallback: if the backend can't be reached
//     (network down, Render waking from its free-tier sleep), the form
//     shows auth_err_generic instead of crashing.
//
// BACKEND CHECKLIST (one-time)
//   1. backend main.py includes auth_backend's auth_router (the kit's
//      main-complete.py already does).
//   2. The MongoDB version of auth_backend.py is on the server with
//      MONGODB_URI set (Render → Environment).
//   3. The frontend knows the backend URL:
//      • dev: nothing to do — Vite proxies /api to :8000 (or set
//        VITE_API_URL=http://localhost:8000 in frontend/.env.local if
//        your vite.config.ts has no /api proxy).
//      • prod (Netlify): Site configuration → Environment variables →
//        add VITE_API_URL = your Render URL, then redeploy. (This is
//        the same variable the rest of the app already uses.)
//
// WHAT'S STILL IN THIS ONE FILE
//   • <SignInButton /> (named export) — the orange chip on the HOME page.
//   • <SignIn /> (default export) — the same form as a standalone page.
//   • signUp / signIn / signOut / useSignedIn — now thin async wrappers
//     around the backend API.
//
// HONEST SCOPE: real shared accounts in MongoDB, passwords bcrypt-hashed
// server-side, sessions are JWT bearer tokens valid 7 days. The token
// sits in localStorage (standard for demos/small apps; XSS on your site
// could read it — upgrade to httpOnly cookies if that ever matters).

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  FaEye,
  FaEyeSlash,
  FaSignInAlt,
  FaSignOutAlt,
  FaTimes,
  FaUserCircle,
  FaUserPlus,
} from "react-icons/fa";

// ── the account store (backend API) ─────────────────────────────────────────

type StoredUser = { name: string; email: string };

/** Backend origin — same pattern as the app's api client. */
const API_BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

function lsGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null; // private mode / storage disabled
  }
}
function lsSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode */
  }
}

function readUser(): StoredUser | null {
  try {
    const raw = lsGet("ut_user");
    return raw ? (JSON.parse(raw) as StoredUser) : null;
  } catch {
    return null;
  }
}

/** tell every mounted chip (and this page) that the session changed */
function announce(): void {
  try {
    window.dispatchEvent(new Event("ut-auth"));
  } catch {
    /* very old browser — the chip just won't auto-refresh */
  }
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** POST to the auth endpoint; returns the parsed body or an i18n error key. */
async function callAuth(
  path: string,
  payload: Record<string, string>,
): Promise<{ ok: true; data: { token: string; user: StoredUser } } | { ok: false; error: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const detail = data && typeof data.detail === "string" ? data.detail : "";
      return { ok: false, error: detail || "auth_err_generic" };
    }
    return { ok: true, data: data as { token: string; user: StoredUser } };
  } catch {
    return { ok: false, error: "auth_err_generic" }; // network down / Render asleep
  }
}

function storeSession(data: { token: string; user: StoredUser }): void {
  lsSet("ut_user", JSON.stringify({ name: data.user.name, email: data.user.email }));
  lsSet("utk_token", data.token);
  announce();
}

/** Returns an i18n error key, or null on success (session is set). */
export async function signUp(name: string, email: string, pass: string): Promise<string | null> {
  // client-side checks first — instant feedback, identical keys to the backend
  if (!name.trim()) return "auth_err_name";
  if (!EMAIL_RE.test(email)) return "auth_err_email";
  if (pass.length < 8) return "auth_err_password";
  const res = await callAuth("signup", { name: name.trim(), email: email.trim(), password: pass });
  if (!res.ok) return res.error;
  storeSession(res.data);
  return null;
}

/** Returns an i18n error key, or null on success (session is set). */
export async function signIn(email: string, pass: string): Promise<string | null> {
  if (!EMAIL_RE.test(email)) return "auth_err_email";
  const res = await callAuth("login", { email: email.trim(), password: pass });
  if (!res.ok) return res.error;
  storeSession(res.data);
  return null;
}

export function signOut(): void {
  try {
    localStorage.removeItem("ut_user");
    localStorage.removeItem("utk_token");
  } catch {
    /* private mode */
  }
  announce();
}

/** The chip subscribes here (plus the native storage event). */
export function useSignedIn(): StoredUser | null {
  const [user, setUser] = useState<StoredUser | null>(() => readUser());
  useEffect(() => {
    const sync = () => setUser(readUser());
    window.addEventListener("ut-auth", sync);
    window.addEventListener("storage", sync); // another tab signed in/out
    return () => {
      window.removeEventListener("ut-auth", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);
  return user;
}

// ── the shared form (used by the overlay and the standalone page) ───────────

function AuthForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"in" | "up">("in");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [errKey, setErrKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const switchTab = (next: "in" | "up") => {
    setTab(next);
    setErrKey(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    const err = await (tab === "in" ? signIn(email, pass) : signUp(name, email, pass));
    setBusy(false);
    if (err) setErrKey(err);
    else onDone();
  };

  const field =
    "w-full rounded-lg border border-[#EAD9C6] bg-white px-3 py-2.5 text-sm text-[#3E2C1C] outline-none placeholder:text-[#B9A08A] focus:border-[#D35400]";

  return (
    <div className="w-full max-w-sm">
      <div className="mb-5 text-center">
        <div className="text-4xl" aria-hidden>
          🛕
        </div>
        <h1 className="mt-2 font-[family-name:var(--font-display)] text-2xl font-bold text-[#5C2E0D]">
          {t("app_name", { defaultValue: "Utkala Yatri" })}
        </h1>
        <p className="mt-1 text-sm font-semibold text-[#8A5A2B]">
          {tab === "in"
            ? t("auth_welcome_back", { defaultValue: "Welcome Back!" })
            : t("auth_create_account", { defaultValue: "Create your account" })}
        </p>
      </div>

      {/* sign in / create account tabs */}
      <div className="mb-4 grid grid-cols-2 gap-1 rounded-xl bg-[#FFF3E4] p-1">
        <button
          type="button"
          onClick={() => switchTab("in")}
          className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition ${
            tab === "in"
              ? "bg-[#D35400] text-white shadow"
              : "text-[#8A5A2B] hover:bg-white/60"
          }`}
        >
          <FaSignInAlt aria-hidden />
          {t("auth_signin", { defaultValue: "Sign In" })}
        </button>
        <button
          type="button"
          onClick={() => switchTab("up")}
          className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition ${
            tab === "up"
              ? "bg-[#D35400] text-white shadow"
              : "text-[#8A5A2B] hover:bg-white/60"
          }`}
        >
          <FaUserPlus aria-hidden />
          {t("auth_signup", { defaultValue: "Sign Up" })}
        </button>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-3">
        {tab === "up" && (
          <label className="block">
            <span className="mb-1 block text-xs font-bold text-[#8A5A2B]">
              {t("auth_name", { defaultValue: "Full name" })}
            </span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              autoComplete="name"
              placeholder={t("auth_name", { defaultValue: "Full name" })}
              className={field}
            />
          </label>
        )}

        <label className="block">
          <span className="mb-1 block text-xs font-bold text-[#8A5A2B]">
            {t("auth_email", { defaultValue: "Email" })}
          </span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus={tab === "in"}
            autoComplete="email"
            placeholder="you@example.com"
            className={field}
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-bold text-[#8A5A2B]">
            {t("auth_password", { defaultValue: "Password" })}
          </span>
          <span className="relative block">
            <input
              type={showPw ? "text" : "password"}
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              autoComplete={tab === "in" ? "current-password" : "new-password"}
              placeholder={tab === "up" ? t("auth_password_hint", { defaultValue: "At least 8 characters" }) : "••••••••"}
              className={`${field} pr-10`}
            />
            <button
              type="button"
              onClick={() => setShowPw((v) => !v)}
              aria-label={showPw ? "Hide password" : "Show password"}
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
            {t(errKey, { defaultValue: "Something went wrong. Please try again." })}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="mt-1 w-full rounded-lg bg-[#D35400] px-4 py-2.5 text-sm font-bold text-white shadow transition hover:bg-[#B84700] disabled:opacity-60"
        >
          {busy
            ? tab === "in"
              ? t("auth_signing_in", { defaultValue: "Signing in…" })
              : t("auth_creating", { defaultValue: "Creating account…" })
            : tab === "in"
              ? t("auth_signin", { defaultValue: "Sign In" })
              : t("auth_signup", { defaultValue: "Sign Up" })}
        </button>
      </form>

      <p className="mt-4 text-center text-xs text-[#8A5A2B]">
        {tab === "in" ? (
          <>
            {t("auth_no_account", { defaultValue: "New to Utkala Yatri?" })}{" "}
            <button
              type="button"
              onClick={() => switchTab("up")}
              className="font-bold text-[#D35400] underline underline-offset-2"
            >
              {t("auth_signup", { defaultValue: "Sign Up" })}
            </button>
          </>
        ) : (
          <>
            {t("auth_have_account", { defaultValue: "Already have an account?" })}{" "}
            <button
              type="button"
              onClick={() => switchTab("in")}
              className="font-bold text-[#D35400] underline underline-offset-2"
            >
              {t("auth_signin", { defaultValue: "Sign In" })}
            </button>
          </>
        )}
      </p>
    </div>
  );
}

// ── the overlay (the sign-in page that opens over the home page) ────────────

function SignInOverlay({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();

  // ESC closes · body scroll locked while open
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[60]" role="dialog" aria-modal="true">
      <button
        type="button"
        aria-label={t("common_close", { defaultValue: "Close" })}
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
          aria-label={t("common_close", { defaultValue: "Close" })}
          className="absolute right-3 top-3 rounded-lg p-2 text-[#8A5A2B] transition hover:bg-[#FFF3E4]"
        >
          <FaTimes aria-hidden />
        </button>
        <div className="flex justify-center">
          <AuthForm onDone={onClose} />
        </div>
      </div>
    </div>
  );
}

// ── the home-page chip (the only integration point) ─────────────────────────

/**
 * The orange chip next to the language select on the home hero. Signed in,
 * it becomes "name + Sign out". Renders nowhere unless a page imports it —
 * keep the import inside Home.tsx only, and it stays home-only.
 */
export function SignInButton() {
  const { t } = useTranslation();
  const user = useSignedIn();
  const [open, setOpen] = useState(false);

  return (
    <>
      {user ? (
        <button
          type="button"
          onClick={signOut}
          title={t("auth_signout", { defaultValue: "Sign out" })}
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
          onClick={() => setOpen(true)}
          className="flex h-10 items-center gap-2 rounded-lg bg-[#D35400] px-4 text-sm font-bold text-white shadow-lg transition hover:bg-[#B84700]"
        >
          <FaUserCircle aria-hidden />
          {t("auth_signin", { defaultValue: "Sign In" })}
        </button>
      )}

      {open && <SignInOverlay onClose={() => setOpen(false)} />}
    </>
  );
}

// ── optional standalone page (default export) ───────────────────────────────

/**
 * The same sign-in as a real page, if you prefer a URL over the overlay:
 *   <Route path="/login" element={<SignIn />} />
 * After signing in it shows a small welcome panel with a plain link home —
 * no router import needed, so this file stays dependency-free.
 */
export default function SignIn() {
  const { t } = useTranslation();
  const [user, setUser] = useState<StoredUser | null>(() => readUser());

  useEffect(() => {
    const sync = () => setUser(readUser());
    window.addEventListener("ut-auth", sync);
    return () => {
      window.removeEventListener("ut-auth", sync);
    };
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-[#F2B33D] via-[#E85D2A] to-[#7A2E1D] p-4">
      <div className="rounded-2xl bg-[#FFF7EF] p-6 shadow-2xl">
        {user ? (
          <div className="w-full max-w-sm text-center">
            <div className="text-4xl" aria-hidden>
              🛕
            </div>
            <p className="mt-3 text-sm font-semibold text-[#8A5A2B]">
              {t("auth_signed_in_as", { defaultValue: "Signed in as" })}
            </p>
            <p className="mt-1 text-xl font-bold text-[#5C2E0D]">{user.name}</p>
            <div className="mt-5 flex flex-col gap-2">
              <a
                href="/"
                className="rounded-lg bg-[#D35400] px-4 py-2.5 text-sm font-bold text-white shadow transition hover:bg-[#B84700]"
              >
                {t("nav_home", { defaultValue: "Home" })}
              </a>
              <button
                type="button"
                onClick={() => {
                  signOut();
                }}
                className="rounded-lg bg-white px-4 py-2.5 text-sm font-bold text-[#C0392B] shadow transition hover:bg-[#FFF3E4]"
              >
                {t("auth_signout", { defaultValue: "Sign out" })}
              </button>
            </div>
          </div>
        ) : (
          <AuthForm onDone={() => announce()} />
        )}
      </div>
    </div>
  );
}

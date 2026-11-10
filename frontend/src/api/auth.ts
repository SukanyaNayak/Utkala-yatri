/**
 * UtkalaYatri — auth API client (frontend/src/api/auth.ts)
 * Talks to the FastAPI auth backend through the same `/api` Vite proxy your
 * other endpoints use (vite.config.ts proxies /api → http://localhost:8000).
 *
 * The token is kept in localStorage ("Remember Me" ✓) or sessionStorage
 * (unchecked — cleared when the tab closes); the user object is cached too
 * so the UI can show the name instantly while /me re-validates in the
 * background.
 */

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

interface Session {
  token: string;
  user: AuthUser;
}

const TOKEN_KEY = "yatri_token";
const USER_KEY = "yatri_user";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function cachedUser(): AuthUser | null {
  try {
    const raw =
      localStorage.getItem(USER_KEY) ?? sessionStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch {
    /* private mode — ignore */
  }
}

/**
 * All backend errors carry an i18n key in `detail`
 * (auth_err_invalid, auth_err_exists, …) — thrown as err.code so the
 * Login page can translate them directly.
 */
async function call<T>(path: string, body?: unknown, token?: string | null): Promise<T> {
  const res = await fetch(`/api/auth/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  const data = (await res.json().catch(() => ({}))) as { detail?: string };
  if (!res.ok) {
    const err = new Error(data.detail ?? "auth_err_generic") as Error & { code: string };
    err.code = data.detail ?? "auth_err_generic";
    throw err;
  }
  return data as T;
}

/**
 * remember=true  → token in localStorage (survives browser restarts)
 * remember=false → token in sessionStorage (cleared when the tab closes)
 * This is what the "Remember Me" checkbox on the Login page controls.
 */
function saveSession(s: Session, remember: boolean): void {
  try {
    const store = remember ? localStorage : sessionStorage;
    store.setItem(TOKEN_KEY, s.token);
    store.setItem(USER_KEY, JSON.stringify(s.user));
  } catch {
    /* private mode — session works, just not persisted */
  }
}

export const authApi = {
  async signup(
    name: string,
    email: string,
    password: string,
    remember = true,
  ): Promise<AuthUser> {
    const s = await call<Session>("signup", { name, email, password });
    saveSession(s, remember);
    return s.user;
  },

  async login(
    email: string,
    password: string,
    remember = true,
  ): Promise<AuthUser> {
    const s = await call<Session>("login", { email, password });
    saveSession(s, remember);
    return s.user;
  },

  /** Re-validate the stored token; throws (code auth_err_invalid) if stale. */
  async me(): Promise<AuthUser> {
    const d = await call<{ user: AuthUser }>("me", undefined, getToken());
    return d.user;
  },
};
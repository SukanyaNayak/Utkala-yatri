# 🛕 Utkala Yatri

> **DISCOVER • PLAN • EXPERIENCE** — *Same Land, New Stories*

A full-stack travel companion for **Odisha, India**: explore curated destinations — the Konark Sun Temple, Jagannath Temple Puri, Chilika Lake, Daringbadi and more — plan trips, browse festivals, find hotels, check emergency helplines, and identify monuments from a photo. The whole app speaks **English, हिन्दी and ଓଡ଼ିଆ**.

🔗 **Live site:** <https://bespoke-kelpie-ef0389.netlify.app>

---

## ✨ What's inside

| Page | What it does |
| --- | --- |
| 🗺️ **Explore Places** | Searchable grid of 25 built-in Odisha destinations with photos, category/city/season filters, a Leaflet map with one pin per place, detail modal (hours, entry fees, insider tips) and ♥ favourites |
| 🤖 **AI Travel Chat** | Ask travel questions about Odisha in the app |
| 🧭 **Trip Planner** | Build and organise a day-by-day plan |
| 🎭 **Festivals** | Rath Yatra, Konark Dance Festival, Dhanu Yatra, Raja Parba, Makar Mela… with photos |
| 🏨 **Nearby Hotels** | Stays across Bhubaneswar, Puri and beyond |
| 💎 **Hidden Gems** | Lesser-known spots with the story behind each |
| 🆘 **Emergency** | Helplines and safety info at a glance |
| 📸 **Landmark Scan** | Upload a photo, AI identifies the monument (needs the backend + a Gemini key) |
| 🔐 **Sign in / Sign up** | Per-browser demo accounts out of the box; real shared accounts when the backend is running |

**Works without the backend:** browsing, Explore (offline dataset + photos), festivals, hotels, emergency, the sign-in demo (localStorage). **Needs the backend:** your own database places, real cross-device accounts, Landmark Scan AI.

---

## 🧰 Tech stack

- **Frontend:** React + TypeScript, Vite, Tailwind CSS, react-router-dom (SPA), react-i18next (3 languages), react-icons, Leaflet 1.9.4 (CDN)
- **Backend:** FastAPI + Uvicorn, bcrypt + PyJWT for auth, SQLite for users, optional Google Gemini API for landmark recognition

---

## 📁 Project structure

```
UtkalaYatri_scaffold/
├── frontend/                  # React + Vite SPA
│   ├── public/
│   │   └── _redirects         # SPA routing rule for Netlify (exact name — NO .txt)
│   ├── src/
│   │   ├── api/client.ts      # all backend calls (base URL → http://localhost:8000)
│   │   ├── components/        # PageHero and shared UI
│   │   └── pages/             # Home, Explore, Chat, Planner, Festivals,
│   │                          # Hotels, Emergency, Gems, Landmark
│   └── index.html
├── backend/
│   ├── main.py                # FastAPI app — /api/places, /api/health, /api/landmark, auth router
│   ├── auth_backend.py        # optional — real accounts (SQLite + bcrypt + JWT)
│   └── requirements.txt
├── deploy/                    # optional deploy configs — netlify.toml, vercel.json, deploy.yml
└── start-dev.ps1              # Windows helper — starts frontend + backend together
```

> 📸 **Screenshots:** drop 2–3 PNGs into a `docs/` folder and embed them here —
> `![Home](docs/screenshot-home.png)` · `![Explore](docs/screenshot-explore.png)`

---

## ✅ Prerequisites

| Tool | Version | Check it |
| --- | --- | --- |
| Node.js | 18 or newer | `node -v` |
| npm | ships with Node | `npm -v` |
| Python | 3.10+ recommended | `python --version` |
| Git | any recent | `git --version` |

**Windows users:** run commands in PowerShell, **one at a time** — pasting multi-line blocks silently fails.

---

## 🚀 Run it locally

### 1 · Get the code

Click the green **Code** button → **Download ZIP** and extract it, or clone:

```bash
git clone https://github.com/YOUR-USERNAME/utkala-yatri.git
cd utkala-yatri
```

*(Replace `YOUR-USERNAME` and the repo name with yours — or use the URL the Code button shows.)*

### 2 · Frontend (terminal 1)

```bash
cd frontend
npm install
npm run dev
```

→ open <http://localhost:5173> — `npm install` takes a few minutes the first time.

### 3 · Backend (terminal 2)

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

→ API docs: <http://127.0.0.1:8000/docs> · health check: <http://127.0.0.1:8000/api/health>

Notes:

- `auth_backend.py` is **optional at runtime** — the backend starts and serves `/api/places` even without it (real accounts just stay off).
- Explore works even with **no backend** (25 built-in places + hosted photos); when the backend answers `/api/places`, its data is merged in automatically.

**One-command alternative (Windows):** run `.\start-dev.ps1` from the project root to start both.

---

## 🔑 Environment variables

| Variable | Where | Needed for |
| --- | --- | --- |
| `GEMINI_API_KEY` | backend environment, set **before** starting uvicorn | Landmark Scan AI recognition |
| `VITE_API_URL` (optional) | frontend environment | override the API base URL — `api/client.ts` defaults to `http://localhost:8000` |

PowerShell example: `$env:GEMINI_API_KEY = "your-key"` in the backend terminal before starting uvicorn. A free Gemini key comes from Google AI Studio.

---

## ☁️ Deploying

### Frontend → Netlify Drop (~2 minutes, no commands beyond one build)

1. Make sure `frontend/public/_redirects` exists with this **one line** — and the file name is exactly `_redirects`, **not** `_redirects.txt`:

   ```
   /*    /index.html   200
   ```

2. Build: `cd frontend` → `npm run build` (check `dist/` now contains `_redirects`, `index.html`, `assets/`)
3. Drag the whole `dist` folder onto <https://app.netlify.com/drop> — live URL immediately
4. Sign up (free) to keep it; rename the site under Site settings if you like

*Alternatives: `deploy/vercel.json` for Vercel (`npm i -g vercel` → `vercel --prod`), or `deploy/deploy.yml` for GitHub Pages (Settings → Pages → Source: GitHub Actions; set the repo-name base path in `vite.config.ts`).*

### Backend → Render (free tier)

Netlify serves static files only — the FastAPI backend needs an always-on host. Render's free tier works:

1. Create a GitHub repo (e.g. `utkala-yatri-backend`) and upload: `main.py`, `requirements.txt`, and optionally `auth_backend.py`
2. In `main.py`, add your live site URL to the CORS list:

   ```python
   allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                  "https://bespoke-kelpie-ef0389.netlify.app"],
   ```

3. On <https://dashboard.render.com>: **New + → Web Service** → pick the repo →
   **Runtime:** Python 3 · **Build:** `pip install -r requirements.txt` ·
   **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. When it shows **Live**, test `https://YOUR-RENDER-URL/api/health` in a browser
5. Point the frontend at it, then rebuild + re-drop the `dist` folder:
   - `frontend/src/api/client.ts` — replace `http://localhost:8000` with the Render URL
   - `Explore.tsx` — paste the same URL into the `REMOTE_API` constant
   - (or leave the client alone and set a `VITE_API_URL` environment variable in Netlify → Site configuration → Environment variables)

### Honest caveats

- **Render free tier sleeps** after ~15 idle minutes — the first visitor waits ~50 seconds while it wakes
- **SQLite accounts are demo-grade** and reset when Render redeploys — fine for a demo, not for real users
- Landmark Scan needs `GEMINI_API_KEY` set in Render → Environment

---

## 🧯 Troubleshooting

| Symptom | Fix |
| --- | --- |
| "Popular Places" empty on the **live** site | Backend isn't deployed — deploy to Render (above), or browse on the built-in offline dataset |
| `localhost:8000` connection refused **locally** | The backend terminal isn't running (or crashed on startup) — start uvicorn again, watch for import errors |
| Browser console shows a **CORS** error on the live site | Your Netlify URL is missing from `allow_origins` in `main.py` — add it and redeploy the backend |
| Refreshing a deep link (e.g. `/explore`) gives **404** on Netlify | `_redirects` is missing or saved as `_redirects.txt` — rename it (no `.txt`), rebuild, re-drop |
| Site doesn't change after a redeploy | Hard-refresh: **Ctrl+Shift+R** (the browser cached the old build) |
| TS error "Cannot find module '../SignIn'" after pasting Home.tsx | Stale editor state — TypeScript: Restart TS Server (the current Home.tsx has no such import) |
| Sign-in card doesn't open | Hard-refresh first; if other buttons work but this one doesn't, send an F12 → Console screenshot |

---

## 🗺️ Roadmap

- Hosted database (MongoDB Atlas) so accounts and places survive redeploys
- Real cross-device sessions on the backend auth set
- More destinations, Odia audio guides, offline PWA mode

---

## 🙏 Credits

Built as a student showcase project. Odisha photography via free stock sources; maps by OpenStreetMap contributors + Leaflet; festivals and place data curated by hand.

## 📄 License

Not chosen yet — add one when you publish (MIT is the usual starting point: create a `LICENSE` file on GitHub via *Add file → Create new file → LICENSE*).

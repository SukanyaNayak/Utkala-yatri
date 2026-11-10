# UtkalaYatri Setup Guide

This guide covers the current React + FastAPI application and the original Streamlit application. The React frontend can be browsed without the backend, but API-backed features require the FastAPI server.

## Prerequisites

- Windows 10/11 with PowerShell (commands below use PowerShell)
- Python 3.10 or newer
- Node.js 20.19+ or 22.12+ with npm
- Git, if cloning the project
- Optional: MongoDB Atlas and a Google Gemini API key

Check installed versions from PowerShell:

```powershell
python --version
node --version
npm --version
git --version
```

## Get the Project

Clone the repository, or open the project folder if you already have it:

```powershell
git clone <repository-url>
cd UtkalaYatri_scaffold
```

Run the remaining commands from the project root unless a step says otherwise.

## Configure Environment Variables

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set values for the services you intend to use:

| Variable | Required for | Notes |
| --- | --- | --- |
| `MONGODB_URI` | MongoDB-backed data and accounts | Use the connection string from MongoDB Atlas. URL-encode special characters in the password. |
| `MONGODB_DB_NAME` | Main app data | Defaults to `utkalayatri`. |
| `MONGODB_DB` | Authentication database | Set this to the same database name as `MONGODB_DB_NAME` if using MongoDB auth. |
| `JWT_SECRET` | Stable login tokens | Optional locally; set a long random value for a persistent deployment. |
| `GEMINI_API_KEY` | AI chat, landmark recognition, and other Gemini features | Obtain a key from Google AI Studio. |
| `OPENROUTESERVICE_API_KEY` | OpenRouteService routing | Optional; routing may use the configured fallback provider. |
| `APP_ENV` | App mode | Defaults to `development`; use `production` for deployments. |

The React app's Vite configuration proxies `/api` requests to `http://localhost:8000`. For another API host, configure the frontend API URL as appropriate for the deployment.

Never commit `.env` or paste secret values into source files. The checked-in `.env.example` is safe to edit as a template, not as a place for real credentials.

## Run the React + FastAPI Application

Use two PowerShell terminals, both opened at the project root.

### 1. Create a Python environment

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

The execution-policy command is only needed if PowerShell blocks environment activation. Alternatively, run Python commands using `\.venv\Scripts\python.exe` without activating the environment.

### 2. Install backend dependencies and start the API

In the first terminal:

```powershell
python -m pip install -r backend/requirements.txt
Set-Location backend
python -m uvicorn main:app --reload --port 8000
```

The backend reads the root `.env` file. With MongoDB configured, you can optionally load the curated catalog into the database from a separate terminal at the project root:

```powershell
python scripts/seed_festivals.py
python scripts/seed_catalog.py
```

The checked-in JSON files under `data/` provide fallback data when MongoDB is unavailable. Authentication is disabled if its MongoDB initialization fails; data endpoints can still run with fallback data.

### 3. Install frontend dependencies and start the website

In the second terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally <http://localhost:5173>.

### 4. Verify the services

- Website: <http://localhost:5173>
- API documentation: <http://127.0.0.1:8000/docs>
- Health endpoint: <http://127.0.0.1:8000/api/health>

The health endpoint reports MongoDB status. A failed MongoDB check does not necessarily mean the API is down; JSON fallback data is available for supported endpoints.

## Run the Original Streamlit Application

The original multi-page Streamlit application is separate from the React frontend. From the project root, create and activate a Python environment as shown above, then install the root requirements and run:

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit, normally <http://localhost:8501>. The app uses the same root `.env` file. MongoDB and Gemini features require their respective credentials; JSON fallback data supports use without a database connection.

## Build and Check the Frontend

From the `frontend` directory:

```powershell
npm run lint
npm run build
```

The production frontend files are generated in `frontend/dist/`.

## Troubleshooting

- **`python` is not recognized:** install Python 3.10+ and enable the option to add Python to `PATH`, or use the Python launcher `py`.
- **PowerShell blocks activation:** run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, or use `\.venv\Scripts\python.exe` directly.
- **Frontend API requests fail:** make sure the backend is running on port 8000 and restart Vite after changing its configuration.
- **MongoDB connection fails:** verify the URI, Atlas network access rules, and database credentials. Encode special characters in the URI password.
- **Sign-up/login is unavailable:** confirm MongoDB is reachable and `MONGODB_DB` is set; the API logs whether auth initialized.
- **AI features report a key error:** set `GEMINI_API_KEY` in the root `.env`, then restart the backend.
- **npm commands fail after dependency changes:** run `npm install` again inside `frontend`.

## Project Layout

```text
backend/       FastAPI app, auth, and API routers
data/          Curated JSON data and raw source datasets
frontend/      React + TypeScript + Vite application
pages/         Streamlit pages
scripts/       Data import, enrichment, and maintenance scripts
services/      Shared business logic and external-service integrations
utils/         Configuration, localization, and shared utilities
```
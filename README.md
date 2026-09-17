# UtkalaYatri — AI Travel Companion for Odisha

A hackathon MVP built with Streamlit that will eventually grow into an
AI-powered travel planning assistant for Odisha, covering itineraries,
a conversational travel assistant, interactive maps, and route planning.

> **Status:** Week 1 scaffold. Core AI/maps/database features are not
> implemented yet — this is the base project structure only.

## Tech stack

| Layer            | Tool                                    |
|-------------------|------------------------------------------|
| UI                 | Streamlit                                |
| Database           | MongoDB Atlas                            |
| AI                 | Gemini API (Weeks 2+)                    |
| Maps               | Folium + OpenStreetMap (Weeks 2+)        |
| Routing            | OpenRouteService / OSRM (later)          |
| Future backend     | FastAPI (post-hackathon migration)       |
| Future frontend    | React (post-hackathon migration)         |

## Project structure

```
UtkalaYatri/
├── app.py                  # Streamlit entry point (UI + navigation only)
├── pages/                  # Additional Streamlit pages (multipage app)
├── services/                # External integrations: MongoDB, Gemini, maps, routing
│   ├── mongodb_service.py
│   └── __init__.py
├── utils/                   # Config + generic helpers (no business logic)
│   ├── config.py
│   ├── helpers.py
│   └── __init__.py
├── data/                    # Static/reference data (place info, etc.)
├── scripts/                 # One-off scripts (data seeding, migrations)
├── .streamlit/
│   └── config.toml          # Theme + server settings
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

**Design principle:** `app.py` and `pages/` contain UI code only.
Anything that talks to MongoDB, Gemini, or map/routing APIs lives in
`services/`. This split is intentional so that most of `services/`
and `utils/config.py` can be reused almost as-is when the project
migrates to a React + FastAPI stack after the hackathon.

## Setup (Windows / VS Code)

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

```powershell
copy .env.example .env
```

Then open `.env` in VS Code and fill in your MongoDB Atlas URI (and
later, your Gemini / OpenRouteService API keys).

### 4. Run the app

```powershell
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

## Roadmap

- **Week 1** ✅ Project scaffold, navigation, session state, styling
- **Week 2** MongoDB Atlas integration (destinations data model), Gemini chat assistant
- **Week 3** Folium + OpenStreetMap map view, itinerary generation, routing (OpenRouteService/OSRM)
- **Post-hackathon** Migrate to React (frontend) + FastAPI (backend), reusing `services/`
Place descriptions: Wikipedia contributors, CC BY-SA 4.0. Facility data © OpenStreetMap contributors. AI-generated text is marked in data.
UtkalaYatri — Explore Odisha Smarter with AI 🛕🌅
An AI-powered tourism assistant for Odisha, India — grounded in a curateddatabase, trilingual (English / हिन्दी / ଓଡ଼ିଆ), voice-enabled, anddemo-proven.

Features
Feature	What it does
🗺️ Place Explorer	231 places: search, category filters, click-to-select map, photos, details
🤖 AI Travel Chat	Gemini chatbot grounded in the app's own place & festival database
🎙️🔊 Voice mode	Speak questions (Gemini transcription), hear spoken answers (gTTS/edge-tts)
📅 Trip Planner	Multi-stop plans with real road routing, nearest-neighbour ordering, cost calculator
🎪 Festival guide	17 curated festivals with a 3-tier lunar-date honesty system (✅/🧮/📅)
🏨 Nearby Hotels	Distance-ranked hotels around any place, price-band filter
🚨 Emergency	National helplines + 3,350 OSM-mapped hospitals/police/fire with tel: links
💎 Hidden Gems	Editorially curated offbeat Odisha with insider tips
📷 Landmark Scan	Photo → landmark recognition constrained to the app's own database
🌐 Trilingual UI	One language setting drives nav, chrome, content, AI replies, and voice
📝 AI review summary	Attribute-based "what visitors say" digest, clearly labeled
Architecture
Streamlit (pages)  ← st.navigation router, single global language setting   └── services/            ← all business logic (portable to FastAPI)         ├── mongodb_service.py    (the only pymongo touchpoint)         ├── place / hotel / festival / chatbot / gemini /         │   routing / landmark / review / tts / stt / translate services         └── every service falls back to data/*.json if Atlas is unreachable   └── MongoDB Atlas        ← places, hotels, festivals, emergency (GeoJSON + 2dsphere)   └── Gemini API           ← chat, insights, transcription, landmark ID, translation   └── OSRM / OpenRouteService ← road routing (provider-configurable)
Run it
pip install -r requirements.txtcopy .env.example .env        # fill MONGODB_URI, GEMINI_API_KEY, GEMINI_MODELpython scripts/seed_festivals.py && python scripts/seed_catalog.pystreamlit run app.py
Data pipeline
scripts/fetch_*.py (OSM / Wikidata / Overpass) → build_dataset.py(clean, dedupe, normalize, GeoJSON) → data/*.json (source of truth) →seed_*.py (upsert to Atlas). Build-time AI enrichment fills content gaps(enrich_places.py, enrich_festivals.py) — reviewed via git before seeding.

Engineering notes (the interesting bits)
Lunar-calendar honesty: Odia festivals shift yearly with the tithi.Dates resolve verified → astronomically computed (±1 day) → typical monthwindow, and the UI badges each answer ✅/🧮/📅. The chatbot is instructed tonever state exact festival dates unless verified.
Model churn resilience: point-version Gemini model names retired twiceduring development; all code reads GEMINI_MODEL / -latest aliases withretry + fallback chains for 429/503, and fails fast with actionable errors.
Three-tier content provenance: hand_curated stories →wikipedia (CC BY-SA) → ai_enriched (expectation-voice, no inventedfacts). Every text and image record is tagged with its source.
No Odia TTS exists (tested Google, Microsoft Edge, and Gemini native —see scripts/check_tts.py): Odia is text-first; speech is planned viaBhashini / AI4Bharat Indic TTS.
Fine-tuning evaluated and rejected: knowledge changes with the data(new festivals, prices); facts live in MongoDB as the single source oftruth and ground generation through retrieval — fine-tuning would freezeknowledge and add staleness without adding capability.
Graceful degradation: with Atlas unreachable, every page serves fromthe JSON fallback — the demo cannot die with the database.
Quota-aware i18n: list views cap live translation calls (~30); thedetail view localizes on demand; festival content is natively trilingual.
Attributions
Facility data: © OpenStreetMap contributors (ODbL)
Place descriptions & photos: Wikipedia / Wikimedia Commons contributors (CC BY-SA 4.0)
AI-generated/translated content is provenance-tagged (*_source fields, 🌐 labels)
Routing: OSRM demo server / OpenRouteService
Roadmap
Bhashini integration for native Odia speech · FastAPI + React migration(services already isolated) · build-time full-content translation ·semantic (embedding) search over places · Wikidata-ID-based image matching.
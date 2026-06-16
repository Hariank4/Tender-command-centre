# MeraPath Tender Command Centre

AI-powered tender intelligence dashboard built during internship.

## How to run

1. cd tender-command-centre
2. source venv/bin/activate
3. python3 scraper.py     ← load tenders
4. python3 main.py        ← start server
5. Open http://localhost:8000

## Tech stack
- AI: Groq API (Llama 3.1) — free
- Backend: FastAPI + Python
- Database: SQLite
- Frontend: HTML/CSS/JS
# MeraPath Tender Command Centre

AI-powered government tender intelligence and bid management dashboard.
Built during internship at MeraPath Education Limited, June 2025.

## What it does
- Automatically scans government portals for new tenders
- AI reads each tender and checks MeraPath's eligibility
- Gives priority score, summary, and proposal structure
- Live dashboard with filters, search, and pipeline tracking
- Real-time alerts via WebSocket

## How to run

# Step 1 — activate environment
source venv/bin/activate

# Step 2 — load tenders into database
python3 scraper.py

# Step 3 — start the server
python3 main.py

# Step 4 — open browser
http://localhost:8000

## Tech stack
- AI Model : Groq API (Llama 3.1 8B) — free tier
- Backend  : FastAPI + Python
- Database : SQLite (tenders.db)
- Frontend : HTML + CSS + JavaScript
- Scraping : Playwright + httpx
- Alerts   : WebSocket (real-time)

## Project structure
database.py   — database setup and queries
ai.py         — Groq AI tender analysis
scraper.py    — tender pipeline runner
main.py       — FastAPI server (8 endpoints)
frontend/     — dashboard web interface
.env          — API keys (not committed to Git)

## Built by
B.Tech CSE (Generative AI) Intern
MeraPath Education Limited
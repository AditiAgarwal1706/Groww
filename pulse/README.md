# PULSE — Smart Market Watchlist
### *"An Attention Layer for Financial Markets"*

> *Your market. Your attention. Nothing unnecessary.*

---

## What is PULSE?

PULSE is an intelligent market watchlist that **remembers what you last saw**, **detects what meaningfully changed**, and **explains what deserves your attention** — so you don't have to monitor the market constantly.

**The core loop:**
```
User checks watchlist → PULSE saves state → Market moves
→ User returns → "3 meaningful changes since your last visit"
→ Click NVDA → See WHY it moved (AI + attribution + timeline)
```

---

## 🚀 Quick Start (Local Dev)

### Prerequisites
- Docker + Docker Compose
- Node.js 18+
- Python 3.12+

### 1. Setup environment
```bash
cd pulse
cp .env.example .env
# Edit .env with your API keys (all optional — works without them!)
```

### 2. Start with Docker
```bash
docker-compose up
```

### 3. Seed demo data
```bash
docker-compose exec backend python scripts/seed_demo_data.py
# Or locally:
cd backend && python -m scripts.seed_demo_data
```

### 4. Open the app
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Demo account:** `demo@pulse.app` / `Demo@2026!`

---

## 🛠 Manual Setup (No Docker)

### Backend
```bash
cd pulse/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Set up .env with DATABASE_URL, REDIS_URL
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd pulse/frontend
npm install
npm run dev
```

---

## 🔑 API Keys (All Optional — App Works Without Them)

| Key | Where to Get | Purpose |
|-----|-------------|---------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) (free) | AI explanations |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) (free 100 req/day) | Real news |
| `ALPHA_VANTAGE_API_KEY` | [alphavantage.co](https://alphavantage.co) (free 25 req/day) | Fallback market data |

**Without keys:** Uses `yfinance` (free, real data) + mock news + algorithmic explanations

---

## 🏗 Architecture

```
React (Vite + TypeScript)          ← Frontend
    ↕ REST API (JSON)
FastAPI (Python)                   ← Backend
    ↕
PostgreSQL + Redis                 ← Data layer
    ↕
yfinance / NewsAPI / Gemini AI     ← External APIs
```

### Intelligence Pipeline
```
User Checkpoint (last-seen state)
    +
Current Market State (yfinance)
    ↓
Feature Extraction (z-scores, volume ratios)
    ↓
Attention Scoring (weighted 0–100)
    ↓
Movement Attribution (company / sector / market)
    ↓
AI Explanation (Gemini with structured evidence)
    ↓
"Here's what changed and why"
```

---

## 📱 Demo Flow (Hackathon Presentation)

1. **Log in** as `demo@pulse.app`
2. See dashboard: *"2 meaningful changes since your last visit (20 hours ago)"*
3. Click **NVDA** attention card (Attention 92 / MAJOR)
4. See **30-day price chart** — the drop is visible
5. See **Movement Attribution**: Company 67% | Sector 25% | Market 8%
6. See **Market Time Machine**: regulatory news → sector weakness → volume spike → price drop
7. Read **AI Explanation**: "NVDA fell 5.2%..."
8. Go back — see **8 stocks marked Normal** — no action needed
9. Hit **Save Checkpoint** — timestamp updated

---

## 📊 Attention Score Model

```python
attention_score = (
    price_anomaly_score   * 0.30  # z-score based
    + volume_anomaly      * 0.15  # vs 20-day avg
    + volatility_score    * 0.15  # vs historical std
    + news_impact_score   * 0.20  # from news classifier
    + relative_perf_score * 0.10  # vs SPY/sector ETF
    + event_score         * 0.10  # upcoming earnings etc.
)
# Normalized to 0–100
```

**Z-score price anomaly:**
```
|z| < 1  → Normal (0–20)
|z| 1–2  → Watch (20–50)
|z| 2–3  → Significant (50–80)
|z| > 3  → Major (80–100)
```

---

## 🗂 Project Structure

```
pulse/
├── backend/           FastAPI Python backend
│   └── app/
│       ├── api/       REST endpoints
│       ├── models/    SQLAlchemy models
│       ├── services/  Business logic
│       │   ├── intelligence/  Attention engine
│       │   ├── market/        yfinance provider
│       │   ├── news/          NewsAPI provider
│       │   └── ai/            Gemini explanation
│       └── workers/   APScheduler background jobs
├── frontend/          React + Vite + TypeScript
│   └── src/
│       ├── pages/     Dashboard, StockDetail, Watchlist, Auth
│       ├── components/ Attention cards, charts, timeline
│       └── api/       API client modules
├── scripts/           seed_demo_data.py
└── docker-compose.yml Local dev environment
```

---

## 🏆 What Makes This Win

| Judge Criterion | How PULSE Delivers |
|----------------|-------------------|
| Novel idea | "Attention layer" — not just a stock tracker |
| Working demo | Seeded scenario, never fails |
| Technical depth | z-score anomaly, attribution decomposition, structured AI |
| Business viability | Every retail investor is the market |
| Code quality | TypeScript, Pydantic, typed throughout |

---

## ⚠️ Limitations (Transparency)

- Market data via `yfinance` may have brief delays
- Attribution is evidence-based estimation, not causal proof
- AI explanations are grounded in data but not financial advice
- News coverage may be incomplete without API key

---

*Built for hackathon by PULSE team. Not financial advice.*

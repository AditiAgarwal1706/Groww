# ⚡ PULSE AI — Real-Time Market Intelligence & AI News Cause Attribution Engine

> **An Intelligent Financial Market Attention & News Attribution Layer for Indian (NSE/BSE) & Global Equities.**  
> *Detect what changed, analyze why it moved, and uncover news events driving stock price trends across any timeframe.*

---

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue?logo=typescript)
![AI Model](https://img.shields.io/badge/AI-Gemini%203.6%20Flash-purple?logo=google)
![Tests](https://img.shields.io/badge/Tests-100%20Passed-success)

---

## 🌟 Key Innovations & Key Features

### 1. 🔍 AI Date Range Cause Analyzer *(New Feature)*
Select **any stock ticker in the world** and specify a **Start Date & End Date**.
- Fetches real-time yfinance market news, price volatility bounds, and volume metrics.
- Invokes **Google Gemini 3.6 Flash** to synthesize an executive cause attribution summary explaining *what primary news events or market dynamics caused the price change*.
- Visualizes weighted factor drivers (e.g. Earnings 50%, Product Announcements 30%, Macro 20%) with interactive impact progress bars.
- Renders an interactive **Key Events Timeline** and complete news article coverage.

### 2. 🇮🇳 Native Indian Market (NSE/BSE) & Global Equities Support
- Full support for Indian tickers (`RELIANCE.NS`, `TCS.NS`, `TATAMOTORS.NS`, `TATASTEEL.NS`, `HDFCBANK.NS`, `INFY.NS`, `SBIN.NS`, `500325.BO`) with INR (`₹`) currency formatting and NIFTY 50 benchmark attribution.
- Supports US equities (`AAPL`, `NVDA`, `TSLA`, `MSFT`, `AMZN`, `GOOGL`).
- **Dynamic Stock Auto-Registration**: Type any valid exchange ticker into search or watchlists — the system automatically verifies it via Yahoo Finance and registers it instantly.

### 3. 🧠 Market Attention Engine & Anomaly Scoring
Calculates a composite **Attention Score (0–100)** to surface high-priority market movements:
```python
attention_score = (
    price_anomaly_z_score * 0.30   # Statistical deviation vs 20-day mean
  + volume_surge_ratio    * 0.15   # Volume ratio vs average
  + volatility_score      * 0.15   # Standard deviation expansion
  + news_impact_score     * 0.20   # Classified news severity
  + relative_perf_score   * 0.10   # Relative performance vs sector/NIFTY
  + event_score           * 0.10   # Upcoming earnings / corp actions
)
```
Classifies movement severity into **MAJOR** (🔴), **IMPORTANT** (🟠), **WATCH** (🟡), and **NORMAL** (🟢).

### 4. 📊 Movement Attribution Decomposition
Deconstructs stock price changes into three distinct components:
- **Company-Specific Signals**: Idiosyncratic price moves driven by earnings, executive changes, or product releases.
- **Sector Effect**: Trends driven by sector ETFs (`NIFTY_IT`, `NIFTY_BANK`, `XLK`, `XLF`).
- **Broad Market Index Effect**: Systemic market trends (`NIFTY 50` / `SPY`).

### 5. ⚡ Real-Time WebSocket Streaming & Market Session Awareness
- Real-time stock price push over WebSockets.
- Detects market sessions: **LIVE** (🟢), **PRE-MARKET** (◑), **AFTER-HOURS** (🌙), and **MARKET CLOSED** (○).

### 6. 📌 Checkpoint Engine
- Remembers when a user last checked their watchlist.
- Highlights *"What changed since your last visit"* so users never miss critical price moves or news events.

---

## 🏗 Architecture & System Design

```
┌─────────────────────────────────────────────────────────────┐
│                 React 18 + Vite + TypeScript                │
│       (Dashboard, Watchlist, AI Range Cause Analyzer)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API / WebSockets
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Python Backend                   │
│   (Auth Middleware, Market Service, Anomaly Pipeline)      │
└──────────────┬───────────────┬───────────────┬──────────────┘
               │               │               │
  ┌────────────▼─────┐ ┌───────▼───────┐ ┌─────▼──────────────┐
  │ SQLite / Postgres│ │ yfinance API  │ │ Gemini 3.6 Flash   │
  │  (Data Store)    │ │  (Real Quotes)│ │ (AI Attribution)   │
  └──────────────────┘ └───────────────┘ └────────────────────┘
```

---

## 📁 Repository Structure

```
pulse/
├── backend/                        FastAPI Python Backend
│   ├── app/
│   │   ├── api/                    REST Endpoints (watchlists, stocks, changes, auth)
│   │   ├── core/                   Configuration & Auth Dependencies
│   │   ├── db/                     Database Sessions & Migrations
│   │   ├── models/                 SQLAlchemy Models (User, Watchlist, Stock, News)
│   │   ├── schemas/                Pydantic Schemas
│   │   ├── services/
│   │   │   ├── ai/                 Gemini 3.6 Flash Explainer Service
│   │   │   ├── intelligence/       Attention Engine & Attribution Decomposition
│   │   │   ├── market/             yfinance Market Data Provider
│   │   │   └── news/               yfinance & NewsAPI Provider
│   │   └── workers/                Background Scheduled Refresh Jobs
│   └── tests/                      Pytest Automated Test Suite (100 Tests)
│
├── frontend/                       React + Vite + TypeScript Frontend
│   └── src/
│       ├── api/                    Axios API Client Modules
│       ├── components/             UI Cards, Gauges, Badges, Charts, Timelines
│       ├── hooks/                  useRealtimeQuotes WebSocket Hook
│       ├── pages/                  Dashboard, WatchlistPage, StockDetail, RangeAnalysisPage
│       └── stores/                 Zustand Authentication Store
│
└── docker-compose.yml              Docker Deployment Config
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.12 or 3.13
- Node.js 18+ & npm

### 1. Backend Setup
```bash
cd pulse/backend

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend server
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs at `http://127.0.0.1:8000` (API Docs at `http://127.0.0.1:8000/docs`).*

### 2. Frontend Setup
```bash
cd pulse/frontend

# Install dependencies & start Vite dev server
npm install
npm run dev
```
*Frontend runs at `http://127.0.0.1:5173`.*

---

## 🧪 Automated Testing

The codebase includes full test coverage for authentication, market data fetching, watchlist CRUD, Gemini AI prompt formatting, range analysis, and WebSockets.

Run the test suite:
```bash
cd pulse/backend
PYTHONPATH=. ./venv/bin/pytest -v
```

**Test Results:**
```
====================== 100 passed in 17.33s ======================
```

---

## 📄 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register new user account |
| `POST` | `/api/auth/login` | Login & generate JWT token |
| `GET`  | `/api/watchlists` | Get user watchlists |
| `POST` | `/api/watchlists/{id}/stocks` | Add any stock ticker to watchlist |
| `GET`  | `/api/stocks/{symbol}/quote` | Get live stock quote & status |
| `GET`  | `/api/stocks/{symbol}/analysis` | Get Attention Score & Movement Attribution |
| `GET`  | `/api/stocks/{symbol}/range-analysis` | **AI Date Range Cause Analyzer** endpoint |
| `WS`   | `/api/ws/quotes` | Real-time WebSocket quote stream |

---

## 🛡️ License

Distributed under the MIT License. Built for real-world equity market research and intelligent portfolio monitoring. Not financial advice.

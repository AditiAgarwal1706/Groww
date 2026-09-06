# PULSE — Smart Market Watchlist
## Full Hackathon Roadmap, Architecture, File Structure & Workflow

> **Tagline:** *Your market. Your attention. Nothing unnecessary.*

---

## 1. Product Vision

PULSE is an intelligent market watchlist that does more than display stock prices.

It remembers **when the user last checked**, compares the previous state with the current state, detects **meaningful changes**, connects those changes with market/sector/news context, ranks what deserves attention, and explains the likely drivers.

### Core promise

Traditional watchlist:

```text
NVDA   $174.30   -5.2%
TSLA   $341.20   +6.1%
AAPL   $241.10   +0.4%
```

PULSE:

```text
3 meaningful changes since your last visit

🔴 NVDA  -5.2%   Attention 92
   Major company/sector movement

🟢 TSLA  +6.1%   Attention 81
   Strong positive event/news signal

🟡 AAPL  +0.4%   Attention 67
   Earnings approaching

8 other stocks require no immediate attention.
```

---

# 2. Problem Statement

Users can easily see market information, but they still have to manually determine:

- What changed since the last time they checked?
- Which movement is actually unusual?
- Is the movement stock-specific, sector-wide, or market-wide?
- Did relevant news appear?
- Which events deserve attention?
- Which information can safely be ignored?
- How reliable or fresh is the available data?

PULSE solves this by adding an **attention and intelligence layer** on top of market data.

---

# 3. Product Principles

1. **Do not predict unnecessarily.**
   - Focus on explaining observed changes.

2. **Do not overwhelm the user.**
   - Surface only meaningful changes.

3. **Do not let the LLM become the source of truth.**
   - Algorithms generate structured evidence.
   - AI converts evidence into explanations.

4. **Always expose data freshness.**
   - Never present delayed data as real-time.

5. **Never claim causality when the system only has correlation.**
   - Use language such as "likely contributor", "associated with", and "evidence suggests".

6. **Remember the user's last state.**
   - This is the core differentiator.

---

# 4. MVP Scope

## P0 — Must Have

- User registration/login
- Create/update/delete watchlists
- Search stocks
- Add/remove stocks
- Current market quote
- Historical market data
- Persistent watchlists
- User last-check checkpoint
- Change detection
- Attention score
- Meaningful-change feed
- Stock detail page
- Data freshness indicator
- Responsive UI

## P1 — Winning Features

- News integration
- News sentiment/impact scoring
- Movement attribution
- "Why did it move?"
- Market Time Machine timeline
- Sector vs market comparison
- AI-generated explanation
- Explanation confidence

## P2 — If Time Remains

- Stock relationship graph
- Market Shockwaves
- Personalized thresholds
- Natural-language queries
- Smart alerts
- Daily/returning-user market brief

## P3 — Do Not Build During the Hackathon

- Automated trading
- Broker integration
- Stock-price prediction
- Reinforcement learning
- Custom LLM
- Full causal inference engine
- Every global exchange
- Complex portfolio management

---

# 5. Recommended Technology Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zustand
- Recharts
- React Router
- Lucide React

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- JWT authentication
- Passlib/bcrypt or equivalent password hashing

## Data

- PostgreSQL
- Redis
- Background worker
- External market-data provider
- External news provider

## AI

- LLM API
- Deterministic analysis first
- LLM explanation second

## Deployment

- Docker
- Docker Compose for development
- Cloud-hosted frontend
- Cloud-hosted backend
- Managed PostgreSQL
- Managed Redis where practical

---

# 6. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │     React App       │
                         │   TypeScript + UI   │
                         └──────────┬──────────┘
                                    │
                              REST / JSON
                                    │
                         ┌──────────▼──────────┐
                         │      FastAPI        │
                         │      Backend        │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              │                     │                      │
              ▼                     ▼                      ▼
        PostgreSQL                Redis              AI Service
              │                     │                      │
              │                     │                      │
              └─────────────┬───────┴──────────────────────┘
                            │
                     Background Worker
                            │
                  ┌─────────┴──────────┐
                  │                    │
                  ▼                    ▼
            Market Data API        News API
```

---

# 7. Data Flow

```text
External Market API
        │
        ▼
Data Collector
        │
        ▼
Normalize Data
        │
        ▼
Validate / Freshness Check
        │
        ▼
PostgreSQL
        │
        ├──────────────► Historical Data
        │
        └──────────────► Current Snapshot
                              │
                              ▼
                       Feature Generation
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
      Price Signal        Volume Signal       Volatility
          │                   │                    │
          └───────────────────┼────────────────────┘
                              ▼
                       Change Detection
                              │
                              ▼
                       Attention Scoring
                              │
                 ┌────────────┴─────────────┐
                 ▼                          ▼
              News Data               Market Context
                 │                          │
                 └────────────┬─────────────┘
                              ▼
                     Movement Attribution
                              │
                              ▼
                      Explanation Engine
                              │
                              ▼
                         React UI
```

---

# 8. Repository Structure

```text
pulse/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   ├── algorithm.md
│   ├── deployment.md
│   └── demo-script.md
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── components.json
│   │
│   ├── public/
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       │
│       ├── api/
│       │   ├── client.ts
│       │   ├── auth.ts
│       │   ├── watchlists.ts
│       │   ├── stocks.ts
│       │   ├── changes.ts
│       │   └── news.ts
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Navbar.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── PageContainer.tsx
│       │   │
│       │   ├── dashboard/
│       │   │   ├── MarketBrief.tsx
│       │   │   ├── AttentionCards.tsx
│       │   │   ├── WatchlistTable.tsx
│       │   │   ├── MarketPulse.tsx
│       │   │   └── NoMeaningfulChanges.tsx
│       │   │
│       │   ├── stocks/
│       │   │   ├── StockHeader.tsx
│       │   │   ├── PriceChart.tsx
│       │   │   ├── ChangeSummary.tsx
│       │   │   ├── AttentionScore.tsx
│       │   │   ├── MovementAttribution.tsx
│       │   │   ├── WhyItMoved.tsx
│       │   │   ├── NewsList.tsx
│       │   │   └── EventTimeline.tsx
│       │   │
│       │   ├── watchlists/
│       │   │   ├── WatchlistCard.tsx
│       │   │   ├── CreateWatchlistDialog.tsx
│       │   │   ├── AddStockDialog.tsx
│       │   │   └── WatchlistSelector.tsx
│       │   │
│       │   └── common/
│       │       ├── Loading.tsx
│       │       ├── ErrorState.tsx
│       │       ├── FreshnessBadge.tsx
│       │       ├── SeverityBadge.tsx
│       │       └── EmptyState.tsx
│       │
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Register.tsx
│       │   ├── Dashboard.tsx
│       │   ├── Watchlist.tsx
│       │   ├── StockDetails.tsx
│       │   ├── Changes.tsx
│       │   └── Settings.tsx
│       │
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useWatchlists.ts
│       │   ├── useQuote.ts
│       │   ├── useChanges.ts
│       │   └── useNews.ts
│       │
│       ├── stores/
│       │   ├── authStore.ts
│       │   └── uiStore.ts
│       │
│       ├── types/
│       │   ├── auth.ts
│       │   ├── stock.ts
│       │   ├── watchlist.ts
│       │   ├── change.ts
│       │   └── news.ts
│       │
│       └── utils/
│           ├── formatPrice.ts
│           ├── formatTime.ts
│           └── severity.ts
│
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── alembic.ini
│   ├── migrations/
│   │
│   └── app/
│       ├── main.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   └── dependencies.py
│       │
│       ├── db/
│       │   ├── database.py
│       │   └── session.py
│       │
│       ├── models/
│       │   ├── user.py
│       │   ├── stock.py
│       │   ├── watchlist.py
│       │   ├── watchlist_stock.py
│       │   ├── market_snapshot.py
│       │   ├── news.py
│       │   ├── checkpoint.py
│       │   └── detected_change.py
│       │
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── stock.py
│       │   ├── watchlist.py
│       │   ├── change.py
│       │   └── news.py
│       │
│       ├── api/
│       │   ├── auth.py
│       │   ├── users.py
│       │   ├── watchlists.py
│       │   ├── stocks.py
│       │   ├── changes.py
│       │   └── news.py
│       │
│       ├── services/
│       │   ├── market/
│       │   │   ├── base.py
│       │   │   ├── provider.py
│       │   │   ├── normalizer.py
│       │   │   └── service.py
│       │   │
│       │   ├── news/
│       │   │   ├── provider.py
│       │   │   ├── classifier.py
│       │   │   └── service.py
│       │   │
│       │   ├── intelligence/
│       │   │   ├── features.py
│       │   │   ├── anomaly.py
│       │   │   ├── change_detector.py
│       │   │   ├── attention.py
│       │   │   ├── attribution.py
│       │   │   └── confidence.py
│       │   │
│       │   ├── checkpoint/
│       │   │   └── service.py
│       │   │
│       │   └── ai/
│       │       ├── prompt.py
│       │       ├── explanation.py
│       │       └── client.py
│       │
│       ├── workers/
│       │   ├── scheduler.py
│       │   ├── market_worker.py
│       │   └── news_worker.py
│       │
│       └── utils/
│           ├── logging.py
│           ├── time.py
│           └── validation.py
│
└── scripts/
    ├── seed_stocks.py
    ├── seed_demo_data.py
    └── reset_db.py
```

---

# 9. Database Schema

## users

```text
id
email
password_hash
created_at
updated_at
```

## stocks

```text
id
symbol
company_name
exchange
sector
currency
created_at
```

## watchlists

```text
id
user_id
name
created_at
updated_at
```

## watchlist_stocks

```text
id
watchlist_id
stock_id
priority
added_at
```

## market_snapshots

```text
id
stock_id
price
open
high
low
previous_close
volume
timestamp
source
data_status
```

## news

```text
id
stock_id
title
summary
source
url
published_at
sentiment
impact_score
event_type
```

## checkpoints

```text
id
user_id
stock_id
price
volume
volatility
attention_score
created_at
```

## detected_changes

```text
id
user_id
stock_id
change_type
severity
score
summary
evidence
detected_at
```

---

# 10. Important Database Relationships

```text
User
 │
 ├──────< Watchlist
 │              │
 │              └──────< WatchlistStock >──── Stock
 │
 └──────< Checkpoint
                    │
                    └──── Stock

Stock
 │
 ├──────< MarketSnapshot
 │
 ├──────< News
 │
 └──────< DetectedChange
```

---

# 11. Authentication Workflow

```text
REGISTER
   │
   ▼
Validate email/password
   │
   ▼
Hash password
   │
   ▼
Store User
   │
   ▼
Return JWT
```

Login:

```text
LOGIN
  │
  ▼
Find user
  │
  ▼
Verify password
  │
  ▼
Generate JWT
  │
  ▼
Frontend stores auth state
```

Every protected request:

```text
React
  │
  └── Authorization: Bearer <token>
                    │
                    ▼
                FastAPI
                    │
                    ▼
              Current User
```

---

# 12. Watchlist Workflow

## Create

```text
User
 │
 ▼
Create Watchlist
 │
 ▼
POST /api/watchlists
 │
 ▼
Database
```

## Add stock

```text
User searches "NVDA"
       │
       ▼
GET /api/stocks/search?q=NVDA
       │
       ▼
Select NVIDIA
       │
       ▼
POST /api/watchlists/{id}/stocks
       │
       ▼
WatchlistStock created
```

## Remove

```text
DELETE /api/watchlists/{id}/stocks/{symbol}
```

---

# 13. Market Data Workflow

Background worker:

```text
Scheduler
   │
   ▼
Get active stocks
   │
   ▼
Fetch market data
   │
   ▼
Normalize response
   │
   ▼
Validate timestamp
   │
   ▼
Check provider consistency
   │
   ▼
Store snapshot
   │
   ▼
Update Redis
```

Do not make every frontend request hit the external market API.

---

# 14. Provider Abstraction

Use an interface:

```python
class MarketDataProvider:

    def get_quote(self, symbol):
        raise NotImplementedError

    def get_history(self, symbol, start, end):
        raise NotImplementedError
```

Provider implementation:

```python
class ExternalMarketProvider(MarketDataProvider):

    def get_quote(self, symbol):
        ...
```

Service:

```python
class MarketService:

    def get_quote(self, symbol):
        try:
            return primary_provider.get_quote(symbol)
        except Exception:
            return fallback_provider.get_quote(symbol)
```

This prevents your application from being tightly coupled to one provider.

---

# 15. Data Freshness

Every market observation should have:

```text
timestamp
source
status
```

Possible statuses:

```text
LIVE
DELAYED
STALE
UNAVAILABLE
CONFLICT
```

Example frontend:

```text
$174.32

Updated 3 min ago
● Delayed
```

If data becomes too old:

```text
⚠ Data is stale.
Last successful update: 28 min ago.
```

Never silently display old data as current.

---

# 16. Conflicting Data

If two providers return:

```text
Provider A: $174.31
Provider B: $174.35
```

Use a configurable tolerance.

```python
difference = abs(a - b) / max(a, b)

if difference <= tolerance:
    accept_latest()
else:
    flag_conflict()
```

Frontend:

```text
⚠ Data discrepancy detected

Reported range:
$174.31 – $174.35

Using latest verified observation.
```

---

# 17. Checkpoint System

This is the central feature.

When a user views a watchlist:

```text
Current State
     │
     ▼
Save checkpoint
```

Checkpoint contains:

```json
{
  "symbol": "NVDA",
  "price": 183.21,
  "volume": 45000000,
  "volatility": 0.021,
  "attention_score": 31,
  "checked_at": "..."
}
```

When they return:

```text
Current State
     │
     ▼
Retrieve previous checkpoint
     │
     ▼
Compare
     │
     ▼
Generate meaningful changes
```

---

# 18. Meaningful Change Engine

The engine should combine several signals.

## Inputs

```text
price return
historical volatility
volume
market return
sector return
news activity
news impact
upcoming event
```

## Example scoring model

```python
attention_score = (
    price_anomaly * 0.30 +
    volume_anomaly * 0.15 +
    volatility_anomaly * 0.15 +
    news_impact * 0.20 +
    relative_performance * 0.10 +
    event_score * 0.10
)
```

Normalize everything to `0–100`.

---

# 19. Price Anomaly

Do not use a fixed threshold alone.

Use historical behavior.

```python
z_score = (
    current_return - mean_return
) / historical_std
```

Interpretation:

```text
|z| < 1       Normal
1–2           Watch
2–3           Significant
>3            Major
```

For example:

```text
Historical average = 0.2%
Historical std = 1.5%
Today's return = -5%

z ≈ -3.47
```

Therefore:

```text
Major price anomaly
```

---

# 20. Volume Anomaly

```python
volume_ratio = current_volume / average_volume
```

Example:

```text
1.0×   Normal
1.5×   Elevated
2.0×   Significant
3.0×   Major
```

A large price move with unusually high volume should receive more attention than the same move with low volume.

---

# 21. Relative Performance

Compare the stock against:

- broad market benchmark
- relevant sector benchmark

Example:

```text
NVDA      -5.2%
NASDAQ    -0.4%
SOX       -1.5%
```

Calculate:

```python
market_relative = stock_return - market_return
sector_relative = stock_return - sector_return
```

Possible explanation:

```text
NVDA significantly underperformed
both the broader market and its sector.
```

---

# 22. News Signal

Normalize each article:

```json
{
  "symbol": "NVDA",
  "title": "Example headline",
  "published_at": "...",
  "event_type": "REGULATORY",
  "sentiment": "NEGATIVE",
  "impact_score": 0.91
}
```

Possible event types:

```text
EARNINGS
GUIDANCE
REGULATORY
PRODUCT
ACQUISITION
MANAGEMENT
ANALYST
LEGAL
PARTNERSHIP
MACRO
OTHER
```

---

# 23. News Relevance

Do not associate every article with a movement.

Consider:

```text
ticker relevance
publication time
event importance
sentiment
price movement after publication
source quality
```

A relevant article published shortly before an abnormal movement receives a stronger signal.

---

# 24. Movement Attribution

Use contribution analysis rather than claiming causal certainty.

Example:

```text
Observed movement: -5.2%

Market effect       -0.4%
Sector effect       -1.3%
Company signals     -3.5%
```

Frontend:

```text
COMPANY-SPECIFIC    ███████████████ 67%
SECTOR              ██████          25%
MARKET              ██               8%
```

Use wording:

> "Available evidence suggests company-specific signals were the largest contributor."

Avoid:

> "This news caused the stock to fall."

---

# 25. Attention Score

Suggested categories:

```text
0–30      Normal
30–60     Watch
60–80     Important
80–100    Major
```

Example:

```text
NVDA
Price anomaly:          92
Volume anomaly:         87
News impact:            90
Relative performance:   95
Event score:             0

Final Attention:        92
```

---

# 26. Detected Change Object

Backend can return:

```json
{
  "symbol": "NVDA",
  "severity": "MAJOR",
  "attention_score": 92,
  "changes": [
    {
      "type": "PRICE",
      "value": -5.2
    },
    {
      "type": "VOLUME",
      "value": 2.8
    },
    {
      "type": "SECTOR",
      "value": -1.5
    }
  ],
  "summary": "NVDA significantly underperformed its sector and broader market."
}
```

---

# 27. AI Explanation Workflow

Never send only:

```text
"NVDA is down. Explain why."
```

Instead send structured evidence:

```json
{
  "symbol": "NVDA",
  "price_change": -5.2,
  "volume_ratio": 2.8,
  "market_change": -0.4,
  "sector_change": -1.5,
  "news": [
    {
      "title": "Example regulatory event",
      "impact": 0.91
    }
  ]
}
```

Prompt requirements:

```text
Explain only from supplied evidence.

Return:
1. What changed
2. Likely contributing factors
3. Why it is unusual
4. Confidence
5. Caveats

Do not invent facts.
Do not provide investment advice.
Do not claim causal certainty.
```

---

# 28. Explanation Response

```json
{
  "summary": "NVDA fell 5.2%, significantly more than the broader market and sector.",
  "drivers": [
    {
      "factor": "Company-specific news",
      "weight": 0.45
    },
    {
      "factor": "Sector weakness",
      "weight": 0.27
    },
    {
      "factor": "Market movement",
      "weight": 0.12
    }
  ],
  "confidence": 87,
  "caveat": "The attribution is evidence-based, not proof of causation."
}
```

---

# 29. Market Time Machine

This should be a major UI feature.

When the user returns:

```text
LAST CHECKED
Sep 3 — 8:42 PM
          │
          ▼
Sep 3 — 10:15 PM
📰 Major news
          │
          ▼
Sep 4 — 11:30 AM
📉 Sector weakness
          │
          ▼
Sep 4 — 12:05 PM
📊 Volume spike
          │
          ▼
Sep 4 — 2:41 PM
🔴 NVDA -5.2%
          │
          ▼
NOW
```

This is generated from stored events.

---

# 30. Dashboard Design

## Header

```text
PULSE

Good afternoon.

Last checked:
Yesterday, 8:42 PM
```

## Market brief

```text
YOUR MARKET BRIEF

3 meaningful changes
2 watch items
8 normal
```

## Attention cards

```text
NVDA
-5.2%
Attention 92
MAJOR

TSLA
+6.1%
Attention 81
MAJOR

AAPL
Earnings approaching
Attention 67
IMPORTANT
```

## Watchlist

```text
Stock | Price | Change | Volume | Attention | Status
```

---

# 31. Stock Detail Page

```text
NVDA

$174.32
-5.2%

WHAT CHANGED?

Price        -5.2%
Volume        2.8×
Sector        -1.5%
Market        -0.4%
News          4 events

ATTENTION
92 / 100

WHY DID IT MOVE?

Company-specific     ███████████████
Sector                ██████
Market                ██

EVENT TIMELINE

10:32  News
11:30  Sector movement
12:05  Volume spike
14:41  Price anomaly
```

---

# 32. "Nothing Important Happened"

This is an important UX feature.

If nothing crosses the meaningful threshold:

```text
✓ Nothing important changed.

12 stocks checked
0 major changes
1 watch item
11 normal
```

This proves that PULSE is designed to reduce noise.

---

# 33. API Specification

## Auth

```http
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

## Watchlists

```http
GET    /api/watchlists
POST   /api/watchlists
GET    /api/watchlists/{id}
PATCH  /api/watchlists/{id}
DELETE /api/watchlists/{id}
```

## Watchlist stocks

```http
POST   /api/watchlists/{id}/stocks
DELETE /api/watchlists/{id}/stocks/{symbol}
```

## Stock search

```http
GET /api/stocks/search?q=nvda
```

## Market data

```http
GET /api/stocks/{symbol}/quote
GET /api/stocks/{symbol}/history
```

## Intelligence

```http
GET /api/watchlists/{id}/changes
GET /api/stocks/{symbol}/analysis
GET /api/stocks/{symbol}/timeline
GET /api/stocks/{symbol}/explanation
```

## Checkpoint

```http
POST /api/watchlists/{id}/checkpoint
GET  /api/watchlists/{id}/checkpoint
```

## News

```http
GET /api/stocks/{symbol}/news
```

---

# 34. API Request Flow — Dashboard

```text
GET /api/dashboard
        │
        ▼
Authenticate user
        │
        ▼
Load user's watchlists
        │
        ▼
Get latest market snapshots
        │
        ▼
Get last checkpoint
        │
        ▼
Run comparison
        │
        ▼
Get detected changes
        │
        ▼
Rank by attention
        │
        ▼
Return dashboard payload
```

Prefer implementing this as a single aggregated dashboard endpoint rather than forcing the browser to make dozens of requests.

---

# 35. Suggested Dashboard Response

```json
{
  "last_checked_at": "...",
  "summary": {
    "major": 2,
    "important": 1,
    "watch": 2,
    "normal": 8
  },
  "top_attention": [
    {
      "symbol": "NVDA",
      "score": 92,
      "severity": "MAJOR"
    },
    {
      "symbol": "TSLA",
      "score": 81,
      "severity": "MAJOR"
    }
  ],
  "watchlist": []
}
```

---

# 36. Background Workers

## Market Worker

Runs periodically.

```text
Scheduler
    │
    ▼
Get symbols requiring updates
    │
    ▼
Fetch quotes
    │
    ▼
Normalize
    │
    ▼
Validate
    │
    ▼
Store snapshot
    │
    ▼
Update Redis
```

## News Worker

```text
Scheduler
    │
    ▼
Get active symbols
    │
    ▼
Fetch recent news
    │
    ▼
Deduplicate
    │
    ▼
Classify
    │
    ▼
Store
```

---

# 37. Caching

Recommended keys:

```text
quote:NVDA
history:NVDA
news:NVDA
analysis:NVDA
```

Example TTL strategy:

```text
Quote       short TTL
News        few minutes
Analysis    few minutes
Historical  longer TTL
```

Exact TTLs should be adapted to the selected provider.

---

# 38. Scaling Strategy

For a hackathon:

```text
React
  │
FastAPI
  │
PostgreSQL
  │
Redis
  │
Worker
```

No microservices.

If the product grows:

```text
Load Balancer
      │
 ┌────┴─────┐
 │          │
API #1    API #2
 │          │
 └────┬─────┘
      │
    Redis
      │
 PostgreSQL
      │
 Worker Pool
```

Most stock-level calculations should be shared across users.

Do not independently fetch the same stock for every user.

---

# 39. Performance Strategy

## Bad

```text
100 users
×
20 stocks
×
every refresh
=
2000 external API requests
```

## Good

```text
External API
      │
      ▼
Shared background collector
      │
      ▼
Redis/PostgreSQL
      │
      ▼
100 users
```

User-specific work should mainly be:

```text
Current state
      +
User checkpoint
      ↓
Personalized comparison
```

---

# 40. Security

Implement:

- JWT authentication
- Password hashing
- Input validation
- Rate limiting
- CORS configuration
- SQL injection protection through ORM/parameterized queries
- Environment variables for secrets
- Secure production cookies/storage strategy
- No API keys in frontend
- No sensitive credentials committed to Git

`.env.example`:

```env
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
MARKET_DATA_API_KEY=
NEWS_API_KEY=
LLM_API_KEY=
```

---

# 41. Error Handling

Backend should distinguish:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
429 Rate Limited
500 Internal Error
503 Provider Unavailable
```

Frontend should show useful states:

```text
Loading...
```

```text
Data temporarily unavailable.
```

```text
Market data is delayed.
```

```text
No meaningful changes detected.
```

---

# 42. Development Workflow

## Step 1 — Repository

Create:

```text
pulse/
frontend/
backend/
docs/
scripts/
```

Initialize Git.

---

## Step 2 — Environment

Create:

```text
.env
.env.example
```

Configure:

```text
PostgreSQL
Redis
market API
news API
LLM API
```

---

## Step 3 — Backend Skeleton

Implement:

```text
FastAPI
configuration
database
models
Alembic
authentication
```

Run:

```text
GET /health
```

Expected:

```json
{
  "status": "ok"
}
```

---

# 43. Backend Build Order

Implement in this exact order:

```text
1. Database
2. User model
3. Authentication
4. Stock model
5. Watchlist model
6. Watchlist CRUD
7. Market provider
8. Market snapshots
9. Checkpoints
10. Change detector
11. Attention scoring
12. News
13. Movement attribution
14. AI explanation
15. Dashboard aggregation
```

Do not start with AI.

---

# 44. Frontend Build Order

```text
1. App shell
2. Login/Register
3. Dashboard layout
4. Watchlist CRUD UI
5. Stock search
6. Watchlist table
7. Attention cards
8. Stock detail
9. Charts
10. Change timeline
11. News
12. Explanation UI
13. Loading/error states
14. Responsive polish
```

---

# 45. Testing Strategy

## Unit tests

Test:

```text
price anomaly
volume anomaly
relative performance
attention score
severity classification
checkpoint comparison
freshness calculation
```

Example:

```text
Input:
current return = -5%
mean = 0.2%
std = 1.5%

Expected:
z-score ≈ -3.47
severity = MAJOR
```

## Integration tests

Test:

```text
Register
  ↓
Login
  ↓
Create watchlist
  ↓
Add stock
  ↓
Get quote
  ↓
Create checkpoint
  ↓
Change simulated
  ↓
Get detected change
```

---

# 46. Demo Data Strategy

Do not rely completely on live market conditions during the judging demo.

Create deterministic demo scenarios.

Example:

```text
Scenario: NVDA shock

Before:
$183.21
Volume ratio: 1.0
Attention: 25

Simulated:
Regulatory news
Sector decline
Volume spike

After:
$174.30
Volume ratio: 2.8
Attention: 92
```

The UI can clearly label demo/simulated data when necessary.

This protects the presentation from unpredictable markets or API failures.

---

# 47. Hackathon Demo Scenario

## Scene 1 — Normal Watchlist

Show:

```text
NVDA  $183.21
TSLA  $321.40
AAPL  $240.90
```

Say:

> "This is a normal watchlist. It tells me what my stocks are doing, but not what deserves my attention."

---

## Scene 2 — Save Checkpoint

Click:

```text
CHECKPOINT SAVED
Sep 3 — 8:42 PM
```

---

## Scene 3 — Simulate Market Events

Trigger:

```text
News event
Sector decline
Volume spike
Price movement
```

---

## Scene 4 — Return to PULSE

Show:

```text
WELCOME BACK

3 meaningful changes since your last visit.
```

---

## Scene 5 — NVDA

Show:

```text
NVDA
-5.2%

Attention Score: 92
```

---

## Scene 6 — Market Time Machine

Show:

```text
10:32 AM  News
11:30 AM  Sector weakness
12:05 PM  Volume spike
2:41 PM   Price anomaly
```

---

## Scene 7 — Market Autopsy

Show:

```text
Company-specific  67%
Sector             25%
Market              8%
```

---

## Scene 8 — AI Explanation

Show:

> "NVDA significantly underperformed the broader market and its sector. Available evidence suggests company-specific signals were the largest contributor."

---

## Scene 9 — Nothing Else Matters

Show:

```text
8 stocks monitored

2 major changes
1 important
8 normal

Only 3 require attention.
```

---

# 48. Hackathon Presentation Structure

Use approximately 7 slides.

## Slide 1 — Problem

> "Markets generate too much information for humans to monitor efficiently."

## Slide 2 — Existing Experience

Show traditional watchlist.

## Slide 3 — PULSE

Show:

> "What changed since you last checked?"

## Slide 4 — How It Works

```text
Market Data
   ↓
Change Detection
   ↓
Attention Engine
   ↓
Explanation
```

## Slide 5 — Demo

Show the Time Machine and Autopsy.

## Slide 6 — Technical Architecture

Show:

```text
React
FastAPI
PostgreSQL
Redis
Workers
AI
```

## Slide 7 — Future

```text
Personalized attention
Relationship graphs
Smart alerts
Market shockwaves
```

---

# 49. What Makes It Different

| Traditional Watchlist | PULSE |
|---|---|
| Shows current price | Shows what changed |
| User manually checks | System prioritizes |
| Raw numbers | Context |
| Fixed threshold | Volatility-aware |
| News feed | Relevant events |
| No memory | Last-check memory |
| Individual stocks | Market/sector context |
| Alerts everything | Attention filtering |
| Generic dashboard | Personalized intelligence |

---

# 50. Core Differentiator

The strongest product loop is:

```text
USER CHECKS
     ↓
SYSTEM SAVES STATE
     ↓
MARKET CHANGES
     ↓
USER RETURNS
     ↓
SYSTEM COMPARES STATES
     ↓
DETECTS SIGNAL
     ↓
RANKS ATTENTION
     ↓
EXPLAINS WHY
```

This loop should drive the entire application.

---

# 51. Recommended 72-Hour Roadmap

## Hours 0–3 — Planning

- Finalize scope
- Choose market/news providers
- Create repository
- Define database schema
- Create wireframes

Deliverable:

```text
Architecture + UI skeleton
```

---

## Hours 3–10 — Backend Foundation

Build:

- FastAPI
- PostgreSQL
- migrations
- authentication
- user model
- stock model
- watchlist CRUD

Deliverable:

```text
Working authenticated API
```

---

## Hours 10–16 — Market Data

Build:

- provider abstraction
- quote fetching
- historical data
- normalization
- freshness tracking
- Redis caching

Deliverable:

```text
Reliable market-data layer
```

---

## Hours 16–23 — Intelligence Engine

Build:

- checkpoints
- price anomaly
- volume anomaly
- volatility
- relative performance
- attention score
- severity

Deliverable:

```text
"What changed?"
```

This is the most important milestone.

---

## Hours 23–29 — News

Build:

- news provider
- deduplication
- ticker mapping
- event classification
- impact scoring

Deliverable:

```text
"What else happened?"
```

---

## Hours 29–34 — AI

Build:

- evidence payload
- explanation prompt
- confidence
- caveat generation

Deliverable:

```text
"Why did it happen?"
```

---

## Hours 34–44 — Frontend

Build:

- authentication pages
- dashboard
- watchlist
- attention cards
- stock details
- charts
- timeline

Deliverable:

```text
Complete user flow
```

---

## Hours 44–50 — Time Machine

Build:

- last-check banner
- change timeline
- event ordering
- comparison UI

Deliverable:

```text
"While you were away..."
```

---

## Hours 50–56 — Polish

Add:

- responsive design
- loading states
- empty states
- error states
- freshness badges
- animations
- typography
- spacing
- visual hierarchy

---

## Hours 56–62 — Demo Reliability

Implement:

- seeded data
- simulated event scenario
- fallback data
- API failure handling
- demo account
- health checks

---

## Hours 62–68 — Testing

Test:

- authentication
- watchlists
- data collection
- checkpointing
- change detection
- dashboard
- AI explanation

---

## Hours 68–72 — Presentation

Prepare:

- pitch
- architecture slide
- demo flow
- technical explanation
- limitations
- future roadmap

---

# 52. Definition of Done

The project is ready when a judge can perform this flow:

```text
Open PULSE
   ↓
Create account
   ↓
Create watchlist
   ↓
Add NVDA
   ↓
See current market information
   ↓
Save/checkpoint state
   ↓
Simulate market changes
   ↓
Return later
   ↓
See "3 meaningful changes"
   ↓
Click NVDA
   ↓
See attention score
   ↓
See timeline
   ↓
See movement attribution
   ↓
Read AI explanation
```

If this works smoothly, the MVP is complete.

---

# 53. Future Roadmap

## Version 1

```text
Smart watchlist
+
last-check comparison
+
attention score
```

## Version 2

```text
news intelligence
+
movement attribution
+
AI explanation
```

## Version 3

```text
relationship graph
+
market shockwaves
+
personalized attention
```

## Version 4

```text
proactive alerts
+
natural-language market queries
+
cross-market intelligence
```

---

# 54. Future Architecture

Eventually:

```text
                         DATA SOURCES
                    ┌────────┼─────────┐
                    ▼        ▼         ▼
                 Stocks    News     Events
                    │        │         │
                    └────────┼─────────┘
                             ▼
                      Event Processing
                             │
                    ┌────────┴─────────┐
                    ▼                  ▼
              Signal Engine       Relationship
                    │               Engine
                    └────────┬─────────┘
                             ▼
                     Attention Engine
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
             User Model             AI Layer
                  │                     │
                  └──────────┬──────────┘
                             ▼
                     Personalized Brief
```

---

# 55. Important Technical Limitations

Be transparent with judges.

### Market data

Some providers may be delayed or rate-limited.

### Attribution

Movement attribution is an evidence-based estimate, not definitive causality.

### AI

LLM explanations should be grounded in structured evidence.

### News

News coverage can be incomplete.

### Attention score

The score is a product-defined prioritization metric, not an objective financial-risk rating.

### Financial advice

PULSE should provide information and context, not personalized investment recommendations.

---

# 56. The Winning Product Narrative

Do not pitch:

> "We built a stock watchlist with AI."

Pitch:

> **"We built an attention layer for financial markets."**

Then explain:

```text
Markets produce thousands of signals.

Humans have limited attention.

PULSE filters the signals.

It remembers what you saw.

It detects what changed.

It determines what is unusual.

It explains the likely drivers.

And it tells you what you can ignore.
```

---

# 57. Final Product Flow

```text
                         PULSE
                           │
                           ▼
                    USER WATCHLIST
                           │
                           ▼
                 ┌───────────────────┐
                 │  CURRENT MARKET   │
                 │      STATE        │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ LAST CHECKPOINT   │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ CHANGE DETECTOR   │
                 └─────────┬─────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
            PRICE        VOLUME       NEWS
              │            │            │
              └────────────┼────────────┘
                           ▼
                 ┌───────────────────┐
                 │ ATTENTION ENGINE  │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ MOVEMENT ANALYSIS │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  AI EXPLANATION   │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │    USER SEES:     │
                 │                   │
                 │ What changed?     │
                 │ Why?              │
                 │ How important?    │
                 │ What can I ignore?│
                 └───────────────────┘
```

---

# 58. The Three Features to Prioritize Above Everything

If the hackathon becomes time-constrained, protect these three:

## 1. Last-Check Intelligence

> **"What happened since I last looked?"**

## 2. Attention Score

> **"What deserves my attention?"**

## 3. Movement Explanation

> **"Why did this happen?"**

Everything else is secondary.

---

# 59. Final One-Line Pitch

> **PULSE is a smart market watchlist that remembers what you saw, detects what meaningfully changed while you were away, and explains what deserves your attention — so you don't have to monitor the market constantly.**


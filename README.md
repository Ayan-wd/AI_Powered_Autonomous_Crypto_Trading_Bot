# AI-Powered Autonomous Crypto Trading Bot

[![CI Test Suite](https://github.com/your-username/AI-Trading-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/AI-Trading-bot/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-cyan.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An institutional-grade, modular, AI-powered cryptocurrency trading system designed initially for **Binance Spot Testnet** and paper trading, prioritizing capital preservation over forcing trades.

The eventual live experiment is designed around **$50 USD capital**, capturing high-probability opportunities while defaulting to `HOLD / NO TRADE` in uncertain market conditions.

---

## 🛡️ Safety-First Principles & Guarantees

* **Safe Defaults**: The system starts strictly in `TRADING_MODE=PAPER`, `TRADING_ENABLED=false`, and `LIVE_TRADING=false`.
* **Dual-Confirmation Safeguard**: Live execution strictly requires both `LIVE_TRADING=true` AND `TRADING_ENABLED=true`.
* **No Withdrawal Permissions**: API keys with withdrawal permissions are never supported or requested.
* **Emergency Kill Switch**: Immediate shutdown endpoint (`POST /api/v1/status/kill-switch`) freezes trading and halts order submission.
* **Capital Protection**: Strict 1% max risk per trade, max $10 position sizing on $50 starting capital, daily loss limit (3%), and drawdown halts (10%).

---

## 🏛️ System Architecture

```
Market Data (Binance REST / WebSocket)
                 ↓
      Quantitative Data Validator (Zero Gaps / Boundary Checks)
                 ↓
      Feature Engineering (EMA 20/50/200, RSI, MACD, ATR, Volatility)
                 ↓
      Machine Learning Engine (XGBoost Probabilities: BUY / HOLD / SELL)
                 ↓
      Deterministic Decision Engine (Return > Cost Hurdle Rate)
                 ↓
      Quantitative Risk Manager (1% Max Risk, Drawdown Guard, Kill Switch)
                 ↓
      Execution Layer (Binance Spot Testnet / Paper Broker)
                 ↓
      Audited Trade Ledger & Continuous Performance Analytics
```

---

## 📁 Repository Structure

```
ai-trading-bot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/         # Health, Status, Account, Trades, Config, Market routes
│   │   ├── core/               # Pydantic Settings, Loguru logging, Security utils
│   │   ├── data/               # Market data engine, WebSocket client, Data validator
│   │   ├── features/           # Technical indicators & Feature matrix calculations
│   │   ├── ml/                 # XGBoost training, Walk-forward validation, Scalers
│   │   ├── strategy/           # Deterministic Decision Engine & Signal generator
│   │   ├── risk/               # Position sizing, Drawdown guard, Kill switch
│   │   ├── execution/          # ExchangeInterface & Binance Spot Client
│   │   ├── backtesting/        # Slippage, Fees, Expectancy & Metrics engine
│   │   ├── portfolio/          # Virtual & Testnet Portfolio manager
│   │   ├── database/           # SQLAlchemy models, SQLite/Postgres async engine & Repos
│   │   ├── monitoring/         # Watchdog, Performance & Health checks
│   │   └── main.py             # FastAPI entry point & lifespan manager
│   ├── tests/                  # Pytest async test suite (19 unit/integration tests)
│   ├── Dockerfile              # Backend container definition
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # Header, MetricCards, AIPredictionCard, MarketOverviewCard, TradesTable, EquityChart
│   │   ├── services/           # Typed REST API service
│   │   ├── types/              # TypeScript trading contracts
│   │   ├── App.tsx             # Main dashboard
│   │   └── index.css           # Tailwind CSS & dark terminal theme
│   ├── Dockerfile              # Frontend multi-stage container
│   ├── nginx.conf              # Nginx reverse proxy
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── historical/             # OHLCV candles & orderbook data
│   └── processed/              # Normalized ML datasets
├── models/                     # Saved model binaries & scalers
├── notebooks/                  # Strategy EDA & Walk-forward analysis
├── docs/                       # Architecture & Risk guidelines
├── scripts/                    # Automation scripts
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI workflow
│   └── PULL_REQUEST_TEMPLATE.md
├── docker-compose.yml          # Container orchestration
├── .env.example
├── .gitignore
├── pytest.ini
└── README.md
```

---

## 🚀 Quickstart Guide

### Option 1: Local Development

#### 1. Backend Setup

```powershell
# In root directory:
cd d:\AI-Trading-bot

# Activate virtual environment
backend\.venv\Scripts\activate

# Run automated tests
backend\.venv\Scripts\pytest backend/tests/ -v

# Launch the FastAPI backend server
backend\.venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
```

* API Root: `http://127.0.0.1:8000`
* Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/api/v1/health`

#### 2. Frontend Dashboard Setup

```powershell
cd frontend
npm install
npm run dev
```

* Dashboard UI: `http://localhost:5173`

---

### Option 2: Docker Compose (All-in-One)

To run the entire system (FastAPI backend + React frontend + SQLite database) in isolated Docker containers:

```bash
# 1. Prepare environment file
cp .env.example .env

# 2. Build and start containers
docker compose up --build -d

# 3. View logs
docker compose logs -f
```

* Frontend UI: `http://localhost:3000`
* Backend API: `http://localhost:8000`

---

## 🧪 Testing

Run backend tests using the virtual environment:

```powershell
# From project root:
backend\.venv\Scripts\pytest backend/tests/ -v
```

Or from within `backend/`:
```powershell
cd backend
..\backend\.venv\Scripts\pytest -v
```

All 19 tests verify:
- ✅ Safe default configuration & live mode guards
- ✅ Data validator OHLCV price rules, gap detection, stale feeds
- ✅ Database models, async SQLite engine, and repositories
- ✅ Exchange interface abstraction and Binance client HMAC SHA256 signatures
- ✅ FastAPI health, status, account, trades, config, and market endpoints

---

## 🌿 Git Workflow & Branches

```bash
# Main production branch
git checkout main

# Feature development branch
git checkout -b feature/phase-1-2-core-market-engine
```

### Pull Request & Merge Workflow

1. Create a feature branch: `git checkout -b feature/<feature-name>`
2. Make changes and verify tests pass: `backend\.venv\Scripts\pytest -v`
3. Commit with semantic messages: `git commit -m "feat(market): add binance testnet client and data validator"`
4. Push to remote and open a Pull Request against `main`.
5. GitHub Actions CI will automatically test backend and verify frontend build.

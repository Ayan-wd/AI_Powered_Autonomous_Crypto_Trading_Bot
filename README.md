# AI-Powered Autonomous Crypto Trading Bot

[![CI Test Suite](https://github.com/Ayan-wd/AI-Trading-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Ayan-wd/AI-Trading-bot/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-cyan.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Test Suite](https://img.shields.io/badge/tests-61%2F61%20passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An institutional-grade, modular, AI-powered cryptocurrency trading system designed for **Binance Spot Testnet** and high-fidelity paper trading, ready for an autonomous live experiment with virtual **$50 USD capital**.

The system prioritizes **capital preservation and mathematical expectancy** over forcing trades, enforcing strict anti-Martingale position sizing, multi-tier circuit breakers, and zero-lookahead machine learning.

---

## 🛡️ Safety-First Institutional Guardrails

* **Safe Defaults**: System initializes strictly in `TRADING_MODE=PAPER`, `TRADING_ENABLED=false`, and `LIVE_TRADING=false`.
* **Dual-Confirmation Safeguard**: Live execution strictly requires both `LIVE_TRADING=true` AND `TRADING_ENABLED=true`.
* **No Withdrawal Permissions**: API keys with withdrawal permissions are strictly prohibited and flagged as security violations.
* **Emergency Kill Switch**: Immediate shutdown endpoint (`POST /api/v1/status/kill-switch`) freezes trading and halts order submission.
* **Anti-Martingale Position Sizing**: Max 1% risk per trade ($0.50 on $50 capital), max $10 position ceiling (20% portfolio allocation).
* **Multi-Tier Circuit Breakers**: 3% daily loss limit, 8% weekly loss limit, 10% max drawdown emergency halt, and 3 consecutive loss cooldown.
* **Cost Hurdle Rate**: Only executes when predicted alpha exceeds $2 \times (\text{0.10\% fee} + \text{0.05\% slippage}) = 0.30\%$.

---

## 🏛️ Comprehensive Architecture

```
                                  [ Binance Spot Testnet / REST & WebSocket ]
                                                       │
                                                       ▼
                                   [ Quantitative Market Data Engine ]
                                  (Gap Detection, Stale Tick Validator)
                                                       │
                                                       ▼
                                      [ Technical Feature Pipeline ]
                                  (EMA 20/50/200, RSI, MACD, ATR, Volatility)
                                                       │
                                                       ▼
                                   [ Walk-Forward XGBoost ML Engine ]
                                  (Zero-Lookahead Scaler, Probabilities)
                                                       │
                                                       ▼
                                  [ Deterministic Strategy Engine ]
                                  (Cost Hurdle Filter: Alpha > 0.30%)
                                                       │
                                                       ▼
                                 [ Quantitative Risk Manager ]
                     (1% Max Risk, Anti-Martingale Sizing, Circuit Breakers)
                                                       │
                                                       ▼
                                     [ Master Order Execution Layer ]
                                   (Paper Simulator / Testnet Client)
                                                       │
                        ┌──────────────────────────────┴──────────────────────────────┐
                        ▼                                                             ▼
         [ Audited Database Ledger ]                                   [ WebSocket Event Stream ]
         (SQLite / PostgreSQL Async)                                  (/api/v1/ws/stream)
                        │                                                             │
                        └──────────────────────────────┬──────────────────────────────┘
                                                       ▼
                                      [ Modern React 19 Dashboard ]
                                (Bot Controls, Telemetry, Risk & Security)
```

---

## 📋 Completed Phases Breakdown

| Phase | Module | Key Features & Institutional Guarantees | Status |
|---|---|---|---|
| **Phase 1** | Base Architecture | FastAPI async backend, SQLite/Postgres models, React 19 UI, Pydantic settings | ✅ Complete |
| **Phase 2** | Market Engine | Binance REST/WebSocket client, HMAC-SHA256 signing, Data validator | ✅ Complete |
| **Phase 3** | Feature Engineering | EMA 20/50/200, RSI, MACD, ATR, Volatility regimes, Zero-Lookahead test | ✅ Complete |
| **Phase 4** | Machine Learning | Walk-Forward expanding XGBoost classifier, RobustScaler serialization | ✅ Complete |
| **Phase 5** | Backtesting | Slippage & fee deductions, Next-bar execution, 3-Way Strategy Comparator | ✅ Complete |
| **Phase 6** | Risk Engine | 1% Fixed fractional sizing, 3% daily loss limit, 10% max DD circuit breaker | ✅ Complete |
| **Phase 7** | Paper Daemon | Autonomous background loop, high-fidelity simulator, intrabar SL/TP | ✅ Complete |
| **Phase 8** | Testnet Layer | Binance Spot Testnet order execution, balance sync, permission audit | ✅ Complete |
| **Phase 9** | Real-time Stream | WebSocket event hub (`/ws/stream`), Sharpe/Sortino/Win Rate analytics | ✅ Complete |
| **Phase 10** | Security Hardening | Recursive secret masking, Token Bucket rate limiter, Resilience watchdog | ✅ Complete |
| **Phase 11** | Packaging & SOP | 7-day experiment runbook, Docker containerization, incident drills | ✅ Complete |

---

## 📁 Repository Structure

```
ai-trading-bot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/         # Health, Status, Account, Trades, Strategy, Trading, Risk, Testnet, Analytics, Security
│   │   │   └── websocket/      # Fast WebSocket connection hub & streaming routes
│   │   ├── core/               # Pydantic Settings, Loguru logging, Security utils, Rate limiter
│   │   ├── data/               # Market data engine, WebSocket client, Data validator
│   │   ├── features/           # Technical indicators, Market regimes, Feature pipeline
│   │   ├── ml/                 # Walk-Forward XGBoost, Scalers, Prediction engine
│   │   ├── strategy/           # Multi-Factor Decision Engine & Cost hurdle filter
│   │   ├── risk/               # Position sizing, Drawdown guard, Circuit breakers
│   │   ├── execution/          # Paper simulator, Order manager, Autonomous trading daemon
│   │   ├── backtesting/        # Slippage, Fees, Next-bar execution, 3-Way comparator
│   │   ├── database/           # SQLAlchemy models, SQLite/Postgres async engine & Repositories
│   │   └── monitoring/         # Watchdog, System health audit, Performance analytics
│   ├── tests/                  # Pytest async test suite (61 unit/integration tests)
│   ├── Dockerfile              # Backend container definition
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # Header, BotControlBar, ActivePositionCard, AnalyticsCard, SecurityAuditCard, etc.
│   │   ├── services/           # Typed REST & WebSocket client
│   │   ├── types/              # TypeScript trading contracts
│   │   ├── App.tsx             # Main dashboard
│   │   └── index.css           # Tailwind CSS & dark terminal theme
│   ├── Dockerfile              # Frontend multi-stage container
│   ├── nginx.conf              # Nginx reverse proxy
│   ├── package.json
│   └── vite.config.ts
├── data/                       # Historical candles & cache
├── docs/
│   └── LIVE_EXPERIMENT_RUNBOOK.md # Production 7-day operating protocol & emergency drills
├── models/                     # Saved XGBoost binaries & RobustScaler registry
├── docker-compose.yml          # Container orchestration
├── .env.example
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

# Run automated tests (61 tests)
backend\.venv\Scripts\pytest backend/tests/ -v

# Launch the FastAPI backend server
backend\.venv\Scripts\uvicorn backend.app.main:app --reload --port 8000
```

* API Root: `http://127.0.0.1:8000`
* Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/api/v1/health`
* Live WebSocket Feed: `ws://127.0.0.1:8000/api/v1/ws/stream`

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

## 📡 REST & WebSocket API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health, database connection, and runtime mode |
| `GET` | `/api/v1/trading/bot/status` | Autonomous trading daemon status, wallet balance, and risk snapshot |
| `POST` | `/api/v1/trading/bot/start` | Start autonomous trading loop (`?symbol=BTCUSDT&timeframe=15m`) |
| `POST` | `/api/v1/trading/bot/stop` | Gracefully stop the autonomous trading loop |
| `GET` | `/api/v1/trading/position` | Inspect currently open active trade position |
| `POST` | `/api/v1/trading/position/close` | Manually close open position at live market price |
| `POST` | `/api/v1/trading/paper/reset` | Reset paper trading wallet to `$50.00 USD` baseline |
| `GET` | `/api/v1/analytics/performance` | Institutional metrics: Sharpe, Sortino, Win Rate, Expectancy |
| `GET` | `/api/v1/security/audit` | Comprehensive security checklist, permission check, rate limiter status |
| `POST` | `/api/v1/status/kill-switch` | Immediate emergency shutdown trigger |
| `WS` | `/api/v1/ws/stream` | Real-time ticker, decision, trade, and equity updates |

---

## 🧪 Testing & Verification

Run the complete 61-test async test suite:

```powershell
backend\.venv\Scripts\pytest backend/tests/ -v
```

```
============================= test session starts =============================
collected 61 items

backend/tests/test_api.py ................................... [ 6%]
backend/tests/test_backtest.py .............................. [ 14%]
backend/tests/test_config.py ................................ [ 21%]
backend/tests/test_data_validator.py ........................ [ 29%]
backend/tests/test_database.py .............................. [ 34%]
backend/tests/test_exchange_interface.py .................... [ 39%]
backend/tests/test_features.py .............................. [ 49%]
backend/tests/test_ml.py .................................... [ 55%]
backend/tests/test_paper_trading.py ......................... [ 67%]
backend/tests/test_risk_and_strategy.py ..................... [ 77%]
backend/tests/test_security_audit.py ........................ [ 86%]
backend/tests/test_testnet_execution.py ..................... [ 95%]
backend/tests/test_ws_and_analytics.py ...................... [100%]

============================= 61 passed in 4.02s ==============================
```

---

## 📖 7-Day Live Experiment Runbook

For complete instructions on running the 7-day autonomous experiment with $50 capital, including day-by-day routines, metrics scorecards, and emergency incident drills, see [docs/LIVE_EXPERIMENT_RUNBOOK.md](docs/LIVE_EXPERIMENT_RUNBOOK.md).

---

## 🌿 Git Workflow & Branches

```bash
# Main production branch
git checkout main

# Feature development branch
git checkout -b feature/phase-1-2-core-market-engine
```

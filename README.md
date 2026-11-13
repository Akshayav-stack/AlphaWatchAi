# AlphaWatch AI — ASTRAQUANT X 2026 (Problem Statement 16)

> **Offline Algorithmic Trading Intelligence Workstation for the Indian Stock Market**  
> *Academic, Educational, and Research Platform — Not Financial Advice.*

---

## 1. Architecture Overview (3-Tier Decoupled System)

AlphaWatch AI is structured into three clean, decoupled tiers with strict data and security boundaries:

```
[ Browser UI ]
      │  (HTTP / Session Cookies / Local Plotly.js)
      ▼
┌────────────────────────────────────────────────────────┐
│  /frontend  (React 18 + Vite + Tailwind CSS)           │
│  - Port 3000 (proxies /api to 5000)                   │
│  - 100% Offline: Local Plotly.js in public/vendor/     │
│  - Dark navy fintech theme, zero horizontal scroll     │
└──────────────────────────┬─────────────────────────────┘
                           │  HTTP / CSRF Protected
                           ▼
┌────────────────────────────────────────────────────────┐
│  /server  (Node.js + Express + SQLite)                 │
│  - Port 5000 (Public API Gateway for Browser)          │
│  - Argon2 password hashing (min 10 chars, blacklist)   │
│  - Signed HttpOnly, Secure, SameSite=Lax cookies       │
│  - Rate limiting & 15-min lockout after 5 failures     │
│  - Parameterized queries with strict user_id isolation │
│  - Only tier that touches the user database            │
└──────────────────────────┬─────────────────────────────┘
                           │  Internal Loopback HTTP only
                           │  (127.0.0.1:8001 - No DB access)
                           ▼
┌────────────────────────────────────────────────────────┐
│  /ml-service  (Python FastAPI Internal)                │
│  - Port 8001 (Private to Node, NEVER exposed to web)   │
│  - Direct import of quant engines in src/*             │
│  - Zero lookahead bias, past-only features             │
│  - Walk-forward ML, calibrated probabilities, SHAP     │
│  - Risk analytics (volatility, VaR, CVaR, positive loss)│
│  - Backtest engine (T+1 Open, STT, brokerage, slippage)│
└────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```text
AlphaWatchAI/
├── .env                        # Active environment configuration
├── .env.example                # Template environment configuration
├── .gitignore                  # Git exclusions for databases, venv, node_modules, and secrets
├── package.json                # Root process orchestrator (concurrently)
├── README.md                   # System documentation and Windows run guide
├── frontend/                   # React + Vite + Tailwind Client (Tier 1)
│   ├── package.json
│   ├── vite.config.js          # Proxies /api to port 5000
│   ├── tailwind.config.js      # Dark navy fintech design tokens
│   ├── public/
│   │   ├── favicon.ico
│   │   └── vendor/plotly.min.js # Local offline Plotly bundle (zero CDN)
│   └── src/
├── server/                     # Node.js + Express Gateway & Database (Tier 2)
│   ├── package.json
│   ├── src/                    # Auth, Session, SQLite ORM, Zod validation, ML Proxy
│   └── tests/                  # Security, Auth, and IDOR unit tests
├── ml-service/                 # Internal Python FastAPI Microservice (Tier 3)
│   ├── requirements.txt
│   └── main.py                 # Pure calculation endpoints wrapping src/
├── src/                        # Preserved Quantitative & Machine Learning Core
│   ├── data_loader.py          # Unified offline price loader & manifest
│   ├── features.py             # Past-only technical indicators & binary target
│   ├── models.py               # Walk-forward Random Forest, Logistic, SHAP
│   ├── signals.py              # Profile thresholds (Conservative/Moderate/Aggressive)
│   ├── risk.py                 # Positive-loss convention, VaR, CVaR, 1y MaxDD
│   ├── portfolio.py            # Valuation, P&L, 30% concentration alerts
│   ├── backtest.py             # Next-day open execution with Indian market friction
│   ├── benchmark.py            # Hardware specs, inference latency & throughput
│   ├── paper_trading.py        # Virtual paper trade logger & ₹10L cash ledger
│   ├── auditor.py              # Claim Auditor evaluating empirical win rates
│   ├── ripple.py               # Macro & sector stress shock analyzer
│   └── profiler.py             # Rule-based investor pattern engine
├── data/
│   ├── raw/                    # Raw historical NSE & Screener files
│   └── processed/              # Verified data manifest (data_manifest.csv)
├── models/saved/               # Serialized model pipelines
├── reports/                    # Generated latency & performance JSONs
└── tests/                      # Python automated test suite (Pytest - 89 tests)
```

---

## 3. Windows Setup & Run Guide

### Prerequisites
- Windows 10 or 11 (64-bit)
- Node.js v20+ (tested on Node v26.13.0)
- Python 3.11+ (virtual environment located in `.\venv\`)

### One Command to Run All Three Services
From the project root in PowerShell:

```powershell
npm run dev:all
```

This single command starts:
1. `[ML]` Python FastAPI microservice on `http://127.0.0.1:8001`
2. `[SERVER]` Node.js Express Public API on `http://127.0.0.1:5000`
3. `[CLIENT]` Vite React Frontend on `http://127.0.0.1:3000`

Then open your browser at:  
👉 **http://127.0.0.1:3000**

---

### Running Individual Services (Optional)

If you prefer separate PowerShell terminal tabs:

**Terminal 1 — Python ML Microservice:**
```powershell
npm run dev:ml
```

**Terminal 2 — Node.js Express Public API:**
```powershell
npm run dev:server
```

**Terminal 3 — React Client:**
```powershell
npm run dev:frontend
```

---

## 4. Automated Testing

- **Run all tests (Python + Node):**
  ```powershell
  npm test
  ```
- **Run Python ML tests (89 tests):**
  ```powershell
  npm run test:python
  ```
- **Run Node API & Security tests:**
  ```powershell
  npm run test:node
  ```

---

## 5. Security Architecture

1. **Argon2 Password Hashing**: Passwords are salted and hashed with Argon2id; minimum 10 characters and screened against common password lists.
2. **Session Cookies**: Signed with `SESSION_SECRET`, set with `HttpOnly`, `SameSite=Lax`, and `Secure` (in production).
3. **Session Rotation**: Session tokens are regenerated on login to prevent session fixation.
4. **CSRF Protection**: Double-submit / cryptographic CSRF tokens on all state-changing endpoints (`POST`, `PUT`, `DELETE`).
5. **Rate Limiting & Account Lockout**: Enforced on authentication endpoints (5 login attempts/min, 3 registrations/min). Accounts are locked for 15 minutes after 5 consecutive failed logins.
6. **SQL Injection Defense**: Strict parameterized queries via SQLite. Zero raw string concatenation.
7. **Strict Ownership Check (IDOR Defense)**: Every database query is scoped to the authenticated `user_id` (`WHERE user_id = ?`).
8. **Isolated ML Service**: The Python ML service is strictly internal (`127.0.0.1:8001`). The browser never communicates with Python directly.
9. **Zero External Surface**: Local Plotly.js bundle, zero CDNs, zero cloud analytics, operates 100% offline.

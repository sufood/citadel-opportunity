# Opportunity Analyser

A full-stack web application that searches [tenders.gov.au](https://www.tenders.gov.au/Atm) for Approach to Market (ATM) opportunities, extracts structured details via browser automation, and downloads associated documents — all through a clean React UI with real-time progress updates.

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend framework** | FastAPI (Python 3.12, async) | Native async support pairs well with Playwright's async API; built-in OpenAPI docs make the API self-documenting |
| **Browser automation** | Playwright (async, Chromium) | Handles JavaScript-rendered pages, authenticated sessions, and file downloads — all things `requests`/`httpx` can't do against this site |
| **HTML parsing** | BeautifulSoup4 | Simpler and more forgiving than lxml for scraping semi-structured government HTML |
| **Data validation** | Pydantic v2 + pydantic-settings | Enforces schema at the boundary; settings load cleanly from `.env` with typed defaults |
| **Frontend framework** | React 19 + TypeScript | Type safety across the frontend; component model fits the panel-based layout |
| **Build tool** | Vite | Sub-second HMR; handles TypeScript and Tailwind without config overhead |
| **Server state** | TanStack Query (React Query) | Automatic caching, deduplication, and background refetch for API data |
| **UI state** | Zustand | Minimal boilerplate for cross-component state (selected ATM, active jobs) without prop drilling |
| **UI components** | shadcn/ui + Tailwind CSS v4 | Unstyled primitives that ship as source code — no runtime dependency, full control over markup |
| **Real-time updates** | Server-Sent Events (SSE) | One-directional server→client push is all we need for job progress; simpler than WebSockets and works through proxies |
| **Containerisation** | Docker + nginx | Multi-stage builds keep images small; nginx handles SPA routing and reverse-proxies API/SSE to the backend |

---

## Key Design Decisions

**Singleton browser context** — Playwright launches one persistent `BrowserContext` at startup and reuses it across all requests. This avoids the 2–3 second cold-start penalty of launching a browser per request and allows session cookies to persist across analysis and download operations.

**Session persistence** — After authenticating, the browser's cookie/storage state is saved to `tmp/.auth_state.json` and restored on restart. This means the app survives restarts without forcing a re-login.

**CloudFront bypass** — The target site blocks default headless user agents via CloudFront WAF. The browser service sets a realistic Chrome user agent to avoid 403 responses.

**Offline-first testing** — The extractor is tested against saved HTML snapshots (26 tests), not the live site. This keeps tests fast, deterministic, and network-independent.

**SSE over WebSockets** — Analysis and download jobs stream progress via SSE (`EventSource` on the client). SSE is unidirectional (server→client), needs no handshake upgrade, and works natively through nginx with `proxy_buffering off`.

**Background tasks with in-memory job store** — Long-running analysis/download operations run as FastAPI `BackgroundTask`s. Progress is tracked in an in-memory dict and streamed to the client. This avoids the complexity of Celery/Redis for what is fundamentally a single-user tool.

---

## Prerequisites

- **Python 3.12+**
- **Node.js 22+** and npm
- A registered account on [tenders.gov.au](https://www.tenders.gov.au) (for document downloads)

---

## Installation

### 1. Clone and set up the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `backend/.env` with your credentials:

```
TENDERS_USERNAME=your_email@example.com
TENDERS_PASSWORD=your_password
TMP_DIR=./tmp
BROWSER_HEADLESS=true
```

Set `BROWSER_HEADLESS=false` to watch the browser during development — useful for debugging selectors and login flow.

### 3. Set up the frontend

```bash
cd frontend
npm install
```

---

## Running (Development)

Start both services — the frontend dev server proxies `/api` requests to the backend automatically.

**Terminal 1 — Backend:**

```bash
cd backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running (Docker)

```bash
docker compose up --build
```

This starts:
- **Backend** on port `8000` — FastAPI + Playwright with Chromium
- **Frontend** on port `5173` — nginx serving the built React app, proxying API and SSE to the backend

Extracted data persists in `backend/tmp/` via a volume mount.

Open [http://localhost:5173](http://localhost:5173).

---

## Usage

1. **Search** — Enter a keyword (e.g. "software", "cloud") and press Enter
2. **Analyse** — Click any result row; the app automatically extracts the full ATM detail page and streams progress via SSE
3. **View details** — Once analysis completes, the right panel shows all extracted fields: agency, dates, description, conditions, contact info, etc.
4. **Download documents** — Click "Download All" in the Documents section to authenticate and download all attached PDFs/documents

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/search?keyword={kw}` | Search opportunities by keyword |
| `GET` | `/api/atm` | List all analysed ATM UUIDs |
| `GET` | `/api/atm/{id}` | Get extracted detail for a specific ATM |
| `POST` | `/api/atm/{id}/scrape` | Start background analysis job → returns `{job_id}` |
| `POST` | `/api/atm/{id}/download` | Start background document download → returns `{job_id}` |
| `GET` | `/api/atm/{id}/files` | List downloaded files for an ATM |
| `GET` | `/api/jobs/{id}/stream` | SSE stream of job progress |

Interactive API docs available at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend is running.

---

## Testing

```bash
cd backend
python3 -m pytest tests/ -v --asyncio-mode=auto
```

57 tests across 6 modules:
- `test_storage.py` — File I/O utilities (9 tests)
- `test_models.py` — Pydantic serialisation roundtrips (7 tests)
- `test_config.py` — Settings loading and validation (3 tests)
- `test_browser.py` — Browser launch, navigation, login flow (6 tests)
- `test_extractor.py` — Search + detail parsing against HTML fixtures (26 tests)
- `test_downloader.py` — Document download with mocked Playwright (6 tests)

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, lifespan, routers
│   │   ├── config.py            # pydantic-settings from .env
│   │   ├── routers/             # search, atm, documents, jobs (SSE)
│   │   ├── services/
│   │   │   ├── browser.py       # Singleton Playwright context + login
│   │   │   ├── extractor.py     # Search + ATM detail parsing
│   │   │   ├── downloader.py    # Authenticated document downloads
│   │   │   └── storage.py       # tmp/ directory + JSON file I/O
│   │   └── models/              # Pydantic schemas (ATMDetail, JobStatus)
│   ├── tests/                   # 57 tests with HTML fixtures
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # SearchBar, ResultsTable, ATMDetailPanel,
│   │   │                        # DocumentList, JobProgress + shadcn/ui
│   │   ├── hooks/               # useSearch, useATMDetail, useJobStatus
│   │   ├── api/client.ts        # Typed axios wrapper
│   │   ├── store/appStore.ts    # Zustand state
│   │   └── types/atm.ts         # TypeScript interfaces
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── docker-compose.yml
```

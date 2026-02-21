# Tenders Scraper — TODO

Progress tracker for Claude Code. Work through tasks in order — each phase depends on the previous.

---

## Phase 1 — Project Scaffold ✅

- [x] Initialise git repo with `.gitignore` (exclude `tmp/`, `.env`, `__pycache__/`, `node_modules/`, `.playwright/`)
- [x] Create `backend/` directory structure as per `CLAUDE.md`
- [x] Create `frontend/` directory structure as per `CLAUDE.md`
- [x] Create `backend/.env.example` with `TENDERS_USERNAME`, `TENDERS_PASSWORD`, `TMP_DIR`, `BROWSER_HEADLESS`
- [x] Create `backend/.env` with real credentials (do not commit)
- [x] Create `backend/requirements.txt` with: `fastapi`, `uvicorn[standard]`, `playwright`, `beautifulsoup4`, `pydantic[email]`, `pydantic-settings`, `python-dotenv`, `aiofiles`
- [x] Run `pip install -r requirements.txt` and `playwright install chromium`
- [x] Scaffold Vite + React + TypeScript frontend: `npm create vite@latest frontend -- --template react-ts`
- [x] Install frontend dependencies: `npm install @tanstack/react-query zustand axios`
- [x] Install shadcn/ui and Tailwind CSS in frontend
- [x] Create `docker-compose.yml` stub (backend + frontend services)

---

## Phase 2 — Backend: Core Services ✅

### 2a. Storage Service (`backend/app/services/storage.py`)
- [x] Implement `create_atm_dir(uuid: str) -> Path` — creates `./tmp/{uuid}/` with `mkdir(parents=True, exist_ok=True)`
- [x] Implement `write_json(uuid: str, filename: str, data: dict)` — writes indented JSON to `./tmp/{uuid}/{filename}`
- [x] Implement `list_atm_dirs() -> list[str]` — returns all UUID subdirectories in `./tmp/`
- [x] Write unit tests for storage functions using a temp directory fixture

### 2b. Pydantic Models (`backend/app/models/`)
- [x] Create `models/atm.py` with `ContactDetails` and `ATMDetail` models (all fields from CLAUDE.md)
- [x] Create `models/job.py` with `JobStatus` model: `job_id`, `status`, `steps: list[str]`, `complete: bool`, `error: str | None`
- [x] Verify models serialise/deserialise correctly with test data

### 2c. Config (`backend/app/config.py`)
- [x] Implement `Settings` class using `pydantic-settings` loading from `.env`
- [x] Expose a `get_settings()` dependency for FastAPI injection
- [x] Confirm settings load correctly and raise clear errors for missing required vars

---

## Phase 3 — Backend: Browser Automation ✅

### 3a. Browser Service (`backend/app/services/browser.py`)
- [x] Implement singleton `BrowserService` class with async init
- [x] Launch Chromium with `headless` flag from settings
- [x] Implement `get_context()` — returns persistent `BrowserContext`, creating if not exists
- [x] Implement `save_session(path)` — calls `context.storage_state(path=path)`
- [x] Implement `restore_session(path)` — restores context from saved state file if it exists
- [x] Add `close()` method for graceful shutdown on app exit (use FastAPI lifespan)

### 3b. Login Flow (`backend/app/services/browser.py` or `downloader.py`)
- [x] Navigate to `https://www.tenders.gov.au/Atm/ViewDocuments/{uuid}` with a known test UUID
- [x] Identify login form selectors (run with `BROWSER_HEADLESS=false` to inspect)
- [x] Implement `login(page, username, password)` — fill fields and click Login button
- [x] Wait for successful login redirect/confirmation
- [x] Save session state to `./tmp/.auth_state.json` after successful login
- [x] Test session restore: confirm subsequent requests skip re-login

---

## Phase 4 — Backend: Extraction ✅

### 4a. Search Results Extraction (`backend/app/services/extractor.py`)
- [x] Navigate to `https://www.tenders.gov.au/Atm?filter=published&Keyword={keyword}`
- [x] Wait for `networkidle`
- [x] Extract all `<a class="detail" href="/Atm/Show/{uuid}">` elements
- [x] Return list of `{uuid, title, href}` dicts
- [x] Save a raw HTML snapshot of the search results page for offline testing

### 4b. ATM Detail Extraction (`backend/app/services/extractor.py`)
- [x] Navigate to `https://www.tenders.gov.au/Atm/Show/{uuid}` with test UUID
- [x] Wait for `networkidle`
- [x] Save raw HTML snapshot of the detail page for offline testing
- [x] Extract `window.dataLayer` via `page.evaluate("() => window.dataLayer")`
- [x] Write result to `./tmp/{uuid}/data-layer.json`
- [x] Parse `<div class="box boxW listInner">` with BeautifulSoup4
- [x] Extract each field listed in CLAUDE.md and map to `ATMDetail` model (all 19 fields)
- [x] Write result to `./tmp/{uuid}/atm-details.json`
- [x] Test extractor against saved HTML snapshots (no network) — 26 tests

---

## Phase 5 — Backend: Document Downloading ✅

### 5a. Downloader Service (`backend/app/services/downloader.py`)
- [x] Navigate to `https://www.tenders.gov.au/Atm/ViewDocuments/{uuid}` (reuse authenticated context)
- [x] Wait for `networkidle`
- [x] Enumerate all downloadable file links on the page
- [x] For each link, use `page.expect_download()` to intercept and save to `./tmp/{uuid}/{filename}`
- [x] Return list of saved file paths
- [x] Handle edge case: no documents available
- [x] Handle edge case: session expired mid-download (re-login and retry)

---

## Phase 6 — Backend: FastAPI Routers & App ✅

### 6a. Jobs Router (`backend/app/routers/jobs.py`)
- [x] Create in-memory `job_store: dict[str, JobStatus]`
- [x] Implement `GET /api/jobs/{job_id}/stream` — SSE endpoint using `StreamingResponse`
- [x] Stream `JobStatus` JSON at 500ms intervals until `complete=True`
- [x] Expose `update_job(job_id, step, complete, error)` helper for other services to call

### 6b. Search Router (`backend/app/routers/search.py`)
- [x] Implement `GET /api/search?keyword={keyword}`
- [x] Call extractor search function and return list of ATM summaries
- [x] Include UUID, title, and detail URL in each result

### 6c. ATM Router (`backend/app/routers/atm.py`)
- [x] Implement `POST /api/atm/{atm_id}/scrape` — triggers background scrape job, returns `job_id`
- [x] Background task: create dir → extract dataLayer → extract ATM details → update job steps
- [x] Implement `GET /api/atm/{atm_id}` — returns `atm-details.json` contents for a given UUID
- [x] Implement `GET /api/atm` — lists all UUIDs with scraped data in `./tmp/`

### 6d. Documents Router (`backend/app/routers/documents.py`)
- [x] Implement `POST /api/atm/{atm_id}/download` — triggers authenticated download job
- [x] Background task: login if needed → download all documents → update job steps
- [x] Implement `GET /api/atm/{atm_id}/files` — lists files in `./tmp/{atm_id}/`

### 6e. Main App (`backend/app/main.py`)
- [x] Create FastAPI app with lifespan (init browser on startup, close on shutdown)
- [x] Register all routers with `/api` prefix
- [x] Add CORS middleware allowing frontend origin
- [x] Serve `./tmp/` as a static files directory for direct file access
- [x] Test all endpoints with `curl` or FastAPI's built-in `/docs` Swagger UI

---

## Phase 7 — Frontend ✅

### 7a. Type Generation
- [x] Created manual TypeScript types matching backend Pydantic models

### 7b. API Client (`frontend/src/api/client.ts`)
- [x] Created typed `axios` wrapper for all backend endpoints
- [x] Functions: `searchATMs(keyword)`, `scrapeATM(id)`, `getATMDetail(id)`, `downloadDocuments(id)`, `listFiles(id)`

### 7c. Zustand Store (`frontend/src/store/appStore.ts`)
- [x] State: `selectedAtmId`, `searchResults`, `activeJobs`, `scrapeJobId`, `downloadJobId`
- [x] Actions: `setSelected`, `setResults`, `updateJob`

### 7d. Hooks
- [x] `useSearch(keyword)` — TanStack Query wrapping `searchATMs`
- [x] `useATMDetail(id)` — TanStack Query wrapping `getATMDetail`
- [x] `useJobStatus(jobId)` — `EventSource` hook returning live `JobStatus`

### 7e. Components
- [x] `SearchBar.tsx` — keyword input + submit, triggers search
- [x] `ResultsTable.tsx` — displays search results with loading skeletons
- [x] `JobProgress.tsx` — shows live SSE step list and completion status
- [x] `ATMDetailPanel.tsx` — displays all `ATMDetail` fields with loading skeleton
- [x] `DocumentList.tsx` — shows downloaded files with links, download-all button

### 7f. App Shell (`frontend/src/App.tsx`)
- [x] Layout: SearchBar top, ResultsTable left panel, ATMDetailPanel + DocumentList right panel
- [x] Wrap app with `QueryClientProvider`
- [x] Wire `selectedAtmId` from store to detail panel and document list

---

## Phase 8 — Docker & Polish

- [x] Complete `backend/Dockerfile` — Python 3.12 base, install deps, install Playwright Chromium
- [x] Complete `frontend/Dockerfile` — Node build stage + nginx serve stage
- [x] Complete `docker-compose.yml` — mount `./tmp/` as volume, pass `.env` to backend
- [x] Test full flow end-to-end: search → scrape → view details → download documents
- [ ] Add `README.md` with setup instructions, `.env` configuration, and usage guide
- [x] Add error handling UI (toast notifications for failed jobs)
- [x] Add loading skeletons for ResultsTable and ATMDetailPanel

---

## Known Test UUID

Use `60e02e43-1969-4d7b-83e4-f953caf81d5c` as the fixture UUID throughout development.

- Detail page: `https://www.tenders.gov.au/Atm/Show/60e02e43-1969-4d7b-83e4-f953caf81d5c`
- Documents: `https://www.tenders.gov.au/Atm/ViewDocuments/60e02e43-1969-4d7b-83e4-f953caf81d5c`

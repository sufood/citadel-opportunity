# Opportunity Analyser — Claude Code Instructions

## Project Overview

An interactive web application that crawls **https://www.tenders.gov.au/Atm** to search for ATM (Approach to Market) opportunities by keyword, extract structured details, authenticate, and download associated documents.

### robots.txt compliance
- `/Atm/*` paths are **allowed** — all target URLs are under this path
- Do **not** use `/Search/*` query paths; use `/Atm` with filter query strings instead
- Disallowed: `/Search/*`, `/Reports/*`, `/Cn/List*`, `/Son/List*`, `/admin*`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (Python 3.11+, async) |
| Browser automation | Playwright (async, Python) |
| HTML parsing | BeautifulSoup4 |
| Data validation | Pydantic v2 |
| Config/secrets | pydantic-settings + `.env` |
| Frontend framework | React 18 + TypeScript |
| Build tool | Vite |
| Server state | TanStack Query (React Query) |
| UI state | Zustand |
| UI components | shadcn/ui + Tailwind CSS |
| Real-time updates | Server-Sent Events (SSE) via FastAPI StreamingResponse |
| Type generation | openapi-typescript (FastAPI → TypeScript types) |

---

## Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS, router registration
│   │   ├── config.py                # pydantic-settings, .env loading
│   │   ├── routers/
│   │   │   ├── search.py            # GET /api/search?keyword=&filter=
│   │   │   ├── atm.py               # POST /api/atm/{id}/scrape, GET /api/atm/{id}
│   │   │   ├── documents.py         # POST /api/atm/{id}/download
│   │   │   └── jobs.py              # GET /api/jobs/{id}/stream (SSE)
│   │   ├── services/
│   │   │   ├── browser.py           # Singleton Playwright browser/context manager
│   │   │   ├── extractor.py         # dataLayer + ATM detail HTML parsing
│   │   │   ├── downloader.py        # Authenticated document downloading
│   │   │   └── storage.py           # tmp dir creation, JSON file I/O per UUID
│   │   └── models/
│   │       ├── atm.py               # Pydantic ATMDetail, ContactDetails models
│   │       └── job.py               # JobStatus model
│   ├── tmp/                         # Runtime output — one subdir per ATM UUID
│   │   └── {uuid}/
│   │       ├── data-layer.json
│   │       ├── atm-details.json
│   │       └── *.pdf / *.docx
│   ├── .env                         # Secrets — never commit
│   ├── .env.example                 # Committed template
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultsTable.tsx
│   │   │   ├── ATMDetailPanel.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── JobProgress.tsx
│   │   ├── hooks/
│   │   │   ├── useSearch.ts
│   │   │   ├── useATMDetail.ts
│   │   │   └── useJobStatus.ts
│   │   ├── api/
│   │   │   └── client.ts            # Typed fetch/axios wrapper
│   │   ├── types/
│   │   │   └── atm.ts               # Shared TypeScript types (or generated)
│   │   ├── store/
│   │   │   └── appStore.ts          # Zustand store
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── docker-compose.yml
```

---

## Key Implementation Details

### Browser Service (`services/browser.py`)
- Use a **singleton** persistent `BrowserContext` — do not launch a new browser per request
- Save session state to `./tmp/.auth_state.json` using `context.storage_state()`
- Restore saved session on startup to avoid re-login on every app restart
- Use `page.wait_for_load_state('networkidle')` before scraping any page
- Run headless by default; `BROWSER_HEADLESS=false` in `.env` for debugging

### Extractor Service (`services/extractor.py`)

**dataLayer extraction:**
```python
data_layer = await page.evaluate("() => window.dataLayer")
# Write to ./tmp/{uuid}/data-layer.json
```

**ATM detail extraction:**
- Target DOM: `<div class="box boxW listInner">`
- Use BeautifulSoup4 on `await page.content()`
- Map yes/no text to booleans for: `multi_agency_access`, `panel_arrangement`, `multi_stage`
- Extract `href` attributes for: Addenda, ATM Documents, Lodgement Page
- Extract name/phone/email from Contact Details section

### Storage Service (`services/storage.py`)
- Base tmp dir: `./tmp/` (configurable via `TMP_DIR` env var)
- Create `./tmp/{uuid}/` with `pathlib.Path.mkdir(parents=True, exist_ok=True)`
- Write `data-layer.json` and `atm-details.json` using `json.dumps(..., indent=2)`

### Authentication (`services/browser.py` / `services/downloader.py`)
- Login URL: `https://www.tenders.gov.au/Atm/ViewDocuments/{uuid}`
- Fill username/password fields and click the Login button
- After login, save `storage_state` so subsequent requests reuse the session
- Credentials come from `.env`: `TENDERS_USERNAME`, `TENDERS_PASSWORD`

### Document Downloads
- After login, enumerate all download links on the ViewDocuments page
- Use Playwright's `page.expect_download()` context manager
- Save each file to `./tmp/{uuid}/{suggested_filename}`

### Job Progress (SSE)
- Every long-running scrape task updates a shared in-memory `job_store: dict[str, JobStatus]`
- `GET /api/jobs/{id}/stream` streams SSE events at 500ms intervals until `status.complete`
- Frontend uses native `EventSource` API — no library needed

### Pydantic Models (`models/atm.py`)
```python
class ContactDetails(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None

class ATMDetail(BaseModel):
    atm_id: str
    agency: str | None = None
    category: str | None = None
    close_date: str | None = None
    publish_date: str | None = None
    location: str | None = None
    atm_type: str | None = None
    multi_agency_access: bool | None = None
    panel_arrangement: bool | None = None
    multi_stage: bool | None = None
    description: str | None = None
    other_instructions: str | None = None
    conditions_for_participation: str | None = None
    timeframe_for_delivery: str | None = None
    address_for_lodgement: str | None = None
    addenda_url: str | None = None
    contact_details: ContactDetails | None = None
    document_urls: list[str] = []
    lodgement_url: str | None = None
```

### Config (`config.py`)
```python
class Settings(BaseSettings):
    tenders_username: str
    tenders_password: str
    tmp_dir: Path = Path("./tmp")
    browser_headless: bool = True
    model_config = SettingsConfigDict(env_file=".env")
```

### `.env.example`
```
TENDERS_USERNAME=your_username_here
TENDERS_PASSWORD=your_password_here
TMP_DIR=./tmp
BROWSER_HEADLESS=true
```

---

## Target URLs

| Purpose | URL Pattern |
|---|---|
| Search/list | `https://www.tenders.gov.au/Atm?filter=published&Keyword={keyword}` |
| Full detail | `https://www.tenders.gov.au/Atm/Show/{uuid}` |
| Documents (login required) | `https://www.tenders.gov.au/Atm/ViewDocuments/{uuid}` |

### UUID Extraction
UUIDs appear in the `href` of `.detail` anchor tags in list results:
```html
<a class="detail" href="/Atm/Show/60e02e43-1969-4d7b-83e4-f953caf81d5c" title="Full Details for ...">Full Details</a>
```
Regex pattern: `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`

---

## Development Guidelines

- All backend code must be **async** — use `async def` and `await` throughout
- Never hardcode credentials — always read from `Settings()`
- Always `await page.wait_for_load_state('networkidle')` before extracting content
- Use `try/except` around all Playwright page interactions — government sites are unreliable
- Log progress steps to the `job_store` so the frontend SSE stream reflects real status
- `tmp/` directory should be in `.gitignore`
- `.env` should be in `.gitignore`; `.env.example` should be committed
- Run Playwright in non-headless mode (`BROWSER_HEADLESS=false`) when debugging selectors

---

## Build Order (follow this sequence)

1. `storage.py` — directory + file I/O utilities
2. `models/atm.py` + `models/job.py` — Pydantic schemas
3. `config.py` — settings from `.env`
4. `browser.py` — Playwright singleton, login, session persistence
5. `extractor.py` — dataLayer + ATM detail parsing (test with saved HTML snapshots)
6. `downloader.py` — authenticated document downloads
7. FastAPI routers — wire services to HTTP endpoints + SSE
8. `main.py` — app setup, CORS, router registration
9. Frontend — `SearchBar` → `ResultsTable` → `ATMDetailPanel` → `JobProgress` → `DocumentList`
10. Docker Compose — containerise backend + frontend

---

## Testing Approach

- Test `extractor.py` using **saved HTML snapshots** from the target site — avoid hitting the network on every test run
- Use a known working ATM UUID (e.g. `60e02e43-1969-4d7b-83e4-f953caf81d5c`) as a fixture
- Test the login flow with `BROWSER_HEADLESS=false` first so you can observe form interaction
- Verify `data-layer.json` and `atm-details.json` are correctly written to `./tmp/{uuid}/` after each extraction

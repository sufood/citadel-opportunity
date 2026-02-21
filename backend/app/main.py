import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import atm, documents, jobs, search, triage
from app.services.browser import BrowserService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: launch browser. Shutdown: close browser."""
    logger.info("Starting browser service")
    svc = await BrowserService.get_instance()
    yield
    logger.info("Shutting down browser service")
    await svc.close()


app = FastAPI(
    title="Opportunity Analyser API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(jobs.router)
app.include_router(search.router)
app.include_router(atm.router)
app.include_router(documents.router)
app.include_router(triage.router)

# Serve tmp/ as static files for direct file access
settings = get_settings()
settings.tmp_dir.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(settings.tmp_dir)), name="files")


@app.get("/api/health")
async def health():
    return {"status": "ok"}

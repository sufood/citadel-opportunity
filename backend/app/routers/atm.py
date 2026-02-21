import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.atm import ATMDetail
from app.routers.jobs import create_job, update_job
from app.services.browser import BrowserService
from app.services.extractor import extract_atm_detail
from app.services.storage import list_atm_dirs, read_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/atm", tags=["atm"])


@router.get("")
async def list_atms() -> list[str]:
    """List all ATM UUIDs with scraped data."""
    return list_atm_dirs()


@router.get("/{atm_id}")
async def get_atm(atm_id: str) -> ATMDetail:
    """Get scraped ATM details for a given UUID."""
    data = read_json(atm_id, "atm-details.json")
    if not data:
        raise HTTPException(status_code=404, detail="ATM data not found. Scrape it first.")
    return ATMDetail(**data)


@router.post("/{atm_id}/scrape")
async def scrape_atm(atm_id: str, background_tasks: BackgroundTasks) -> dict:
    """Trigger a background scrape job for an ATM. Returns job_id."""
    job_id = create_job()
    background_tasks.add_task(_run_scrape, job_id, atm_id)
    return {"job_id": job_id}


async def _run_scrape(job_id: str, atm_id: str) -> None:
    """Background task: scrape ATM detail page."""
    svc = await BrowserService.get_instance()
    page = await svc.new_page()
    try:
        update_job(job_id, step="Starting scrape", status="running")

        update_job(job_id, step="Navigating to ATM detail page")
        detail = await extract_atm_detail(page, atm_id)

        update_job(job_id, step=f"Extracted details for {detail.atm_id}")
        update_job(job_id, step="Scrape complete", complete=True)

        logger.info("Scrape completed for %s", atm_id)
    except Exception as e:
        logger.exception("Scrape failed for %s", atm_id)
        update_job(job_id, error=str(e))
    finally:
        await page.close()

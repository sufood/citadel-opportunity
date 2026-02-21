import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.routers.jobs import create_job, update_job
from app.services.downloader import download_documents
from app.services.storage import list_files

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/atm", tags=["documents"])


@router.post("/{atm_id}/download")
async def download_atm_documents(
    atm_id: str, background_tasks: BackgroundTasks
) -> dict:
    """Trigger authenticated document download for an ATM. Returns job_id."""
    job_id = create_job()
    background_tasks.add_task(_run_download, job_id, atm_id)
    return {"job_id": job_id}


@router.get("/{atm_id}/files")
async def get_atm_files(atm_id: str) -> list[str]:
    """List downloaded files for an ATM."""
    files = list_files(atm_id)
    if not files:
        raise HTTPException(status_code=404, detail="No files found. Download them first.")
    return files


async def _run_download(job_id: str, atm_id: str) -> None:
    """Background task: download documents for an ATM."""
    try:
        update_job(job_id, step="Starting document download", status="running")
        update_job(job_id, step="Authenticating")

        paths = await download_documents(atm_id)

        for p in paths:
            update_job(job_id, step=f"Downloaded {p.name}")

        update_job(
            job_id,
            step=f"Download complete — {len(paths)} files",
            complete=True,
        )
        logger.info("Downloaded %d files for %s", len(paths), atm_id)
    except Exception as e:
        logger.exception("Download failed for %s", atm_id)
        update_job(job_id, error=str(e))

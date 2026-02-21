import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.triage import TriageResult
from app.routers.jobs import create_job, update_job
from app.services.triage import get_cached_triage, run_triage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/atm", tags=["triage"])


@router.post("/{atm_id}/triage")
async def triage_atm(atm_id: str, background_tasks: BackgroundTasks) -> dict:
    """Trigger AI triage scoring for an ATM. Returns job_id."""
    job_id = create_job()
    background_tasks.add_task(_run_triage, job_id, atm_id)
    return {"job_id": job_id}


@router.get("/{atm_id}/triage", response_model=TriageResult)
async def get_triage_result(atm_id: str) -> TriageResult:
    """Get the cached triage result for an ATM."""
    result = get_cached_triage(atm_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No triage result found. Run triage first.")
    return result


async def _run_triage(job_id: str, atm_id: str) -> None:
    """Background task: run triage scoring for an ATM."""
    try:
        update_job(job_id, step="Starting triage analysis", status="running")

        def on_step(msg: str) -> None:
            update_job(job_id, step=msg)

        result = await run_triage(atm_id, on_step=on_step)

        update_job(
            job_id,
            step=f"Triage complete — {result.total}/100 ({result.band})",
            complete=True,
        )
    except Exception as e:
        logger.exception("Triage failed for %s", atm_id)
        update_job(job_id, error=str(e))

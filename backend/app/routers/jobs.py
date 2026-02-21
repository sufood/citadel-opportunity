import asyncio
import json
import logging
import uuid as uuid_mod

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.job import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# In-memory job store — shared across routers
job_store: dict[str, JobStatus] = {}


def create_job() -> str:
    """Create a new job and return its ID."""
    job_id = str(uuid_mod.uuid4())
    job_store[job_id] = JobStatus(job_id=job_id, status="pending")
    return job_id


def update_job(
    job_id: str,
    step: str | None = None,
    status: str | None = None,
    complete: bool = False,
    error: str | None = None,
) -> None:
    """Update a job's progress. Called by background tasks."""
    job = job_store.get(job_id)
    if not job:
        logger.warning("Attempted to update unknown job: %s", job_id)
        return

    if step:
        job.steps.append(step)
    if status:
        job.status = status
    if complete:
        job.complete = True
        job.status = "completed"
    if error:
        job.error = error
        job.complete = True
        job.status = "failed"


@router.get("/{job_id}")
async def get_job(job_id: str) -> JobStatus:
    """Get current job status."""
    job = job_store.get(job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/stream")
async def stream_job(job_id: str) -> StreamingResponse:
    """SSE endpoint — streams JobStatus JSON at 500ms intervals until complete."""

    async def event_stream():
        while True:
            job = job_store.get(job_id)
            if not job:
                data = json.dumps({"error": "Job not found"})
                yield f"data: {data}\n\n"
                return

            data = job.model_dump_json()
            yield f"data: {data}\n\n"

            if job.complete:
                return

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

from pydantic import BaseModel


class JobStatus(BaseModel):
    job_id: str
    status: str = "pending"
    steps: list[str] = []
    complete: bool = False
    error: str | None = None

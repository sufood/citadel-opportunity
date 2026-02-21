from typing import Literal

from pydantic import BaseModel


class TriageResult(BaseModel):
    industry_match: int
    industry_rationale: str
    capability_match: int
    capability_rationale: str
    case_study_evidence: int
    case_study_rationale: str
    recommended_case_studies: list[str]
    differentiators: int
    differentiators_rationale: str
    total: int
    band: Literal["Pursue", "Qualify", "No Bid"]
    capability_gaps: list[str]
    key_differentiators: list[str]
    risks: list[str]
    summary: str

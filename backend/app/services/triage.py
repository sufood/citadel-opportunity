import asyncio
import json
import logging
from collections.abc import Callable
from functools import partial
from pathlib import Path

import anthropic
import pdfplumber
from docx import Document as DocxDocument

from app.config import get_settings
from app.models.triage import TriageResult
from app.services.storage import create_atm_dir, read_json, write_json

logger = logging.getLogger(__name__)

# Cached reference file contents — loaded once
_services_content: str | None = None
_case_studies_content: str | None = None
_triage_rubric: str | None = None

# Project root where the reference markdown files live.
# Walk up from this file until we find the reference data directory.
# Works both locally (4 levels up) and in Docker (3 levels up).
def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "citadel-edge-tender-triage-process.md").exists():
            return current
        current = current.parent
    raise FileNotFoundError(
        "Could not locate reference data (citadel-edge-*.md). "
        "Ensure reference markdown files are present in the project root."
    )


_PROJECT_ROOT = _find_project_root()


def _load_reference_file(filename: str) -> str:
    path = _PROJECT_ROOT / filename
    if not path.exists():
        raise FileNotFoundError(f"Reference file not found: {path}")
    return path.read_text(encoding="utf-8")


def _get_services() -> str:
    global _services_content
    if _services_content is None:
        _services_content = _load_reference_file("citadel-edge-services-industries.md")
    return _services_content


def _get_case_studies() -> str:
    global _case_studies_content
    if _case_studies_content is None:
        _case_studies_content = _load_reference_file("citadel-edge-case-studies.md")
    return _case_studies_content


def _get_triage_rubric() -> str:
    global _triage_rubric
    if _triage_rubric is None:
        _triage_rubric = _load_reference_file("citadel-edge-tender-triage-process.md")
    return _triage_rubric


def _extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        text_parts: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception:
        logger.exception("Failed to extract text from PDF: %s", path)
        return f"[Failed to extract text from {path.name}]"


def _extract_docx_text(path: Path) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = DocxDocument(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        logger.exception("Failed to extract text from DOCX: %s", path)
        return f"[Failed to extract text from {path.name}]"


def _extract_spreadsheet_text(path: Path) -> str:
    """Basic text extraction for CSV/XLS files."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        logger.exception("Failed to read spreadsheet: %s", path)
        return f"[Failed to read {path.name}]"


def read_all_content(
    uuid: str, on_step: Callable[[str], None] | None = None
) -> str:
    """
    Read every file in tmp/{uuid}/ and return combined text content.
    Handles JSON, PDF, DOCX, and CSV files.
    """
    dir_path = create_atm_dir(uuid)
    parts: list[str] = []

    files = sorted(
        f for f in dir_path.iterdir()
        if f.is_file() and f.name != "triage-result.json"
    )

    for file_path in files:
        suffix = file_path.suffix.lower()

        if on_step:
            on_step(f"Extracting text from {file_path.name}")

        if suffix == ".json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                content = json.dumps(data, indent=2)
            except Exception:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"=== {file_path.name} ===\n{content}")

        elif suffix == ".pdf":
            text = _extract_pdf_text(file_path)
            parts.append(f"=== {file_path.name} ===\n{text}")

        elif suffix in (".docx", ".doc"):
            text = _extract_docx_text(file_path)
            parts.append(f"=== {file_path.name} ===\n{text}")

        elif suffix in (".csv", ".xls", ".xlsx"):
            text = _extract_spreadsheet_text(file_path)
            parts.append(f"=== {file_path.name} ===\n{text}")

        else:
            parts.append(f"=== {file_path.name} ===\n[Unsupported file type: {suffix}]")

    return "\n\n".join(parts)


SYSTEM_PROMPT = """\
You are a tender triage analyst for Citadel Edge, an Australian technology company.

Your task is to score an incoming tender against Citadel Edge's capability profile using the scoring rubric provided. You have access to:
1. The full tender details and associated documents
2. Citadel Edge's services and industries profile
3. Citadel Edge's case studies (evidence of prior delivery)
4. The scoring rubric

Score the tender across four dimensions and provide a structured assessment. Be specific in your rationale — reference actual services, case studies by name, and concrete details from the tender documents.

IMPORTANT: Your scores MUST strictly follow the rubric ranges:
- Industry Match: 0-20
- Capability Match: 0-30
- Case Study Evidence: 0-30
- Differentiators: 0-20
- Total: sum of the four scores (0-100)

Band assignment:
- 75-100 = "Pursue"
- 50-74 = "Qualify"
- 0-49 = "No Bid"
"""


def _build_user_prompt(tender_content: str) -> str:
    return f"""\
## Scoring Rubric

{_get_triage_rubric()}

---

## Citadel Edge — Services & Industries

{_get_services()}

---

## Citadel Edge — Case Studies

{_get_case_studies()}

---

## Tender Content (all scraped data and downloaded documents)

{tender_content}

---

Score this tender now. Return your assessment as a JSON object matching the required schema."""


TRIAGE_TOOL = {
    "name": "submit_triage_result",
    "description": "Submit the structured triage result for this tender.",
    "input_schema": {
        "type": "object",
        "properties": {
            "industry_match": {
                "type": "integer",
                "description": "Industry match score (0-20)",
            },
            "industry_rationale": {
                "type": "string",
                "description": "Rationale for the industry match score",
            },
            "capability_match": {
                "type": "integer",
                "description": "Capability match score (0-30)",
            },
            "capability_rationale": {
                "type": "string",
                "description": "Rationale for the capability match score",
            },
            "case_study_evidence": {
                "type": "integer",
                "description": "Case study evidence score (0-30)",
            },
            "case_study_rationale": {
                "type": "string",
                "description": "Rationale for the case study evidence score",
            },
            "recommended_case_studies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of recommended case studies to include in the bid",
            },
            "differentiators": {
                "type": "integer",
                "description": "Differentiators score (0-20)",
            },
            "differentiators_rationale": {
                "type": "string",
                "description": "Rationale for the differentiators score",
            },
            "total": {
                "type": "integer",
                "description": "Total score (sum of all four dimensions, 0-100)",
            },
            "band": {
                "type": "string",
                "enum": ["Pursue", "Qualify", "No Bid"],
                "description": "Triage band based on total score",
            },
            "capability_gaps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Capability gaps that would need to be addressed",
            },
            "key_differentiators": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key differentiators to lead with in the bid",
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Risks to flag for this tender",
            },
            "summary": {
                "type": "string",
                "description": "Brief executive summary of the triage assessment",
            },
        },
        "required": [
            "industry_match",
            "industry_rationale",
            "capability_match",
            "capability_rationale",
            "case_study_evidence",
            "case_study_rationale",
            "recommended_case_studies",
            "differentiators",
            "differentiators_rationale",
            "total",
            "band",
            "capability_gaps",
            "key_differentiators",
            "risks",
            "summary",
        ],
    },
}


async def run_triage(uuid: str, on_step: Callable[[str], None] | None = None) -> TriageResult:
    """
    Run the full triage process for an ATM:
    1. Read all content from tmp/{uuid}/
    2. Call Claude with the scoring rubric + reference data
    3. Parse and persist the result

    Blocking I/O (file reads, Anthropic API call) runs in a thread pool
    so the event loop stays free for SSE delivery.
    """
    loop = asyncio.get_running_loop()

    async def step(msg: str) -> None:
        if on_step:
            on_step(msg)
        logger.info("Triage [%s]: %s", uuid, msg)
        # Yield to the event loop so SSE can deliver this step
        await asyncio.sleep(0)

    # --- Step 1: Extract text from all files in tmp/{uuid}/ ---
    # Run in thread because file I/O + PDF/DOCX parsing is blocking.
    # We pass on_step so each file is reported individually.
    tender_content: str = await loop.run_in_executor(
        None, partial(read_all_content, uuid, on_step=on_step)
    )
    # Yield after the blocking call so SSE can deliver the file steps
    await asyncio.sleep(0)

    if not tender_content.strip():
        raise ValueError(f"No content found in tmp/{uuid}/ — scrape and download first")

    content_len = len(tender_content)
    await step(f"Extracted {content_len:,} characters of tender content")

    # --- Step 2: Build prompt with reference data ---
    await step("Loading Citadel Edge capability profile and case studies")
    user_prompt = _build_user_prompt(tender_content)

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    # --- Step 3: Call Claude API (blocking HTTP) in thread ---
    await step("Scoring tender against rubric — this may take up to 30 seconds")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = await loop.run_in_executor(
        None,
        partial(
            client.messages.create,
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[TRIAGE_TOOL],
            tool_choice={"type": "tool", "name": "submit_triage_result"},
            messages=[{"role": "user", "content": user_prompt}],
        ),
    )

    # Extract the tool use result
    tool_result = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_triage_result":
            tool_result = block.input
            break

    if not tool_result:
        raise RuntimeError("Claude did not return a structured triage result")

    await step("Processing triage result")
    result = TriageResult(**tool_result)

    # Persist to disk
    write_json(uuid, "triage-result.json", result.model_dump())
    await step(f"Triage complete — {result.total}/100 ({result.band})")

    return result


def get_cached_triage(uuid: str) -> TriageResult | None:
    """Return persisted triage result if it exists."""
    data = read_json(uuid, "triage-result.json")
    if data is None:
        return None
    return TriageResult(**data)

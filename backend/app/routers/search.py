import logging

from fastapi import APIRouter

from app.services.browser import BrowserService
from app.services.extractor import search_atms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(keyword: str) -> list[dict]:
    """Search for ATM tenders by keyword."""
    svc = await BrowserService.get_instance()
    page = await svc.new_page()
    try:
        results = await search_atms(page, keyword)
        logger.info("Search for '%s' returned %d results", keyword, len(results))
        return results
    finally:
        await page.close()

import logging
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.services.browser import BASE_URL, BrowserService
from app.services.storage import create_atm_dir

logger = logging.getLogger(__name__)


async def download_documents(uuid: str, max_retries: int = 1) -> list[Path]:
    """
    Authenticate (if needed), navigate to ViewDocuments, and download all files.
    Returns list of saved file paths.
    """
    svc = await BrowserService.get_instance()
    page = await svc.new_page()

    try:
        return await _attempt_download(svc, page, uuid, max_retries)
    finally:
        await page.close()


async def _attempt_download(
    svc: BrowserService, page: Page, uuid: str, retries_left: int
) -> list[Path]:
    """Navigate to documents page, authenticate if needed, download files."""
    target_url = f"{BASE_URL}/Atm/ViewDocuments/{uuid}"

    authenticated = await svc.ensure_authenticated(page, target_url)
    if not authenticated:
        raise RuntimeError(f"Failed to authenticate for document download: {uuid}")

    # Check if we actually landed on the documents page
    if "/RegisteredUser/Login" in page.url:
        raise RuntimeError(f"Still on login page after auth attempt: {uuid}")

    # Enumerate download links
    links = await _find_download_links(page)

    if not links:
        logger.info("No documents available for %s", uuid)
        return []

    dest_dir = create_atm_dir(uuid)
    saved: list[Path] = []

    for link_selector in links:
        try:
            path = await _download_file(page, link_selector, dest_dir)
            if path:
                saved.append(path)
        except PlaywrightTimeout:
            if retries_left > 0:
                logger.warning(
                    "Download timed out for %s, re-authenticating and retrying",
                    uuid,
                )
                # Session may have expired — re-login and retry the whole batch
                return await _attempt_download(svc, page, uuid, retries_left - 1)
            logger.exception("Download timed out for %s with no retries left", uuid)
        except Exception:
            logger.exception("Failed to download a file for %s", uuid)

    return saved


async def _find_download_links(page: Page) -> list:
    """
    Find all downloadable file links on the ViewDocuments page.
    Returns element handles for each download link.
    """
    # Primary: tenders.gov.au uses /Atm/DownloadSoftCopy/ and /Atm/DownloadAddenda/
    links = await page.query_selector_all(
        'a[href*="/DownloadSoftCopy/"], a[href*="/DownloadAddenda/"]'
    )

    if not links:
        # Fallback: generic download-looking links
        links = await page.query_selector_all(
            'a[href*="/Download/"], a[href*="download"]'
        )

    if not links:
        # Final fallback: any link with a file extension
        all_links = await page.query_selector_all("a")
        download_links = []
        for link in all_links:
            href = await link.get_attribute("href") or ""
            if any(
                ext in href.lower()
                for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".csv"]
            ):
                download_links.append(link)
        links = download_links

    return links


async def _download_file(page: Page, element, dest_dir: Path) -> Path | None:
    """Click a download link and save the file to dest_dir."""
    try:
        async with page.expect_download(timeout=30000) as download_info:
            await element.click()

        download = await download_info.value
        filename = download.suggested_filename
        save_path = dest_dir / filename

        await download.save_as(str(save_path))
        logger.info("Downloaded: %s", save_path)
        return save_path

    except PlaywrightTimeout:
        # Re-raise so caller can handle retry
        raise
    except Exception:
        logger.exception("Failed to save download")
        return None

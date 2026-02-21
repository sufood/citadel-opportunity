"""Integration tests for BrowserService — requires network access."""

import asyncio
import os
from unittest.mock import patch

import pytest

# Skip all tests if no network / CI environment
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipped in CI — requires browser + network",
)

TEST_UUID = "60e02e43-1969-4d7b-83e4-f953caf81d5c"


@pytest.fixture
def settings_env(tmp_path):
    env = {
        "TENDERS_USERNAME": "test@example.com",
        "TENDERS_PASSWORD": "notreal",
        "TMP_DIR": str(tmp_path),
        "BROWSER_HEADLESS": "true",
    }
    with patch.dict(os.environ, env, clear=False):
        # Clear the lru_cache so Settings re-reads env
        from app.config import get_settings
        get_settings.cache_clear()
        yield tmp_path
        get_settings.cache_clear()


@pytest.fixture
async def browser_service(settings_env):
    from app.services.browser import BrowserService
    # Reset singleton
    BrowserService._instance = None
    svc = await BrowserService.get_instance()
    yield svc
    await svc.close()


@pytest.mark.asyncio
async def test_browser_launches(browser_service):
    """Browser service should launch and provide a context."""
    ctx = await browser_service.get_context()
    assert ctx is not None


@pytest.mark.asyncio
async def test_new_page_loads_atm_show(browser_service):
    """Should be able to load the ATM Show page (no auth required)."""
    page = await browser_service.new_page()
    try:
        await page.goto(f"https://www.tenders.gov.au/Atm/Show/{TEST_UUID}")
        await page.wait_for_load_state("networkidle")
        title = await page.title()
        assert "AusTender" in title
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_view_documents_redirects_to_login(browser_service):
    """ViewDocuments should redirect to login when not authenticated."""
    page = await browser_service.new_page()
    try:
        await page.goto(
            f"https://www.tenders.gov.au/Atm/ViewDocuments/{TEST_UUID}"
        )
        await page.wait_for_load_state("networkidle")
        assert "/RegisteredUser/Login" in page.url
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_login_with_bad_credentials(browser_service):
    """Login with fake credentials should return False."""
    page = await browser_service.new_page()
    try:
        await page.goto(
            f"https://www.tenders.gov.au/Atm/ViewDocuments/{TEST_UUID}"
        )
        await page.wait_for_load_state("networkidle")
        result = await browser_service.login(page)
        assert result is False
    finally:
        await page.close()


@pytest.mark.asyncio
async def test_save_session_creates_file(browser_service, settings_env):
    """save_session should write .auth_state.json to tmp dir."""
    await browser_service.save_session()
    auth_file = settings_env / ".auth_state.json"
    assert auth_file.exists()


@pytest.mark.asyncio
async def test_close_clears_singleton(browser_service):
    """After close(), singleton should be cleared."""
    from app.services.browser import BrowserService
    await browser_service.close()
    assert BrowserService._instance is None

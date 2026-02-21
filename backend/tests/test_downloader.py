"""Tests for downloader service — uses mocks for Playwright interactions."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def settings_env(tmp_path):
    env = {
        "TENDERS_USERNAME": "test@example.com",
        "TENDERS_PASSWORD": "notreal",
        "TMP_DIR": str(tmp_path),
        "BROWSER_HEADLESS": "true",
    }
    with patch.dict(os.environ, env, clear=False):
        from app.config import get_settings
        get_settings.cache_clear()
        yield tmp_path
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_download_no_documents(settings_env):
    """When no download links exist, returns empty list."""
    from app.services.downloader import _find_download_links

    mock_page = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[])

    links = await _find_download_links(mock_page)
    assert links == []


@pytest.mark.asyncio
async def test_find_download_links_with_download_hrefs(settings_env):
    """Should find links with /Download/ in href."""
    from app.services.downloader import _find_download_links

    mock_link = AsyncMock()
    mock_page = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[mock_link])

    links = await _find_download_links(mock_page)
    assert len(links) == 1


@pytest.mark.asyncio
async def test_download_file_saves_to_dest(settings_env):
    """_download_file should save the downloaded file to dest_dir."""
    from app.services.downloader import _download_file

    dest_dir = settings_env / "test-uuid"
    dest_dir.mkdir()

    mock_download = MagicMock()
    mock_download.suggested_filename = "tender_doc.pdf"
    mock_download.save_as = AsyncMock()

    mock_element = AsyncMock()

    # Playwright's expect_download is an async context manager.
    # After the `async with` block, `await download_info.value` returns the Download.
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    # In Playwright, `download_info.value` is a coroutine. `await download_info.value`
    # must return the Download object. We use an immediately-created coroutine.
    import asyncio

    async def _value():
        return mock_download

    mock_ctx.value = _value()

    mock_page = AsyncMock()
    mock_page.expect_download = MagicMock(return_value=mock_ctx)

    result = await _download_file(mock_page, mock_element, dest_dir)

    assert result == dest_dir / "tender_doc.pdf"
    mock_download.save_as.assert_called_once_with(str(dest_dir / "tender_doc.pdf"))


@pytest.mark.asyncio
async def test_download_documents_auth_failure_raises(settings_env):
    """Should raise RuntimeError if authentication fails."""
    from app.services.downloader import _attempt_download

    mock_svc = AsyncMock()
    mock_svc.ensure_authenticated = AsyncMock(return_value=False)

    mock_page = AsyncMock()

    with pytest.raises(RuntimeError, match="Failed to authenticate"):
        await _attempt_download(mock_svc, mock_page, "some-uuid", 0)


@pytest.mark.asyncio
async def test_download_documents_still_on_login_raises(settings_env):
    """Should raise RuntimeError if still on login page after auth."""
    from app.services.downloader import _attempt_download

    mock_svc = AsyncMock()
    mock_svc.ensure_authenticated = AsyncMock(return_value=True)

    mock_page = AsyncMock()
    mock_page.url = "https://www.tenders.gov.au/RegisteredUser/Login?ReturnUrl=foo"

    with pytest.raises(RuntimeError, match="Still on login page"):
        await _attempt_download(mock_svc, mock_page, "some-uuid", 0)


@pytest.mark.asyncio
async def test_download_documents_empty_page_returns_empty(settings_env):
    """When authenticated but no links found, returns empty list."""
    from app.services.downloader import _attempt_download

    mock_svc = AsyncMock()
    mock_svc.ensure_authenticated = AsyncMock(return_value=True)

    mock_page = AsyncMock()
    mock_page.url = "https://www.tenders.gov.au/Atm/ViewDocuments/some-uuid"
    mock_page.query_selector_all = AsyncMock(return_value=[])

    result = await _attempt_download(mock_svc, mock_page, "some-uuid", 0)
    assert result == []

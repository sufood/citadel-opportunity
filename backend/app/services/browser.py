import logging
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

BASE_URL = "https://www.tenders.gov.au"


class BrowserService:
    """Singleton Playwright browser/context manager."""

    _instance: "BrowserService | None" = None

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    @classmethod
    async def get_instance(cls) -> "BrowserService":
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._init()
        return cls._instance

    async def _init(self) -> None:
        settings = get_settings()
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
        )
        auth_path = self._auth_state_path()
        if auth_path.exists():
            logger.info("Restoring session from %s", auth_path)
            self._context = await self._browser.new_context(
                user_agent=USER_AGENT,
                storage_state=str(auth_path),
            )
        else:
            self._context = await self._browser.new_context(
                user_agent=USER_AGENT,
            )

    def _auth_state_path(self) -> Path:
        settings = get_settings()
        return settings.tmp_dir / ".auth_state.json"

    async def get_context(self) -> BrowserContext:
        """Return the persistent browser context."""
        if self._context is None:
            await self._init()
        assert self._context is not None
        return self._context

    async def new_page(self) -> Page:
        """Create a new page in the persistent context."""
        ctx = await self.get_context()
        return await ctx.new_page()

    async def save_session(self) -> None:
        """Save browser context storage state for session reuse."""
        if self._context is None:
            return
        path = self._auth_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(path))
        logger.info("Session saved to %s", path)

    async def login(self, page: Page) -> bool:
        """
        Log in to tenders.gov.au using credentials from settings.

        Expects the page to be on or redirected to the login form.
        Returns True on success, False on failure.
        """
        settings = get_settings()
        try:
            # Wait for the main login form
            await page.wait_for_selector("#form-Email", timeout=10000)

            await page.fill("#form-Email", settings.tenders_username)
            await page.fill("#form-Password", settings.tenders_password)
            await page.click('input[type="submit"][value="Login"]')

            # Wait for navigation after login
            await page.wait_for_load_state("networkidle")

            # If we're still on the login page, login failed
            if "/RegisteredUser/Login" in page.url:
                logger.error("Login failed — still on login page")
                return False

            await self.save_session()
            logger.info("Login successful")
            return True

        except Exception:
            logger.exception("Login failed")
            return False

    async def ensure_authenticated(self, page: Page, target_url: str) -> bool:
        """
        Navigate to target_url. If redirected to login, authenticate first.
        Returns True if the page is ready at the target URL.
        """
        try:
            await page.goto(target_url)
            await page.wait_for_load_state("networkidle")

            if "/RegisteredUser/Login" in page.url:
                logger.info("Redirected to login — authenticating")
                success = await self.login(page)
                if not success:
                    return False
                # After login we should be redirected to the target
                await page.wait_for_load_state("networkidle")

            return True

        except Exception:
            logger.exception("Failed to navigate to %s", target_url)
            return False

    async def close(self) -> None:
        """Graceful shutdown."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        BrowserService._instance = None
        logger.info("Browser service closed")

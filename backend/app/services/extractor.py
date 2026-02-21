import logging
import re

from bs4 import BeautifulSoup
from playwright.async_api import Page

from app.models.atm import ATMDetail, ContactDetails
from app.services.storage import write_json

logger = logging.getLogger(__name__)

BASE_URL = "https://www.tenders.gov.au"
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


# ---------------------------------------------------------------------------
# 4a — Search Results
# ---------------------------------------------------------------------------


async def search_atms(page: Page, keyword: str) -> list[dict]:
    """
    Navigate to the ATM search page and extract result summaries.
    Returns list of {uuid, title, href} dicts.
    """
    url = f"{BASE_URL}/Atm?filter=published&Keyword={keyword}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")

    html = await page.content()
    return parse_search_results(html)


def parse_search_results(html: str) -> list[dict]:
    """Parse search results HTML (offline-testable)."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    for link in soup.find_all("a", class_="detail"):
        href = link.get("href", "")
        match = UUID_RE.search(href)
        if not match:
            continue

        uuid = match.group(0)
        title = link.get("title", "").replace("Full Details for ", "")

        results.append({
            "uuid": uuid,
            "title": title,
            "href": f"{BASE_URL}{href}",
        })

    return results


# ---------------------------------------------------------------------------
# 4b — ATM Detail Extraction
# ---------------------------------------------------------------------------


async def extract_atm_detail(page: Page, uuid: str) -> ATMDetail:
    """
    Navigate to the ATM detail page, extract dataLayer and all fields.
    Writes data-layer.json and atm-details.json to tmp/{uuid}/.
    """
    url = f"{BASE_URL}/Atm/Show/{uuid}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")

    # Extract and save dataLayer
    try:
        data_layer = await page.evaluate("() => window.dataLayer")
        if data_layer:
            write_json(uuid, "data-layer.json", data_layer)
            logger.info("Saved data-layer.json for %s", uuid)
    except Exception:
        logger.exception("Failed to extract dataLayer for %s", uuid)

    html = await page.content()
    detail = parse_atm_detail(html, uuid)

    write_json(uuid, "atm-details.json", detail.model_dump())
    logger.info("Saved atm-details.json for %s", uuid)

    return detail


def parse_atm_detail(html: str, uuid: str) -> ATMDetail:
    """Parse ATM detail HTML into an ATMDetail model (offline-testable)."""
    soup = BeautifulSoup(html, "html.parser")

    # Main detail container
    main_box = soup.find("div", class_="box boxW listInner")

    def _field(label_for: str) -> str | None:
        """Extract text value for a field by its label 'for' attribute."""
        if not main_box:
            return None
        label = main_box.find("label", attrs={"for": label_for})
        if not label:
            return None
        list_desc = label.find_parent("div", class_="list-desc")
        if not list_desc:
            return None
        inner = list_desc.find("div", class_="list-desc-inner")
        if not inner:
            return None
        return inner.get_text(strip=True)

    def _bool_field(label_for: str) -> bool | None:
        text = _field(label_for)
        if text and text.lower() == "yes":
            return True
        if text and text.lower() == "no":
            return False
        return None

    def _link_field(label_for: str) -> str | None:
        """Extract href from a link inside a field."""
        if not main_box:
            return None
        label = main_box.find("label", attrs={"for": label_for})
        if not label:
            return None
        list_desc = label.find_parent("div", class_="list-desc")
        if not list_desc:
            return None
        anchor = list_desc.find("a")
        if not anchor:
            return None
        href = anchor.get("href", "")
        return f"{BASE_URL}{href}" if href.startswith("/") else href

    def _rich_text(label_for: str) -> str | None:
        """Extract text from a rich-text field, preserving paragraph breaks."""
        if not main_box:
            return None
        label = main_box.find("label", attrs={"for": label_for})
        if not label:
            return None
        list_desc = label.find_parent("div", class_="list-desc")
        if not list_desc:
            return None
        inner = list_desc.find("div", class_="list-desc-inner")
        if not inner:
            return None
        paragraphs = inner.find_all("p")
        if paragraphs:
            return "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return inner.get_text(strip=True) or None

    # Close date — text before the timezone span
    close_date = None
    if main_box:
        close_label = main_box.find("label", attrs={"for": "CloseDate"})
        if close_label:
            list_desc = close_label.find_parent("div", class_="list-desc")
            if list_desc:
                inner = list_desc.find("div", class_="list-desc-inner")
                if inner:
                    text = inner.find(string=True, recursive=False)
                    if text:
                        close_date = text.strip()

    # Contact details — separate container
    contact = _extract_contact(soup)

    # Action links — ATM Documents + Lodgement
    document_urls: list[str] = []
    lodgement_url = None
    for btn_div in soup.find_all("div", class_="btn-actions"):
        for a in btn_div.find_all("a", class_="rBtn"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
            if "Documents" in text:
                document_urls.append(full_url)
            elif "Lodgement" in text:
                lodgement_url = full_url

    return ATMDetail(
        atm_id=_field("AtmId") or uuid,
        agency=_field("Agency"),
        category=_field("Category"),
        close_date=close_date,
        publish_date=_field("PublishDate"),
        location=_field("Locations"),
        atm_type=_field("Type"),
        multi_agency_access=_bool_field("MultiAgencyAccess"),
        panel_arrangement=_bool_field("PanelArrangement"),
        multi_stage=_bool_field("MultiStage"),
        description=_rich_text("Description"),
        other_instructions=_rich_text("OtherInstructions"),
        conditions_for_participation=_rich_text("ConditionsForParticipation"),
        timeframe_for_delivery=_rich_text("TimeframeForDelivery"),
        address_for_lodgement=_field("AddressForLodgement"),
        addenda_url=_link_field("HasAddenda"),
        contact_details=contact,
        document_urls=document_urls,
        lodgement_url=lodgement_url,
    )


def _extract_contact(soup: BeautifulSoup) -> ContactDetails | None:
    """Extract contact details from the sidebar contact box."""
    contact_div = soup.find("div", class_="contact-long")
    if not contact_div:
        return None

    name = None
    phone = None
    email = None

    paragraphs = contact_div.find_all("p")
    for p in paragraphs:
        if p.get("class") and "contact-heading" in p.get("class", []):
            continue

        label = p.find("label")
        if label:
            label_for = label.get("for", "")
            if label_for == "PhoneNumber":
                span = p.find("span")
                if span:
                    phone = p.get_text(strip=True).replace(span.get_text(), "").strip()
            elif label_for == "EmailAddress":
                email_link = p.find("a")
                if email_link:
                    email = email_link.get_text(strip=True)
        elif name is None:
            text = p.get_text(strip=True)
            if text:
                name = text

    return ContactDetails(name=name, phone=phone, email=email)

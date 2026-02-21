"""Offline tests for extractor — uses saved HTML snapshots, no network."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
TEST_UUID = "60e02e43-1969-4d7b-83e4-f953caf81d5c"


@pytest.fixture
def search_html() -> str:
    return (FIXTURES / "search_results.html").read_text()


@pytest.fixture
def detail_html() -> str:
    return (FIXTURES / "atm_detail.html").read_text()


# ---------------------------------------------------------------------------
# 4a — Search Results Parsing
# ---------------------------------------------------------------------------


class TestParseSearchResults:
    def test_returns_list(self, search_html):
        from app.services.extractor import parse_search_results

        results = parse_search_results(search_html)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_each_result_has_required_keys(self, search_html):
        from app.services.extractor import parse_search_results

        results = parse_search_results(search_html)
        for r in results:
            assert "uuid" in r
            assert "title" in r
            assert "href" in r

    def test_uuids_are_valid(self, search_html):
        import re

        from app.services.extractor import UUID_RE, parse_search_results

        results = parse_search_results(search_html)
        for r in results:
            assert UUID_RE.fullmatch(r["uuid"]), f"Invalid UUID: {r['uuid']}"

    def test_hrefs_are_full_urls(self, search_html):
        from app.services.extractor import parse_search_results

        results = parse_search_results(search_html)
        for r in results:
            assert r["href"].startswith("https://www.tenders.gov.au/Atm/Show/")

    def test_titles_are_nonempty(self, search_html):
        from app.services.extractor import parse_search_results

        results = parse_search_results(search_html)
        for r in results:
            assert len(r["title"]) > 0

    def test_empty_html_returns_empty_list(self):
        from app.services.extractor import parse_search_results

        assert parse_search_results("<html><body></body></html>") == []


# ---------------------------------------------------------------------------
# 4b — ATM Detail Parsing
# ---------------------------------------------------------------------------


class TestParseATMDetail:
    def test_atm_id(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.atm_id == "EST10864"

    def test_agency(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.agency is not None
        assert "Defence" in detail.agency

    def test_category(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.category is not None
        assert len(detail.category) > 0

    def test_close_date(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.close_date is not None
        # Should have date and time, not timezone text
        assert "Local Time" not in detail.close_date
        assert "Show close time" not in detail.close_date

    def test_publish_date(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.publish_date is not None

    def test_location(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.location is not None

    def test_atm_type(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.atm_type is not None

    def test_boolean_fields(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert isinstance(detail.multi_agency_access, bool)
        assert isinstance(detail.panel_arrangement, bool)
        assert isinstance(detail.multi_stage, bool)

    def test_description(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.description is not None
        assert len(detail.description) > 10

    def test_other_instructions(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        # May or may not be present depending on tender
        # Just ensure it parses without error
        assert detail.other_instructions is None or len(detail.other_instructions) > 0

    def test_conditions_for_participation(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.conditions_for_participation is None or len(detail.conditions_for_participation) > 0

    def test_address_for_lodgement(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.address_for_lodgement is None or len(detail.address_for_lodgement) > 0

    def test_addenda_url(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        if detail.addenda_url:
            assert detail.addenda_url.startswith("https://")

    def test_contact_details(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.contact_details is not None
        assert detail.contact_details.name is not None
        assert len(detail.contact_details.name) > 0

    def test_contact_email(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.contact_details is not None
        assert detail.contact_details.email is not None
        assert "@" in detail.contact_details.email

    def test_contact_phone(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.contact_details is not None
        assert detail.contact_details.phone is not None

    def test_document_urls(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert len(detail.document_urls) > 0
        for url in detail.document_urls:
            assert url.startswith("https://")

    def test_lodgement_url(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        assert detail.lodgement_url is not None
        assert detail.lodgement_url.startswith("https://")

    def test_full_roundtrip_serialization(self, detail_html):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail(detail_html, TEST_UUID)
        json_str = detail.model_dump_json()
        from app.models.atm import ATMDetail

        restored = ATMDetail.model_validate_json(json_str)
        assert restored == detail

    def test_empty_html_uses_uuid_fallback(self):
        from app.services.extractor import parse_atm_detail

        detail = parse_atm_detail("<html><body></body></html>", "fallback-uuid")
        assert detail.atm_id == "fallback-uuid"

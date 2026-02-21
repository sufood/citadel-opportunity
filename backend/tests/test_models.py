from app.models.atm import ATMDetail, ContactDetails
from app.models.job import JobStatus


def test_contact_details_defaults():
    c = ContactDetails()
    assert c.name is None
    assert c.phone is None
    assert c.email is None


def test_contact_details_full():
    c = ContactDetails(name="John", phone="0412345678", email="j@example.com")
    d = c.model_dump()
    assert d == {"name": "John", "phone": "0412345678", "email": "j@example.com"}


def test_atm_detail_minimal():
    a = ATMDetail(atm_id="60e02e43-1969-4d7b-83e4-f953caf81d5c")
    assert a.atm_id == "60e02e43-1969-4d7b-83e4-f953caf81d5c"
    assert a.agency is None
    assert a.document_urls == []


def test_atm_detail_full_roundtrip():
    data = {
        "atm_id": "60e02e43-1969-4d7b-83e4-f953caf81d5c",
        "agency": "Dept of Defence",
        "category": "IT Services",
        "close_date": "2025-06-01T14:00:00",
        "publish_date": "2025-05-01",
        "location": "ACT",
        "atm_type": "Request for Tender",
        "multi_agency_access": True,
        "panel_arrangement": False,
        "multi_stage": False,
        "description": "A test tender",
        "other_instructions": "None",
        "conditions_for_participation": "ABN required",
        "timeframe_for_delivery": "6 months",
        "address_for_lodgement": "123 Main St",
        "addenda_url": "/Atm/ShowAddenda/abc",
        "contact_details": {
            "name": "Jane Doe",
            "phone": "0298765432",
            "email": "jane@gov.au",
        },
        "document_urls": ["/doc/1", "/doc/2"],
        "lodgement_url": "/Atm/Lodgement/abc",
    }
    a = ATMDetail(**data)
    dumped = a.model_dump()
    assert dumped == data

    # Roundtrip via JSON
    json_str = a.model_dump_json()
    restored = ATMDetail.model_validate_json(json_str)
    assert restored == a


def test_job_status_defaults():
    j = JobStatus(job_id="job-1")
    assert j.status == "pending"
    assert j.steps == []
    assert j.complete is False
    assert j.error is None


def test_job_status_with_progress():
    j = JobStatus(
        job_id="job-1",
        status="running",
        steps=["Created directory", "Extracting dataLayer"],
        complete=False,
    )
    d = j.model_dump()
    assert d["steps"] == ["Created directory", "Extracting dataLayer"]
    assert d["status"] == "running"


def test_job_status_error():
    j = JobStatus(job_id="job-1", status="failed", complete=True, error="Timeout")
    assert j.error == "Timeout"
    assert j.complete is True

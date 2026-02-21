from pydantic import BaseModel


class ContactDetails(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None


class ATMDetail(BaseModel):
    atm_id: str
    agency: str | None = None
    category: str | None = None
    close_date: str | None = None
    publish_date: str | None = None
    location: str | None = None
    atm_type: str | None = None
    multi_agency_access: bool | None = None
    panel_arrangement: bool | None = None
    multi_stage: bool | None = None
    description: str | None = None
    other_instructions: str | None = None
    conditions_for_participation: str | None = None
    timeframe_for_delivery: str | None = None
    address_for_lodgement: str | None = None
    addenda_url: str | None = None
    contact_details: ContactDetails | None = None
    document_urls: list[str] = []
    lodgement_url: str | None = None

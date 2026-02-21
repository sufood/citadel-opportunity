export interface ContactDetails {
  name: string | null;
  phone: string | null;
  email: string | null;
}

export interface ATMDetail {
  atm_id: string;
  agency: string | null;
  category: string | null;
  close_date: string | null;
  publish_date: string | null;
  location: string | null;
  atm_type: string | null;
  multi_agency_access: boolean | null;
  panel_arrangement: boolean | null;
  multi_stage: boolean | null;
  description: string | null;
  other_instructions: string | null;
  conditions_for_participation: string | null;
  timeframe_for_delivery: string | null;
  address_for_lodgement: string | null;
  addenda_url: string | null;
  contact_details: ContactDetails | null;
  document_urls: string[];
  lodgement_url: string | null;
}

export interface JobStatus {
  job_id: string;
  status: string;
  steps: string[];
  complete: boolean;
  error: string | null;
}

export interface SearchResult {
  uuid: string;
  title: string;
  href: string;
}

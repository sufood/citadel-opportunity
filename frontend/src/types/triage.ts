export interface TriageResult {
  industry_match: number;
  industry_rationale: string;
  capability_match: number;
  capability_rationale: string;
  case_study_evidence: number;
  case_study_rationale: string;
  recommended_case_studies: string[];
  differentiators: number;
  differentiators_rationale: string;
  total: number;
  band: "Pursue" | "Qualify" | "No Bid";
  capability_gaps: string[];
  key_differentiators: string[];
  risks: string[];
  summary: string;
}

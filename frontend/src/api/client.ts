import axios from "axios";
import type { ATMDetail, JobStatus, SearchResult } from "@/types/atm";
import type { TriageResult } from "@/types/triage";

const api = axios.create({
  baseURL: "/api",
});

export async function searchATMs(keyword: string): Promise<SearchResult[]> {
  const { data } = await api.get<SearchResult[]>("/search", {
    params: { keyword },
  });
  return data;
}

export async function scrapeATM(
  atmId: string
): Promise<{ job_id: string }> {
  const { data } = await api.post<{ job_id: string }>(
    `/atm/${atmId}/scrape`
  );
  return data;
}

export async function getATMDetail(atmId: string): Promise<ATMDetail> {
  const { data } = await api.get<ATMDetail>(`/atm/${atmId}`);
  return data;
}

export async function downloadDocuments(
  atmId: string
): Promise<{ job_id: string }> {
  const { data } = await api.post<{ job_id: string }>(
    `/atm/${atmId}/download`
  );
  return data;
}

export async function listFiles(atmId: string): Promise<string[]> {
  const { data } = await api.get<string[]>(`/atm/${atmId}/files`);
  return data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const { data } = await api.get<JobStatus>(`/jobs/${jobId}`);
  return data;
}

export async function triageATM(
  atmId: string
): Promise<{ job_id: string }> {
  const { data } = await api.post<{ job_id: string }>(
    `/atm/${atmId}/triage`
  );
  return data;
}

export async function getTriageResult(
  atmId: string
): Promise<TriageResult> {
  const { data } = await api.get<TriageResult>(`/atm/${atmId}/triage`);
  return data;
}

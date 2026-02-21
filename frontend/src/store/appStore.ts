import { create } from "zustand";
import type { SearchResult, JobStatus } from "@/types/atm";

interface AppState {
  searchResults: SearchResult[];
  setSearchResults: (results: SearchResult[]) => void;

  selectedAtmId: string | null;
  setSelectedAtmId: (id: string | null) => void;

  activeJobs: Record<string, JobStatus>;
  updateJob: (jobId: string, status: JobStatus) => void;
  clearJob: (jobId: string) => void;

  scrapeJobId: string | null;
  setScrapeJobId: (id: string | null) => void;
  downloadJobId: string | null;
  setDownloadJobId: (id: string | null) => void;
  triageJobId: string | null;
  setTriageJobId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  searchResults: [],
  setSearchResults: (results) => set({ searchResults: results }),

  selectedAtmId: null,
  setSelectedAtmId: (id) => set({ selectedAtmId: id }),

  activeJobs: {},
  updateJob: (jobId, status) =>
    set((state) => ({
      activeJobs: { ...state.activeJobs, [jobId]: status },
    })),
  clearJob: (jobId) =>
    set((state) => {
      const rest = Object.fromEntries(
        Object.entries(state.activeJobs).filter(([key]) => key !== jobId),
      );
      return { activeJobs: rest };
    }),

  scrapeJobId: null,
  setScrapeJobId: (id) => set({ scrapeJobId: id }),
  downloadJobId: null,
  setDownloadJobId: (id) => set({ downloadJobId: id }),
  triageJobId: null,
  setTriageJobId: (id) => set({ triageJobId: id }),
}));

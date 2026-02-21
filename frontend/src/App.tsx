import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { SearchBar } from "@/components/SearchBar";
import { ResultsTable } from "@/components/ResultsTable";
import { ATMDetailPanel } from "@/components/ATMDetailPanel";
import { DocumentList } from "@/components/DocumentList";
import { TriagePanel } from "@/components/TriagePanel";
import { JobProgress } from "@/components/JobProgress";
import { useSearch } from "@/hooks/useSearch";
import { useATMDetail } from "@/hooks/useATMDetail";
import { useJobStatus } from "@/hooks/useJobStatus";
import { useAppStore } from "@/store/appStore";
import { useTheme } from "@/hooks/useTheme";
import { scrapeATM } from "@/api/client";


function App() {
  useTheme(); // sync <html> dark class with browser preference
  const [keyword, setKeyword] = useState("");
  const queryClient = useQueryClient();
  const scrapeCompletedRef = useRef(false);

  const selectedAtmId = useAppStore((s) => s.selectedAtmId);
  const setSelectedAtmId = useAppStore((s) => s.setSelectedAtmId);
  const scrapeJobId = useAppStore((s) => s.scrapeJobId);
  const setScrapeJobId = useAppStore((s) => s.setScrapeJobId);
  const downloadJobId = useAppStore((s) => s.downloadJobId);
  const setTriageJobId = useAppStore((s) => s.setTriageJobId);

  const { data: searchResults, isLoading: searchLoading, error: searchError } = useSearch(keyword);
  const { data: atmDetail, isLoading: detailLoading } = useATMDetail(selectedAtmId);
  const scrapeStatus = useJobStatus(scrapeJobId);
  const downloadStatus = useJobStatus(downloadJobId);

  const downloadComplete = !!(downloadStatus?.complete && !downloadStatus.error);
  const triageJobId = useAppStore((s) => s.triageJobId);

  // Guided hint pulses — only one active at a time
  const pulseSearch = !keyword && !selectedAtmId;
  const pulseDownload = !!selectedAtmId && !!atmDetail && !downloadJobId && !downloadComplete;
  const pulseTriage = downloadComplete && !triageJobId;

  // Show search errors
  useEffect(() => {
    if (searchError) {
      toast.error("Search failed", {
        description: searchError.message,
      });
    }
  }, [searchError]);

  // Handle scrape completion
  useEffect(() => {
    if (!scrapeStatus) {
      scrapeCompletedRef.current = false;
      return;
    }
    if (scrapeStatus.complete && !scrapeCompletedRef.current) {
      scrapeCompletedRef.current = true;
      if (scrapeStatus.error) {
        toast.error("Analysis failed", { description: scrapeStatus.error });
      } else {
        toast.success("Analysis complete", {
          description: `Details extracted for ${scrapeStatus.steps.length} steps.`,
        });
        queryClient.invalidateQueries({ queryKey: ["atm-detail", selectedAtmId] });
      }
    }
  }, [scrapeStatus, selectedAtmId, queryClient]);

  const handleSearch = (kw: string) => {
    setKeyword(kw);
    setSelectedAtmId(null);
    setScrapeJobId(null);
    setTriageJobId(null);
    scrapeCompletedRef.current = false;
  };

  const handleSelect = async (uuid: string) => {
    setSelectedAtmId(uuid);
    setScrapeJobId(null);
    setTriageJobId(null);
    scrapeCompletedRef.current = false;

    try {
      const { job_id } = await scrapeATM(uuid);
      setScrapeJobId(job_id);
    } catch {
      // detail may already exist — silently continue
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold mb-3">Opportunity Analyser</h1>
          <SearchBar onSearch={handleSearch} isLoading={searchLoading} pulse={pulseSearch} />
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Results + Triage */}
          <div className="lg:col-span-2 space-y-4">
            <ResultsTable
              results={searchResults ?? []}
              selectedId={selectedAtmId}
              onSelect={handleSelect}
              isLoading={searchLoading}
              hasSearched={keyword.length > 0}
            />

            {selectedAtmId && (
              <TriagePanel
                atmId={selectedAtmId}
                downloadComplete={downloadComplete}
                pulse={pulseTriage}
              />
            )}
          </div>

          {/* Right: Detail + Documents */}
          <div className="lg:col-span-3 space-y-4">
            {scrapeJobId && !scrapeStatus?.complete && (
              <JobProgress job={scrapeStatus} label="Analysis Progress" />
            )}

            <ATMDetailPanel detail={atmDetail} isLoading={detailLoading} />

            {selectedAtmId && <DocumentList atmId={selectedAtmId} pulse={pulseDownload} />}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

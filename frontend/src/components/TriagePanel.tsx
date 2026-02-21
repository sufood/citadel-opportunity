import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Target,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  BookOpen,
  Shield,
  RefreshCw,
  Loader2,
  CheckCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useJobStatus } from "@/hooks/useJobStatus";
import { useAppStore } from "@/store/appStore";
import { triageATM, getTriageResult } from "@/api/client";
import type { TriageResult } from "@/types/triage";

interface TriagePanelProps {
  atmId: string | null;
  downloadComplete: boolean;
  pulse?: boolean;
}

function ScoreBar({
  label,
  score,
  max,
}: {
  label: string;
  score: number;
  max: number;
}) {
  const pct = max > 0 ? (score / max) * 100 : 0;

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">
          {score}/{max}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-secondary">
        <div
          className="h-full rounded-full bg-blue-500 dark:bg-blue-400 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function DisclosureSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 py-1.5 text-sm font-medium hover:text-primary transition-colors"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        {icon}
        {title}
      </button>
      {open && <div className="pl-6 pb-2 text-sm">{children}</div>}
    </div>
  );
}

function bandColor(band: TriageResult["band"]) {
  switch (band) {
    case "Pursue":
      return "bg-green-600 dark:bg-green-500 text-white";
    case "Qualify":
      return "bg-amber-500 dark:bg-amber-400 text-white dark:text-black";
    case "No Bid":
      return "bg-red-600 dark:bg-red-500 text-white";
  }
}

function TriageProcessingState({ steps }: { steps: string[] }) {
  return (
    <div className="space-y-2">
      <ul className="space-y-1.5">
        {steps.map((step, i) => {
          const isCurrent = i === steps.length - 1;
          return (
            <li key={i} className="flex items-start gap-2 text-sm">
              {isCurrent ? (
                <Loader2 className="h-3.5 w-3.5 mt-0.5 shrink-0 animate-spin text-muted-foreground" />
              ) : (
                <CheckCircle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-green-600 dark:text-green-400" />
              )}
              <span className={isCurrent ? "text-foreground" : "text-muted-foreground"}>
                {step}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function TriageResultDisplay({ result }: { result: TriageResult }) {
  return (
    <div className="space-y-4">
      {/* Score + Band */}
      <div className="flex items-center justify-between">
        <div className="text-2xl font-bold">{result.total}/100</div>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${bandColor(result.band)}`}
        >
          {result.band}
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-muted-foreground">{result.summary}</p>

      <Separator />

      {/* Score breakdown */}
      <div className="space-y-3">
        <ScoreBar label="Industry Match" score={result.industry_match} max={20} />
        <ScoreBar label="Capability Match" score={result.capability_match} max={30} />
        <ScoreBar label="Case Study Evidence" score={result.case_study_evidence} max={30} />
        <ScoreBar label="Differentiators" score={result.differentiators} max={20} />
      </div>

      <Separator />

      {/* Expandable sections */}
      <div className="space-y-1">
        <DisclosureSection
          title="Rationale"
          icon={<BookOpen className="h-3.5 w-3.5" />}
        >
          <div className="space-y-3">
            <div>
              <div className="font-medium text-xs text-muted-foreground mb-1">Industry Match</div>
              <p>{result.industry_rationale}</p>
            </div>
            <div>
              <div className="font-medium text-xs text-muted-foreground mb-1">Capability Match</div>
              <p>{result.capability_rationale}</p>
            </div>
            <div>
              <div className="font-medium text-xs text-muted-foreground mb-1">Case Study Evidence</div>
              <p>{result.case_study_rationale}</p>
            </div>
            <div>
              <div className="font-medium text-xs text-muted-foreground mb-1">Differentiators</div>
              <p>{result.differentiators_rationale}</p>
            </div>
          </div>
        </DisclosureSection>

        {result.recommended_case_studies.length > 0 && (
          <DisclosureSection
            title="Recommended Case Studies"
            icon={<BookOpen className="h-3.5 w-3.5" />}
          >
            <ul className="list-disc pl-4 space-y-1">
              {result.recommended_case_studies.map((cs, i) => (
                <li key={i}>{cs}</li>
              ))}
            </ul>
          </DisclosureSection>
        )}

        {result.key_differentiators.length > 0 && (
          <DisclosureSection
            title="Key Differentiators"
            icon={<Shield className="h-3.5 w-3.5" />}
          >
            <ul className="list-disc pl-4 space-y-1">
              {result.key_differentiators.map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
          </DisclosureSection>
        )}

        {result.capability_gaps.length > 0 && (
          <DisclosureSection
            title="Capability Gaps"
            icon={<AlertTriangle className="h-3.5 w-3.5" />}
          >
            <ul className="list-disc pl-4 space-y-1">
              {result.capability_gaps.map((g, i) => (
                <li key={i}>{g}</li>
              ))}
            </ul>
          </DisclosureSection>
        )}

        {result.risks.length > 0 && (
          <DisclosureSection
            title="Risks"
            icon={<AlertTriangle className="h-3.5 w-3.5" />}
          >
            <ul className="list-disc pl-4 space-y-1">
              {result.risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </DisclosureSection>
        )}
      </div>
    </div>
  );
}

export function TriagePanel({ atmId, downloadComplete, pulse }: TriagePanelProps) {
  const triageJobId = useAppStore((s) => s.triageJobId);
  const setTriageJobId = useAppStore((s) => s.setTriageJobId);
  const triageStatus = useJobStatus(triageJobId);
  const triageCompletedRef = useRef(false);

  // Try to load cached triage result
  const {
    data: cachedResult,
    refetch: refetchResult,
  } = useQuery({
    queryKey: ["triage-result", atmId],
    queryFn: () => getTriageResult(atmId!),
    enabled: !!atmId,
    retry: false,
  });

  // Refetch result when triage job completes
  useEffect(() => {
    if (!triageStatus) {
      triageCompletedRef.current = false;
      return;
    }
    if (triageStatus.complete && !triageStatus.error && !triageCompletedRef.current) {
      triageCompletedRef.current = true;
      refetchResult();
    }
  }, [triageStatus, refetchResult]);

  // Reset when ATM changes
  useEffect(() => {
    triageCompletedRef.current = false;
  }, [atmId]);

  const handleTriage = async () => {
    if (!atmId) return;
    triageCompletedRef.current = false;
    const { job_id } = await triageATM(atmId);
    setTriageJobId(job_id);
  };

  if (!atmId) return null;

  const hasResult = !!cachedResult;
  const isRunning = !!(triageJobId && triageStatus && !triageStatus.complete);
  const canTriage = downloadComplete && !isRunning;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Target className="h-4 w-4" />
            Tender Triage
          </CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={handleTriage}
            disabled={!canTriage}
            className={pulse && !isRunning && !hasResult ? "animate-pulse-hint" : ""}
          >
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Analysing...
              </>
            ) : hasResult ? (
              <>
                <RefreshCw className="h-4 w-4 mr-1" />
                Re-triage
              </>
            ) : (
              <>
                <Target className="h-4 w-4 mr-1" />
                Triage This Tender
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {!downloadComplete && !hasResult && (
          <p className="text-sm text-muted-foreground">
            Download documents first to enable triage scoring.
          </p>
        )}

        {isRunning && (
          <TriageProcessingState steps={triageStatus?.steps ?? []} />
        )}

        {triageStatus?.error && !isRunning && (
          <div className="text-sm text-destructive">
            Triage failed: {triageStatus.error}
          </div>
        )}

        {cachedResult && !isRunning && (
          <TriageResultDisplay result={cachedResult} />
        )}
      </CardContent>
    </Card>
  );
}

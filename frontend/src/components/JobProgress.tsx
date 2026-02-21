import { CheckCircle, Loader2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { JobStatus } from "@/types/atm";

interface JobProgressProps {
  job: JobStatus | null;
  label?: string;
}

export function JobProgress({ job, label = "Job Progress" }: JobProgressProps) {
  if (!job) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{label}</CardTitle>
          <Badge
            variant={
              job.error
                ? "destructive"
                : job.complete
                  ? "default"
                  : "secondary"
            }
          >
            {job.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1.5">
          {job.steps.map((step, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              {i === job.steps.length - 1 && !job.complete ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
              ) : (
                <CheckCircle className="h-3.5 w-3.5 text-green-600" />
              )}
              <span>{step}</span>
            </li>
          ))}
          {job.error && (
            <li className="flex items-center gap-2 text-sm text-destructive">
              <XCircle className="h-3.5 w-3.5" />
              <span>{job.error}</span>
            </li>
          )}
        </ul>
      </CardContent>
    </Card>
  );
}

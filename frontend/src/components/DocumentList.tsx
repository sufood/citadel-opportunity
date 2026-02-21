import { useQuery } from "@tanstack/react-query";
import { FileText, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { listFiles, downloadDocuments } from "@/api/client";
import { useAppStore } from "@/store/appStore";
import { useJobStatus } from "@/hooks/useJobStatus";
import { JobProgress } from "./JobProgress";

interface DocumentListProps {
  atmId: string | null;
  pulse?: boolean;
}

export function DocumentList({ atmId, pulse }: DocumentListProps) {
  const downloadJobId = useAppStore((s) => s.downloadJobId);
  const setDownloadJobId = useAppStore((s) => s.setDownloadJobId);
  const downloadStatus = useJobStatus(downloadJobId);

  const { data: files, refetch } = useQuery({
    queryKey: ["files", atmId],
    queryFn: () => listFiles(atmId!),
    enabled: !!atmId,
    retry: false,
  });

  // Refetch files when download completes
  if (downloadStatus?.complete && !downloadStatus.error) {
    refetch();
  }

  const handleDownload = async () => {
    if (!atmId) return;
    const { job_id } = await downloadDocuments(atmId);
    setDownloadJobId(job_id);
  };

  if (!atmId) return null;

  // Filter out JSON metadata files for display
  const docFiles = files?.filter(
    (f) => !f.endsWith(".json")
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Documents</CardTitle>
          <Button size="sm" variant="outline" onClick={handleDownload} className={pulse ? "animate-pulse-hint" : ""}>
            <Download className="h-4 w-4 mr-1" />
            Download All
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {downloadJobId && (
          <JobProgress job={downloadStatus} label="Download Progress" />
        )}

        {docFiles && docFiles.length > 0 ? (
          <ul className="space-y-1.5">
            {docFiles.map((file) => (
              <li key={file}>
                <a
                  href={`/files/${atmId}/${encodeURIComponent(file)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-primary hover:underline"
                >
                  <FileText className="h-3.5 w-3.5 shrink-0" />
                  {file}
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            No documents yet. Click "Download All" to fetch them.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

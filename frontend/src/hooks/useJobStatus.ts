import { useEffect, useMemo, useRef, useState } from "react";
import type { JobStatus } from "@/types/atm";

export function useJobStatus(jobId: string | null) {
  const [statusMap, setStatusMap] = useState<Record<string, JobStatus>>({});
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    const es = new EventSource(`/api/jobs/${jobId}/stream`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data: JobStatus = JSON.parse(event.data);
        setStatusMap((prev) => ({ ...prev, [jobId]: data }));

        if (data.complete) {
          es.close();
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [jobId]);

  return useMemo(() => (jobId ? statusMap[jobId] ?? null : null), [jobId, statusMap]);
}

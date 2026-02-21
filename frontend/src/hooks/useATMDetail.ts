import { useQuery } from "@tanstack/react-query";
import { getATMDetail } from "@/api/client";

export function useATMDetail(atmId: string | null) {
  return useQuery({
    queryKey: ["atm-detail", atmId],
    queryFn: () => getATMDetail(atmId!),
    enabled: !!atmId,
    retry: false,
  });
}

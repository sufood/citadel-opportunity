import { useQuery } from "@tanstack/react-query";
import { searchATMs } from "@/api/client";

export function useSearch(keyword: string) {
  return useQuery({
    queryKey: ["search", keyword],
    queryFn: () => searchATMs(keyword),
    enabled: keyword.length > 0,
    staleTime: 60_000,
  });
}

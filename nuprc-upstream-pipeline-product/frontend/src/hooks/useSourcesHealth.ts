import { useQuery } from "@tanstack/react-query";
import { fetchSourcesHealth } from "@/lib/api";

export function useSourcesHealth() {
  return useQuery({
    queryKey: ["sources", "health"],
    queryFn: fetchSourcesHealth,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

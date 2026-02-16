import { useQuery } from "@tanstack/react-query";
import { fetchPlatformStatus } from "@/lib/api";

export function usePlatformStatus() {
  return useQuery({
    queryKey: ["platform", "status"],
    queryFn: fetchPlatformStatus,
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}

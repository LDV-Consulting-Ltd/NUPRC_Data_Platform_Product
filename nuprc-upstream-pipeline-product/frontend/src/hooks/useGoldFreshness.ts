import { useQuery } from "@tanstack/react-query";
import { fetchGoldFreshness } from "@/lib/api";

export function useGoldFreshness() {
  return useQuery({
    queryKey: ["gold", "freshness"],
    queryFn: fetchGoldFreshness,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

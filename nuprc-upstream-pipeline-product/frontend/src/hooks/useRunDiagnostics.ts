import { useQuery } from "@tanstack/react-query";
import { fetchRunDiagnostics } from "@/lib/api";

export function useRunDiagnostics(runId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["pipeline", "run", runId, "diagnostics"],
    queryFn: () => fetchRunDiagnostics(runId!),
    enabled: !!runId && enabled,
  });
}

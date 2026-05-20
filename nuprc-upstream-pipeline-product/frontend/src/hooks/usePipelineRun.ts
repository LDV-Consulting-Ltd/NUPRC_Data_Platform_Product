import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPipelineRun, startPipelineRun, startPgPipelineRun, retryPipelineRun } from "@/lib/api";
import type { PipelineMode, PgPipelineMode } from "@/lib/types";

export function usePipelineRun(runId: string | null, options?: { enabled: boolean }) {
  const enabled = options?.enabled ?? !!runId;
  return useQuery({
    queryKey: ["pipeline", "run", runId],
    queryFn: () => fetchPipelineRun(runId!),
    enabled: !!runId && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" ? 4000 : false;
    },
  });
}

export function useStartPipelineRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mode: PipelineMode) => startPipelineRun(mode),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
      queryClient.invalidateQueries({ queryKey: ["pipeline", "run", data.run_id] });
      queryClient.setQueryData(["pipeline", "run", data.run_id], null);
    },
  });
}

export function useStartPgPipelineRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mode: PgPipelineMode) => startPgPipelineRun(mode),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
      queryClient.invalidateQueries({ queryKey: ["pipeline", "run", data.run_id] });
      queryClient.setQueryData(["pipeline", "run", data.run_id], null);
    },
  });
}

export function useRetryPipelineRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (_runId?: string) => retryPipelineRun(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["platform", "status"] });
      if (data?.run_id) {
        queryClient.invalidateQueries({ queryKey: ["pipeline", "run", data.run_id] });
      }
    },
  });
}

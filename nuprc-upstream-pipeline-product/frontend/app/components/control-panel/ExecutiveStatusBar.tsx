"use client";

import { useGoldFreshness } from "@/hooks/useGoldFreshness";
import { usePlatformStatus } from "@/hooks/usePlatformStatus";
import type { PlatformStatus, SourceHealthItem } from "@/lib/types";
import { LoadingRows, MetricTile, StateBlock } from "../console/ui";

function formatTime(iso: string) {
  try {
    const d = new Date(iso);
    return (
      d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) +
      " — " +
      d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })
    );
  } catch {
    return iso;
  }
}

function formatDuration(seconds: number) {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s ? `${m}m ${s}s` : `${m}m`;
}

function latestPublished(sources: SourceHealthItem[] | undefined) {
  const stamps = (sources ?? [])
    .map((source) => source.last_update)
    .filter((value): value is string => Boolean(value))
    .sort();
  return stamps.length ? stamps[stamps.length - 1] : null;
}

export default function ExecutiveStatusBar() {
  const { data, isLoading, isError } = usePlatformStatus();
  const freshness = useGoldFreshness();

  if (isError) {
    return (
      <StateBlock tone="error" title="Platform status is unavailable">
        The control panel could not read the latest ingestion attempt. Published warehouse freshness is requested separately.
      </StateBlock>
    );
  }

  const s: PlatformStatus | null = data ?? null;
  const publishedAt = latestPublished(freshness.data);

  if (isLoading && !s) return <LoadingRows />;

  return (
    <section className="pc-metrics" aria-label="Ingestion and published snapshot">
      <MetricTile
        label="Latest ingestion attempt"
        value={s?.last_run ? s.last_run.status : "—"}
        detail={s?.last_run ? `${formatTime(s.last_run.at)} · ${formatDuration(s.last_run.duration_seconds)}` : "No attempt returned"}
      />
      <MetricTile
        label="Latest published snapshot"
        value={freshness.isLoading ? "Loading" : publishedAt ? formatTime(publishedAt) : "—"}
        detail="Newest warehouse freshness timestamp across oil, gas, rig activity, and concession"
      />
      <MetricTile
        label="Pipeline status"
        value={s?.system_health ?? "—"}
        detail="From the platform status feed"
      />
      <MetricTile
        label="Records on the latest attempt"
        value={(s?.records_today ?? 0).toLocaleString("en-GB")}
        detail="Rows reported on the latest run metadata. Unit is records, not barrels or scf."
      />
      <MetricTile
        label="SLA marker"
        value={`${s?.sla_compliance.met ?? 0}/${s?.sla_compliance.total ?? 0}`}
        detail={s?.sla_compliance.label ?? "Daily SLA: 02:00 delivery"}
      />
    </section>
  );
}

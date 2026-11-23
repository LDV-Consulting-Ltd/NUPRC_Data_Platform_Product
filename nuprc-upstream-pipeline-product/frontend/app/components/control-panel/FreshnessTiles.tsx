"use client";

import Link from "next/link";
import { useGoldFreshness } from "@/hooks/useGoldFreshness";
import { sourceByKey } from "@/lib/public-sources";
import type { SourceHealthItem } from "@/lib/types";
import { GapNote, LoadingRows, StateBlock, StatusPill, toneForStatus } from "../console/ui";

function intervalLabel(minutes: number) {
  if (minutes >= 1440) return "Daily";
  return `${minutes} minutes`;
}

export default function FreshnessTiles() {
  const { data: sources, isLoading, isError } = useGoldFreshness();

  return (
    <section className="pc-card">
      <div className="pc-card-h">
        <h2>Published snapshot freshness</h2>
        <StatusPill tone="neutral">Target ≤ 6h</StatusPill>
      </div>
      <div className="pc-card-b">
        {isLoading && <LoadingRows />}
        {isError && (
          <StateBlock tone="error" title="Warehouse freshness is unavailable">
            The published snapshot could not be read. The latest ingestion attempt is still shown above.
          </StateBlock>
        )}
        {!isLoading && !isError && (sources ?? []).length === 0 && (
          <StateBlock tone="empty" title="No published snapshot yet">
            The warehouse freshness feed returned no oil, gas, rig, or concession rows.
          </StateBlock>
        )}
        {!isLoading && !isError && (sources ?? []).length > 0 && (
          <div className="pc-flow" style={{ gridTemplateColumns: "1fr" }}>
            {(sources ?? []).map((source) => (
              <FreshnessRow key={source.source_key} source={source} />
            ))}
          </div>
        )}
        <GapNote>Scores are freshness points out of 100. They are not production volumes.</GapNote>
      </div>
    </section>
  );
}

function FreshnessRow({ source }: { source: SourceHealthItem }) {
  const meta = sourceByKey(source.source_key);
  return (
    <article className="pc-step">
      <div className="pc-step-k">{meta?.commodity ?? "Dataset"}</div>
      <strong>{source.label}</strong>
      <p>
        Last published update: {source.last_update ? new Date(source.last_update).toLocaleString("en-GB") : "—"} · Expected{" "}
        {intervalLabel(source.expected_interval_minutes)}
      </p>
      <p>
        Freshness score: <b className="pc-num">{source.freshness_score}</b>/100
        {meta ? ` · ${meta.unit}` : ""}
      </p>
      <StatusPill tone={toneForStatus(source.status)}>{source.status}</StatusPill>
      <p>
        <Link href={`/regulatory?source=${encodeURIComponent(source.source_key)}`}>Open in Upstream Intelligence</Link>
        {meta && (
          <>
            {" · "}
            <a href={meta.href} target="_blank" rel="noopener noreferrer">
              Published report
            </a>
          </>
        )}
      </p>
    </article>
  );
}

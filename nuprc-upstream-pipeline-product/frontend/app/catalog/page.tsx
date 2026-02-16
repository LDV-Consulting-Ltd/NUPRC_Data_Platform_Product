"use client";

import { useState, useEffect } from "react";
import V2Header from "../components/V2Header";
import Link from "next/link";
import { fetchCatalogTables, type CatalogTable } from "@/lib/api";

type Layer = "bronze" | "silver" | "gold";

export default function CatalogPage() {
  const [layer, setLayer] = useState<Layer>("bronze");
  const [tables, setTables] = useState<CatalogTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchCatalogTables(layer)
      .then((res) => setTables(res.tables))
      .catch((e) => setError(String(e.message)))
      .finally(() => setLoading(false));
  }, [layer]);

  return (
    <>
      <V2Header
        title="Data Catalog"
        subtitle="Dataset profiles by layer: Bronze (raw), Silver (cleaned), Gold (warehouse). Select a layer to list tables."
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Layer selector */}
        <section className="bg-white rounded-2xl border border-slate-200 p-4">
          <div className="flex flex-col sm:flex-row gap-3 items-center">
            <span className="text-sm font-semibold text-slate-600">Layer:</span>
            <div className="flex gap-2">
              {(["bronze", "silver", "gold"] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => setLayer(l)}
                  className={`px-4 py-2 rounded-xl font-semibold text-sm capitalize ${layer === l ? "bg-ldv-green text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Table list from /catalog/tables?layer= */}
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200 font-bold">
            Tables — {layer} ({tables.length})
          </div>
          {error && (
            <div className="p-4 text-red-600 text-sm">{error}</div>
          )}
          {loading && (
            <div className="p-8 text-slate-500 text-center">Loading…</div>
          )}
          {!loading && !error && (
            <ul className="divide-y divide-slate-100">
              {tables.length === 0 ? (
                <li className="p-8 text-slate-500 text-center">No tables in this layer.</li>
              ) : (
                tables.map((t) => (
                  <li key={`${layer}.${t.physical_name}`}>
                    <Link
                      href={`/showcase/catalog?schema=${layer}&table=${t.physical_name}`}
                      className="block p-4 hover:bg-slate-50"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div>
                          <div className="font-semibold text-slate-900">{t.display_name}</div>
                          <div className="text-xs font-mono text-slate-500 mt-0.5">{t.physical_name}</div>
                          {t.description && (
                            <div className="text-sm text-slate-600 mt-1">{t.description}</div>
                          )}
                          {(t.subject_area || t.grain) && (
                            <div className="text-xs text-slate-500 mt-1">
                              {[t.subject_area, t.grain].filter(Boolean).join(" · ")}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <span className="text-slate-500">Rows: {(t.row_count ?? 0).toLocaleString()}</span>
                          {t.last_updated && (
                            <span className="text-slate-400">Updated: {t.last_updated}</span>
                          )}
                        </div>
                      </div>
                    </Link>
                  </li>
                ))
              )}
            </ul>
          )}
        </section>

        {/* Dataset profile page concept */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="text-sm text-slate-500">Dataset profile (V2)</div>
          <div className="font-bold mt-1">Description · Owner · Data Contract · Freshness · Quality Score · Lineage graph</div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs text-slate-500">Data Contract</div>
              <div className="text-sm mt-1">Schema version, required columns, constraints</div>
            </div>
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs text-slate-500">Lineage</div>
              <div className="text-sm mt-1">Upstream sources → downstream consumers</div>
            </div>
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="text-xs text-slate-500">Freshness & quality</div>
              <div className="text-sm mt-1">Last updated, trust score</div>
            </div>
          </div>
        </section>

        <p className="text-sm text-slate-600">
          <Link href="/showcase/catalog" className="text-ldv-blue font-semibold hover:underline">Open legacy Data Catalog</Link>
        </p>
      </div>
    </>
  );
}

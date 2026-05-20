"use client";

import { useEffect, useState } from "react";
import { backendGet } from "@/lib/backend";
import SectionHeader from "@/components/enterprise/SectionHeader";
import type { LucideIcon } from "lucide-react";

type TableInfo = {
  schema: string;
  table_name: string;
  full_name: string;
  row_count: number;
  layer: string;
  canonical?: boolean;
};

type WarehouseResponse = { ok: boolean; tables: TableInfo[] };

export default function LayerTablesView({
  layer,
  title,
  description,
  icon,
  accent = "#14b8a6",
}: {
  layer: string;
  title: string;
  description: string;
  icon: LucideIcon;
  accent?: string;
}) {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEmpty, setShowEmpty] = useState(false);

  useEffect(() => {
    const q = showEmpty ? "?non_empty=false" : "";
    backendGet<WarehouseResponse>(`/warehouse/tables${q}`)
      .then((d) => setTables((d.tables || []).filter((t) => t.layer === layer)))
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [layer, showEmpty]);

  const bySchema = tables.reduce<Record<string, TableInfo[]>>((acc, t) => {
    const s = t.schema;
    if (!acc[s]) acc[s] = [];
    acc[s].push(t);
    return acc;
  }, {});

  return (
    <div className="w-full">
      <SectionHeader icon={icon} title={title} description={description} />
      <label className="flex items-center gap-2 mb-4 text-sm text-slate-600">
        <input type="checkbox" checked={showEmpty} onChange={(e) => setShowEmpty(e.target.checked)} />
        Show empty tables
      </label>
      {loading && <p className="text-slate-500">Loading tables…</p>}
      {err && <p className="text-red-600 text-sm">{err}</p>}
      {!loading && !err && tables.length === 0 && (
        <p className="text-slate-500">No {layer} tables with data yet.</p>
      )}
      {Object.entries(bySchema).map(([schema, rows]) => (
        <section key={schema} className="mb-8 w-full">
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500 mb-3">{schema}</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 w-full">
            {rows.map((t) => (
              <div
                key={t.full_name}
                className="rounded-xl border border-slate-200 bg-white p-4 flex justify-between items-center shadow-sm"
              >
                <div className="min-w-0">
                  <div className="font-semibold text-[#0f2744] truncate">{t.table_name}</div>
                  <div className="text-xs text-slate-500 truncate">{t.full_name}</div>
                </div>
                <div className="text-xl font-bold shrink-0 ml-3" style={{ color: accent }}>
                  {t.row_count.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

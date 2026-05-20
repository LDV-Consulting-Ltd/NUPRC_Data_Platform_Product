"use client";

import { useEffect, useState } from "react";
import { Warehouse } from "lucide-react";
import { backendGet } from "@/lib/backend";
import SectionHeader from "@/components/enterprise/SectionHeader";

type TableInfo = {
  schema: string;
  table_name: string;
  full_name: string;
  row_count: number;
  layer: string;
};

type WarehouseResponse = { ok: boolean; tables: TableInfo[] };

const LAYER_ORDER = ["meta", "bronze", "silver", "warehouse"] as const;
const LAYER_LABELS: Record<string, string> = {
  meta: "Meta",
  bronze: "Bronze",
  silver: "Silver",
  warehouse: "Warehouse",
};
const LAYER_ACCENTS: Record<string, string> = {
  meta: "#6366f1",
  bronze: "#f59e0b",
  silver: "#2563eb",
  warehouse: "#14b8a6",
};

export default function WarehousePage() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [showEmpty, setShowEmpty] = useState(false);

  useEffect(() => {
    const q = showEmpty ? "?non_empty=false" : "";
    backendGet<WarehouseResponse>(`/warehouse/tables${q}`)
      .then((d) => setTables(d.tables || []))
      .catch((e) => setErr(String(e)));
  }, [showEmpty]);

  return (
    <div className="w-full">
      <SectionHeader
        icon={Warehouse}
        title="Warehouse Explorer"
        description="All PostgreSQL tables grouped by schema with live row counts."
      />
      <label className="flex items-center gap-2 mb-6 text-sm text-slate-600">
        <input type="checkbox" checked={showEmpty} onChange={(e) => setShowEmpty(e.target.checked)} />
        Show empty tables
      </label>
      {err && <p className="text-red-600 text-sm mb-4">{err}</p>}
      {LAYER_ORDER.map((layer) => {
        const rows = tables.filter((t) => t.layer === layer);
        if (rows.length === 0) return null;
        const bySchema = rows.reduce<Record<string, TableInfo[]>>((acc, t) => {
          if (!acc[t.schema]) acc[t.schema] = [];
          acc[t.schema].push(t);
          return acc;
        }, {});
        return (
          <section key={layer} className="mb-10 w-full">
            <h2 className="text-lg font-bold text-[#0f2744] mb-4 flex items-center gap-2">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: LAYER_ACCENTS[layer] }}
              />
              {LAYER_LABELS[layer]}
            </h2>
            {Object.entries(bySchema).map(([schema, schemaTables]) => (
              <div key={schema} className="mb-6">
                <h3 className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">{schema}</h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 w-full">
                  {schemaTables.map((t) => (
                    <div
                      key={t.full_name}
                      className="rounded-xl border border-slate-200 bg-white p-4 flex justify-between items-center shadow-sm"
                    >
                      <div className="min-w-0">
                        <div className="font-semibold text-[#0f2744] truncate">{t.table_name}</div>
                        <div className="text-xs text-slate-500 truncate">{t.full_name}</div>
                      </div>
                      <div
                        className="text-xl font-bold shrink-0 ml-3"
                        style={{ color: LAYER_ACCENTS[layer] }}
                      >
                        {t.row_count.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}

"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { backendGet } from "@/lib/backend";
import { fetchCatalogTables } from "@/lib/api";
import SectionHeader from "@/components/enterprise/SectionHeader";

type TableInfo = { table_name: string; row_count: number; layer: string };

export default function AnalyticsPage() {
  const [silverBars, setSilverBars] = useState<{ name: string; rows: number }[]>([]);
  const [layerBars, setLayerBars] = useState<{ layer: string; rows: number }[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [warehouse, catalog] = await Promise.all([
          backendGet<{ tables: TableInfo[] }>("/warehouse/tables"),
          fetchCatalogTables("silver").catch(() => null),
        ]);
        const silverTables = (warehouse.tables || []).filter((t) => t.layer === "silver" && t.row_count > 0);
        const topSilver = silverTables
          .sort((a, b) => b.row_count - a.row_count)
          .slice(0, 12)
          .map((t) => ({ name: t.table_name.replace(/^fact_|^dim_/, ""), rows: t.row_count }));

        if (topSilver.length > 0) {
          setSilverBars(topSilver);
        } else if (catalog?.tables?.length) {
          setSilverBars(
            catalog.tables
              .filter((t) => t.row_count > 0)
              .slice(0, 12)
              .map((t) => ({ name: t.display_name || t.physical_name, rows: t.row_count }))
          );
        }

        const layers = ["bronze", "silver", "warehouse"] as const;
        setLayerBars(
          layers.map((layer) => ({
            layer,
            rows: (warehouse.tables || [])
              .filter((t) => t.layer === layer)
              .reduce((sum, t) => sum + t.row_count, 0),
          }))
        );
      } catch (e) {
        setErr(String(e));
      }
    })();
  }, []);

  return (
    <div className="w-full space-y-8">
      <SectionHeader
        icon={BarChart3}
        title="Analytics"
        description="Row counts by silver table and layer totals from the warehouse API."
      />
      {err && <p className="text-red-600 text-sm">{err}</p>}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm w-full">
        <h3 className="font-bold text-[#0f2744] mb-4">Rows by layer</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={layerBars}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="layer" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => [Number(v).toLocaleString(), "Rows"]} />
              <Bar dataKey="rows" fill="#14b8a6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm w-full">
        <h3 className="font-bold text-[#0f2744] mb-4">Top silver tables</h3>
        {silverBars.length === 0 ? (
          <p className="text-slate-500 text-sm">No silver row counts available yet.</p>
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={silverBars} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => [Number(v).toLocaleString(), "Rows"]} />
                <Bar dataKey="rows" fill="#0f2744" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>
    </div>
  );
}

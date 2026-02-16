import V2Header from "../components/V2Header";
import Link from "next/link";

export default function LineagePage() {
  const nodes = [
    { id: "nuprc_oil", label: "NUPRC Oil", layer: "Source" },
    { id: "nuprc_gas", label: "NUPRC Gas", layer: "Source" },
    { id: "bronze_oil", label: "bronze.oil_production_status_raw", layer: "Bronze" },
    { id: "silver_oil", label: "silver.oil_production", layer: "Silver" },
    { id: "wh_fact", label: "warehouse.fact_oil_production", layer: "Warehouse" },
  ];

  return (
    <>
      <V2Header
        title="Lineage Explorer"
        subtitle="Interactive graph: click a dataset to highlight upstream and downstream"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Interactive graph placeholder */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div className="font-bold">Lineage graph</div>
            <span className="text-xs px-2 py-1 rounded-full bg-slate-100 chip">Click node to highlight paths</span>
          </div>
          <div className="mt-4 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 min-h-[320px] flex items-center justify-center">
            <div className="text-center text-slate-500">
              <div className="font-semibold">Interactive lineage (V2)</div>
              <div className="text-sm mt-1">Sources → Bronze → Silver → Warehouse → Products</div>
              <div className="mt-4 flex flex-wrap gap-2 justify-center">
                {nodes.map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    className="px-3 py-2 rounded-lg bg-white border border-slate-200 hover:border-ldv-green hover:bg-emerald-50 text-sm font-medium"
                  >
                    {n.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Legend */}
        <section className="flex flex-wrap gap-4 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-slate-400" /> Source
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-amber-500" /> Bronze
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-ldv-blue" /> Silver
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-ldv-green" /> Warehouse
          </span>
        </section>

        <p className="text-sm text-slate-600">
          <Link href="/showcase/diagrams" className="text-ldv-blue font-semibold hover:underline">Open legacy Lineage / Diagrams</Link>
        </p>
      </div>
    </>
  );
}

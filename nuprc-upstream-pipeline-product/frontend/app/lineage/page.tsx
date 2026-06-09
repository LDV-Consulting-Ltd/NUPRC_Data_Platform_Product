import V2Header from "../components/V2Header";
import Link from "next/link";

const LINEAGE_NODES = [
  { id: "src_oil", label: "NUPRC Oil Production", layer: "Source" },
  { id: "src_gas", label: "NUPRC Gas Production", layer: "Source" },
  { id: "src_rig", label: "NUPRC Rig Disposition", layer: "Source" },
  { id: "src_conc", label: "NUPRC Concession Status", layer: "Source" },
  { id: "bronze_oil", label: "bronze.etl_oil_production_raw", layer: "Bronze" },
  { id: "bronze_gas", label: "bronze.etl_gas_production_raw", layer: "Bronze" },
  { id: "bronze_rig", label: "bronze.etl_rig_disposition_raw", layer: "Bronze" },
  { id: "bronze_conc", label: "bronze.etl_concessions_raw", layer: "Bronze" },
  { id: "silver_oil", label: "silver.fact_oil_production", layer: "Silver" },
  { id: "silver_gas", label: "silver.fact_gas_production", layer: "Silver" },
  { id: "silver_rig", label: "silver.fact_rig_disposition", layer: "Silver" },
  { id: "silver_conc", label: "silver.fact_concession_status", layer: "Silver" },
  { id: "gold_oil", label: "gold.gold_oil_fact_production", layer: "Gold" },
  { id: "gold_gas", label: "gold.gold_gas_fact_production", layer: "Gold" },
  { id: "gold_rig", label: "gold.gold_rig_fact_activity", layer: "Gold" },
  { id: "gold_conc", label: "gold.gold_concession_fact_snapshot", layer: "Gold" },
  { id: "catalog", label: "data_catalog.available_tables", layer: "Catalog" },
];

export default function LineagePage() {
  return (
    <>
      <V2Header
        title="Lineage Explorer"
        subtitle="Structural v1 lineage: canonical medallion tables registered in data_catalog.available_tables"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div className="font-bold">Structural lineage graph</div>
            <span className="text-xs px-2 py-1 rounded-full bg-slate-100 chip">v1 ETL canonical tables</span>
          </div>
          <p className="text-sm text-slate-600 mt-2">
            Sources → Bronze (etl_*) → Silver (fact_*) → Gold (gold_*) → data_catalog.available_tables → /catalog and /warehouse APIs.
          </p>
          <div className="mt-4 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 min-h-[320px] flex items-center justify-center">
            <div className="text-center text-slate-500">
              <div className="font-semibold">Interactive lineage (V2)</div>
              <div className="text-sm mt-1">Click a node to highlight upstream and downstream paths</div>
              <div className="mt-4 flex flex-wrap gap-2 justify-center max-w-4xl">
                {LINEAGE_NODES.map((n) => (
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
            <span className="w-3 h-3 rounded-full bg-ldv-green" /> Gold
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-500" /> Catalog
          </span>
        </section>

        <p className="text-sm text-slate-600">
          <Link href="/showcase/diagrams" className="text-ldv-blue font-semibold hover:underline">
            Open legacy Lineage / Diagrams
          </Link>
          {" · "}
          <Link href="/catalog" className="text-ldv-blue font-semibold hover:underline">
            Live Tables catalog
          </Link>
        </p>
      </div>
    </>
  );
}

import V2Header from "../components/V2Header";
import Link from "next/link";

export default function DataQualityPage() {
  const scores = [
    { name: "Oil Production", completeness: 98, freshness: 92, schemaStability: 100, anomalyRate: 0.2, overall: 92 },
    { name: "Gas Production", completeness: 85, freshness: 54, schemaStability: 95, anomalyRate: 1.1, overall: 72 },
    { name: "Rig Disposition", completeness: 96, freshness: 88, schemaStability: 100, anomalyRate: 0.5, overall: 88 },
    { name: "Concession Status", completeness: 100, freshness: 79, schemaStability: 100, anomalyRate: 0, overall: 85 },
  ];

  return (
    <>
      <V2Header
        title="Data Quality"
        subtitle="Data Trust Score by completeness, freshness, schema stability, and anomaly rate"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Data Trust Score System */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-500">Platform-wide</div>
              <div className="text-xl font-bold">Data Trust Scores</div>
            </div>
            <span className="px-3 py-1.5 rounded-full bg-slate-100 chip text-xs">
              Score: Completeness · Freshness · Schema · Anomaly
            </span>
          </div>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
            {scores.map((row) => (
              <div
                key={row.name}
                className="rounded-xl border border-slate-200 p-4 flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold">{row.name}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    Completeness {row.completeness}% · Freshness {row.freshness} · Schema {row.schemaStability}% · Anomaly {row.anomalyRate}%
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold ${
                    row.overall >= 85 ? "text-emerald-600" : row.overall >= 70 ? "text-ldv-amber" : "text-ldv-red"
                  }`}>
                    {row.overall}
                  </div>
                  <div className="text-xs text-slate-500">/ 100</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Column-level quality drill */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="font-bold">Column-level Quality Drill</div>
          <div className="text-sm text-slate-600 mt-1">
            Select a dataset to see per-column trust (null rate, format, outliers).
          </div>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {["bronze.oil_production_status_raw", "bronze.gas_production_status_raw", "silver.oil_production", "warehouse.fact_oil_production"].map((ds) => (
              <button
                key={ds}
                type="button"
                className="rounded-xl border border-slate-200 p-3 text-left text-sm hover:bg-slate-50 hover:border-ldv-green"
              >
                <span className="font-mono text-xs break-all">{ds}</span>
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Click a dataset to open column-level quality metrics (V2).
          </p>
        </section>

        <p className="text-sm text-slate-600">
          <Link href="/showcase/quality" className="text-ldv-blue font-semibold hover:underline">Open legacy Data Quality dashboard</Link>
        </p>
      </div>
    </>
  );
}

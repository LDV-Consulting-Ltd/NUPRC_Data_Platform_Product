import V2Header from "../components/V2Header";

export default function TrustPage() {
  const heatmap = [
    { dataset: "bronze.oil_production_status_raw", score: 92, trend: "up" },
    { dataset: "bronze.gas_production_status_raw", score: 72, trend: "down" },
    { dataset: "silver.oil_production", score: 95, trend: "up" },
    { dataset: "warehouse.fact_oil_production", score: 98, trend: "stable" },
  ];

  return (
    <>
      <V2Header
        title="Trust Scoring"
        subtitle="Platform-wide data trust heatmap"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="text-sm text-slate-500">Platform-wide</div>
          <div className="text-xl font-bold mt-1">Trust heatmap</div>
          <div className="mt-4 rounded-xl overflow-hidden border border-slate-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left p-4 font-semibold">Dataset</th>
                  <th className="text-left p-4 font-semibold">Trust score</th>
                  <th className="text-left p-4 font-semibold">Trend</th>
                </tr>
              </thead>
              <tbody>
                {heatmap.map((row) => (
                  <tr
                    key={row.dataset}
                    className="border-b border-slate-100"
                    style={{
                      backgroundColor:
                        row.score >= 85
                          ? "rgba(16, 185, 129, 0.08)"
                          : row.score >= 70
                            ? "rgba(245, 158, 11, 0.08)"
                            : "rgba(220, 38, 38, 0.06)",
                    }}
                  >
                    <td className="p-4 font-mono text-xs">{row.dataset}</td>
                    <td className="p-4">
                      <span
                        className={`font-bold ${
                          row.score >= 85 ? "text-emerald-700" : row.score >= 70 ? "text-amber-700" : "text-red-700"
                        }`}
                      >
                        {row.score}
                      </span>
                      <span className="text-slate-500"> / 100</span>
                    </td>
                    <td className="p-4">
                      <span className="text-slate-600 capitalize">{row.trend}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="flex gap-4 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-emerald-200" /> High (85+)
          </span>
          <span className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-amber-200" /> Medium (70–84)
          </span>
          <span className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-red-200" /> Low (&lt;70)
          </span>
        </div>
      </div>
    </>
  );
}

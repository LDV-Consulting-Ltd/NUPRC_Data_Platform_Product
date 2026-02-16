import V2Header from "../components/V2Header";

export default function CostPage() {
  const rows = [
    { run: "RUN-2026-02-07-2114", cost: "—", dataset: "Full pipeline" },
    { run: "RUN-2026-02-07-0200", cost: "—", dataset: "Full pipeline" },
  ];

  return (
    <>
      <V2Header
        title="Cost & Usage"
        subtitle="FinOps dashboard: cost per run, cost per dataset, forecast"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Summary cards */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="text-xs text-slate-500">Cost this month</div>
            <div className="text-xl font-bold mt-1">—</div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="text-xs text-slate-500">Cost per run (avg)</div>
            <div className="text-xl font-bold mt-1">—</div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="text-xs text-slate-500">Cost per dataset</div>
            <div className="text-xl font-bold mt-1">—</div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="text-xs text-slate-500">Forecast (next 30d)</div>
            <div className="text-xl font-bold mt-1">—</div>
          </div>
        </section>

        {/* Cost per run table */}
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200 font-bold">Cost per run</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-semibold">Run</th>
                  <th className="text-left p-4 font-semibold">Cost</th>
                  <th className="text-left p-4 font-semibold">Dataset / scope</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.run} className="border-b border-slate-100">
                    <td className="p-4 font-mono text-xs">{r.run}</td>
                    <td className="p-4">{r.cost}</td>
                    <td className="p-4">{r.dataset}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="text-sm text-slate-500">
          FinOps metrics (cost per run, per dataset, forecast) can be wired to your billing backend (V2).
        </div>
      </div>
    </>
  );
}

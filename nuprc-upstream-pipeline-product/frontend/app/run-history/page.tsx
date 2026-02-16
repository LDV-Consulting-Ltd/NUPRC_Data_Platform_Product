import Link from "next/link";
import V2Header from "../components/V2Header";

export default function RunHistoryPage() {
  const runs = [
    { id: "RUN-2026-02-07-2114", trigger: "Scheduled", duration: "14m 22s", cost: "—", volume: "1.24M", result: "Success", sla: "Met" },
    { id: "RUN-2026-02-07-0200", trigger: "Scheduled", duration: "18m 05s", cost: "—", volume: "1.41M", result: "Success", sla: "Met" },
    { id: "RUN-2026-02-06-2112", trigger: "Manual", duration: "12m 44s", cost: "—", volume: "1.18M", result: "Success", sla: "—" },
    { id: "RUN-2026-02-06-0200", trigger: "Scheduled", duration: "—", cost: "—", volume: "—", result: "Failed", sla: "Breach" },
  ];

  return (
    <>
      <V2Header
        title="Run History"
        subtitle="Timeline and table of pipeline runs with trigger, duration, cost, volume, result, and SLA impact"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Timeline + Table hybrid */}
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200">
            <div className="text-sm text-slate-500">Run Timeline (last 7 days)</div>
            <div className="mt-3 flex gap-2 overflow-x-auto pb-2">
              {["07 Feb 02:00", "07 Feb 21:14", "06 Feb 02:00", "06 Feb 21:12", "05 Feb 02:00"].map((label, i) => (
                <button
                  key={label}
                  type="button"
                  className={`shrink-0 px-4 py-2 rounded-xl text-sm font-semibold ${
                    i === 1 ? "bg-ldv-green text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-semibold">Run ID</th>
                  <th className="text-left p-4 font-semibold">Trigger Source</th>
                  <th className="text-left p-4 font-semibold">Duration</th>
                  <th className="text-left p-4 font-semibold">Cost</th>
                  <th className="text-left p-4 font-semibold">Data Volume</th>
                  <th className="text-left p-4 font-semibold">Result</th>
                  <th className="text-left p-4 font-semibold">SLA Impact</th>
                  <th className="text-left p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="p-4 font-mono text-xs">{run.id}</td>
                    <td className="p-4">{run.trigger}</td>
                    <td className="p-4">{run.duration}</td>
                    <td className="p-4">{run.cost}</td>
                    <td className="p-4">{run.volume}</td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          run.result === "Success" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                        }`}
                      >
                        {run.result}
                      </span>
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          run.sla === "Met" ? "bg-emerald-50 text-emerald-700" : run.sla === "Breach" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {run.sla}
                      </span>
                    </td>
                    <td className="p-4">
                      <Link
                        href={`/showcase/runs?run_id=${run.id}`}
                        className="text-ldv-blue font-semibold hover:underline"
                      >
                        View
                      </Link>
                      <span className="mx-2 text-slate-300">|</span>
                      <button type="button" className="text-ldv-blue font-semibold hover:underline">
                        Re-run from step
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <p className="text-xs text-slate-500">
          Run Replay: Select a run and choose a step to re-execute from (V2 feature).
        </p>
      </div>
    </>
  );
}

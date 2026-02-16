import V2Header from "../components/V2Header";

export default function PipelineConfigPage() {
  const sources = ["Oil Production", "Gas Production", "Rig Disposition", "Concession Status"];
  const steps = ["Source", "Bronze", "Silver", "Warehouse", "Validate"];

  return (
    <>
      <V2Header
        title="Pipeline Config"
        subtitle="Visual pipeline builder: drag sources, transformations, validation rules"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="text-sm text-slate-500">Admin (SaaS)</div>
          <div className="text-xl font-bold mt-1">Visual pipeline builder</div>
          <div className="mt-5 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 min-h-[360px] p-6">
            {/* Drag areas */}
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="lg:w-48">
                <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Sources</div>
                <div className="space-y-2">
                  {sources.map((s) => (
                    <div
                      key={s}
                      className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium cursor-move hover:border-ldv-green"
                    >
                      {s}
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Pipeline canvas</div>
                <div className="flex gap-4 overflow-x-auto pb-4">
                  {steps.map((step) => (
                    <div
                      key={step}
                      className="shrink-0 w-40 rounded-xl border border-slate-200 bg-white p-4 text-center"
                    >
                      <div className="text-sm font-semibold">{step}</div>
                      <div className="mt-2 text-xs text-slate-500">Drop here</div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-slate-500 mt-2">
                  Drag sources onto canvas. Add transformations and validation rules (V2).
                </div>
              </div>
              <div className="lg:w-48">
                <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Validation rules</div>
                <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600">
                  Add schema checks, null checks, range rules.
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

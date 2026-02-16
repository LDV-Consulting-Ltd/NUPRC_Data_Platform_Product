export default function V2Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
        <div>
          <div className="text-lg font-bold">
            Energy Regulator Tenant Data Fabric <span className="text-slate-400 font-semibold">/</span> {title}
          </div>
          {subtitle && <div className="text-xs text-slate-500 mt-0.5">{subtitle}</div>}
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 chip text-xs">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> System Health: <b>Healthy</b>
          </span>
          <button type="button" className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-sm font-semibold">Notifications</button>
          <button type="button" className="px-3 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold">Admin</button>
        </div>
      </div>
    </header>
  );
}

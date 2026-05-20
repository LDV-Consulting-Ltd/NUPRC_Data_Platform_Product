import type { LucideIcon } from "lucide-react";

type Tone = "neutral" | "success" | "warning" | "danger" | "teal";

const toneMap: Record<Tone, string> = {
  neutral: "bg-white text-slate-800 border-slate-200",
  success: "bg-white text-emerald-800 border-emerald-200",
  warning: "bg-white text-amber-900 border-amber-200",
  danger: "bg-white text-red-800 border-red-200",
  teal: "bg-white text-teal-900 border-teal-200",
};

export default function StatusCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "neutral",
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  hint?: string;
  tone?: Tone;
}) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${toneMap[tone]}`}>
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-xl bg-[#0f2744] text-teal-300 flex items-center justify-center shrink-0">
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
          <div className="text-2xl font-bold mt-1 text-[#0f2744]">{value}</div>
          {hint && <div className="text-xs mt-1 text-slate-500">{hint}</div>}
        </div>
      </div>
    </div>
  );
}

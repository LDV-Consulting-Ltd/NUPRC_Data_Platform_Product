import type { LucideIcon } from "lucide-react";

export default function SectionHeader({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex items-start gap-4 mb-6">
      <div className="h-12 w-12 rounded-2xl bg-[#0f2744] text-teal-300 flex items-center justify-center shrink-0">
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-[#0f2744]">{title}</h2>
        {description && <p className="text-sm text-slate-600 mt-1 max-w-3xl">{description}</p>}
      </div>
    </div>
  );
}

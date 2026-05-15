import type { RecommendationsReport, RecommendationSection } from "../types/api";

const statusStyles = {
  ok: {
    border: "border-emerald-900/50",
    bg: "bg-emerald-950/30",
    pill: "bg-emerald-950/80 text-emerald-300",
    dot: "bg-emerald-400",
  },
  caution: {
    border: "border-amber-900/50",
    bg: "bg-amber-950/25",
    pill: "bg-amber-950/80 text-amber-300",
    dot: "bg-amber-400",
  },
  critical: {
    border: "border-red-900/50",
    bg: "bg-red-950/25",
    pill: "bg-red-950/80 text-red-300",
    dot: "bg-red-400",
  },
} as const;

function SectionCard({ section, label }: { section: RecommendationSection; label: string }) {
  const s = statusStyles[section.status];
  return (
    <div className={`rounded border p-3 ${s.border} ${s.bg}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{label}</div>
        <span className={`shrink-0 rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${s.pill}`}>
          {section.status === "ok" ? "OK" : section.status === "caution" ? "UWAGA" : "STOP"}
        </span>
      </div>
      <h3 className="mt-1 text-sm font-medium text-slate-100">{section.headline}</h3>
      <ul className="mt-2 space-y-1.5">
        {section.items.map((item) => (
          <li key={item} className="flex gap-2 text-[11px] leading-snug text-slate-300">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${s.dot}`} aria-hidden />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RecommendationsPanel({ report }: { report: RecommendationsReport | null | undefined }) {
  if (!report) {
    return (
      <div className="rounded border border-line bg-panel p-3 text-xs text-slate-500">
        Rekomendacje — przelicz plan ładunku.
      </div>
    );
  }

  const s = statusStyles[report.summary.status];

  return (
    <div className="space-y-3">
      <div className={`rounded border p-3 ${s.border} ${s.bg}`}>
        <div className="flex items-start justify-between gap-2">
          <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Podsumowanie</div>
          <span className={`shrink-0 rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${s.pill}`}>
            {report.summary.status === "ok" ? "OK" : report.summary.status === "caution" ? "UWAGA" : "STOP"}
          </span>
        </div>
        <h3 className="mt-1 text-sm font-semibold text-slate-100">{report.summary.headline}</h3>
        <p className="mt-2 text-[11px] leading-relaxed text-slate-300">{report.summary.paragraph}</p>
        <p className="mt-2 rounded border border-line/60 bg-black/20 px-2 py-1.5 text-[11px] font-medium text-slate-200">
          {report.summary.verdict}
        </p>
        {report.summary.key_metrics.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {report.summary.key_metrics.map((m) => (
              <span key={m} className="rounded bg-panel2 px-2 py-0.5 font-mono text-[10px] text-slate-400">
                {m}
              </span>
            ))}
          </div>
        )}
      </div>
      <SectionCard section={report.loading} label="Rekomendacja załadunku" />
      <SectionCard section={report.driving} label="Rekomendacja jazdy" />
    </div>
  );
}
